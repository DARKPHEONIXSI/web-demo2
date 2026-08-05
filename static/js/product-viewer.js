/* ═══════════════════════════════════════════════════════════
   product-viewer.js — Interactive 3D Product Viewer
   Renders a rotating ice crystal / geometric object that
   users can drag to rotate and zoom with scroll
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  window.init3DProductViewer = function (containerId, productColor) {
    const container = document.getElementById(containerId);
    if (!container || !window.THREE) return;

    const THREE = window.THREE;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0a0e27, 0.02);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 6);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // Main product geometry — Stylized 3D Ice Skate
    const color = productColor || 0x00d4ff;
    const mainMesh = new THREE.Group();
    
    // Blade
    const bladeShape = new THREE.Shape();
    bladeShape.moveTo(-1.5, -0.8);
    bladeShape.lineTo(1.5, -0.8);
    bladeShape.quadraticCurveTo(2.0, -0.8, 2.0, -0.2); // Curved front tip
    bladeShape.lineTo(1.8, -0.2);
    bladeShape.lineTo(1.2, -0.6); // Inner edge
    bladeShape.lineTo(-1.2, -0.6);
    bladeShape.lineTo(-1.5, -0.2);
    bladeShape.lineTo(-1.7, -0.2);
    bladeShape.lineTo(-1.5, -0.8);
    const bladeExtrude = { depth: 0.1, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: 0.02, bevelThickness: 0.02 };
    const bladeGeom = new THREE.ExtrudeGeometry(bladeShape, bladeExtrude);
    const bladeMat = new THREE.MeshStandardMaterial({ color: 0xe8edf5, metalness: 0.9, roughness: 0.1 });
    const blade = new THREE.Mesh(bladeGeom, bladeMat);
    blade.position.z = -0.05;
    mainMesh.add(blade);

    // Boot
    const bootShape = new THREE.Shape();
    bootShape.moveTo(-1.2, -0.2); // Heel bottom
    bootShape.lineTo(1.2, -0.2);  // Toe bottom
    bootShape.quadraticCurveTo(1.6, 0.2, 1.0, 0.8); // Toe box
    bootShape.lineTo(0.2, 1.2);   // Laces area
    bootShape.lineTo(-0.5, 2.8);  // Top front ankle
    bootShape.lineTo(-1.2, 2.8);  // Top back ankle
    bootShape.lineTo(-1.5, 0.5);  // Heel back curve
    bootShape.lineTo(-1.2, -0.2);
    const bootExtrude = { depth: 0.6, bevelEnabled: true, bevelSegments: 4, steps: 1, bevelSize: 0.1, bevelThickness: 0.1 };
    const bootGeom = new THREE.ExtrudeGeometry(bootShape, bootExtrude);
    const mainMat = new THREE.MeshPhysicalMaterial({
      color: color,
      metalness: 0.2,
      roughness: 0.15,
      transparent: true,
      opacity: 0.7,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
    });
    const boot = new THREE.Mesh(bootGeom, mainMat);
    boot.position.z = -0.3;
    mainMesh.add(boot);

    // Wireframe overlay for boot
    const wireMat = new THREE.MeshBasicMaterial({
      color: color,
      wireframe: true,
      transparent: true,
      opacity: 0.15,
    });
    const wireBoot = new THREE.Mesh(bootGeom, wireMat);
    wireBoot.position.z = -0.3;
    mainMesh.add(wireBoot);

    scene.add(mainMesh);
    
    // Scale and center the skate
    mainMesh.scale.setScalar(0.7);
    mainMesh.position.y = -0.5;

    // Inner glow object (attached to mainMesh)
    const glowGeom = new THREE.SphereGeometry(1.0, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.08,
    });
    const glowMesh = new THREE.Mesh(glowGeom, glowMat);
    glowMesh.position.y = 1.0;
    mainMesh.add(glowMesh);

    // Floating mini crystals
    const minis = [];
    for (let i = 0; i < 6; i++) {
      const s = 0.15 + Math.random() * 0.2;
      const g = new THREE.OctahedronGeometry(s, 0);
      const m = new THREE.MeshPhysicalMaterial({
        color: color,
        metalness: 0.3,
        roughness: 0.2,
        transparent: true,
        opacity: 0.4 + Math.random() * 0.3,
      });
      const mesh = new THREE.Mesh(g, m);
      const angle = (i / 6) * Math.PI * 2;
      const radius = 2.5 + Math.random();
      mesh.position.set(Math.cos(angle) * radius, (Math.random() - 0.5) * 2, Math.sin(angle) * radius);
      mesh.userData = { angle, radius, speed: 0.3 + Math.random() * 0.5, yOffset: mesh.position.y };
      minis.push(mesh);
      scene.add(mesh);
    }

    // Lights
    const ambLight = new THREE.AmbientLight(0x334466, 0.8);
    scene.add(ambLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(5, 5, 5);
    scene.add(dirLight);
    const pointLight1 = new THREE.PointLight(color, 1.5, 20);
    pointLight1.position.set(-3, 2, 3);
    scene.add(pointLight1);
    const pointLight2 = new THREE.PointLight(0xa78bfa, 0.8, 15);
    pointLight2.position.set(3, -2, -3);
    scene.add(pointLight2);

    // Drag to rotate
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };
    let rotVelocity = { x: 0, y: 0 };

    renderer.domElement.addEventListener('pointerdown', (e) => {
      isDragging = true;
      prevMouse.x = e.clientX;
      prevMouse.y = e.clientY;
      renderer.domElement.style.cursor = 'grabbing';
    });

    window.addEventListener('pointerup', () => {
      isDragging = false;
      renderer.domElement.style.cursor = 'grab';
    });

    window.addEventListener('pointermove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouse.x;
      const dy = e.clientY - prevMouse.y;
      rotVelocity.x = dy * 0.005;
      rotVelocity.y = dx * 0.005;
      prevMouse.x = e.clientX;
      prevMouse.y = e.clientY;
    });

    // Scroll to zoom
    renderer.domElement.addEventListener('wheel', (e) => {
      e.preventDefault();
      camera.position.z = Math.max(3, Math.min(10, camera.position.z + e.deltaY * 0.01));
    }, { passive: false });

    renderer.domElement.style.cursor = 'grab';

    // Animate
    const clock = new THREE.Clock();
    function animate() {
      requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      // Auto rotate + drag
      if (!isDragging) {
        rotVelocity.x *= 0.95;
        rotVelocity.y *= 0.95;
        mainMesh.rotation.y += 0.003;
      }
      mainMesh.rotation.x += rotVelocity.x;
      mainMesh.rotation.y += rotVelocity.y;

      // Pulse glow
      glowMesh.scale.setScalar(1 + Math.sin(time * 2) * 0.05);
      mainMat.opacity = 0.65 + Math.sin(time * 1.5) * 0.05;

      // Orbit mini crystals
      minis.forEach((m) => {
        m.userData.angle += 0.005 * m.userData.speed;
        m.position.x = Math.cos(m.userData.angle) * m.userData.radius;
        m.position.z = Math.sin(m.userData.angle) * m.userData.radius;
        m.position.y = m.userData.yOffset + Math.sin(time * m.userData.speed) * 0.5;
        m.rotation.x += 0.01;
        m.rotation.y += 0.015;
      });

      renderer.render(scene, camera);
    }
    animate();

    // Resize
    const ro = new ResizeObserver(() => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
    ro.observe(container);
  };
})();
