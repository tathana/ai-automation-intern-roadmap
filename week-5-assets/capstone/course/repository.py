"""SQLite task queue for one-host labs; computation happens outside transactions."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid


class Conflict(ValueError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as con:
            con.executescript('''
            CREATE TABLE IF NOT EXISTS events (
              event_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
              amount_minor INTEGER NOT NULL, payload TEXT NOT NULL,
              created REAL NOT NULL, anomalies TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks (
              id INTEGER PRIMARY KEY, kind TEXT NOT NULL, task_key TEXT NOT NULL,
              payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'queued',
              attempts INTEGER NOT NULL DEFAULT 0, available REAL NOT NULL,
              lease_token TEXT, lease_until REAL, result TEXT,
              created REAL NOT NULL, finished REAL, UNIQUE(kind, task_key));
            CREATE TABLE IF NOT EXISTS audit (
              id INTEGER PRIMARY KEY, task_id INTEGER NOT NULL,
              action TEXT NOT NULL, at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS reviews (
              task_id INTEGER PRIMARY KEY, reason TEXT NOT NULL,
              state TEXT NOT NULL DEFAULT 'pending', reviewer TEXT,
              decision_id TEXT UNIQUE, decision TEXT, decided REAL);
            CREATE INDEX IF NOT EXISTS task_claim ON tasks(state,available);
            CREATE INDEX IF NOT EXISTS event_velocity ON events(user_id,created);
            ''')

    @contextmanager
    def connection(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            with con:
                yield con
        finally:
            con.close()

    @staticmethod
    def audit(con, tid, action, now):
        con.execute('INSERT INTO audit(task_id,action,at) VALUES (?,?,?)', (tid,action,now))

    @staticmethod
    def review(con, tid, reason):
        con.execute('INSERT INTO reviews(task_id,reason) VALUES (?,?) ON CONFLICT(task_id) DO NOTHING', (tid,reason))

    def ingest_transaction(self, payload, now):
        raw = encoded(payload)
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            old = con.execute('SELECT payload FROM events WHERE event_id=?', (payload['event_id'],)).fetchone()
            if old:
                if old['payload'] != raw:
                    raise Conflict('same_event_id_different_payload')
                task = con.execute("SELECT id FROM tasks WHERE kind='transaction' AND task_key=?", (payload['event_id'],)).fetchone()
                self.audit(con,task['id'],'duplicate_received',now)
                return task['id'], True
            anomalies = []
            if payload['amount_minor'] >= 100_000:
                anomalies.append('large_amount')
            previous = con.execute('SELECT COUNT(*) FROM events WHERE user_id=? AND created>? AND created<=?', (payload['user_id'],now-60,now)).fetchone()[0]
            if previous+1 >= 3:
                anomalies.append('velocity_3_in_60s')
            con.execute('INSERT INTO events VALUES (?,?,?,?,?,?)', (payload['event_id'],payload['user_id'],payload['amount_minor'],raw,now,encoded(anomalies)))
            task_payload = {**payload,'anomalies':anomalies}
            tid = con.execute("INSERT INTO tasks(kind,task_key,payload,available,created) VALUES ('transaction',?,?,?,?)", (payload['event_id'],encoded(task_payload),now,now)).lastrowid
            self.audit(con,tid,'accepted',now)
            if anomalies:
                self.review(con,tid,'transaction_anomaly')
            return tid, False

    def ingest_resume(self, payload, now):
        # This endpoint receives text, so this is a text hash, never a file-bytes hash.
        digest = hashlib.sha256(payload['document_text'].encode('utf-8')).hexdigest()
        key = encoded([payload['candidate_id'],digest,payload['processing_version'],payload['job_version']])
        raw = encoded(payload)
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            old = con.execute("SELECT id,payload FROM tasks WHERE kind='resume' AND task_key=?", (key,)).fetchone()
            if old:
                if old['payload'] != raw:
                    raise Conflict('same_document_version_different_options')
                self.audit(con,old['id'],'duplicate_received',now)
                return old['id'], True
            tid=con.execute("INSERT INTO tasks(kind,task_key,payload,available,created) VALUES ('resume',?,?,?,?)",(key,raw,now,now)).lastrowid
            self.audit(con,tid,'accepted',now)
            return tid, False

    def claim(self, now, lease_seconds=30):
        if lease_seconds <= 0:
            raise ValueError('positive lease required')
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            expired=con.execute("SELECT id FROM tasks WHERE state='running' AND lease_until<=? AND attempts>=3", (now,)).fetchall()
            for row in expired:
                con.execute("UPDATE tasks SET state='failed',lease_token=NULL,lease_until=NULL,result=?,finished=? WHERE id=?", (encoded({'reason':'crash_budget_exhausted'}),now,row['id']))
                self.review(con,row['id'],'crash_budget_exhausted')
                self.audit(con,row['id'],'crash_budget_exhausted',now)
            row=con.execute("SELECT * FROM tasks WHERE attempts<3 AND ((state IN ('queued','retry_pending') AND available<=?) OR (state='running' AND lease_until<=?)) ORDER BY id LIMIT 1",(now,now)).fetchone()
            if row is None:
                return None
            token=uuid.uuid4().hex
            con.execute("UPDATE tasks SET state='running',attempts=attempts+1,lease_token=?,lease_until=? WHERE id=?",(token,now+lease_seconds,row['id']))
            self.audit(con,row['id'],'lease_reclaimed' if row['state']=='running' else 'claimed',now)
            return {**dict(row),'payload':json.loads(row['payload']),'attempts':row['attempts']+1,'lease_token':token,'lease_until':now+lease_seconds}

    def finish(self, task, state, result, now, review_reason=None, delay=1):
        if state not in {'succeeded','needs_review','retry_pending','failed'}:
            raise ValueError('unsupported terminal/next state')
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            changed=con.execute("UPDATE tasks SET state=?,result=?,available=?,finished=?,lease_token=NULL,lease_until=NULL WHERE id=? AND state='running' AND lease_token=? AND lease_until>?", (state,encoded(result),now+delay,None if state=='retry_pending' else now,task['id'],task['lease_token'],now)).rowcount
            if not changed:
                return False  # Old or expired lease cannot overwrite a newer attempt.
            self.audit(con,task['id'],state,now)
            if review_reason:
                self.review(con,task['id'],review_reason)
            return True

    def task(self, tid):
        with self.connection() as con:
            row=con.execute('SELECT id,kind,state,attempts,result,created,finished FROM tasks WHERE id=?',(tid,)).fetchone()
            if row is None:
                return None
            return {**dict(row),'result':json.loads(row['result']) if row['result'] else None}

    def history(self, tid):
        with self.connection() as con:
            return [dict(r) for r in con.execute('SELECT action,at FROM audit WHERE task_id=? ORDER BY id',(tid,))]

    def reviews(self):
        with self.connection() as con:
            return [dict(r) for r in con.execute('SELECT * FROM reviews ORDER BY task_id')]

    def decide(self, tid, decision, reviewer, now):
        raw=encoded(decision)
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT * FROM reviews WHERE task_id=?',(tid,)).fetchone()
            if row is None:
                raise KeyError('review_not_found')
            if row['decision_id']:
                if row['decision_id']==decision['decision_id'] and row['decision']==raw and row['reviewer']==reviewer:
                    return dict(row)
                raise Conflict('review_already_decided')
            if con.execute('SELECT 1 FROM reviews WHERE decision_id=?',(decision['decision_id'],)).fetchone():
                raise Conflict('decision_id_in_use')
            con.execute('UPDATE reviews SET state=?,reviewer=?,decision_id=?,decision=?,decided=? WHERE task_id=?',(decision['outcome'],reviewer,decision['decision_id'],raw,now,tid))
            self.audit(con,tid,'review_decided',now)
            return dict(con.execute('SELECT * FROM reviews WHERE task_id=?',(tid,)).fetchone())

    def summary(self):
        with self.connection() as con:
            return {'events':con.execute('SELECT COUNT(*) FROM events').fetchone()[0],
                    'tasks_by_state':{r['state']:r['n'] for r in con.execute('SELECT state,COUNT(*) n FROM tasks GROUP BY state')},
                    'pending_reviews':con.execute("SELECT COUNT(*) FROM reviews WHERE state='pending'").fetchone()[0]}
