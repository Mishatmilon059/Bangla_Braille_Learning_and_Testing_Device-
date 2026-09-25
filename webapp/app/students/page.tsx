"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { loadRoster, loadStudentProfile, masteryTier } from "./studentsApp";
import { LETTERS } from "@/lib/brailleMap";

const CONF_LABEL = { confident: "কনফিডেন্ট", hesitant: "দ্বিধাগ্রস্ত", guessing: "অনুমাননির্ভর" };
const CONF_COLOR = { confident: "var(--green)", hesitant: "var(--amber)", guessing: "var(--red)" };

const REFRESH_MS = 5000;

export default function StudentsPage() {
  const [roster, setRoster] = useState<any[] | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [profile, setProfile] = useState<any | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(false);

  // Live dashboard: a new attempt logged by the model should show up here
  // without the teacher having to reload the page.
  useEffect(() => {
    loadRoster().then(setRoster);
    const id = setInterval(() => loadRoster().then(setRoster), REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!openId) return;
    const id = setInterval(() => {
      loadStudentProfile(openId).then(setProfile);
    }, REFRESH_MS);
    return () => clearInterval(id);
  }, [openId]);

  async function toggle(studentId: string) {
    if (openId === studentId) {
      setOpenId(null);
      setProfile(null);
      return;
    }
    setOpenId(studentId);
    setProfile(null);
    setLoadingProfile(true);
    const p = await loadStudentProfile(studentId);
    setProfile(p);
    setLoadingProfile(false);
  }

  return (
    <div className="teacher-app">
      <header className="app-hdr">
        <div className="hdr1">
          <Link href="/teacher" className="btn-back">←</Link>
          <span className="hdr-title">শিক্ষার্থীদের অগ্রগতি</span>
        </div>
        <div className="hdr2">{roster ? `মোট ${roster.length} জন শিক্ষার্থী` : "লোড হচ্ছে..."}</div>
      </header>

      <main className="main">
        {roster && roster.length === 0 && (
          <div className="card center" style={{ padding: 24, color: "var(--text2)" }}>
            এখনো কোনো শিক্ষার্থীর ডাটা নেই।
          </div>
        )}

        {roster && roster.length > 0 && (
          <>
            <div className="card dashboard-stats">
              <div className="dstat">
                <div className="dstat-v">{roster.length}</div>
                <div className="dstat-l">শিক্ষার্থী</div>
              </div>
              <div className="dstat">
                <div className="dstat-v">{roster.reduce((a, s) => a + s.total, 0)}</div>
                <div className="dstat-l">মোট attempt</div>
              </div>
              <div className="dstat">
                <div className="dstat-v">
                  {Math.round((roster.reduce((a, s) => a + s.accuracy, 0) / roster.length) * 100)}%
                </div>
                <div className="dstat-l">গড় নির্ভুলতা</div>
              </div>
            </div>

            {/* Ranking chart -- same ranking as the list below, but as bars so
                "who's ahead, who's behind" reads in one glance, not just numbers. */}
            <div className="card ranking-chart">
              <div className="text-xs" style={{ color: "var(--text2)", marginBottom: 10 }}>
                নির্ভুলতা অনুযায়ী র‍্যাংকিং
              </div>
              {roster.map((s, i) => (
                <div className="rank-bar-row" key={s.studentId}>
                  <span className="rank-bar-id">{s.studentId}</span>
                  <div className="rank-bar-track">
                    <div
                      className={`rank-bar-fill${i === 0 ? " gold" : s.accuracy < 0.4 ? " weak" : ""}`}
                      style={{ width: `${Math.max(4, Math.round(s.accuracy * 100))}%` }}
                    />
                  </div>
                  <span className="rank-bar-pct">{Math.round(s.accuracy * 100)}%</span>
                </div>
              ))}
            </div>
          </>
        )}

        {roster?.map((s, i) => (
          <div className="card student-card" key={s.studentId}>
            <button className="student-row" onClick={() => toggle(s.studentId)} type="button">
              <div className={`student-rank${i === 0 ? " gold" : ""}`}>{i + 1}</div>
              <div className="student-row-id">{s.studentId}</div>
              <div className="student-row-stats">
                <span>{s.total} attempts</span>
                <span className={s.accuracy >= 0.7 ? "text-good" : s.accuracy >= 0.4 ? "text-medium" : "text-poor"}>
                  {Math.round(s.accuracy * 100)}%
                </span>
                <span className="text-xs" style={{ color: "var(--text2)" }}>
                  {new Date(s.lastSeen).toLocaleDateString()}
                </span>
              </div>
              <div className="student-row-caret">{openId === s.studentId ? "▲" : "▼"}</div>
            </button>

            {openId === s.studentId && (
              <div className="student-profile">
                {loadingProfile && <div className="text-xs">লোড হচ্ছে...</div>}
                {profile && (
                  <>
                    {/* Overall numbers */}
                    <div className="profile-stat-row">
                      <div className="pstat"><div className="pstat-v">{profile.total}</div><div className="pstat-l">মোট</div></div>
                      <div className="pstat"><div className="pstat-v text-good">{profile.correct}</div><div className="pstat-l">সঠিক</div></div>
                      <div className="pstat"><div className="pstat-v text-poor">{profile.wrong}</div><div className="pstat-l">ভুল</div></div>
                      <div className="pstat"><div className="pstat-v">{(profile.avgResponseMs / 1000).toFixed(1)}s</div><div className="pstat-l">গড় সময়</div></div>
                    </div>

                    {/* Model's confidence-state read on this student */}
                    <div className="text-xs" style={{ color: "var(--text2)", margin: "12px 0 6px" }}>
                      মডেলের কনফিডেন্স-স্টেট আউটপুট ({profile.confidence.total} attempt-এ)
                    </div>
                    <div className="conf-bar">
                      {(["confident", "hesitant", "guessing"] as const).map((k) => {
                        const pct = profile.confidence[k] * 100;
                        return pct > 0 ? (
                          <div key={k} style={{ width: `${pct}%`, background: CONF_COLOR[k] }} title={`${CONF_LABEL[k]}: ${pct.toFixed(0)}%`} />
                        ) : null;
                      })}
                    </div>
                    <div className="conf-legend">
                      {(["confident", "hesitant", "guessing"] as const).map((k) => (
                        <span key={k}><i style={{ background: CONF_COLOR[k] }} />{CONF_LABEL[k]} {Math.round(profile.confidence[k] * 100)}%</span>
                      ))}
                    </div>

                    {/* Latest attempt -- the actual feature values the model saw
                        (input) and what it decided (output), refreshed live. */}
                    {profile.latest && (
                      <>
                        <div className="text-xs" style={{ color: "var(--text2)", margin: "14px 0 6px" }}>
                          সর্বশেষ attempt — {new Date(profile.latest.at).toLocaleString()}
                        </div>
                        <div className="latest-io">
                          <div className="latest-io-col">
                            <div className="latest-io-hdr">মডেল ইনপুট</div>
                            <div className="io-row"><span>response_time</span><b>{Math.round(profile.latest.input.response_time ?? 0)}ms</b></div>
                            <div className="io-row"><span>press_duration</span><b>{Math.round(profile.latest.input.press_duration ?? 0)}ms</b></div>
                            <div className="io-row"><span>retry_count</span><b>{profile.latest.input.retry_count ?? 0}</b></div>
                            <div className="io-row"><span>prev_accuracy</span><b>{((profile.latest.input.prev_accuracy ?? 0) * 100).toFixed(0)}%</b></div>
                            <div className="io-row"><span>prev_mastery</span><b>{((profile.latest.input.prev_mastery ?? 0) * 100).toFixed(0)}%</b></div>
                            <div className="io-row"><span>hint_count</span><b>{profile.latest.input.hint_count ?? 0}</b></div>
                            <div className="io-row"><span>current_streak</span><b>{profile.latest.input.current_streak ?? 0}</b></div>
                            <div className="io-row"><span>wrong_streak</span><b>{profile.latest.input.wrong_streak ?? 0}</b></div>
                          </div>
                          <div className="latest-io-col">
                            <div className="latest-io-hdr">মডেল আউটপুট</div>
                            <div className="io-row"><span>ফলাফল</span><b className={profile.latest.output.is_correct ? "text-good" : "text-poor"}>{profile.latest.output.is_correct ? "সঠিক" : "ভুল"}</b></div>
                            <div className="io-row"><span>teaching_action</span><b>{["REPEAT", "HINT", "NORMAL_PRACTICE"][profile.latest.output.teaching_action] ?? "—"}</b></div>
                            <div className="io-row"><span>confidence_state</span><b>{["CONFIDENT", "HESITANT", "GUESSING"][profile.latest.output.confidence_state] ?? "—"}</b></div>
                          </div>
                        </div>
                      </>
                    )}

                    {/* Session-by-session accuracy trend */}
                    <div className="text-xs" style={{ color: "var(--text2)", margin: "14px 0 6px" }}>
                      সেশন অনুযায়ী অগ্রগতি ({profile.sessions.length} সেশন)
                    </div>
                    <SessionTrendChart sessions={profile.sessions} />

                    {/* Per-letter mastery */}
                    <div className="text-xs" style={{ color: "var(--text2)", margin: "14px 0 6px" }}>
                      অক্ষরভিত্তিক দক্ষতা
                    </div>
                    <div className="mastery-grid">
                      {profile.grid.map((g: any) => (
                        <div
                          key={g.id}
                          className={`mastery-dot tier-${masteryTier(g.mastery, g.attempts)}`}
                          title={`${g.char} — ${g.attempts} attempts, mastery ${(g.mastery * 100).toFixed(0)}%`}
                        >
                          {g.char}
                        </div>
                      ))}
                    </div>

                    {/* Test Sessions history */}
                    {profile.testSessions && profile.testSessions.length > 0 && (
                      <div style={{ marginTop: 16 }}>
                        <div className="text-xs" style={{ color: "var(--text2)", margin: "14px 0 6px", fontWeight: 700 }}>
                          📋 পরীক্ষার ফলাফল ও ইতিহাস ({profile.testSessions.length} টি পরীক্ষা)
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {profile.testSessions.map((t: any) => {
                            const pct = t.total > 0 ? Math.round((t.correct / t.total) * 100) : 0;
                            const lettersStr = Array.isArray(t.letter_ids)
                              ? t.letter_ids.map((id: number) => LETTERS[id]?.char || `#${id}`).join(", ")
                              : "";
                            return (
                              <div
                                key={t.id}
                                style={{
                                  background: "var(--surface)",
                                  border: "1px solid var(--border)",
                                  borderRadius: 8,
                                  padding: "10px 12px",
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                                }}
                              >
                                <div>
                                  <div style={{ fontWeight: 600, fontSize: 13 }}>
                                    পরীক্ষা #{t.id} —{" "}
                                    <span style={{ color: pct >= 80 ? "var(--green-dark)" : pct >= 50 ? "var(--amber)" : "var(--red)" }}>
                                      {pct}%
                                    </span>
                                  </div>
                                  <div style={{ fontSize: 11, color: "var(--text2)", marginTop: 2 }}>
                                    সঠিক: <b style={{ color: "var(--green-dark)" }}>{t.correct}</b> | ভুল: <b style={{ color: "var(--red)" }}>{t.wrong}</b> | মোট: {t.total}
                                  </div>
                                  {lettersStr && (
                                    <div style={{ fontSize: 11, color: "var(--text2)", marginTop: 2 }}>
                                      বর্ণসমূহ: <span style={{ color: "var(--text)" }}>{lettersStr}</span>
                                    </div>
                                  )}
                                </div>
                                <div style={{ fontSize: 11, color: "var(--text2)", textAlign: "right" }}>
                                  {new Date(t.created_at).toLocaleDateString()}
                                  <br />
                                  {new Date(t.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        ))}
      </main>
    </div>
  );
}

function SessionTrendChart({ sessions }: { sessions: any[] }) {
  if (!sessions || sessions.length === 0) {
    return <div className="text-xs" style={{ color: "var(--text2)" }}>কোনো সেশন ডেটা নেই।</div>;
  }
  const W = 300, H = 70, PAD = 6;
  const n = sessions.length;
  const x = (i: number) => (n === 1 ? W / 2 : PAD + (i * (W - 2 * PAD)) / (n - 1));
  const y = (acc: number) => H - PAD - acc * (H - 2 * PAD);
  const points = sessions.map((s, i) => `${x(i)},${y(s.accuracy)}`).join(" ");
  const first = sessions[0].accuracy;
  const last = sessions[sessions.length - 1].accuracy;
  const trendUp = last >= first;

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none">
        <line x1={PAD} y1={y(0.5)} x2={W - PAD} y2={y(0.5)} stroke="var(--border)" strokeDasharray="3,3" strokeWidth={1} />
        <polyline points={points} fill="none" stroke={trendUp ? "var(--green)" : "var(--red)"} strokeWidth={2} />
        {sessions.map((s, i) => (
          <circle key={i} cx={x(i)} cy={y(s.accuracy)} r={3} fill={trendUp ? "var(--green)" : "var(--red)"} />
        ))}
      </svg>
      <div className="text-xs" style={{ color: trendUp ? "var(--green-dark)" : "var(--red)", marginTop: 2 }}>
        {trendUp ? "▲ উন্নতি হচ্ছে" : "▼ পারফরম্যান্স কমছে"} — প্রথম সেশন {Math.round(first * 100)}% → সর্বশেষ সেশন {Math.round(last * 100)}%
      </div>
    </div>
  );
}
