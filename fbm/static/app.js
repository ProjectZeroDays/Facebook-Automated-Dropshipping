// app.js — toasts, modals, ⌘K, tables
(function () {
  window.toast = function (tone, title, body) {
    const host = document.getElementById('toastHost');
    if (!host) return;
    const el = document.createElement('div');
    el.className = 'toast toast--' + (tone || 'info');
    el.innerHTML = '<strong>' + title + '</strong> ' + (body || '');
    host.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  };
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-modal]');
    if (btn) {
      const m = document.querySelector(btn.dataset.modal);
      if (m && m.showModal) m.showModal();
    }
    const close = e.target.closest('[data-close]');
    if (close) close.closest('dialog')?.close();
    const post = e.target.closest('[data-post]');
    if (post) {
      fetch(post.dataset.post, { method: 'POST', headers: { 'X-CSRF-Token': window.csrfToken || '' } })
        .then(r => r.json()).then(d => window.toast('success', 'Done', d && d.message)).catch(() => window.toast('danger', 'Failed', ''));
    }
    const copy = e.target.closest('[data-copy]');
    if (copy) {
      navigator.clipboard?.writeText(copy.dataset.copy);
      window.toast('success', 'Copied', copy.dataset.copy);
    }
    const theme = e.target.closest('[data-theme-toggle]');
    if (theme) {
      const cur = document.documentElement.dataset.theme;
      document.documentElement.dataset.theme = cur === 'dark' ? 'light' : 'dark';
    }
  });
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      const p = document.querySelector('[data-palette]');
      if (p) p.click();
    }
  });
})();
