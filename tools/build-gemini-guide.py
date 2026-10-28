"""Build static Thai reading pages. Build-only dependency: mistune==3.1.3."""
from pathlib import Path
import html
import json
import re
import zipfile
import mistune

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'gemini-agent-platform'
LESSONS = [
    ('01-overview', 'ภาพรวมแพลตฟอร์ม', 'Build · Scale · Govern · Optimize', '9:42'),
    ('02-setup', 'เตรียมเครื่องและสร้าง Agent ตัวแรก', 'Python · uv · ADK · Google Cloud · ADC', '25:03'),
    ('03-website-agent', 'สร้างและ Deploy เว็บไซต์ด้วย Agent', 'Instructions · Tools · Firebase Hosting', '14:53'),
    ('04-deployment', 'Deploy ตัว Agent ขึ้นคลาวด์', 'Manifest · Service Account · Unified Tool', '18:53'),
    ('05-security', 'เพิ่มความปลอดภัยด้วย Model Armor', 'Prompt Injection · Confidence · Enforcement', '8:56'),
    ('06-observability', 'Observability และ Traces', 'OpenTelemetry · IAM · Metrics · Spans', '9:39'),
]
e = html.escape

class Renderer(mistune.HTMLRenderer):
    def __init__(self):
        super().__init__(escape=True)
        self.sections = []

    def heading(self, text, level, **attrs):
        if level == 1:
            return f'<h1>{text}</h1>\n'
        anchor = 'summary' if text == 'สรุปท้ายเรื่อง' else f'section-{len(self.sections) + 1}'
        self.sections.append((level, anchor, text))
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'

    def table(self, text):
        return f'<div class="table-wrap" role="region" aria-label="ตารางประกอบบทเรียน" tabindex="0"><table>{text}</table></div>\n'

def shell(title, body, description):
    return f'''<!doctype html>
<html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{e(description)}"><title>{e(title)} | AI & Automation Knowledge</title>
<link rel="stylesheet" href="style.css"></head><body>
<a class="skip" href="#main">ข้ามไปเนื้อหา</a>
<header class="topbar"><a href="../index.html">← คลังความรู้หลัก</a><a href="index.html">Gemini Agent Platform · 6 บท</a></header>
{body}<footer>เรียบเรียงภาษาไทยจากข้อความถอดเสียงที่ผู้ใช้ส่งมา · เนื้อหาสำหรับทบทวนและอ้างอิง</footer></body></html>'''

search = []
cards = []
full = []
for n, (slug, title, tags, duration) in enumerate(LESSONS, 1):
    raw = (DEST / f'{slug}.md').read_text(encoding='utf-8')
    full.append(raw)
    renderer = Renderer()
    body = mistune.create_markdown(renderer=renderer, plugins=['table'])(raw)
    toc = ''.join(f'<a class="depth-{level}" href="#{anchor}">{text}</a>' for level, anchor, text in renderer.sections)
    course_nav = ''.join(f'<a href="{s}.html" {"aria-current=page" if s == slug else ""}>{i:02d} · {e(t)}</a>' for i, (s,t,_,_) in enumerate(LESSONS, 1))
    previous = f'<a href="{LESSONS[n-2][0]}.html">← บทก่อนหน้า</a>' if n > 1 else '<a href="index.html">← สารบัญหลักสูตร</a>'
    following = f'<a href="{LESSONS[n][0]}.html">บทถัดไป →</a>' if n < 6 else '<a href="index.html">กลับสารบัญ →</a>'
    markup = f'''<div class="reader-layout"><aside><details open><summary>บทเรียนทั้ง 6 คลิป</summary><nav aria-label="บทเรียน">{course_nav}</nav></details>
    <details class="toc" open><summary>สารบัญบทนี้</summary><nav aria-label="หัวข้อในบท">{toc}</nav></details></aside>
    <main id="main" class="article"><div class="eyebrow">บทที่ {n:02d} / 06 · คลิป {duration} นาที</div>
    <div class="reading-actions"><a href="#summary">ข้ามไปสรุปท้ายเรื่อง ↓</a><a href="{slug}.md" download>ดาวน์โหลด Markdown</a><button type="button" onclick="window.print()">พิมพ์ / บันทึก PDF</button></div>
    {body}<nav class="pager" aria-label="เปลี่ยนบท">{previous}{following}</nav></main></div>'''
    (DEST / f'{slug}.html').write_text(shell(title, markup, f'บทที่ {n}: {title} — เนื้อหาละเอียดตามเวลาและสรุปท้ายเรื่อง'), encoding='utf-8')
    plain = re.sub(r'[#*`>|]', '', raw)
    search.append(dict(title=title, text=plain, slug=slug))
    cards.append(f'''<a class="card" data-lesson="{n-1}" href="{slug}.html"><div class="eyebrow">คลิป {n:02d} · {duration} นาที</div><h2>{e(title)}</h2><p>{e(tags)}</p><p class="match" hidden></p><span class="open">อ่านเนื้อหาและสรุป →</span></a>''')

