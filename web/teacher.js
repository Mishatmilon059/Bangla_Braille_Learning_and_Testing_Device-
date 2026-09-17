// teacher.js — Teacher Panel Logic (green mobile UI)
import { SUPABASE_URL, SUPABASE_ANON_KEY } from './config.js';

// ─── Braille map (Bangladesh standard, all 50 verified letters) ──────────────
const LETTERS = [
  { id:0,  char:'অ',  name:'অ (স্বরবর্ণ)',        dots:[1],           category:'vowel' },
  { id:1,  char:'আ',  name:'আ (স্বরবর্ণ)',         dots:[3,4,5],       category:'vowel' },
  { id:2,  char:'ই',  name:'ই (স্বরবর্ণ)',          dots:[2,4],         category:'vowel' },
  { id:3,  char:'ঈ',  name:'ঈ (স্বরবর্ণ)',          dots:[3,5],         category:'vowel' },
  { id:4,  char:'উ',  name:'উ (স্বরবর্ণ)',          dots:[1,3,6],       category:'vowel' },
  { id:5,  char:'ঊ',  name:'ঊ (স্বরবর্ণ)',          dots:[1,2,5,6],     category:'vowel' },
  { id:6,  char:'ঋ',  name:'ঋ (দুই-কোষ)',           dots:[1,2,3,5],     category:'vowel',     prefix:[5] },
  { id:7,  char:'এ',  name:'এ (স্বরবর্ণ)',          dots:[1,5],         category:'vowel' },
  { id:8,  char:'ঐ',  name:'ঐ (স্বরবর্ণ)',          dots:[3,4],         category:'vowel' },
  { id:9,  char:'ও',  name:'ও (স্বরবর্ণ)',          dots:[1,3,5],       category:'vowel' },
  { id:10, char:'ঔ',  name:'ঔ (স্বরবর্ণ)',          dots:[2,4,6],       category:'vowel' },
  { id:11, char:'ক',  name:'ক (ব্যঞ্জনবর্ণ)',       dots:[1,3],         category:'consonant' },
  { id:12, char:'খ',  name:'খ (ব্যঞ্জনবর্ণ)',       dots:[1,3,4,6],     category:'consonant' },
  { id:13, char:'গ',  name:'গ (ব্যঞ্জনবর্ণ)',       dots:[1,2,4,5],     category:'consonant' },
  { id:14, char:'ঘ',  name:'ঘ (ব্যঞ্জনবর্ণ)',       dots:[1,2,6],       category:'consonant' },
  { id:15, char:'ঙ',  name:'ঙ (ব্যঞ্জনবর্ণ)',       dots:[3,4,6],       category:'consonant' },
  { id:16, char:'চ',  name:'চ (ব্যঞ্জনবর্ণ)',       dots:[1,4],         category:'consonant' },
  { id:17, char:'ছ',  name:'ছ (ব্যঞ্জনবর্ণ)',       dots:[1,6],         category:'consonant' },
  { id:18, char:'জ',  name:'জ (ব্যঞ্জনবর্ণ)',       dots:[2,4,5],       category:'consonant' },
  { id:19, char:'ঝ',  name:'ঝ (ব্যঞ্জনবর্ণ)',       dots:[1,3,5,6],     category:'consonant' },
  { id:20, char:'ঞ',  name:'ঞ (ব্যঞ্জনবর্ণ)',       dots:[2,5],         category:'consonant' },
  { id:21, char:'ট',  name:'ট (ব্যঞ্জনবর্ণ)',       dots:[2,3,4,5,6],   category:'consonant' },
  { id:22, char:'ঠ',  name:'ঠ (ব্যঞ্জনবর্ণ)',       dots:[2,4,5,6],     category:'consonant' },
  { id:23, char:'ড',  name:'ড (ব্যঞ্জনবর্ণ)',       dots:[1,2,4,6],     category:'consonant' },
  { id:24, char:'ঢ',  name:'ঢ (ব্যঞ্জনবর্ণ)',       dots:[1,2,3,4,5,6], category:'consonant' },
  { id:25, char:'ণ',  name:'ণ (ব্যঞ্জনবর্ণ)',       dots:[3,4,5,6],     category:'consonant' },
  { id:26, char:'ত',  name:'ত (ব্যঞ্জনবর্ণ)',       dots:[2,3,4,5],     category:'consonant' },
  { id:27, char:'থ',  name:'থ (ব্যঞ্জনবর্ণ)',       dots:[1,4,5,6],     category:'consonant' },
  { id:28, char:'দ',  name:'দ (ব্যঞ্জনবর্ণ)',       dots:[1,4,5],       category:'consonant' },
  { id:29, char:'ধ',  name:'ধ (ব্যঞ্জনবর্ণ)',       dots:[2,3,4,6],     category:'consonant' },
  { id:30, char:'ন',  name:'ন (ব্যঞ্জনবর্ণ)',       dots:[1,3,4,5],     category:'consonant' },
  { id:31, char:'প',  name:'প (ব্যঞ্জনবর্ণ)',       dots:[1,2,3,4],     category:'consonant' },
  { id:32, char:'ফ',  name:'ফ (ব্যঞ্জনবর্ণ)',       dots:[2,3,5],       category:'consonant' },
  { id:33, char:'ব',  name:'ব (ব্যঞ্জনবর্ণ)',       dots:[1,2],         category:'consonant' },
  { id:34, char:'ভ',  name:'ভ (ব্যঞ্জনবর্ণ)',       dots:[1,2,3,6],     category:'consonant' },
  { id:35, char:'ম',  name:'ম (ব্যঞ্জনবর্ণ)',       dots:[1,3,4],       category:'consonant' },
  { id:36, char:'য',  name:'য (ব্যঞ্জনবর্ণ)',       dots:[1,3,4,5,6],   category:'consonant' },
  { id:37, char:'র',  name:'র (ব্যঞ্জনবর্ণ)',       dots:[1,2,3,5],     category:'consonant' },
  { id:38, char:'ল',  name:'ল (ব্যঞ্জনবর্ণ)',       dots:[1,2,3],       category:'consonant' },
  { id:39, char:'শ',  name:'শ (ব্যঞ্জনবর্ণ)',       dots:[1,4,6],       category:'consonant' },
  { id:40, char:'ষ',  name:'ষ (ব্যঞ্জনবর্ণ)',       dots:[1,2,3,4,6],   category:'consonant' },
  { id:41, char:'স',  name:'স (ব্যঞ্জনবর্ণ)',       dots:[2,3,4],       category:'consonant' },
  { id:42, char:'হ',  name:'হ (ব্যঞ্জনবর্ণ)',       dots:[1,2,5],       category:'consonant' },
  { id:43, char:'ড়',  name:'ড় (ব্যঞ্জনবর্ণ)',       dots:[1,2,4,5,6],   category:'consonant' },
  { id:44, char:'ঢ়',  name:'ঢ় (ব্যঞ্জনবর্ণ)',       dots:[1,2,3,5,6],   category:'consonant' },
  { id:45, char:'য়',  name:'য় (ব্যঞ্জনবর্ণ)',       dots:[2,6],         category:'consonant' },
  { id:46, char:'ৎ',  name:'ৎ (দুই-কোষ)',           dots:[2,3,4,5],     category:'consonant', prefix:[5] },
  { id:47, char:'ং',  name:'ং (অনুস্বর)',            dots:[5,6],         category:'consonant' },
  { id:48, char:'ঃ',  name:'ঃ (বিসর্গ)',             dots:[6],           category:'consonant' },
  { id:49, char:'ঁ',  name:'ঁ (চন্দ্রবিন্দু)',       dots:[3],           category:'consonant' },
];

