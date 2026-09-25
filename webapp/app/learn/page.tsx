"use client";

import { useEffect } from "react";
import { startLearnScreenApp } from "./learnScreenApp";

// The "শেখা" tab: a live hardware teaching session. Moved out of the
// teacher panel's old "শেখানো" tab so this nav item does exactly one thing
// (teach), separate from "শিক্ষক" (which now only runs exams).
export default function LearnScreenPage() {
  useEffect(() => {
    const cleanup = startLearnScreenApp();
    return cleanup;
  }, []);

  return (
    <div className="teacher-app">
      {/* ══════════════ HEADER ══════════════ */}
      <header className="app-hdr">
        <div className="hdr1">
          <button className="btn-back" id="btn-back" type="button">←</button>
          <span className="hdr-title" id="hdr-title">সহজ পাঠ</span>
          <div className="esp-badge off" id="esp-badge">
            <div className="esp-dot off" id="esp-dot"></div>
            <span id="esp-label">ESP32 খুঁজছে...</span>
          </div>
        </div>
        <div className="hdr2" id="hdr-sub">ছাত্র: S01 • বর্ণমালা শিক্ষা</div>
        <div className="student-switch">
          <span className="student-switch-lbl">সক্রিয় ছাত্র:</span>
          <span className="student-switch-id" id="student-id-label">S01</span>
          <button className="student-switch-btn" id="btn-change-student" type="button">পরিবর্তন</button>
        </div>
      </header>

      <main className="main">
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
            <div className="card hidden" id="rnd-sel-card">
              <div className="card-lbl-row">
                <span className="card-lbl">নির্বাচিত বর্ণ</span>
                <span className="text-xs" id="rnd-label">এলোমেলো মোড</span>
              </div>
              <div className="char-display">
                <div className="char-bn" id="rnd-char">ক</div>
                <div className="char-sub" id="rnd-name">ব্যঞ্জনবর্ণ</div>
                <div className="text-xs hidden" id="rnd-prefix" style={{ color: "var(--amber)", marginTop: 4 }}></div>
              </div>
              <div className="center" id="rnd-dots"></div>
              <div className="badge-row">
                <div className="badge green hidden" id="rnd-match-badge">✓ সঠিক ইনপুট (ESP32)</div>
                <button className="badge amber hidden" id="btn-rnd-play" type="button">🔊 আবার শোনান</button>
              </div>
              <div className="btn-row" style={{ marginTop: 14 }}>
                <button className="btn primary" id="btn-rnd-teach" type="button">▶ শেখান</button>
                <button className="btn danger" id="btn-rnd-stop" type="button">✕ থামান</button>
              </div>
            </div>

            <div className="result-panel hidden" id="rnd-result">
              <div className="result-top">
                <span className="action-badge wait" id="rnd-action">—</span>
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
      </main>

      <div className="toast" id="toast"></div>
    </div>
  );
}
