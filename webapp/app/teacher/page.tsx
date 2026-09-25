"use client";

import { useEffect } from "react";
import { startTeacherApp } from "./teacherApp";

// The "শিক্ষক" tab: exam/test flow only (select letters -> run test ->
// results). Teaching a letter for the first time is a different feature and
// now lives at "শেখা" (webapp/app/learn/).
export default function TeacherPage() {
  useEffect(() => {
    const cleanup = startTeacherApp();
    return cleanup;
  }, []);

  return (
    <div className="teacher-app">
      {/* ══════════════ HEADER ══════════════ */}
      <header className="app-hdr">
        <div className="hdr1">
          <button className="btn-back" id="btn-back" type="button">←</button>
          <span className="hdr-title" id="hdr-title">বর্ণ নির্বাচন</span>
          <div className="esp-badge off" id="esp-badge">
            <div className="esp-dot off" id="esp-dot"></div>
            <span id="esp-label">ESP32 খুঁজছে...</span>
          </div>
        </div>
        <div className="hdr2" id="hdr-sub">ছাত্র: S01 • পরীক্ষা মোড</div>
        <div className="student-switch">
          <span className="student-switch-lbl">সক্রিয় ছাত্র:</span>
          <span className="student-switch-id" id="student-id-label">S01</span>
          <button className="student-switch-btn" id="btn-change-student" type="button">পরিবর্তন</button>
        </div>
      </header>

      <main className="main">
        {/* ████ TEST SELECT SCREEN ████ */}
        <div id="screen-test-select" className="screen active">
          <div className="sel-card hidden" id="test-sel-preview">
            <div className="sel-char" id="test-sel-char">—</div>
            <div className="sel-info">
              <div className="sel-info-lbl">শেষ নির্বাচিত</div>
              <div className="sel-info-name" id="test-sel-name">—</div>
            </div>
          </div>

          <div className="flex-row" style={{ marginBottom: 12 }}>
            <span className="text-sm" style={{ flex: 1, color: "var(--text2)" }}>বর্ণ নির্বাচন করুন (পরীক্ষার জন্য)</span>
            <button className="badge amber" style={{ cursor: "pointer", border: "none" }} id="btn-test-rnd-sel" type="button">এলোমেলো বাছাই</button>
          </div>

          <div className="cat-tabs" id="test-cat-tabs">
            <button className="cat-tab active" data-cat="all" type="button">সব (৫০)</button>
            <button className="cat-tab" data-cat="vowel" type="button">স্বরবর্ণ</button>
            <button className="cat-tab" data-cat="consonant" type="button">ব্যঞ্জনবর্ণ</button>
          </div>
          <div className="letter-grid" id="test-sel-grid"></div>

          <div className="card" style={{ position: "sticky", bottom: 80 }}>
            <div className="flex-row" style={{ marginBottom: 10 }}>
              <span className="text-sm" id="test-sel-count">০ টি বর্ণ নির্বাচিত</span>
              <button className="btn-sm" style={{ background: "var(--bg)", color: "var(--text2)", border: "1.5px solid var(--border)" }} id="btn-test-clear" type="button">পরিষ্কার</button>
            </div>
            <button className="btn primary mb0 disabled" id="btn-test-start" type="button">পরীক্ষা শুরু করুন →</button>
          </div>
        </div>

        {/* ████ TEST RUNNING SCREEN ████ */}
        <div id="screen-test-run" className="screen">
          <div className="card">
            <div className="prog-row">
              <span id="test-q-num">প্রশ্ন ১ / ১০</span>
              <span id="test-q-pct">১০%</span>
            </div>
            <div className="prog-bg"><div className="prog-fill" id="test-q-bar" style={{ width: "10%" }}></div></div>
          </div>

          <div className="test-char-card">
            <div className="char-bn" id="test-q-char">ক</div>
            <div className="char-sub" id="test-q-name">ব্যঞ্জনবর্ণ</div>
            <div className="mt3">
              <span className="wait-dot"></span>
              <span className="text-sm" style={{ color: "var(--text2)" }}>ইনপুটের অপেক্ষায়...</span>
            </div>
          </div>

          <div className="warn-card">
            <div className="warn-title">⚠️ পরীক্ষা মোড সক্রিয়</div>
            <div className="warn-body">কোনো ডট ভাইব্রেট করবে না — ছাত্র শুধু অডিও শুনে ESP32-এর পুশ বাটনে সঠিক ডট চাপবে এবং SUBMIT চাপবে। ওয়েব থেকে কোনো ইনপুট দেওয়া যাবে না।</div>
          </div>

          <button className="btn danger" id="btn-test-abort" type="button">পরীক্ষা বাতিল করুন</button>
        </div>

        {/* ████ RESULTS SCREEN ████ */}
        <div id="screen-results" className="screen">
          <div className="card center" style={{ paddingBottom: 20 }}>
            <div className="text-xs" style={{ marginBottom: 12 }}>ফলাফল ও মূল্যায়ন</div>
            <div className="score-ring">
              <svg width="120" height="120" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" strokeWidth="10" />
                <circle cx="60" cy="60" r="50" fill="none" stroke="#16a34a" strokeWidth="10"
                  strokeDasharray="314.16" strokeDashoffset="314.16" strokeLinecap="round" id="score-arc" />
              </svg>
              <div className="score-inner">
                <div className="score-pct" id="res-pct">০%</div>
                <div className="score-lbl" id="res-fraction">০/০ সঠিক</div>
              </div>
            </div>
            <div className="text-xs" style={{ marginTop: 4, marginBottom: 5 }}>পরীক্ষার পারফরম্যান্স</div>
            <div className="perf-bar"><div className="perf-fill" id="res-perf" style={{ width: "0%" }}></div></div>
          </div>

          <div className="stat-row">
            <div className="stat-box"><div className="stat-n" id="res-time">—</div><div className="stat-l">মোট সময়</div></div>
            <div className="stat-box"><div className="stat-n" id="res-speed">—</div><div className="stat-l">গড়/বর্ণ</div></div>
            <div className="stat-box"><div className="stat-n" style={{ color: "var(--green)" }} id="res-correct">০</div><div className="stat-l">সঠিক</div></div>
            <div className="stat-box"><div className="stat-n" style={{ color: "var(--red)" }} id="res-wrong">০</div><div className="stat-l">ভুল</div></div>
          </div>

          <div className="card">
            <div className="ans-tabs">
              <button className="ans-tab active" id="ans-tab-c" type="button">সঠিক <span className="ans-cnt g" id="ans-cnt-c">০</span></button>
              <button className="ans-tab" id="ans-tab-w" type="button">ভুল <span className="ans-cnt r" id="ans-cnt-w">০</span></button>
            </div>
            <div id="ans-correct-panel"><div className="correct-chips" id="res-correct-list"></div></div>
            <div id="ans-wrong-panel" className="hidden"><div id="res-wrong-list"></div></div>
          </div>

          <div className="auto-report">✓ অটোমেটিক রিপোর্ট পাঠানো হয়েছে</div>
          <button className="btn primary" id="btn-res-retry" type="button">পুনরায় পরীক্ষা দিন</button>
          <button className="btn outline" id="btn-res-home" type="button">নতুন পরীক্ষা</button>
        </div>
      </main>

      <div className="toast" id="toast"></div>
    </div>
  );
}