function dotsToMask(dots) { return dots.reduce((m, d) => m | (1 << (d - 1)), 0); }
LETTERS.forEach(l => { l.mask = dotsToMask(l.dots); });

const TEACHING   = ['আবার চেষ্টা করো', 'হিন্ট দেখুন', 'সঠিক — এগিয়ে যান'];
const CONFIDENCE = ['আত্মবিশ্বাসী', 'দ্বিধাগ্রস্ত', 'অনুমান করছে'];

// ─── State ───────────────────────────────────────────────────────────────────
const S = {
  screen:      'learn',
  learnMode:   'seq',
  seqIdx:      0,
  autoAdvance: false,
  rndSelected: null,
  rndFilter:   'all',
  testFilter:  'all',
  testSelected: new Set(),
  testQueue:   [],
  testQIdx:    0,
  testResults: [],
  testStartTime: null,
  sessionStart:  null,
  lastAttemptId: null,
  pollTimer:     null,
  simDots:       new Set(),
  studentId:  'S01',
  deviceId:   'esp32_01',
  weaknesses: {},
  resTab:     'correct',
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

// ─── Polling ──────────────────────────────────────────────────────────────────
function startPoll() {
  S.sessionStart = new Date().toISOString();
  S.lastAttemptId = null;
  clearInterval(S.pollTimer);
  S.pollTimer = setInterval(pollAttempts, 500);
  setEspStatus('connected');
}

function stopPoll() { clearInterval(S.pollTimer); setEspStatus('idle'); }

async function pollAttempts() {
  const rows = await sbGet('attempts', {
    select: 'id,char_id,is_correct,teaching_action,confidence_state,response_time,entered_pattern,expected_pattern,created_at',
    created_at: `gt.${S.sessionStart}`,
    order: 'created_at.desc',
    limit: '1',
  });
  if (rows.length && rows[0].id !== S.lastAttemptId) {
    S.lastAttemptId = rows[0].id;
    handleAttempt(rows[0]);
  }
}

async function sendPlay(letterId, isTest = false) {
  await sbPost('remote_commands', {
    device_id: S.deviceId,
    letter_id: letterId,
    command:   isTest ? 'test' : 'play',
    created_at: new Date().toISOString(),
  });
}

// ─── Attempt handler ──────────────────────────────────────────────────────────
function handleAttempt(row) {
  if (S.screen === 'learn') {
    const letter = S.learnMode === 'seq'
      ? LETTERS[S.seqIdx]
      : (S.rndSelected !== null ? LETTERS[S.rndSelected] : null);
    if (!letter || row.char_id !== letter.id) return;

    renderLearnResult(row, letter);

    if (row.is_correct && S.learnMode === 'seq' && S.autoAdvance) {
      setTimeout(seqNext, 1200);
    }
  } else if (S.screen === 'test-run') {
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
      sendPlay(S.testQueue[S.testQIdx].id, true);
      renderTestQuestion();
    }
  }
}

