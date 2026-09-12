"""Small, isolated teaching traces using the actual capstone implementation.

Run from capstone: python learning_walkthrough.py state
Uses a temporary database and simulated time. No HTTP server or paid AI calls.
"""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from course.models import Resume, Transaction
from course.repository import Store
from course.service import process_one


def event(key='E1', amount=150_000, mode='normal'):
    return Transaction(event_id=key, user_id='U1', amount_minor=amount, mode=mode).model_dump()


def show(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def state_demo(store):
    tid, duplicate = store.ingest_transaction(event(), 100)
    print(f'first: task_id={tid} duplicate={duplicate}')
    reopened = Store(store.path)
    repeated_id, duplicate = reopened.ingest_transaction(event(), 101)
    print(f'reopened: task_id={repeated_id} duplicate={duplicate}')
    assert tid == repeated_id and duplicate
    with reopened.connection() as con:
        rows = con.execute('SELECT id, state, attempts FROM tasks ORDER BY id').fetchall()
        show([dict(row) for row in rows])
    assert reopened.summary()['events'] == 1


def retry_demo(store):
    tid, _ = store.ingest_transaction(event(mode='transient'), 100)
    for now in [100, 100.5, 101, 102, 103]:
        worked = process_one(store, lambda: now)
        task = store.task(tid)
        print(f'time={now} worked={worked} state={task["state"]} attempts={task["attempts"]}')
    assert task['state'] == 'succeeded' and task['attempts'] == 3


def lease_demo(store):
    tid, _ = store.ingest_transaction(event(), 0)
    old = store.claim(1)
    new = store.claim(32)
    old_accepted = store.finish(old, 'succeeded', {'owner': 'old'}, 33)
    new_accepted = store.finish(new, 'succeeded', {'owner': 'new'}, 33)
    print(f'old_completion_accepted={old_accepted}')
    print(f'new_completion_accepted={new_accepted}')
    assert old_accepted is False and new_accepted is True
    show(store.task(tid))


def review_demo(store):
    payload = Resume(candidate_id='C1', document_text='Built a Python ETL project.').model_dump()
    tid, _ = store.ingest_resume(payload, 100)
    process_one(store, lambda: 101)
    before = store.task(tid)['result']
    print('review_before=' + store.reviews()[0]['state'])
    decision = {'decision_id': 'D1', 'outcome': 'verified', 'note': 'Checked synthetic evidence'}
    first = store.decide(tid, decision, 'local-demo-reviewer', 102)
    repeated = store.decide(tid, decision, 'local-demo-reviewer', 103)
    print('review_after=' + first['state'])
    print('same_decision_on_replay=' + str(first == repeated))
    print('ai_result_unchanged=' + str(before == store.task(tid)['result']))
    assert first == repeated and before == store.task(tid)['result']
    show(store.history(tid))


def transaction_demo(store):
    tids = []
    for index, amount in enumerate([500, 100_000, 500]):
        tid, _ = store.ingest_transaction(event(key=f'E{index+1}', amount=amount), 100 + index)
        tids.append(tid)
    while process_one(store, lambda: 110):
        pass
    rules = [store.task(tid)['result']['rules'] for tid in tids]
    assert rules == [[], ['large_amount'], ['velocity_3_in_60s']]
    show({'rules_per_event': rules, 'summary': store.summary()})


def hr_demo(store, mode):
    payload = Resume(candidate_id='C1', document_text='Built a Python ETL project.',
                     job_requirements=['Python', 'Docker'], mode=mode).model_dump()
    tid, _ = store.ingest_resume(payload, 99)
    for now in [100, 101, 103]:
        process_one(store, lambda: now)
    task = store.task(tid)
    expected = {'normal': 'succeeded', 'transient': 'succeeded', 'timeout': 'failed',
                'invalid_json': 'needs_review', 'hallucination': 'needs_review'}[mode]
    assert task['state'] == expected
    if expected == 'succeeded':
        assert [m['status'] for m in task['result']['requirement_matches']] == ['evidence_found', 'not_evidenced']
    show(task)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', choices=['state', 'retry', 'lease', 'review', 'transaction', 'hr'])
    parser.add_argument('--mode', choices=['normal', 'transient', 'timeout', 'invalid_json', 'hallucination'], default='normal', help='Used by the hr scenario')
    args = parser.parse_args()
    with TemporaryDirectory(prefix='week5-learning-') as directory:
        store = Store(Path(directory) / 'learning.sqlite3')
        if args.scenario == 'hr':
            hr_demo(store, args.mode)
        else:
            {'state': state_demo, 'retry': retry_demo, 'lease': lease_demo,
             'review': review_demo, 'transaction': transaction_demo}[args.scenario](store)
    print('PASS: teaching assertions; temporary database closed and removed')


if __name__ == '__main__':
    main()
