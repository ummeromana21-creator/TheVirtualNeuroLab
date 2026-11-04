/* Feather Atlas shared shell: icons, day/dusk, hub top bar. Load before page scripts. */
window.Feather = (() => {
  const HUBS = [
    { id: 'home', name: 'Home', sub: 'start here', icon: 'i-house', href: 'index.html' },
    { id: 'discover', name: 'Neuron Silencing Screen', sub: 'switch off a neuron', icon: 'i-fly', href: 'discover/' },
    { id: 'disease', name: 'Parkinson\u2019s', sub: 'brain disease', icon: 'i-pulse2', href: 'disease/' },
    { id: 'flies', name: 'Vivarium', sub: 'Fly and her behaviours', icon: 'i-fly', href: 'flies/' },
    { id: 'atlas', name: 'Fly Atlas', sub: 'regions · cell types', icon: 'i-layers', href: 'library/' },
    { id: 'worm', name: 'The worm', sub: 'C. elegans', icon: 'i-worm', href: 'worm/' },
    { id: 'next', name: 'What\u2019s next', sub: 'the plan', icon: 'i-next', href: 'next/' },
  ];
  const DEFS = `<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>`
    + `<symbol id="i-house" viewBox="0 0 24 24"><path d="M4 11l8-7 8 7M6 10v10h12V10"/></symbol>`
    + `<symbol id="i-flask" viewBox="0 0 24 24"><path d="M10 3h4M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 18l-5-9V3"/></symbol>`
    + `<symbol id="i-layers" viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5"/></symbol>`
    + `<symbol id="i-chat" viewBox="0 0 24 24"><path d="M4 6h16v9H9l-5 4V6z"/></symbol>`
    + `<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.5 4.5l2 2M17.5 17.5l2 2M19.5 4.5l-2 2M6.5 17.5l-2 2"/></symbol>`
    + `<symbol id="i-chev" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></symbol>`
    + `<symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 5-6 8-6s6.5 2 8 6"/></symbol>`
    + `<symbol id="i-fly" viewBox="0 0 24 24"><ellipse cx="12" cy="13" rx="3" ry="5"/><path d="M9 11C5 8 3 5 3 5s4-1 7 3M15 11c4-3 6-6 6-6s-4-1-7 3"/></symbol>`
    + `<symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></symbol>`
    + `<symbol id="i-worm" viewBox="0 0 24 24"><path d="M4 16c2-5 5-5 7-2s5 3 7-2"/><circle cx="18.5" cy="9.5" r="1.2"/></symbol>`
    + `<symbol id="i-pulse2" viewBox="0 0 24 24"><path d="M3 12h4l2-5 4 10 2-5h6"/></symbol>`
    + `<symbol id="i-next" viewBox="0 0 24 24"><path d="M5 12h12M13 7l5 5-5 5"/></symbol>`
    + `<symbol id="i-cards" viewBox="0 0 24 24"><rect x="4" y="6" width="16" height="13" rx="2"/><path d="M4 11h16M8 15h5"/></symbol>`
    + `</defs></svg>`;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let onLight = null;

  function icons() {
    // Pages ship their own symbol sets; add only the ones the bar needs.
    const have = id => !!document.getElementById(id);
    if (['i-house', 'i-fly', 'i-menu', 'i-user', 'i-worm', 'i-next', 'i-pulse2'].every(have)) return;
    const wrap = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    wrap.setAttribute('width', '0'); wrap.setAttribute('height', '0');
    wrap.setAttribute('style', 'position:absolute'); wrap.setAttribute('aria-hidden', 'true');
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const tmp = document.createElement('div');
    tmp.innerHTML = DEFS;
    tmp.querySelectorAll('symbol').forEach(s => { if (!have(s.id)) defs.appendChild(s); });
    if (!defs.childNodes.length) return;
    wrap.appendChild(defs);
    document.body.insertAdjacentElement('afterbegin', wrap);
  }
  function mode() { return document.documentElement.dataset.light || 'day'; }
  function apply(m) {
    document.documentElement.dataset.light = m;
    const hero = document.getElementById('hero');
    if (hero) hero.dataset.light = m;
    document.body.style.background = m === 'dusk' ? '#18191a' : '';
    document.querySelectorAll('[data-light-toggle]').forEach(b =>
      b.setAttribute('aria-pressed', String(m === 'dusk')));
    try { localStorage.setItem('feather-light', m); } catch {}
    if (onLight) onLight(m);
  }
  function init(opts = {}) {
    onLight = opts.onLight || null;
    let m = 'day';
    try { m = localStorage.getItem('feather-light') || 'day'; } catch {}
    if (m !== 'day' && m !== 'dusk') m = 'day';
    apply(m);
    document.addEventListener('click', e => {
      const g = e.target.closest('[data-goto]');
      if (g) { location.assign(g.dataset.goto); return; }
      if (e.target.closest('[data-light-toggle]')) apply(mode() === 'dusk' ? 'day' : 'dusk');
    });
    return m;
  }
  function wireProfile(wrap, base) {
    const btn = wrap.querySelector('[data-profile]');
    const menu = wrap.querySelector('.shell-menu');
    const paint = user => {
      if (user) {
        const nm = user.name || user.email || '?';
        btn.innerHTML = `<span class="shell-av" aria-hidden="true">${esc(nm.trim().charAt(0).toUpperCase())}</span>`;
        btn.setAttribute('aria-label', `Account: ${nm}`);
        menu.innerHTML = `<div class="shell-me"><b>${esc(nm)}</b><span>${esc(user.email || '')}</span></div>`
          + `<a href="${base}duo/profile.html">Profile details</a><button data-signout>Sign out</button>`;
        menu.querySelector('[data-signout]').onclick = async e => {
          e.stopPropagation();
          menu.hidden = true;
          try { await window.DuoAuth.signOut(); } catch {}
        };
      } else {
        btn.innerHTML = '<svg class="ic"><use href="#i-user"/></svg>';
        btn.setAttribute('aria-label', 'Sign in');
        menu.innerHTML = `<a href="${base}duo/?signin=1">Sign in / create account</a>`;
      }
    };
    paint(null);
    if (window.DuoAuth) {
      window.DuoAuth.ready.then(() => paint(window.DuoAuth.currentUser())).catch(() => paint(null));
      window.DuoAuth.onAuthChange(paint);
    }
    btn.onclick = e => {
      e.stopPropagation();
      const user = window.DuoAuth && window.DuoAuth.currentUser();
      if (!user) { location.assign(base + 'duo/?signin=1'); return; }
      menu.hidden = !menu.hidden;
    };
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) menu.hidden = true; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') menu.hidden = true; });
  }

  // ---- Guided tour: a short walkthrough per page; runs once automatically on a first visit ----
  const TOURS = {
    home: [
      { t: 'Welcome to the Virtual Neuro Lab', b: 'This lab runs experiments on a simulation of the complete fruit-fly brain, reconstructed synapse by synapse from electron microscopy. This short tour shows you around. You can replay it any time with the Tour button at the top.' },
      { el: '.shell-nav, .shell-menubtn', t: 'Getting around', b: 'Every part of the lab is here. Each page has its own short tour the first time you open it.' },
      { el: '.cta', t: 'Start here: the Neuron Silencing Screen', b: 'Switch off one neuron and see whether the fly can still eat or drink. This is where the lab makes new predictions that no one has tested yet.' },
      { el: '.tiles', t: 'The rest of the lab', b: 'Parkinson\u2019s, the experiments and their full records, the flies in 3D, a map of every brain region, and the worm.' },
      { el: '#muse-btn', t: 'Ask Muse', b: 'Got a question? Muse, Meta’s AI, answers from the lab’s own records first and then the web, and shows its sources.' },
      { el: '[data-light-toggle]', t: 'Light or dark', b: 'Switch between a light and a dark look whenever you like.' },
    ],
    discover: [
      { t: 'The Neuron Silencing Screen', b: 'Here you switch off one neuron at a time in a simulated fly brain and watch whether the signal still reaches the tongue.' },
      { el: '.taste', t: '1. Pick a taste', b: 'Sugar (eating) or water (drinking). This is what we put on the fly’s tongue.' },
      { el: '#filt', t: '2. Choose which neurons to see', b: '“Needed” shows neurons the fly can’t eat or drink without. “New discoveries” are ones no living fly has been tested on, as far as we know.' },
      { el: '#list', t: '3. Switch one off', b: 'Click a neuron to switch it off. The number shows how hard the tongue neuron fires before and after.' },
      { el: '.routes', t: '4. Compare the two brains', b: 'Top: the normal brain. Bottom: the same brain with your neuron switched off. Each map shows the route the signal took to the tongue in most of 20 runs; connections missing from the bottom map went silent.' },
      { el: '.ctrl', t: '5. Play it', b: 'Press Play to watch the signal travel, or drag the slider to step through time.' },
      { el: '.story', t: '6. What it means', b: 'Who the neuron is, what its wiring shows, what switching it off did, how a real fly lab would test it, and what that tells us.' },
      { el: '#infer', t: 'What it all means', b: 'What we can conclude from the results, how it could help in the real world, and what it doesn’t tell us.' },
    ],
    flies: [
      { t: 'The Vivarium', b: 'Meet Fly: a body from a micro-CT scan of a real fruit fly, with a brain wired from the FlyWire map.' },
      { el: '#choose', t: '1. Choose what she senses', b: 'A taste on her tongue, or a touch on her antennae. "Adjust strengths" offers 24 taste mixes.' },
      { el: '#brainView', t: '2. Watch her brain', b: 'The signal comes in, the regions that process it light up, and the neuron that decides fires (or stays grey). Hover over any part to see its name.' },
      { el: '#bodyView', t: '3. See what she does', b: 'Once the deciding neuron fires, she acts: tongue out to feed, or front legs cleaning her antennae.' },
      { el: '#trust', t: 'How far to trust it', b: 'The brain passed its calibration test and was checked against results known from real flies. "See the evidence" has every check, misses included.' },
    ],
    atlas: [
      { t: 'The Fly Atlas', b: 'Every brain and nerve-cord region, what it does, and how much wiring it holds.' },
      { el: '.topsearch, .top', t: 'Search', b: 'Type a region, a job (like “vision”) or a cell type.' },
      { el: '#filterPanel, #filterBtn', t: 'Filter', b: 'Choose which fly to look at and narrow the list by region family.' },
      { el: '#grid', t: 'Open a region', b: 'Each card shows where the region sits in the brain. Open one to explore it in 3D.' },
    ],
    prediction: [
      { t: 'Prediction check', b: 'Before the real 3D data arrived, the lab predicted where each fly’s neurons sit using only its wiring. This page grades that guess.' },
      { el: '#big', t: 'The score', b: 'How closely the prediction matched the real brain, compared with a random guess.' },
      { el: '#overlay', t: 'See it', b: 'Predicted and real positions drawn on top of each other.' },
      { el: '#tbl', t: 'Region by region', b: 'Where the prediction did well and where it missed.' },
    ],
    experiments: [
      { t: 'Taste experiments', b: 'Put tastes on the simulated fly’s tongue, and see how often the untouched brain matches what real flies do.' },
      { el: '.ctrl', t: '1. Choose tastes', b: 'Pick sugar, bitter and water levels, or tap a preset, then press Run.' },
      { el: '.stage', t: '2. Watch the brain', b: 'Taste neurons light up first, then the neurons that respond, then MN9, the neuron that moves the tongue.' },
      { el: '.story', t: '3. Read what happened', b: 'A step-by-step explanation written from that run’s numbers.' },
      { el: '#r1', t: 'The exam', b: 'Round 1 checks the brain against results already known from real flies. Nothing was adjusted to pass; misses stay on the page.' },
      { el: '#infer', t: 'What it all means', b: 'What we conclude, how it could help in the real world, and the limits.' },
    ],
    worm: [
      { t: 'Meet the worm', b: 'C. elegans is a 1 mm roundworm and the first animal whose whole wiring diagram was mapped. All 302 of its neurons are here.' },
      { el: '#stage', t: 'Look around', b: 'Drag to turn, scroll to zoom. The head is on the left. Hover a dot to see a neuron\u2019s name; click it to see who it talks to.' },
      { el: '#legend', t: 'Three kinds of neuron', b: 'Blue neurons sense the world, amber ones decide, pink ones move the body. Tap a group to hide or show it.' },
      { el: '#presets', t: 'Famous circuits', b: 'Light up a well-known circuit, like the one that makes the worm back away when its head is touched.' },
      { el: '#q', t: 'Find a neuron', b: 'Every worm neuron has a name, the same in every worm. Type one, like AVAL.' },
    ],
    disease: [
      { t: 'Parkinson\u2019s: the mechanism', b: 'In Parkinson\u2019s, dopamine-making neurons die. This page traces, in a real fly brain\u2019s wiring, where their signal goes and what is cut off as they die.' },
      { el: '#scen', t: 'Choose how they die', b: 'Fly models report losses in different clusters. Pick a pattern.' },
      { el: '.slider', t: 'Let them die', b: 'Drag the slider or press Play. Dead dopamine neurons turn grey; neurons that lose their dopamine input turn from blue to red.' },
      { el: '#find', t: 'What the wiring shows', b: 'The main findings, calculated from the data, followed by what dopamine is known to do there.' },
    ],
    next: [
      { t: 'What\u2019s next', b: 'Where the lab goes from here: predictions waiting for a real-fly test, work in progress, and plans.' },
      { el: '#preds', t: 'Predictions to test', b: 'Each card says how sure we are, from 30 repeated runs and the model\u2019s track record, and whether a real-fly test is known.' },
      { el: '.how', t: 'How a lab could test one', b: 'The steps a fly lab would take to confirm or reject a prediction.' },
    ],
    notebook: [
      { t: 'The lab notebook', b: 'A full record of every experiment: question, method, pass mark, results, conclusion, how sure we are, and whether it points to a discovery.' },
      { el: '#how-sure', t: 'How sure are we?', b: 'How each prediction gets its confidence level, and why none of them is proof yet.' },
      { el: '#filters', t: 'Find records', b: 'Show only potential discoveries, results that match real flies, or misses.' },
      { el: '#list', t: 'Open a record', b: 'Click any record to see every detail of that experiment.' },
    ],
    calibration: [
      { t: 'The calibration test', b: 'Before any experiment, the simulated brain must get a known result right: sugar makes a fly stick out its tongue, bitter stops it.' },
      { el: '#verdicts', t: 'The result', b: 'Whether the brain passed, and by how much.' },
      { el: '#chart', t: 'More sugar, more tongue', b: 'How the tongue neuron responds as the sugar signal gets stronger.' },
      { el: '#engine', t: 'Can the engine be trusted?', b: 'Our simulation engine checked against the original authors’ own code.' },
    ],
  };
  const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch {} } };
  let tourKey = null;
  function pick(sel) {
    if (!sel) return null;
    for (const q of sel.split(',')) {
      const n = document.querySelector(q.trim());
      if (n) { const r = n.getBoundingClientRect(); if (r.width > 0 && r.height > 0 && getComputedStyle(n).visibility !== 'hidden') return n; }
    }
    return null;
  }
  function tourCSS() {
    if (document.getElementById('tour-css')) return;
    const c = document.createElement('style'); c.id = 'tour-css';
    c.textContent = `.tourbtn{display:flex;align-items:center;gap:6px;height:34px;padding:0 14px;border-radius:100px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font-weight:600;font-size:13px;cursor:pointer;white-space:nowrap}
.tourbtn:hover{border-color:var(--sage)}.tourbtn .q{width:18px;height:18px;border-radius:50%;background:var(--sage);color:var(--sage-ink);display:grid;place-items:center;font-size:11.5px;font-weight:700}
#tour-veil{position:fixed;inset:0;z-index:90}
#tour-spot{position:fixed;z-index:91;border-radius:14px;box-shadow:0 0 0 3px var(--focus),0 0 0 9999px rgba(0,0,0,.55);pointer-events:none;transition:all .3s var(--ease,ease)}
#tour-spot.none{box-shadow:0 0 0 9999px rgba(0,0,0,.55);width:0!important;height:0!important;left:50%!important;top:50%!important}
#tour-box{position:fixed;z-index:92;width:min(380px,calc(100vw - 32px));background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:20px;padding:18px 18px 14px;box-shadow:0 18px 50px rgba(0,0,0,.3);font-size:15px;line-height:1.55}
#tour-box h2{font-family:inherit;font-size:18px;font-weight:700;letter-spacing:-.01em;margin:0 0 6px}
#tour-box p{margin:0 0 14px}
#tour-box .row{display:flex;align-items:center;gap:8px}
#tour-box .n{font-size:12.5px;color:var(--muted);margin-right:auto}
#tour-box button{font:inherit;font-size:14px;font-weight:600;border-radius:100px;padding:8px 16px;cursor:pointer;border:1px solid var(--line);background:var(--panel);color:var(--ink)}
#tour-box button.pri{background:var(--sage);color:var(--sage-ink);border-color:var(--sage)}
#tour-box .off{border:none;background:none;padding:0;font-size:12.5px;font-weight:400;color:var(--muted);text-decoration:underline;margin-top:10px;display:block}
@media (max-width:700px){#tour-box{left:16px!important;right:16px;width:auto;bottom:16px!important;top:auto!important}}`;
    document.head.appendChild(c);
  }
  function startTour(key) {
    const steps = TOURS[key]; if (!steps) return;
    endTour(); tourCSS();
    store.set('flylab-tour-' + key, 'seen');
    const back = document.activeElement;
    const veil = document.createElement('div'); veil.id = 'tour-veil';
    const spot = document.createElement('div'); spot.id = 'tour-spot'; spot.setAttribute('aria-hidden', 'true');
    const box = document.createElement('div'); box.id = 'tour-box';
    box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-labelledby', 'tour-h'); box.setAttribute('aria-describedby', 'tour-p');
    document.body.append(veil, spot, box);
    let i = 0, target = null;
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    function place() {
      const W = innerWidth, H = innerHeight;
      if (!target) { spot.className = 'none'; box.style.left = Math.max(16, (W - box.offsetWidth) / 2) + 'px'; box.style.top = Math.max(16, (H - box.offsetHeight) / 2) + 'px'; return; }
      spot.className = '';
      const r = target.getBoundingClientRect(), pad = 6;
      const top = Math.max(4, r.top - pad), left = Math.max(4, r.left - pad);
      const bottom = Math.min(H - 4, r.bottom + pad), right = Math.min(W - 4, r.right + pad);
      Object.assign(spot.style, { left: left + 'px', top: top + 'px', width: Math.max(0, right - left) + 'px', height: Math.max(0, bottom - top) + 'px' });
      if (W <= 700) return;  // phones: the box sits at the bottom (CSS)
      const bw = box.offsetWidth, bh = box.offsetHeight, gap = 14;
      let x, y;
      if (H - bottom >= bh + gap) { y = bottom + gap; x = left; }
      else if (top >= bh + gap) { y = top - bh - gap; x = left; }
      else if (W - right >= bw + gap) { x = right + gap; y = top; }
      else if (left >= bw + gap) { x = left - bw - gap; y = top; }
      else { x = (W - bw) / 2; y = H - bh - 16; }
      box.style.left = Math.min(Math.max(16, x), W - bw - 16) + 'px';
      box.style.top = Math.min(Math.max(16, y), H - bh - 16) + 'px';
    }
    function show(k) {
      i = k; const st = steps[i];
      target = pick(st.el);
      box.innerHTML = `<h2 id="tour-h">${esc(st.t)}</h2><p id="tour-p">${esc(st.b)}</p><div class="row"><span class="n">${i + 1} of ${steps.length}</span>`
        + (i ? '<button data-b>Back</button>' : '<button data-x>Skip</button>')
        + `<button class="pri" data-n>${i === steps.length - 1 ? 'Done' : 'Next'}</button></div>`
        + (i === 0 ? '<button class="off" data-off>Don’t show tours automatically</button>' : '');
      if (target) target.scrollIntoView({ block: 'center', inline: 'nearest', behavior: reduce ? 'auto' : 'smooth' });
      place(); setTimeout(place, reduce ? 0 : 420);
      box.querySelector('[data-n]').focus();
    }
    box.addEventListener('click', e => {
      if (e.target.closest('[data-n]')) { i < steps.length - 1 ? show(i + 1) : endTour(); }
      else if (e.target.closest('[data-b]')) show(i - 1);
      else if (e.target.closest('[data-x]')) endTour();
      else if (e.target.closest('[data-off]')) { store.set('flylab-tour-off', '1'); endTour(); }
    });
    const onKey = e => {
      if (e.key === 'Escape') { e.preventDefault(); endTour(); }
      else if (e.key === 'ArrowRight') { i < steps.length - 1 ? show(i + 1) : endTour(); }
      else if (e.key === 'ArrowLeft' && i) show(i - 1);
      else if (e.key === 'Tab') {  // keep focus inside the tour box
        const f = [...box.querySelectorAll('button')]; const a = f.indexOf(document.activeElement);
        e.preventDefault(); f[(a + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
      }
    };
    const onMove = () => place();
    document.addEventListener('keydown', onKey, true); addEventListener('resize', onMove); addEventListener('scroll', onMove, true);
    tourKey = { veil, spot, box, onKey, onMove, back };
    show(0);
  }
  function endTour() {
    if (!tourKey) return;
    const { veil, spot, box, onKey, onMove, back } = tourKey; tourKey = null;
    veil.remove(); spot.remove(); box.remove();
    document.removeEventListener('keydown', onKey, true); removeEventListener('resize', onMove); removeEventListener('scroll', onMove, true);
    const tb = document.querySelector('.tourbtn'); (tb || back || document.body).focus && (tb || back).focus();
  }
  function pageKey(current) { return /calibration\.html$/.test(location.pathname) ? 'calibration' : /notebook\.html$/.test(location.pathname) ? 'notebook' : current; }
  function skipLink() {
    if (document.querySelector('.skiplink')) return;
    const m = document.querySelector('main, [role="main"]'); if (!m) return;
    if (!m.id) m.id = 'main';
    if (!m.hasAttribute('tabindex')) m.setAttribute('tabindex', '-1');
    const a = document.createElement('a'); a.className = 'skiplink'; a.href = '#' + m.id; a.textContent = 'Skip to content';
    document.body.insertAdjacentElement('afterbegin', a);
  }
  // Build the shared top bar into el. extras: selectors adopted into the right slot.
  function topbar(el, { brand, sub = '', base = './', current = '', extras = [], light = true, profile = true } = {}) {
    icons();
    const kept = extras.map(s => document.querySelector(s)).filter(Boolean);
    kept.forEach(n => n.remove());
    const items = HUBS.map(h => {
      const inner = `<svg class="ic"><use href="#${h.icon}"/></svg><span>${h.name}<small>${h.sub}</small></span>`;
      return h.id === current
        ? `<span class="cur" aria-current="page">${inner}</span>`
        : `<a href="${base + h.href}">${inner}</a>`;
    }).join('');
    el.classList.add('shell-top');
    el.innerHTML = `<div class="shell-brand"><span class="shell-name">${brand}</span>`
      + (sub ? `<span class="shell-sub">${sub}</span>` : '') + `</div>`
      + `<button class="shell-menubtn iconbtn" aria-expanded="false" aria-label="Open menu"><svg class="ic"><use href="#i-menu"/></svg></button>`
      + `<nav class="shell-nav" aria-label="The Virtual Neuro Lab">${items}</nav><div class="shell-extra"></div>`;
    const nav = el.querySelector('.shell-nav');
    const menuBtn = el.querySelector('.shell-menubtn');
    menuBtn.addEventListener('click', e => {
      e.stopPropagation();
      const open = nav.classList.toggle('open');
      menuBtn.setAttribute('aria-expanded', String(open));
      menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
    document.addEventListener('click', e => {
      if (!el.contains(e.target) && nav.classList.contains('open')) {
        nav.classList.remove('open');
        menuBtn.setAttribute('aria-expanded', 'false');
        menuBtn.setAttribute('aria-label', 'Open menu');
      }
    });
    const slot = el.querySelector('.shell-extra');
    kept.forEach(n => slot.appendChild(n));
    const key = pageKey(current);
    if (TOURS[key]) {
      tourCSS();
      const tb = document.createElement('button');
      tb.className = 'tourbtn'; tb.type = 'button';
      tb.innerHTML = '<span class="q" aria-hidden="true">?</span>Tour';
      tb.setAttribute('aria-label', 'Start a guided tour of this page');
      tb.onclick = e => { e.stopPropagation(); startTour(key); };
      el.appendChild(tb);
      if (!store.get('flylab-tour-off') && !store.get('flylab-tour-' + key)) setTimeout(() => { if (!tourKey) startTour(key); }, 1400);
    }
    skipLink();
    if (light) {
      const b = document.createElement('button');
      b.className = 'iconbtn'; b.dataset.lightToggle = '';
      b.setAttribute('aria-label', 'Dark mode');
      b.setAttribute('aria-pressed', String(mode() === 'dusk'));
      b.innerHTML = '<svg class="ic"><use href="#i-sun"/></svg>';
      el.appendChild(b);
    }
    if (profile) {
      const wrap = document.createElement('div');
      wrap.className = 'shell-prof';
      wrap.innerHTML = '<button class="iconbtn" data-profile aria-label="Sign in"><svg class="ic"><use href="#i-user"/></svg></button><div class="shell-menu" hidden></div>';
      el.appendChild(wrap);
      wireProfile(wrap, base);
    }
    askMuse();
    return el;
  }
  // ---- Ask Muse: floating panel on every page (answers come from tools/server.py) ----
  function askMuse() {
    if (document.getElementById('muse-btn')) return;
    const css = document.createElement('style');
    css.textContent = `#muse-btn{position:fixed;right:18px;bottom:18px;z-index:60;background:var(--sage);color:var(--sage-ink);border:none;border-radius:999px;padding:11px 16px;font-weight:700;font-size:14px;box-shadow:0 6px 20px rgba(0,0,0,.18);cursor:pointer}
#muse-pane{position:fixed;right:18px;bottom:70px;z-index:61;width:min(420px,calc(100vw - 32px));max-height:min(620px,calc(100dvh - 100px));display:flex;flex-direction:column;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:16px;box-shadow:0 14px 40px rgba(0,0,0,.22);overflow:hidden}
#muse-pane[hidden]{display:none}
#muse-pane header{padding:12px 14px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:8px}
#muse-pane header b{font-size:15px}#muse-pane header small{display:block;color:var(--muted);font-size:11.5px}
#muse-pane .x{background:none;border:none;font-size:20px;cursor:pointer;color:var(--muted)}
#muse-log{flex:1;overflow:auto;padding:12px 14px;display:flex;flex-direction:column;gap:10px;font-size:14px;line-height:1.55}
.mq{align-self:flex-end;background:var(--sage-tint);border-radius:12px 12px 2px 12px;padding:8px 11px;max-width:85%}
.ma{background:var(--bg);border-radius:12px 12px 12px 2px;padding:9px 11px}
.ma sup{margin:0 2px}.ma sup a{font-size:10.5px;text-decoration:none;font-weight:700;margin-left:1px}
.ma .src{margin-top:8px;display:flex;flex-direction:column;gap:4px;font-size:12px}
.ma .src a{color:var(--ink)}.ma .src .k{font-size:10.5px;font-weight:700;letter-spacing:.06em;padding:1px 6px;border-radius:6px;margin-right:6px}
.k-lab{background:var(--ok-bg);color:var(--ok-ink)}.k-web{background:var(--info-bg);color:var(--info-ink)}
.ma .ai{font-size:11px;color:var(--muted);margin-top:6px}
#muse-form{display:flex;gap:8px;padding:10px;border-top:1px solid var(--line)}
#muse-form input{flex:1;border:1px solid var(--line);border-radius:10px;padding:9px 11px;background:var(--bg);color:var(--ink);font:inherit}
#muse-form button{background:var(--sage);color:var(--sage-ink);border:none;border-radius:10px;padding:0 14px;font-weight:700;cursor:pointer}
.mchips{display:flex;flex-wrap:wrap;gap:6px}.mchips button{background:none;border:1px dashed var(--line);border-radius:999px;padding:4px 10px;font-size:12px;color:var(--muted);cursor:pointer}`;
    document.head.appendChild(css);
    const btn = document.createElement('button'); btn.id = 'muse-btn'; btn.textContent = 'Ask Muse';
    const pane = document.createElement('section'); pane.id = 'muse-pane'; pane.hidden = true; pane.setAttribute('aria-label', 'Ask Muse');
    pane.innerHTML = `<header><div><b>Ask Muse</b><small>Answers from the lab's records first, then the web. Written by AI; check the sources.</small></div><button class="x" aria-label="Close">×</button></header>
      <div id="muse-log" aria-live="polite"><div class="mchips">${['What is MN9?', 'Why did experiment E4 miss?', 'What does the Neuron Silencing Screen predict?', 'What happens when dopamine neurons die?'].map(q => `<button>${q}</button>`).join('')}</div></div>
      <form id="muse-form"><input placeholder="Ask anything about the lab…" aria-label="Your question" maxlength="1000"><button>Ask</button></form>`;
    document.body.append(btn, pane);
    const log = pane.querySelector('#muse-log'), input = pane.querySelector('input');
    const esc = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    btn.onclick = () => { pane.hidden = !pane.hidden; if (!pane.hidden) input.focus(); };
    pane.querySelector('.x').onclick = () => { pane.hidden = true; };
    log.querySelector('.mchips').addEventListener('click', e => { const b = e.target.closest('button'); if (b) send(b.textContent); });
    pane.querySelector('form').onsubmit = e => { e.preventDefault(); const q = input.value.trim(); if (q) { input.value = ''; send(q); } };
    async function send(q) {
      log.insertAdjacentHTML('beforeend', `<div class="mq">${esc(q)}</div>`);
      const a = document.createElement('div'); a.className = 'ma'; a.textContent = 'Looking in the lab…'; log.appendChild(a); log.scrollTop = log.scrollHeight;
      let r;
      try { r = await (await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q, page: location.pathname + location.hash }) })).json(); }
      catch (err) { r = { answer: 'Muse is offline: start the lab with start_skeleton.command (it runs the lab’s own server).', sources: [] }; }
      const S = Object.fromEntries((r.sources || []).map(s => [s.id, s]));
      let html = esc(r.answer || '').replace(/\[([LW]\d+)\]/g, (m, id) => S[id] ? `<sup><a href="${esc(S[id].url)}" ${S[id].kind === 'web' ? 'target="_blank" rel="noopener"' : ''} title="${esc(S[id].title)}">${id}</a></sup>` : '').replace(/\n/g, '<br>');
      if ((r.sources || []).length) html += `<div class="src">${r.sources.map(s => `<div><span class="k ${s.kind === 'web' ? 'k-web' : 'k-lab'}">${s.kind === 'web' ? 'WEB' : 'LAB'} ${s.id}</span><a href="${esc(s.url)}" ${s.kind === 'web' ? 'target="_blank" rel="noopener"' : ''}>${esc(s.title)}</a>${s.where ? ` <span style="color:var(--muted)">· ${esc(s.where)}</span>` : ''}</div>`).join('')}</div>`;
      if (r.model) html += `<div class="ai">Written by ${esc(r.model)} (Meta). It can make mistakes; it can't run or change experiments.</div>`;
      a.innerHTML = html; log.scrollTop = log.scrollHeight;
    }
  }
  return { icons, init, mode, topbar, HUBS, startTour, endTour };
})();
