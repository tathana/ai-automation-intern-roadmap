(() => {
  'use strict';
  const form = document.getElementById('prompt-builder');
  if (!form) return;
  const output = document.getElementById('builder-output');
  const status = document.getElementById('builder-status');
  const field = name => form.elements.namedItem(name).value.trim();
  const optional = (label, value) => value ? `\n${label}: ${value}` : '';

  form.addEventListener('submit', event => {
    event.preventDefault();
    const role = field('role');
    const task = field('task');
    if (!role || !task) {
      status.textContent = 'กรุณากรอกบทบาทและงานก่อน';
      return;
    }
    const kind = field('kind');
    const language = field('language');
    const audience = field('audience');
    const format = field('format');
    const context = field('context');
    const requirements = field('requirements');
    const constraints = field('constraints');
    let intro;
    if (kind === 'grounded') {
      intro = `You are a ${role}. Answer this question using only the provided source: ${task}.`;
    } else if (kind === 'review') {
      intro = `You are a ${role}. Review and improve this draft for the following task: ${task}.`;
    } else if (kind === 'create') {
      intro = `You are a ${role}. Create content for this task: ${task}.`;
    } else {
      intro = `You are a ${role}. Your task is to ${task}.`;
    }
    const sourceLabel = kind === 'grounded' ? 'Source text' : kind === 'review' ? 'Draft to review' : 'Context or input';
    const ending = kind === 'grounded'
      ? 'Use only the source text for factual claims. Cite the relevant part if possible. If the answer is absent, state that it was not found. Do not guess.'
      : kind === 'review'
        ? 'Return the issues found, a revised answer, and anything that still needs human verification. Do not invent facts.'
        : 'If important information is missing, state the gap or ask a clarifying question. Do not invent facts.';
    output.value = intro
      + optional('Target audience', audience)
      + optional(sourceLabel, context)
      + optional('Output format', format)
      + `\nAnswer language: ${language}.`
      + optional('Requirements', requirements)
      + optional('Constraints', constraints)
      + `\n${ending}`;
    status.textContent = 'สร้างแล้ว — อ่านทวนและแก้ข้อความก่อนคัดลอก';
    output.focus();
  });

  document.getElementById('builder-example').addEventListener('click', () => {
    form.elements.namedItem('kind').value = 'general';
    form.elements.namedItem('language').value = 'Thai';
    form.elements.namedItem('role').value = 'patient AWS instructor';
    form.elements.namedItem('task').value = 'explain the difference between a foundation model and a chatbot';
    form.elements.namedItem('audience').value = 'Thai beginners with limited English';
    form.elements.namedItem('format').value = '5 bullet points and one simple workplace example';
    form.elements.namedItem('context').value = 'I am preparing for the Generative AI Essentials on AWS class.';
    form.elements.namedItem('requirements').value = 'Define each technical term in simple Thai.';
    form.elements.namedItem('constraints').value = 'Do not assume AWS experience or invent product features.';
    form.requestSubmit();
  });

  form.addEventListener('reset', () => {
    output.value = '';
    status.textContent = '';
  });

  document.getElementById('builder-copy').addEventListener('click', async () => {
    if (!output.value.trim()) {
      status.textContent = 'สร้างพรอมป์ต์ก่อนคัดลอก';
      return;
    }
    try {
      await navigator.clipboard.writeText(output.value);
      status.textContent = 'คัดลอกแล้ว';
    } catch {
      output.focus();
      output.select();
      status.textContent = 'เลือกข้อความแล้ว กด Ctrl+C หรือ Command+C เพื่อคัดลอก';
    }
  });
})();
