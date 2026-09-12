# Capstone Lab — Native ก่อน แล้วค่อย Compose

ถ้าเพิ่งเรียน API/worker/transaction และเปิด source แล้วรู้สึกว่าโค้ดแน่น ให้เริ่ม [GUIDED_CODE_TOUR.md](GUIDED_CODE_TOUR.md) ก่อน เอกสารนั้นแปลศัพท์และไล่ request หนึ่งก้อนผ่าน `models.py → api.py → repository.py → service.py → worker.py` ทีละช่วง

## ขอบเขต

ระบบ local-only สำหรับข้อมูลสังเคราะห์ มี API, worker, SQLite queue, mock AI, audit และ review decision ไม่มีการเรียก paid API ไม่มีอีเมลหรือการจ้างงานอัตโนมัติ เว็บบทเรียนไม่ได้ host backend นี้ ต้องดาวน์โหลด ZIP แล้วรันในเครื่อง

## 1. เตรียม environment

เปิด PowerShell ใน folder `capstone` หลังแตก ZIP ใช้ Python 3.12 เป็น baseline ของ Docker/CI (การตรวจบน host ระบุเวอร์ชันจริงใน Verification)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

ไม่ต้อง activate ก็ได้ เพราะระบุ interpreter ตรง ๆ ถ้าใช้ `python` ในคำสั่งถัดไป ให้แน่ใจว่าเป็น environment ที่ติดตั้ง packages แล้ว ไม่ใช้ global interpreter คนละตัวสลับกัน

### ถ้ายังไม่พร้อมเปิดหลาย terminal

ทดลอง walkthrough ก่อน API ได้โดยไม่ต้องตั้ง token หรือเปิด Docker:

```powershell
.\.venv\Scripts\python.exe learning_walkthrough.py state
.\.venv\Scripts\python.exe learning_walkthrough.py retry
.\.venv\Scripts\python.exe learning_walkthrough.py lease
.\.venv\Scripts\python.exe learning_walkthrough.py review
.\.venv\Scripts\python.exe learning_walkthrough.py transaction
.\.venv\Scripts\python.exe learning_walkthrough.py hr
```

แต่ละคำสั่งใช้ DB ชั่วคราวของตัวเองและตรวจผลด้วย assertions เมื่อผ่านจะจบด้วย PASS อ่านโค้ดคู่กับบท 06–08 และ 12–13 เพื่อเห็นว่าเกิดอะไรขึ้น ข้อมูลนี้จะไม่ไปปรากฏใน API ที่เปิดภายหลัง เพราะไม่ได้ใช้ DB ไฟล์เดียวกัน และไม่ได้จำลอง network จริง

## 2. เปิด API — terminal A

```powershell
$env:CAPSTONE_DB = "data/capstone.sqlite3"
$env:REVIEW_TOKEN = (& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))")
.\.venv\Scripts\python.exe -m uvicorn course.api:app --host 127.0.0.1 --port 8015
```

คำสั่งสร้าง token แบบสุ่มเก็บใน environment ของ terminal นี้ ห้าม commit/แชร์ค่า API อ่าน token ตอนเริ่ม process ถ้าเปลี่ยนค่าต้อง restart API ส่วน review เป็นตัวเลือกสำหรับการทดลองประมวลผล แต่ถ้าไม่ตั้ง token review endpoints จะตอบ 503 เพื่อไม่เปิดใช้แบบไม่มีการป้องกัน

## 3. เปิด worker — terminal B ใน folder เดียวกัน

```powershell
$env:CAPSTONE_DB = "data/capstone.sqlite3"
.\.venv\Scripts\python.exe -m course.worker
```

สอง terminal ต้องชี้ DB ไฟล์เดียวกัน Relative path คิดจาก directory ที่รัน ไม่ใช่ตำแหน่งไฟล์ Python ถ้าเปิด terminal คนละ folder ให้ใช้ absolute DB path เดียวกัน

## 4. ทดลอง — terminal C

```powershell
.\.venv\Scripts\python.exe demo.py transaction
.\.venv\Scripts\python.exe demo.py hr
.\.venv\Scripts\python.exe demo.py transaction --mode transient
.\.venv\Scripts\python.exe demo.py hr --mode hallucination
```

