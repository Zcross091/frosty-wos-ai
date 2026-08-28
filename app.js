/**
 * Frosty AI — Interactive 3D Canvas, Simulator, & Codex Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  init3DBackground();
  initCommandSimulator();
  initHeroCodex();
  initFormationCalculator();
  initCopyButtons();
  initReleaseUpdatePopup();
});

/* ==========================================================================
   1. Three.js 3D Cyber-Frost Particle & Crystal Vortex
   ========================================================================== */
function init3DBackground() {
  const canvas = document.getElementById('bg3d');
  if (!canvas) return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 30;

  const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // --- 1. Floating Frost Shards / Polyhedra ---
  const crystalGroup = new THREE.Group();
  const crystalMaterials = [
    new THREE.MeshBasicMaterial({ color: 0x00f0ff, wireframe: true, transparent: true, opacity: 0.35 }),
    new THREE.MeshBasicMaterial({ color: 0x0099ff, wireframe: true, transparent: true, opacity: 0.25 }),
    new THREE.MeshBasicMaterial({ color: 0x8a2be2, wireframe: true, transparent: true, opacity: 0.3 })
  ];

  const geometries = [
    new THREE.IcosahedronGeometry(2.2, 0),
    new THREE.OctahedronGeometry(1.8, 0),
    new THREE.TetrahedronGeometry(2.0, 0),
    new THREE.DodecahedronGeometry(1.6, 0)
  ];

  const crystals = [];
  for (let i = 0; i < 18; i++) {
    const geo = geometries[i % geometries.length];
    const mat = crystalMaterials[i % crystalMaterials.length];
    const mesh = new THREE.Mesh(geo, mat);

    mesh.position.x = (Math.random() - 0.5) * 55;
    mesh.position.y = (Math.random() - 0.5) * 45;
    mesh.position.z = (Math.random() - 0.5) * 25;

    mesh.rotation.x = Math.random() * Math.PI;
    mesh.rotation.y = Math.random() * Math.PI;

    mesh.userData = {
      rotSpeedX: (Math.random() - 0.5) * 0.015,
      rotSpeedY: (Math.random() - 0.5) * 0.015,
      floatSpeed: 0.005 + Math.random() * 0.01,
      initY: mesh.position.y
    };

    crystals.push(mesh);
    crystalGroup.add(mesh);
  }
  scene.add(crystalGroup);

  // --- 2. Snow / Ice Particle Vortex ---
  const particleCount = 750;
  const particleGeo = new THREE.BufferGeometry();
  const particlePositions = new Float32Array(particleCount * 3);
  const particleScales = new Float32Array(particleCount);

  for (let i = 0; i < particleCount * 3; i += 3) {
    particlePositions[i] = (Math.random() - 0.5) * 70;
    particlePositions[i + 1] = (Math.random() - 0.5) * 60;
    particlePositions[i + 2] = (Math.random() - 0.5) * 40;
    particleScales[i / 3] = Math.random() * 1.5;
  }

  particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
  const particleMat = new THREE.PointsMaterial({
    color: 0x00f0ff,
    size: 0.35,
    transparent: true,
    opacity: 0.65,
    blending: THREE.AdditiveBlending
  });

  const particleSystem = new THREE.Points(particleGeo, particleMat);
  scene.add(particleSystem);

  // --- 3. Interactive Mouse Parallax ---
  let mouseX = 0;
  let mouseY = 0;
  let targetX = 0;
  let targetY = 0;

  window.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX - window.innerWidth / 2) * 0.02;
    mouseY = (e.clientY - window.innerHeight / 2) * 0.02;
  });

  // --- 4. Animation Loop ---
  let clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);
    const elapsedTime = clock.getElapsedTime();

    // Smooth camera mouse follow
    targetX += (mouseX - targetX) * 0.05;
    targetY += (mouseY - targetY) * 0.05;
    camera.position.x = targetX;
    camera.position.y = -targetY;
    camera.lookAt(scene.position);

    // Rotate crystals
    crystals.forEach((c) => {
      c.rotation.x += c.userData.rotSpeedX;
      c.rotation.y += c.userData.rotSpeedY;
      c.position.y = c.userData.initY + Math.sin(elapsedTime * c.userData.floatSpeed * 10) * 1.5;
    });

    // Particle subtle rotation
    particleSystem.rotation.y = elapsedTime * 0.03;
    particleSystem.rotation.x = elapsedTime * 0.015;

    renderer.render(scene, camera);
  }
  animate();

  // --- 5. Resize Handler ---
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  });
}

