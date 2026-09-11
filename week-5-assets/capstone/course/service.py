"""Deterministic mock AI and validation. No paid calls or financial actions."""
import json
import re
from .models import ResumeOutput


class TemporaryFailure(Exception):
    pass


def mock_generate(task):
    payload=task['payload']
    mode=payload['mode']
    if mode=='timeout' or (mode=='transient' and task['attempts']<3):
        raise TemporaryFailure('simulated_provider_failure')
    if mode=='invalid_json':
        return '{'
    if task['kind']=='transaction':
        return json.dumps({'event_id':payload['event_id'], 'anomalies':[] if mode=='hallucination' else payload['anomalies'], 'summary':'Fixture summary; rules are the authoritative source.'})
    if mode=='hallucination':
        return json.dumps({'claims':[{'skill':'Rust','quote':'Built a Rust trading project.'}]})
    claims=[{'skill':m.group(1),'quote':m.group(0)} for m in re.finditer(r'Built a (Python|SQL|Docker) [^.\n]+\.',payload['document_text'])]
    return json.dumps({'claims':claims})


def process_one(store, clock, provider=mock_generate):
    task=store.claim(clock())
    if task is None:
        return False
    try:
        raw=provider(task)
        result=json.loads(raw)
        if not isinstance(result,dict):
            raise ValueError('not_object')
        if task['kind']=='transaction':
            p=task['payload']
            if set(result)!={'event_id','anomalies','summary'} or result['event_id']!=p['event_id'] or result['anomalies']!=p['anomalies'] or not isinstance(result['summary'],str) or not result['summary'].strip():
                raise ValueError('summary_contract_mismatch')
            # Free text remains untrusted even when rule labels match.
            result['summary_is_mock']=True
            result['rules']=p['anomalies']
            result['requires_human_review']=bool(p['anomalies'])
            reason='transaction_anomaly' if p['anomalies'] else None
        else:
            result=ResumeOutput.model_validate(result).model_dump()
            seen=set()
            for claim in result['claims']:
                if not isinstance(claim,dict) or set(claim)!={'skill','quote'}:
                    raise ValueError('claim_schema')
                if not all(isinstance(v,str) and v.strip() for v in claim.values()):
                    raise ValueError('blank_claim')
                if claim['quote'] not in task['payload']['document_text'] or claim['skill'] not in claim['quote']:
                    raise ValueError('unsupported_claim')
                if any(word in claim['quote'].lower() for word in ['never','not ','ไม่เคย']):
                    raise ValueError('negation')
                if claim['skill'] in seen:
                    raise ValueError('duplicate_claim')
                seen.add(claim['skill'])
            result['requires_human_review']=True
            result['validation_level']='lexical_only'
            result['job_version']=task['payload']['job_version']
            result['requirement_matches']=[
                {'requirement':requirement,
                 'status':'evidence_found' if any(c['skill'].casefold()==requirement.casefold() for c in result['claims']) else 'not_evidenced',
                 'evidence':[c['quote'] for c in result['claims'] if c['skill'].casefold()==requirement.casefold()]}
                for requirement in task['payload']['job_requirements']]
            result['warnings']=['Lexical evidence only; not a hiring recommendation.']
            reason='resume_evidence_review'
        store.finish(task,'succeeded',result,clock(),reason)
    except TemporaryFailure:
        exhausted=task['attempts']>=3
        fallback={'rules':task['payload']['anomalies'],'summary_unavailable':True} if task['kind']=='transaction' else {}
        store.finish(task,'failed' if exhausted else 'retry_pending',{'reason':'retry_exhausted' if exhausted else 'temporary_failure',**fallback},clock(),'retry_exhausted' if exhausted else None,delay=2**(task['attempts']-1))
    except (ValueError,TypeError,KeyError):
        fallback={'rules':task['payload']['anomalies'],'summary_unavailable':True} if task['kind']=='transaction' else {}
        store.finish(task,'needs_review',{'reason':'invalid_ai_output','validated_output':None,**fallback},clock(),'invalid_ai_output')
    return True
