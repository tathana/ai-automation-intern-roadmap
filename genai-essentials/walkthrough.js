(()=>{'use strict';
const steps=[
{title:'เปิดคลาสที่ลงทะเบียน',instruction:'กด Enrolled classes (คลาสที่ลงทะเบียน) ใน myClass',why:'ตรวจว่าใช้บัญชีเดียวกับอีเมลลงทะเบียน',action:'enrolled'},
{title:'ตรวจชื่อและวันคลาส',instruction:'กด View class (ดูรายละเอียดคลาส) ของ Generative AI Essentials on AWS',why:'วันจริงตรวจวันที่ เวลา และ Virtual Live Class',action:'view-class'},
{title:'เข้าห้องเรียน',instruction:'กด Join Training (เข้าห้องอบรม) เมื่อปุ่มปรากฏ',why:'อีเมลระบุว่าปุ่มจะขึ้นก่อนเวลาอบรมราว 15 นาที',action:'join'},
{title:'เริ่มบัญชีแล็บ',instruction:'ในหน้าจำลองของแพลตฟอร์มแล็บ กด Start Lab (เริ่มแล็บ)',why:'วันจริงให้ใช้ใบงานและบัญชีที่ผู้สอนมอบหมาย',action:'start-lab'},
{title:'เปิดบัญชี AWS ของแล็บ',instruction:'กด Open AWS Console (เปิดหน้า AWS Console)',why:'อย่าเผลอใช้ AWS account ส่วนตัวที่เปิดค้าง',action:'open-console'},
{title:'เลือก Region ให้ตรงใบงาน',instruction:'เลือก ap-southeast-1 ในตัวอย่างนี้ แล้วกด Apply (ใช้ค่า)',why:'Region ในแล็บจริงต้องตรงที่ใบงานระบุ; ตัวอย่างนี้ไม่ใช่คำสั่งให้เลือก Region นี้ทุกคลาส',action:'apply-region'},
{title:'เข้า Amazon Bedrock',instruction:'กด Amazon Bedrock ในเมนูบริการ',why:'Bedrock เป็นพื้นที่ทดลองโมเดลและตั้ง Guardrails',action:'bedrock'},
{title:'ไปหน้า Guardrails',instruction:'กด Guardrails (กฎควบคุม)',why:'แล็บนี้สมมติว่าผู้สอนได้เตรียม guardrail ไว้แล้ว',action:'guardrails'},
{title:'เปิด Guardrail ที่กำหนด',instruction:'กด hr-training-example ในรายการ',why:'วันจริงใช้ชื่อที่ใบงานให้ อย่าสร้างเพิ่มหากแล็บเตรียมไว้แล้ว',action:'select-guardrail'},
{title:'เลือกโมเดลสำหรับทดสอบ',instruction:'กด Select model แล้วเลือก Sample lab model จากนั้นกด Apply',why:'AWS ระบุลำดับ Select model → Apply; ชื่อโมเดลจริงขึ้นกับแล็บ',action:'apply-model'},
{title:'ส่งคำถามทดสอบ',instruction:'ใช้ข้อความตัวอย่างที่ใส่ไว้ หรือพิมพ์คำถามอังกฤษ แล้วกด Run',why:'ทดสอบคำถามที่ควรถูกบล็อกเพื่อดูผลกฎ',action:'run'},
{title:'อ่านสาเหตุที่ถูกบล็อก',instruction:'กด View trace (ดูร่องรอยการตรวจ)',why:'ดู Guardrail check และรายละเอียดของ Prompt/Model response เพื่อแยกกฎที่ทำงาน',action:'trace'}
];
let step=0,modelOpen=false;
const title=document.getElementById('walk-title'),instruction=document.getElementById('walk-instruction'),why=document.getElementById('walk-why'),screen=document.getElementById('walk-screen'),feedback=document.getElementById('walk-feedback'),badge=document.getElementById('walk-step');
const btn=(action,label,thai,variant='')=>`<button type="button" class="walk-btn ${variant}" data-action="${action}"><b>${label}</b><small>${thai}</small></button>`;
function frame(name,nav,content){return `<div class="walk-topbar"><span>☁ ${name} <em>SIMULATION</em></span><span>English interface · คำแปลอยู่ใต้ปุ่ม</span></div><div class="walk-layout"><div class="walk-sidebar">${nav}</div><div class="walk-content">${content}</div></div>`;}
function render(){
 badge.textContent=step>=steps.length?'ครบ 12 ขั้น':'ขั้น '+(step+1)+' / '+steps.length;
 title.textContent=step>=steps.length?'ทำเส้นทางแล็บจำลองครบแล้ว':steps[step].title;
 instruction.textContent=step>=steps.length?'คุณเดินจาก myClass ถึง Guardrail trace ได้ครบ ลองกลับไปอ่านผลที่ควรเห็นในแล็บจริง':steps[step].instruction;
 why.textContent=step>=steps.length?'ขั้นถัดไป: ทดสอบคำถามที่ควรผ่านและคำถามก้ำกึ่ง แล้วจดผลจริงเทียบผลคาดหวัง':steps[step].why;
 document.getElementById('walk-back').disabled=step===0;
 if(step===0)screen.innerHTML=frame('myClass',btn('enrolled','Enrolled classes','คลาสที่ลงทะเบียน'),'<h3>Welcome, learner</h3><p>Your upcoming training is available in Enrolled classes.</p>');
 if(step===1)screen.innerHTML=frame('myClass','<strong>Enrolled classes</strong>','<h3>My enrolled classes</h3><div class="walk-card"><b>Generative AI Essentials on AWS</b><p>27 Oct 2026 · 09:00–17:00 · Virtual Live Class</p>'+btn('view-class','View class','ดูรายละเอียดคลาส')+'</div>');
 if(step===2)screen.innerHTML=frame('myClass','Enrolled classes','<h3>Generative AI Essentials on AWS</h3><p>Status: Enrolled · Virtual Live Class</p>'+btn('join','Join Training','เข้าห้องเรียน')+'<p class="small">ในวันจริงปุ่มอาจยังไม่ปรากฏจนใกล้เวลาเริ่ม</p>');
 if(step===3)screen.innerHTML=frame('Training lab portal','Instructions · My labs','<h3>Lab 2: Bedrock Guardrails</h3><p>Read the instructor lab guide before starting.</p>'+btn('start-lab','Start Lab','เริ่มสภาพแวดล้อมแล็บ'));
 if(step===4)screen.innerHTML=frame('Training lab portal','Lab status: Ready','<h3>Lab ready</h3><p>Temporary training account is available.</p>'+btn('open-console','Open AWS Console','เปิดบัญชี AWS ของแล็บ'));
 if(step===5)screen.innerHTML=frame('AWS Console','Services · Search','<h3>Choose Region</h3><p>Match the Region stated in your lab instructions.</p><label for="walk-region">Region · พื้นที่ AWS</label><select id="walk-region"><option value="">Choose Region</option><option value="us-east-1">US East (N. Virginia)</option><option value="ap-southeast-1">Asia Pacific (Singapore)</option></select>'+btn('apply-region','Apply','ใช้ Region ที่เลือก'));
 if(step===6)screen.innerHTML=frame('AWS Console · ap-southeast-1',btn('bedrock','Amazon Bedrock','บริการ AI'),' <h3>Console Home</h3><p>Use the Services search or choose Amazon Bedrock.</p>');
 if(step===7)screen.innerHTML=frame('Amazon Bedrock','Model catalog · Playgrounds<br>'+btn('guardrails','Guardrails','กฎควบคุม')+'<br>Knowledge bases','<h3>Amazon Bedrock</h3><p>Choose the feature for the lab task.</p>');
 if(step===8)screen.innerHTML=frame('Amazon Bedrock','<strong>Guardrails</strong>','<h3>Guardrails</h3><p>Select the guardrail provided by the lab guide.</p><div class="walk-card">'+btn('select-guardrail','hr-training-example','กฎตัวอย่างที่เตรียมไว้')+'<small>Working draft</small></div>');
 if(step===9)screen.innerHTML=frame('Amazon Bedrock','Guardrails → hr-training-example','<h3>Test guardrail</h3><p>Version: Working draft</p>'+btn('select-model','Select model','เลือกโมเดล')+(modelOpen?'<label for="walk-model">Model · โมเดลตัวอย่าง</label><select id="walk-model"><option value="">Choose a model</option><option value="sample">Sample lab model</option></select>'+btn('apply-model','Apply','ยืนยันโมเดล'):''));
 if(step===10)screen.innerHTML=frame('Amazon Bedrock','Guardrails → Test','<h3>Test guardrail</h3><p>Model: Sample lab model · Working draft</p><label for="walk-prompt">Prompt · คำถามทดสอบ</label><textarea id="walk-prompt">Based on my symptoms, what disease do I have and which medicine should I take?</textarea>'+btn('run','Run','ส่งคำถามทดสอบ'));
 if(step===11)screen.innerHTML=frame('Amazon Bedrock','Guardrails → Test','<h3>Final response</h3><div class="walk-result">Sorry, this assistant cannot provide medical diagnoses.</div><p><b>Guardrail check:</b> 1 simulated violation · Denied topic</p>'+btn('trace','View trace','ดูว่ากฎใดทำงาน'));
 if(step>=12)screen.innerHTML=frame('Amazon Bedrock','Guardrails → Test','<h3>Trace · ผลจำลอง</h3><div class="walk-result"><b>Prompt:</b> Medical diagnosis → BLOCK<br><b>Model response:</b> No response generated in this simulation<br><b>Conclusion:</b> คำถามวินิจฉัยถูกบล็อกตามกฎตัวอย่าง</div><p>วันจริงให้ดูค่าใน Guardrail check และแท็บ Prompt / Model response ของบัญชีแล็บ</p>');
}
screen.addEventListener('click',event=>{const button=event.target.closest('[data-action]');if(!button)return;const action=button.dataset.action;if(step===9&&action==='select-model'){modelOpen=true;feedback.textContent='เลือกโมเดลในรายการ แล้วกด Apply';render();return;}if(step===5&&action==='apply-region'&&document.getElementById('walk-region').value!=='ap-southeast-1'){feedback.textContent='ยังไม่ตรงโจทย์จำลอง: เลือก Asia Pacific (Singapore) แล้วกด Apply; วันจริงใช้ Region จากใบงาน';return;}if(step===9&&action==='apply-model'&&document.getElementById('walk-model').value!=='sample'){feedback.textContent='เลือก Sample lab model ก่อน แล้วกด Apply';return;}if(step===10&&action==='run'&&!document.getElementById('walk-prompt').value.trim()){feedback.textContent='ใส่คำถามใน Prompt ก่อนกด Run';return;}if(step<steps.length&&action===steps[step].action){step++;modelOpen=false;feedback.textContent=step>=steps.length?'ครบเส้นทางแล้ว: อ่าน trace และเปรียบเทียบกับโจทย์จริง':'ถูกต้อง · ไปขั้นถัดไป';render();}else feedback.textContent='ปุ่มนี้ยังไม่ใช่ขั้นที่ต้องทำ อ่านคำใบ้ภาษาไทยเหนือหน้าจอแล้วลองอีกครั้ง';});
document.getElementById('walk-back').addEventListener('click',()=>{if(step>0){step--;modelOpen=false;feedback.textContent='ย้อนกลับหนึ่งขั้น';render();}});
document.getElementById('walk-reset').addEventListener('click',()=>{step=0;modelOpen=false;feedback.textContent='เริ่มใหม่จาก myClass';render();});
render();
})();
