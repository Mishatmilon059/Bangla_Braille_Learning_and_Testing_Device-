// Teacher-facing student roster + per-student profile.
//
// Reads three tables that already exist for this purpose (they just had no
// UI in front of them yet): `attempts` (for who has practiced and overall
// accuracy), `student_weaknesses` (per-letter mastery/streak state -- the
// same fields the ESP32 needs for personalization), and `test_sessions`
// (past test-mode results).

import { SUPABASE_URL, SUPABASE_ANON_KEY } from "@/lib/config";
import { LETTERS } from "@/lib/brailleMap";

const HDR = () => ({
  apikey: SUPABASE_ANON_KEY,
  Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
});

async function sbGet(table, params = {}) {
  const url = new URL(`${SUPABASE_URL}/rest/v1/${table}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  try {
    const r = await fetch(url, { headers: HDR() });
    return r.ok ? r.json() : [];
  } catch {
    return [];
  }
}

/** One row per distinct student found in `attempts`, with aggregate stats
 *  computed client-side (no view/RPC needed -- the row counts here are small,
 *  a handful of testers, not a production-scale user base). */
export async function loadRoster() {
  const rows = await sbGet("attempts", {
    select: "user_id,is_correct,created_at",
    is_synthetic: "eq.false",
    order: "created_at.asc",
    limit: "20000",
  });
  const byStudent = new Map();
  for (const r of rows) {
    const id = r.user_id || "(unknown)";
    if (!byStudent.has(id)) {
      byStudent.set(id, { studentId: id, total: 0, correct: 0, firstSeen: r.created_at, lastSeen: r.created_at });
    }
    const s = byStudent.get(id);
    s.total += 1;
    if (r.is_correct) s.correct += 1;
    s.lastSeen = r.created_at;
  }
  // Best performer first -- this is a leaderboard-style overview, not an
  // activity feed, so rank by accuracy rather than recency.
  return Array.from(byStudent.values())
    .map((s) => ({ ...s, accuracy: s.total > 0 ? s.correct / s.total : 0 }))
    .sort((a, b) => b.accuracy - a.accuracy);
}

/** Full profile for one student: per-letter mastery grid (what the ESP32's
 *  fetch_student_state() would load) PLUS the analytics a teacher actually
 *  needs to judge how this student is doing -- overall accuracy, the
 *  model's confidence-state read on them (confident / hesitant / guessing),
 *  and a session-by-session accuracy trend so improvement (or regression)
 *  is visible at a glance, not just a flat list of individual attempts. */
export async function loadStudentProfile(studentId) {
  const [weak, attempts] = await Promise.all([
    sbGet("student_weaknesses", {
      student_id: `eq.${studentId}`,
      select: "char_id,correct_count,wrong_count,mastery,current_streak,wrong_streak,last_tested",
    }),
    sbGet("attempts", {
      user_id: `eq.${studentId}`,
      select: "char_id,is_correct,response_time,press_duration,retry_count,prev_accuracy,prev_mastery,hint_count,current_streak,wrong_streak,teaching_action,confidence_state,session_id,created_at",
      order: "created_at.asc",
      limit: "5000",
    }),
  ]);

  const byChar = new Map(weak.map((w) => [w.char_id, w]));
  const grid = LETTERS.map((l) => {
    const w = byChar.get(l.id);
    const total = w ? (w.correct_count || 0) + (w.wrong_count || 0) : 0;
    return {
      id: l.id,
      char: l.char,
      mastery: w ? w.mastery : 0,
      attempts: total,
      accuracy: total > 0 ? w.correct_count / total : null,
    };
  });

  const total = attempts.length;
  const correct = attempts.filter((a) => a.is_correct).length;
  const wrong = total - correct;
  const avgResponseMs = total
    ? Math.round(attempts.reduce((s, a) => s + (a.response_time || 0), 0) / total)
    : 0;

  // confidence_state: 0 CONFIDENT, 1 HESITANT, 2 GUESSING (spec/engine_spec.json)
  const confCounts = [0, 0, 0];
  for (const a of attempts) {
    if (a.confidence_state === 0 || a.confidence_state === 1 || a.confidence_state === 2) {
      confCounts[a.confidence_state]++;
    }
  }
  const confTotal = confCounts[0] + confCounts[1] + confCounts[2];
  const confidence = {
    confident: confTotal ? confCounts[0] / confTotal : 0,
    hesitant: confTotal ? confCounts[1] / confTotal : 0,
    guessing: confTotal ? confCounts[2] / confTotal : 0,
    total: confTotal,
  };

  // Group chronologically by session_id -- attempts are already order=created_at.asc,
  // so the first time a session_id is seen fixes that session's position in the trend.
  const bySession = new Map();
  const sessionOrder = [];
  for (const a of attempts) {
    const sid = a.session_id || "unknown";
    if (!bySession.has(sid)) {
      bySession.set(sid, { total: 0, correct: 0, firstAt: a.created_at });
      sessionOrder.push(sid);
    }
    const s = bySession.get(sid);
    s.total += 1;
    if (a.is_correct) s.correct += 1;
  }
  const sessions = sessionOrder.map((sid, i) => {
    const s = bySession.get(sid);
    return {
      index: i + 1,
      accuracy: s.total ? s.correct / s.total : 0,
      total: s.total,
      date: s.firstAt,
    };
  });

  // The model's most recent input (what fed the decision) and output (what
  // it decided) -- so the dashboard can show not just "how did they do" but
  // "what did the model actually see and conclude on the last attempt".
  const latestAttempt = total ? attempts[total - 1] : null;
  const latest = latestAttempt && {
    input: {
      response_time: latestAttempt.response_time,
      press_duration: latestAttempt.press_duration,
      retry_count: latestAttempt.retry_count,
      prev_accuracy: latestAttempt.prev_accuracy,
      prev_mastery: latestAttempt.prev_mastery,
      hint_count: latestAttempt.hint_count,
      current_streak: latestAttempt.current_streak,
      wrong_streak: latestAttempt.wrong_streak,
    },
    output: {
      is_correct: latestAttempt.is_correct,
      teaching_action: latestAttempt.teaching_action,
      confidence_state: latestAttempt.confidence_state,
    },
    at: latestAttempt.created_at,
    charId: latestAttempt.char_id,
  };

  return { grid, total, correct, wrong, avgResponseMs, confidence, sessions, latest };
}

export function masteryTier(mastery, attempts) {
  if (attempts === 0) return "none";
  if (mastery >= 0.7) return "good";
  if (mastery >= 0.35) return "medium";
  return "poor";
}