/* ==========================================================================
   2. Interactive Discord Command Simulator Engine
   ========================================================================== */
const SIMULATOR_DATA = {
  wos_bear: {
    user: "!wos considering there are new generation of heroes now upto gen 16, write me a good lineup to use to join rallies in bear trap",
    title: "❄️ Frosty Tactical Advisory • Bear Trap Joiner Strategy",
    body: `
      <p>Even with <strong>Generation 16 legends (Seigel, Ursar, Aisling)</strong> active, joining a Bear Trap rally is governed by Whiteout Survival's fundamental joiner mechanics:</p>
      
      <h4>🐻 1. The Core Rally Joiner Rule</h4>
      <ul>
        <li>In Whiteout Survival, when you <strong>join</strong> an alliance rally, your personal hero stats do <em>not</em> buff the overall rally march.</li>
        <li><strong>Only the TOP 4 rally joiners' first expedition skill (Top-Right Skill)</strong> buffs the entire alliance rally damage!</li>
      </ul>

      <h4>⚔️ 2. Optimal 3-Hero Joiner March</h4>
      <ul>
        <li><strong>Position 1 (Leader):</strong> <code>Jessie</code> — <em>Must be 1st hero!</em> Grants <strong>+25% Damage Dealt</strong> to the entire rally.</li>
        <li><strong>Position 2 (Deputy 1):</strong> <code>Seo-yoon</code> (+20% Attack buff) or <code>Jeronimo</code> (+15% Attack/Damage).</li>
        <li><strong>Position 3 (Deputy 2):</strong> Your highest stat Marksman (e.g. <code>Aisling (Gen 16)</code> / <code>Bradley (Gen 7)</code> / <code>Alonso (Gen 2)</code>) for auxiliary troop stats.</li>
      </ul>

      <h4>🎯 3. Optimal Troop Ratio</h4>
      <ul>
        <li>Use <code>10% Infantry / 10% Lancer / 80% Marksman</code> (or pure <code>0/20/80</code>). Bear Trap never kills your troops, so maximize backline Marksman DPS!</li>
      </ul>

      <p>💡 <strong>Grandmaster Tip:</strong> <em>Save your strongest Gen 16 damage squad (Seigel + Aisling + Ursar) to lead your own personal rally march where their massive 2131% stats apply directly!</em></p>
    `,
    footer: "Engine: Gemini (gemini-3.6-flash) • Latency: 0.58s • Chief: Alliance Chief"
  },
  hero_flint: {
    user: "/hero name: Flint",
    title: "🛡️ Hero Dossier: 🔥 Flint — Generation 2 (Mythic Infantry)",
    body: `
      <h4>Role & Tactical Classification</h4>
      <ul>
        <li><strong>Type:</strong> Mythic Infantry / Combat — Premier Frontline Burn Tank & Dragonbane Specialist.</li>
        <li><strong>Unlock Window:</strong> ~Day 40+ (Featured on Gen 2 Lucky Wheel & Hall of Heroes).</li>
      </ul>

      <h4>📈 Key Stats & Multipliers</h4>
      <ul>
        <li><strong>Exploration:</strong> Attack 2,043 · Defense 2,664 · Health 39,960</li>
        <li><strong>Expedition Buffs:</strong> Infantry Attack <code>+240.19%</code> · Infantry Defense <code>+240.19%</code></li>
      </ul>

      <h4>⚙️ Exclusive Gear: Dragonbane</h4>
      <ul>
        <li><strong>Vengeful Task:</strong> After triggering <em>Incinerator</em> (40% HP heal), gains <strong>+24% Attack</strong> until battle ends.</li>
        <li><strong>Dragonbreath:</strong> Garrison defending troops gain <strong>+15% Attack</strong>.</li>
      </ul>

      <p>💰 <strong>F2P vs P2W Verdict:</strong> <em>The absolute highest priority Lucky Wheel investment for F2P in Gen 2. Reach 3–4★ to unlock his core tanking resilience. Pair with Alonso & Philly.</em></p>
    `,
    footer: "Engine: Gemini (gemini-3.6-flash) • Latency: 0.44s • Hero: Flint"
  },
  gen_16: {
    user: "!wos write about generation 16",
    title: "👑 Frosty Generation Master Guide: Generation 16 (Legendary)",
    body: `
      <p>Generation 16 unlocks when your State reaches approximately <strong>1,160+ days server age</strong> (~80 days after Gen 15). Features unprecedented stat scaling of <strong>+2,131.70%</strong> Expedition buffs.</p>

      <h4>🛡️ 1. Seigel (Legendary Infantry)</h4>
      <ul>
        <li><strong>Role:</strong> Ultra-tanky frontline reflect shield & Night's Guard veteran.</li>
        <li><strong>Skill (Spike Guard):</strong> Extends spike armor for 5s — Defense +25% and reflects 25% incoming damage back to attackers.</li>
        <li><strong>Exclusive Gear:</strong> <em>Blacklight Halberd</em> (Heals 25% of reflected damage as Health).</li>
      </ul>

      <h4>🏹 2. Aisling (Legendary Marksman)</h4>
      <ul>
        <li><strong>Role:</strong> High-velocity siege sniper & endgame backline burst DPS.</li>
        <li><strong>Strengths:</strong> Highest Marksman lethal multiplier in Whiteout Survival history.</li>
      </ul>

      <h4>🐎 3. Ursar (Legendary Lancer)</h4>
      <ul>
        <li><strong>Role:</strong> Windbreaker Support DPS & debuff applicator (Hall of Heroes exclusive).</li>
      </ul>
    `,
    footer: "Engine: Gemini (gemini-3.6-flash) • Latency: 0.65s • Generation: Gen 16"
  },
  lineup_pvp: {
    user: "/lineup mode: PvP Field Battle generation: Gen 7",
    title: "⚔️ Tactical Formation & Lineup Advisory (PvP Gen 7)",
    body: `
      <h4>🛡️ Recommended 3-Hero March</h4>
      <ul>
        <li><strong>Leader (Captain):</strong> <code>Bradley</code> (Gen 7 Infantry) — Frontline stun & defense shield.</li>
        <li><strong>Deputy 1:</strong> <code>Edith</code> (Gen 7 Marksman) — Armor-piercing DPS & critical lethality.</li>
        <li><strong>Deputy 2:</strong> <code>Gordon</code> (Gen 7 Lancer) or <code>Hector</code> (Gen 4 Lancer).</li>
      </ul>

      <h4>📊 Troop Distribution Ratio: 50 / 20 / 30</h4>
      <ul>
        <li>🛡️ <strong>50% Infantry:</strong> Essential shield wall. Protects your backline from enemy lancer piercing.</li>
        <li>🐎 <strong>20% Lancers:</strong> Targets enemy marksmen in mid-range skirmishes.</li>
        <li>🏹 <strong>30% Marksmen:</strong> Delivers sustained lethal DPS safely behind Bradley's shield.</li>
      </ul>

      <p>💡 <strong>Grandmaster Tip:</strong> <em>Never drop below 45% Infantry in PvP field battles, or enemy marches will break your line and wipe your marksmen in round 2!</em></p>
    `,
    footer: "Engine: Gemini (gemini-3.6-flash) • Latency: 0.51s • Mode: PvP"
  },
  event_joe: {
    user: "!event Crazy Joe",
    title: "🎯 Frosty Event Master Guide: Crazy Joe Defense",
    body: `
      <h4>Overview & Structure</h4>
      <ul>
        <li>20 assault waves over ~40 minutes. Waves <strong>10 & 20</strong> are massive coordinated strikes on the <strong>Alliance Headquarters (HQ)</strong>!</li>
      </ul>

      <h4>🚨 Critical Troop Reinforcement Rules</h4>
      <ul>
        <li>❌ <strong>NEVER send Marksmen to allies or Alliance HQ!</strong> Keep marksmen on your own wall barricade.</li>
        <li>✅ <strong>Send ONLY Infantry & Lancers</strong> to reinforce teammates and HQ.</li>
      </ul>

      <h4>🏆 High Scoring "Empty City" Technique</h4>
      <ul>
        <li>Send 100% of your marching troops out to reinforce online alliance members. When Joe attacks your empty city, you still earn full defense points while allies defend you!</li>
      </ul>

      <p>💡 <strong>Chief's Checklist:</strong> <em>Recall 1 march 5 minutes before Wave 10 and Wave 20 to heavily reinforce the Alliance HQ with T10/T11 Infantry!</em></p>
    `,
    footer: "Engine: Gemini (gemini-3.6-flash) • Latency: 0.49s • Event: Crazy Joe"
  }
};

