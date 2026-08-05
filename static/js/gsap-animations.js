/* ═══════════════════════════════════════════════════════════
   gsap-animations.js — Premium Motion Design System
   Split-text reveals, scrubbed paragraphs, 3D card entrances,
   clip-path transitions, choreographed staggers, magnetic buttons,
   scroll progress, nav morphing
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  if (!window.gsap) return;
  const gsap = window.gsap;
  const ScrollTrigger = window.ScrollTrigger;

  if (ScrollTrigger) gsap.registerPlugin(ScrollTrigger);

  /* ── Premium Easing Constants ────────────────────────── */
  const EASE = {
    premium: 'cubic-bezier(0.4, 0, 0.2, 1)',
    entrance: 'power3.out',
    exit: 'power2.in',
    spring: 'elastic.out(1, 0.75)',
    smooth: 'power2.inOut',
    dramatic: 'expo.out',
    gentle: 'sine.inOut'
  };

  /* ── Utility: Split text into words/chars ────────────── */
  function splitTextIntoWords(element) {
    if (!element || element.dataset.split === 'true') return;
    const text = element.textContent;
    const words = text.split(/\s+/);
    element.innerHTML = words.map(word =>
      `<span class="word-wrap" style="display:inline-block;overflow:hidden;vertical-align:top;">` +
      `<span class="word" style="display:inline-block;transform:translateY(100%);opacity:0;">${word}</span>` +
      `</span> `
    ).join('');
    element.dataset.split = 'true';
  }

  function splitTextIntoChars(element) {
    if (!element || element.dataset.splitChar === 'true') return;
    const text = element.textContent;
    element.innerHTML = text.split('').map((char, i) =>
      `<span class="char" style="display:inline-block;opacity:0;transform:translateY(8px);">${char === ' ' ? '&nbsp;' : char}</span>`
    ).join('');
    element.dataset.splitChar = 'true';
  }

  /* ── Utility: Split paragraph into words for scrub ───── */
  function splitParaWords(element) {
    if (!element || element.dataset.splitPara === 'true') return;
    const text = element.textContent;
    const words = text.split(/\s+/);
    element.innerHTML = words.map(word =>
      `<span class="scrub-word" style="opacity:0.15;display:inline;">${word}</span> `
    ).join('');
    element.dataset.splitPara = 'true';
  }

  /* ═══════════════════════════════════════════════════════
     INIT PAGE ANIMATIONS
     Called each time a page loads via the SPA router
     ═══════════════════════════════════════════════════════ */
  window.initPageAnimations = function () {
    // Kill all existing ScrollTriggers
    if (ScrollTrigger) ScrollTrigger.getAll().forEach(t => t.kill());

    /* ── 1. Split-Text Hero Title Reveal ──────────────── */
    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
      splitTextIntoWords(heroTitle);
      const words = heroTitle.querySelectorAll('.word');
      gsap.fromTo(words,
        { y: '105%', opacity: 0, rotateX: 40 },
        {
          y: '0%',
          opacity: 1,
          rotateX: 0,
          duration: 0.9,
          stagger: 0.06,
          ease: EASE.dramatic,
          delay: 0.2
        }
      );
    }

    /* ── 2. Character-by-Character Kicker Typewriter ──── */
    const heroKicker = document.querySelector('.hero-kicker');
    if (heroKicker) {
      splitTextIntoChars(heroKicker);
      const chars = heroKicker.querySelectorAll('.char');
      gsap.fromTo(chars,
        { opacity: 0, y: 8 },
        {
          opacity: 1,
          y: 0,
          duration: 0.05,
          stagger: 0.03,
          ease: 'none',
          delay: 0.1
        }
      );
      // Add blinking cursor after last char
      const cursor = document.createElement('span');
      cursor.className = 'type-cursor';
      cursor.textContent = '|';
      cursor.style.cssText = 'animation:cursorBlink 0.8s infinite;color:var(--accent-ice);font-weight:300;margin-left:2px;';
      heroKicker.appendChild(cursor);
      // Remove cursor after animation
      setTimeout(() => cursor.remove(), 3000);
    }

    /* ── 3. Hero Subtitle & Actions Entrance ─────────── */
    const heroSubtitle = document.querySelector('.hero-subtitle');
    const heroActions = document.querySelector('.hero-actions');
    const heroVisual = document.querySelector('.hero-visual');

    if (heroSubtitle) {
      gsap.fromTo(heroSubtitle,
        { opacity: 0, y: 25, filter: 'blur(4px)' },
        { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.8, ease: EASE.entrance, delay: 0.7 }
      );
    }
    if (heroActions) {
      gsap.fromTo(heroActions.children,
        { opacity: 0, y: 15, scale: 0.95 },
        { opacity: 1, y: 0, scale: 1, duration: 0.6, stagger: 0.1, ease: EASE.entrance, delay: 0.9 }
      );
    }
    if (heroVisual) {
      gsap.fromTo(heroVisual,
        { opacity: 0, scale: 0.88, x: 40, filter: 'blur(8px)' },
        { opacity: 1, scale: 1, x: 0, filter: 'blur(0px)', duration: 1.2, ease: EASE.dramatic, delay: 0.5 }
      );
    }

    /* ── 4. Scrubbed Paragraph Reveals ─────────────────── */
    if (ScrollTrigger) {
      gsap.utils.toArray('.section-subtitle').forEach(el => {
        splitParaWords(el);
        const scrubWords = el.querySelectorAll('.scrub-word');
        gsap.to(scrubWords, {
          opacity: 1,
          stagger: 0.05,
          ease: 'none',
          scrollTrigger: {
            trigger: el,
            start: 'top 90%',
            end: 'top 40%',
            scrub: 1.5
          }
        });
      });
    }

    /* ── 5. Section Title Clip-Path Reveal ─────────────── */
    gsap.utils.toArray('.section-title').forEach(el => {
      gsap.fromTo(el,
        {
          clipPath: 'inset(100% 0 0 0)',
          opacity: 0,
          y: 20
        },
        {
          clipPath: 'inset(0% 0 0 0)',
          opacity: 1,
          y: 0,
          duration: 0.9,
          ease: EASE.dramatic,
          scrollTrigger: {
            trigger: el,
            start: 'top 92%',
            end: 'top 60%',
            scrub: false,
            once: true
          }
        }
      );
    });

    /* ── 6. Section Labels Slide In ────────────────────── */
    gsap.utils.toArray('.section-label').forEach(label => {
      gsap.fromTo(label,
        { opacity: 0, x: -25, filter: 'blur(3px)' },
        {
          opacity: 1, x: 0, filter: 'blur(0px)',
          duration: 0.7,
          ease: EASE.entrance,
          scrollTrigger: {
            trigger: label,
            start: 'top 94%',
            once: true
          }
        }
      );
    });

    /* ── 7. 3D Perspective Card Entrances ──────────────── */
    gsap.utils.toArray('.grid-3, .grid-4, .pathway-grid, .admin-stat-grid').forEach(grid => {
      const items = grid.children;
      if (items.length === 0) return;

      // Set perspective on parent
      grid.style.perspective = '1200px';

      gsap.fromTo(items,
        {
          opacity: 0,
          y: 40,
          rotateX: 8,
          scale: 0.94,
          transformOrigin: 'center top'
        },
        {
          opacity: 1,
          y: 0,
          rotateX: 0,
          scale: 1,
          duration: 0.7,
          stagger: 0.08,
          ease: EASE.dramatic,
          scrollTrigger: {
            trigger: grid,
            start: 'top 92%',
            once: true
          }
        }
      );
    });

    /* ── 8. Glass Card Reveals with Depth ──────────────── */
    gsap.utils.toArray('.glass-card').forEach(card => {
      gsap.fromTo(card,
        {
          opacity: 0,
          scale: 0.95,
          y: 25,
          filter: 'blur(4px)'
        },
        {
          opacity: 1,
          scale: 1,
          y: 0,
          filter: 'blur(0px)',
          duration: 0.8,
          ease: EASE.entrance,
          scrollTrigger: {
            trigger: card,
            start: 'top 95%',
            once: true
          }
        }
      );
    });

    /* ── 9. Reveal Elements ───────────────────────────── */
    gsap.utils.toArray('.reveal').forEach(el => {
      gsap.fromTo(el,
        { opacity: 0, y: 30 },
        {
          opacity: 1, y: 0,
          duration: 0.7,
          ease: EASE.entrance,
          scrollTrigger: {
            trigger: el,
            start: 'top 94%',
            once: true
          }
        }
      );
    });

    /* ── 10. Stat Counter with Spring Overshoot ───────── */
    gsap.utils.toArray('.stat-grid strong, .admin-stat strong').forEach(el => {
      const text = el.textContent.trim();
      const match = text.match(/^[₹]?([\d,]+\.?\d*)/);
      if (!match) return;
      const target = parseFloat(match[1].replace(/,/g, ''));
      if (isNaN(target)) return;
      const prefix = text.startsWith('₹') ? '₹' : '';
      const suffix = text.replace(/^[₹]?[\d,]+\.?\d*/, '');

      el.textContent = prefix + '0' + suffix;

      // Overshoot: count to 105% then settle back
      const overshoot = Math.round(target * 1.05);

      gsap.to({ val: 0 }, {
        val: overshoot,
        duration: 1.6,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: el,
          start: 'top 95%',
          once: true
        },
        onUpdate: function () {
          const current = Math.round(this.targets()[0].val);
          el.textContent = prefix + current.toLocaleString() + suffix;
        },
        onComplete: function () {
          // Settle back to actual value
          gsap.to({ val: overshoot }, {
            val: target,
            duration: 0.4,
            ease: 'power2.inOut',
            onUpdate: function () {
              const current = Math.round(this.targets()[0].val);
              el.textContent = prefix + current.toLocaleString() + suffix;
            }
          });
        }
      });
    });

    /* ── 11. Parallax Hero Image ──────────────────────── */
    const heroImage = document.querySelector('.hero-image');
    if (heroImage && ScrollTrigger) {
      gsap.to(heroImage, {
        y: 50,
        scale: 1.02,
        ease: 'none',
        scrollTrigger: {
          trigger: '.hero',
          start: 'top top',
          end: 'bottom top',
          scrub: 1.5
        }
      });
    }

    /* ── 12. Orbit Card Float (CSS-powered via class) ──── */
    gsap.utils.toArray('.orbit-card').forEach((card, i) => {
      gsap.to(card, {
        y: -12,
        duration: 3 + i * 0.5,
        ease: EASE.gentle,
        yoyo: true,
        repeat: -1
      });
    });

    /* ── 13. Page Hero Text ───────────────────────────── */
    const pageHero = document.querySelector('.page-hero');
    if (pageHero) {
      gsap.fromTo(pageHero.children,
        { opacity: 0, y: 25, filter: 'blur(3px)' },
        { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.7, stagger: 0.12, ease: EASE.entrance }
      );
    }

    /* ── 14. Article Card Image Hover (Ken Burns) ──────── */
    document.querySelectorAll('.article-card-img-wrap').forEach(wrap => {
      const img = wrap.querySelector('.article-card-img');
      if (!img) return;

      wrap.addEventListener('mouseenter', () => {
        gsap.to(img, { scale: 1.06, duration: 0.7, ease: EASE.smooth });
      });
      wrap.addEventListener('mouseleave', () => {
        gsap.to(img, { scale: 1, duration: 0.5, ease: EASE.entrance });
      });
    });

    /* ── 15. Pathway Card 3D Tilt on Hover ────────────── */
    document.querySelectorAll('.pathway-card').forEach(card => {
      card.style.transformStyle = 'preserve-3d';
      card.style.perspective = '800px';

      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        gsap.to(card, {
          rotateY: x * 12,
          rotateX: -y * 8,
          scale: 1.03,
          duration: 0.4,
          ease: EASE.entrance
        });
        // Float icon up
        const icon = card.querySelector('.material-symbols-outlined');
        if (icon) {
          gsap.to(icon, { y: -4, scale: 1.1, duration: 0.3, ease: EASE.entrance });
        }
      });

      card.addEventListener('mouseleave', () => {
        gsap.to(card, {
          rotateY: 0, rotateX: 0, scale: 1,
          duration: 0.5, ease: EASE.entrance
        });
        const icon = card.querySelector('.material-symbols-outlined');
        if (icon) {
          gsap.to(icon, { y: 0, scale: 1, duration: 0.3, ease: EASE.entrance });
        }
      });
    });

    /* ── 16. Feature Card Entrance ─────────────────────── */
    const featureCard = document.querySelector('.feature-card');
    if (featureCard && ScrollTrigger) {
      const featureImage = featureCard.querySelector('.feature-image');
      if (featureImage) {
        gsap.fromTo(featureImage,
          { clipPath: 'inset(0 100% 0 0)', opacity: 0 },
          {
            clipPath: 'inset(0 0% 0 0)', opacity: 1,
            duration: 1.2,
            ease: EASE.dramatic,
            scrollTrigger: {
              trigger: featureCard,
              start: 'top 80%',
              once: true
            }
          }
        );
      }
    }

    // Refresh ScrollTrigger
    if (ScrollTrigger) {
      setTimeout(() => ScrollTrigger.refresh(), 150);
    }
  };

  /* ═══════════════════════════════════════════════════════
     MAGNETIC BUTTON EFFECT
     ═══════════════════════════════════════════════════════ */
  document.addEventListener('mousemove', (e) => {
    document.querySelectorAll('.btn-primary, .btn-secondary, .btn-ghost').forEach(btn => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      const dist = Math.sqrt(x * x + y * y);
      if (dist < 100) {
        const pull = 1 - dist / 100;
        gsap.to(btn, {
          x: x * pull * 0.12,
          y: y * pull * 0.12,
          duration: 0.3,
          ease: EASE.entrance
        });
      } else {
        gsap.to(btn, { x: 0, y: 0, duration: 0.5, ease: EASE.entrance });
      }
    });
  });

  /* ═══════════════════════════════════════════════════════
     PREMIUM PAGE TRANSITION (Clip-Path Wipe)
     ═══════════════════════════════════════════════════════ */
  window.pageTransition = function (onMid) {
    const content = document.querySelector('.page-content');
    if (!content) {
      if (onMid) onMid();
      return;
    }

    const tl = gsap.timeline();

    // Exit: wipe up with blur
    tl.to(content, {
      clipPath: 'inset(0 0 100% 0)',
      filter: 'blur(6px)',
      opacity: 0.3,
      scale: 0.98,
      duration: 0.35,
      ease: EASE.exit,
      onComplete: function () {
        if (onMid) onMid();
        // Reset clip for entrance
        gsap.set(content, {
          clipPath: 'inset(100% 0 0 0)',
          filter: 'blur(6px)',
          opacity: 0.3,
          scale: 0.98
        });
        // Enter: wipe down with blur clear
        gsap.to(content, {
          clipPath: 'inset(0 0 0 0)',
          filter: 'blur(0px)',
          opacity: 1,
          scale: 1,
          duration: 0.4,
          ease: EASE.dramatic,
          delay: 0.05
        });
      }
    });
  };

  /* ═══════════════════════════════════════════════════════
     SCROLL PROGRESS BAR
     ═══════════════════════════════════════════════════════ */
  const progressBar = document.getElementById('scroll-progress');
  if (progressBar) {
    window.addEventListener('scroll', () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      progressBar.style.width = progress + '%';
    }, { passive: true });
  }

  /* ═══════════════════════════════════════════════════════
     NAV SCROLL MORPHING
     ═══════════════════════════════════════════════════════ */
  let lastScrollY = 0;
  window.addEventListener('scroll', () => {
    const nav = document.querySelector('.nav');
    if (!nav) return;

    const scrolled = window.scrollY > 50;
    nav.classList.toggle('scrolled', scrolled);

    // Subtle scale morph
    if (scrolled && !nav.dataset.morphed) {
      gsap.to(nav, {
        height: 56,
        duration: 0.4,
        ease: EASE.entrance
      });
      const logo = nav.querySelector('.site-logo');
      if (logo) {
        gsap.to(logo, { scale: 0.85, duration: 0.3, ease: EASE.entrance });
      }
      nav.dataset.morphed = 'true';
    } else if (!scrolled && nav.dataset.morphed) {
      gsap.to(nav, {
        height: 'auto',
        duration: 0.4,
        ease: EASE.entrance
      });
      const logo = nav.querySelector('.site-logo');
      if (logo) {
        gsap.to(logo, { scale: 1, duration: 0.3, ease: EASE.entrance });
      }
      nav.dataset.morphed = '';
    }

    lastScrollY = window.scrollY;
  }, { passive: true });

  /* ═══════════════════════════════════════════════════════
     CART BADGE BOUNCE
     ═══════════════════════════════════════════════════════ */
  const origUpdateCartBadge = window.updateCartBadge;
  window.updateCartBadge = function () {
    if (origUpdateCartBadge) origUpdateCartBadge();
    const badge = document.getElementById('cartBadge');
    if (badge) {
      gsap.fromTo(badge,
        { scale: 1.4, rotate: 10 },
        { scale: 1, rotate: 0, duration: 0.5, ease: 'elastic.out(1, 0.4)' }
      );
    }
  };

  /* ═══════════════════════════════════════════════════════
     THEME TOGGLE ANIMATION
     ═══════════════════════════════════════════════════════ */
  const origToggleTheme = window.toggleTheme;
  window.toggleTheme = function () {
    const btn = document.getElementById('themeToggle');
    if (btn) {
      gsap.fromTo(btn,
        { rotate: 0, scale: 0.8 },
        { rotate: 360, scale: 1, duration: 0.6, ease: EASE.entrance }
      );
    }
    if (origToggleTheme) origToggleTheme();
  };

})();
