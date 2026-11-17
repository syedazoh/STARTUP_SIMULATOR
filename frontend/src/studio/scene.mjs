import { AGENTS, layoutLabels } from "./model.mjs";

// Framework-neutral WebGL scene: used by the React 18 and Next/React 19 clients.
// No network, model downloads, application state writes, or provider effects.
export function createStudio(
  THREE,
  canvas,
  {
    onSelect = (_id) => {},
    onProject = (_positions) => {},
    onTransfer = (_transfer) => {},
    reducedMotion = false,
  } = {},
) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: "low-power",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 80);
  const lookAt = new THREE.Vector3(0, 0.75, 0);
  scene.add(new THREE.HemisphereLight("#d7ccff", "#171020", 2.3));
  const light = (color, intensity, x, y, z) => {
    const l = new THREE.DirectionalLight(color, intensity);
    l.position.set(x, y, z);
    scene.add(l);
  };
  light("#fff0d8", 4, 2, 9, 7);
  light("#a67bff", 5, -6, 5, -4);
  light("#9e73e4", 2, 5, 3, -3);
  const standard = (color, metalness = 0.15, roughness = 0.48) =>
    new THREE.MeshStandardMaterial({ color, metalness, roughness });
  const glow = (color, opacity = 1) =>
    new THREE.MeshBasicMaterial({ color, transparent: opacity < 1, opacity });
  const dark = standard("#24202e", 0.65, 0.4),
    lightShell = standard("#d9d1e2", 0.3, 0.3),
    visor = standard("#14101f", 0.6, 0.18);
  const rounded = (w, h, d, r = 0.12) => {
    r = Math.min(r, w / 2, h / 2);
    const shape = new THREE.Shape();
    shape.moveTo(r, 0);
    shape.lineTo(w - r, 0);
    shape.quadraticCurveTo(w, 0, w, r);
    shape.lineTo(w, h - r);
    shape.quadraticCurveTo(w, h, w - r, h);
    shape.lineTo(r, h);
    shape.quadraticCurveTo(0, h, 0, h - r);
    shape.lineTo(0, r);
    shape.quadraticCurveTo(0, 0, r, 0);
    const g = new THREE.ExtrudeGeometry(shape, {
      depth: d,
      bevelEnabled: true,
      bevelSegments: 2,
      steps: 1,
      bevelSize: 0.025,
      bevelThickness: 0.025,
      curveSegments: 5,
    });
    g.translate(-w / 2, -h / 2, -d / 2);
    return g;
  };
  const mesh = (geo, material, parent = scene, pos = [0, 0, 0]) => {
    const m = new THREE.Mesh(geo, material);
    m.position.set(...pos);
    parent.add(m);
    return m;
  };
  const cylinder = (r, h, material, parent, pos) =>
    mesh(new THREE.CylinderGeometry(r, r, h, 40), material, parent, pos);
  const sphere = (r, material, parent, pos) =>
    mesh(new THREE.SphereGeometry(r, 20, 14), material, parent, pos);
  const floor = cylinder(
    6.4,
    0.18,
    standard("#17131f", 0.45, 0.7),
    scene,
    [0, -0.17, 0],
  );
  floor.scale.z = 0.83;
  const ring = mesh(
    new THREE.TorusGeometry(5.65, 0.012, 6, 100),
    glow("#7850b6", 0.7),
    scene,
    [0, -0.055, 0],
  );
  ring.rotation.x = -Math.PI / 2;
  ring.scale.y = 0.86;
  for (let i = 0; i < 64; i++) {
    const a = (i / 64) * Math.PI * 2;
    const dot = mesh(
      new THREE.BoxGeometry(0.035, 0.015, 0.1),
      glow(i % 4 === 0 ? "#ab82e8" : "#473457"),
      scene,
      [Math.cos(a) * 5.75, -0.048, Math.sin(a) * 4.96],
    );
    dot.rotation.y = -a;
  }
  // A central approval station is visually separate from the CEO's authority.
  cylinder(1.36, 0.22, standard("#292033", 0.7, 0.3), scene, [0, 0.04, 0]);
  cylinder(1.16, 0.04, standard("#393044", 0.5, 0.35), scene, [0, 0.17, 0]);
  const ownerRing = mesh(
    new THREE.TorusGeometry(1.13, 0.018, 8, 80),
    glow("#c4a5f3"),
    scene,
    [0, 0.21, 0],
  );
  ownerRing.rotation.x = -Math.PI / 2;
  const owner = new THREE.Group();
  scene.add(owner);
  owner.position.set(0, 0.45, 0);
  const core = mesh(
    new THREE.OctahedronGeometry(0.39, 1),
    standard("#b295d6", 0.65, 0.23),
    owner,
    [0, 0.35, 0],
  );
  const orbit = mesh(
    new THREE.TorusGeometry(0.65, 0.014, 8, 50),
    glow("#d9c6a4"),
    owner,
    [0, 0.35, 0],
  );
  orbit.rotation.x = 0.4;
  orbit.rotation.y = 0.3;
  const portals = new THREE.Group();
  scene.add(portals);
  for (let i = 0; i < 7; i++) {
    const radius = 6.8 + i * 0.42,
      z = -5 - i * 2.5;
    const points = [];
    for (let j = 0; j <= 5; j++) {
      const angle = (j / 5) * Math.PI * 2 + Math.PI / 2;
      points.push(
        new THREE.Vector3(
          Math.cos(angle) * radius,
          Math.sin(angle) * radius + 2.2,
          z,
        ),
      );
    }
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(points),
      new THREE.LineBasicMaterial({
        color: i % 3 === 0 ? "#b996dc" : "#63447c",
        transparent: true,
        opacity: 0.36 - i * 0.035,
      }),
    );
    portals.add(line);
  }
  const agents = new Map();
  for (const agent of AGENTS) {
    const group = new THREE.Group();
    group.position.set(...agent.position);
    scene.add(group);
    group.userData.agent = agent.id;
    cylinder(0.91, 0.15, standard("#292331", 0.6, 0.45), group, [0, 0.005, 0]);
    const halo = mesh(
      new THREE.TorusGeometry(0.83, 0.025, 8, 64),
      glow(agent.color, 0.7),
      group,
      [0, 0.1, 0],
    );
    halo.rotation.x = -Math.PI / 2;
    cylinder(0.7, 0.08, standard("#3c3147", 0.4, 0.6), group, [0, 0.12, 0]);
    const body = new THREE.Group();
    body.position.y = 0.2;
    group.add(body);
    body.rotation.y =
      Math.atan2(9 - agent.position[0], 12 - agent.position[2]) * 0.65;
    const accent = standard(agent.color, 0.4, 0.35);
    for (const side of [-1, 1]) {
      mesh(rounded(0.25, 0.25, 0.48, 0.08), dark, body, [
        side * 0.23,
        0.17,
        0.08,
      ]);
      cylinder(0.105, 0.44, lightShell, body, [side * 0.22, 0.46, 0]);
      sphere(0.12, dark, body, [side * 0.22, 0.64, 0]);
    }
    mesh(rounded(0.67, 0.65, 0.47, 0.16), accent, body, [0, 1.02, 0]);
    mesh(rounded(0.44, 0.32, 0.035, 0.06), dark, body, [0, 1.08, 0.26]);
    mesh(
      new THREE.BoxGeometry(0.21, 0.035, 0.025),
      glow(agent.color),
      body,
      [0, 1.14, 0.29],
    );
    mesh(
      new THREE.BoxGeometry(0.12, 0.025, 0.025),
      glow("#efe6d7"),
      body,
      [0, 1.04, 0.29],
    );
    cylinder(0.12, 0.12, dark, body, [0, 1.43, 0]);
    const head = new THREE.Group();
    head.position.y = 1.83;
    body.add(head);
    mesh(rounded(0.9, 0.64, 0.59, 0.18), lightShell, head);
    mesh(rounded(0.77, 0.4, 0.045, 0.13), visor, head, [0, 0, 0.32]);
    for (const side of [-1, 1]) {
      mesh(rounded(0.075, 0.15, 0.025, 0.035), glow(agent.color), head, [
        side * 0.16,
        0.025,
        0.36,
      ]);
      sphere(0.105, accent, head, [side * 0.5, 0, 0]);
    }
    mesh(
      new THREE.BoxGeometry(0.12, 0.024, 0.025),
      glow("#e8d7bd"),
      head,
      [0, -0.115, 0.36],
    );
    const antenna = cylinder(0.023, 0.19, dark, head, [0.29, 0.42, 0]);
    sphere(0.047, glow(agent.color), head, [0.29, 0.53, 0]);
    if (agent.id === "ceo") {
      mesh(
        rounded(0.18, 0.1, 0.035, 0.015),
        standard("#e1c28d", 0.75, 0.3),
        body,
        [0, 1.2, 0.28],
      );
      antenna.scale.y = 1.3;
    }
    const arms = [];
    for (const side of [-1, 1]) {
      const arm = new THREE.Group();
      arm.position.set(side * 0.43, 1.25, 0);
      body.add(arm);
      sphere(0.12, dark, arm, [0, 0, 0]);
      cylinder(0.105, 0.37, lightShell, arm, [side * 0.04, -0.22, 0]);
      sphere(0.11, accent, arm, [side * 0.04, -0.43, 0]);
      cylinder(0.085, 0.23, lightShell, arm, [side * 0.03, -0.56, 0.03]);
      sphere(0.115, lightShell, arm, [side * 0.02, -0.73, 0.06]);
      arm.rotation.z = side * 0.1;
      arms.push(arm);
    }
    // Physical work terminal, with a purple screen, sits beside every avatar.
    const desk = new THREE.Group();
    desk.position.set(0.65, 0.6, -0.28);
    desk.rotation.y = -0.3;
    group.add(desk);
    cylinder(0.045, 0.63, dark, desk, [0, -0.2, 0]);
    mesh(rounded(0.8, 0.06, 0.49, 0.06), dark, desk, [0, 0.12, 0]);
    const screen = mesh(
      rounded(0.65, 0.38, 0.045, 0.035),
      dark,
      desk,
      [0, 0.36, -0.12],
    );
    screen.rotation.x = -0.2;
    const panel = mesh(
      new THREE.PlaneGeometry(0.55, 0.27),
      glow("#624780"),
      desk,
      [0, 0.36, -0.088],
    );
    panel.rotation.x = -0.2;
    agents.set(agent.id, {
      group,
      body,
      head,
      halo,
      arms,
      phase: Math.random() * Math.PI * 2,
    });
  }
  let selected = "ceo",
    transfer = null,
    ended = false,
    animation = null,
    disposed = false,
    yaw = 0.12,
    follow = false,
    immersive = false,
    drag = null,
    didDrag = false;
  const cameraPoint = new THREE.Vector3(),
    ray = new THREE.Raycaster(),
    mouse = new THREE.Vector2();
  const projects = () => {
    const values = {};
    for (const a of AGENTS) {
      const v = new THREE.Vector3(a.position[0], 3.18, a.position[2]).project(
        camera,
      );
      values[a.id] = [
        (v.x * 0.5 + 0.5) * canvas.clientWidth,
        (-v.y * 0.5 + 0.5) * canvas.clientHeight,
      ];
    }
    const v = new THREE.Vector3(0, 1.9, 0).project(camera);
    values.owner = [
      (v.x * 0.5 + 0.5) * canvas.clientWidth,
      (-v.y * 0.5 + 0.5) * canvas.clientHeight,
    ];
    onProject(layoutLabels(values, canvas.clientWidth, canvas.clientHeight));
  };
  function resize() {
    if (disposed) return;
    const { width, height } = canvas.getBoundingClientRect();
    if (!width || !height) return;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    const distance = camera.aspect < 1 ? 21 : immersive ? 14.5 : 17;
    camera.position.set(
      Math.sin(0.65 + yaw) * distance,
      distance * 0.65,
      Math.cos(0.65 + yaw) * distance,
    );
    camera.lookAt(lookAt);
    camera.updateProjectionMatrix();
    render(performance.now());
  }
  const endpoints = (id) =>
    id === "owner"
      ? new THREE.Vector3(0, 1.1, 0)
      : new THREE.Vector3(...AGENTS.find((a) => a.id === id).position).add(
          new THREE.Vector3(0, 1.4, 0),
        );
  const clearTransfer = () => {
    if (!transfer) return;
    scene.remove(transfer.group);
    transfer.group.traverse((o) => {
      o.geometry?.dispose();
      if (o.material) o.material.dispose();
    });
    transfer = null;
  };
  const playTransfer = (value) => {
    clearTransfer();
    if (!value) {
      render(performance.now());
      return;
    }
    const start = endpoints(value.sender),
      end = endpoints(value.receiver);
    const curve = new THREE.QuadraticBezierCurve3(
      start,
      new THREE.Vector3((start.x + end.x) / 2, 4.3, (start.z + end.z) / 2),
      end,
    );
    const group = new THREE.Group();
    scene.add(group);
    mesh(
      new THREE.TubeGeometry(curve, 48, 0.045, 8, false),
      glow("#b48aff", 0.8),
      group,
    );
    // A bright core and fixed arrowheads make direction legible before/after delivery.
    mesh(
      new THREE.TubeGeometry(curve, 48, 0.012, 6, false),
      glow("#f0dfff"),
      group,
    );
    for (const at of [0.25, 0.5, 0.76]) {
      const arrow = mesh(
        new THREE.ConeGeometry(0.12, 0.32, 8),
        glow("#ead1ff"),
        group,
        curve.getPoint(at).toArray(),
      );
      arrow.quaternion.setFromUnitVectors(
        new THREE.Vector3(0, 1, 0),
        curve.getTangent(at).normalize(),
      );
    }
    const packet = new THREE.Group();
    group.add(packet);
    mesh(
      rounded(0.72, 0.49, 0.08, 0.06),
      standard("#e5d9f6", 0.3, 0.25),
      packet,
    );
    mesh(
      new THREE.BoxGeometry(0.44, 0.045, 0.015),
      glow("#6a32b5"),
      packet,
      [-0.02, 0.055, 0.06],
    );
    mesh(
      new THREE.BoxGeometry(0.32, 0.04, 0.015),
      glow("#6a32b5"),
      packet,
      [-0.055, -0.025, 0.06],
    );
    packet.quaternion.copy(camera.quaternion);
    const arrival = mesh(
      new THREE.TorusGeometry(0.47, 0.025, 8, 40),
      glow("#dbc5fd"),
      group,
      end.toArray(),
    );
    arrival.rotation.x = -Math.PI / 2;
    arrival.visible = false;
    transfer = {
      ...value,
      group,
      packet,
      curve,
      arrival,
      started: performance.now(),
    };
    ended = false;
    onTransfer({ ...value, stage: "sending" });
    if (reducedMotion) {
      packet.position.copy(end);
      arrival.visible = true;
      onTransfer({ ...value, stage: "arrived" });
      render(performance.now());
    }
  };
  function render(now) {
    const t = now / 1000;
    for (const [id, a] of agents) {
      const elapsed = transfer ? now - transfer.started : Infinity;
      const sending = transfer?.sender === id && elapsed < 2100,
        receiving =
          transfer?.receiver === id &&
          (reducedMotion || (elapsed > 1500 && elapsed < 3900));
      const focus = selected === id || sending || receiving;
      a.halo.material.opacity = focus ? 1 : 0.38;
      if (!reducedMotion) {
        a.body.position.y = 0.2 + Math.sin(t * 1.2 + a.phase) * 0.025;
        a.head.rotation.z = Math.sin(t * 0.7 + a.phase) * 0.035;
        a.arms[1].rotation.x = sending
          ? -0.95
          : receiving
            ? -0.55
            : Math.sin(t + a.phase) * 0.035;
        a.arms[0].rotation.z = -0.1 + (receiving ? -0.25 : 0);
      }
    }
    if (!reducedMotion) core.rotation.y = t * 0.22;
    if (transfer && !reducedMotion) {
      const p = Math.min((now - transfer.started) / 2100, 1);
      const eased = 1 - Math.pow(1 - p, 2);
      transfer.packet.position.copy(transfer.curve.getPoint(eased));
      transfer.packet.quaternion.copy(camera.quaternion);
      transfer.packet.rotateZ(Math.sin(p * Math.PI) * 0.16);
      transfer.arrival.visible = p > 0.87;
      transfer.arrival.scale.setScalar(0.6 + (p > 0.87 ? (p - 0.87) * 4 : 0));
      if (p >= 1 && !ended) {
        ended = true;
        onTransfer({
          ...transfer,
          group: undefined,
          packet: undefined,
          curve: undefined,
          arrival: undefined,
          stage: "arrived",
        });
      }
      // Retain the last recorded route until the next handoff or explicit clear.
    }
    if (follow && !reducedMotion) {
      const target = transfer
        ? transfer.curve.getPoint(0.5)
        : new THREE.Vector3(0, 1, 0);
      cameraPoint.set(target.x + 10, 8.5, target.z + 10);
      camera.position.lerp(cameraPoint, 0.025);
      camera.lookAt(target);
    }
    renderer.render(scene, camera);
    projects();
  }
  function loop(now) {
    if (disposed) return;
    if (!document.hidden) render(now);
    animation = requestAnimationFrame(loop);
  }
  const down = (e) => {
    drag = [e.clientX, e.clientY];
    didDrag = false;
    canvas.setPointerCapture?.(e.pointerId);
  };
  const move = (e) => {
    if (!drag) return;
    const dx = e.clientX - drag[0];
    if (Math.abs(dx) > 3) didDrag = true;
    yaw = Math.max(-0.6, Math.min(0.65, yaw + dx * 0.004));
    drag = [e.clientX, e.clientY];
    resize();
  };
  const up = (e) => {
    if (!didDrag) {
      const box = canvas.getBoundingClientRect();
      mouse.set(
        ((e.clientX - box.left) / box.width) * 2 - 1,
        -((e.clientY - box.top) / box.height) * 2 + 1,
      );
      ray.setFromCamera(mouse, camera);
      const hits = ray.intersectObjects(scene.children, true);
      for (const hit of hits) {
        let node = hit.object;
        while (node) {
          if (node.userData.agent) {
            onSelect(node.userData.agent);
            drag = null;
            return;
          }
          node = node.parent;
        }
      }
    }
    drag = null;
  };
  const cancel = () => {
    drag = null;
  };
  canvas.addEventListener("pointerdown", down);
  canvas.addEventListener("pointermove", move);
  canvas.addEventListener("pointerup", up);
  canvas.addEventListener("pointercancel", cancel);
  const observer = new ResizeObserver(resize);
  observer.observe(canvas);
  resize();
  if (!reducedMotion) animation = requestAnimationFrame(loop);
  return {
    select(id) {
      selected = id;
      render(performance.now());
    },
    playTransfer,
    setImmersive(value) {
      immersive = value;
      resize();
    },
    follow(value) {
      follow = value;
      if (!value) resize();
    },
    resetCamera() {
      yaw = 0.12;
      resize();
    },
    dispose() {
      disposed = true;
      cancelAnimationFrame(animation);
      observer.disconnect();
      canvas.removeEventListener("pointerdown", down);
      canvas.removeEventListener("pointermove", move);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("pointercancel", cancel);
      scene.traverse((o) => {
        o.geometry?.dispose();
        if (o.material) {
          const list = Array.isArray(o.material) ? o.material : [o.material];
          list.forEach((m) => m.dispose());
        }
      });
      renderer.dispose();
      // React StrictMode may immediately reuse this canvas. dispose GPU resources
      // without explicitly losing its context; the browser releases it on removal.
    },
  };
}
