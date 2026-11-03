// Pure logic for the cell-type viewer (no three.js here, so node can test it).
// Rule sources: BUILD brief + approved changes; nt rule mirrors build_celltypes.py.

export function stem(name) {
  // Sibling stem: strip one trailing lowercase letter ("T4a" -> "T4").
  return /[a-z]$/.test(name) ? name.slice(0, -1) : name;
}

export function siblings(names, name) {
  const s = stem(name);
  return names.filter(n => n !== name && stem(n) === s);
}

export function sideName(code) {
  return code === 1 ? "left" : code === 2 ? "right" : "central/unknown";
}

// nt: {ACH: n, ..., unknown?: n}. Shares are of PREDICTED neurons; the
// unpredicted share is reported separately. Returns {text, mixed, tie}.
export function ntSummary(nt, n) {
  const known = Object.entries(nt).filter(([k]) => k !== "unknown");
  const tot = known.reduce((a, [, v]) => a + v, 0);
  const unk = nt.unknown || 0;
  let text, mixed = false, tie = false;
  if (!tot) {
    text = "unpredicted";
  } else {
    const best = Math.max(...known.map(([, v]) => v));
    const winners = known.filter(([, v]) => v === best).map(([k]) => k).sort();
    const pct = Math.round(100 * best / tot);
    tie = winners.length > 1;
    text = tie ? `${winners.join("/")} tie ${pct}%` : `${winners[0]} ${pct}%`;
    mixed = best / tot <= 0.60;
    if (mixed) text += " — mixed prediction";
  }
  if (unk && n) text += ` · ${Math.round(100 * unk / n)}% unpredicted`;
  return { text, mixed, tie };
}

// Full split for cards: "ACH 82%, GLUT 15% (predicted; 52% unpredicted)".
export function ntFull(nt) {
  const known = Object.entries(nt).filter(([k]) => k !== "unknown")
    .sort((a, b) => b[1] - a[1]);
  const tot = known.reduce((a, [, v]) => a + v, 0);
  const unk = nt.unknown || 0;
  const n = tot + unk;
  if (!tot) return "unpredicted";
  const parts = known.filter(([, v]) => 100 * v / tot >= 0.5)
    .map(([k, v]) => `${k} ${Math.round(100 * v / tot)}%`);
  let s = parts.join(", ") + " (of predicted";
  if (unk) s += `; ${Math.round(100 * unk / n)}% unpredicted`;
  s += ")";
  const best = known[0][1];
  if (known.length > 1 && known[1][1] === best) s += "; tie — mixed prediction";
  else if (best / tot <= 0.60) s += "; mixed prediction";
  return s;
}

export function parseHash(hash) {
  const h = (hash || "").replace(/^#/, "");
  try { return decodeURIComponent(h); } catch { return h; }
}

// True when the type's dots huddle in one spot: the recorded point sits in
// the shared neuropil, not on each cell body (e.g. ORN_V in its glomerulus).
export function isCollapsed(typeSpan, brainDiag, n) {
  return n >= 20 && typeSpan / brainDiag < 0.12;
}
