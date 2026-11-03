/* (three.js loads only inside the brains rail module, ask/brain3d.js.) */

/* ================= 1. CONFIG + ERROR OVERLAY ================= */
const WS_SCHEME = location.protocol === 'https:' ? 'wss' : 'ws';
const WS_URL = `${WS_SCHEME}://${location.hostname || 'localhost'}:8765`;
const errBox = document.getElementById('err');
function showErr(msg) { errBox.style.display = 'block'; errBox.textContent += msg + '\n'; }
addEventListener('error', e => showErr('Error: ' + (e.message || e.error)));
addEventListener('unhandledrejection', e => showErr('Rejected: ' + (e.reason && e.reason.message || e.reason)));

/* ================= 2. LIVE DATA LAYER ================= */
const Live = {
  ws: null, hello: null, state: null, idSeq: 0, pending: {},
  subs: { hello: [], state: [], result: [] },
  on(ev, fn) { (this.subs[ev] || (this.subs[ev] = [])).push(fn); },
  emit(ev, data) { for (const fn of this.subs[ev] || []) { try { fn(data); } catch (e) { showErr(ev + ': ' + e.message); } } },
  get connected() { return !!this.ws && this.ws.readyState === 1; },
  send(obj) {
    if (!this.connected) { setStatus('off', 'lab offline — command dropped'); return null; }
    const id = 's' + (++this.idSeq);
    try {
      this.ws.send(JSON.stringify({ ...obj, id }));
    } catch { return null; }  // dropped between check and send: caller falls back
    return id;
  },
  ask(obj, cb, timeout = 15000) {
    const id = this.send(obj);
    if (!id) return;
    this.pending[id] = cb;
    setTimeout(() => delete this.pending[id], timeout);
  },
  connect() {
    setStatus('off', 'connecting…');
    let ws;
    try { ws = new WebSocket(WS_URL); } catch { return void setTimeout(() => this.connect(), 2000); }
    this.ws = ws;
    ws.onopen = () => setStatus('off', 'Start the lab to see the flies live — replays still work');
    ws.onmessage = ev => {
      let m;
      try { m = JSON.parse(ev.data); } catch { return; }
      if (m.type === 'hello') { this.hello = m; this.emit('hello', m); }
      else if (m.type === 'state') { this.state = m; this.emit('state', m); }
      else if (m.type === 'result') { this.emit('result', m); }
      else if (m.type === 'experiment_progress' || m.type === 'experiment_done' || m.type === 'experiment_cancelled') { this.emit(m.type, m); }
      else if (m.type === 'notebook_log') { this.emit('notebook_log', m); }
      else if (m.type === 'ack') {
        const cb = this.pending[m.id];
        if (cb) { delete this.pending[m.id]; cb(m); }
      }
    };
    ws.onclose = () => {
      this.ws = null;
      for (const id of Object.keys(this.pending)) {  // never strand a waiter on a dead socket
        try { this.pending[id](null); } catch {}
        delete this.pending[id];
      }
      setStatus('off', 'offline — retrying…');
      setTimeout(() => this.connect(), 2000);
    };
    ws.onerror = () => { try { ws.close(); } catch {} };
  },
};
const statusEl = document.getElementById('status');
const statusText = document.getElementById('statusText');
function setStatus(mode, text) {
  statusEl.classList.toggle('live', mode === 'live');
  statusText.textContent = text;
}
let liveTick = 0;
Live.on('state', st => {
  liveTick++;
  if (liveTick % 10 === 1) {
    const txt = innerWidth < 600 ? `live · ${st.sps}/s` : `live · step ${st.t} · ${st.sps}/s`;
    setStatus('live', txt);
  }
});

/* ================= 3. SHARED HELPERS ================= */
const SLOTS = ['control:banc', 'control:malecns', 'treatment:banc', 'treatment:malecns'];
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function slotShort(slot) { return slot.startsWith('control') ? 'C·' + slot.slice(8, 10).toUpperCase() : 'V·' + slot.slice(10, 12).toUpperCase(); }
function flyName(slot) {
  const box = slot.startsWith('control') ? 'C' : 'V';
  const label = (Live.hello && Live.hello.flies[slot] && Live.hello.flies[slot].label) || slotShort(slot);
  return `${box} · ${label}`;
}
function drugList(fs) {
  if (!fs || !fs.drugs) return '—';
  const parts = Object.entries(fs.drugs).map(([d, a]) => `${esc(d)} ${(+a).toFixed(3)}`);
  return parts.length ? parts.join(', ') : 'clean';
}

/* ================= 4. BRAINS RAIL (static #brainWrap, wired by ask/app.js) =====
   The Ask bench owns this rail: fly tabs + one shared 3D brain stage. Study
   only publishes its Live layer (globalThis.StudyLive, set below) so the bench
   can subscribe to the page's single socket. */
