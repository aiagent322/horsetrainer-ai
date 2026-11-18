/* HorseTrainer.ai — site navigation and page UI */
'use strict';

function initNav() {
  const nav = document.querySelector('.nav');
  const menuBtn = document.getElementById('nav-menu-btn');
  const drawer = document.getElementById('nav-drawer');

  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 20);
    }, { passive: true });
  }

  if (menuBtn && drawer) {
    const desktop = window.matchMedia('(min-width: 900px)');
    const positionDrawer = () => {
      if (nav) drawer.style.top = nav.getBoundingClientRect().bottom + 'px';
    };
    const setOpen = open => {
      if (open) positionDrawer();
      drawer.classList.toggle('open', open);
      drawer.inert = !open;
      menuBtn.setAttribute('aria-expanded', String(open));
      menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      document.body.style.overflow = open ? 'hidden' : '';
    };
    menuBtn.setAttribute('aria-controls', drawer.id);
    setOpen(false);
    menuBtn.addEventListener('click', () => setOpen(!drawer.classList.contains('open')));
    drawer.querySelectorAll('.nav-link').forEach(link => link.addEventListener('click', () => setOpen(false)));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && drawer.classList.contains('open')) {
        setOpen(false);
        menuBtn.focus();
      }
    });
    desktop.addEventListener('change', event => { if (event.matches) setOpen(false); });
    if (nav && 'ResizeObserver' in window) new ResizeObserver(positionDrawer).observe(nav);
    window.addEventListener('resize', positionDrawer);
  }

  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });
}

function initAnimations() {
  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('.fade-up').forEach(el => el.classList.add('visible'));
    return;
  }
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.fade-up').forEach(el => obs.observe(el));
}

function initDisciplineFilter() {
  const filterBtns = document.querySelectorAll('[data-filter]');
  const filterable = document.querySelectorAll('[data-disc]');
  if (!filterBtns.length) return;
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      const filter = btn.dataset.filter;
      filterable.forEach(el => {
        el.style.display = filter === 'all' || el.dataset.disc === filter ? '' : 'none';
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initAnimations();
  initDisciplineFilter();
});
