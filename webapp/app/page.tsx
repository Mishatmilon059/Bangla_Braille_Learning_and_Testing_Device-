"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { loadRoster } from "./students/studentsApp";

export default function HomePage() {
  const [roster, setRoster] = useState<any[] | null>(null);
  useEffect(() => {
    loadRoster().then(setRoster);
  }, []);

  const top5 = roster ? roster.slice(0, 5) : [];

  return (
    <div className="home-screen">
      <div className="home-container">
        {/* Brand / Logo Section */}
        <header className="home-header">
          <div className="home-brand">
            <div className="home-logo-box">
              <div className="home-dots6">
                <span className="on"></span><span></span>
                <span className="on"></span><span className="on"></span>
                <span></span><span className="on"></span>
              </div>
            </div>
            <div className="home-brand-text">
              <h1>বাংলা ব্রেইল টিউটর</h1>
              <p>Bangla Braille Learning & Testing Device System</p>
            </div>
          </div>
        </header>

        {/* Hero Welcome Card */}
        <div className="home-hero-card">
          <div className="hero-content">
            <h2>বাংলা ব্রেইল কী?</h2>
            <ul className="home-feature-list">
              <li>৬-ডট সেল পদ্ধতি — প্রতিটি অক্ষর সর্বোচ্চ ৬টি ডটের সমন্বয়ে গঠিত</li>
              <li>মোট ৫০টি মূল অক্ষর — ১১টি স্বরবর্ণ ও ৩৯টি ব্যঞ্জনবর্ণ/চিহ্ন</li>
              <li>কিছু অক্ষর (যেমন ঋ, ৎ) দুই-ধাপে শেখানো হয় — একটি নির্দেশক ডট, তারপর মূল প্যাটার্ন</li>
              <li>স্পর্শ (ভাইব্রেশন) ও শ্রবণ (অডিও) — দুই মাধ্যমেই শেখার সুযোগ</li>
            </ul>
          </div>
        </div>

        {/* Overview dashboard -- so a teacher opening the app sees the class
            state immediately, without having to go into "শিক্ষার্থী" first. */}
        {roster && roster.length > 0 && (
          <Link href="/students" className="home-overview-card">
            <div className="home-overview-hdr">
              <h3>শ্রেণির ওভারভিউ</h3>
              <span className="home-overview-more">বিস্তারিত দেখুন →</span>
            </div>
            <div className="home-overview-stats">
              <div className="ho-stat">
                <div className="ho-v">{roster.length}</div>
                <div className="ho-l">শিক্ষার্থী</div>
              </div>
              <div className="ho-stat">
                <div className="ho-v">{roster.reduce((a, s) => a + s.total, 0)}</div>
                <div className="ho-l">মোট attempt</div>
              </div>
              <div className="ho-stat">
                <div className="ho-v">
                  {Math.round((roster.reduce((a, s) => a + s.accuracy, 0) / roster.length) * 100)}%
                </div>
                <div className="ho-l">গড় নির্ভুলতা</div>
              </div>
            </div>
            <div className="home-rank-col">
              <div className="home-rank-col-hdr top">শীর্ষ ৫</div>
              {top5.map((s, i) => (
                <div className="home-rank-row" key={s.studentId}>
                  <span className="hr-i">{i + 1}</span>
                  <span className="hr-id">{s.studentId}</span>
                  <span className="hr-pct top">{Math.round(s.accuracy * 100)}%</span>
                </div>
              ))}
            </div>
          </Link>
        )}

        {/* Project credit */}
        <div className="home-credit-card">
          <p>This app is developed for the EEE 416 course by:</p>
          <div className="home-credit-names">
            <span>Mishat Hasan Milon</span>
            <span>Khalid Mehebub</span>
            <span>Md. Adib Hasan Audhi</span>
            <span>Santu Nag</span>
          </div>
        </div>
      </div>
    </div>
  );
}
