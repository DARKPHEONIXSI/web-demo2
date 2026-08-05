/* ═══════════════════════════════════════════════════════════
   app.js — SPA Router, Navigation, Dark/Light Toggle
   Hash-based routing, page loading, theme persistence
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Route definitions ─────────────────────────────────
  // IMPORTANT: paths must be absolute /static/pages/... so that Flask
  // can serve them correctly regardless of what URL the SPA is on.
  const routes = {
    '':              '/static/pages/home.html',
    'home':          '/static/pages/home.html',
    'shop':          '/static/pages/shop.html',
    'product':       '/static/pages/product.html',
    'post':          '/static/pages/post.html',
    'gallery':       '/static/pages/gallery.html',
    'about':         '/static/pages/about.html',
    'contact':       '/static/pages/contact.html',
    'checkout':      '/static/pages/checkout.html',
    'profile':       '/static/pages/profile.html',
    'techniques':    '/static/pages/techniques.html',
    'legal':         '/static/pages/legal.html',
    'order':         '/static/pages/order-tracking.html',
    'invoice':       '/static/pages/invoice.html',
    'return':        '/static/pages/return-request.html',
    'isu-rules':     '/static/pages/isu-rules.html',
    'rules':         '/static/pages/isu-rules.html',
    'payment-failed':'/static/pages/payment-failed.html',
    'success':       '/static/pages/success.html',
    'page':          '/static/pages/page.html',
    // Admin pages — all stored flat in static/pages/ (no admin/ subfolder)
    'admin/login':   '/static/pages/login.html',
    'admin/dashboard':'/static/pages/dashboard.html',
    'admin/orders':  '/static/pages/orders.html',
    'admin/marketplace':'/static/pages/marketplace.html',
    'admin/posts':   '/static/pages/posts.html',
    'admin/post-edit':'/static/pages/post-edit.html',
    'admin/pages':   '/static/pages/pages.html',
    'admin/page-edit':'/static/pages/page-edit.html',
    'admin/messages':'/static/pages/messages.html',
    'admin/settings':'/static/pages/settings.html',
    'admin/product-edit':'/static/pages/product-edit.html',
    'admin/media':   '/static/pages/media.html',
    'admin/users':   '/static/pages/users.html',
  };

  const pageContent = document.getElementById('page-content');
  const pageCache = {};
  let currentRoute = '';

  // ── Parse route from hash ─────────────────────────────
  function parseHash() {
    const hash = window.location.hash.slice(2) || 'home'; // remove #/
    const parts = hash.split('/');
    // Handle parameterized routes like #/product/1 or #/post/slug
    if (parts.length >= 2 && ['product', 'post', 'order', 'invoice', 'return'].includes(parts[0])) {
      return { route: parts[0], param: parts.slice(1).join('/') };
    }
    if (parts.length >= 3 && parts[0] === 'admin') {
      return { route: parts[0] + '/' + parts[1], param: parts[2] || null };
    }
    return { route: parts.join('/'), param: null };
  }

  // ── Load a page ───────────────────────────────────────
  async function loadPage(routeKey, param) {
    const file = routes[routeKey];
    if (!file) {
      pageContent.innerHTML = `
        <div class="section" style="text-align:center; padding:8rem 2rem;">
          <h1 style="font-family:var(--font-display); font-size:4rem; color:var(--accent-ice);">404</h1>
          <p style="color:var(--text-secondary); margin:1rem 0 2rem;">Page not found in the ice.</p>
          <a href="#/home" class="btn-primary">Back to Home</a>
        </div>`;
      return;
    }

    try {
      let html;
      const isAdmin = routeKey.startsWith('admin');
      if (!isAdmin && pageCache[file]) {
        html = pageCache[file];
      } else {
        const resp = await fetch(file + '?t=' + Date.now());
        if (!resp.ok) throw new Error('Failed to load ' + file);
        html = await resp.text();
        if (!isAdmin) pageCache[file] = html;
      }

      // Inject param into page context
      window.__routeParam = param;

      pageContent.innerHTML = html;

      // Execute inline scripts
      pageContent.querySelectorAll('script').forEach((oldScript) => {
        const newScript = document.createElement('script');
        if (oldScript.src) {
          newScript.src = oldScript.src;
        } else {
          newScript.textContent = oldScript.textContent;
        }
        oldScript.parentNode.replaceChild(newScript, oldScript);
      });

      // Init animations
      if (window.initPageAnimations) {
        setTimeout(() => window.initPageAnimations(), 50);
      }

      // Update cart badge
      if (typeof updateCartBadge === 'function') updateCartBadge();

      // Scroll to top
      window.scrollTo({ top: 0, behavior: 'instant' });

      // Update active nav link
      updateActiveNav(routeKey);

      // Hide/show global chrome for admin vs public routes
      const isAdminRoute = routeKey.startsWith('admin');
      const mainNav = document.getElementById('mainNav');
      const threeCanvas = document.getElementById('three-canvas');
      const scrollProgress = document.getElementById('scroll-progress');
      if (mainNav) mainNav.style.display = isAdminRoute ? 'none' : '';
      if (threeCanvas) threeCanvas.style.display = isAdminRoute ? 'none' : '';
      if (scrollProgress) scrollProgress.style.display = isAdminRoute ? 'none' : '';

      // Show/hide global footer — home page uses the CTA section's footer bar, admin has its own layout
      const globalFooter = document.getElementById('global-footer');
      if (globalFooter) {
        const isHome = routeKey === '' || routeKey === 'home';
        const isAdmin = routeKey.startsWith('admin');
        globalFooter.classList.toggle('footer--hidden', isHome || isAdmin);
      }

    } catch (err) {
      console.error('Route load error:', err);
      pageContent.innerHTML = `
        <div class="section" style="text-align:center; padding:8rem 2rem;">
          <h1 style="font-family:var(--font-display); font-size:2rem; color:var(--accent-error);">Error Loading Page</h1>
          <p style="color:var(--text-secondary); margin:1rem 0;">Something went wrong. Please try again.</p>
          <a href="#/home" class="btn-primary">Back to Home</a>
        </div>`;
    }
  }

  // ── Update active nav link ────────────────────────────
  function updateActiveNav(routeKey) {
    document.querySelectorAll('.nav-links a').forEach((a) => {
      const href = a.getAttribute('href');
      if (!href) return;
      const linkRoute = href.replace('#/', '');
      a.classList.toggle('active', linkRoute === routeKey || (routeKey === '' && linkRoute === 'home'));
    });
  }

  // ── Router ────────────────────────────────────────────
  function onRouteChange() {
    const { route, param } = parseHash();
    if (route === currentRoute && !param) return;
    currentRoute = route;

    // Use page transition if available
    if (window.pageTransition && pageContent.innerHTML) {
      window.pageTransition(() => loadPage(route, param));
    } else {
      loadPage(route, param);
    }
  }

  window.addEventListener('hashchange', onRouteChange);

  // ── Theme Toggle ──────────────────────────────────────
  function initTheme() {
    const saved = localStorage.getItem('onice_theme');
    if (saved) {
      document.documentElement.setAttribute('data-theme', saved);
    }
    updateThemeIcon();
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('onice_theme', next);
    updateThemeIcon();
  }

  function updateThemeIcon() {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    btn.innerHTML = isLight ? '🌙' : '☀️';
    btn.title = isLight ? 'Switch to dark mode' : 'Switch to light mode';
  }

  window.toggleTheme = toggleTheme;

  // ── Mobile Nav ────────────────────────────────────────
  window.toggleMobileNav = function () {
    const nav = document.querySelector('.nav-links');
    if (nav) nav.classList.toggle('open');
  };

  // Close mobile nav on link click
  document.addEventListener('click', (e) => {
    if (e.target.closest('.nav-links a')) {
      const nav = document.querySelector('.nav-links');
      if (nav) nav.classList.remove('open');
    }
  });

  // ── Nav scroll effect ─────────────────────────────────
  window.addEventListener('scroll', () => {
    const nav = document.querySelector('.nav');
    if (nav) {
      nav.classList.toggle('scrolled', window.scrollY > 50);
    }
  });

  // ── Toast system ──────────────────────────────────────
  window.showToast = function (msg, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const t = document.createElement('div');
    t.className = 'toast' + (type === 'error' ? ' toast-error' : '');
    t.textContent = msg;
    container.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    setTimeout(() => {
      t.classList.remove('show');
      setTimeout(() => t.remove(), 300);
    }, 2700);
  };

  // ── Navigate helper ───────────────────────────────────
  window.navigateTo = function (route) {
    window.location.hash = '#/' + route;
  };

  // ── Tab Switcher (ISU Rules) ──────────────────────────
  window.switchTab = function (tabId, btn) {
    document.querySelectorAll('.rule-pane').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.rule-tab').forEach(b => b.classList.remove('active'));
    const targetPane = document.getElementById(tabId);
    if (targetPane) targetPane.style.display = 'block';
    if (btn) btn.classList.add('active');
  };

  // ── Auth Modal ────────────────────────────────────────
  window.openAuthModal = function (mode) {
    let overlay = document.getElementById('auth-overlay');
    if (overlay) {
      overlay.classList.add('open');
      const loginTab = overlay.querySelector('[data-tab="login"]');
      const registerTab = overlay.querySelector('[data-tab="register"]');
      const loginForm = overlay.querySelector('#loginForm');
      const registerForm = overlay.querySelector('#registerForm');
      if (mode === 'register') {
        loginTab?.classList.remove('active');
        registerTab?.classList.add('active');
        loginForm && (loginForm.style.display = 'none');
        registerForm && (registerForm.style.display = 'block');
      } else {
        loginTab?.classList.add('active');
        registerTab?.classList.remove('active');
        loginForm && (loginForm.style.display = 'block');
        registerForm && (registerForm.style.display = 'none');
      }
      return;
    }
    // Load modal
    fetch('/static/pages/auth-modal.html')
      .then(r => r.text())
      .then(html => {
        const div = document.createElement('div');
        div.innerHTML = html;
        document.body.appendChild(div.firstElementChild);
        openAuthModal(mode);
      });
  };

  window.closeAuthModal = function () {
    const overlay = document.getElementById('auth-overlay');
    if (overlay) overlay.classList.remove('open');
  };

  // ── Initialize ────────────────────────────────────────
  initTheme();

  // Hide global footer immediately if landing on home (CTA section has its own footer)
  const initialHash = window.location.hash.slice(2) || 'home';
  const initialRoute = initialHash.split('/')[0];
  const globalFooterEl = document.getElementById('global-footer');
  if (globalFooterEl && (initialRoute === '' || initialRoute === 'home')) {
    globalFooterEl.classList.add('footer--hidden');
  }

  // Initial route load
  if (!window.location.hash || window.location.hash === '#' || window.location.hash === '#/') {
    window.location.hash = '#/home';
  } else {
    onRouteChange();
  }
})();
