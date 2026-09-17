// teacher.js — Teacher Panel Logic
// Imports credentials from config.js (never hardcode keys here)
import { SUPABASE_URL, SUPABASE_ANON_KEY } from './config.js';

// ─── Braille map (Bangladesh standard, all 50 verified letters) ───────────────
const LETTERS = [
  { id:0,  char:'অ',  name:'অ',              dots:[1],           category:'vowel' },
  { id:1,  char:'আ',  name:'আ',              dots:[3,4,5],       category:'vowel' },
  { id:2,  char:'ই',  name:'ই',              dots:[2,4],         category:'vowel' },
  { id:3,  char:'ঈ',  name:'ঈ',              dots:[3,5],         category:'vowel' },
  { id:4,  char:'উ',  name:'উ',              dots:[1,3,6],       category:'vowel' },
  { id:5,  char:'ঊ',  name:'ঊ',              dots:[1,2,5,6],     category:'vowel' },
  { id:6,  char:'ঋ',  name:'ঋ (দুই-কোষ)',  dots:[1,2,3,5],     category:'vowel',     prefix:[5] },
  { id:7,  char:'এ',  name:'এ',              dots:[1,5],         category:'vowel' },
  { id:8,  char:'ঐ',  name:'ঐ',              dots:[3,4],         category:'vowel' },
  { id:9,  char:'ও',  name:'ও',              dots:[1,3,5],       category:'vowel' },
  { id:10, char:'ঔ',  name:'ঔ',              dots:[2,4,6],       category:'vowel' },
  { id:11, char:'ক',  name:'ক',              dots:[1,3],         category:'consonant' },
  { id:12, char:'খ',  name:'খ',              dots:[1,3,4,6],     category:'consonant' },
  { id:13, char:'গ',  name:'গ',              dots:[1,2,4,5],     category:'consonant' },
  { id:14, char:'ঘ',  name:'ঘ',              dots:[1,2,6],       category:'consonant' },
  { id:15, char:'ঙ',  name:'ঙ',              dots:[3,4,6],       category:'consonant' },
  { id:16, char:'চ',  name:'চ',              dots:[1,4],         category:'consonant' },
  { id:17, char:'ছ',  name:'ছ',              dots:[1,6],         category:'consonant' },
  { id:18, char:'জ',  name:'জ',              dots:[2,4,5],       category:'consonant' },
  { id:19, char:'ঝ',  name:'ঝ',              dots:[1,3,5,6],     category:'consonant' },
  { id:20, char:'ঞ',  name:'ঞ',              dots:[2,5],         category:'consonant' },
  { id:21, char:'ট',  name:'ট',              dots:[2,3,4,5,6],   category:'consonant' },
  { id:22, char:'ঠ',  name:'ঠ',              dots:[2,4,5,6],     category:'consonant' },
  { id:23, char:'ড',  name:'ড',              dots:[1,2,4,6],     category:'consonant' },
  { id:24, char:'ঢ',  name:'ঢ',              dots:[1,2,3,4,5,6], category:'consonant' },
  { id:25, char:'ণ',  name:'ণ',              dots:[3,4,5,6],     category:'consonant' },
  { id:26, char:'ত',  name:'ত',              dots:[2,3,4,5],     category:'consonant' },
  { id:27, char:'থ',  name:'থ',              dots:[1,4,5,6],     category:'consonant' },
  { id:28, char:'দ',  name:'দ',              dots:[1,4,5],       category:'consonant' },
  { id:29, char:'ধ',  name:'ধ',              dots:[2,3,4,6],     category:'consonant' },
  { id:30, char:'ন',  name:'ন',              dots:[1,3,4,5],     category:'consonant' },
  { id:31, char:'প',  name:'প',              dots:[1,2,3,4],     category:'consonant' },
  { id:32, char:'ফ',  name:'ফ',              dots:[2,3,5],       category:'consonant' },
  { id:33, char:'ব',  name:'ব',              dots:[1,2],         category:'consonant' },
  { id:34, char:'ভ',  name:'ভ',              dots:[1,2,3,6],     category:'consonant' },
  { id:35, char:'ম',  name:'ম',              dots:[1,3,4],       category:'consonant' },
  { id:36, char:'য',  name:'য',              dots:[1,3,4,5,6],   category:'consonant' },
  { id:37, char:'র',  name:'র',              dots:[1,2,3,5],     category:'consonant' },
  { id:38, char:'ল',  name:'ল',              dots:[1,2,3],       category:'consonant' },
  { id:39, char:'শ',  name:'শ',              dots:[1,4,6],       category:'consonant' },
  { id:40, char:'ষ',  name:'ষ',              dots:[1,2,3,4,6],   category:'consonant' },
  { id:41, char:'স',  name:'স',              dots:[2,3,4],       category:'consonant' },
  { id:42, char:'হ',  name:'হ',              dots:[1,2,5],       category:'consonant' },
  { id:43, char:'ড়',  name:'ড়',              dots:[1,2,4,5,6],   category:'consonant' },
  { id:44, char:'ঢ়',  name:'ঢ়',              dots:[1,2,3,5,6],   category:'consonant' },
  { id:45, char:'য়',  name:'য়',              dots:[2,6],         category:'consonant' },
  { id:46, char:'ৎ',  name:'ৎ (দুই-কোষ)',  dots:[2,3,4,5],     category:'consonant', prefix:[5] },
  { id:47, char:'ং',  name:'ং (অনুস্বর)',    dots:[5,6],         category:'consonant' },
  { id:48, char:'ঃ',  name:'ঃ (বিসর্গ)',     dots:[6],           category:'consonant' },
  { id:49, char:'ঁ',  name:'ঁ (চন্দ্রবিন্দু)', dots:[3],        category:'consonant' },
];

