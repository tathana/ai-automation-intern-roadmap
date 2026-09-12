# Guided Code Tour — Daily Operations Report Automation

โปรเจกต์นี้ไม่มี AI เพราะโจทย์เป็นกฎและการรวมตัวเลขที่กำหนดชัด การใช้ Python/SQL deterministic ทำให้ผลซ้ำได้ ทดสอบง่าย และอธิบายยอดได้

## ศัพท์ก่อนเปิด Code

| ศัพท์ | ความหมายในระบบนี้ |
|---|---|
| Parsing | แปลง syntax ของ CSV/JSON ให้เป็น Python data |
| Validation | ตรวจ type/range/allowed value ตาม contract |
| Domain rule | กฎของงาน เช่น event ID ห้ามซ้ำ |
| Atomic | สำเร็จทั้งก้อนหรือล้มทั้งก้อน |
| Canonical payload | JSON รูปมาตรฐานที่ใช้ hash/เปรียบเทียบ |
| Idempotency | ส่ง batch เดิมซ้ำแล้วจำนวน event ไม่เพิ่ม |
| Aggregate | รวมหลายแถวเป็น count/sum/group |
| Repository | ชั้นที่รวม SQL และ transaction |
| Application factory | ฟังก์ชันสร้าง app ที่เปลี่ยน DB ใน test ได้ |

## 1. CSV หนึ่งแถวเดินทางอย่างไร

```text
CSV string values
  ↓ cli.load_records()
dict และแปลง amount_minor เป็น int
  ↓ BatchRequest(...)
Pydantic Event objects
  ↓ service.accept_batch()
repository.import_batch()
  ↓ SQLite transaction
batches + events + audit
```

CSV parser คืนทุก field เป็น string จึงมีบรรทัด:

```python
dict(row) | {"amount_minor": int(row["amount_minor"])}
```

`dict(row)` copy แถวเดิม ส่วน operator `|` รวม dict โดยค่าฝั่งขวาทับ `amount_minor` ให้เป็น integer ถ้าค่าเป็น `"ten"`, `int()` จะ fail ก่อนถึง DB

## 2. Pydantic Model ทำอะไร

ใน `models.py`:

```python
class Event(BaseModel):
    event_id: str
    occurred_at: datetime
    amount_minor: int = Field(ge=0, le=1_000_000_000)
    status: Literal["success", "failed"]
    channel: str
```

อ่านเป็นแบบฟอร์ม:

```text
event_id       ต้องเป็นข้อความตาม pattern
occurred_at    ต้องแปลงเป็นวันที่เวลาได้
amount_minor   ต้องเป็น int และอยู่ในช่วง
status         เลือกได้เพียง success/failed
channel        ต้องเป็นชื่อสั้นตาม pattern
```

Validator ของ `amount_minor` ตรวจเพิ่มว่า input ต้องเป็น integer จริง ไม่รับ JSON string `"100"` แบบเงียบ ๆ แม้ Pydantic ปกติอาจช่วยแปลง type ได้

## 3. ทำไม Batch ตรวจ Event ID ซ้ำก่อน DB

```python
keys = [record.event_id for record in self.records]
if len(keys) != len(set(keys)):
    raise ValueError("duplicate event_id inside batch")
```

List เก็บทุก ID ส่วน set เก็บค่าไม่ซ้ำ ถ้าจำนวนไม่เท่ากันแปลว่ามี ID ซ้ำใน request เดียว การตรวจตรงนี้ให้ error อ่านง่าย ส่วน `PRIMARY KEY` ใน DB ยังเป็นด่านป้องกันจริงอีกชั้น

## 4. Canonical Payload และ Hash

```python
raw = json.dumps(
    batch.model_dump(mode="json"),
    sort_keys=True,
    ensure_ascii=False,
    separators=(",", ":"),
)
digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

ทีละขั้น:

1. `model_dump(mode="json")` ทำ datetime ให้เป็นค่าที่ JSON เขียนได้
2. `sort_keys=True` ทำลำดับ key แน่นอน
3. separators ตัด whitespace ที่ไม่เกี่ยวกับความหมาย
4. encode เป็น bytes เพราะ SHA-256 รับ bytes
5. `hexdigest()` คืน fingerprint 64 ตัวอักษร

Hash ใช้ตรวจ payload equality อย่างคงที่ ไม่ใช่ encryption และไม่ควรใช้ซ่อน PII

## 5. Atomic Import

ใน `repository.import_batch()`:

```text
BEGIN IMMEDIATE
  ↓ มี batch_id เดิมไหม
  ├─ hash เดิม → duplicate
  ├─ hash ต่าง → BatchConflict
  └─ ใหม่ → ตรวจ event collision
              ↓
       insert batch
       insert events ทั้งหมด
       insert audit