function initCommandSimulator() {
  const simButtons = document.querySelectorAll('.sim-btn');
  const userText = document.getElementById('sim-user-text');
  const embedTitle = document.getElementById('sim-embed-title');
  const embedBody = document.getElementById('sim-embed-body');
  const embedFooter = document.getElementById('sim-embed-footer');

  function renderScenario(key) {
    const data = SIMULATOR_DATA[key];
    if (!data) return;

    // Fade animation
    embedBody.style.opacity = '0';
    setTimeout(() => {
      userText.textContent = data.user;
      embedTitle.textContent = data.title;
      embedBody.innerHTML = data.body;
      embedFooter.textContent = data.footer;
      embedBody.style.opacity = '1';
    }, 150);
  }

  simButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      simButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const cmdKey = btn.getAttribute('data-cmd');
      renderScenario(cmdKey);
    });
  });

  // Initial render
  renderScenario('wos_bear');

  // Interactive buttons in Discord view
  const regenBtn = document.getElementById('sim-regenerate-btn');
  if (regenBtn) {
    regenBtn.addEventListener('click', () => {
      embedBody.style.opacity = '0.4';
      setTimeout(() => {
        embedBody.style.opacity = '1';
        embedFooter.textContent = `Engine: Gemini (gemini-3.6-flash) • Latency: 0.47s • Regenerated by Chief`;
      }, 300);
    });
  }

  const lineupBtn = document.getElementById('sim-lineup-btn');
  if (lineupBtn) {
    lineupBtn.addEventListener('click', () => {
      const pvpBtn = document.getElementById('sim-btn-pvp');
      if (pvpBtn) pvpBtn.click();
    });
  }

  const dismissBtn = document.getElementById('sim-dismiss-btn');
  if (dismissBtn) {
    dismissBtn.addEventListener('click', () => {
      const container = document.getElementById('sim-embed-container');
      if (container) {
        container.style.display = container.style.display === 'none' ? 'flex' : 'none';
      }
    });
  }
}

