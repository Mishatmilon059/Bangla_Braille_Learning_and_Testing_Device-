"use client";

import Link from "next/link";

export default function HomePage() {
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
              <span className="home-badge">BUET EEE 416 • Group 08</span>
              <h1>বাংলা ব্রেইল টিউটর</h1>
              <p>Bangla Braille Learning & Testing Device System</p>
            </div>
          </div>
        </header>

        {/* Hero Welcome Card */}
        <div className="home-hero-card">
          <div className="hero-content">
            <h2>সহজ পদ্ধতিতে বাংলা ব্রেইল শিখুন ও মূল্যায়ন করুন</h2>
            <p>
              ৬-ডট হ্যাপটিক ভাইব্রেশন, সুস্পষ্ট কণ্ঠস্বর এবং ইন্টারেক্টিভ অনুশীলনের মাধ্যমে ব্রেইল চর্চা করার সম্পূর্ণ ব্যবস্থা। নিচের অপশন থেকে নির্বাচন করুন:
            </p>
          </div>

          {/* Navigation Choices */}
          <div className="home-grid">
            {/* Learn Option */}
            <Link href="/learn" className="home-card-link learn-card">
              <div className="card-top">
                <div className="card-icon-wrap green-grad">
                  <span className="card-icon">📖</span>
                </div>
                <span className="card-pill green">শিক্ষার্থী মোড</span>
              </div>
              <div className="card-body">
                <h3>ব্রেইল শেখা ও অনুশীলন</h3>
                <p>
                  বর্ণমালাভিত্তিক পাঠ, ৬-ডট কিপ্যাড ইনপুট, তাত্ক্ষণিক অডিও উচ্চারণ ও ভয়েস ফিডব্যাকের মাধ্যমে নিজে নিজে ব্রেইল শিখুন।
                </p>
              </div>
              <div className="card-footer">
                <span className="btn-action primary-btn">
                  অনুশীলন শুরু করুন
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </span>
              </div>
            </Link>

            {/* Teacher Option */}
            <Link href="/teacher" className="home-card-link teacher-card">
              <div className="card-top">
                <div className="card-icon-wrap emerald-outline">
                  <span className="card-icon">👩‍🏫</span>
                </div>
                <span className="card-pill amber">শিক্ষক প্যানেল</span>
              </div>
              <div className="card-body">
                <h3>ব্রেইল টেস্টিং ও মূল্যায়ন</h3>
                <p>
                  ESP32 হার্ডওয়্যার ডিভাইসের সাথে রিয়েল-টাইম সংযোগ, দূর থেকে পরীক্ষা পরিচালনা এবং শিক্ষার্থীদের দুর্বলতা ও স্কোর পর্যবেক্ষণ।
                </p>
              </div>
              <div className="card-footer">
                <span className="btn-action outline-btn">
                  শিক্ষক ড্যাশবোর্ড
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </span>
              </div>
            </Link>
          </div>

          {/* Feature Highlights Footer */}
          <div className="home-features">
            <div className="feature-item">
              <span className="feature-dot"></span>
              <span>৬-ডট হ্যাপটিক মোটর</span>
            </div>
            <div className="feature-item">
              <span className="feature-dot"></span>
              <span>স্বাভাবিক বাংলা অডিও</span>
            </div>
            <div className="feature-item">
              <span className="feature-dot"></span>
              <span>ESP32 ক্লাউড সিঙ্ক</span>
            </div>
            <div className="feature-item">
              <span className="feature-dot"></span>
              <span>অন-ডিভাইস AI মডেল</span>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <footer className="home-footer">
          <p>
            তত্ত্বাবধানে: ডিপার্টমেন্ট অব EEE, বাংলাদেশ প্রকৌশল বিশ্ববিদ্যালয় (BUET)
          </p>
        </footer>
      </div>
    </div>
  );
}