// ─── UI helpers ───────────────────────────────────────────────────────────────
const el = id => document.getElementById(id);

function showToast(msg, duration = 2000) {
  const t = el('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}

function setEspStatus(state) {
  const badge = el('esp-badge');
  const dot   = el('esp-dot');
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
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const target = el('screen-' + name);
  if (target) target.classList.add('active');

  // Update header title
  const titles = {
    'learn': 'সহজ পাঠ',
    'test-select': 'বর্ণ নির্বাচন',
    'test-run': 'পরীক্ষা চলছে',
    'results': 'ফলাফল ও মূল্যায়ন',
  };
  el('hdr-title').textContent = titles[name] || 'শিক্ষক প্যানেল';

  // Update bottom nav active state
  const navMap = { 'learn': 'nav-learn', 'test-select': 'nav-test', 'test-run': 'nav-test', 'results': 'nav-test' };
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const activeNav = el(navMap[name]);
  if (activeNav) activeNav.classList.add('active');
}

function brailleCellHtml(dotMask, expectedMask = -1) {
  const order = [1, 4, 2, 5, 3, 6];
  return `<div class="braille-cell">${order.map(d => {
    const bit = 1 << (d - 1);
    const on  = Boolean(dotMask & bit);
    let cls   = 'bdot';
    if (expectedMask >= 0) {
      const exp = Boolean(expectedMask & bit);
      if (on && exp)   cls += ' correct';
      else if (!on && exp)  cls += ' missing';
      else if (on && !exp)  cls += ' extra';
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
  if (extra.length)   parts.push(`অতিরিক্ত → ডট ${extra.join(', ')}`);
  return parts.join('  |  ') || 'আবার চেষ্টা করো';
}

function classifyError(row) {
  const rt = row.response_time ?? 0;
  if (rt > 6000) return { type: 'time', label: 'সময় বেশি লেগেছে' };
  const entered  = row.entered_pattern  ?? 0;
  const expected = row.expected_pattern ?? 0;
  if (entered !== expected) return { type: 'dots', label: 'ভুল ডট প্রেস' };
  return { type: 'retry', label: 'বারবার ভুল চেষ্টা' };
}

// ─── Student weaknesses ───────────────────────────────────────────────────────
async function loadWeaknesses() {
  const rows = await sbGet('student_weaknesses', { student_id: `eq.${S.studentId}` });
  S.weaknesses = {};
  rows.forEach(r => { S.weaknesses[r.char_id] = r; });
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

// ─── Letter grid renderer ─────────────────────────────────────────────────────
function renderLetterGrid(containerId, filter = 'all', isTest = false, onClickOverride = null) {
  const container = el(containerId);
  const letters   = filter === 'all' ? LETTERS : LETTERS.filter(l => l.category === filter);
  const selected  = isTest ? S.testSelected : new Set();

  container.innerHTML = letters.map(l => {
    const sel = selected.has(l.id) ? 'selected' : '';
    const mCls = getMasteryClass(l.id);
    return `<div class="lg-item ${sel}" data-id="${l.id}">
      <div class="mastery-dot ${mCls}"></div>
      <div class="lg-char">${l.char}</div>
    </div>`;
  }).join('');

  container.querySelectorAll('.lg-item').forEach(item => {
    item.addEventListener('click', () => {
      const id     = +item.dataset.id;
      const letter = LETTERS[id];
      if (onClickOverride) { onClickOverride(letter, item); return; }

      if (isTest) {
        if (S.testSelected.has(id)) S.testSelected.delete(id);
        else S.testSelected.add(id);
        item.classList.toggle('selected', S.testSelected.has(id));
        updateTestSelCount();
        if (S.testSelected.size > 0) {
          el('test-sel-char').textContent  = letter.char;
          el('test-sel-name').textContent  = letter.name;
          el('test-sel-preview').classList.remove('hidden');
        } else {
          el('test-sel-preview').classList.add('hidden');
        }
      } else {
        // random learning
        S.rndSelected = id;
        container.querySelectorAll('.lg-item').forEach(i =>
          i.classList.toggle('selected', +i.dataset.id === id));
        el('rnd-char').textContent = letter.char;
        el('rnd-name').textContent = letter.name;
        el('rnd-sel-card').classList.remove('hidden');
        el('rnd-result').classList.add('hidden');
        sendPlay(id);
      }
    });
  });
}

function updateTestSelCount() {
  const n = S.testSelected.size;
  el('test-sel-count').textContent = `${n} টি বর্ণ নির্বাচিত`;
  const btn = el('btn-test-start');
  if (n > 0) btn.classList.remove('disabled');
  else       btn.classList.add('disabled');
}

// ─── Category filter tabs ─────────────────────────────────────────────────────
function wireCatTabs(tabsId, onSelect) {
  document.querySelectorAll(`#${tabsId} .cat-tab`).forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll(`#${tabsId} .cat-tab`).forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      onSelect(tab.dataset.cat);
    });
  });
}

