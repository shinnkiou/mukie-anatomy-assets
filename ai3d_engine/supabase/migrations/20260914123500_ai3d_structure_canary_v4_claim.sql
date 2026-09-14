-- NEVER TEAR AI3D-013: exact claim path for v0.2.3 / CANARY-004.
-- This remains isolated from the MVP queue and all production Structure jobs.

create or replace function public.ai3d_claim_structure_canary_job_v4(
  p_device_key text,
  p_lease_owner text,
  p_lease_seconds integer default 180
)
returns setof public.ai3d_worker_jobs
language plpgsql
security invoker
as $$
declare
  v_job_id uuid;
  v_now timestamptz := now();
  v_lease_seconds integer := greatest(30, least(coalesce(p_lease_seconds, 180), 300));
begin
  if p_device_key is null or length(p_device_key) < 8 then
    raise exception 'invalid device key';
  end if;
  if p_lease_owner is null or length(p_lease_owner) < 8 then
    raise exception 'invalid lease owner';
  end if;

  select j.id into v_job_id
  from public.ai3d_worker_jobs j
  where j.status = 'QUEUED'
    and j.action = 'ai3d_structure_module_v1'
    and j.project_key = 'never_tear_ai3d_engine'
    and j.task_id = 'AI3D-013'
    and j.job_key = 'AI3D-013-PHYSICAL-STRUCTURE-CANARY-004'
    and j.command_id = 'AI3D-013-STRUCTURE-CANARY-004-NEVER-TEAR'
    and j.contract_version = 'never-tear-ai3d-worker-v1'
    and j.max_attempts = 1
    and j.attempt_count < j.max_attempts
  order by j.queued_at, j.created_at
  for update skip locked
  limit 1;

  if v_job_id is null then
    return;
  end if;

  update public.ai3d_worker_jobs
  set status = 'RUNNING',
      device_key = p_device_key,
      lease_owner = p_lease_owner,
      lease_until = v_now + make_interval(secs => v_lease_seconds),
      attempt_count = attempt_count + 1,
      started_at = coalesce(started_at, v_now),
      updated_at = v_now,
      error_code = null,
      error_detail = '{}'::jsonb
  where id = v_job_id;

  insert into public.ai3d_worker_events(job_id,event_type,status,device_key,detail)
  values(
    v_job_id,
    'STRUCTURE_CANARY_V4_CLAIMED',
    'RUNNING',
    p_device_key,
    jsonb_build_object('lease_owner',p_lease_owner,'lease_seconds',v_lease_seconds)
  );

  return query
  select j.* from public.ai3d_worker_jobs j where j.id = v_job_id;
end;
$$;

revoke execute on function public.ai3d_claim_structure_canary_job_v4(text,text,integer) from public, anon, authenticated;
grant execute on function public.ai3d_claim_structure_canary_job_v4(text,text,integer) to service_role;
