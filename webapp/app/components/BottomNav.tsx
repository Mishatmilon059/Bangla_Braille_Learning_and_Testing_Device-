"use client";

// Shared bottom navigation so every page in the app is reachable from every
// other page. White/green, matching the rest of the app's theme -- no emoji,
// simple line icons instead.
import { Suspense } from "react";
import { usePathname, useRouter } from "next/navigation";

function IconHome() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5.5 10v9a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-9" />
    </svg>
  );
}
function IconBook() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 5.5A2 2 0 0 1 6 4h5v16H6a2 2 0 0 0-2 1.5V5.5Z" />
      <path d="M20 5.5A2 2 0 0 0 18 4h-5v16h5a2 2 0 0 1 2 1.5V5.5Z" />
    </svg>
  );
}
function IconTeacher() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="3.2" />
      <path d="M5 20c0-3.6 3.1-6.5 7-6.5s7 2.9 7 6.5" />
      <path d="m9.5 15.5 2 2 3.5-4" />
    </svg>
  );
}
function IconStudents() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 19c0-3 2.5-5.4 5.5-5.4S14.5 16 14.5 19" />
      <circle cx="17" cy="9" r="2.3" />
      <path d="M15.8 13.2c2.4.3 4.2 2.3 4.2 4.8" />
    </svg>
  );
}
function IconData() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 6v12c0 1.1 3.1 2 7 2s7-.9 7-2V6" />
      <path d="M5 6c0 1.1 3.1 2 7 2s7-.9 7-2-3.1-2-7-2-7 .9-7 2Z" />
      <path d="M5 12c0 1.1 3.1 2 7 2s7-.9 7-2" />
    </svg>
  );
}

const ITEMS = [
  { href: "/", Icon: IconHome, label: "হোম" },
  { href: "/learn", Icon: IconBook, label: "শেখা" },
  { href: "/teacher", Icon: IconTeacher, label: "পরীক্ষা দাও" },
  { href: "/students", Icon: IconStudents, label: "শিক্ষার্থী" },
  { href: "/data-collection", Icon: IconData, label: "ডেটা" },
];

export default function BottomNav() {
  return (
    <Suspense fallback={null}>
      <BottomNavInner />
    </Suspense>
  );
}

function BottomNavInner() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <nav className="global-bottom-nav">
      {ITEMS.map(({ href, Icon, label }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <button
            key={href}
            type="button"
            className={`gbn-item${active ? " active" : ""}`}
            onClick={() => router.push(href)}
          >
            <Icon />
            <span className="gbn-label">{label}</span>
          </button>
        );
      })}
    </nav>
  );
}
