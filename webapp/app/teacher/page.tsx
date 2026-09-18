"use client";

import { useEffect } from "react";
import Link from "next/link";
import { startTeacherApp } from "./teacherApp";

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
          <span className="hdr-title" id="hdr-title">সহজ পাঠ</span>
          <div className="esp-badge" id="esp-badge">
            <div className="esp-dot" id="esp-dot"></div>
            <span id="esp-label">ESP32 সংযুক্ত</span>
          </div>
        </div>
        <div className="hdr2" id="hdr-sub">ছাত্র: S01 • বর্ণমালা শিক্ষা</div>
      </header>

      <main className="main">
        {/* ████ LEARN SCREEN ████ */}
        <div id="screen-learn" className="screen active">
          <div className="tab-pills">
            <button className="tab-pill active" id="tp-seq" type="button">ক্রমানুসারে (১, ২, ৩...)</button>
            <button className="tab-pill" id="tp-rnd" type="button">এলোমেলো (Random)</button>
          </div>

          {/* Sequential panel */}
          <div id="panel-seq">
            <div className="card">
              <div className="card-lbl-row">
                <span className="card-lbl">বর্তমান পাঠ</span>
                <span className="text-xs" id="seq-label">বর্ণমালা নম্বর ১</span>
              </div>
              <div className="char-display">
                <div className="char-bn" id="seq-char">অ</div>
                <div className="char-sub" id="seq-name">স্বরবর্ণ</div>
                <div className="text-xs hidden" id="seq-prefix" style={{ color: "var(--amber)", marginTop: 4 }}></div>
              </div>
              <div className="center" id="seq-dots"></div>
              <div className="badge-row">
                <div className="badge green hidden" id="seq-match-badge">✓ সঠিক ইনপুট (ESP32)</div>
                <button className="badge amber" id="btn-seq-play" type="button">🔊 উচ্চারণ শুনুন</button>
              </div>
            </div>

            <div className="result-panel hidden" id="seq-result">
              <div className="result-top">
                <span className="action-badge wait" id="seq-action">—</span>
                <span className="conf-text" id="seq-conf"></span>
              </div>
              <div className="hint-line hidden" id="seq-hint"></div>
              <div className="match-line hidden" id="seq-match-line"></div>
              <div className="dots-row hidden" id="seq-dots-cmp">
                <div><div className="dots-lbl">দেওয়া</div><div id="seq-dots-ent"></div></div>
                <div><div className="dots-lbl">সঠিক</div><div id="seq-dots-exp"></div></div>
              </div>
            </div>

            <div className="card">
              <div className="prog-row">
                <span id="seq-progress">অগ্রগতি: ১/৫০</span>
                <span id="seq-pct">২%</span>
              </div>
              <div className="prog-bg"><div className="prog-fill" id="seq-bar" style={{ width: "2%" }}></div></div>
            </div>

            <div className="btn-row">
              <button className="btn outline" id="btn-seq-prev" type="button">← আগে</button>
              <button className="btn outline" id="btn-seq-auto" type="button">⚡ অটো</button>
              <button className="btn outline" id="btn-seq-next" type="button">পরে →</button>
            </div>
            <button className="btn primary" id="btn-seq-teach" type="button">▶ পাঠদান শুরু করুন</button>
            <button className="btn danger" id="btn-seq-stop" type="button">✕ পাঠদান থামান</button>

            <div className="warn-card">
              <div className="warn-title">ℹ️ শুধু হার্ডওয়্যার ইনপুট</div>
              <div className="warn-body">ছাত্র ESP32-এর পুশ বাটনে ডট চাপবে এবং SUBMIT চাপবে। ওয়েব থেকে কোনো ইনপুট দেওয়ার সুযোগ নেই।</div>
            </div>
          </div>

          {/* Random panel */}
          <div id="panel-rnd" className="hidden">
            <div className="sel-card hidden" id="rnd-sel-card">
              <div className="sel-char" id="rnd-char">ক</div>
              <div className="sel-info">
                <div className="sel-info-lbl">নির্বাচিত বর্ণ</div>
                <div className="sel-info-name" id="rnd-name">ব্যঞ্জনবর্ণ</div>
              </div>
              <button className="badge amber" id="btn-rnd-play" type="button">🔊</button>
            </div>

            <div className="result-panel hidden" id="rnd-result">
              <div className="result-top">
                <span className="action-badge wait" id="rnd-action">অপেক্ষায়...</span>
                <span className="conf-text" id="rnd-conf"></span>
              </div>
              <div className="hint-line hidden" id="rnd-hint"></div>
              <div className="dots-row hidden" id="rnd-dots-cmp">
                <div><div className="dots-lbl">দেওয়া</div><div id="rnd-dots-ent"></div></div>
                <div><div className="dots-lbl">সঠিক</div><div id="rnd-dots-exp"></div></div>
              </div>
            </div>

            <div className="cat-tabs" id="rnd-cat-tabs">
              <button className="cat-tab active" data-cat="all" type="button">সব (৫০)</button>
              <button className="cat-tab" data-cat="vowel" type="button">স্বরবর্ণ (১১)</button>
              <button className="cat-tab" data-cat="consonant" type="button">ব্যঞ্জনবর্ণ (৩৯)</button>
            </div>
            <div className="letter-grid" id="rnd-grid"></div>
          </div>
        </div>

        {/* ████ TEST SELECT SCREEN ████ */}
        <div id="screen-test-select" className="screen">
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
          <button className="btn outline" id="btn-res-home" type="button">হোমে ফিরে যান</button>
        </div>
      </main>

      {/* ══════════════ BOTTOM NAV ══════════════ */}
      <nav className="bottom-nav">
        <button className="nav-btn" id="nav-dash" type="button">
          <span className="nav-icon">⊞</span><span className="nav-lbl">ড্যাশবোর্ড</span>
        </button>
        <button className="nav-btn active" id="nav-learn" type="button">
          <span className="nav-icon">📖</span><span className="nav-lbl">শেখানো</span>
        </button>
        <button className="nav-btn" id="nav-test" type="button">
          <span className="nav-icon">📝</span><span className="nav-lbl">পরীক্ষা</span>
        </button>
        <Link href="/" className="nav-btn" id="nav-info">
          <span className="nav-icon">ℹ️</span><span className="nav-lbl">নির্দেশনা</span>
        </Link>
      </nav>

      <div className="toast" id="toast"></div>
    </div>
  );
}