function dotsToMask(dots) { return dots.reduce((m, d) => m | (1 << (d - 1)), 0); }
LETTERS.forEach(l => { l.mask = dotsToMask(l.dots); });

const TEACHING = ['আবার চেষ্টা করো', 'হিন্ট দেখুন', 'সঠিক — এগিয়ে যান'];
const CONFIDENCE = ['আত্মবিশ্বাসী', 'দ্বিধাগ্রস্ত', 'অনুমান করছে'];

// ─── Application state ────────────────────────────────────────────────────────
const S = {
  mode: 'learn',          // 'learn' | 'test'
  learnMode: 'seq',       // 'seq' | 'rnd'
  seqIdx: 0,
  autoAdvance: true,
  rndSelected: null,      // LETTERS index
  sessionStart: null,
  lastAttemptId: null,
  pollTimer: null,

  testPhase: 'select',    // 'select' | 'running' | 'done'
  testSelected: new Set(),
  testQueue: [],
  testQIdx: 0,
  testResults: [],
  studentId: 'S01',
  deviceId: 'esp32_01',

  // hardware simulator state
  simDots: new Set(),
};

// ─── Supabase helpers ─────────────────────────────────────────────────────────
const HDR = () => ({
  apikey: SUPABASE_ANON_KEY,
  Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
  'Content-Type': 'application/json',
});