// ─── Sequential mode ──────────────────────────────────────────────────────────
function seqRender() {
  const letter = LETTERS[S.seqIdx];
  el('seq-char').textContent   = letter.char;
  el('seq-name').textContent   = letter.name;
  el('seq-label').textContent  = `বর্ণমালা নম্বর ${S.seqIdx + 1}`;
  const pct = Math.round(((S.seqIdx + 1) / LETTERS.length) * 100);
  el('seq-progress').textContent = `অগ্রগতি: ${S.seqIdx + 1}/${LETTERS.length}`;
  el('seq-pct').textContent      = `${pct}%`;
  el('seq-bar').style.width      = `${pct}%`;
  el('seq-dots').innerHTML       = brailleCellHtml(letter.mask);

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
  const ta  = row.teaching_action  ?? 2;
  const cs  = row.confidence_state ?? 1;
  const ok  = row.is_correct;
  const ep  = row.expected_pattern ?? letter.mask;
  const inp = row.entered_pattern  ?? 0;

  const isSeq = S.learnMode === 'seq';
  const prefix = isSeq ? 'seq' : 'rnd';
  const resultEl = el(prefix + '-result');
  resultEl.classList.remove('hidden');

  const actionEl = el(prefix + '-action');
  actionEl.textContent = TEACHING[ta];
  actionEl.className = 'action-badge ' + ['repeat', 'hint', 'correct'][ta];

  el(prefix + '-conf').textContent = CONFIDENCE[cs];

  if (isSeq) {
    const hintEl = el('seq-hint');
    hintEl.textContent = ok ? '✓ সঠিক উত্তর' : generateHint(inp, ep);
    hintEl.classList.remove('hidden');
    hintEl.style.color = ok ? 'var(--green-dark)' : 'var(--amber)';

    const matchEl = el('seq-match-badge');
    if (ok) matchEl.classList.remove('hidden');
    else    matchEl.classList.add('hidden');

    const cmpEl = el('seq-dots-cmp');
    cmpEl.classList.remove('hidden');
    el('seq-dots-ent').innerHTML = brailleCellHtml(inp, ep);
    el('seq-dots-exp').innerHTML = brailleCellHtml(ep);
  } else {
    const hintEl = el('rnd-hint');
    hintEl.textContent = ok ? '✓ সঠিক উত্তর' : generateHint(inp, ep);
    hintEl.classList.remove('hidden');
    hintEl.style.color = ok ? 'var(--green-dark)' : 'var(--amber)';

    const cmpEl = el('rnd-dots-cmp');
    cmpEl.classList.remove('hidden');
    el('rnd-dots-ent').innerHTML = brailleCellHtml(inp, ep);
    el('rnd-dots-exp').innerHTML = brailleCellHtml(ep);
  }
}

