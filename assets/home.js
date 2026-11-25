(function(){
  const data = window.ProfileData;
  if (!data) return;

  const byYearDesc = (a, b) => (b.year || 0) - (a.year || 0);
  const publications = [...(data.publications || [])].sort(byYearDesc);
  const programs = data.observingPrograms || [];
  const grants = [...(data.grants || [])].sort(byYearDesc);
  const latest = publications[0];

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el && value) el.textContent = value;
  }
  function setHTML(id, value) {
    const el = document.getElementById(id);
    if (el && value) el.innerHTML = value;
  }
  function setHref(id, value) {
    const el = document.getElementById(id);
    if (el && value) el.href = value;
  }
  function formatGrantName(name) {
    return (name || '')
      .replace(/\s*travel grant\s*$/i, '')
      .replace(/\s*grant\s*$/i, '')
      .replace(/\s*fellowship\s*$/i, '')
      .replace(/^The\s+/i, '')
      .trim();
  }

  if (latest) {
    setText('latest-publication-title', latest.title);
    const ref = [latest.journal, latest.volume, latest.page].filter(Boolean).join(' ');
    setHTML('latest-publication-meta', `<i>${latest.journal}</i>${latest.volume ? ' ' + latest.volume : ''}${latest.page ? ', ' + latest.page : ''} · ${latest.year}`);
    setHref('latest-publication-doi', latest.url);
  }

  setText('publication-count', publications.length + ' first-author papers');
  setText('program-count', programs.length + ' observing programs');

  const grantNames = [];
  grants.forEach(g => {
    const clean = formatGrantName(g.name);
    if (clean && !grantNames.includes(clean)) grantNames.push(clean);
  });
  const shortGrantList = grantNames.slice(0, 3).join(', ');
  setText('grant-list', shortGrantList || 'Selected research and travel grants');

  const updateEl = document.getElementById('data-updated');
  if (updateEl && data.updated) {
    updateEl.setAttribute('datetime', data.updated);
    updateEl.textContent = new Date(data.updated + 'T00:00:00').toLocaleDateString('en', {year: 'numeric', month: 'long', day: 'numeric'});
  }
})();