แต่ละคำสั่งสร้าง ID สังเคราะห์ใหม่ แล้วส่ง payload เดิมซ้ำหนึ่งรอบเพื่อยืนยัน task เดียว Transaction normal จบ succeeded และรายการเข้าเกณฑ์มี review; transient สำเร็จที่ attempt 3; hallucination HR จบ needs_review ไม่เผย validated output ที่ใช้ไม่ได้

ดู API docs ที่ `http://127.0.0.1:8015/docs` และสุขภาพที่ `/health` **202 intake ไม่ใช่ผลสำเร็จ** script จะ poll task ให้ ส่วน `--once` ของ worker ทำได้มากสุดหนึ่ง attempt ไม่ได้รอ retry ครบเอง

## 5. ทดลอง review

เก็บ token เดียวกับ terminal A ไว้ใน session ที่ส่ง request อย่างปลอดภัย ตัวอย่างต่อไปนี้ใช้ `$env:REVIEW_TOKEN` ที่ตั้งไว้แล้ว ไม่ใช่ให้ paste token ลง source:

```powershell
$reviewHeaders = @{ Authorization = "Bearer $env:REVIEW_TOKEN" }
Invoke-RestMethod http://127.0.0.1:8015/reviews -Headers $reviewHeaders
$decisionBody = @{ decision_id="D-local-001"; outcome="verified"; note="Checked synthetic evidence" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8015/reviews/1/decision -Method Post -Headers $reviewHeaders -ContentType "application/json" -Body $decisionBody
```

เปลี่ยนเลข `1` เป็น task ID ที่มี review ของคุณ อย่าคัดลอก ID โดยไม่ตรวจ การส่ง decision เดิมซ้ำคืนผลเดิม เปลี่ยนเนื้อหาใน decision ที่ตัดสินแล้วคืน 409 ไม่มี endpoint แก้ decision ใน lab รุ่นนี้

## 6. Docker Compose — ทางเลือกหลัง native

หยุด native API/worker ด้วย Ctrl+C ก่อนเพื่อไม่ชน port และไม่สับสน DB สองชุด ตรวจ Docker Engine พร้อม จากนั้น:

```powershell
Copy-Item .env.example .env
# เปิด .env ด้วย editor แล้วแทน REVIEW_TOKEN ด้วยค่าสุ่มของเครื่อง
docker compose config --quiet
docker compose up --build -d api worker
docker compose ps
docker compose logs --tail 50 api worker
```

รัน demo จาก host ได้เหมือนเดิม DB แบบ Compose อยู่ใน named volume ไม่ใช่ `data/` ของ native การย้าย mode จึงไม่ได้ย้ายข้อมูลให้อัตโนมัติ

ทดสอบ persistence ด้วยส่งงาน → จด task ID → `docker compose restart api worker` → GET task เดิม อย่าใช้ `down -v` เพราะเป็นการขอลบ volume หลังเรียนใช้ `docker compose stop api worker` หยุดโดยไม่ลบข้อมูล

n8n profile แยกไว้เพื่อไม่ชน instance เดิม ค่า image ใน example เป็น compatibility baseline เก่า **ไม่ใช่เวอร์ชันที่รับรอง security ปัจจุบัน** ตรวจ release/security ของ n8n และกำหนด image ที่อนุมัติก่อนเปิด profile หรือใช้ n8n native เดิมกับ workflow host ที่ให้มา

## ไฟล์ที่ควรเปิดประกอบ

- [models.py](course/models.py): input contract
- [repository.py](course/repository.py): durable queue, transaction, lease
- [service.py](course/service.py): mock และ output validation
- [tests](tests/test_capstone.py): ตัวอย่าง Arrange/Act/Assert
- [Dockerfile](Dockerfile) และ [Compose](compose.yaml)
- [Runbook](RUNBOOK.md): เมื่อค้าง/ผิดปกติ

Dependencies กำหนดช่วงเวอร์ชัน ไม่ใช่ lockfile ที่ pin ทุก dependency ขอบเขตความถูกต้องคือเวอร์ชันและ checks ที่บันทึกใน Verification ไม่รับรองการ resolve ทุกวันในอนาคต
