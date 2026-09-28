# AgentOps Workshop Field Notes

เว็บภาษาไทยแบบ static ในโปรเจกต์ learning portal เดิม ไม่ใช้ AWS credentials ไม่มี AWS SDK หรือคำสั่งเรียก cloud และไม่มี analytics

## เปิดเว็บ

จากโฟลเดอร์ roadmap-site:

```sh
python -m http.server 8771 --bind 127.0.0.1
```

เปิด http://127.0.0.1:8771/agentops/ (ต้องเสิร์ฟจากราก roadmap-site เนื่องจาก assets ใช้ root-relative paths)

หากเครื่องใช้คำสั่ง python3 ให้แทน python ด้วย python3 ไม่ต้องติดตั้ง npm packages เพื่อเปิดเว็บ

## โครงสร้าง

- agentops/index.html — สรุปและขอบเขตหลักฐาน
- basics.html — เริ่มจากศูนย์: Terminal บน Mac/แล็บ, shell, AWS CLI, ตัวแปร, JSON และการอ่าน error; ตัวอย่างคัดลอกไม่เรียก AWS จริง
- glossary.html — 22 คำพร้อมค้น
- modules.html — บทเรียนพื้นฐาน 9 หัวข้อ: API, Agent/Tool, Git/Version, CI/CD, Evaluation, AWS, Policy, Observability และอ่านภาษาอังกฤษ (แทนแผนที่ Module ที่ไม่มีข้อมูล)
- simulator.html — 3 เหตุการณ์แบบทีละขั้น
- debug.html — policy, spans, NEW_VERSION checklist
- talk.html — บทพูดและคำถาม
- quiz.html — 12 ข้อพร้อมเหตุผล
- app.js, data.js, style.css — assets ของเว็บ
- ../tools/agentops-data.json — เนื้อหาที่ใช้สร้างและข้อมูลจำลอง
- ../tools/build-agentops.mjs — generator

แก้เนื้อหาแล้วสร้างใหม่จากราก:

```sh
node tools/build-agentops.mjs
```

## ข้อจำกัดหลักฐาน

บทเรียนพื้นฐานเป็นเนื้อหาอธิบายแนวคิด ไม่อ้างหมายเลข Module ของ AWS และตัดแผนที่ Module ที่ไม่มีข้อมูลออกแล้ว ข้อมูลผลทดลองที่เก็บไว้ในส่วนแก้ปัญหา/บทพูดมาจากข้อความผู้ใช้เล่าภาพ ไม่ใช่การตรวจ AWS ล่าสุด ไม่เผยแพร่ลิงก์ join/access code หรือ identifiers จริง

ต้องตรวจจริง: endpoint-version mapping, request tool/target, policy association/scope/context/decision, Lambda/tool result, input spans และ log source, pipeline execution/prod approval, online evaluation configuration การมีคำตอบ Refund processed ไม่ยืนยันธุรกรรม

## พฤติกรรมใน browser

อ่านและ checklist เก็บใน localStorage key agentops-field-notes-v1 ไม่ส่งเซิร์ฟเวอร์ หาก storage ใช้ไม่ได้ยังอ่านและเล่นได้แต่ไม่รับประกันการจำสถานะ Quiz อยู่ในหน่วยความจำหน้านั้น รีโหลดเริ่มใหม่ ช่องติ๊ก checklist คืออ่าน/เตรียมตรวจ ไม่ใช่ AWS ผ่านแล้ว

ลิงก์เอกสาร AWS เปิดภายนอกเมื่อผู้ใช้กดเท่านั้น ไม่มีการดึง AWS หรือ service ภายนอกอัตโนมัติ ข้อมูล simulation และ quiz ฝังใน data.js ไม่ใช่ผล AWS