// ─── Random mode ──────────────────────────────────────────────────────────────
function rndInit() {
  renderLetterGrid('rnd-grid', S.rndFilter, false);
}

// ─── Test mode ────────────────────────────────────────────────────────────────
function testInit() {
  S.testSelected = new Set();
  S.testResults  = [];
  S.testQIdx     = 0;
  el('test-sel-preview').classList.add('hidden');
  el('btn-test-start').classList.add('disabled');
  el('test-sel-count').textContent = '০ টি বর্ণ নির্বাচিত';
  renderLetterGrid('test-sel-grid', S.testFilter, true);
  showScreen('test-select');
}

function testStart() {
  if (S.testSelected.size === 0) return;
  S.testPhase    = 'running';
  S.testQIdx     = 0;
  S.testResults  = [];
  S.testStartTime = Date.now();
  S.testQueue    = [...S.testSelected].map(id => LETTERS[id]).sort(() => Math.random() - 0.5);

  showScreen('test-run');
  sendPlay(S.testQueue[0].id, true);
  renderTestQuestion();

  // Clear sim dots
  S.simDots.clear();
  document.querySelectorAll('.sim-dot').forEach(b => b.classList.remove('on'));
}

function renderTestQuestion() {
  const letter = S.testQueue[S.testQIdx];
  const total  = S.testQueue.length;
  const pct    = Math.round(((S.testQIdx + 1) / total) * 100);
  el('test-q-num').textContent  = `প্রশ্ন ${S.testQIdx + 1} / ${total}`;
  el('test-q-pct').textContent  = `${pct}%`;
  el('test-q-bar').style.width  = `${pct}%`;
  el('test-q-char').textContent = letter.char;
  el('test-q-name').textContent = letter.name;
}