COMMIT
```

ถ้า insert event แถวที่สามพัง context manager จะ rollback ทำให้แถวหนึ่งและสองไม่ค้างอยู่ นี่คือความหมายของ **all-or-nothing transaction**

## 6. ทำไม Event ID ซ้ำข้าม Batch เป็น Conflict

`batch_id` บอกการส่งหนึ่งก้อน ส่วน `event_id` บอกเหตุการณ์ทางธุรกิจหนึ่งรายการ หาก `E1` เคยอยู่ B1 แล้ว B2 ส่ง E1 อีก ระบบไม่รู้ว่าเป็นการ copy ผิดหรือแก้ข้อมูล จึงปฏิเสธด้วย `EVENT_ALREADY_IMPORTED` แทนการนับสองครั้ง

## 7. SQL Report อ่านอย่างไร

```sql
SUM(CASE WHEN status='success' THEN 1 ELSE 0 END)
```

แปลเป็น flow:

```text
แต่ละ row
  ├─ status success → ให้ค่า 1
  └─ อื่น            → ให้ค่า 0
SUM ทุกแถว → จำนวน success
```

ส่วนยอดเงิน:

```sql
SUM(CASE WHEN status='success' THEN amount_minor ELSE 0 END)
```

นับ amount เฉพาะรายการสำเร็จ `GROUP BY channel` แบ่งกองตามช่องทาง แล้ว query รวมไม่ group ให้ยอดรวมทั้งวัน

## 8. API Factory และ Endpoint

```python
def create_app(path=None):
    store = Store(path or os.environ.get("OPS_DB", "data/ops.sqlite3"))
```

Test ส่ง `tmp_path/api.sqlite3` จึงไม่แตะ DB จริง ส่วน runtime อ่าน `OPS_DB`

```python
@app.post("/batches", response_model=BatchAccepted, status_code=202)
def create_batch(batch: BatchRequest):
    return accept_batch(store, batch)
```

FastAPI parse/validate ก่อนเข้า function, service สั่ง repository, `response_model` ตรวจ output อีกครั้ง

## 9. Atomic Report File

`write_report_atomic()` เขียน temporary file ใน directory เดียวกันก่อน:

```text
daily-xxxx.tmp
  ↓ json.dump + flush + fsync
os.replace
  ↓
daily.json
```

ถ้า serialize fail ก่อน replace ไฟล์เป้าหมายเดิมยังอยู่ วิธีนี้ไม่ใช่ backup แต่ลด output ครึ่งไฟล์

## 10. Tests กำลังพิสูจน์อะไร

- CSV loader + Pydantic: parser และ contract ต่อกันได้
- restart: สร้าง `Store(path)` ใหม่แล้วยังพบ batch เดิม
- duplicate/conflict: safe replay ไม่เพิ่ม row และ payload เปลี่ยนถูกบล็อก
- event collision: batch ที่สองไม่ถูกเขียนครึ่งเดียว
- report: count/sum/group ถูกต้อง
- API: status `202/409/422/404` สอดคล้อง behavior

อย่าดูเพียง `5 passed` ให้เปิด assertion แล้วบอกว่ามันป้องกัน failure แบบใด

## 11. Docker และ n8n

Docker ทำให้ API รันบน Python/dependencies ที่ประกาศ Compose ผูก port `127.0.0.1:8020` และ volume `/data` ส่วน n8n ส่ง BatchRequest เข้า API เท่านั้น กฎ dedup/aggregate ยังอยู่ Python/SQLite

## ลองตอบหลังอ่าน

1. parsing กับ validation ต่างกันอย่างไร
2. ทำไมต้องมีทั้ง Pydantic duplicate check และ DB primary key
3. batch hash ป้องกันเหตุการณ์ใด
4. transaction ทำให้ batch ไม่เข้าครึ่งเดียวอย่างไร
5. ทำไม report นี้ไม่ต้องใช้ LLM
