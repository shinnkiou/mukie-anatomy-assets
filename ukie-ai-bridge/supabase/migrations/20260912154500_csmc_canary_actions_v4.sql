-- Isolated CSMC canary action expansion only.
-- Production worker/job tables and production claim RPC are untouched.

alter table public.ukie_csmc_observer_jobs
  drop constraint if exists ukie_csmc_observer_jobs_action_check;

alter table public.ukie_csmc_observer_jobs
  add constraint ukie_csmc_observer_jobs_action_check
  check (action = any (array[
    'csmc_observer_capture'::text,
    'csmc_observer_diagnose_v1'::text,
    'csmc_artifact_upload'::text
  ]));
