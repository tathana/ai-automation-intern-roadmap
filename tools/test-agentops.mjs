import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const dir=path.join(root,'agentops');
const files=fs.readdirSync(dir).filter(f=>f.endsWith('.html'));
assert.equal(files.length,8);
let links=0;
for(const file of files){
const html=fs.readFileSync(path.join(dir,file),'utf8');
assert.equal((html.match(/<h1>/g)||[]).length,1,file);
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(new Set(ids).size,ids.length,'duplicate ids '+file);
for(const [,href] of html.matchAll(/(?:href|src)="([^"]+)"/g)){
if(/^https:/.test(href))continue;
const [raw,anchor]=href.split('#');let target=raw?path.join(root,raw):path.join(dir,file);
if(!path.extname(target))target=path.join(target,'index.html');
assert(fs.existsSync(target),'Missing '+href+' in '+file);
if(anchor){const dest=fs.readFileSync(target,'utf8');assert(dest.includes('id="'+anchor+'"'),'Missing anchor '+href);}links++;
}
assert(!/access-code=|arn:aws|[0-9]{12}/.test(html),'identifier-like data '+file);
}
const app=fs.readFileSync(path.join(dir,'app.js'),'utf8');
assert(!/\bfetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket|https:/.test(app),'unexpected network API');
const d=JSON.parse(fs.readFileSync(path.join(root,'tools/agentops-data.json'),'utf8'));
assert.equal(d.quiz.length,12);assert.equal(d.cases.length,3);
for(const q of d.quiz){assert(q[2]>=0&&q[2]<q[1].length);assert(q[3].length>20);}
assert(d.cases.find(c=>c.id==='high').observed.includes('ยังไม่ยืนยัน'));
assert(d.cases.find(c=>c.id==='eligible').observed.includes('ข้อมูลสร้าง'));
assert(d.evidence.some(x=>x.join(' ').includes('ยังไม่ได้สร้าง')));
console.log('PASS 8 pages, '+links+' local links/anchors/assets, no duplicate IDs, no identifier-like data or network APIs, scenario/quiz integrity');
