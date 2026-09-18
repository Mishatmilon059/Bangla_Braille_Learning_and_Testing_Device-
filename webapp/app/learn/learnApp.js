// Practice-session driver for the /learn page.
//
// Ported from web/app.js. Deliberately kept close to the original's
// imperative, getElementById-driven style rather than rewritten as
// prop/state-driven React -- this is the timing- and scoring-critical path
// (response_time, press_duration, the exact feature-sampling order) that
// must keep matching the ESP32 firmware and the generated rule engine
// exactly. Re-deriving the same behavior through render-driven state would
// be higher risk for no behavioral benefit. Runs once, from a useEffect in
// page.tsx, against the JSX-rendered DOM (same element ids as web/index.html).

import {
  SPEC_VERSION, TEACHING_ACTION, TEACHING_ACTION_NAMES,
  CONFIDENCE_STATE_NAMES,
  evaluateTeachingAction, evaluateConfidence,
  SESSION_TARGET_ATTEMPTS,
} from '@/lib/ruleEngine';
import { BrailleCell, KeyPad } from '@/lib/keypad';
import { dotsToMask, maskToDots, displayChar, LETTERS } from '@/lib/brailleMap';
import { LearnerState, AttemptLogger, deviceId, uuid } from '@/lib/storage';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@/lib/config';

const MAX_TRIES_PER_PROMPT = 4;
const PROFILE_KEY = 'braille.profile';