globalThis.StudyLive = Live;   // read by ask/app.js initOnce (classic script, loaded first)

/* ================= 5. LAB PAGES 1–5 ================= */
const page = document.getElementById('page');
const benchStash = new Map();   // bench id -> detached #page children (ask keeps its thread)
const Labs = {
  current: null, refs: {},
  open(id) {
    const lab = LABS.find(l => l.id === id);
    if (!lab) return;
    const page = document.getElementById('page');
    if (this.current && this.current !== id) benchStash.set(this.current, [...page.childNodes]);
    page.replaceChildren();
    this.current = id;
    this.refs = {};
    document.getElementById('pagewrap').scrollTop = 0;
    paintBenchTabs();
    lab.render();
    this.tick();
  },
  tick() {
    if (!Live.state) return;
    const lab = LABS.find(l => l.id === this.current);
    if (lab && lab.tick) { try { lab.tick(); } catch (e) { showErr('tick ' + this.current + ': ' + e.message); } }
  },
};
function renderAsk() {
  AskBench.mount(document.getElementById('page'));
}
function initBenchTabs() {
  const bar = document.getElementById('benchTabs');
  if (LABS.length < 2) { if (bar) bar.style.display = 'none'; return; }
  for (const lab of LABS) {
    const b = document.createElement('button');
    b.dataset.lab = lab.id;
    b.textContent = lab.name.split(' ')[0];   // Ask (sole bench; row hides when alone)
    b.title = lab.name;
    b.onclick = () => Labs.open(lab.id);
    bar.appendChild(b);
  }
  paintBenchTabs();
}
function paintBenchTabs() {
  const bar = document.getElementById('benchTabs');
  if (!bar) return;
  for (const b of bar.children) b.setAttribute('aria-current', String(b.dataset.lab === Labs.current));
}

/* ================= 7. REGISTRY, NAV, MINI, BOOT ================= */
const LABS = [
  { id: 'ask', name: 'Ask the flies', render: renderAsk },
];
function initNav() {
  Feather.topbar(document.getElementById('shellBar'), { brand: 'Fly Lab', sub: 'Study · ask · benches · live', base: './', current: 'study' });
  Feather.init();
}
const mini = document.getElementById('mini');
function tickMini() {
  const st = Live.state;
  if (!st) { mini.innerHTML = '<p class="note">Start the lab to see the flies live — replays still work.</p>'; return; }
  mini.innerHTML = `<div class="kv"><b>step ${st.t}</b> · ${st.sps}/s · focus ${esc(flyName(st.focus))}</div>
    <div class="kv">${st.trial ? `trial ${esc(st.trial.label)} ${(st.trial.progress * 100).toFixed(0)}%` : 'no trial'}</div>
    <div class="kv">${st.experiment ? `exp ${esc(st.experiment.label)} ${(st.experiment.progress * 100).toFixed(0)}%` : 'no experiment'}</div>
    <div class="kv" style="margin-top:6px">${SLOTS.map(s => {
      const fs = st.flies[s];
      return `<div>${esc(flyName(s))}: ${((fs.rates.all || 0) * st.sps).toFixed(1)}/s · ${drugList(fs)}</div>`;
    }).join('')}</div>`;
}
let lastT = performance.now(), tickAcc = 0;
function frame(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000);
  lastT = now;
  try {
    tickAcc += dt;
    if (tickAcc > 0.12) {
      tickAcc = 0;
      Labs.tick();
      tickMini();
    }
  } catch (e) { showErr('frame: ' + e.message); }
  requestAnimationFrame(frame);
}
function paintStrip(el, s) {
  const provOk = s.provenance === "ALL PASS";
  const refOk = s.green === s.total && s.total > 0;
  el.innerHTML =
    `<span class="${provOk ? "ok" : "bad"}">provenance ${esc(s.provenance)}</span>` +
    `<span class="${refOk ? "ok" : "bad"}">referees ${s.green}/${s.total}</span>` +
    `<span>${esc(s.weight_model)} · dose ${esc(s.dose_model)}</span>` +
    `<span>site ${esc(s.commit_site)} · sim ${esc(s.commit_sim)}</span>` +
    `<span>checked ${esc(s.built_utc)}</span>`;
  el.hidden = false;
}
function loadStrip() {
  const el = document.getElementById('modelstrip');
  if (!el) return;
  fetch('status.json').then(r => r.json()).then(s => paintStrip(el, s)).catch(() => {});
}
initNav();
initBenchTabs();
loadStrip();
Labs.open('ask');
Live.connect();
AskBench.initOnce();
Live.on('hello', () => Labs.open(Labs.current || 'ask'));
requestAnimationFrame(frame);
