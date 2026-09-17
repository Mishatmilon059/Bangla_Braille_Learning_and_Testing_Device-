-- Migration 001: Teacher panel supporting tables
-- Run in Supabase SQL editor (Dashboard → SQL Editor)

-- Remote commands: teacher → ESP32 (letter to play, mode)
CREATE TABLE IF NOT EXISTS public.remote_commands (
  id          bigserial PRIMARY KEY,
  device_id   text NOT NULL,
  letter_id   integer NOT NULL,
  command     text NOT NULL DEFAULT 'play', -- 'play' | 'test' (no motors)
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- Student weakness tracking: built up from test results
CREATE TABLE IF NOT EXISTS public.student_weaknesses (
  id            bigserial PRIMARY KEY,
  student_id    text NOT NULL,
  char_id       integer NOT NULL,
  wrong_count   integer NOT NULL DEFAULT 0,
  correct_count integer NOT NULL DEFAULT 0,
  last_tested   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (student_id, char_id)
);

-- Test sessions: full result record per test run
CREATE TABLE IF NOT EXISTS public.test_sessions (
  id          bigserial PRIMARY KEY,
  student_id  text NOT NULL,
  teacher_id  text,
  letter_ids  jsonb NOT NULL,  -- array of char_ids tested
  results     jsonb NOT NULL,  -- [{char_id, is_correct, response_time}]
  total       integer NOT NULL,
  correct     integer NOT NULL,
  wrong       integer NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- RLS: allow anon read/write (same pattern as attempts table)
ALTER TABLE public.remote_commands    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_weaknesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.test_sessions      ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_rw_remote_commands"    ON public.remote_commands
  FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_rw_student_weaknesses" ON public.student_weaknesses
  FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_rw_test_sessions"      ON public.test_sessions
  FOR ALL TO anon USING (true) WITH CHECK (true);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_remote_commands_device   ON public.remote_commands (device_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_student_weaknesses_sid   ON public.student_weaknesses (student_id, wrong_count DESC);
CREATE INDEX IF NOT EXISTS idx_test_sessions_student    ON public.test_sessions (student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_attempts_session_start   ON public.attempts (created_at DESC);