export function loadProfile() {
  try { return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null'); } catch { return null; }
}

export function saveProfile(name, userId) {
  const p = { name: name.trim(), userId: userId.trim().toUpperCase(), createdAt: new Date().toISOString() };
  localStorage.setItem(PROFILE_KEY, JSON.stringify(p));
  return p;
}

function initials(name) {
  return name.trim().split(/\s+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase() || '?';
}

/**
 * Starts the whole practice app against the currently-mounted DOM. Returns a
 * cleanup function. Must only be called once per mount (page.tsx guards
 * this against React StrictMode's dev double-invoke).
 */
export function startLearnApp({ rerun }) {
  const $ = (id) => document.getElementById(id);

  const ui = {
    syncStatus: $('syncStatus'),
    setup: $('setup'), practice: $('practice'),
    mode: $('mode'), setLen: $('setLen'), charSet: $('charSet'),
    startBtn: $('startBtn'), exportBtn: $('exportBtn'), flushBtn: $('flushBtn'),
    resetBtn: $('resetBtn'), modeNote: $('modeNote'),
    attemptNo: $('attemptNo'), attemptTotal: $('attemptTotal'), diffLevel: $('diffLevel'),
    promptChar: $('promptChar'), promptName: $('promptName'),
    replayBtn: $('replayBtn'), submitBtn: $('submitBtn'), clearBtn: $('clearBtn'),
    hintBtn: $('hintBtn'), stopBtn: $('stopBtn'),
    hintBox: $('hintBox'), feedback: $('feedback'),
    stRows: $('stRows'), stAcc: $('stAcc'), stSess: $('stSess'), stDays: $('stDays'),
    stChars: $('stChars'), stQueue: $('stQueue'),
    taTable: $('taTable'), csTable: $('csTable'), charTable: $('charTable'),
  };

  const MODE_NOTES = {
    normal: 'দুর্বল অক্ষরের দিকে ঝোঁক বেশি — স্বাভাবিক ক্লাস বণ্টন তৈরি করে।',
    targeted: 'পুরনো ও দুর্বল অক্ষরের দিকে ইচ্ছাকৃত ঝোঁক, যাতে বিরল নিয়মগুলোও দেখা যায়। ফিচার ভ্যালু কখনো বানানো হয় না।',
    review: 'শুধু আগে দেখা অক্ষর যাদের mastery ০.৫-এর নিচে। পরের দিনের অনুশীলনের জন্য।',
  };

  const state = {
    letters: LETTERS, active: [],
    learner: null, logger: null, cell: null, pad: null,
    audio: new Map(),
    session: null, current: null, running: false,
  };

  const cleanupFns = [];
  const on = (el, ev, fn) => { el.addEventListener(ev, fn); cleanupFns.push(() => el.removeEventListener(ev, fn)); };

  function showUserBadge(profile) {
    const badge = $('userBadge');
    $('userAvatar').textContent = initials(profile.name);
    $('userName').textContent = profile.name;
    $('userIdDisplay').textContent = profile.userId;
    badge.classList.add('show');
  }

  async function checkSupabase() {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
      ui.syncStatus.className = 'sync-status';
      ui.syncStatus.textContent = 'offline (no backend configured)';
      return;
    }
    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/attempts?limit=0`, {
        headers: { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` },
      });
      if (res.ok || res.status === 406) {
        ui.syncStatus.className = 'sync-status ok';
        ui.syncStatus.textContent = 'Supabase connected';
      } else {
        ui.syncStatus.className = 'sync-status error';
        ui.syncStatus.textContent = `Supabase error ${res.status}`;
      }
    } catch {
      ui.syncStatus.className = 'sync-status error';
      ui.syncStatus.textContent = 'Supabase unreachable';
    }
  }

  async function loadLearner() {
    const id = loadProfile()?.userId || 'P01';
    state.learner = new LearnerState(id);
    if (state.logger && state.logger.configured) {
      await state.logger.syncRemoteForUser(id, state.learner);
      renderAll();
    }
  }

  function activeSet() {
    const which = ui.charSet.value;
    if (which === 'vowels') return state.letters.filter((l) => l.category === 'vowel');
    if (which === 'consonants') return state.letters.filter((l) => l.category === 'consonant');
    return state.letters;
  }

  function audioFor(track) {
    const key = String(track);
    if (!state.audio.has(key)) {
      const a = new Audio(`/audio/${String(track).padStart(4, '0')}.mp3`);
      a.preload = 'auto';
      state.audio.set(key, a);
    }
    return state.audio.get(key);
  }

  function playPrompt(startClock = true) {
    const letter = state.current?.letter;
    if (!letter) return;
    const a = audioFor(letter.id + 1);
    const begin = () => { if (startClock) state.current.promptEndMs = performance.now(); };
    a.onended = begin;
    a.onerror = begin;
    a.currentTime = 0;
    a.play().catch(begin);
    setTimeout(() => { if (startClock && state.current && state.current.promptEndMs === null) begin(); }, 4000);
  }

  function playCue(track) {
    const a = audioFor(track);
    a.currentTime = 0;
    a.play().catch(() => {});
  }

  function startSession() {
    loadLearner();
    state.active = activeSet();
    const total = Math.max(1, Number(ui.setLen.value) || SESSION_TARGET_ATTEMPTS);
    state.session = {
      id: uuid(),
      number: state.learner.startSession(),
      attemptIndex: 0,
      total,
      mode: ui.mode.value,
    };
    state.running = true;
    ui.practice.classList.add('show');
    ui.setup.querySelectorAll('input,select').forEach((el) => { el.disabled = true; });
    ui.startBtn.disabled = true;
    ui.attemptTotal.textContent = total;
    state.pad.enable();
    playCue(59);
    setTimeout(nextPrompt, 900);
  }

  function endSession(reason) {
    state.running = false;
    state.pad.disable();
    ui.practice.classList.remove('show');
    ui.setup.querySelectorAll('input,select').forEach((el) => { el.disabled = false; });
    ui.startBtn.disabled = false;
    state.current = null;
    if (reason !== 'stopped') playCue(60);
    state.logger.flush();
    renderAll();
  }

  function pickLetter(prevAction, prevLetter) {
    const seen = state.active.filter((l) => state.learner.char(l.id).seen > 0);

    if (prevAction === TEACHING_ACTION.REPEAT || prevAction === TEACHING_ACTION.HINT) {
      return prevLetter;
    }

    if (state.session.mode === 'review') {
      const weak = seen.filter((l) => state.learner.char(l.id).mastery < 0.5);
      if (weak.length) return weak[Math.floor(Math.random() * weak.length)];
    }

    if (state.session.mode === 'targeted') {
      const now = Date.now();
      const scored = state.active.map((l) => {
        const c = state.learner.char(l.id);
        const staleS = c.lastPracticeMs == null ? 0 : (now - c.lastPracticeMs) / 1000;
        const staleness = Math.min(1, staleS / 86400);
        const weakness = 1 - c.mastery;
        const wrongPressure = Math.min(1, c.wrongStreak / 3);
        return { l, score: weakness * 2 + staleness * 2 + wrongPressure * 3 + Math.random() * 0.5 };
      });
      scored.sort((a, b) => b.score - a.score);
      return scored[Math.floor(Math.random() * Math.min(5, scored.length))].l;
    }

    const weights = state.active.map((l) => 0.15 + (1 - state.learner.char(l.id).mastery));
    const total = weights.reduce((a, b) => a + b, 0);
    let r = Math.random() * total;
    for (let i = 0; i < state.active.length; i++) {
      r -= weights[i];
      if (r <= 0) return state.active[i];
    }
    return state.active[state.active.length - 1];
  }

  function nextPrompt(prevAction = null, prevLetter = null) {
    if (!state.running) return;
    if (state.session.attemptIndex >= state.session.total) return endSession('complete');

    const letter = pickLetter(prevAction, prevLetter);
    state.current = { letter, promptEndMs: null, tries: 0, hints: 0 };

    state.cell.clear();
    state.pad.reset();
    if (state.pad.clearHint) state.pad.clearHint();
    ui.hintBox.classList.remove('show');
    ui.feedback.classList.remove('show');
    ui.promptChar.textContent = displayChar(letter.char);
    ui.promptChar.classList.remove('prompt-hidden');
    ui.promptName.textContent = `${letter.name} — যে ডট শুনছেন তা লিখুন`;
    ui.attemptNo.textContent = state.session.attemptIndex + 1;
    ui.diffLevel.textContent = state.learner.data.difficulty;
    playPrompt(true);
  }

  function clearEntry() {
    state.pad.reset();
    state.cell.clear();
    if (state.current && state.current.hints > 0) {
      const dots = state.current.letter.dots || [];
      state.cell.showHint(dots);
      if (state.pad.showHint) state.pad.showHint(dots);
    }
  }

  function showHint() {
    if (!state.running || !state.current) return;
    state.current.hints += 1;
    const letter = state.current.letter;
    const dots = letter.dots || [];

    state.cell.showHint(dots);
    if (state.pad && state.pad.showHint) state.pad.showHint(dots);

    if (letter.cells && letter.cells.length === 2) {
      const [pre, main] = letter.cells;
      ui.hintBox.innerHTML =
        `<b>💡 ইঙ্গিত (Hint):</b> ২-সেল ব্রেইল — প্রথমে প্রিফিক্স ডট <b>${pre.join(',')}</b> (ডিভাইস ভাইব্রেট করবে), এরপর সঠিক ডট: ` +
        main.map((d) => `<span class="pill ok" style="font-weight:700">ডট ${d}</span>`).join(' ');
    } else {
      ui.hintBox.innerHTML =
        `<b>💡 ইঙ্গিত (Hint):</b> সঠিক ডট হলো — ` +
        dots.map((d) => `<span class="pill ok" style="font-weight:700">ডট ${d}</span>`).join(' ');
    }
    ui.hintBox.classList.add('show');
    playCue(54);
  }

  function submit() {
    if (!state.running || !state.current) return;
    const cur = state.current;
    const letter = cur.letter;
    const now = performance.now();
    const nowMs = Date.now();

    const enteredMask = state.pad.mask;
    if (enteredMask === 0 && state.pad.firstPressMs === null) return;

    const expectedMask = dotsToMask(letter.dots);
    const correct = enteredMask === expectedMask;

    const c = state.learner.char(letter.id);
    const pre = {
      prev_accuracy: state.learner.accuracy(letter.id),
      prev_mastery: c.mastery,
      prev_mistakes: c.mistakes,
      prev_confidence: c.lastConfidence,
      time_since_last_practice: state.learner.timeSinceLastPractice(letter.id, nowMs),
    };

    const promptEnd = cur.promptEndMs === null ? now : cur.promptEndMs;
    const responseTime = Math.max(0, now - promptEnd);

    const confidencePlaceholder = c.lastConfidence;
    state.learner.applyOutcome(letter.id, correct, confidencePlaceholder, nowMs);
    const after = state.learner.char(letter.id);

    const f = {
      char_id: letter.id,
      response_time: responseTime,
      press_duration: state.pad.meanPressDuration(now),
      retry_count: cur.tries,
      prev_accuracy: pre.prev_accuracy,
      prev_mastery: pre.prev_mastery,
      hint_count: cur.hints,
      session_number: state.session.number,
      difficulty_level: state.learner.data.difficulty,
      time_since_last_practice: pre.time_since_last_practice,
      prev_confidence: pre.prev_confidence,
      current_streak: after.streak,
      wrong_streak: after.wrongStreak,
      prev_mistakes: pre.prev_mistakes,
    };

    const confidence = evaluateConfidence(f);
    const action = evaluateTeachingAction(f);

    after.lastConfidence = confidence;
    state.learner.save();

    state.logger.log({
      created_at: new Date().toISOString(),
      user_id: state.learner.userId,
      session_id: state.session.id,
      device_id: deviceId(),
      attempt_index: state.session.attemptIndex,
      ...f,
      teaching_action: action,
      confidence_state: confidence,
      expected_pattern: expectedMask,
      entered_pattern: enteredMask,
      is_correct: correct,
      press_order: JSON.stringify(state.pad.pressOrder),
      source: 'web',
      is_synthetic: false,
      spec_version: SPEC_VERSION,
      braille_map_verified: Boolean(letter.verified),
    });

    showFeedback(correct, action, confidence, expectedMask, enteredMask);
    state.session.attemptIndex += 1;
    cur.tries += 1;
    renderAll();

    const retryThisPrompt = !correct && cur.tries < MAX_TRIES_PER_PROMPT &&
      (action === TEACHING_ACTION.REPEAT || action === TEACHING_ACTION.HINT);

    setTimeout(() => {
      if (!state.running) return;
      if (state.session.attemptIndex >= state.session.total) return endSession('complete');
      if (retryThisPrompt) {
        state.pad.reset();
        state.cell.clear();
        if (action === TEACHING_ACTION.HINT) showHint();
        cur.promptEndMs = performance.now();
        ui.attemptNo.textContent = state.session.attemptIndex + 1;
        ui.feedback.classList.remove('show');
      } else {
        nextPrompt(action, letter);
      }
    }, correct ? 1100 : 1800);
  }

  function showFeedback(correct, action, confidence, expectedMask, enteredMask) {
    state.cell.showComparison(expectedMask, enteredMask);
    ui.feedback.className = 'feedback show ' + (correct ? 'ok' : 'bad');
    const want = maskToDots(expectedMask).join(',') || '—';
    const got = maskToDots(enteredMask).join(',') || '—';
    ui.feedback.innerHTML = correct
      ? `<b>সঠিক — correct.</b> dots ${want}` +
        `<span class="act">action: ${TEACHING_ACTION_NAMES[action]} · confidence: ${CONFIDENCE_STATE_NAMES[confidence]}</span>`
      : `<b>ভুল — expected dots ${want}, got ${got}</b>` +
        `<span class="act">action: ${TEACHING_ACTION_NAMES[action]} · confidence: ${CONFIDENCE_STATE_NAMES[confidence]}</span>`;
    playCue(correct ? 51 : 52);
  }

  function barClass(v) { return v < 0.34 ? 'low' : v < 0.67 ? 'mid' : 'good'; }

  function renderAll() {
    const s = state.learner.summary();
    ui.stRows.textContent = state.logger.rowCount;
    ui.stAcc.textContent = s.accuracy === null ? '—' : (s.accuracy * 100).toFixed(0) + '%';
    ui.stSess.textContent = s.sessions;
    ui.stDays.textContent = Math.max(s.days, state.logger.distinctDays());
    ui.stChars.textContent = s.charsSeen;
    ui.stQueue.textContent = state.logger.queueLength;

    renderClassTable(ui.taTable, TEACHING_ACTION_NAMES,
      state.logger.classCounts('teaching_action', TEACHING_ACTION_NAMES.length));
    renderClassTable(ui.csTable, CONFIDENCE_STATE_NAMES,
      state.logger.classCounts('confidence_state', CONFIDENCE_STATE_NAMES.length));
    renderCharTable();
  }

  function renderClassTable(table, names, counts) {
    const tbody = table.querySelector('tbody');
    const max = Math.max(30, ...counts);
    tbody.innerHTML = names.map((n, i) => {
      const v = counts[i];
      const pill = v >= 30 ? 'ok' : v > 0 ? 'warn' : 'bad';
      return `<tr>
        <td>${n}</td>
        <td class="num"><span class="pill ${pill}">${v}</span></td>
        <td><div class="bar"><i class="${v >= 30 ? 'good' : v > 0 ? 'mid' : 'low'}"
             style="width:${Math.min(100, (v / max) * 100)}%"></i></div></td>
      </tr>`;
    }).join('');
  }

  function renderCharTable() {
    const tbody = ui.charTable.querySelector('tbody');
    const rows = state.letters
      .map((l) => ({ l, c: state.learner.char(l.id) }))
      .filter((x) => x.c.seen > 0)
      .sort((a, b) => a.c.mastery - b.c.mastery);

    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="color:var(--muted)">এই অংশগ্রহণকারীর জন্য এখনো কোনো attempt নেই।</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(({ l, c }) => {
      const acc = c.seen ? c.correct / c.seen : 0;
      return `<tr>
        <td style="font-size:1.2rem">${displayChar(l.char)}</td>
        <td style="color:var(--muted)">${l.name}</td>
        <td class="num">${c.seen}</td>
        <td class="num">${(acc * 100).toFixed(0)}%</td>
        <td><div class="bar"><i class="${barClass(c.mastery)}" style="width:${(c.mastery * 100).toFixed(0)}%"></i></div></td>
        <td class="num">${c.streak > 0 ? '+' + c.streak : c.wrongStreak > 0 ? '-' + c.wrongStreak : '0'}</td>
        <td class="num">${c.mistakes}</td>
      </tr>`;
    }).join('');
  }

  // --- profile gate --------------------------------------------------------

  function wireProfileEvents(rerun) {
    const saveBtn = $('profileSaveBtn');
    const changeBtn = $('changeProfileBtn');

    on(saveBtn, 'click', () => {
      const name = ($('profileName').value || '').trim();
      const userId = ($('profileId').value || '').trim().toUpperCase();
      if (!name || !userId) {
        $('profileName').classList.toggle('error', !name);
        $('profileId').classList.toggle('error', !userId);
        return;
      }
      saveProfile(name, userId);
      $('profileScreen').classList.add('hidden');
      rerun();
    });
    ['profileName', 'profileId'].forEach((id) => {
      const el = $(id);
      if (el) on(el, 'keydown', (e) => { if (e.key === 'Enter') saveBtn.click(); });
    });

    if (changeBtn) {
      on(changeBtn, 'click', () => {
        const p = loadProfile();
        if (p) {
          $('profileName').value = p.name;
          $('profileId').value = p.userId;
        }
        $('profileScreen').classList.remove('hidden');
      });
    }
  }

  // --- boot --------------------------------------------------------------

  const profile = loadProfile();
  if (!profile) {
    $('profileScreen').classList.remove('hidden');
    wireProfileEvents(rerun);
    return () => { cleanupFns.forEach((fn) => fn()); };
  }

  $('profileScreen').classList.add('hidden');
  showUserBadge(profile);

  state.cell = new BrailleCell($('cell'));
  state.pad = new KeyPad(document.querySelector('.keys'), {
    onChange: (mask) => state.cell.setMask(mask, { pulse: true }),
  });
  cleanupFns.push(() => state.pad.destroy());

  state.logger = new AttemptLogger((kind, msg) => {
    ui.syncStatus.className = 'sync-status ' + (kind === 'ok' ? 'ok' : kind === 'error' ? 'error' : kind === 'pending' ? 'pending' : '');
    ui.syncStatus.textContent = msg;
    ui.syncStatus.title = kind === 'error' ? 'Click to retry' : '';
    ui.syncStatus.style.cursor = kind === 'error' ? 'pointer' : '';
  });
  on(ui.syncStatus, 'click', () => { if (state.logger) state.logger.retryNow(); });

  checkSupabase();

  ui.setLen.value = SESSION_TARGET_ATTEMPTS;
  loadLearner();

  on(ui.mode, 'change', () => { ui.modeNote.textContent = MODE_NOTES[ui.mode.value]; });
  ui.modeNote.textContent = MODE_NOTES[ui.mode.value];

  on(ui.startBtn, 'click', startSession);
  on(ui.stopBtn, 'click', () => endSession('stopped'));
  on(ui.submitBtn, 'click', submit);
  on(ui.clearBtn, 'click', clearEntry);
  on(ui.hintBtn, 'click', showHint);
  on(ui.replayBtn, 'click', () => playPrompt(false));
  on(ui.exportBtn, 'click', () => state.logger.downloadCSV());
  on(ui.flushBtn, 'click', () => state.logger.flush());
  on(ui.resetBtn, 'click', () => {
    const id = state.learner.userId;
    if (!confirm(`${id}-এর সংরক্ষিত সব অগ্রগতি রিসেট করবেন?\n\nলগ করা rows এবং offline queue মুছবে না — শুধু এই অংশগ্রহণকারীর mastery/streak ইতিহাস মুছে যাবে।`)) return;
    state.learner.reset();
    renderAll();
  });

  const keyHandler = (e) => {
    if (!state.running) return;
    if (e.key === 'Enter') { e.preventDefault(); submit(); }
    else if (e.key === 'Escape') { e.preventDefault(); clearEntry(); }
    else if (e.key.toLowerCase() === 'h') { e.preventDefault(); showHint(); }
  };
  addEventListener('keydown', keyHandler);
  cleanupFns.push(() => removeEventListener('keydown', keyHandler));

  wireProfileEvents(rerun);
  renderAll();

  return () => { cleanupFns.forEach((fn) => fn()); };
}
