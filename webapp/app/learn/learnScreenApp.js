// "শেখা" (Learn) screen logic -- the live hardware teaching session: pick a
// letter (in order, or a specific one), the ESP32 plays its audio and
// vibrates the pattern, the student answers on the physical device, and the
// result streams back here.
//
// This used to live inside the teacher panel's "শেখানো" tab
// (webapp/app/teacher/teacherApp.js). It was split out into its own
// top-level page because it is a different feature from "পরীক্ষা" (which
// tests a student on letters already taught), not a sub-mode of the same
// screen -- each nav item now does exactly one thing.

import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@/lib/config';
import { LETTERS as RAW_LETTERS } from '@/lib/brailleMap';

const LETTERS = RAW_LETTERS.map((l) => ({
  ...l,
  name: `${l.char} (${l.category === 'vowel' ? 'স্বরবর্ণ' : l.cells ? 'দুই-কোষ' : 'ব্যঞ্জনবর্ণ'})`,
  prefix: l.cells ? l.cells[0] : undefined,
}));

const TEACHING   = ['আবার চেষ্টা করো', 'হিন্ট দেখুন', 'সঠিক — এগিয়ে যান'];
const CONFIDENCE = ['আত্মবিশ্বাসী', 'দ্বিধাগ্রস্ত', 'অনুমান করছে'];

