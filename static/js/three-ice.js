/* ═══════════════════════════════════════════════════════════
   three-ice.js — Realistic 3D Figure Skating Scene
   Anatomical skaters, flowing costumes, hair physics,
   graceful choreography, ice trails, stage lighting
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  const canvas = document.getElementById('three-canvas');
  if (!canvas) return;

  /* ── GPU Performance Check ───────────────────────────── */
  function checkGPU() {
    try {
      const c = document.createElement('canvas');
      const gl = c.getContext('webgl') || c.getContext('experimental-webgl');
      if (!gl) return false;
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      if (ext) {
        const r = gl.getParameter(ext.UNMASKED_RENDERER_WEBGL).toLowerCase();
        if (r.includes('swiftshader') || r.includes('llvmpipe') || r.includes('software')) return false;
      }
      return true;
    } catch (e) { return false; }
  }

  const isMobile = /Mobi|Android|iPhone/i.test(navigator.userAgent);
  const hasGPU = checkGPU();

  if (!hasGPU || (isMobile && window.innerWidth < 640)) {
    canvas.style.display = 'none';
    document.body.style.background = 'linear-gradient(180deg, #060a1a 0%, #0a0e27 40%, #111a42 100%)';
    return;
  }

  /* ── Three.js Setup ──────────────────────────────────── */
  const THREE = window.THREE;
  if (!THREE) return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 50;

  const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: !isMobile,
    powerPreference: 'high-performance'
  });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);
  renderer.shadowMap.enabled = !isMobile;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  /* ── Mouse Tracking ──────────────────────────────────── */
  const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
  document.addEventListener('mousemove', (e) => {
    mouse.targetX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouse.targetY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  /* ── Snowflakes ──────────────────────────────────────── */
  const snowCount = isMobile ? 200 : 500;
  const snowGeometry = new THREE.BufferGeometry();
  const snowPositions = new Float32Array(snowCount * 3);
  const snowSpeeds = new Float32Array(snowCount);
  const snowSizes = new Float32Array(snowCount);

  for (let i = 0; i < snowCount; i++) {
    snowPositions[i * 3] = (Math.random() - 0.5) * 120;
    snowPositions[i * 3 + 1] = (Math.random() - 0.5) * 100;
    snowPositions[i * 3 + 2] = (Math.random() - 0.5) * 80;
    snowSpeeds[i] = 0.02 + Math.random() * 0.04;
    snowSizes[i] = 0.5 + Math.random() * 1.5;
  }

  snowGeometry.setAttribute('position', new THREE.BufferAttribute(snowPositions, 3));
  snowGeometry.setAttribute('size', new THREE.BufferAttribute(snowSizes, 1));

  const snowMaterial = new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uColor: { value: new THREE.Color(0x7eb8ff) },
      uOpacity: { value: 0.6 }
    },
    vertexShader: `
      attribute float size;
      varying float vOpacity;
      void main() {
        vOpacity = size / 2.0;
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * (30.0 / -mvPosition.z);
        gl_Position = projectionMatrix * mvPosition;
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      uniform float uOpacity;
      varying float vOpacity;
      void main() {
        float d = length(gl_PointCoord - vec2(0.5));
        if (d > 0.5) discard;
        float alpha = smoothstep(0.5, 0.1, d) * uOpacity * vOpacity;
        gl_FragColor = vec4(uColor, alpha);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  });

  const snowParticles = new THREE.Points(snowGeometry, snowMaterial);
  scene.add(snowParticles);

  /* ── Ice Rink Floor & Markings ───────────────────────── */
  const rinkGroup = new THREE.Group();

  const rinkWidth = 120;
  const rinkDepth = 60;
  const cornerRadius = 14;

  const rinkShape = new THREE.Shape();
  rinkShape.moveTo(-rinkWidth / 2 + cornerRadius, -rinkDepth / 2);
  rinkShape.lineTo(rinkWidth / 2 - cornerRadius, -rinkDepth / 2);
  rinkShape.quadraticCurveTo(rinkWidth / 2, -rinkDepth / 2, rinkWidth / 2, -rinkDepth / 2 + cornerRadius);
  rinkShape.lineTo(rinkWidth / 2, rinkDepth / 2 - cornerRadius);
  rinkShape.quadraticCurveTo(rinkWidth / 2, rinkDepth / 2, rinkWidth / 2 - cornerRadius, rinkDepth / 2);
  rinkShape.lineTo(-rinkWidth / 2 + cornerRadius, rinkDepth / 2);
  rinkShape.quadraticCurveTo(-rinkWidth / 2, rinkDepth / 2, -rinkWidth / 2, rinkDepth / 2 - cornerRadius);
  rinkShape.lineTo(-rinkWidth / 2, -rinkDepth / 2 + cornerRadius);
  rinkShape.quadraticCurveTo(-rinkWidth / 2, -rinkDepth / 2, -rinkWidth / 2 + cornerRadius, -rinkDepth / 2);

  const rinkGeometry = new THREE.ShapeGeometry(rinkShape);
  const rinkMaterial = new THREE.MeshStandardMaterial({
    color: 0x88bbff,
    transparent: true,
    opacity: 0.25,
    roughness: 0.05,
    metalness: 0.9,
    side: THREE.DoubleSide
  });
  const iceRink = new THREE.Mesh(rinkGeometry, rinkMaterial);
  iceRink.rotation.x = -Math.PI / 2;
  rinkGroup.add(iceRink);

  // Rink Boards
  const boardMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.2 });
  const innerShape = new THREE.Shape();
  const innerW = rinkWidth - 1;
  const innerD = rinkDepth - 1;
  innerShape.moveTo(-innerW / 2 + cornerRadius, -innerD / 2);
  innerShape.lineTo(innerW / 2 - cornerRadius, -innerD / 2);
  innerShape.quadraticCurveTo(innerW / 2, -innerD / 2, innerW / 2, -innerD / 2 + cornerRadius);
  innerShape.lineTo(innerW / 2, innerD / 2 - cornerRadius);
  innerShape.quadraticCurveTo(innerW / 2, innerD / 2, innerW / 2 - cornerRadius, innerD / 2);
  innerShape.lineTo(-innerW / 2 + cornerRadius, innerD / 2);
  innerShape.quadraticCurveTo(-innerW / 2, innerD / 2, -innerW / 2, innerD / 2 - cornerRadius);
  innerShape.lineTo(-innerW / 2, -innerD / 2 + cornerRadius);
  innerShape.quadraticCurveTo(-innerW / 2, -innerD / 2, -innerW / 2 + cornerRadius, -innerD / 2);

  rinkShape.holes.push(innerShape);
  const hollowBoardGeo = new THREE.ExtrudeGeometry(rinkShape, { depth: 3, bevelEnabled: false });
  const hollowBoards = new THREE.Mesh(hollowBoardGeo, boardMaterial);
  hollowBoards.rotation.x = -Math.PI / 2;
  rinkGroup.add(hollowBoards);

  // Rink Markings
  const redLineGeo = new THREE.PlaneGeometry(1, rinkDepth);
  const redLineMat = new THREE.MeshBasicMaterial({ color: 0xcc0000, transparent: true, opacity: 0.3, side: THREE.DoubleSide, depthWrite: false });
  const redLine = new THREE.Mesh(redLineGeo, redLineMat);
  redLine.rotation.x = -Math.PI / 2;
  redLine.position.y = 0.02;
  redLine.renderOrder = 1;
  rinkGroup.add(redLine);

  const blueLineGeo = new THREE.PlaneGeometry(1, rinkDepth);
  const blueLineMat = new THREE.MeshBasicMaterial({ color: 0x0000cc, transparent: true, opacity: 0.3, side: THREE.DoubleSide, depthWrite: false });

  const blueLine1 = new THREE.Mesh(blueLineGeo, blueLineMat);
  blueLine1.rotation.x = -Math.PI / 2;
  blueLine1.position.set(-20, 0.02, 0);
  blueLine1.renderOrder = 1;
  rinkGroup.add(blueLine1);

  const blueLine2 = new THREE.Mesh(blueLineGeo, blueLineMat);
  blueLine2.rotation.x = -Math.PI / 2;
  blueLine2.position.set(20, 0.02, 0);
  blueLine2.renderOrder = 1;
  rinkGroup.add(blueLine2);

  const circleGeo = new THREE.RingGeometry(8, 8.5, 32);
  const circleMat = new THREE.MeshBasicMaterial({ color: 0x0000cc, transparent: true, opacity: 0.3, side: THREE.DoubleSide, depthWrite: false });
  const centerCircle = new THREE.Mesh(circleGeo, circleMat);
  centerCircle.rotation.x = -Math.PI / 2;
  centerCircle.position.y = 0.02;
  centerCircle.renderOrder = 1;
  rinkGroup.add(centerCircle);

  rinkGroup.position.y = -25;
  scene.add(rinkGroup);

  /* ── Aurora Borealis ─────────────────────────────────── */
  const auroraGeometry = new THREE.PlaneGeometry(160, 40, 64, 16);
  const auroraMaterial = new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector2(0, 0) }
    },
    vertexShader: `
      uniform float uTime;
      varying vec2 vUv;
      varying float vDisplace;
      void main() {
        vUv = uv;
        vec3 pos = position;
        float wave = sin(pos.x * 0.08 + uTime * 0.3) * 3.0;
        wave += sin(pos.x * 0.04 + uTime * 0.15) * 5.0;
        wave += cos(pos.x * 0.12 + uTime * 0.5) * 1.5;
        pos.y += wave;
        vDisplace = wave / 10.0;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      varying vec2 vUv;
      varying float vDisplace;
      void main() {
        vec3 colorA = vec3(0.0, 0.83, 1.0);
        vec3 colorB = vec3(0.0, 1.0, 0.53);
        vec3 colorC = vec3(0.65, 0.55, 0.98);
        float mix1 = sin(vUv.x * 3.14 + uTime * 0.2) * 0.5 + 0.5;
        float mix2 = cos(vUv.x * 2.0 + uTime * 0.15) * 0.5 + 0.5;
        vec3 color = mix(colorA, colorB, mix1);
        color = mix(color, colorC, mix2 * 0.4);
        float alpha = smoothstep(0.0, 0.5, vUv.y) * smoothstep(1.0, 0.5, vUv.y);
        alpha *= 0.15 + abs(vDisplace) * 0.05;
        alpha *= smoothstep(0.0, 0.2, vUv.x) * smoothstep(1.0, 0.8, vUv.x);
        gl_FragColor = vec4(color, alpha);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide
  });

  const aurora = new THREE.Mesh(auroraGeometry, auroraMaterial);
  aurora.position.set(0, 30, -30);
  scene.add(aurora);

  /* ═══════════════════════════════════════════════════════
     REALISTIC FIGURE SKATERS
     ═══════════════════════════════════════════════════════ */

  /**
   * Creates a realistic figure skater with anatomical proportions,
   * flowing costume, and hair physics chain.
   */
  function createRealisticSkater(dressColorHex, scale) {
    const group = new THREE.Group();

    const dressColor = new THREE.Color(dressColorHex);
    const skinColor = new THREE.Color(0xf5cdb6);
    const hairColor = new THREE.Color(0x2a1a0e);
    const bladeColor = new THREE.Color(0xd0d0d0);
    const tightsColor = new THREE.Color(0xf0d0b8);

    /* ── Materials ──────────────────────────────────────── */
    const dressMat = new THREE.MeshPhysicalMaterial({
      color: dressColor,
      roughness: 0.25,
      metalness: 0.15,
      transparent: true,
      opacity: 0.92,
      clearcoat: 0.4,
      clearcoatRoughness: 0.3,
      side: THREE.DoubleSide
    });

    const skinMat = new THREE.MeshStandardMaterial({
      color: skinColor,
      roughness: 0.55,
      metalness: 0.02
    });

    const tightsMat = new THREE.MeshStandardMaterial({
      color: tightsColor,
      roughness: 0.4,
      metalness: 0.0,
      transparent: true,
      opacity: 0.9
    });

    const hairMat = new THREE.MeshStandardMaterial({
      color: hairColor,
      roughness: 0.6,
      metalness: 0.1
    });

    const skateMat = new THREE.MeshStandardMaterial({
      color: 0xf8f8f8,
      roughness: 0.15,
      metalness: 0.1
    });

    const bladeMat = new THREE.MeshStandardMaterial({
      color: bladeColor,
      metalness: 1.0,
      roughness: 0.05
    });

    /* Sequin sparkle points on dress */
    const sequinGeo = new THREE.BufferGeometry();
    const sequinCount = 40;
    const sequinPositions = new Float32Array(sequinCount * 3);
    const sequinSizes = new Float32Array(sequinCount);
    for (let i = 0; i < sequinCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const r = 0.4 + Math.random() * 0.5;
      const h = 2.8 + Math.random() * 2.2;
      sequinPositions[i * 3] = Math.cos(angle) * r;
      sequinPositions[i * 3 + 1] = h;
      sequinPositions[i * 3 + 2] = Math.sin(angle) * r;
      sequinSizes[i] = 0.06 + Math.random() * 0.08;
    }
    sequinGeo.setAttribute('position', new THREE.BufferAttribute(sequinPositions, 3));
    sequinGeo.setAttribute('size', new THREE.BufferAttribute(sequinSizes, 1));
    const sequinMat = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.12,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    const sequins = new THREE.Points(sequinGeo, sequinMat);
    group.add(sequins);

    /* ── Torso (Lathe for natural curves) ──────────────── */
    // Profile: waist → ribcage → shoulders
    const torsoProfile = [
      new THREE.Vector2(0.42, 0),    // waist
      new THREE.Vector2(0.40, 0.3),
      new THREE.Vector2(0.44, 0.6),  // ribcage
      new THREE.Vector2(0.50, 0.9),
      new THREE.Vector2(0.55, 1.2),  // bust
      new THREE.Vector2(0.50, 1.5),
      new THREE.Vector2(0.42, 1.7),  // shoulders narrow
      new THREE.Vector2(0.25, 1.9),  // neck base
    ];
    const torsoGeo = new THREE.LatheGeometry(torsoProfile, 16);
    const torso = new THREE.Mesh(torsoGeo, dressMat);
    torso.position.y = 2.8;
    group.add(torso);

    /* ── Skirt (Ring of flowing triangles with physics) ─── */
    const skirtSegments = 24;
    const skirtGeo = new THREE.ConeGeometry(1.6, 2.0, skirtSegments, 1, true);
    const skirt = new THREE.Mesh(skirtGeo, dressMat);
    skirt.position.y = 2.2;
    // Store original vertices for cloth sim
    skirt.userData.originalPositions = skirtGeo.attributes.position.array.slice();
    group.add(skirt);

    // Skirt ruffle edge (tulle-like layer)
    const ruffleGeo = new THREE.RingGeometry(0.3, 1.7, skirtSegments, 1);
    const ruffleMat = dressMat.clone();
    ruffleMat.opacity = 0.5;
    ruffleMat.side = THREE.DoubleSide;
    const ruffle = new THREE.Mesh(ruffleGeo, ruffleMat);
    ruffle.rotation.x = -Math.PI / 2;
    ruffle.position.y = 1.2;
    group.add(ruffle);

    /* ── Neck & Head ───────────────────────────────────── */
    const neckGeo = new THREE.CylinderGeometry(0.15, 0.18, 0.5, 12);
    const neck = new THREE.Mesh(neckGeo, skinMat);
    neck.position.y = 4.85;
    group.add(neck);

    // Head — slightly elongated sphere for elegance
    const headGeo = new THREE.SphereGeometry(0.5, 20, 20);
    headGeo.scale(1, 1.08, 0.95);
    const head = new THREE.Mesh(headGeo, skinMat);
    head.position.y = 5.55;
    group.add(head);

    /* ── Face details ──────────────────────────────────── */
    // Eyes (small dark spheres)
    const eyeGeo = new THREE.SphereGeometry(0.05, 8, 8);
    const eyeMat = new THREE.MeshBasicMaterial({ color: 0x1a1a2e });
    const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
    leftEye.position.set(-0.15, 5.6, 0.42);
    group.add(leftEye);
    const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
    rightEye.position.set(0.15, 5.6, 0.42);
    group.add(rightEye);

    // Lips
    const lipGeo = new THREE.SphereGeometry(0.08, 8, 6);
    lipGeo.scale(1.4, 0.5, 0.6);
    const lipMat = new THREE.MeshStandardMaterial({ color: 0xd4727a, roughness: 0.3 });
    const lips = new THREE.Mesh(lipGeo, lipMat);
    lips.position.set(0, 5.38, 0.4);
    group.add(lips);

    /* ── Hair (bun + crown + ponytail chain) ───────────── */
    // Hair crown (cap over head)
    const hairCapGeo = new THREE.SphereGeometry(0.52, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.55);
    const hairCap = new THREE.Mesh(hairCapGeo, hairMat);
    hairCap.position.y = 5.55;
    group.add(hairCap);

    // Bun
    const bunGeo = new THREE.SphereGeometry(0.25, 12, 12);
    const bun = new THREE.Mesh(bunGeo, hairMat);
    bun.position.set(0, 5.95, -0.3);
    group.add(bun);

    // Ponytail chain (spring physics)
    const ponytailChain = [];
    const ponytailSegments = 5;
    for (let i = 0; i < ponytailSegments; i++) {
      const seg = new THREE.Mesh(
        new THREE.SphereGeometry(0.12 - i * 0.015, 8, 8),
        hairMat
      );
      seg.position.set(0, 5.7 - i * 0.28, -0.4 - i * 0.12);
      seg.userData.restY = seg.position.y;
      seg.userData.restZ = seg.position.z;
      seg.userData.velocityX = 0;
      seg.userData.velocityZ = 0;
      ponytailChain.push(seg);
      group.add(seg);
    }

    /* ── Arms (Tube geometry for smooth limbs) ─────────── */
    function createArm() {
      const shoulderPivot = new THREE.Group();

      // Upper arm
      const upperArmGeo = new THREE.CylinderGeometry(0.12, 0.10, 1.3, 10);
      const upperArm = new THREE.Mesh(upperArmGeo, skinMat);
      upperArm.position.y = -0.65;
      shoulderPivot.add(upperArm);

      // Elbow pivot
      const elbowPivot = new THREE.Group();
      elbowPivot.position.y = -1.3;
      shoulderPivot.add(elbowPivot);

      // Forearm
      const forearmGeo = new THREE.CylinderGeometry(0.10, 0.07, 1.2, 10);
      const forearm = new THREE.Mesh(forearmGeo, skinMat);
      forearm.position.y = -0.6;
      elbowPivot.add(forearm);

      // Hand (elegant flattened sphere)
      const handGeo = new THREE.SphereGeometry(0.09, 8, 8);
      handGeo.scale(1, 0.6, 1.3);
      const hand = new THREE.Mesh(handGeo, skinMat);
      hand.position.y = -1.2;
      elbowPivot.add(hand);

      // Fingers (3 small capsules for elegance)
      for (let f = -1; f <= 1; f++) {
        const fingerGeo = new THREE.CylinderGeometry(0.02, 0.015, 0.2, 6);
        const finger = new THREE.Mesh(fingerGeo, skinMat);
        finger.position.set(f * 0.04, -1.35, 0);
        finger.rotation.x = 0.1;
        elbowPivot.add(finger);
      }

      return { shoulder: shoulderPivot, elbow: elbowPivot };
    }

    const leftArm = createArm();
    leftArm.shoulder.position.set(-0.55, 4.6, 0);
    leftArm.shoulder.rotation.z = Math.PI / 7;
    group.add(leftArm.shoulder);

    const rightArm = createArm();
    rightArm.shoulder.position.set(0.55, 4.6, 0);
    rightArm.shoulder.rotation.z = -Math.PI / 7;
    group.add(rightArm.shoulder);

    /* ── Legs ──────────────────────────────────────────── */
    function createLeg() {
      const hipPivot = new THREE.Group();

      // Thigh
      const thighGeo = new THREE.CylinderGeometry(0.18, 0.14, 1.5, 12);
      const thigh = new THREE.Mesh(thighGeo, tightsMat);
      thigh.position.y = -0.75;
      hipPivot.add(thigh);

      // Knee pivot
      const kneePivot = new THREE.Group();
      kneePivot.position.y = -1.5;
      hipPivot.add(kneePivot);

      // Shin
      const shinGeo = new THREE.CylinderGeometry(0.14, 0.09, 1.5, 12);
      const shin = new THREE.Mesh(shinGeo, tightsMat);
      shin.position.y = -0.75;
      kneePivot.add(shin);

      // Boot
      const bootGeo = new THREE.BoxGeometry(0.3, 0.5, 0.6);
      bootGeo.translate(0, 0, 0.1);
      const boot = new THREE.Mesh(bootGeo, skateMat);
      boot.position.set(0, -1.55, 0);
      kneePivot.add(boot);

      // Blade
      const bladeGeo = new THREE.BoxGeometry(0.03, 0.12, 0.9);
      const blade = new THREE.Mesh(bladeGeo, bladeMat);
      blade.position.set(0, -1.75, 0.15);
      kneePivot.add(blade);

      // Blade edge (thin line for realism)
      const edgeGeo = new THREE.BoxGeometry(0.005, 0.03, 0.95);
      const edgeMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const edge = new THREE.Mesh(edgeGeo, edgeMat);
      edge.position.set(0, -1.82, 0.15);
      kneePivot.add(edge);

      return { hip: hipPivot, knee: kneePivot };
    }

    const leftLeg = createLeg();
    leftLeg.hip.position.set(-0.22, 2.8, 0);
    group.add(leftLeg.hip);

    const rightLeg = createLeg();
    rightLeg.hip.position.set(0.22, 2.8, 0);
    group.add(rightLeg.hip);

    group.scale.set(scale, scale, scale);

    return {
      root: group,
      leftArm, rightArm,
      leftLeg, rightLeg,
      skirt, ruffle, sequins,
      ponytailChain,
      dressMat, skinMat, tightsMat
    };
  }

  /* ── Choreography Poses ──────────────────────────────── */
  // Smooth interpolation helper
  function lerpAngle(current, target, t) {
    return current + (target - current) * t;
  }

  const POSES = {
    glide: {
      leftArm: { shoulder: { x: -0.3, z: Math.PI / 5 }, elbow: { x: -0.15 } },
      rightArm: { shoulder: { x: 0.3, z: -Math.PI / 5 }, elbow: { x: -0.15 } },
      leftLeg: { hip: { x: 0 }, knee: { x: 0 } },
      rightLeg: { hip: { x: 0 }, knee: { x: 0 } },
      bodyLean: 0
    },
    arabesque: {
      leftArm: { shoulder: { x: -0.5, z: Math.PI / 3 }, elbow: { x: -0.1 } },
      rightArm: { shoulder: { x: 0.2, z: -Math.PI / 2.5 }, elbow: { x: -0.05 } },
      leftLeg: { hip: { x: 0.1 }, knee: { x: 0.05 } },
      rightLeg: { hip: { x: -1.5 }, knee: { x: 0.2 } },  // Extended back
      bodyLean: 0.15
    },
    spiral: {
      leftArm: { shoulder: { x: -0.8, z: Math.PI / 2.8 }, elbow: { x: -0.1 } },
      rightArm: { shoulder: { x: 0.6, z: -Math.PI / 2.2 }, elbow: { x: 0 } },
      leftLeg: { hip: { x: 0 }, knee: { x: 0 } },
      rightLeg: { hip: { x: -2.0 }, knee: { x: 0 } },  // High extension
      bodyLean: 0.3
    },
    insideEdge: {
      leftArm: { shoulder: { x: -0.45, z: Math.PI / 3.4 }, elbow: { x: -0.1 } },
      rightArm: { shoulder: { x: 0.15, z: -Math.PI / 2.8 }, elbow: { x: -0.05 } },
      leftLeg: { hip: { x: 0.2 }, knee: { x: 0.25 } },
      rightLeg: { hip: { x: -0.25 }, knee: { x: 0.1 } },
      bodyLean: -0.22
    },
    outsideEdge: {
      leftArm: { shoulder: { x: 0.15, z: Math.PI / 2.8 }, elbow: { x: -0.05 } },
      rightArm: { shoulder: { x: -0.45, z: -Math.PI / 3.4 }, elbow: { x: -0.1 } },
      leftLeg: { hip: { x: -0.25 }, knee: { x: 0.1 } },
      rightLeg: { hip: { x: 0.2 }, knee: { x: 0.25 } },
      bodyLean: 0.22
    },
    threeTurn: {
      leftArm: { shoulder: { x: -0.2, z: Math.PI / 2.2 }, elbow: { x: -0.2 } },
      rightArm: { shoulder: { x: -0.2, z: -Math.PI / 2.2 }, elbow: { x: -0.2 } },
      leftLeg: { hip: { x: 0.1 }, knee: { x: 0.45 } },
      rightLeg: { hip: { x: -0.15 }, knee: { x: 0.2 } },
      bodyLean: 0
    },
    laybackSpin: {
      leftArm: { shoulder: { x: -1.2, z: Math.PI / 6 }, elbow: { x: -0.3 } },
      rightArm: { shoulder: { x: -1.2, z: -Math.PI / 6 }, elbow: { x: -0.3 } },
      leftLeg: { hip: { x: 0.2 }, knee: { x: -0.3 } },
      rightLeg: { hip: { x: 0 }, knee: { x: 0 } },
      bodyLean: -0.4  // Arching backward
    },
    sitSpin: {
      leftArm: { shoulder: { x: 0.5, z: Math.PI / 6 }, elbow: { x: -0.4 } },
      rightArm: { shoulder: { x: 0.5, z: -Math.PI / 6 }, elbow: { x: -0.4 } },
      leftLeg: { hip: { x: -2.2 }, knee: { x: 2.5 } },  // Crouched
      rightLeg: { hip: { x: -0.3 }, knee: { x: 0 } },  // Extended forward
      bodyLean: 0.6
    },
    camelSpin: {
      leftArm: { shoulder: { x: -0.2, z: Math.PI / 2.5 }, elbow: { x: -0.1 } },
      rightArm: { shoulder: { x: -0.2, z: -Math.PI / 2.5 }, elbow: { x: -0.1 } },
      leftLeg: { hip: { x: 0 }, knee: { x: 0 } },
      rightLeg: { hip: { x: -1.57 }, knee: { x: 0 } },  // Horizontal back
      bodyLean: 0.5
    },
    jumpTuck: {
      leftArm: { shoulder: { x: 0, z: Math.PI / 10 }, elbow: { x: -0.8 } },
      rightArm: { shoulder: { x: 0, z: -Math.PI / 10 }, elbow: { x: -0.8 } },
      leftLeg: { hip: { x: -0.3 }, knee: { x: 0.3 } },
      rightLeg: { hip: { x: -0.3 }, knee: { x: 0.3 } },
      bodyLean: 0
    },
    landing: {
      leftArm: { shoulder: { x: -0.5, z: Math.PI / 2.5 }, elbow: { x: -0.1 } },
      rightArm: { shoulder: { x: 0.3, z: -Math.PI / 2 }, elbow: { x: -0.05 } },
      leftLeg: { hip: { x: -0.6 }, knee: { x: 0.8 } },  // Bent landing leg
      rightLeg: { hip: { x: -1.2 }, knee: { x: 0 } },    // Extended behind
      bodyLean: 0.1
    }
  };

  function applyPose(skater, pose, blendFactor) {
    const t = Math.min(blendFactor, 1);
    // Left arm
    skater.leftArm.shoulder.rotation.x = lerpAngle(skater.leftArm.shoulder.rotation.x, pose.leftArm.shoulder.x, t);
    skater.leftArm.shoulder.rotation.z = lerpAngle(skater.leftArm.shoulder.rotation.z, pose.leftArm.shoulder.z, t);
    skater.leftArm.elbow.rotation.x = lerpAngle(skater.leftArm.elbow.rotation.x, pose.leftArm.elbow.x, t);
    // Right arm
    skater.rightArm.shoulder.rotation.x = lerpAngle(skater.rightArm.shoulder.rotation.x, pose.rightArm.shoulder.x, t);
    skater.rightArm.shoulder.rotation.z = lerpAngle(skater.rightArm.shoulder.rotation.z, pose.rightArm.shoulder.z, t);
    skater.rightArm.elbow.rotation.x = lerpAngle(skater.rightArm.elbow.rotation.x, pose.rightArm.elbow.x, t);
    // Left leg
    skater.leftLeg.hip.rotation.x = lerpAngle(skater.leftLeg.hip.rotation.x, pose.leftLeg.hip.x, t);
    skater.leftLeg.knee.rotation.x = lerpAngle(skater.leftLeg.knee.rotation.x, pose.leftLeg.knee.x, t);
    // Right leg
    skater.rightLeg.hip.rotation.x = lerpAngle(skater.rightLeg.hip.rotation.x, pose.rightLeg.hip.x, t);
    skater.rightLeg.knee.rotation.x = lerpAngle(skater.rightLeg.knee.rotation.x, pose.rightLeg.knee.x, t);
  }

  /* ── Ice Trail Particles ─────────────────────────────── */
  const trailCount = 200;
  const trailGeo = new THREE.BufferGeometry();
  const trailPositions = new Float32Array(trailCount * 3);
  const trailAlphas = new Float32Array(trailCount);
  const trailSizes = new Float32Array(trailCount);
  const showTrailParticles = false;
  let trailIndex = 0;

  for (let i = 0; i < trailCount; i++) {
    trailPositions[i * 3] = 0;
    trailPositions[i * 3 + 1] = -999;
    trailPositions[i * 3 + 2] = 0;
    trailAlphas[i] = 0;
    trailSizes[i] = 0.3;
  }

  trailGeo.setAttribute('position', new THREE.BufferAttribute(trailPositions, 3));
  trailGeo.setAttribute('alpha', new THREE.BufferAttribute(trailAlphas, 1));

  const trailMat = new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(0xaaddff) } },
    vertexShader: `
      attribute float alpha;
      varying float vAlpha;
      void main() {
        vAlpha = alpha;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = 3.0 * (20.0 / -mv.z);
        gl_Position = projectionMatrix * mv;
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      varying float vAlpha;
      void main() {
        float d = length(gl_PointCoord - vec2(0.5));
        if (d > 0.5) discard;
        float a = smoothstep(0.5, 0.0, d) * vAlpha;
        gl_FragColor = vec4(uColor, a * 0.6);
      }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  });

  const trailParticles = new THREE.Points(trailGeo, trailMat);
  if (showTrailParticles) scene.add(trailParticles);

  function emitTrail(x, y, z) {
    if (!showTrailParticles) return;
    const i = trailIndex % trailCount;
    trailPositions[i * 3] = x + (Math.random() - 0.5) * 0.5;
    trailPositions[i * 3 + 1] = y;
    trailPositions[i * 3 + 2] = z + (Math.random() - 0.5) * 0.5;
    trailAlphas[i] = 1.0;
    trailIndex++;
  }

  /* ── Create Skaters ──────────────────────────────────── */
  const skaterConfigs = [
    { color: 0x88ccff, scale: 0.9, speed: 0.3, pathX: 45, pathZ: 25, offset: 0, choreoType: 'featured' },
    { color: 0xff99bb, scale: 0.8, speed: 0.38, pathX: 30, pathZ: 15, offset: Math.PI, choreoType: 'spinner' },
    { color: 0xbb88ff, scale: 0.85, speed: 0.25, pathX: 20, pathZ: 10, offset: Math.PI / 2, choreoType: 'jumper' }
  ];

  const skaters = skaterConfigs.map(cfg => {
    const s = createRealisticSkater(cfg.color, cfg.scale);
    scene.add(s.root);
    return {
      ...s,
      speed: cfg.speed,
      pathX: cfg.pathX,
      pathZ: cfg.pathZ,
      offset: cfg.offset,
      choreoType: cfg.choreoType,
      currentPose: 'glide',
      poseTime: 0,
      jumping: false,
      jumpTime: 0,
      spinning: false,
      spinStartTime: 0,
      sequenceIndex: 0,
      lastPoseSwitch: 0,
      colorHex: cfg.color
    };
  });

  // Choreography sequences per type
  const choreoSequences = {
    featured: ['glide', 'insideEdge', 'outsideEdge', 'spiral', 'glide', 'camelSpin', 'threeTurn', 'glide'],
    spinner: ['glide', 'threeTurn', 'laybackSpin', 'outsideEdge', 'sitSpin', 'insideEdge', 'camelSpin', 'glide'],
    jumper: ['glide', 'insideEdge', 'threeTurn', 'outsideEdge', 'jumpTuck', 'glide', 'spiral']
  };

  const ICE_Y = -23.3;
  const JUMP_DURATION = 1.8;
  const JUMP_HEIGHT = 5.8;
  const spinPoses = ['laybackSpin', 'sitSpin', 'camelSpin'];
  const stepPoses = ['insideEdge', 'outsideEdge', 'threeTurn'];

  function smooth01(value) {
    return value * value * (3 - 2 * value);
  }

  function getPoseDuration(poseName) {
    if (poseName === 'jumpTuck') return JUMP_DURATION;
    if (poseName === 'landing') return 1.4;
    if (spinPoses.includes(poseName)) return 3.4;
    if (stepPoses.includes(poseName)) return 1.45;
    if (poseName === 'glide') return 2.0;
    return 3.0;
  }

  /* ── Stage Lighting ──────────────────────────────────── */
  // Ambient
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);

  // Main key light
  const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
  keyLight.position.set(20, 30, 20);
  scene.add(keyLight);

  // Colored spotlights following skaters
  const spotColors = [0xfff5e6, 0xffb3d9, 0xd4b3ff];
  const showSpotlightCones = false;
  const spotlights = spotColors.map((color, i) => {
    const spot = new THREE.SpotLight(color, 1.2, 80, Math.PI / 8, 0.5, 1);
    spot.position.set(0, 20, 0);
    scene.add(spot);
    scene.add(spot.target);

    // Volumetric cone (visual only)
    const coneGeo = new THREE.ConeGeometry(6, 20, 16, 1, true);
    const coneMat = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.03,
      side: THREE.DoubleSide,
      depthWrite: false
    });
    const cone = new THREE.Mesh(coneGeo, coneMat);
    cone.rotation.x = Math.PI;
    if (showSpotlightCones) scene.add(cone);

    return { light: spot, cone };
  });

  // Rim light for silhouette edges
  const rimLight = new THREE.PointLight(0x00d4ff, 0.6, 100);
  rimLight.position.set(-30, 15, -20);
  scene.add(rimLight);

  const backLight = new THREE.PointLight(0xa78bfa, 0.4, 80);
  backLight.position.set(30, 10, -30);
  scene.add(backLight);

  /* ── Animation Loop ──────────────────────────────────── */
  let animationId;
  let lastTime = performance.now() * 0.001;

  function animate() {
    animationId = requestAnimationFrame(animate);

    if (document.querySelector('.admin-layout')) return;

    const time = performance.now() * 0.001;
    const dt = Math.min(time - lastTime, 0.05);
    lastTime = time;

    // Smooth mouse
    mouse.x += (mouse.targetX - mouse.x) * 0.05;
    mouse.y += (mouse.targetY - mouse.y) * 0.05;

    /* ── Update Snowflakes ───────────────────────────── */
    const snowPos = snowGeometry.attributes.position.array;
    for (let i = 0; i < snowCount; i++) {
      snowPos[i * 3 + 1] -= snowSpeeds[i];
      snowPos[i * 3] += Math.sin(time + i) * 0.01;
      if (snowPos[i * 3 + 1] < -50) {
        snowPos[i * 3 + 1] = 50;
        snowPos[i * 3] = (Math.random() - 0.5) * 120;
      }
    }
    snowGeometry.attributes.position.needsUpdate = true;
    snowMaterial.uniforms.uTime.value = time;

    /* ── Rink parallax ───────────────────────────────── */
    rinkGroup.position.x = mouse.x * 2;
    rinkGroup.position.z = -40 + mouse.y * 2;

    /* ── Animate Skaters ─────────────────────────────── */
    skaters.forEach((s, idx) => {
      const sequence = choreoSequences[s.choreoType];
      const poseDuration = getPoseDuration(s.currentPose);
      const strideSpeed = time * s.speed * 6;

      // Advance choreography
      if (time - s.lastPoseSwitch > poseDuration) {
        s.sequenceIndex = (s.sequenceIndex + 1) % sequence.length;
        s.currentPose = sequence[s.sequenceIndex];
        s.lastPoseSwitch = time;
        s.poseTime = time;

        if (s.currentPose === 'jumpTuck') {
          s.jumping = true;
          s.jumpTime = time;
        }
        if (spinPoses.includes(s.currentPose)) {
          s.spinning = true;
          s.spinStartTime = time;
        }
      }

      // Path movement
      const t = time * s.speed + s.offset;
      const px = Math.sin(t) * s.pathX;
      const pz = Math.cos(t) * s.pathZ;
      const nextPx = Math.sin(t + 0.1) * s.pathX;
      const nextPz = Math.cos(t + 0.1) * s.pathZ;
      const travelYaw = Math.atan2(nextPx - px, nextPz - pz);

      s.root.position.x = px;
      s.root.position.z = -40 + pz;

      // Get current pose definition
      const pose = POSES[s.currentPose] || POSES.glide;
      const blendSpeed = 0.06;

      if (s.jumping) {
        const jTime = time - s.jumpTime;
        const jumpProgress = Math.min(Math.max(jTime / JUMP_DURATION, 0), 1);
        if (jTime > JUMP_DURATION) {
          s.jumping = false;
          s.currentPose = 'landing';
          s.lastPoseSwitch = time;
        }

        const jumpHeight = Math.sin(jumpProgress * Math.PI) * JUMP_HEIGHT;
        s.root.position.y = ICE_Y + Math.max(0, jumpHeight);
        s.root.rotation.y = travelYaw + smooth01(jumpProgress) * Math.PI * 2;
        s.root.rotation.z = Math.sin(jumpProgress * Math.PI) * 0.08;

        if (jTime < 0.3) {
          applyPose(s, POSES.glide, blendSpeed);
        } else if (jTime < 1.25) {
          applyPose(s, POSES.jumpTuck, blendSpeed * 2);
        } else {
          // Landing prep
          applyPose(s, POSES.landing, blendSpeed * 2);
        }

        if (jTime > 0.2 && jTime < 1.5 && showTrailParticles) {
          emitTrail(px, -24.5, -40 + pz);
        }
      } else if (s.spinning) {
        const spinTime = time - s.spinStartTime;
        if (spinTime > poseDuration) {
          s.spinning = false;
        }

        applyPose(s, pose, blendSpeed * 1.5);

        const spinPhase = Math.min(Math.max(spinTime / poseDuration, 0), 1);
        const spinTurns = 3 + idx * 0.5;
        s.root.rotation.y = travelYaw + smooth01(spinPhase) * Math.PI * 2 * spinTurns;
        s.root.rotation.z = (pose.bodyLean || 0) * 0.35;
        s.root.position.y = ICE_Y;

        if (Math.random() < 0.3 && showTrailParticles) {
          emitTrail(s.root.position.x, -24.5, s.root.position.z);
        }
      } else {
        s.root.position.y = ICE_Y;

        if (s.currentPose === 'glide') {
          // Skating stride animation
          const stride = Math.sin(strideSpeed);
          const strideTarget = {
            leftArm: {
              shoulder: { x: -stride * 0.5, z: Math.PI / 5 },
              elbow: { x: -0.15 }
            },
            rightArm: {
              shoulder: { x: stride * 0.5, z: -Math.PI / 5 },
              elbow: { x: -0.15 }
            },
            leftLeg: {
              hip: { x: stride * 0.45 },
              knee: { x: Math.max(0, stride * 0.4) }
            },
            rightLeg: {
              hip: { x: -stride * 0.45 },
              knee: { x: Math.max(0, -stride * 0.4) }
            },
            bodyLean: -Math.sin(t) * 0.12
          };
          applyPose(s, strideTarget, blendSpeed * 2);
        } else {
          // Apply choreography pose
          applyPose(s, pose, blendSpeed);
        }

        const poseElapsed = time - s.poseTime;
        const stepProgress = Math.min(Math.max(poseElapsed / poseDuration, 0), 1);
        let turnOffset = 0;
        if (s.currentPose === 'threeTurn') {
          turnOffset = smooth01(stepProgress) * Math.PI;
        } else if (s.currentPose === 'insideEdge') {
          turnOffset = Math.sin(stepProgress * Math.PI) * 0.45;
        } else if (s.currentPose === 'outsideEdge') {
          turnOffset = -Math.sin(stepProgress * Math.PI) * 0.45;
        }

        s.root.rotation.y = travelYaw + turnOffset;

        const edgeLean = stepPoses.includes(s.currentPose)
          ? (pose.bodyLean || 0) * Math.sin(stepProgress * Math.PI)
          : (pose.bodyLean || -Math.sin(t) * 0.12);
        s.root.rotation.z = edgeLean;

        if (Math.random() < 0.15 && showTrailParticles) {
          emitTrail(px, -24.8, -40 + pz);
        }
      }

      /* ── Skirt cloth simulation ────────────────────── */
      const skirtPos = s.skirt.geometry.attributes.position.array;
      const origPos = s.skirt.userData.originalPositions;
      const rotSpeed = s.spinning ? 0.3 : 0.05;
      for (let v = 0; v < skirtPos.length; v += 3) {
        const origY = origPos[v + 1];
        // Only affect bottom ring vertices (y is negative in cone)
        if (origY < -0.5) {
          const wave = Math.sin(time * 3 + origPos[v] * 2) * 0.15;
          const swing = Math.cos(time * s.speed * 4 + origPos[v + 2] * 3) * 0.2;
          const spinFlare = s.spinning ? Math.sin(time * 8 + origPos[v]) * 0.4 : 0;
          skirtPos[v] = origPos[v] + (wave + spinFlare) * (1 + Math.abs(origY));
          skirtPos[v + 2] = origPos[v + 2] + swing * (1 + Math.abs(origY));
        }
      }
      s.skirt.geometry.attributes.position.needsUpdate = true;

      /* ── Ponytail spring physics ───────────────────── */
      const rotY = s.root.rotation.y;
      const rotVelX = Math.sin(rotY) * (s.spinning ? 0.5 : 0.1);
      const rotVelZ = Math.cos(rotY) * (s.spinning ? 0.3 : 0.05);
      s.ponytailChain.forEach((seg, pi) => {
        const damping = 0.85;
        const spring = 0.08;
        const drag = pi * 0.15;
        seg.userData.velocityX += (rotVelX * drag - (seg.position.x - 0) * spring);
        seg.userData.velocityZ += (rotVelZ * drag - (seg.position.z - seg.userData.restZ) * spring);
        seg.userData.velocityX *= damping;
        seg.userData.velocityZ *= damping;
        seg.position.x += seg.userData.velocityX * dt * 10;
        seg.position.z = seg.userData.restZ + seg.userData.velocityZ * dt * 10;
        // Subtle bob
        seg.position.y = seg.userData.restY + Math.sin(time * 2 + pi * 0.5) * 0.03;
      });

      /* ── Sequin sparkle ────────────────────────────── */
      s.sequins.material.opacity = 0.4 + Math.sin(time * 4 + idx) * 0.3;

      /* ── Spotlight tracking ────────────────────────── */
      if (spotlights[idx]) {
        const spot = spotlights[idx];
        spot.light.target.position.set(s.root.position.x, -25, s.root.position.z);
        spot.light.position.set(s.root.position.x + 5, 15, s.root.position.z + 10);
        spot.cone.position.set(s.root.position.x + 5, 5, s.root.position.z + 10);
        spot.cone.lookAt(s.root.position);
      }
    });

    /* ── Fade ice trails ─────────────────────────────── */
    for (let i = 0; i < trailCount; i++) {
      if (trailAlphas[i] > 0) {
        trailAlphas[i] -= dt * 0.4;
        if (trailAlphas[i] < 0) trailAlphas[i] = 0;
      }
    }
    trailGeo.attributes.position.needsUpdate = true;
    trailGeo.attributes.alpha.needsUpdate = true;

    /* ── Aurora ───────────────────────────────────────── */
    auroraMaterial.uniforms.uTime.value = time;
    auroraMaterial.uniforms.uMouse.value.set(mouse.x, mouse.y);

    /* ── Camera ───────────────────────────────────────── */
    camera.position.x += (mouse.x * 3 - camera.position.x) * 0.02;
    camera.position.y += (-mouse.y * 2 - camera.position.y) * 0.02;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
  }

  animate();

  /* ── Resize ──────────────────────────────────────────── */
  function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }
  window.addEventListener('resize', onResize);

  /* ── Theme-Aware Adjustments ─────────────────────────── */
  function updateTheme() {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';

    snowMaterial.uniforms.uOpacity.value = isLight ? 0.35 : 0.6;
    snowMaterial.uniforms.uColor.value.setHex(isLight ? 0x60a5fa : 0x7eb8ff);

    rinkMaterial.opacity = isLight ? 0.4 : 0.25;
    rinkMaterial.color.setHex(isLight ? 0xdbeafe : 0x88bbff);
    rinkMaterial.metalness = isLight ? 0.5 : 0.9;
    rinkMaterial.roughness = isLight ? 0.15 : 0.05;

    boardMaterial.color.setHex(isLight ? 0x64748b : 0xffffff);
    boardMaterial.opacity = isLight ? 0.6 : 0.2;

    redLineMat.opacity = isLight ? 0.6 : 0.3;
    blueLineMat.opacity = isLight ? 0.6 : 0.3;
    circleMat.opacity = isLight ? 0.6 : 0.3;

    ambientLight.intensity = isLight ? 0.8 : 0.5;
    keyLight.intensity = isLight ? 1.0 : 0.8;

    skaters.forEach((s, idx) => {
      const lightColors = [0x3b82f6, 0xe11d48, 0x8b5cf6];
      const darkColors = [0x88ccff, 0xff99bb, 0xbb88ff];
      s.dressMat.color.setHex(isLight ? lightColors[idx] : darkColors[idx]);
      s.dressMat.opacity = isLight ? 0.85 : 0.92;
      s.skinMat.color.setHex(isLight ? 0xeab896 : 0xf5cdb6);
    });

    trailMat.uniforms.uColor.value.setHex(isLight ? 0x3b82f6 : 0xaaddff);
  }

  const observer = new MutationObserver(updateTheme);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  // Cleanup
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(animationId);
    } else {
      lastTime = performance.now() * 0.001;
      animate();
    }
  });
})();
