/* Chemical Library: list + filters + detail sheet, all from data.json. */
"use strict";
(async () => {
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const CONF_CLASS = { fly: "c-fly", insect: "c-insect", mammal: "c-mammal", none: "c-none" };

  let data;
  try { data = await (await fetch("data.json?v=2")).json(); }
  catch (e) { $("grid").innerHTML = '<p class="empty">Could not load data.json — open this page through the local server, not by double-clicking the file.</p>'; return; }

  const items = data.chemicals;
  const state = { q: "", group: null, conf: null };

  // ---------- filters ----------
  const chip = (label, on, attr, val) =>
    `<button ${attr}="${esc(val)}" aria-pressed="${on}">${esc(label)}</button>`;
  function paintChips() {
    $("groups").innerHTML = chip("All groups", !state.group, "data-group", "")
      + data.groups.map(g => chip(g, state.group === g, "data-group", g)).join("");
    $("confs").innerHTML = chip("Any evidence", !state.conf, "data-conf", "")
      + Object.entries(data.confidence).map(([k, v]) => chip(v.label, state.conf === k, "data-conf", k)).join("");
  }
  $("groups").addEventListener("click", e => {
    const b = e.target.closest("[data-group]"); if (!b) return;
    state.group = b.dataset.group || null; paintChips(); paint();
  });
  $("confs").addEventListener("click", e => {
    const b = e.target.closest("[data-conf]"); if (!b) return;
    state.conf = b.dataset.conf || null; paintChips(); paint();
  });
  $("q").addEventListener("input", e => { state.q = e.target.value.trim().toLowerCase(); paint(); });

  const hay = c => [c.name, c.sci || "", c.group, c.what, c.fly,
    ...(c.targets || []).map(t => t.name + " " + t.role)].join(" ").toLowerCase();
  const confTag = k => `<span class="conf ${CONF_CLASS[k]}">${esc(data.confidence[k].label)}</span>`;
  const pic = c => c.img
    ? `<img src="${esc(c.img)}" alt="2D structure of ${esc(c.name)}" loading="lazy">`
    : `<span class="noimg">${esc(c.formula === "protein" ? "a protein — no small-molecule drawing" : "no structure")}</span>`;

  // ---------- grid ----------
  function paint() {
    const shown = items.filter(c =>
      (!state.group || c.group === state.group) &&
      (!state.conf || c.confidence === state.conf) &&
      (!state.q || hay(c).includes(state.q)));
    $("count").textContent = shown.length === items.length
      ? `${items.length} substances`
      : `${shown.length} of ${items.length} substances`;
    $("grid").innerHTML = shown.length ? shown.map(c => `
      <button class="card" data-id="${esc(c.id)}">
        <div class="pic">${pic(c)}</div>
        <div class="body">
          <span class="grp">${esc(c.group)}</span>
          <h2 class="serif">${esc(c.name)}</h2>
          ${c.sci ? `<p class="sci">${esc(c.sci)}</p>` : ""}
          <p class="one">${esc(c.what)}</p>
          <div>${confTag(c.confidence)}</div>
        </div>
      </button>`).join("")
      : '<p class="empty">Nothing matches. Try another word or clear the filters.</p>';
  }
  $("grid").addEventListener("click", e => {
    const b = e.target.closest("[data-id]"); if (b) open(b.dataset.id);
  });

  // ---------- detail ----------
  let lastFocus = null;
  function open(id, push = true) {
    const c = items.find(x => x.id === id); if (!c) return;
    lastFocus = document.activeElement;
    const conf = data.confidence[c.confidence];
    $("detail").innerHTML = `
      <div class="dhead">
        <span class="grp eyebrow">${esc(c.group)}</span>
        <h2 id="dName">${esc(c.name)}</h2>
        <p class="what">${esc(c.what)}</p>
      </div>
      <div class="dpic">${pic(c)}</div>
      <div class="meta">
        ${c.formula ? `<span>Formula <b>${esc(c.formula)}</b></span>` : ""}
        ${c.sci ? `<span>Scientific name <b class="sci">${esc(c.sci)}</b></span>` : ""}
      </div>
      <h3>In a real fruit fly</h3>
      <p>${esc(c.fly)}</p>
      <h3>How a fly meets it</h3>
      <p>${esc(c.route)}</p>
      <h3>What it acts on in the fly</h3>
      <ul class="targets">${(c.targets || []).map(t =>
        `<li><b>${esc(t.name)}</b> <span>— ${esc(t.role)}</span></li>`).join("")}</ul>
      <h3>How sure are we?</h3>
      <div class="confbox">${confTag(c.confidence)}<p>${esc(conf.help)}</p></div>
      <h3>Papers</h3>
      ${c.refs && c.refs.length
        ? `<ol class="refs">${c.refs.map(r => `<li>${esc(r.cite)}<span class="claim">${esc(r.claim)}</span></li>`).join("")}</ol>`
        : '<p class="dim">No fly paper — there is no known fly target.</p>'}
      ${c.pubchem ? `<a class="ext" href="https://pubchem.ncbi.nlm.nih.gov/compound/${encodeURIComponent(c.pubchem)}" target="_blank" rel="noopener">
        <svg class="ic"><use href="#i-out"/></svg>PubChem record</a>` : ""}`;
    $("sheet").hidden = false;
    document.body.style.overflow = "hidden";
    document.querySelector("#sheet .panel").scrollTop = 0;
    document.querySelector("#sheet .panel").focus();
    if (push) history.replaceState(null, "", "#" + c.id);
  }
  function close() {
    $("sheet").hidden = true;
    document.body.style.overflow = "";
    history.replaceState(null, "", location.pathname + location.search);
    if (lastFocus) lastFocus.focus();
  }
  $("sheet").addEventListener("click", e => { if (e.target.closest("[data-close]")) close(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !$("sheet").hidden) close(); });

  paintChips();
  paint();
  if (location.hash.length > 1) open(decodeURIComponent(location.hash.slice(1)), false);
})();
