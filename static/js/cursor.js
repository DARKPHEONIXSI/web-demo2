/* ═══════════════════════════════════════════════════════════
   cursor.js — Animated Custom Cursor + Snowflake Trail
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // Skip on touch devices
  if ('ontouchstart' in window || navigator.maxTouchPoints > 0) return;

  // Default cursor is visible now, no need to hide it

  // Create cursor elements
  const dot = document.createElement('div');
  dot.className = 'cursor-dot';
  document.body.appendChild(dot);

  const ring = document.createElement('div');
  ring.className = 'cursor-ring';
  document.body.appendChild(ring);

  // Trail particles pool
  const trailCount = 8;
  const trails = [];
  for (let i = 0; i < trailCount; i++) {
    const t = document.createElement('div');
    t.className = 'cursor-trail';
    document.body.appendChild(t);
    trails.push({ el: t, x: 0, y: 0, life: 0 });
  }

  let mouseX = 0, mouseY = 0;
  let dotX = 0, dotY = 0;
  let ringX = 0, ringY = 0;
  let trailIndex = 0;
  let lastTrailTime = 0;

  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;

    // Spawn trail particles
    const now = Date.now();
    if (now - lastTrailTime > 50) {
      lastTrailTime = now;
      const trail = trails[trailIndex % trailCount];
      trail.x = mouseX;
      trail.y = mouseY;
      trail.life = 1;
      trailIndex++;
    }
  });

  // Hover detection
  document.addEventListener('mouseover', (e) => {
    const target = e.target.closest('a, button, [role="button"], .article-card, .product-card, .pathway-card, .gallery-item, .technique-item');
    if (target) {
      dot.classList.add('hover');
      ring.classList.add('hover');
    }
  });
  document.addEventListener('mouseout', (e) => {
    const target = e.target.closest('a, button, [role="button"], .article-card, .product-card, .pathway-card, .gallery-item, .technique-item');
    if (target) {
      dot.classList.remove('hover');
      ring.classList.remove('hover');
    }
  });

  // Cursor is now visible, we only render the trailing animation elements

  // Animation loop
  function animateCursor() {
    // Smooth follow for dot
    dotX += (mouseX - dotX) * 0.25;
    dotY += (mouseY - dotY) * 0.25;
    dot.style.left = dotX + 'px';
    dot.style.top = dotY + 'px';

    // Slower follow for ring (elastic effect)
    ringX += (mouseX - ringX) * 0.12;
    ringY += (mouseY - ringY) * 0.12;
    ring.style.left = ringX + 'px';
    ring.style.top = ringY + 'px';

    // Update trail particles
    trails.forEach((t) => {
      if (t.life > 0) {
        t.life -= 0.03;
        t.el.style.left = t.x + 'px';
        t.el.style.top = t.y + 'px';
        t.el.style.opacity = t.life * 0.5;
        t.el.style.transform = `translate(-50%, -50%) scale(${t.life})`;
        t.y -= 0.3; // Snowflake float upward
        t.x += (Math.random() - 0.5) * 0.5;
      } else {
        t.el.style.opacity = 0;
      }
    });

    requestAnimationFrame(animateCursor);
  }

  animateCursor();
})();
