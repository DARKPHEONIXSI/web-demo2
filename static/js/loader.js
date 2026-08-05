/* ═══════════════════════════════════════════════════════════
   loader.js — Premium Ice Crystal Loading Screen
   Animated ice crystal formation, particle progress bar,
   shatter/dissolve exit transition
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  const loader = document.getElementById('loader');
  if (!loader) return;

  /* ── Create ice crystal SVG animation ────────────────── */
  const crystalContainer = document.createElement('div');
  crystalContainer.className = 'loader-crystal';
  crystalContainer.innerHTML = `
    <svg viewBox="0 0 100 100" width="80" height="80" style="filter: drop-shadow(0 0 12px rgba(0,212,255,0.4));">
      <g class="crystal-group" style="transform-origin: 50px 50px;">
        <!-- Main hexagonal crystal -->
        <polygon class="crystal-facet crystal-facet-1" points="50,10 80,30 80,70 50,90 20,70 20,30"
          fill="none" stroke="rgba(0,212,255,0.8)" stroke-width="1"
          style="stroke-dasharray: 240; stroke-dashoffset: 240;" />
        <!-- Inner structure -->
        <line class="crystal-line crystal-line-1" x1="50" y1="10" x2="50" y2="90"
          stroke="rgba(126,184,255,0.4)" stroke-width="0.5"
          style="stroke-dasharray: 80; stroke-dashoffset: 80;" />
        <line class="crystal-line crystal-line-2" x1="20" y1="30" x2="80" y2="70"
          stroke="rgba(126,184,255,0.4)" stroke-width="0.5"
          style="stroke-dasharray: 80; stroke-dashoffset: 80;" />
        <line class="crystal-line crystal-line-3" x1="80" y1="30" x2="20" y2="70"
          stroke="rgba(126,184,255,0.4)" stroke-width="0.5"
          style="stroke-dasharray: 80; stroke-dashoffset: 80;" />
        <!-- Center glow -->
        <circle class="crystal-core" cx="50" cy="50" r="4"
          fill="rgba(0,212,255,0.6)" style="opacity:0;" />
        <!-- Smaller inner hexagon -->
        <polygon class="crystal-facet crystal-facet-2" points="50,25 67,37 67,63 50,75 33,63 33,37"
          fill="none" stroke="rgba(167,139,250,0.5)" stroke-width="0.5"
          style="stroke-dasharray: 160; stroke-dashoffset: 160;" />
      </g>
      <!-- Floating particles around crystal -->
      <circle class="crystal-particle" cx="15" cy="20" r="1.5" fill="rgba(0,212,255,0.6)" style="opacity:0;" />
      <circle class="crystal-particle" cx="85" cy="25" r="1" fill="rgba(126,184,255,0.5)" style="opacity:0;" />
      <circle class="crystal-particle" cx="90" cy="75" r="1.5" fill="rgba(167,139,250,0.4)" style="opacity:0;" />
      <circle class="crystal-particle" cx="10" cy="80" r="1" fill="rgba(0,255,136,0.4)" style="opacity:0;" />
      <circle class="crystal-particle" cx="50" cy="5" r="1" fill="rgba(0,212,255,0.5)" style="opacity:0;" />
      <circle class="crystal-particle" cx="50" cy="95" r="1.2" fill="rgba(126,184,255,0.4)" style="opacity:0;" />
    </svg>
  `;

  // Insert crystal before the logo
  const loaderLogo = loader.querySelector('img');
  if (loaderLogo) {
    loaderLogo.style.display = 'none';
    loader.insertBefore(crystalContainer, loader.firstChild);
  }

  /* ── Animate crystal formation ───────────────────────── */
  function animateCrystal() {
    // Phase 1: Draw outer hexagon
    const facet1 = loader.querySelector('.crystal-facet-1');
    const facet2 = loader.querySelector('.crystal-facet-2');
    const lines = loader.querySelectorAll('.crystal-line');
    const core = loader.querySelector('.crystal-core');
    const particles = loader.querySelectorAll('.crystal-particle');
    const crystalGroup = loader.querySelector('.crystal-group');

    if (!facet1) return;

    // Continuous rotation
    let rotation = 0;
    function rotateCrystal() {
      rotation += 0.3;
      if (crystalGroup) crystalGroup.style.transform = `rotate(${rotation}deg)`;
      if (!loader.classList.contains('hidden')) {
        requestAnimationFrame(rotateCrystal);
      }
    }
    requestAnimationFrame(rotateCrystal);

    // Phase 1: Outer hexagon draws in (0-600ms)
    setTimeout(() => {
      facet1.style.transition = 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
      facet1.style.strokeDashoffset = '0';
    }, 100);

    // Phase 2: Internal lines appear (400-800ms)
    lines.forEach((line, i) => {
      setTimeout(() => {
        line.style.transition = 'stroke-dashoffset 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
        line.style.strokeDashoffset = '0';
      }, 400 + i * 150);
    });

    // Phase 3: Inner hexagon (700ms)
    setTimeout(() => {
      facet2.style.transition = 'stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
      facet2.style.strokeDashoffset = '0';
    }, 700);

    // Phase 4: Core glow (900ms)
    setTimeout(() => {
      core.style.transition = 'opacity 0.4s ease-out';
      core.style.opacity = '1';
      // Pulse the core
      core.style.animation = 'corePulse 1.5s ease-in-out infinite';
    }, 900);

    // Phase 5: Particles float in (1000ms+)
    particles.forEach((p, i) => {
      setTimeout(() => {
        p.style.transition = 'opacity 0.3s ease-out';
        p.style.opacity = '1';
        p.style.animation = `particleFloat${(i % 3) + 1} ${2 + i * 0.3}s ease-in-out infinite`;
      }, 1000 + i * 100);
    });
  }

  animateCrystal();

  /* ── Animate the title letters ───────────────────────── */
  const title = loader.querySelector('.loader-title');
  if (title) {
    const text = title.textContent;
    title.textContent = '';
    text.split('').forEach((char, i) => {
      const span = document.createElement('span');
      span.textContent = char === ' ' ? '\u00A0' : char;
      span.style.animationDelay = (i * 0.08) + 's';
      title.appendChild(span);
    });
  }

  /* ── Animate progress bar with particle edge ─────────── */
  const fill = loader.querySelector('.loader-bar-fill');
  let progress = 0;

  function tick() {
    progress += (100 - progress) * 0.06;
    if (fill) fill.style.width = Math.min(progress, 100) + '%';
    if (progress < 98) requestAnimationFrame(tick);
  }
  tick();

  /* ── Shatter exit transition ─────────────────────────── */
  function hideLoader() {
    if (fill) fill.style.width = '100%';

    // Create shatter particles
    const shatterCount = 20;
    for (let i = 0; i < shatterCount; i++) {
      const particle = document.createElement('div');
      particle.className = 'shatter-particle';
      const angle = (i / shatterCount) * Math.PI * 2;
      const distance = 80 + Math.random() * 120;
      const size = 3 + Math.random() * 6;
      particle.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: var(--accent-ice);
        border-radius: 2px;
        top: 50%;
        left: 50%;
        opacity: 0.8;
        pointer-events: none;
        transform: translate(-50%, -50%) rotate(${Math.random() * 360}deg);
        transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
      `;
      loader.appendChild(particle);

      // Trigger explosion
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          particle.style.transform = `translate(
            calc(-50% + ${Math.cos(angle) * distance}px),
            calc(-50% + ${Math.sin(angle) * distance}px)
          ) rotate(${Math.random() * 720}deg) scale(0)`;
          particle.style.opacity = '0';
        });
      });
    }

    setTimeout(() => {
      loader.style.transition = 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1), backdrop-filter 0.5s';
      loader.style.opacity = '0';
      loader.style.backdropFilter = 'blur(0px)';
      loader.classList.add('hidden');

      setTimeout(() => {
        if (loader.parentNode) loader.style.display = 'none';
      }, 600);
    }, 300);
  }

  // Wait for page load
  if (document.readyState === 'complete') {
    setTimeout(hideLoader, 1200);
  } else {
    window.addEventListener('load', () => setTimeout(hideLoader, 800));
  }

  // Fallback: always hide after 5 seconds
  setTimeout(hideLoader, 5000);
})();