/* ==========================================================================
   3. Interactive Hero & Generation Codex
   ========================================================================== */
const CODEX_DATA = {
  16: [
    { name: "Seigel", type: "infantry", title: "Gen 16 (Legendary)", statAtk: 92, statDef: 99, statHp: 98, skill: "Spike Guard: 25% Damage Reflect + Debuff Immunity window.", role: "God-tier Frontline Tank & Garrison Lead" },
    { name: "Aisling", type: "marksman", title: "Gen 16 (Legendary)", statAtk: 99, statDef: 85, statHp: 88, skill: "Moonpiercer: +60% Armor Penetration & Massive Siege Crit.", role: "Primary Endgame Burst Damage Dealer" },
    { name: "Ursar", type: "lancer", title: "Gen 16 (Legendary)", statAtk: 94, statDef: 92, statHp: 91, skill: "Toxic Gale: +35% Enemy Attack reduction & Bleed dots.", role: "Hall of Heroes Support & Marksman Counter" }
  ],
  7: [
    { name: "Edith", type: "infantry", title: "Gen 7 (Mythic)", statAtk: 84, statDef: 95, statHp: 94, skill: "Strategic Balance: Shields Marksmen & boosts Lancers.", role: "Frontline Mech Tank with Mr. Tin" },
    { name: "Bradley", type: "marksman", title: "Gen 7 (Mythic)", statAtk: 92, statDef: 78, statHp: 80, skill: "Piercing Shell: Armor penetration & heavy siege sniper.", role: "Core PvP Damage Carry" }
  ],
  4: [
    { name: "Lynn", type: "marksman", title: "Gen 4 (Mythic)", statAtk: 85, statDef: 74, statHp: 76, skill: "Heavy Shot: Stun chances & high attack speed.", role: "F2P Wheel Marksman Star" },
    { name: "Hector", type: "infantry", title: "Gen 4 (Mythic)", statAtk: 78, statDef: 86, statHp: 87, skill: "Indomitable: Defense escalation over long rallies.", role: "Heavy Castle Garrison Wall" }
  ],
  2: [
    { name: "Flint", type: "infantry", title: "Gen 2 (Mythic)", statAtk: 72, statDef: 84, statHp: 85, skill: "Dragonbane Flame: AOE burn & 40% self-heal on trigger.", role: "Must-Have F2P Lucky Wheel Tank" },
    { name: "Alonso", type: "marksman", title: "Gen 2 (Mythic)", statAtk: 82, statDef: 70, statHp: 73, skill: "Trapnet: 1.5s teamwide stun & damage amplification.", role: "Exploration & Arena Burst King" },
    { name: "Philly", type: "lancer", title: "Gen 2 (Mythic)", statAtk: 74, statDef: 75, statHp: 80, skill: "First Aid: Heals entire march HP over long SvS battles.", role: "Sustained Rally Healer" }
  ],
  1: [
    { name: "Jeronimo", type: "infantry", title: "Gen 1 (Mythic)", statAtk: 76, statDef: 78, statHp: 79, skill: "Warlord's Might: +15% rally damage joiner buff.", role: "VIP Rally Lead & Universal Joiner" },
    { name: "Molly", type: "marksman", title: "Gen 1 (Mythic)", statAtk: 78, statDef: 65, statHp: 68, skill: "Snowball barrage: Stun & AOE arena clearing.", role: "Day 1 Free F2P Damage Queen" }
  ],
  0: [
    { name: "Jessie", type: "lancer", title: "Epic Core (F2P)", statAtk: 65, statDef: 66, statHp: 70, skill: "Rally Buff: TOP-1 JOINER MUST-HAVE (+25% Damage Dealt).", role: "Essential Joiner for Every Bear Trap & SvS" },
    { name: "Sergey", type: "infantry", title: "Epic Core (F2P)", statAtk: 60, statDef: 75, statHp: 76, skill: "Iron Resolve: -20% incoming damage taken.", role: "Best Early Game F2P Defense Tank" },
    { name: "Seo-yoon", type: "lancer", title: "Epic Core (F2P)", statAtk: 66, statDef: 64, statHp: 68, skill: "War Hymn: +20% Attack buff to entire rally.", role: "Essential Top-4 Rally Joiner" }
  ]
};

