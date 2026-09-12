# Full Project B — Daily Operations Report Automation

Reference implementation สำหรับข้อมูลสังเคราะห์ รับ event เป็น batch จาก CSV/JSON หรือ API ตรวจด้วย Pydantic บันทึกทั้ง batch แบบ atomic ใน SQLite ป้องกันการส่งซ้ำ แล้วสร้างรายงานรายวันผ่าน CLI/API

ถ้าเพิ่งเริ่มเรื่อง Pydantic/transaction/idempotency ให้อ่าน [GUIDED_CODE_TOUR.md](GUIDED_CODE_TOUR.md) คู่กับ source เอกสารจะไล่ CSV หนึ่งแถวจนกลายเป็นรายงานและแปลศัพท์เทคนิคทุก boundary

> Local educational system • no real customer/payment data • no money movement • no production authentication

## Architecture

```text
CSV/JSON → CLI ─┐
                ├→ Batch service → SQLite batches/events/audit
n8n → FastAPI ──┘                         ↓
                                  Report query
                                     ├→ GET /reports/{day}
                                     └→ atomic JSON file
```

## Structure

```text
ops_report/
├── models.py       # Pydantic input/output contracts
├── repository.py   # schema, transaction, idempotency, aggregate query
├── service.py      # orchestration and atomic output
├── api.py          # HTTP boundary
└── cli.py          # CSV/JSON boundary
tests/              # unit/integration/API evidence
fixtures/           # synthetic data only
workflows/          # inactive n8n example
Dockerfile
compose.yaml
RUNBOOK.md
```

## 1. Setup และ Test

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: tests ผ่านทั้งหมด ก่อนใช้ CLI หรือ Docker

## 2. CLI Flow

```powershell
$env:OPS_DB = "data/ops.sqlite3"
.\.venv\Scripts\python.exe -m ops_report.cli import --batch-id BATCH-DEMO-001 --file fixtures/events.csv
.\.venv\Scripts\python.exe -m ops_report.cli import --batch-id BATCH-DEMO-001 --file fixtures/events.csv
.\.venv\Scripts\python.exe -m ops_report.cli report --day 2026-09-13 --output reports/2026-09-13.json
```

ครั้งแรกต้อง `duplicate=false` ครั้งที่สอง `duplicate=true` และจำนวน event ไม่เพิ่ม รายงานถูกเขียนด้วย temporary file แล้ว replace

## 3. API Flow

```powershell
$env:OPS_DB = "data/ops.sqlite3"
.\.venv\Scripts\python.exe -m uvicorn ops_report.api:app --host 127.0.0.1 --port 8020
```

เปิด `http://127.0.0.1:8020/docs` แล้วทดลอง:

- `GET /health` — process alive
- `GET /ready` — query database ได้
- `POST /batches` — validate + atomic import
- `GET /reports/2026-09-13` — aggregate จาก DB
- `GET /batches/{batch_id}/audit` — ดู event trail

## 4. Docker

หยุด native API ก่อนเพื่อไม่ให้ port ชน:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail 50 api
```

ข้อมูล Compose อยู่ใน named volume แยกจาก `data/` บน host อย่าใช้ `docker compose down -v` หากต้องการเก็บข้อมูล

## Contracts สำคัญ

- batch ID เดิม + canonical payload เดิม → batch เดิม, `duplicate=true`
- batch ID เดิม + payload ต่าง → `409 BATCH_PAYLOAD_CONFLICT`
- event ID ซ้ำกับ batch อื่น → `409 EVENT_ALREADY_IMPORTED`
- แถวใด invalid → ทั้ง batch ไม่ถูกเขียน
- report คำนวณจาก events ใน DB ไม่รับ aggregate จาก client

## Production Gaps

- ไม่มี authentication/RBAC/TLS/rate limiting
- SQLite เป็น single-host educational choice
- ไม่มี distributed queue หรือ scheduler
- ไม่มี schema migration framework/backup policy
- n8n export เป็นตัวอย่าง local และไม่มี credentials
- ไม่มีเงินจริงหรือ action ภายนอก

อ่าน [RUNBOOK](RUNBOOK.md) ก่อน demo หรือส่งต่อ
