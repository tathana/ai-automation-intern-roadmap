import fs from 'node:fs/promises';
export async function foundations({panel,detail,e}){
const first=JSON.parse(await fs.readFile(new URL('agentops-foundations.json',import.meta.url),'utf8'));
const extra=JSON.parse(await fs.readFile(new URL('agentops-foundations-extra.json',import.meta.url),'utf8'));
const lessons=[...first,...extra];
let html=panel('เริ่มเรียนโดยไม่ต้องมีพื้นฐาน','<p>นี่คือบทเรียนเรียงตามความเข้าใจ ไม่ใช่หมายเลข Module ของ AWS อ่านครั้งละ 1–2 หัวข้อแล้วลองตอบท้ายหัวข้อ เวลาน้อยให้เริ่ม 1, 2 และ 4 เพื่อเห็นภาพ agent กับ CI/CD</p><div class="controls">'+lessons.map((x,i)=>'<a href="#lesson-'+i+'">'+e(x.title)+'</a>').join('')+'</div>');
html+=lessons.map((x,i)=>'<section class="panel" id="lesson-'+i+'"><span class="badge expected">บทเรียนพื้นฐาน · ตัวอย่างเพื่ออธิบาย</span><h2>'+e(x.title)+'</h2>'+x.text.map(p=>'<p>'+e(p)+'</p>').join('')+'<div class="sim-step"><h3>ตัวอย่างเชื่อมภาพ</h3><p>'+e(x.example)+'</p></div><div class="expected-box" style="padding:20px;border-radius:10px"><h3>เจอภาษาอังกฤษแบบนี้ ให้อ่านว่า…</h3><p lang="en"><strong>'+e(x.english[0])+'</strong></p><p>'+e(x.english[1])+'</p><p>'+e(x.english[2])+'</p></div>'+detail('ลองตอบ: '+e(x.question),'<p>'+e(x.answer)+'</p>')+'</section>').join('');
html+=panel('เล่าระบบใน 30 วินาที','<p>“ระบบนี้ใช้โมเดลช่วยเลือกเครื่องมือเพื่อทำงานครับ ตอนเปลี่ยนเวอร์ชันมี pipeline ตรวจ tests และ evaluation ก่อนส่งไป staging/prod ส่วนตอนรับคำขอ Runtime รัน agent เครื่องมือทำงานภายใต้สิทธิ์และ policy แล้วใช้ log/trace ดูว่าเกิดอะไรที่ขั้นไหนครับ”</p><p>อ่านต่อ: <a href="/agentops/basics.html">Terminal และ AWS CLI</a> → <a href="/agentops/simulator.html">ห้องจำลอง</a> → <a href="/agentops/quiz.html">แบบทบทวน</a></p>');
return html;
}