function initHeroCodex() {
  const tabs = document.querySelectorAll('.gen-tab');
  const cardsContainer = document.getElementById('hero-cards-container');

  function renderGenHeroes(genKey) {
    const heroes = CODEX_DATA[genKey] || [];
    cardsContainer.innerHTML = '';

    heroes.forEach((h) => {
      const card = document.createElement('div');
      card.className = 'hero-card glass-card';

      const typeClass = `type-${h.type}`;
      const typeIcon = h.type === 'infantry' ? '🛡️' : h.type === 'lancer' ? '🐎' : '🏹';

      card.innerHTML = `
        <div class="hero-card-header">
          <div class="hero-card-title">
            <span>${typeIcon}</span>
            <span>${h.name}</span>
          </div>
          <span class="hero-type-badge ${typeClass}">${h.type}</span>
        </div>
        <p style="color: var(--text-muted); font-size: 0.85rem; font-weight: 600;">${h.title} • ${h.role}</p>

        <div class="hero-stats-list">
          <div class="stat-bar-row">
            <span>Attack</span>
            <div class="stat-bar-track"><div class="stat-bar-val" style="width: ${h.statAtk}%"></div></div>
          </div>
          <div class="stat-bar-row">
            <span>Defense</span>
            <div class="stat-bar-track"><div class="stat-bar-val" style="width: ${h.statDef}%"></div></div>
          </div>
          <div class="stat-bar-row">
            <span>Health</span>
            <div class="stat-bar-track"><div class="stat-bar-val" style="width: ${h.statHp}%"></div></div>
          </div>
        </div>

        <div class="hero-skill-chip">
          <strong>⚡ Signature Skill:</strong> ${h.skill}
        </div>
      `;

      cardsContainer.appendChild(card);
    });
  }

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      const gen = tab.getAttribute('data-gen');
      renderGenHeroes(gen);
    });
  });

  // Initial render
  renderGenHeroes('16');
}

