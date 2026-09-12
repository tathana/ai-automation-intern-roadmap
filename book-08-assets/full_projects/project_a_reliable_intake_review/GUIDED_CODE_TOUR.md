# Guided Code Tour — Reliable Intake & Review Platform

เอกสารนี้ใช้คู่กับ source จริง จุดประสงค์คืออ่านโค้ดเป็น flow ไม่ใช่จำ syntax ทั้งไฟล์ในครั้งเดียว

## ศัพท์สำคัญก่อนเปิด Code

| ศัพท์ | แปลให้เห็นภาพ |
|---|---|
| API endpoint | ประตูที่ระบบอื่นใช้ส่ง/ขอข้อมูล |
| Schema/model | แบบฟอร์มที่ระบุชื่อ field, type และกฎตรวจ |
| Repository | ชั้นที่รับผิดชอบอ่าน/เขียนฐานข้อมูล |
| Service | ผู้จัดลำดับ use case ว่าต้องเรียกอะไรตามลำดับ |
| Durable queue | รายการงานใน DB ที่ process ปิดแล้วไม่หาย |
| Claim | worker จองงานหนึ่งชิ้นเพื่อเริ่มทำ |
| Lease | สิทธิ์ทำงานที่มีวันหมดอายุ |
| Stale worker | worker เก่าที่กลับมาหลังสิทธิ์หมด |
| Mock provider | ตัวจำลองบริการ AI ที่ให้ผลแน่นอนเพื่อ test |
| Audit trail | ประวัติ action ที่ตรวจย้อนหลังได้ |

## 1. Pydantic Model รับอะไร

เปิด `course/models.py` แล้วหา `Transaction` และ `Resume` ตัวอย่าง model ทำหน้าที่เหมือนแบบฟอร์มหน้าประตู:

```python
class Transaction(BaseModel):
    event_id: str
    user_id: str
    amount_minor: int
    mode: Literal["normal", "transient", "timeout", "invalid_json", "hallucination"]
```

อ่านแบบนี้:

```text
JSON request
  ↓ Pydantic ตรวจชื่อ/type/value
Transaction object
  ↓ .model_dump()
dict ที่ repository รับไปเก็บ
```

`amount_minor` คือจำนวนเงินหน่วยย่อยแบบ integer เช่น 10025 = 100.25 หน่วย วิธีนี้หลีกเลี่ยงความคลาดเคลื่อนของ float แต่ยังต้องกำหนด currency/scale ในระบบจริง

## 2. Factory `create_app()` คืออะไร

ใน `course/api.py`:

```python
def create_app(path=None, clock=time, review_token=None):
    store = Store(path or os.environ.get("CAPSTONE_DB", "data/capstone.sqlite3"))
```

`create_app` คือ **application factory** แทนที่จะสร้าง app ที่เปลี่ยนอะไรไม่ได้ เราส่ง DB ชั่วคราวและนาฬิกาจำลองจาก test ได้:

```text
ตอนรันจริง → path จาก CAPSTONE_DB, clock=time
ตอน test    → tmp_path/test.sqlite3, clock=lambda: 100
```

สิ่งนี้เรียกว่า **dependency injection** ภาษาง่ายคือ “ไม่ให้ฟังก์ชันแอบเลือก dependency ทุกอย่างเอง แต่เปิดช่องให้ caller ส่งของทดแทนได้”

## 3. Intake Endpoint

```python
@app.post("/transactions", status_code=202)
def transaction(payload: Transaction):
    task_id, duplicate = store.ingest_transaction(payload.model_dump(), clock())
    return {"task_id": task_id, "duplicate": duplicate,
            "state": store.task(task_id)["state"]}
```

ไล่ทีละบรรทัด:

1. decorator ผูก HTTP `POST /transactions` และ status `202`
2. `payload: Transaction` สั่ง FastAPI/Pydantic ตรวจ request ก่อนเข้า function
3. `.model_dump()` เปลี่ยน model เป็น dict สำหรับ repository
4. repository คืน `task_id` และบอกว่าเป็น duplicate หรือไม่
5. endpoint ตอบ state ปัจจุบัน ไม่รอ worker

`202` คือ accepted ไม่ใช่ succeeded

## 4. Transaction Intake ใน Repository

แก่นอยู่ใน `ingest_transaction()`:

```text
raw = canonical JSON
BEGIN IMMEDIATE
  ↓ SELECT event_id เดิม
  ├─ payload เดิม → task เดิม, duplicate=True
  ├─ payload ต่าง → Conflict
  └─ event ใหม่ → insert event + task + audit
COMMIT
```

`BEGIN IMMEDIATE` ขอสิทธิ์เขียนตั้งแต่ต้น ช่วยให้การตรวจแล้วเขียนมี boundary ชัดบน SQLite ส่วน `UNIQUE` ใน schema เป็นด่านสุดท้าย ไม่พึ่งความหวังว่า request จะไม่มาพร้อมกัน

