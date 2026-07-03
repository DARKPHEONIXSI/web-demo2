/**
 * aurora.js — 3D Elements and Animations for the On Ice "Aurora Frost" Theme
 * Requires Three.js and GSAP to be loaded.
 */

document.addEventListener('DOMContentLoaded', () => {
    
  // =========================================================================
  // 1. GLOBAL GSAP ANIMATIONS
  // =========================================================================
  
  if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(ScrollTrigger);

      // Fade-up elements
      gsap.utils.toArray('[data-animate="fade-up"]').forEach(el => {
          gsap.fromTo(el, 
              { y: 30, opacity: 0 },
              { 
                  y: 0, opacity: 1, 
                  duration: 0.8, 
                  ease: "power3.out",
                  scrollTrigger: {
                      trigger: el,
                      start: "top 85%",
                      toggleActions: "play none none reverse"
                  }
              }
          );
      });

      // Cards stagger
      const grids = document.querySelectorAll('.posts-grid, .related-grid, .tech-grid, .gallery-grid, .hero-stats-grid');
      grids.forEach(grid => {
          const cards = grid.querySelectorAll('[data-animate="card"]');
          if (cards.length > 0) {
              gsap.fromTo(cards,
                  { y: 40, opacity: 0 },
                  {
                      y: 0, opacity: 1,
                      duration: 0.6,
                      stagger: 0.1,
                      ease: "power2.out",
                      scrollTrigger: {
                          trigger: grid,
                          start: "top 80%",
                          toggleActions: "play none none reverse"
                      }
                  }
              );
          }
      });

      // Hero animations (if present)
      const heroLeft = document.querySelector('[data-animate="hero"]');
      if (heroLeft) {
          gsap.fromTo(heroLeft.children,
              { x: -30, opacity: 0 },
              {
                  x: 0, opacity: 1,
                  duration: 0.8,
                  stagger: 0.1,
                  ease: "power3.out",
                  delay: 0.2
              }
          );
      }
      
      const heroRight = document.querySelector('[data-animate="hero-right"]');
      if (heroRight) {
          gsap.fromTo(heroRight,
              { opacity: 0, scale: 0.95 },
              {
                  opacity: 1, scale: 1,
                  duration: 1.2,
                  ease: "power2.out",
                  delay: 0.4
              }
          );
      }
  }

  // =========================================================================
  // 2. AMBIENT BACKGROUND PARTICLES (THREE.JS)
  // =========================================================================

  if (typeof THREE !== 'undefined') {
      const bgCanvas = document.getElementById('aurora-canvas');
      if (bgCanvas) {
          const scene = new THREE.Scene();
          
          // Camera
          const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
          camera.position.z = 30;

          // Renderer
          const renderer = new THREE.WebGLRenderer({ canvas: bgCanvas, alpha: true, antialias: true });
          renderer.setSize(window.innerWidth, window.innerHeight);
          renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

          // Particles
          const particlesGeometry = new THREE.BufferGeometry();
          const particlesCount = 300;
          const posArray = new Float32Array(particlesCount * 3);
          const scales = new Float32Array(particlesCount);

          for(let i = 0; i < particlesCount * 3; i++) {
              posArray[i] = (Math.random() - 0.5) * 100;
          }
          for(let i = 0; i < particlesCount; i++) {
              scales[i] = Math.random();
          }

          particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
          particlesGeometry.setAttribute('aScale', new THREE.BufferAttribute(scales, 1));

          // Material with aurora colors
          const particlesMaterial = new THREE.PointsMaterial({
              size: 0.15,
              color: 0x38e0b0, // Aurora Teal
              transparent: true,
              opacity: 0.6,
              blending: THREE.AdditiveBlending
          });

          const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
          scene.add(particlesMesh);

          // Mouse interaction
          let mouseX = 0;
          let mouseY = 0;
          let targetX = 0;
          let targetY = 0;
          const windowHalfX = window.innerWidth / 2;
          const windowHalfY = window.innerHeight / 2;

          document.addEventListener('mousemove', (event) => {
              mouseX = (event.clientX - windowHalfX);
              mouseY = (event.clientY - windowHalfY);
          });

          // Animation loop
          const clock = new THREE.Clock();

          const tick = () => {
              const elapsedTime = clock.getElapsedTime();

              // Update particles
              particlesMesh.rotation.y = elapsedTime * 0.05;
              particlesMesh.rotation.x = elapsedTime * 0.02;

              // Parallax effect
              targetX = mouseX * 0.001;
              targetY = mouseY * 0.001;
              
              particlesMesh.rotation.y += 0.05 * (targetX - particlesMesh.rotation.y);
              particlesMesh.rotation.x += 0.05 * (targetY - particlesMesh.rotation.x);
              
              // Color shift
              const hue = (elapsedTime * 0.05) % 1;
              const color = new THREE.Color().setHSL(0.5 + (hue * 0.2), 0.8, 0.6); // Shifts between teal and cyan/blue
              particlesMaterial.color.copy(color);

              // Render
              renderer.render(scene, camera);

              // Call tick again on the next frame
              window.requestAnimationFrame(tick);
          };

          tick();

          // Resize handler
          window.addEventListener('resize', () => {
              camera.aspect = window.innerWidth / window.innerHeight;
              camera.updateProjectionMatrix();
              renderer.setSize(window.innerWidth, window.innerHeight);
          });
      }
  }

  // =========================================================================
  // 3. HERO 3D ICE GLOBE (THREE.JS)
  // =========================================================================

  const heroContainer = document.getElementById('hero3d');
  
  if (heroContainer && typeof THREE !== 'undefined') {
      const hScene = new THREE.Scene();
      
      const width = heroContainer.clientWidth || window.innerWidth / 2;
      const height = heroContainer.clientHeight || window.innerHeight * 0.8;
      
      const hCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
      hCamera.position.z = 5;
      
      const hRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
      hRenderer.setSize(width, height);
      hRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      heroContainer.appendChild(hRenderer.domElement);

      // Icosahedron (Ice crystal sphere)
      const geometry = new THREE.IcosahedronGeometry(1.5, 1);
      
      // Wireframe material
      const material = new THREE.MeshBasicMaterial({
          color: 0x38e0b0,
          wireframe: true,
          transparent: true,
          opacity: 0.3
      });
      
      const sphere = new THREE.Mesh(geometry, material);
      hScene.add(sphere);
      
      // Inner solid sphere for depth
      const innerGeometry = new THREE.IcosahedronGeometry(1.48, 1);
      const innerMaterial = new THREE.MeshBasicMaterial({
          color: 0x050814,
          transparent: true,
          opacity: 0.8
      });
      const innerSphere = new THREE.Mesh(innerGeometry, innerMaterial);
      hScene.add(innerSphere);

      // Points (Vertices)
      const pointsMat = new THREE.PointsMaterial({
          color: 0x00d4ff,
          size: 0.05,
          transparent: true,
          opacity: 0.8,
          blending: THREE.AdditiveBlending
      });
      const points = new THREE.Points(geometry, pointsMat);
      hScene.add(points);

      // Mouse interaction for hero sphere
      let hMouseX = 0;
      let hMouseY = 0;
      
      heroContainer.addEventListener('mousemove', (e) => {
          const rect = heroContainer.getBoundingClientRect();
          hMouseX = ((e.clientX - rect.left) / width) * 2 - 1;
          hMouseY = -((e.clientY - rect.top) / height) * 2 + 1;
      });
      
      heroContainer.addEventListener('mouseleave', () => {
          hMouseX = 0;
          hMouseY = 0;
      });

      const hClock = new THREE.Clock();

      const hTick = () => {
          const elapsedTime = hClock.getElapsedTime();

          // Base rotation
          sphere.rotation.y = elapsedTime * 0.1;
          sphere.rotation.x = elapsedTime * 0.05;
          
          innerSphere.rotation.y = elapsedTime * 0.1;
          innerSphere.rotation.x = elapsedTime * 0.05;
          
          points.rotation.y = elapsedTime * 0.1;
          points.rotation.x = elapsedTime * 0.05;

          // Mouse influence
          sphere.rotation.y += hMouseX * 0.5;
          sphere.rotation.x -= hMouseY * 0.5;
          
          innerSphere.rotation.y += hMouseX * 0.5;
          innerSphere.rotation.x -= hMouseY * 0.5;
          
          points.rotation.y += hMouseX * 0.5;
          points.rotation.x -= hMouseY * 0.5;
          
          // Color pulsation
          const pulse = Math.sin(elapsedTime * 2) * 0.5 + 0.5;
          material.opacity = 0.1 + (pulse * 0.2);
          pointsMat.size = 0.03 + (pulse * 0.03);

          hRenderer.render(hScene, hCamera);
          window.requestAnimationFrame(hTick);
      };

      hTick();

      // Resize handler
      window.addEventListener('resize', () => {
          if (!heroContainer) return;
          const newWidth = heroContainer.clientWidth || window.innerWidth / 2;
          const newHeight = heroContainer.clientHeight || window.innerHeight * 0.8;
          
          hCamera.aspect = newWidth / newHeight;
          hCamera.updateProjectionMatrix();
          hRenderer.setSize(newWidth, newHeight);
      });
  }

  // =========================================================================
  // 4. SKATER SCROLL ANIMATION & DOT RAIL
  // =========================================================================

  const dotRail = document.getElementById('dotRail');
  const skater = document.getElementById('scrollSkater');
  const dots = document.querySelectorAll('.dot-rail .dot');

  if (dotRail && skater && dots.length > 0 && typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      // Calculate total scrollable height
      const scrollHeight = document.body.scrollHeight - window.innerHeight;

      // Animate skater down the rail
      gsap.to(skater, {
          top: "100%",
          ease: "none",
          scrollTrigger: {
              trigger: document.body,
              start: "top top",
              end: "bottom bottom",
              scrub: 1, // Smooth out the scrubbing
              onUpdate: (self) => {
                  const progress = self.progress;
                  const velocity = self.getVelocity();
                  
                  // Gliding Sway (Strides)
                  // Use progress to calculate a smooth sine wave (e.g. 10 full strides down the page)
                  const sway = Math.sin(progress * Math.PI * 20) * 15; // +/- 15px
                  
                  // Leaning Rotation based on velocity and sway
                  // Lean forward based on speed, lean side-to-side based on the stride
                  const forwardLean = Math.max(-10, Math.min(20, velocity / 150));
                  const sideLean = Math.cos(progress * Math.PI * 20) * 10;
                  const rotation = forwardLean + sideLean;

                  gsap.to(skater, { 
                      x: sway, 
                      rotation: rotation, 
                      duration: 0.3, 
                      ease: "power1.out",
                      overwrite: "auto" 
                  });

                  // Light up dots based on progress
                  dots.forEach((dot, index) => {
                      const dotProgress = index / (dots.length - 1);
                      if (progress >= dotProgress - 0.05 && progress <= dotProgress + 0.05) {
                          dot.classList.add('active');
                      } else {
                          dot.classList.remove('active');
                      }
                  });
              }
          }
      });
      
      // Click dots to scroll
      dots.forEach((dot, index) => {
          dot.addEventListener('click', () => {
              const targetY = (index / (dots.length - 1)) * scrollHeight;
              window.scrollTo({ top: targetY, behavior: 'smooth' });
          });
      });
  }

});
