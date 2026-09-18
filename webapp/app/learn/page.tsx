"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { startLearnApp } from "./learnApp";

export default function LearnPage() {
  const [bootGen, setBootGen] = useState(0);

  useEffect(() => {
    // Guards React StrictMode's dev double-invoke from double-booting the
    // app (double KeyPad/AttemptLogger construction would double-register
    // listeners). Each real bootGen change still gets a fresh mount.
    const cleanup = startLearnApp({ rerun: () => setBootGen((g) => g + 1) });
    return cleanup;
  }, [bootGen]);

  return (
    <div className="dark-app">
      <div className="wrap">
        <header>
          <Link href="/" style={{ display: "inline-flex", alignItems: "center", textDecoration: "none" }}>
            <h1>বাংলা ব্রেইল</h1>
          </Link>
          <span className="grow"></span>
          <div className="user-badge" id="userBadge">
            <div className="avatar" id="userAvatar"></div>
            <div>
              <div className="uname" id="userName"></div>
              <div className="uid" id="userIdDisplay"></div>
            </div>
            <button className="ghost" id="changeProfileBtn" type="button">পরিবর্তন</button>
          </div>
          <span className="sync-status" id="syncStatus">not started</span>
        </header>

        {/* ---------------- setup ---------------- */}
        <div className="panel" id="setup">
          <h2>অনুশীলন শুরু করুন</h2>
          <div className="row">
            <div>
              <label htmlFor="mode">মোড</label>
              <select id="mode" defaultValue="normal">
                <option value="normal">স্বাভাবিক</option>
                <option value="targeted">লক্ষ্যভিত্তিক</option>
                <option value="review">পুনরালোচনা</option>
              </select>
            </div>
            <div>
              <label htmlFor="setLen">প্রতি সেশনে attempts</label>
              <input id="setLen" type="number" defaultValue={20} min={5} max={100} />
            </div>
            <div>
              <label htmlFor="charSet">অক্ষর সেট</label>
              <select id="charSet" defaultValue="all">
                <option value="vowels">স্বরবর্ণ (১১)</option>
                <option value="all">সব অক্ষর (৫০)</option>
                <option value="consonants">ব্যঞ্জনবর্ণ (৩৯)</option>
              </select>
            </div>
          </div>
          <div className="actions">
            <button id="startBtn" type="button">▶ সেশন শুরু করো</button>
            <button id="exportBtn" className="ghost" type="button">CSV ডাউনলোড</button>
            <button id="flushBtn" className="ghost" type="button">Sync করো</button>
            <button id="resetBtn" className="ghost" type="button">রিসেট</button>
          </div>
          <p className="note" id="modeNote"></p>
        </div>

        {/* ---------------- practice ---------------- */}
        <div className="panel" id="practice">
          <h2>Attempt <span id="attemptNo">1</span> / <span id="attemptTotal">20</span>
            &nbsp;·&nbsp; difficulty <span id="diffLevel">1</span></h2>

          <div className="stage">
            <div className="left">
              <div className="prompt-char" id="promptChar">?</div>
              <div className="prompt-name" id="promptName">শুনুন ও লিখুন</div>
              <div className="cell" id="cell">
                <div className="dot" data-dot="1">1</div><div className="dot" data-dot="4">4</div>
                <div className="dot" data-dot="2">2</div><div className="dot" data-dot="5">5</div>
                <div className="dot" data-dot="3">3</div><div className="dot" data-dot="6">6</div>
              </div>
              <div className="actions" style={{ justifyContent: "center" }}>
                <button id="replayBtn" className="ghost" type="button">🔊 আবার শুনুন</button>
              </div>
            </div>

            <div className="right">
              <div className="keys">
                <div className="key" data-dot="1">Dot 1<span className="kb">F / Num 7</span></div>
                <div className="key" data-dot="4">Dot 4<span className="kb">J / Num 8</span></div>
                <div className="key" data-dot="2">Dot 2<span className="kb">D / Num 4</span></div>
                <div className="key" data-dot="5">Dot 5<span className="kb">K / Num 5</span></div>
                <div className="key" data-dot="3">Dot 3<span className="kb">S / Num 1</span></div>
                <div className="key" data-dot="6">Dot 6<span className="kb">L / Num 2</span></div>
              </div>

              <div className="actions">
                <button id="submitBtn" type="button">Submit <span className="mono" style={{ opacity: 0.8 }}>↵</span></button>
                <button id="clearBtn" className="ghost" type="button">Clear <span className="mono" style={{ opacity: 0.8 }}>esc</span></button>
                <button id="hintBtn" className="ghost" type="button">Hint <span className="mono" style={{ opacity: 0.8 }}>H</span></button>
                <button id="stopBtn" className="ghost" type="button">সেশন শেষ করো</button>
              </div>

              <div className="hint-box" id="hintBox"></div>
              <div className="feedback" id="feedback"></div>
            </div>
          </div>
        </div>

        {/* ---------------- live stats ---------------- */}
        <div className="panel">
          <h2>অগ্রগতি</h2>
          <div className="stats">
            <div className="stat"><div className="v" id="stRows">0</div><div className="k">মোট attempt</div></div>
            <div className="stat"><div className="v" id="stAcc">—</div><div className="k">নির্ভুলতা</div></div>
            <div className="stat"><div className="v" id="stSess">0</div><div className="k">সেশন</div></div>
            <div className="stat"><div className="v" id="stDays">0</div><div className="k">দিন</div></div>
            <div className="stat"><div className="v" id="stChars">0</div><div className="k">অক্ষর দেখা</div></div>
            <div className="stat"><div className="v" id="stQueue">0</div><div className="k">sync বাকি</div></div>
          </div>
        </div>

        {/* ---------------- per-character mastery (collapsible) ---------------- */}
        <CollapsiblePanel title="অক্ষরভিত্তিক দক্ষতা">
          <div className="tbl-wrap">
            <table id="charTable">
              <thead><tr>
                <th>অক্ষর</th><th>নাম</th><th className="num">seen</th><th className="num">acc</th>
                <th style={{ width: 110 }}>mastery</th><th className="num">streak</th><th className="num">ভুল</th>
              </tr></thead>
              <tbody></tbody>
            </table>
          </div>
        </CollapsiblePanel>

        {/* ---------------- class balance (collapsible) ---------------- */}
        <CollapsiblePanel title="ডেটা ব্যালেন্স">
          <div className="row">
            <div className="tbl-wrap">
              <table id="taTable">
                <thead><tr><th>Teaching action</th><th className="num">rows</th><th style={{ width: 90 }}></th></tr></thead>
                <tbody></tbody>
              </table>
            </div>
            <div className="tbl-wrap">
              <table id="csTable">
                <thead><tr><th>Confidence state</th><th className="num">rows</th><th style={{ width: 90 }}></th></tr></thead>
                <tbody></tbody>
              </table>
            </div>
          </div>
        </CollapsiblePanel>
      </div>

      {/* ---------------- profile screen overlay ---------------- */}
      <div id="profileScreen" className="gate-screen hidden">
        <div className="gate-card">
          <div className="dots6">
            <span className="on"></span><span></span>
            <span className="on"></span><span className="on"></span>
            <span></span><span className="on"></span>
          </div>
          <h1>বাংলা ব্রেইল</h1>
          <p>অনুশীলন শুরু করার আগে আপনার তথ্য দিন</p>
          <div className="gate-field">
            <label htmlFor="profileName">আপনার নাম</label>
            <input id="profileName" placeholder="যেমন: রাহেলা" autoComplete="name" />
          </div>
          <div className="gate-field">
            <label htmlFor="profileId">আইডি</label>
            <input id="profileId" placeholder="যেমন: S01" autoComplete="off" style={{ textTransform: "uppercase" }} />
          </div>
          <button id="profileSaveBtn" type="button" style={{ width: "100%", marginTop: 8, padding: 14, fontSize: "1rem" }}>শুরু করো →</button>
        </div>
      </div>
    </div>
  );
}

function CollapsiblePanel({ title, children }: { title: string; children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(true);
  return (
    <div className="panel">
      <h2>
        {title}
        <button className="panel-toggle" type="button" onClick={() => setCollapsed((c) => !c)}>
          {collapsed ? "▾ দেখাও" : "▴ লুকাও"}
        </button>
      </h2>
      <div className="collapsible-body" style={{ maxHeight: collapsed ? 0 : 2000, overflow: "hidden", transition: "max-height 0.3s ease" }}>
        {children}
      </div>
    </div>
  );
}