index_body = f'''<section class="hero"><div class="eyebrow">VIDEO STUDY NOTES · ภาษาไทย</div><h1>Gemini Enterprise<br>Agent Platform</h1><p>จาก Agent ตัวแรกบนเครื่อง สู่การ Deploy กำกับดูแล และติดตามระบบบนคลาวด์</p><div class="chips"><span>6 คลิป</span><span>ประมาณ 87 นาที</span><span>เนื้อหาละเอียด + สรุปทุกบท</span></div></section>
<main id="main" class="course-home"><section class="intro"><h2>อ่านตามลำดับ หรือค้นหัวข้อที่ต้องใช้</h2><p>รวมเนื้อหาฉบับละเอียดที่เรียบเรียงจากบทสนทนาเดิม ทั้งช่วงเวลา ตาราง คำสั่งตัวอย่าง คำอธิบายเพิ่มเติม และสรุปท้ายเรื่อง แยกเป็น 6 บทตามคลิป</p>
<div class="source-note"><strong>ที่มาและขอบเขต</strong><p>เรียบเรียงจากข้อความถอดเสียงที่ผู้ใช้ส่งมา ไม่ใช่เอกสารทางการของ Google ชื่อผลิตภัณฑ์ เมนู โมเดล คำสั่ง และค่าตั้งค่าที่ไม่ชัดเจนยังคงมีหมายเหตุไว้ในแต่ละบท</p><a href="https://www.youtube.com/watch?v=5QeVww6NrCM" target="_blank" rel="noopener noreferrer">ดูคลิปแรกบน YouTube ↗</a> · <a href="https://youtube.com/playlist?list=PLNVctHyaujto" target="_blank" rel="noopener noreferrer">เพลย์ลิสต์ที่ผู้ใช้ส่งมา ↗</a></div>
<div class="course-flow" aria-label="ลำดับการเรียน"><span>ภาพรวม</span><span>→ Build</span><span>→ Scale</span><span>→ Govern</span><span>→ Optimize</span></div>
<label for="search"><strong>ค้นในเนื้อหาทั้ง 6 บท</strong></label><input id="search" type="search" placeholder="เช่น ADC, Firebase, Model Armor, Trace" autocomplete="off"><p id="search-status" role="status" aria-live="polite">แสดง 6 บท</p></section>
<section class="grid" aria-label="บทเรียน">{''.join(cards)}</section><p id="empty" hidden>ไม่พบหัวข้อที่ค้น ลองใช้คำที่สั้นลงหรือคำภาษาอังกฤษ</p>
<section class="downloads"><h2>เก็บไว้อ่านต่อ</h2><p>แต่ละบทมีสารบัญ ลิงก์ไปสรุป และปุ่มพิมพ์เพื่อบันทึกเป็น PDF อ่านได้โดยไม่ต้องเข้าสู่ระบบ</p><a class="button" href="gemini-agent-platform-notes.zip" download>ดาวน์โหลด Markdown ครบ 6 บท</a></section></main>
<script id="search-data" type="application/json">{json.dumps(search, ensure_ascii=False).replace('<', chr(92)+'u003c')}</script><script src="search.js" defer></script>'''
(DEST / 'index.html').write_text(shell('Gemini Enterprise Agent Platform — 6 บท', index_body, 'คลังความรู้ภาษาไทย 6 คลิป: ภาพรวม Setup สร้างเว็บไซต์ Deploy Agent Model Armor และ Observability พร้อมสรุปท้ายบท'), encoding='utf-8')
with zipfile.ZipFile(DEST / 'gemini-agent-platform-notes.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for slug, *_ in LESSONS:
        archive.write(DEST / f'{slug}.md', f'{slug}.md')
print(f'Built {len(LESSONS)} chapters, course index, and Markdown download.')
