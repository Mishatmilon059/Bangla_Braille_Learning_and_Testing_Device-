-- =============================================================================
-- Bangla Braille Tutor — Full Supabase Setup
-- Run this ONCE in Supabase Dashboard → SQL Editor → New query → Run
-- Idempotent: safe to re-run if already partially applied.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- TABLE 1: attempts  (main data-collection table)
-- ---------------------------------------------------------------------------
create table if not exists attempts (
  id                bigserial primary key,
  created_at        timestamptz not null default now(),

  user_id           text        not null,
  session_id        text        not null,
  device_id         text        not null,
  attempt_index     integer     not null,

  char_id                   smallint         not null,
  response_time             double precision not null,
  press_duration            double precision not null,
  retry_count               smallint         not null,
  prev_accuracy             double precision not null,
  prev_mastery              double precision not null,
  hint_count                smallint         not null,
  session_number            smallint         not null,
  difficulty_level          smallint         not null,
  time_since_last_practice  double precision not null,
  prev_confidence           smallint         not null,
  current_streak            smallint         not null,
  wrong_streak              smallint         not null,
  prev_mistakes             smallint         not null,

  teaching_action   smallint    not null,
  confidence_state  smallint    not null,

  expected_pattern  smallint    not null,
  entered_pattern   smallint    not null,
  is_correct        boolean     not null,
  press_order       text,

  source              text     not null default 'web',
  is_synthetic        boolean  not null default false,
  spec_version        integer  not null default 1,
  braille_map_verified boolean not null default false,

  constraint attempts_char_id_range     check (char_id between 0 and 49),
  constraint attempts_confidence_range  check (confidence_state between 0 and 2),
  constraint attempts_difficulty_range  check (difficulty_level between 1 and 5),
  constraint attempts_source_valid      check (source in ('web','esp32','synthetic')),
  constraint attempts_streak_exclusive  check (current_streak = 0 or wrong_streak = 0)
);

-- teaching_action: migrate old 6-class values (3/4/5) to NORMAL_PRACTICE (2)
-- before tightening the constraint, so re-runs on existing data don't fail.
update attempts set teaching_action = 2 where teaching_action > 2;
alter table attempts drop constraint if exists attempts_teaching_range;
alter table attempts add constraint attempts_teaching_range
  check (teaching_action between 0 and 2);

create index if not exists attempts_user_session_idx on attempts (user_id, session_id);
create index if not exists attempts_created_idx      on attempts (created_at);
create index if not exists attempts_labels_idx       on attempts (teaching_action, confidence_state);
create index if not exists attempts_synthetic_idx    on attempts (is_synthetic);

create unique index if not exists attempts_dedupe_idx
  on attempts (session_id, attempt_index)
  where is_synthetic = false;

alter table attempts enable row level security;
drop policy if exists attempts_anon_insert on attempts;
create policy attempts_anon_insert on attempts for insert to anon with check (true);
drop policy if exists attempts_anon_select on attempts;
create policy attempts_anon_select on attempts for select to anon using (true);


-- ---------------------------------------------------------------------------
-- TABLE 2: remote_commands  (teacher panel → ESP32 via cloud)
-- ---------------------------------------------------------------------------
create table if not exists remote_commands (
  id          bigserial primary key,
  created_at  timestamptz not null default now(),
  device_id   text        not null,
  letter_id   smallint,
  dot         smallint,
  command     text        not null default 'play',

  constraint remote_commands_dot_range    check (dot is null or dot between 1 and 6),
  constraint remote_commands_letter_range check (letter_id is null or letter_id between 0 and 49)
);

-- If table already existed without the command column, add it
alter table remote_commands add column if not exists command text not null default 'play';
alter table remote_commands add column if not exists dot smallint;
alter table remote_commands add column if not exists letter_id smallint;

create index if not exists remote_commands_device_idx on remote_commands (device_id, id);

alter table remote_commands enable row level security;
drop policy if exists remote_commands_anon_insert on remote_commands;
create policy remote_commands_anon_insert on remote_commands for insert to anon with check (true);
drop policy if exists remote_commands_anon_select on remote_commands;
create policy remote_commands_anon_select on remote_commands for select to anon using (true);


-- ---------------------------------------------------------------------------
-- TABLE 3: student_weaknesses  (mastery tracking per student+char)
-- ---------------------------------------------------------------------------
create table if not exists student_weaknesses (
  id            bigserial primary key,
  student_id    text        not null,
  char_id       integer     not null,
  wrong_count   integer     not null default 0,
  correct_count integer     not null default 0,
  last_tested   timestamptz not null default now(),
  unique (student_id, char_id)
);

create index if not exists idx_student_weaknesses_sid
  on student_weaknesses (student_id, wrong_count desc);

alter table student_weaknesses enable row level security;
drop policy if exists anon_rw_student_weaknesses on student_weaknesses;
create policy anon_rw_student_weaknesses on student_weaknesses
  for all to anon using (true) with check (true);


-- ---------------------------------------------------------------------------
-- TABLE 4: test_sessions  (full result record per test run)
-- ---------------------------------------------------------------------------
create table if not exists test_sessions (
  id          bigserial primary key,
  student_id  text        not null,
  teacher_id  text,
  letter_ids  jsonb       not null,
  results     jsonb       not null,
  total       integer     not null,
  correct     integer     not null,
  wrong       integer     not null,
  created_at  timestamptz not null default now()
);

create index if not exists idx_test_sessions_student
  on test_sessions (student_id, created_at desc);

alter table test_sessions enable row level security;
drop policy if exists anon_rw_test_sessions on test_sessions;
create policy anon_rw_test_sessions on test_sessions
  for all to anon using (true) with check (true);


-- ---------------------------------------------------------------------------
-- VIEWS  (monitoring dashboards — check during data collection)
-- ---------------------------------------------------------------------------
create or replace view class_balance as
select 'teaching_action' as head, teaching_action as class_id,
       count(*) as total,
       count(*) filter (where not is_synthetic) as real_rows,
       count(*) filter (where is_synthetic) as synthetic_rows
from attempts group by teaching_action
union all
select 'confidence_state', confidence_state,
       count(*),
       count(*) filter (where not is_synthetic),
       count(*) filter (where is_synthetic)
from attempts group by confidence_state
order by head, class_id;

create or replace view participant_progress as
select user_id,
       count(*)                                     as attempts,
       count(distinct session_id)                   as sessions,
       count(distinct date(created_at))             as session_days,
       round(avg(case when is_correct then 1 else 0 end)::numeric, 3) as accuracy,
       count(distinct char_id)                      as chars_seen,
       min(created_at)                              as first_seen,
       max(created_at)                              as last_seen
from attempts where not is_synthetic
group by user_id order by attempts desc;

create or replace view character_difficulty as
select char_id,
       count(*)                                                        as attempts,
       round(avg(case when is_correct then 1 else 0 end)::numeric, 3) as accuracy,
       round(avg(response_time)::numeric, 0)                          as avg_response_ms,
       round(avg(retry_count)::numeric, 2)                            as avg_retries
from attempts where not is_synthetic
group by char_id order by accuracy asc;

create or replace view collection_summary as
select count(*)                                       as total_rows,
       count(*) filter (where not is_synthetic)       as real_rows,
       count(*) filter (where is_synthetic)           as synthetic_rows,
       count(distinct user_id) filter (where not is_synthetic) as participants,
       count(distinct session_id) filter (where not is_synthetic) as sessions,
       count(distinct date(created_at)) filter (where not is_synthetic) as collection_days,
       bool_and(braille_map_verified)                 as all_rows_verified_map
from attempts;
