// Supabase connection for the data-collection app.
//
// The key below is the PUBLISHABLE key. It is designed to ship in every client
// and is safe in git -- it grants only what supabase/full_setup.sql's RLS
// policies allow (insert/select on attempts, remote_commands; full anon
// read-write on student_weaknesses/test_sessions for the teacher panel).
//
// NEVER put the secret / service_role key here. That key bypasses RLS
// completely, and this file ships to every browser that opens the app.
//
// NEXT_PUBLIC_* env vars let you override these per-deployment without
// touching source; both fall back to the values already used by web/config.js
// so the app works out of the box with zero setup, matching that app's
// zero-config philosophy.

export const SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL || "https://rufaacgatrebsyxnyfbq.supabase.co";
export const SUPABASE_ANON_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-";

// Identifies which machine a row came from, so you can tell devices apart in
// the merged dataset. Auto-generated and remembered per browser.
export const DEVICE_ID_KEY = "braille.device_id";