/* ==========================================================================
   4. Interactive Troop Ratio Calculator
   ========================================================================== */
const FORMATION_PRESETS = {
  pvp: {
    title: "Standard PvP Field Battle Formation",
    badge: "50 / 20 / 30",
    inf: 50,
    lan: 20,
    mar: 30,
    notes: "Infantry absorbs 100% of enemy front damage. If infantry falls below 40%, your marksmen will be wiped out in seconds. 50/20/30 gives your marksmen the protection needed to deal maximum sustained damage over extended fights."
  },
  bear: {
    title: "Bear Trap Maximum PvE Damage Composition",
    badge: "10 / 10 / 80",
    inf: 10,
    lan: 10,
    mar: 80,
    notes: "The Bear Trap monster never kills or injures your troops! Therefore, defensive shields and heavy infantry are unnecessary. Pack 80% Marksmen to maximize total raw damage points."
  },
  defense: {
    title: "Castle & Stronghold Heavy Garrison Defense",
    badge: "60 / 20 / 20",
    inf: 60,
    lan: 20,
    mar: 20,
    notes: "When defending against multiple incoming enemy rallies during Sunfire Castle or SvS, your wall absorbs immense burst damage. 60% Infantry with Sergey or Bradley ensures your garrison never gets breached."
  },
  burst: {
    title: "High Burst 4-1-1 Attack Formation",
    badge: "40 / 10 / 50",
    inf: 40,
    lan: 10,
    mar: 50,
    notes: "An aggressive offensive lineup designed for quick wipeouts against weaker enemy cities and foundry nodes. Gives huge marksman burst while maintaining the 40% minimum infantry threshold."
  }
};

function initFormationCalculator() {
  const presetButtons = document.querySelectorAll('.preset-btn');
  const titleEl = document.getElementById('calc-scenario-title');
  const badgeEl = document.getElementById('calc-ratio-badge');
  const valInf = document.getElementById('val-inf');
  const valLan = document.getElementById('val-lan');
  const valMar = document.getElementById('val-mar');
  const barInf = document.getElementById('bar-inf');
  const barLan = document.getElementById('bar-lan');
  const barMar = document.getElementById('bar-mar');
  const notesEl = document.getElementById('calc-notes');

  function renderPreset(key) {
    const p = FORMATION_PRESETS[key];
    if (!p) return;

    titleEl.textContent = p.title;
    badgeEl.textContent = p.badge;

    valInf.textContent = `${p.inf}%`;
    valLan.textContent = `${p.lan}%`;
    valMar.textContent = `${p.mar}%`;

    barInf.style.width = `${p.inf}%`;
    barLan.style.width = `${p.lan}%`;
    barMar.style.width = `${p.mar}%`;

    notesEl.innerHTML = `<h4>💡 Grandmaster Tactical Doctrine</h4><p>${p.notes}</p>`;
  }

  presetButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      presetButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const presetKey = btn.getAttribute('data-preset');
      renderPreset(presetKey);
    });
  });

  // Initial render
  renderPreset('pvp');
}

/* ==========================================================================
   5. Copy Code Buttons
   ========================================================================== */
