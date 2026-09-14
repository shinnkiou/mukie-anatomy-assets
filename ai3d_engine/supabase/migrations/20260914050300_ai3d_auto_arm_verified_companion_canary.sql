-- NEVER TEAR AI3D
-- Applied to Supabase project vbuokbwglauibabinaqs as migration
-- 20260914050300 / ai3d_auto_arm_verified_companion_canary
--
-- Purpose: queue exactly one AI3D-002 physical CANARY only after the
-- separate verified companion writes fresh AI3D capability telemetry.
-- The legacy UKIE worker is intentionally ineligible.

create schema if not exists ai3d_internal;

revoke all on schema ai3d_internal from public;
revoke all on schema ai3d_internal from anon;
revoke all on schema ai3d_internal from authenticated;
grant usage on schema ai3d_internal to service_role;

create or replace function ai3d_internal.arm_ai3d002_canary_on_verified_companion()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public, ai3d_internal
as $$
declare
  v_ai3d_worker_version text;
  v_ai3d_contract_version text;
  v_ai3d_last_seen timestamptz;
  v_caps jsonb;
  v_job_id uuid;
begin
  if new.status <> 'ACTIVE' then return new; end if;

  v_ai3d_worker_version := coalesce(new.metadata->>'ai3d_worker_version', '');
  v_ai3d_contract_version := coalesce(new.metadata->>'ai3d_contract_version', '');
  v_caps := coalesce(new.metadata->'ai3d_capabilities', '[]'::jsonb);

  begin
    v_ai3d_last_seen := nullif(new.metadata->>'ai3d_last_seen', '')::timestamptz;
  exception when others then
    return new;
  end;

  if v_ai3d_worker_version <> '0.1.0-ai3d-canary' then return new; end if;
  if v_ai3d_contract_version <> 'never-tear-ai3d-worker-v1' then return new; end if;
  if jsonb_typeof(v_caps) <> 'array' or not (v_caps ? 'ai3d_blender_physical_mvp_v1') then return new; end if;
  if v_ai3d_last_seen is null or new.last_seen is null then return new; end if;
  if v_ai3d_last_seen < now() - interval '90 seconds' or new.last_seen < now() - interval '90 seconds' then return new; end if;
  if abs(extract(epoch from (new.last_seen - v_ai3d_last_seen))) > 5 then return new; end if;

  insert into public.ai3d_worker_jobs(
    job_key, command_id, project_key, task_id, action, contract_version,
    status, input, device_key, max_attempts
  ) values (
    'AI3D-002-PHYSICAL-CANARY-001',
    'AI3D-002-CANARY-001-NEVER-TEAR',
    'never_tear_ai3d_engine',
    'AI3D-002',
    'ai3d_blender_physical_mvp_v1',
    'never-tear-ai3d-worker-v1',
    'QUEUED',
    jsonb_build_object(
      'object', jsonb_build_object(
        'name', 'MVP_Physical_Box', 'kind', 'box',
        'size', jsonb_build_array(1.8, 1.2, 1.4),
        'position', jsonb_build_array(1.0, 0.6, -2.0),
        'rotation', jsonb_build_array(0.0, 0.35, 0.0),
        'material', jsonb_build_object('color_srgb', '#7c8792', 'roughness', 0.42, 'metallic', 0.12)
      ),
      'camera', jsonb_build_object(
        'position', jsonb_build_array(6.5, 4.2, 7.5),
        'target', jsonb_build_array(1.0, 0.6, -2.0),
        'lens_mm', 50
      ),
      'render', jsonb_build_object(
        'width', 960, 'height', 540,
        'engine', 'BLENDER_EEVEE_NEXT',
        'output_format', 'PNG', 'color_mode', 'RGBA'
      )
    ),
    new.device_key,
    1
  )
  on conflict (job_key) do nothing
  returning id into v_job_id;

  if v_job_id is not null then
    insert into public.ai3d_worker_events(job_id, event_type, status, device_key, detail)
    values (
      v_job_id, 'AUTO_ARMED_ON_VERIFIED_COMPANION', 'QUEUED', new.device_key,
      jsonb_build_object(
        'ai3d_worker_version', v_ai3d_worker_version,
        'ai3d_contract_version', v_ai3d_contract_version,
        'capability', 'ai3d_blender_physical_mvp_v1',
        'source', 'ukie_worker_devices_verified_companion_heartbeat',
        'max_attempts', 1
      )
    );

    update public.ai3d_tasks
    set qa_summary = coalesce(qa_summary, '{}'::jsonb) || jsonb_build_object(
          'auto_arm_gate', 'QUEUED_ONE_CANARY_ON_VERIFIED_COMPANION',
          'auto_arm_job_id', v_job_id,
          'auto_arm_device_key', new.device_key,
          'auto_arm_worker_version', v_ai3d_worker_version,
          'auto_arm_contract_version', v_ai3d_contract_version,
          'auto_arm_trigger', 'ai3d_auto_arm_verified_companion_canary'
        ),
        next_action = 'Verified AI3D companion heartbeat auto-queued exactly one AI3D-002 physical CANARY. Observe claim/lease/heartbeat, durable PNG readback, automated QA, then perform visual QA before any promotion.',
        updated_at = now()
    where task_id = 'AI3D-002';

    update public.ai3d_projects
    set next_action = 'AI3D-002 verified companion detected and exactly one physical CANARY queued automatically. Observe physical evidence and visual QA; never promote from automated QA alone.',
        metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
          'ai3d002_auto_arm', 'QUEUED',
          'ai3d002_auto_arm_job_id', v_job_id,
          'ai3d002_auto_arm_device_key', new.device_key,
          'ai3d002_auto_arm_worker_version', v_ai3d_worker_version
        ),
        updated_at = now()
    where project_key = 'never_tear_ai3d_engine';
  end if;

  return new;
exception when others then
  return new;
end;
$$;

revoke all on function ai3d_internal.arm_ai3d002_canary_on_verified_companion() from public;
revoke all on function ai3d_internal.arm_ai3d002_canary_on_verified_companion() from anon;
revoke all on function ai3d_internal.arm_ai3d002_canary_on_verified_companion() from authenticated;
grant execute on function ai3d_internal.arm_ai3d002_canary_on_verified_companion() to service_role;

create trigger trg_ai3d002_auto_arm_verified_companion
after update of metadata, last_seen, status on public.ukie_worker_devices
for each row
execute function ai3d_internal.arm_ai3d002_canary_on_verified_companion();