## 5. Worker Claim และ Lease

ใน `Store.claim(now, lease_seconds=30)`:

```python
token = uuid.uuid4().hex
connection.execute(
    "UPDATE tasks SET state='running', attempts=attempts+1, "
    "lease_token=?, lease_until=? WHERE id=?",
    (token, now + lease_seconds, row["id"]),
)
```

ภาพที่เกิดขึ้น:

```text
task queued
  ↓ worker A claim เวลา 100
state=running
lease_token=A
lease_until=130
```

ถ้า A หาย หลังเวลา 130 worker B claim ใหม่ด้วย token B ได้ เวลา A กลับมา `finish()` จะ update ด้วยเงื่อนไข token A ซึ่งไม่ตรงแล้ว จึงเขียนทับ B ไม่ได้

## 6. Mock AI และ Provider Failure

ใน `service.py`, `mock_generate(task)` อ่าน `mode` เพื่อคืนผลแน่นอน:

```text
normal        → output ตาม contract
transient     → fail สอง attempt แรกแล้วสำเร็จ
timeout       → fail จน budget หมด
invalid_json  → คืน "{" ให้ parse ไม่ได้
hallucination → คืน quote ที่ไม่มีใน Resume
```

นี่เรียกว่า **deterministic mock** เพราะ input/mode เดิมให้ผลเดิม ทำให้ test failure path ได้โดยไม่เสียเงินและไม่ขึ้นกับ model จริง

## 7. `process_one()` อ่านอย่างไร

```python
task = store.claim(clock())
if task is None:
    return False
```

ถ้าไม่มีงาน `False` แปลว่า “รอบนี้ไม่มีงาน” ไม่ใช่ processing fail

```python
raw = provider(task)
result = json.loads(raw)
```

provider คืน raw string ก่อน แล้ว application parse เอง จึงทดสอบ invalid JSON ได้

สำหรับ Resume:

```python
if claim["quote"] not in task["payload"]["document_text"]:
    raise ValueError("unsupported_claim")
```

นี่คือ lexical evidence check: quote ต้องปรากฏตรงใน source ช่วยบล็อกการแต่งข้อความ แต่ยังไม่พิสูจน์ความหมายเชิงลึก จึงติด `validation_level='lexical_only'` และส่งคน review

## 8. Retry State

```text
TemporaryFailure
  ↓ attempts < 3
retry_pending + available=now+backoff
  ↓ worker รอบก่อนเวลานัด claim ไม่ได้
attempt 3 ยัง fail
  ↓ failed + review/fallback
```

คำว่า **bounded retry** หมายถึงมีเงื่อนไขและจุดจบ ไม่ใช่ `while True` ลองใหม่ตลอด

## 9. Human Review

`authorize()` ตรวจ Bearer token ด้วย `hmac.compare_digest` และปิด review endpoint ด้วย `503` หากไม่มี token ที่ตั้งค่าเหมาะสม จากนั้น `Store.decide()` ใช้ `decision_id` ป้องกัน double submit:

```text
decision_id เดิม + body เดิม → คืน decision เดิม
decision_id เดิม + body ต่าง → 409 conflict
```

นี่คือ idempotency ของการตัดสินใจ ไม่ใช่ authentication production ตัว token ยังเป็นเพียง local demo

## 10. อ่าน Tests เป็นคำอธิบาย Behavior

เริ่มจากชื่อ test:

- `test_durable_dedup_and_conflict` — reopen store แล้วยัง dedup ได้
- `test_atomic_concurrent_intake` — request พร้อมกันสร้างงานเดียว
- `test_expired_worker_cannot_overwrite` — worker เก่าเขียนทับไม่ได้
- `test_bounded_retry` — retry มี budget
- `test_hr_evidence_and_human_review` — AI output ต้องผ่าน evidence/review

อ่าน Arrange → Act → Assert:

```text
Arrange: สร้าง store/payload
Act: เรียก use case
Assert: ตรวจ response + state + side effect
```

## 11. Docker และ n8n อยู่ชั้นไหน

Docker ทำให้ API/worker รันจาก environment ที่ประกาศได้ Compose เชื่อม process, network และ volume ส่วน n8n เป็น client/orchestrator ที่เรียก API ทั้งสองอย่างไม่ควรเปลี่ยนกฎใน repository/service

## ลองอธิบายเองหลังอ่าน

1. เพราะอะไร API ตอบ 202 ก่อน worker ทำเสร็จ
2. unique constraint ต่างจาก `SELECT` ก่อน insert อย่างไร
3. lease token ป้องกันปัญหาใด
4. schema validation กับ evidence validation ต่างกันอย่างไร
5. ทำไม `succeeded` ของ Resume ไม่ใช่ “ผู้สมัครผ่าน”
