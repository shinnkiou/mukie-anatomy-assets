create table if not exists public.ukie_csmc_observer_jobs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  device_key text not null,
  job_key text not null unique,
  action text not null default 'csmc_observer_capture' check (action = 'csmc_observer_capture'),
  status text not null default 'QUEUED' check (status = any (array['QUEUED'::text,'CLAIMED'::text,'COMPLETED'::text,'FAILED'::text,'TIMEOUT'::text])),
  attempt_no integer not null default 0 check (attempt_no >= 0),
  lease_owner text,
  lease_until timestamptz,
  result jsonb not null default '{}'::jsonb,
  error_code text,
  error_detail jsonb not null default '{}'::jsonb,
  requested_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  updated_at timestamptz not null default now()
);

alter table public.ukie_csmc_observer_jobs enable row level security;
revoke all on table public.ukie_csmc_observer_jobs from anon, authenticated;
grant select, insert, update, delete on table public.ukie_csmc_observer_jobs to service_role;

create index if not exists ukie_csmc_observer_jobs_claim_idx
  on public.ukie_csmc_observer_jobs (user_id, device_key, status, requested_at);

create or replace function public.ukie_claim_next_csmc_observer_job(
  p_user_id uuid,
  p_device_key text,
  p_lease_owner text,
  p_lease_seconds integer default 300
)
returns setof public.ukie_csmc_observer_jobs
language plpgsql
security definer
set search_path = ''
as $$
begin
  if p_lease_owner is null or length(p_lease_owner) < 8 then
    raise exception 'invalid lease owner';
  end if;

  return query
  update public.ukie_csmc_observer_jobs as j
     set status = 'CLAIMED',
         attempt_no = j.attempt_no + 1,
         lease_owner = p_lease_owner,
         lease_until = now() + make_interval(secs => least(greatest(p_lease_seconds, 30), 600)),
         started_at = coalesce(j.started_at, now()),
         updated_at = now()
   where j.id = (
     select q.id
       from public.ukie_csmc_observer_jobs as q
      where q.user_id = p_user_id
        and q.device_key = p_device_key
        and q.status = 'QUEUED'
      order by q.requested_at asc
      for update skip locked
      limit 1
   )
  returning j.*;
end;
$$;

revoke all on function public.ukie_claim_next_csmc_observer_job(uuid,text,text,integer) from public, anon, authenticated;
grant execute on function public.ukie_claim_next_csmc_observer_job(uuid,text,text,integer) to service_role;