export function startLearnScreenApp() {
  const el = (id) => document.getElementById(id);

  const S = {
    learnMode: 'seq',
    seqIdx: 0,
    autoAdvance: false,
    rndSelected: null,
    rndFilter: 'all',
    sessionStart: null,
    lastAttemptId: null,
    pollTimer: null,
    studentId: (typeof window !== 'undefined' && window.localStorage.getItem('teacher_student_id')) || 'S01',
    deviceId: 'esp32_01',
    weaknesses: {},
  };

  const cleanupFns = [];
  const on = (elOrId, ev, fn) => {
    const target = typeof elOrId === 'string' ? el(elOrId) : elOrId;
    if (!target) return;
    target.addEventListener(ev, fn);
    cleanupFns.push(() => target.removeEventListener(ev, fn));
  };

  // ─── Supabase helpers ───────────────────────────────────────────────────
  const HDR = () => ({
    apikey: SUPABASE_ANON_KEY,
    Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    'Content-Type': 'application/json',
  });

  async function sbGet(table, params = {}) {
    const url = new URL(`${SUPABASE_URL}/rest/v1/${table}`);
    for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
    try { const r = await fetch(url, { headers: HDR() }); return r.ok ? r.json() : []; }
    catch { return []; }
  }

  async function sbPost(table, body) {
    return fetch(`${SUPABASE_URL}/rest/v1/${table}`, {
      method: 'POST',
      headers: { ...HDR(), Prefer: 'return=minimal' },
      body: JSON.stringify(body),
    }).catch(() => null);
  }

  // ─── Polling ────────────────────────────────────────────────────────────
  // The badge only ever said "সংযুক্ত" (connected) because loading this page
  // started a database poll -- that proves nothing about whether an ESP32 is
  // actually out there. It now starts as "খুঁজছে..." (searching) and only
  // flips to connected once a genuinely new attempt row (created after this
  // session started) actually arrives -- real evidence the device is alive.
  let lastActiveTimestamp = 0;

  function startPoll() {
    S.sessionStart = new Date().toISOString();
    S.lastAttemptId = null;
    lastActiveTimestamp = 0;
    clearInterval(S.pollTimer);
    S.pollTimer = setInterval(pollAttempts, 200);
    cleanupFns.push(() => clearInterval(S.pollTimer));
    checkRecentActivity();
  }

  async function checkRecentActivity() {
    const recentWindow = new Date(Date.now() - 45 * 1000).toISOString();
    const rows = await sbGet('attempts', {
      select: 'id,created_at,user_id',
      device_id: `eq.${S.deviceId}`,
      created_at: `gt.${recentWindow}`,
      limit: '1',
    });
    if (rows.length) {
      lastActiveTimestamp = Date.now();
      setEspStatus('connected');
    } else {
      setEspStatus('searching');
    }
  }

  function stopPoll() { clearInterval(S.pollTimer); setEspStatus('idle'); }

  async function pollAttempts() {
    const rows = await sbGet('attempts', {
      select: 'id,char_id,is_correct,teaching_action,confidence_state,response_time,entered_pattern,expected_pattern,created_at',
      device_id: `eq.${S.deviceId}`,
      created_at: `gt.${S.sessionStart}`,
      order: 'created_at.desc',
      limit: '1',
    });
    if (rows.length && rows[0].id !== S.lastAttemptId) {
      S.lastAttemptId = rows[0].id;
      lastActiveTimestamp = Date.now();
      setEspStatus('connected');
      handleAttempt(rows[0]);
    } else if (lastActiveTimestamp > 0 && Date.now() - lastActiveTimestamp > 60000) {
      setEspStatus('searching');
    }
  }

  async function sendPlay(letterId) {
    await sbPost('remote_commands', {
      device_id: S.deviceId,
      student_id: S.studentId,
      letter_id: letterId,
      command: 'play',
      created_at: new Date().toISOString(),
    });
  }

  // ─── Student switching ──────────────────────────────────────────────────
  function setStudentId(id) {
    const clean = (id || '').trim();
    if (!clean || clean === S.studentId) return;
    S.studentId = clean;
    try { window.localStorage.setItem('teacher_student_id', clean); } catch {}
    updateStudentBadge();
    loadWeaknesses();
  }

  function updateStudentBadge() {
    const badge = el('student-id-label');
    if (badge) badge.textContent = S.studentId;
  }

  // ─── Attempt handler ────────────────────────────────────────────────────
  function handleAttempt(row) {
    const letter = S.learnMode === 'seq'
      ? LETTERS[S.seqIdx]
      : (S.rndSelected !== null ? LETTERS[S.rndSelected] : null);
    if (!letter || row.char_id !== letter.id) return;

    renderLearnResult(row, letter);

    if (row.is_correct && S.learnMode === 'seq') {
      showToast('✓ সঠিক উত্তর! পরবর্তী বর্ণে যাওয়া হচ্ছে...', 1800);
      setTimeout(seqNext, 1500);
    }
  }

  // ─── UI helpers ─────────────────────────────────────────────────────────
  function showToast(msg, duration = 2000) {
    const t = el('toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), duration);
  }

  function setEspStatus(state) {
    const badge = el('esp-badge');
    const dot = el('esp-dot');
    if (!badge || !dot) return;
    if (state === 'connected') {
      badge.classList.remove('off'); dot.classList.remove('off');
      el('esp-label').textContent = 'ESP32 সংযুক্ত';
    } else {
      badge.classList.add('off'); dot.classList.add('off');
      el('esp-label').textContent = 'ESP32 নিষ্ক্রিয়';
    }
  }

  function brailleCellHtml(dotMask, expectedMask = -1) {
    const order = [1, 4, 2, 5, 3, 6];
    return `<div class="braille-cell">${order.map((d) => {
      const bit = 1 << (d - 1);
      const on = Boolean(dotMask & bit);
      let cls = 'bdot';
      if (expectedMask >= 0) {
        const exp = Boolean(expectedMask & bit);
        if (on && exp) cls += ' correct';
        else if (!on && exp) cls += ' missing';
        else if (on && !exp) cls += ' extra';
      } else if (on) cls += ' on';
      return `<span class="${cls}" title="ডট ${d}"></span>`;
    }).join('')}</div>`;
  }

  function generateHint(entered, expected) {
    const missing = [], extra = [];
    for (let d = 0; d < 6; d++) {
      const bit = 1 << d;
      if ((expected & bit) && !(entered & bit)) missing.push(d + 1);
      if (!(expected & bit) && (entered & bit)) extra.push(d + 1);
    }
    const parts = [];
    if (missing.length) parts.push(`বাদ পড়েছে → ডট ${missing.join(', ')}`);
    if (extra.length) parts.push(`অতিরিক্ত → ডট ${extra.join(', ')}`);
    return parts.join('  |  ') || 'আবার চেষ্টা করো';
  }

  // ─── Student weaknesses (mastery dots on the random-mode grid) ─────────
  async function loadWeaknesses() {
    const rows = await sbGet('student_weaknesses', { student_id: `eq.${S.studentId}` });
    S.weaknesses = {};
    rows.forEach((r) => { S.weaknesses[r.char_id] = r; });
  }

  function getMasteryClass(charId) {
    const w = S.weaknesses[charId];
    if (!w) return 'none';
    const total = (w.wrong_count || 0) + (w.correct_count || 0);
    if (total === 0) return 'none';
    const rate = (w.correct_count || 0) / total;
    if (rate >= 0.8) return 'good';
    if (rate >= 0.5) return 'medium';
    return 'poor';
  }

  function wireCatTabs(tabsId, onSelect) {
    document.querySelectorAll(`#${tabsId} .cat-tab`).forEach((tab) => {
      tab.addEventListener('click', () => {
        document.querySelectorAll(`#${tabsId} .cat-tab`).forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        onSelect(tab.dataset.cat);
      });
    });
  }

  function renderLetterGrid(containerId, filter = 'all') {
    const container = el(containerId);
    const letters = filter === 'all' ? LETTERS : LETTERS.filter((l) => l.category === filter);

    container.innerHTML = letters.map((l) => {
      const mCls = getMasteryClass(l.id);
      return `<div class="lg-item" data-id="${l.id}">
        <div class="mastery-dot ${mCls}"></div>
        <div class="lg-char">${l.char}</div>
      </div>`;
    }).join('');

    container.querySelectorAll('.lg-item').forEach((item) => {
      item.addEventListener('click', () => {
        const id = +item.dataset.id;
        const letter = LETTERS[id];
        S.rndSelected = id;
        container.querySelectorAll('.lg-item').forEach((i) =>
          i.classList.toggle('selected', +i.dataset.id === id));
        el('rnd-char').textContent = letter.char;
        el('rnd-name').textContent = letter.name;
        el('rnd-label').textContent = `নির্বাচিত বর্ণ #${id + 1}`;
        el('rnd-dots').innerHTML = brailleCellHtml(letter.mask);
        if (letter.prefix) {
          el('rnd-prefix').textContent = `দুই-কোষ: প্রথমে ডট ${letter.prefix.join(',')} স্পন্দিত হবে`;
          el('rnd-prefix').classList.remove('hidden');
        } else {
          el('rnd-prefix').classList.add('hidden');
        }
        el('rnd-sel-card').classList.remove('hidden');
        el('rnd-result').classList.add('hidden');
        const matchEl = el('rnd-match-badge');
        if (matchEl) matchEl.classList.add('hidden');
        sendPlay(id);
        showToast(`'${letter.char}' পাঠদান শুরু হয়েছে (ESP32 শুনছে...)`);
      });
    });
  }

  // ─── Sequential mode ────────────────────────────────────────────────────
  function seqRender() {
    const letter = LETTERS[S.seqIdx];
    el('seq-char').textContent = letter.char;
    el('seq-name').textContent = letter.name;
    el('seq-label').textContent = `বর্ণমালা নম্বর ${S.seqIdx + 1}`;
    const pct = Math.round(((S.seqIdx + 1) / LETTERS.length) * 100);
    el('seq-progress').textContent = `অগ্রগতি: ${S.seqIdx + 1}/${LETTERS.length}`;
    el('seq-pct').textContent = `${pct}%`;
    el('seq-bar').style.width = `${pct}%`;
    el('seq-dots').innerHTML = brailleCellHtml(letter.mask);

    if (letter.prefix) {
      el('seq-prefix').textContent = `দুই-কোষ: প্রথমে ডট ${letter.prefix.join(',')} স্পন্দিত হবে`;
      el('seq-prefix').classList.remove('hidden');
    } else {
      el('seq-prefix').classList.add('hidden');
    }

    el('seq-result').classList.add('hidden');
    el('seq-match-badge').classList.add('hidden');
    el('hdr-sub').textContent = `ছাত্র: ${S.studentId} • ক্রমানুসারে • বর্ণ ${S.seqIdx + 1}/${LETTERS.length}`;
  }

  function seqNext() {
    if (S.seqIdx < LETTERS.length - 1) {
      S.seqIdx++;
      seqRender();
      sendPlay(LETTERS[S.seqIdx].id);
    } else {
      showToast('সব বর্ণ শেষ হয়েছে!');
    }
  }

  function seqPrev() {
    if (S.seqIdx > 0) { S.seqIdx--; seqRender(); }
  }

  function renderLearnResult(row, letter) {
    const ta = row.teaching_action ?? 2;
    const cs = row.confidence_state ?? 1;
    const ok = row.is_correct;
    const ep = row.expected_pattern ?? letter.mask;
    const inp = row.entered_pattern ?? 0;

    const isSeq = S.learnMode === 'seq';
    const prefix = isSeq ? 'seq' : 'rnd';
    const resultEl = el(prefix + '-result');
    resultEl.classList.remove('hidden');

    const actionEl = el(prefix + '-action');
    actionEl.textContent = TEACHING[ta];
    actionEl.className = 'action-badge ' + ['repeat', 'hint', 'correct'][ta];

    el(prefix + '-conf').textContent = CONFIDENCE[cs];

    const hintEl = el(prefix + '-hint');
    hintEl.textContent = ok ? '✓ সঠিক উত্তর' : generateHint(inp, ep);
    hintEl.classList.remove('hidden');
    hintEl.style.color = ok ? 'var(--green-dark)' : 'var(--amber)';

    const matchEl = el(prefix + '-match-badge');
    if (matchEl) {
      if (ok) {
        matchEl.textContent = '✓ সঠিক উত্তর (ESP32)';
        matchEl.className = 'badge green';
        matchEl.classList.remove('hidden');
      } else {
        matchEl.textContent = '✕ ভুল উত্তর (আবার চেষ্টা করুন)';
        matchEl.className = 'badge amber';
        matchEl.classList.remove('hidden');
      }
    }

    const cmpEl = el(prefix + '-dots-cmp');
    cmpEl.classList.remove('hidden');
    el(prefix + '-dots-ent').innerHTML = brailleCellHtml(inp, ep);
    el(prefix + '-dots-exp').innerHTML = brailleCellHtml(ep);
  }

  // ─── Random mode ────────────────────────────────────────────────────────
  function rndInit() {
    renderLetterGrid('rnd-grid', S.rndFilter);
  }

  // ─── Mode switching (sequential <-> random, both inside "শেখা") ────────
  function setLearnMode(lm) {
    S.learnMode = lm;
    el('tp-seq').classList.toggle('active', lm === 'seq');
    el('tp-rnd').classList.toggle('active', lm === 'rnd');
    if (lm === 'seq') {
      el('panel-seq').classList.remove('hidden');
      el('panel-rnd').classList.add('hidden');
      seqRender();
      sendPlay(LETTERS[S.seqIdx].id);
    } else {
      el('panel-seq').classList.add('hidden');
      el('panel-rnd').classList.remove('hidden');
      rndInit();
      el('hdr-sub').textContent = `ছাত্র: ${S.studentId} • এলোমেলো মোড`;
    }
  }

  function handleBack() {
    const base = process.env.NEXT_PUBLIC_BASE_PATH || '';
    window.location.href = base ? `${base}/` : '/';
  }

  // ─── Init ───────────────────────────────────────────────────────────────
  on('btn-back', 'click', handleBack);

  on('tp-seq', 'click', () => setLearnMode('seq'));
  on('tp-rnd', 'click', () => setLearnMode('rnd'));

  on('btn-seq-prev', 'click', seqPrev);
  on('btn-seq-next', 'click', seqNext);
  on('btn-seq-teach', 'click', () => { sendPlay(LETTERS[S.seqIdx].id); showToast('পাঠদান শুরু হয়েছে'); });
  on('btn-seq-play', 'click', () => { sendPlay(LETTERS[S.seqIdx].id); });
  on('btn-seq-stop', 'click', () => { stopPoll(); showToast('পাঠদান থামানো হয়েছে'); });
  on('btn-seq-auto', 'click', () => {
    S.autoAdvance = !S.autoAdvance;
    el('btn-seq-auto').textContent = S.autoAdvance ? '⚡ অটো চালু' : '⚡ অটো';
    el('btn-seq-auto').className = S.autoAdvance ? 'btn primary' : 'btn outline';
  });

  on('btn-rnd-play', 'click', () => {
    if (S.rndSelected !== null) sendPlay(S.rndSelected);
  });

  wireCatTabs('rnd-cat-tabs', (cat) => {
    S.rndFilter = cat;
    renderLetterGrid('rnd-grid', cat);
  });

  on('btn-change-student', 'click', () => {
    const next = window.prompt('ছাত্রের কোড লিখুন (যেমন P01):', S.studentId);
    if (next) setStudentId(next);
  });

  updateStudentBadge();
  loadWeaknesses();
  seqRender();
  startPoll();

  return () => { cleanupFns.forEach((fn) => fn()); };
}
