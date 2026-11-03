/* Validation battery: renders battery.json. Read-only; no inventing. */
(function () {
  'use strict';
  var STATUS_WORDS = {
    'matches': 'matches real flies',
    'recorded': 'recorded',
    'checks-green': 'checks green',
    'preliminary-match': 'early match — weak test',
    'mismatch': 'mismatch — a discovery',
    'mismatch-predicted': 'expected mismatch — run it',
    'negative-result': 'negative result',
    'proposed': 'proposed — not run yet'
  };
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function verdictClass(v) {
    v = String(v || '');
    if (v.indexOf('SUPPORTED') === 0 && v.indexOf('NOT') !== 0) return 'v-SUPPORTED';
    if (v.indexOf('NOT') === 0) return 'v-NOT';
    if (v.indexOf("CAN'T") === 0) return 'v-CANT';
    return 'v-MIXED';
  }
  function card(e) {
    var h = '<div class="bcard" id="b-' + esc(e.id) + '">';
    h += '<h3>' + esc(e.id) + ' · ' + esc(e.title) +
      ' <span class="st st-' + esc(e.status) + '">' + esc(STATUS_WORDS[e.status] || e.status) + '</span></h3>';
    if (e.literature) h += '<p><span class="blab">Real flies: </span>' + esc(e.literature) + '</p>';
    h += '<p><span class="blab">We predicted: </span>' + esc(e.prediction) + '</p>';
    h += '<details><summary>How the sim does it (methods)</summary><p>' + esc(e.mechanism) + '</p>';
    if (e.notes) h += '<p>' + esc(e.notes) + '</p>';
    if (e.evidence_tests && e.evidence_tests.length)
      h += '<p>Checks: ' + e.evidence_tests.map(function (t) { return '<span class="mono">' + esc(t) + '</span>'; }).join(', ') + '</p>';
    h += '</details>';
    if (e.records && e.records.length) {
      h += '<div class="recs">' + e.records.map(function (r) {
        return '<span class="rec"><b class="' + verdictClass(r.verdict) + '">' + esc(r.verdict) + '</b> · ' +
          esc(r.date) + ' · <span class="mono">' + esc(r.weight_model ? r.weight_model + ' · rec ' + r.id : 'old model, before Nov 1') + '</span></span>';
      }).join('') + '</div>';
    }
    return h + '</div>';
  }
  fetch('battery.json?v=1').then(function (r) {
    if (!r.ok) throw new Error('battery.json missing');
    return r.json();
  }).then(function (b) {
    var real = [], mach = [];
    (b.entries || []).forEach(function (e) {
      ((e.section === 'machinery' ? mach : real)).push(e);
    });
    document.getElementById('gridReal').innerHTML = real.map(card).join('') || '<p class="note">None yet.</p>';
    document.getElementById('gridMach').innerHTML = mach.map(card).join('') || '<p class="note">None yet.</p>';
    document.getElementById('counts').textContent =
      real.length + ' real-fly entries · ' + mach.length + ' machinery proofs · ' +
      (b.record_count != null ? b.record_count + ' notebook records searched' : '');
    if (b.generated) document.getElementById('gen').textContent = b.generated;
  }).catch(function (err) {
    document.getElementById('counts').textContent = 'Could not load battery.json: ' + err.message;
  });
})();
