// Teacher panel logic — exam/test flow only.
//
// This used to also contain the "শেখানো" (teaching) screen, but that runs a
// different feature (a live teaching session) from a different menu
// ("পরীক্ষা" tests a student on letters they've already been taught) and was
// moved to webapp/app/learn/learnScreenApp.js so each nav item does exactly
// one thing. This file keeps only the test-select -> test-run -> results
// flow.
//
// Same low-risk strategy as learnApp.js: reuse the exact tested
// getElementById-driven state machine rather than re-deriving it as
// idiomatic React state, wired up via a useEffect in page.tsx against
// JSX-rendered elements with matching ids.

import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@/lib/config';
import { LETTERS as RAW_LETTERS } from '@/lib/brailleMap';
import { updateMastery } from '@/lib/ruleEngine';

const LETTERS = RAW_LETTERS.map((l) => ({
  ...l,
  name: `${l.char} (${l.category === 'vowel' ? 'স্বরবর্ণ' : l.cells ? 'দুই-কোষ' : 'ব্যঞ্জনবর্ণ'})`,
  prefix: l.cells ? l.cells[0] : undefined,
}));

export function startTeacherApp() {
  const el = (id) => document.getElementById(id);

  const S = {
    screen: 'test-select',
    testFilter: 'all',
    testSelected: new Set(),
    testQueue: [],
    testQIdx: 0,
    testResults: [],
    testStartTime: null,
    sessionStart: null,
    lastAttemptId: null,
    pollTimer: null,
    studentId: (typeof window !== 'undefined' && window.localStorage.getItem('teacher_student_id')) || 'S01',
    deviceId: 'esp32_01',
    weaknesses: {},
    resTab: 'correct',
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

  async function sbUpsert(table, body, onConflict) {
    return fetch(`${SUPABASE_URL}/rest/v1/${table}?on_conflict=${onConflict}`, {
      method: 'POST',
      headers: { ...HDR(), Prefer: 'resolution=merge-duplicates,return=minimal' },
      body: JSON.stringify(body),
    }).catch(() => null);
  }

  // ─── Polling ────────────────────────────────────────────────────────────
  // Same honesty fix as learnScreenApp.js: starting a DB poll proves nothing
  // about a real ESP32 being present, so the badge starts as "খুঁজছে..." and
  // only flips to connected once a genuinely new attempt row actually arrives.
  function startPoll() {
    S.sessionStart = new Date().toISOString();
    S.lastAttemptId = null;
    clearInterval(S.pollTimer);
    S.pollTimer = setInterval(pollAttempts, 200);
    cleanupFns.push(() => clearInterval(S.pollTimer));
    checkRecentActivity();
  }

  async function checkRecentActivity() {
    const thirtyMinsAgo = new Date(Date.now() - 30 * 60 * 1000).toISOString();
    const rows = await sbGet('attempts', {
      select: 'id,created_at',
      device_id: `eq.${S.deviceId}`,
      created_at: `gt.${thirtyMinsAgo}`,
      limit: '1',
    });
    if (rows.length) {
      setEspStatus('connected');
    }
  }

  function stopPoll() { clearInterval(S.pollTimer); setEspStatus('idle'); }

  async function pollAttempts() {
    const rows = await sbGet('attempts', {
      select: 'id,char_id,is_correct,teaching_action,confidence_state,response_time,entered_pattern,expected_pattern,created_at',
      user_id: `eq.${S.studentId}`,
      created_at: `gt.${S.sessionStart}`,
      order: 'created_at.desc',
      limit: '1',
    });
    if (rows.length && rows[0].id !== S.lastAttemptId) {
      S.lastAttemptId = rows[0].id;
      setEspStatus('connected');
      handleAttempt(rows[0]);
    }
  }

  async function sendPlay(letterId, isTest = false, testIndex = null, testTotal = null) {
    const body = {
      device_id: S.deviceId,
      student_id: S.studentId,
      letter_id: letterId,
      command: isTest ? 'test' : 'play',
      created_at: new Date().toISOString(),
    };
    if (isTest) { body.test_index = testIndex; body.test_total = testTotal; }
    await sbPost('remote_commands', body);
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
    if (S.screen !== 'test-run') return;
    const expected = S.testQueue[S.testQIdx];
    if (!expected || row.char_id !== expected.id) return;

    S.testResults.push({
      letter: expected,
      is_correct: row.is_correct,
      response_time: row.response_time ?? 0,
      entered_pattern: row.entered_pattern ?? 0,
      expected_pattern: row.expected_pattern ?? expected.mask,
    });

    if (S.testQIdx + 1 >= S.testQueue.length) {
      setTimeout(testShowResults, 800);
    } else {
      S.testQIdx++;
      sendPlay(S.testQueue[S.testQIdx].id, true, S.testQIdx, S.testQueue.length);
      renderTestQuestion();
    }
  }

  // ─── UI helpers ─────────────────────────────────────────────────────────
  function showToast(msg, duration = 2000) {
    const t = el('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), duration);
  }

  function setEspStatus(state) {
    const badge = el('esp-badge');
    const dot = el('esp-dot');
    if (state === 'connected') {
      badge.classList.remove('off'); dot.classList.remove('off');
      el('esp-label').textContent = 'ESP32 সংযুক্ত';
    } else {
      badge.classList.add('off'); dot.classList.add('off');
      el('esp-label').textContent = 'ESP32 নিষ্ক্রিয়';
    }
  }

  function showScreen(name) {
    S.screen = name;
    document.querySelectorAll('.teacher-app .screen').forEach((s) => s.classList.remove('active'));
    const target = el('screen-' + name);
    if (target) target.classList.add('active');

    const titles = {
      'test-select': 'বর্ণ নির্বাচন',
      'test-run': 'পরীক্ষা চলছে',
      results: 'ফলাফল ও মূল্যায়ন',
    };
    el('hdr-title').textContent = titles[name] || 'পরীক্ষা';
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

  function classifyError(row) {
    const rt = row.response_time ?? 0;
    if (rt > 6000) return { type: 'time', label: 'সময় বেশি লেগেছে' };
    const entered = row.entered_pattern ?? 0;
    const expected = row.expected_pattern ?? 0;
    if (entered !== expected) return { type: 'dots', label: 'ভুল ডট প্রেস' };
    return { type: 'retry', label: 'বারবার ভুল চেষ্টা' };
  }

  // ─── Student weaknesses ─────────────────────────────────────────────────
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

  // ─── Letter grid renderer (test-select only, in this file) ─────────────
  function renderLetterGrid(containerId, filter = 'all') {
    const container = el(containerId);
    const letters = filter === 'all' ? LETTERS : LETTERS.filter((l) => l.category === filter);

    container.innerHTML = letters.map((l) => {
      const sel = S.testSelected.has(l.id) ? 'selected' : '';
      const mCls = getMasteryClass(l.id);
      return `<div class="lg-item ${sel}" data-id="${l.id}">
        <div class="mastery-dot ${mCls}"></div>
        <div class="lg-char">${l.char}</div>
      </div>`;
    }).join('');

    container.querySelectorAll('.lg-item').forEach((item) => {
      item.addEventListener('click', () => {
        const id = +item.dataset.id;
        const letter = LETTERS[id];
        if (S.testSelected.has(id)) S.testSelected.delete(id);
        else S.testSelected.add(id);
        item.classList.toggle('selected', S.testSelected.has(id));
        updateTestSelCount();
        if (S.testSelected.size > 0) {
          el('test-sel-char').textContent = letter.char;
          el('test-sel-name').textContent = letter.name;
          el('test-sel-preview').classList.remove('hidden');
        } else {
          el('test-sel-preview').classList.add('hidden');
        }
      });
    });
  }

  function updateTestSelCount() {
    const n = S.testSelected.size;
    el('test-sel-count').textContent = `${n} টি বর্ণ নির্বাচিত`;
    const btn = el('btn-test-start');
    if (n > 0) btn.classList.remove('disabled');
    else btn.classList.add('disabled');
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

  // ─── Test mode ──────────────────────────────────────────────────────────
  function testInit() {
    S.testSelected = new Set();
    S.testResults = [];
    S.testQIdx = 0;
    el('test-sel-preview').classList.add('hidden');
    el('btn-test-start').classList.add('disabled');
    el('test-sel-count').textContent = '০ টি বর্ণ নির্বাচিত';
    renderLetterGrid('test-sel-grid', S.testFilter);
    showScreen('test-select');
  }

  function testStart() {
    if (S.testSelected.size === 0) return;
    S.testQIdx = 0;
    S.testResults = [];
    S.testStartTime = Date.now();
    S.testQueue = [...S.testSelected].map((id) => LETTERS[id]).sort(() => Math.random() - 0.5);

    showScreen('test-run');
    sendPlay(S.testQueue[0].id, true, 0, S.testQueue.length);
    renderTestQuestion();
  }

  function renderTestQuestion() {
    const letter = S.testQueue[S.testQIdx];
    const total = S.testQueue.length;
    const pct = Math.round(((S.testQIdx + 1) / total) * 100);
    el('test-q-num').textContent = `প্রশ্ন ${S.testQIdx + 1} / ${total}`;
    el('test-q-pct').textContent = `${pct}%`;
    el('test-q-bar').style.width = `${pct}%`;
    el('test-q-char').textContent = letter.char;
    el('test-q-name').textContent = letter.name;
  }

  function testShowResults() {
    const elapsed = Math.round((Date.now() - (S.testStartTime ?? Date.now())) / 1000);
    const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const ss = String(elapsed % 60).padStart(2, '0');

    const correct = S.testResults.filter((r) => r.is_correct);
    const wrong = S.testResults.filter((r) => !r.is_correct);
    const total = S.testResults.length;
    const pct = total ? Math.round((correct.length / total) * 100) : 0;

    const avgMs = total
      ? Math.round(S.testResults.reduce((s, r) => s + r.response_time, 0) / total)
      : 0;

    const circumference = 314.16;
    const offset = circumference * (1 - pct / 100);
    el('score-arc').setAttribute('stroke-dashoffset', offset.toFixed(2));
    el('res-pct').textContent = `${pct}%`;
    el('res-fraction').textContent = `${correct.length}/${total} সঠিক`;
    el('res-perf').style.width = `${pct}%`;

    el('res-time').textContent = `${mm}:${ss}`;
    el('res-speed').textContent = avgMs > 0 ? `${(avgMs / 1000).toFixed(1)}s` : '—';
    el('res-correct').textContent = correct.length;
    el('res-wrong').textContent = wrong.length;
    el('ans-cnt-c').textContent = correct.length;
    el('ans-cnt-w').textContent = wrong.length;

    el('res-correct-list').innerHTML = correct.length
      ? correct.map((r) => `<div class="correct-chip"><span>${r.letter.char}</span><span class="ck">✓</span></div>`).join('')
      : '<span class="text-xs">কোনোটি সঠিক হয়নি</span>';

    el('res-wrong-list').innerHTML = wrong.length
      ? wrong.map((r) => {
          const err = classifyError(r);
          return `<div class="wrong-item">
            <div class="wrong-char">${r.letter.char}</div>
            <div class="wrong-detail">
              <div class="wrong-reason">${r.letter.name}</div>
              <span class="err-tag ${err.type}">${err.label}</span>
            </div>
          </div>`;
        }).join('')
      : '<span class="text-xs">কোনো ভুল নেই!</span>';

    resTab('correct');
    showScreen('results');
    testSave();
  }

  async function testSave() {
    const results = S.testResults.map((r) => ({
      char_id: r.letter.id, is_correct: r.is_correct, response_time: r.response_time,
    }));
    await sbPost('test_sessions', {
      student_id: S.studentId, teacher_id: S.deviceId,
      letter_ids: S.testResults.map((r) => r.letter.id),
      results, total: S.testResults.length,
      correct: S.testResults.filter((r) => r.is_correct).length,
      wrong: S.testResults.filter((r) => !r.is_correct).length,
    });
    // Accumulate onto whatever this student's row already holds -- the same
    // (student_id, char_id) row is also written by the ESP32's personalization
    // path (see firmware/t12_ml_complete's save_student_weakness()), so
    // overwriting wrong_count/correct_count with a flat 0/1 here would erase
    // that history every time a test runs. mastery/streaks are updated with
    // the exact same EMA formula the firmware and web/rule_engine.js use, so
    // a test result affects "mastery" the same way a learning attempt does.
    for (const r of S.testResults) {
      const prev = S.weaknesses[r.letter.id] || {
        correct_count: 0, wrong_count: 0, mastery: 0, current_streak: 0, wrong_streak: 0,
      };
      await sbUpsert('student_weaknesses', {
        student_id: S.studentId, char_id: r.letter.id,
        correct_count: (prev.correct_count || 0) + (r.is_correct ? 1 : 0),
        wrong_count: (prev.wrong_count || 0) + (r.is_correct ? 0 : 1),
        mastery: updateMastery(prev.mastery || 0, r.is_correct ? 1 : 0),
        current_streak: r.is_correct ? (prev.current_streak || 0) + 1 : 0,
        wrong_streak: r.is_correct ? 0 : (prev.wrong_streak || 0) + 1,
        last_tested: new Date().toISOString(),
      }, 'student_id,char_id');
    }
    await loadWeaknesses();
  }

  function resTab(tab) {
    S.resTab = tab;
    el('ans-tab-c').classList.toggle('active', tab === 'correct');
    el('ans-tab-w').classList.toggle('active', tab === 'wrong');
    if (tab === 'correct') {
      el('ans-correct-panel').classList.remove('hidden');
      el('ans-wrong-panel').classList.add('hidden');
    } else {
      el('ans-correct-panel').classList.add('hidden');
      el('ans-wrong-panel').classList.remove('hidden');
    }
  }

  function handleBack() {
    if (S.screen === 'test-select') {
      const base = process.env.NEXT_PUBLIC_BASE_PATH || '';
      window.location.href = base ? `${base}/` : '/';
    } else if (S.screen === 'test-run') {
      if (confirm('পরীক্ষা বাতিল করবেন?')) showScreen('test-select');
    } else if (S.screen === 'results') {
      testInit();
    }
  }

  // ─── Init ───────────────────────────────────────────────────────────────
  on('btn-back', 'click', handleBack);

  wireCatTabs('test-cat-tabs', (cat) => {
    S.testFilter = cat;
    renderLetterGrid('test-sel-grid', cat);
  });

  on('btn-test-rnd-sel', 'click', () => {
    const filtered = S.testFilter === 'all' ? LETTERS : LETTERS.filter((l) => l.category === S.testFilter);
    const n = Math.min(10, filtered.length);
    const shuffled = filtered.sort(() => Math.random() - 0.5).slice(0, n);
    S.testSelected = new Set(shuffled.map((l) => l.id));
    renderLetterGrid('test-sel-grid', S.testFilter);
    updateTestSelCount();
    if (shuffled.length > 0) {
      const last = shuffled[shuffled.length - 1];
      el('test-sel-char').textContent = last.char;
      el('test-sel-name').textContent = last.name;
      el('test-sel-preview').classList.remove('hidden');
    }
    showToast(`${n}টি বর্ণ এলোমেলোভাবে নির্বাচিত`);
  });

  on('btn-test-clear', 'click', () => {
    S.testSelected.clear();
    renderLetterGrid('test-sel-grid', S.testFilter);
    updateTestSelCount();
    el('test-sel-preview').classList.add('hidden');
  });

  on('btn-test-start', 'click', testStart);
  on('btn-test-abort', 'click', () => {
    if (confirm('পরীক্ষা বাতিল করবেন?')) {
      stopPoll();
      testInit();
    }
  });

  on('ans-tab-c', 'click', () => resTab('correct'));
  on('ans-tab-w', 'click', () => resTab('wrong'));
  on('btn-res-retry', 'click', testInit);
  on('btn-res-home', 'click', testInit);

  on('btn-change-student', 'click', () => {
    const next = window.prompt('ছাত্রের কোড লিখুন (যেমন P01):', S.studentId);
    if (next) setStudentId(next);
  });

  updateStudentBadge();
  el('hdr-sub').textContent = `ছাত্র: ${S.studentId} • পরীক্ষা মোড`;
  loadWeaknesses();
  testInit();
  startPoll();

  return () => { cleanupFns.forEach((fn) => fn()); };
}
