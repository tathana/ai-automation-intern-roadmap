import hmac
import os
from time import time
from fastapi import FastAPI, Header, HTTPException, Request as HTTPRequest
from fastapi.responses import JSONResponse
from .models import Transaction, Resume, Decision
from .repository import Store, Conflict


def create_app(path=None, clock=time, review_token=None):
    store=Store(path or os.environ.get('CAPSTONE_DB','data/capstone.sqlite3'))
    token=review_token if review_token is not None else os.environ.get('REVIEW_TOKEN','')
    app=FastAPI(title='Week 5 Local Synthetic Capstone')
    app.state.store=store

    @app.exception_handler(Conflict)
    async def conflict_handler(request: HTTPRequest, exc: Conflict):
        return JSONResponse({'detail':str(exc)},status_code=409)

    @app.get('/health')
    def health():
        store.summary()  # Readiness includes a database query.
        return {'status':'ok','scope':'week5-local-synthetic','provider':'mock'}

    @app.post('/transactions',status_code=202)
    def transaction(payload: Transaction):
        tid,duplicate=store.ingest_transaction(payload.model_dump(),clock())
        return {'task_id':tid,'duplicate':duplicate,'state':store.task(tid)['state']}

    @app.post('/resumes',status_code=202)
    def resume(payload: Resume):
        tid,duplicate=store.ingest_resume(payload.model_dump(),clock())
        return {'task_id':tid,'duplicate':duplicate,'state':store.task(tid)['state']}

    @app.get('/tasks/{tid}')
    def get_task(tid: int):
        result=store.task(tid)
        if result is None:
            raise HTTPException(404,'task_not_found')
        return result

    @app.get('/tasks/{tid}/audit')
    def audit(tid: int):
        if store.task(tid) is None:
            raise HTTPException(404,'task_not_found')
        return {'records':store.history(tid)}

    @app.get('/summary')
    def summary():
        return store.summary()

    def authorize(authorization):
        if len(token)<20 or token.startswith('replace-'):
            raise HTTPException(503,'review_auth_not_configured')
        if not authorization or not hmac.compare_digest(authorization,'Bearer '+token):
            raise HTTPException(401,'unauthorized')

    @app.get('/reviews')
    def reviews(authorization: str | None=Header(default=None)):
        authorize(authorization)
        return {'reviews':store.reviews()}

    @app.post('/reviews/{tid}/decision')
    def decide(tid: int, payload: Decision, authorization: str | None=Header(default=None)):
        authorize(authorization)
        try:
            return store.decide(tid,payload.model_dump(),'local-demo-reviewer',clock())
        except KeyError:
            raise HTTPException(404,'review_not_found')

    return app


app=create_app()