function initCopyButtons() {
  const copyBtn = document.getElementById('copy-deploy-btn');
  if (!copyBtn) return;

  copyBtn.addEventListener('click', () => {
    const codeText = `git clone https://github.com/Zcross091/frosty-wos-ai.git\ncd frosty-wos-ai\npip install -r requirements.txt\ncp .env.example .env\npython3 ingest.py --local-only --clean\npm2 start ecosystem.config.js\npm2 save`;

    navigator.clipboard.writeText(codeText).then(() => {
      const originalHtml = copyBtn.innerHTML;
      copyBtn.innerHTML = `<span>✅</span> <span>Copied!</span>`;
      setTimeout(() => {
        copyBtn.innerHTML = originalHtml;
      }, 2000);
    });
  });
}

/* ==========================================================================
   6. GitHub Release In-Browser Update Pop-Up
   ========================================================================== */
function initReleaseUpdatePopup() {
  const GITHUB_RELEASE_API = 'https://api.github.com/repos/Zcross091/frosty-wos-ai/releases/latest';

  fetch(GITHUB_RELEASE_API)
    .then((res) => (res.ok ? res.json() : null))
    .then((data) => {
      if (!data || !data.tag_name) return;

      const latestTag = data.tag_name;
      const releaseName = data.name || `Frosty Release ${latestTag}`;
      const releaseUrl = data.html_url || 'https://github.com/Zcross091/frosty-wos-ai/releases';

      // Check if user dismissed this specific release
      if (localStorage.getItem('dismissed_release') === latestTag) return;

      // Find APK download URL if present
      let apkUrl = releaseUrl;
      if (data.assets && data.assets.length > 0) {
        const apkAsset = data.assets.find((a) => a.name && a.name.endsWith('.apk'));
        if (apkAsset) apkUrl = apkAsset.browser_download_url;
      }

      // Create stylish pop-up element
      const popup = document.createElement('div');
      popup.id = 'release-popup';
      popup.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        max-width: 380px;
        background: rgba(15, 25, 44, 0.95);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid #00F0FF;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0, 240, 255, 0.25), 0 4px 12px rgba(0,0,0,0.6);
        z-index: 99999;
        font-family: 'Outfit', sans-serif;
        color: #ffffff;
        animation: slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1);
      `;

      popup.innerHTML = `
        <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 36px; height: 36px; border-radius: 50%; background: rgba(0, 240, 255, 0.15); border: 1px solid #00F0FF; display: flex; align-items: center; justify-content: center; font-size: 18px;">
              🚀
            </div>
            <div>
              <div style="font-weight: 800; font-size: 15px; color: #ffffff;">New Release Available!</div>
              <div style="font-size: 12px; color: #00F0FF; font-weight: 600;">${latestTag}</div>
            </div>
          </div>
          <button id="close-release-popup" style="background: none; border: none; color: #94A3B8; cursor: pointer; font-size: 18px; line-height: 1; padding: 2px;">✕</button>
        </div>

        <p style="font-size: 13px; color: #CBD5E1; line-height: 1.4; margin: 0 0 14px 0;">
          ${releaseName} is now live with updated Whiteout Survival hero archives and mobile app improvements.
        </p>

        <div style="display: flex; gap: 8px;">
          <a href="${apkUrl}" target="_blank" rel="noopener noreferrer" style="flex: 1; text-align: center; background: #00F0FF; color: #060B13; font-weight: 700; font-size: 12.5px; padding: 9px 14px; border-radius: 10px; text-decoration: none; display: inline-block;">
            📱 Download APK
          </a>
          <a href="${releaseUrl}" target="_blank" rel="noopener noreferrer" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.2); color: #ffffff; font-weight: 600; font-size: 12.5px; padding: 9px 12px; border-radius: 10px; text-decoration: none; display: inline-block;">
            View Notes
          </a>
        </div>
      `;

      document.body.appendChild(popup);

      document.getElementById('close-release-popup').addEventListener('click', () => {
        localStorage.setItem('dismissed_release', latestTag);
        popup.style.opacity = '0';
        popup.style.transform = 'translateY(15px)';
        popup.style.transition = 'all 0.3s ease';
        setTimeout(() => popup.remove(), 300);
      });
    })
    .catch(() => {});
}
