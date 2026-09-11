from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from course.api import create_app
from course.models import Transaction, Resume
from course.repository import Store, Conflict
from course.service import process_one


def event(key='E1', mode='normal', amount=100_000):
    return Transaction(event_id=key,user_id='U1',amount_minor=amount,mode=mode).model_dump()


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path/'test.sqlite3')


def test_durable_dedup_and_conflict(store):
    tid,duplicate=store.ingest_transaction(event(),100)
    assert not duplicate
    reopened=Store(store.path)
    assert reopened.ingest_transaction(event(),101)==(tid,True)
    with pytest.raises(Conflict):
        reopened.ingest_transaction(event(amount=5),102)
    assert reopened.summary()['events']==1


def test_rules_velocity_and_duplicate_not_counted(store):
    store.ingest_transaction(event('1',amount=1),100)
    store.ingest_transaction(event('1',amount=1),101)
    store.ingest_transaction(event('2',amount=1),110)
    tid,_=store.ingest_transaction(event('3',amount=1),120)
    while process_one(store,lambda:121):
        pass
    assert store.task(tid)['result']['rules']==['velocity_3_in_60s']


def test_velocity_window_excludes_exactly_sixty_seconds(store):
    store.ingest_transaction(event('1',amount=1),0)
    store.ingest_transaction(event('2',amount=1),1)
    tid,_=store.ingest_transaction(event('3',amount=1),60)
    while process_one(store,lambda:61):
        pass
    assert store.task(tid)['result']['rules']==[]


def test_atomic_concurrent_intake(store):
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:store.ingest_transaction(event(),100),range(8)))
    assert len({r[0] for r in results})==1
    assert sum(not r[1] for r in results)==1


def test_only_one_worker_claims(store):
    store.ingest_transaction(event(),100)
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims=list(pool.map(lambda _:store.claim(101),range(4)))
    assert sum(c is not None for c in claims)==1


def test_expired_worker_cannot_overwrite(store):
    tid,_=store.ingest_transaction(event(),100)
    old=store.claim(101)
    assert not store.finish(old,'succeeded',{'stale':True},131)
    new=Store(store.path).claim(132)
    assert new['attempts']==2
    assert not store.finish(old,'succeeded',{'stale':True},133)
    assert store.finish(new,'succeeded',{'new':True},133)
    assert store.task(tid)['result']=={'new':True}


def test_crash_budget_exhausted(store):
    tid,_=store.ingest_transaction(event(),0)
    for now in (0,31,62):
        assert store.claim(now)
    assert store.claim(93) is None
    assert store.task(tid)['state']=='failed'
    assert store.reviews()[0]['reason']=='transaction_anomaly'
    assert store.task(tid)['result']['reason']=='crash_budget_exhausted'
    assert store.history(tid)[-1]['action']=='crash_budget_exhausted'


@pytest.mark.parametrize('mode,expected', [('normal','succeeded'),('invalid_json','needs_review'),('hallucination','needs_review')])
def test_transaction_output_contract(store,mode,expected):
    tid,_=store.ingest_transaction(event(mode=mode),100)
    assert process_one(store,lambda:101)
    assert store.task(tid)['state']==expected
    assert len(store.reviews())==1


@pytest.mark.parametrize('mode,expected',[('transient','succeeded'),('timeout','failed')])
def test_bounded_retry(store,mode,expected):
    tid,_=store.ingest_transaction(event(mode=mode),100)
    process_one(store,lambda:100)
    assert not process_one(store,lambda:100.5)
    process_one(store,lambda:101)
    assert not process_one(store,lambda:102)
    process_one(store,lambda:103)
    assert store.task(tid)['state']==expected
    assert store.task(tid)['attempts']==3


@pytest.mark.parametrize('mode,expected',[('normal','succeeded'),('hallucination','needs_review')])
def test_hr_evidence_and_human_review(store,mode,expected):
    payload=Resume(candidate_id='C1',document_text='Built a Python ETL project.',mode=mode).model_dump()
    tid,_=store.ingest_resume(payload,100)
    assert store.ingest_resume(payload,101)==(tid,True)
    process_one(store,lambda:102)
    assert store.task(tid)['state']==expected
    assert len(store.reviews())==1


def test_review_auth_idempotency_and_result_immutable(tmp_path):
    token='test-only-not-a-live-token-12345'
    app=create_app(tmp_path/'api.sqlite3',clock=lambda:100,review_token=token)
    client=TestClient(app)
    response=client.post('/transactions',json=event())
    assert response.status_code==202
    tid=response.json()['task_id']
    process_one(app.state.store,lambda:101)
    before=client.get(f'/tasks/{tid}').json()['result']
    assert client.get('/reviews').status_code==401
    headers={'Authorization':'Bearer '+token}
    decision={'decision_id':'D1','outcome':'verified','note':'Synthetic review complete'}
    first=client.post(f'/reviews/{tid}/decision',json=decision,headers=headers)
    assert first.status_code==200
    assert client.post(f'/reviews/{tid}/decision',json=decision,headers=headers).json()==first.json()
    assert client.post(f'/reviews/{tid}/decision',json={**decision,'note':'changed'},headers=headers).status_code==409
    assert client.get(f'/tasks/{tid}').json()['result']==before


def test_http_validation_conflict_and_unconfigured_auth(tmp_path):
    client=TestClient(create_app(tmp_path/'api.sqlite3',review_token=''))
    assert client.post('/transactions',json={**event(),'amount_minor':0}).status_code==422
    assert client.post('/transactions',json={**event(),'amount_minor':'100'}).status_code==422
    assert client.post('/transactions',json=event()).status_code==202
    assert client.post('/transactions',json=event(amount=2)).status_code==409
    assert client.get('/reviews').status_code==503
    assert client.get('/tasks/999').status_code==404


def test_unexpected_exception_leaves_recoverable_lease(store):
    tid,_=store.ingest_transaction(event(),0)
    def broken(task):
        raise RuntimeError('synthetic failure')
    with pytest.raises(RuntimeError):
        process_one(store,lambda:1,provider=broken)
    assert store.task(tid)['state']=='running'
    assert process_one(Store(store.path),lambda:32)
    assert store.task(tid)['state']=='succeeded'


def test_anomaly_review_exists_without_ai_worker(store):
    tid,_=store.ingest_transaction(event(),100)
    assert store.task(tid)['state']=='queued'
    assert store.reviews()[0]['reason']=='transaction_anomaly'


def test_ai_failure_preserves_rules(store):
    tid,_=store.ingest_transaction(event(mode='invalid_json'),100)
    process_one(store,lambda:101)
    assert store.task(tid)['result']['rules']==['large_amount']
    assert store.task(tid)['result']['summary_unavailable'] is True


def test_configurable_requirement_evidence_not_rejection(store):
    payload=Resume(candidate_id='C1',document_text='Built a Python ETL project.',job_requirements=['Python','Docker']).model_dump()
    tid,_=store.ingest_resume(payload,100)
    process_one(store,lambda:101)
    result=store.task(tid)['result']
    assert [m['status'] for m in result['requirement_matches']]==['evidence_found','not_evidenced']
    assert result['requirement_matches'][1]['evidence']==[]
    assert result['requires_human_review'] is True
    with pytest.raises(Conflict):
        store.ingest_resume({**payload,'job_requirements':['SQL']},102)
    other,_=store.ingest_resume({**payload,'job_requirements':['SQL'],'job_version':'demo-v2'},103)
    assert other!=tid
