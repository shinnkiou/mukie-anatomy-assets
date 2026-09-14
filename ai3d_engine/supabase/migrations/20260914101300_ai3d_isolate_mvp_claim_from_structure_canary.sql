-- NEVER TEAR AI3D-013 routing fix.
-- Root cause: the legacy MVP claim RPC could claim any queued AI3D action.
-- This allowed an older MVP worker to consume the Structure CANARY before the
-- isolated ai3d_structure_module_v1 worker could claim it.
-- Preserve the legacy endpoint, but fail closed to the physical MVP action only.

create or replace function public.ai3d_claim_next_worker_job(
  p_device_key text,
  p_lease_owner text,
  p_lease_seconds integer default 120
)
returns setof public.ai3d_worker_jobs
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_id uuid;
begin
  if p_device_key is null or length(trim(p_device_key)) < 8 then
    raise exception 'AI3D_DEVICE_KEY_INVALID';
  end if;
  if p_lease_owner is null or length(trim(p_lease_owner)) < 8 then
    raise exception 'AI3D_LEASE_OWNER_INVALID';
  end if;
  if p_lease_seconds < 30 or p_lease_seconds > 300 then
    raise exception 'AI3D_LEASE_SECONDS_INVALID';
  end if;

  select j.id into v_id
  from public.ai3d_worker_jobs j
  where j.action = 'ai3d_blender_physical_mvp_v1'
    and j.contract_version = 'never-tear-ai3d-worker-v1'
    and j.attempt_count < j.max_attempts
    and (
      j.status = 'QUEUED'
      or (j.status in ('CLAIMED','RUNNING') and j.lease_until is not null and j.lease_until < now())
    )
  order by
    case when j.status = 'QUEUED' then 0 else 1 end,
    j.queued_at,
    j.created_at
  for update skip locked
  limit 1;

  if v_id is null then
    return;
  end if;

  update public.ai3d_worker_jobs
  set status = 'CLAIMED',
      device_key = p_device_key,
      attempt_count = attempt_count + 1,
      lease_owner = p_lease_owner,
      lease_until = now() + make_interval(secs => p_lease_seconds),
      started_at = coalesce(started_at, now()),
      updated_at = now(),
      error_code = null,
      error_detail = '{}'::jsonb
  where id = v_id;

  insert into public.ai3d_worker_events(job_id, event_type, status, device_key, detail)
  select id, 'CLAIM', status, device_key,
         jsonb_build_object(
           'lease_owner', lease_owner,
           'lease_until', lease_until,
           'attempt_count', attempt_count
         )
  from public.ai3d_worker_jobs
  where id = v_id;

  return query
  select * from public.ai3d_worker_jobs where id = v_id;
end;
$$;

revoke all on function public.ai3d_claim_next_worker_job(text, text, integer)
  from public, anon, authenticated;
grant execute on function public.ai3d_claim_next_worker_job(text, text, integer)
  to service_role;

comment on function public.ai3d_claim_next_worker_job(text, text, integer) is
  'Legacy AI3D MVP claim path; fail-closed to ai3d_blender_physical_mvp_v1 only. Structure CANARY jobs must use ai3d_claim_structure_canary_job.';
