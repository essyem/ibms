document.addEventListener('DOMContentLoaded', function () {
  const btn = document.getElementById('nav-toggle');
  const list = document.getElementById('main-nav-list');
  if (!btn || !list) return;

  btn.addEventListener('click', function () {
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', String(!expanded));
    list.classList.toggle('open');
  });
});