async function sbGet(table, params = {}) {
  const url = new URL(`${SUPABASE_URL}/rest/v1/${table}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  try {
    const r = await fetch(url, { headers: HDR() });
    return r.ok ? r.json() : [];
  } catch { return []; }
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

// ─── Polling ─────────────────────────────────────────────────────────────────
function startPoll() {
  S.sessionStart = new Date().toISOString();
  S.lastAttemptId = null;
  clearInterval(S.pollTimer);
  S.pollTimer = setInterval(pollAttempts, 500);
  setStatus('connected');
}

function stopPoll() {
  clearInterval(S.pollTimer);
  setStatus('idle');
}

async function pollAttempts() {
  const rows = await sbGet('attempts', {
    select: 'id,char_id,is_correct,teaching_action,confidence_state,response_time,entered_pattern,expected_pattern,created_at',
    'created_at': `gt.${S.sessionStart}`,
    order: 'created_at.desc',
    limit: '1',
  });
  if (rows.length && rows[0].id !== S.lastAttemptId) {
    S.lastAttemptId = rows[0].id;
    handleAttempt(rows[0]);
  }
}

// ─── Command to ESP32 ─────────────────────────────────────────────────────────
async function sendPlay(letterId, isTest = false) {
  await sbPost('remote_commands', {
    device_id: S.deviceId,
    letter_id: letterId,
    command: isTest ? 'test' : 'play',
    created_at: new Date().toISOString(),
  });
}

// ─── Hint generation ─────────────────────────────────────────────────────────
function generateHint(entered, expected) {
  const missing = [], extra = [];
  for (let d = 0; d < 6; d++) {
    const bit = 1 << d;
    if ((expected & bit) && !(entered & bit)) missing.push(d + 1);
    if (!(expected & bit) && (entered & bit)) extra.push(d + 1);
  }
  const parts = [];
  if (missing.length) parts.push(`বাদ পড়েছে → ডট ${missing.join(', ')}`);
  if (extra.length)   parts.push(`অতিরিক্ত চেপেছে → ডট ${extra.join(', ')}`);
  return parts.join('  |  ') || 'আবার চেষ্টা করো';
}

// ─── Handle incoming attempt from Supabase ────────────────────────────────────
function handleAttempt(row) {
  renderResultPanel(row);

  if (S.mode === 'learn') {
    const currentLetter = S.learnMode === 'seq'
      ? LETTERS[S.seqIdx]
      : (S.rndSelected !== null ? LETTERS[S.rndSelected] : null);

    if (!currentLetter || row.char_id !== currentLetter.id) return;

    if (row.is_correct) {
      flashEl('result-panel', 'flash-green');
      if (S.learnMode === 'seq' && S.autoAdvance) {
        setTimeout(seqNext, 1200);
      } else if (S.learnMode === 'rnd') {
        el('rnd-correct-flash').classList.add('visible');
        setTimeout(() => el('rnd-correct-flash').classList.remove('visible'), 1400);
      }
    }
  } else if (S.mode === 'test' && S.testPhase === 'running') {
    const expected = S.testQueue[S.testQIdx];
    if (row.char_id !== expected.id) return;

    S.testResults.push({
      letter: expected,
      is_correct: row.is_correct,
      response_time: row.response_time,
    });

    if (S.testQIdx + 1 >= S.testQueue.length) {
      setTimeout(testShowResults, 800);
    } else {
      S.testQIdx++;
      const next = S.testQueue[S.testQIdx];
      sendPlay(next.id, true);
      renderTestQuestion();
    }
  }
}

// ─── UI helpers ───────────────────────────────────────────────────────────────
const el   = id => document.getElementById(id);
const show = id => { el(id).style.display = ''; };
const hide = id => { el(id).style.display = 'none'; };

function flashEl(id, cls) {
  el(id).classList.add(cls);
  setTimeout(() => el(id).classList.remove(cls), 1000);
}

function setStatus(state) {
  const dot = el('status-dot');
  dot.className = 'status-dot ' + state;
  el('status-text').textContent =
    state === 'connected' ? 'সংযুক্ত' : state === 'idle' ? 'নিষ্ক্রিয়' : 'সংযোগ বিচ্ছিন্ন';
}

// Braille cell HTML: 6 dots, colored by comparison if expectedMask given
function brailleCellHtml(dotMask, expectedMask = -1) {
  const order = [1, 4, 2, 5, 3, 6]; // grid reading order: left col top-to-bottom, then right col
  return `<div class="braille-cell">${order.map(d => {
    const bit = 1 << (d - 1);
    const on  = Boolean(dotMask & bit);
    let cls = 'bdot';
    if (expectedMask >= 0) {
      const exp = Boolean(expectedMask & bit);
      if (on  && exp)  cls += ' correct';
      else if (!on && exp)  cls += ' missing';
      else if (on  && !exp) cls += ' extra';
    } else {
      if (on) cls += ' on';
    }
    return `<span class="${cls}" title="ডট ${d}"></span>`;
  }).join('')}</div>`;
}

// ─── Result panel ─────────────────────────────────────────────────────────────
function renderResultPanel(row) {
  const panel = el('result-panel');
  panel.style.display = '';

  const ta  = row.teaching_action ?? 2;
  const cs  = row.confidence_state ?? 1;
  const ok  = row.is_correct;
  const ep  = row.expected_pattern ?? 0;
  const inp = row.entered_pattern  ?? 0;
  const rt  = row.response_time    ?? 0;

  const taColors = ['#FF9F0A', '#FF3B30', '#34C759'];
  const csColors = ['#34C759', '#FF9F0A', '#FF3B30'];

  el('result-action').textContent  = TEACHING[ta];
  el('result-action').style.color  = taColors[ta];
  el('result-conf').textContent    = CONFIDENCE[cs];
  el('result-conf').style.color    = csColors[cs];
  el('result-time').textContent    = `${Math.round(rt)} ms`;
  el('result-hint').textContent    = ok ? '✓ সঠিক উত্তর' : generateHint(inp, ep);
  el('result-hint').style.color    = ok ? '#34C759' : '#FF9F0A';
  el('result-dots-entered').innerHTML  = brailleCellHtml(inp, ep);
  el('result-dots-expected').innerHTML = brailleCellHtml(ep);
}

// ─── Sequential mode ──────────────────────────────────────────────────────────
function seqInit() {
  seqRender();
}

function seqSetLetter(idx) {
  S.seqIdx = Math.max(0, Math.min(LETTERS.length - 1, idx));
  seqRender();
}

function seqRender() {
  const letter = LETTERS[S.seqIdx];
  el('seq-char').textContent     = letter.char;
  el('seq-name').textContent     = letter.name;
  el('seq-progress').textContent = `বর্ণ ${S.seqIdx + 1} / ${LETTERS.length}`;
  el('seq-progress-bar').style.width = `${((S.seqIdx + 1) / LETTERS.length) * 100}%`;
  el('seq-dots').innerHTML       = brailleCellHtml(letter.mask);
  if (letter.prefix) {
    el('seq-prefix-note').textContent = `দুই-কোষ: প্রথমে ডট ${letter.prefix.join(',')} স্পন্দিত হবে`;
    el('seq-prefix-note').style.display = '';
  } else {
    el('seq-prefix-note').style.display = 'none';
  }
  hide('result-panel');
}

function seqNext() {
  if (S.seqIdx < LETTERS.length - 1) {
    seqSetLetter(S.seqIdx + 1);
    sendPlay(LETTERS[S.seqIdx].id);
  }
}

function seqPrev() {
  seqSetLetter(S.seqIdx - 1);
}

function seqPlay() {
  sendPlay(LETTERS[S.seqIdx].id);
}

// ─── Random mode ──────────────────────────────────────────────────────────────
function rndInit() {
  renderLetterGrid('rnd-grid', LETTERS, null, (letter) => {
    S.rndSelected = letter.id;
    el('rnd-char').textContent = letter.char;
    el('rnd-name').textContent = letter.name;
    el('rnd-dots').innerHTML   = brailleCellHtml(letter.mask);
    hide('result-panel');
    sendPlay(letter.id);
    // highlight selected
    document.querySelectorAll('#rnd-grid .letter-btn').forEach(b => {
      b.classList.toggle('selected', +b.dataset.id === letter.id);
    });
  });
  el('rnd-char').textContent = '—';
  el('rnd-name').textContent = 'একটি বর্ণ নির্বাচন করুন';
  el('rnd-dots').innerHTML   = '';
}

// ─── Test mode ────────────────────────────────────────────────────────────────
function testInit() {
  S.testPhase    = 'select';
  S.testSelected = new Set();
  S.testResults  = [];
  show('test-select'); hide('test-running'); hide('test-results');

  renderLetterGrid('test-select-grid', LETTERS, S.testSelected, (letter) => {
    if (S.testSelected.has(letter.id)) S.testSelected.delete(letter.id);
    else                               S.testSelected.add(letter.id);
    document.querySelectorAll('#test-select-grid .letter-btn').forEach(b => {
      b.classList.toggle('selected', S.testSelected.has(+b.dataset.id));
    });
    el('test-count').textContent = `${S.testSelected.size} টি বর্ণ নির্বাচিত`;
    el('test-btn-start').disabled = S.testSelected.size === 0;
  });
}

function testStart() {
  if (S.testSelected.size === 0) return;
  S.studentId = el('input-student').value.trim() || 'S01';
  S.testPhase = 'running';
  S.testQIdx  = 0;
  S.testResults = [];

  // Shuffle selected letters
  S.testQueue = [...S.testSelected].map(id => LETTERS[id]).sort(() => Math.random() - 0.5);

  hide('test-select'); show('test-running'); hide('test-results');
  sendPlay(S.testQueue[0].id, true); // true = test mode (no motors)
  renderTestQuestion();
}

function renderTestQuestion() {
  const letter = S.testQueue[S.testQIdx];
  const total  = S.testQueue.length;
  el('test-q-progress').textContent = `প্রশ্ন ${S.testQIdx + 1} / ${total}`;
  el('test-q-bar').style.width = `${((S.testQIdx + 1) / total) * 100}%`;
  el('test-q-char').textContent = letter.char;
  el('test-q-name').textContent = letter.name;
}

function testShowResults() {
  S.testPhase = 'done';
  hide('test-running'); show('test-results');

  const correct = S.testResults.filter(r => r.is_correct);
  const wrong   = S.testResults.filter(r => !r.is_correct);

  el('res-total').textContent   = S.testResults.length;
  el('res-correct').textContent = correct.length;
  el('res-wrong').textContent   = wrong.length;

  el('res-correct-list').innerHTML = correct.length
    ? correct.map(r => `<span class="res-letter correct">${r.letter.char}</span>`).join('')
    : '<span class="text-muted">কোনোটি নয়</span>';

  el('res-wrong-list').innerHTML = wrong.length
    ? wrong.map(r => `<span class="res-letter wrong">${r.letter.char}</span>`).join('')
    : '<span class="text-muted">কোনোটি নয়</span>';
}

async function testSave() {
  const results = S.testResults.map(r => ({
    char_id: r.letter.id,
    is_correct: r.is_correct,
    response_time: r.response_time,
  }));

  // Save test session
  await sbPost('test_sessions', {
    student_id: S.studentId,
    teacher_id: S.deviceId,
    letter_ids: S.testResults.map(r => r.letter.id),
    results,
    total:   S.testResults.length,
    correct: S.testResults.filter(r => r.is_correct).length,
    wrong:   S.testResults.filter(r => !r.is_correct).length,
  });

  // Upsert weakness records
  for (const r of S.testResults) {
    await sbUpsert('student_weaknesses', {
      student_id:    S.studentId,
      char_id:       r.letter.id,
      wrong_count:   r.is_correct ? 0 : 1,
      correct_count: r.is_correct ? 1 : 0,
      last_tested:   new Date().toISOString(),
    }, 'student_id,char_id');
  }

  el('btn-save').textContent  = '✓ সংরক্ষিত';
  el('btn-save').disabled     = true;
}

// ─── Letter grid renderer ─────────────────────────────────────────────────────
function renderLetterGrid(containerId, letters, selectedSet, onClick) {
  const container = el(containerId);
  container.innerHTML = letters.map(letter => {
    const sel = selectedSet && selectedSet.has(letter.id) ? 'selected' : '';
    return `<button class="letter-btn ${sel}" data-id="${letter.id}"
      title="${letter.name}">${letter.char}</button>`;
  }).join('');
  container.querySelectorAll('.letter-btn').forEach(btn => {
    btn.addEventListener('click', () => onClick(LETTERS[+btn.dataset.id]));
  });
}

// ─── Hardware simulator ───────────────────────────────────────────────────────
function simToggleDot(d) {
  if (S.simDots.has(d)) S.simDots.delete(d); else S.simDots.add(d);
  document.querySelectorAll('.sim-dot').forEach(btn => {
    btn.classList.toggle('on', S.simDots.has(+btn.dataset.dot));
  });
}

async function simSubmit() {
  const currentLetter = S.mode === 'learn' && S.learnMode === 'seq'
    ? LETTERS[S.seqIdx]
    : S.mode === 'learn' && S.rndSelected !== null
      ? LETTERS[S.rndSelected]
      : S.mode === 'test' && S.testPhase === 'running'
        ? S.testQueue[S.testQIdx]
        : null;

  if (!currentLetter) return;

  const entered   = [...S.simDots].reduce((m, d) => m | (1 << (d - 1)), 0);
  const expected  = currentLetter.mask;
  const is_correct = entered === expected;
  const ta = is_correct ? 2 : (S.simDots.size === 0 ? 0 : 1);
  const cs = is_correct ? 0 : 1;

  // Post simulated attempt to Supabase
  await sbPost('attempts', {
    user_id: S.studentId, session_id: crypto.randomUUID(), device_id: S.deviceId,
    attempt_index: 0, char_id: currentLetter.id, response_time: 1500, press_duration: 200,
    retry_count: 0, prev_accuracy: 0.7, prev_mastery: 0.6, hint_count: 0,
    session_number: 1, difficulty_level: 2, time_since_last_practice: 0,
    prev_confidence: 1, current_streak: 0, wrong_streak: 0, prev_mistakes: 0,
    teaching_action: ta, confidence_state: cs, expected_pattern: expected,
    entered_pattern: entered, is_correct, press_order: '[]',
    source: 'simulator', is_synthetic: false, spec_version: 2, braille_map_verified: true,
    created_at: new Date().toISOString(),
  });

  S.simDots.clear();
  document.querySelectorAll('.sim-dot').forEach(b => b.classList.remove('on'));
}

// ─── Mode switching ───────────────────────────────────────────────────────────
function setMode(mode) {
  S.mode = mode;
  el('tab-learn').classList.toggle('active', mode === 'learn');
  el('tab-test').classList.toggle('active',  mode === 'test');
  mode === 'learn' ? (show('panel-learn'), hide('panel-test'))
                   : (hide('panel-learn'), show('panel-test'));
  if (mode === 'learn') setLearnMode(S.learnMode);
  else testInit();
}

function setLearnMode(lm) {
  S.learnMode = lm;
  el('subtab-seq').classList.toggle('active', lm === 'seq');
  el('subtab-rnd').classList.toggle('active', lm === 'rnd');
  lm === 'seq' ? (show('sub-seq'), hide('sub-rnd'), seqInit())
               : (hide('sub-seq'), show('sub-rnd'), rndInit());
}

// ─── Init ─────────────────────────────────────────────────────────────────────
export function init() {
  // Wire device/student inputs
  el('input-device').addEventListener('change', e => { S.deviceId = e.target.value.trim() || 'esp32_01'; });
  el('input-student').addEventListener('change', e => { S.studentId = e.target.value.trim() || 'S01'; });

  // Mode tabs
  el('tab-learn').addEventListener('click', () => setMode('learn'));
  el('tab-test').addEventListener('click',  () => setMode('test'));

  // Learn sub-tabs
  el('subtab-seq').addEventListener('click', () => setLearnMode('seq'));
  el('subtab-rnd').addEventListener('click', () => setLearnMode('rnd'));

  // Sequential controls
  el('btn-seq-prev').addEventListener('click', seqPrev);
  el('btn-seq-play').addEventListener('click', seqPlay);
  el('btn-seq-next').addEventListener('click', seqNext);
  el('btn-auto').addEventListener('click', () => {
    S.autoAdvance = !S.autoAdvance;
    el('btn-auto').classList.toggle('active', S.autoAdvance);
    el('btn-auto').textContent = S.autoAdvance ? '⚡ অটো চালু' : '⏸ অটো বন্ধ';
  });

  // Test controls
  el('test-btn-start').addEventListener('click', testStart);
  el('btn-save').addEventListener('click', testSave);
  el('btn-retry').addEventListener('click', testInit);

  // Hardware simulator
  document.querySelectorAll('.sim-dot').forEach(btn => {
    btn.addEventListener('click', () => simToggleDot(+btn.dataset.dot));
  });
  el('btn-sim-submit').addEventListener('click', simSubmit);
  el('btn-sim-clear').addEventListener('click', () => {
    S.simDots.clear();
    document.querySelectorAll('.sim-dot').forEach(b => b.classList.remove('on'));
  });

  // Start
  setMode('learn');
  startPoll();
}
