(() => {
  'use strict';
  const lessons = JSON.parse(document.getElementById('search-data').textContent);
  const input = document.getElementById('search');
  const cards = [...document.querySelectorAll('[data-lesson]')];
  input.addEventListener('input', () => {
    const query = input.value.trim().toLocaleLowerCase('th');
    let count = 0;
    cards.forEach((card, i) => {
      const lesson = lessons[i];
      const pos = lesson.text.toLocaleLowerCase('th').indexOf(query);
      const matched = !query || pos !== -1;
      card.hidden = !matched;
      const excerpt = card.querySelector('.match');
      excerpt.hidden = !query || !matched;
      excerpt.textContent = query && matched ? '…' + lesson.text.slice(Math.max(0, pos - 45), pos + query.length + 130).replace(/\s+/g, ' ') + '…' : '';
      if (matched) count++;
    });
    document.getElementById('search-status').textContent = `แสดง ${count} จาก 6 บท`;
    document.getElementById('empty').hidden = count !== 0;
  });
})();