function testShowResults() {
  const elapsed = Math.round((Date.now() - (S.testStartTime ?? Date.now())) / 1000);
  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
  const ss = String(elapsed % 60).padStart(2, '0');

  const correct = S.testResults.filter(r => r.is_correct);
  const wrong   = S.testResults.filter(r => !r.is_correct);
  const total   = S.testResults.length;
  const pct     = total ? Math.round((correct.length / total) * 100) : 0;

  const avgMs = total
    ? Math.round(S.testResults.reduce((s, r) => s + r.response_time, 0) / total)
    : 0;

  // Score ring
  const circumference = 314.16;
  const offset = circumference * (1 - pct / 100);
  el('score-arc').setAttribute('stroke-dashoffset', offset.toFixed(2));
  el('res-pct').textContent      = `${pct}%`;
  el('res-fraction').textContent = `${correct.length}/${total} সঠিক`;
  el('res-perf').style.width     = `${pct}%`;

  // Stats
  el('res-time').textContent    = `${mm}:${ss}`;
  el('res-speed').textContent   = avgMs > 0 ? `${(avgMs / 1000).toFixed(1)}s` : '—';
  el('res-correct').textContent = correct.length;
  el('res-wrong').textContent   = wrong.length;
  el('ans-cnt-c').textContent   = correct.length;
  el('ans-cnt-w').textContent   = wrong.length;

  // Correct list
  el('res-correct-list').innerHTML = correct.length
    ? correct.map(r => `<div class="correct-chip"><span>${r.letter.char}</span><span class="ck">✓</span></div>`).join('')
    : '<span class="text-xs">কোনোটি সঠিক হয়নি</span>';

  // Wrong list with error types
  el('res-wrong-list').innerHTML = wrong.length
    ? wrong.map(r => {
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

  // Switch to correct tab by default
  resTab('correct');
  showScreen('results');

  // Auto-save
  testSave();
}

async function testSave() {
  const results = S.testResults.map(r => ({
    char_id: r.letter.id, is_correct: r.is_correct, response_time: r.response_time,
  }));
  await sbPost('test_sessions', {
    student_id: S.studentId, teacher_id: S.deviceId,
    letter_ids: S.testResults.map(r => r.letter.id),
    results, total: S.testResults.length,
    correct: S.testResults.filter(r => r.is_correct).length,
    wrong:   S.testResults.filter(r => !r.is_correct).length,
  });
  for (const r of S.testResults) {
    await sbUpsert('student_weaknesses', {
      student_id: S.studentId, char_id: r.letter.id,
      wrong_count:   r.is_correct ? 0 : 1,
      correct_count: r.is_correct ? 1 : 0,
      last_tested:   new Date().toISOString(),
    }, 'student_id,char_id');
  }
  // Reload weaknesses to update mastery dots
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

// ─── Hardware simulator ───────────────────────────────────────────────────────
function simToggleDot(d) {
  if (S.simDots.has(d)) S.simDots.delete(d); else S.simDots.add(d);
  document.querySelectorAll('.sim-dot').forEach(btn =>
    btn.classList.toggle('on', S.simDots.has(+btn.dataset.dot)));
}

async function simSubmit() {
  const letter = S.screen === 'learn' && S.learnMode === 'seq'
    ? LETTERS[S.seqIdx]
    : S.screen === 'learn' && S.rndSelected !== null
      ? LETTERS[S.rndSelected]
      : S.screen === 'test-run'
        ? S.testQueue[S.testQIdx]
        : null;

  if (!letter) { showToast('প্রথমে একটি বর্ণ বাজান'); return; }

  const entered    = [...S.simDots].reduce((m, d) => m | (1 << (d - 1)), 0);
  const expected   = letter.mask;
  const is_correct = entered === expected;
  const ta = is_correct ? 2 : (S.simDots.size === 0 ? 0 : 1);
  const cs = is_correct ? 0 : 1;

  await sbPost('attempts', {
    user_id: S.studentId, session_id: crypto.randomUUID(), device_id: S.deviceId,
    attempt_index: 0, char_id: letter.id,
    response_time: 1500, press_duration: 200, retry_count: 0,
    prev_accuracy: 0.7, prev_mastery: 0.6, hint_count: 0,
    session_number: 1, difficulty_level: 2, time_since_last_practice: 0,
    prev_confidence: 1, current_streak: 0, wrong_streak: 0, prev_mistakes: 0,
    teaching_action: ta, confidence_state: cs,
    expected_pattern: expected, entered_pattern: entered,
    is_correct, press_order: '[]',
    source: 'simulator', is_synthetic: false, spec_version: 2, braille_map_verified: true,
    created_at: new Date().toISOString(),
  });

  S.simDots.clear();
  document.querySelectorAll('.sim-dot').forEach(b => b.classList.remove('on'));
}

function simClear() {
  S.simDots.clear();
  document.querySelectorAll('.sim-dot').forEach(b => b.classList.remove('on'));
}

// ─── Mode switching ───────────────────────────────────────────────────────────
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

// ─── Back button ─────────────────────────────────────────────────────────────
function handleBack() {
  if (S.screen === 'test-select' || S.screen === 'results') {
    showScreen('learn');
  } else if (S.screen === 'test-run') {
    if (confirm('পরীক্ষা বাতিল করবেন?')) showScreen('test-select');
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────
export async function init() {
  // Header sub info
  el('hdr-sub').textContent = `ছাত্র: ${S.studentId} • বর্ণমালা শিক্ষা`;

  // Load weaknesses in background
  loadWeaknesses();

  // Back button
  el('btn-back').addEventListener('click', handleBack);

  // Learn tab pills
  el('tp-seq').addEventListener('click', () => setLearnMode('seq'));
  el('tp-rnd').addEventListener('click', () => setLearnMode('rnd'));

  // Sequential controls
  el('btn-seq-prev').addEventListener('click', seqPrev);
  el('btn-seq-next').addEventListener('click', seqNext);
  el('btn-seq-teach').addEventListener('click', () => { sendPlay(LETTERS[S.seqIdx].id); showToast('পাঠদান শুরু হয়েছে'); });
  el('btn-seq-play').addEventListener('click', () => { sendPlay(LETTERS[S.seqIdx].id); });
  el('btn-seq-stop').addEventListener('click', () => { stopPoll(); showToast('পাঠদান থামানো হয়েছে'); });
  el('btn-seq-auto').addEventListener('click', () => {
    S.autoAdvance = !S.autoAdvance;
    el('btn-seq-auto').textContent = S.autoAdvance ? '⚡ অটো চালু' : '⚡ অটো';
    el('btn-seq-auto').className   = S.autoAdvance ? 'btn primary' : 'btn outline';
  });

  // Random play button
  el('btn-rnd-play').addEventListener('click', () => {
    if (S.rndSelected !== null) sendPlay(S.rndSelected);
  });

  // Random category filter
  wireCatTabs('rnd-cat-tabs', cat => {
    S.rndFilter = cat;
    renderLetterGrid('rnd-grid', cat, false);
  });

  // Test select category filter
  wireCatTabs('test-cat-tabs', cat => {
    S.testFilter = cat;
    renderLetterGrid('test-sel-grid', cat, true);
  });

  // Test select controls
  el('btn-test-rnd-sel').addEventListener('click', () => {
    const filtered = S.testFilter === 'all' ? LETTERS : LETTERS.filter(l => l.category === S.testFilter);
    const n = Math.min(10, filtered.length);
    const shuffled = filtered.sort(() => Math.random() - 0.5).slice(0, n);
    S.testSelected = new Set(shuffled.map(l => l.id));
    renderLetterGrid('test-sel-grid', S.testFilter, true);
    updateTestSelCount();
    if (shuffled.length > 0) {
      const last = shuffled[shuffled.length - 1];
      el('test-sel-char').textContent = last.char;
      el('test-sel-name').textContent = last.name;
      el('test-sel-preview').classList.remove('hidden');
    }
    showToast(`${n}টি বর্ণ এলোমেলোভাবে নির্বাচিত`);
  });

  el('btn-test-clear').addEventListener('click', () => {
    S.testSelected.clear();
    renderLetterGrid('test-sel-grid', S.testFilter, true);
    updateTestSelCount();
    el('test-sel-preview').classList.add('hidden');
  });

  el('btn-test-start').addEventListener('click', testStart);
  el('btn-test-abort').addEventListener('click', () => {
    if (confirm('পরীক্ষা বাতিল করবেন?')) {
      stopPoll();
      testInit();
    }
  });

  // Results
  el('ans-tab-c').addEventListener('click', () => resTab('correct'));
  el('ans-tab-w').addEventListener('click', () => resTab('wrong'));
  el('btn-res-retry').addEventListener('click', testInit);
  el('btn-res-home').addEventListener('click', () => showScreen('learn'));

  // Hardware simulator (all .sim-dot buttons across all screens share simDots state)
  document.querySelectorAll('.sim-dot').forEach(btn =>
    btn.addEventListener('click', () => simToggleDot(+btn.dataset.dot)));
  el('btn-sim-clear').addEventListener('click', simClear);
  el('btn-sim-submit').addEventListener('click', simSubmit);
  el('btn-sim-clear2').addEventListener('click', simClear);
  el('btn-sim-submit2').addEventListener('click', simSubmit);

  // Bottom nav
  el('nav-dash').addEventListener('click',  () => showScreen('learn'));
  el('nav-learn').addEventListener('click', () => showScreen('learn'));
  el('nav-test').addEventListener('click',  testInit);
  el('nav-info').addEventListener('click',  () => window.open('./index.html', '_self'));

  // Init first render
  seqRender();
  startPoll();
}
