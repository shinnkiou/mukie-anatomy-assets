from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import discord
    from discord import app_commands
    from discord.ext import commands
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "discord.py is not installed. Run INSTALL_DISCORD_SUPPORT.bat first."
    ) from exc

BASE = Path(__file__).resolve().parent
RUNTIME = BASE / "runtime"
JOBS = RUNTIME / "jobs"
CONFIG_PATH = BASE / "config" / "discord.local.json"
STOP_DISCORD = RUNTIME / "STOP_DISCORD"
DISCORD_HEARTBEAT = RUNTIME / "discord_heartbeat.json"
DISCORD_STATE = RUNTIME / "discord_state.json"
COMMAND_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,120}$")
FINAL_STATES = {"SUCCESS", "FAILED", "BLOCKED", "INCOMPLETE", "STOPPED"}
ACTIVE_STATES = {"QUEUED", "CLAIMED", "PREFLIGHT", "RUNNING", "PAUSING", "PAUSED", "STOPPING", "WAITING_APPROVAL"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(
            "Discord relay is not configured. Run CONFIGURE_DISCORD_RELAY.bat first."
        )
    raw = load_json(CONFIG_PATH)
    guild_id = raw.get("guild_id")
    if not isinstance(guild_id, int) or guild_id <= 0:
        raise RuntimeError("config/discord.local.json must contain a numeric guild_id")
    for key in ("channel_id", "user_id"):
        value = raw.get(key)
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise RuntimeError(f"{key} must be null or a numeric Discord snowflake")
    return raw


def save_binding(config: dict[str, Any], *, channel_id: int, user_id: int) -> None:
    updated = dict(config)
    updated["channel_id"] = int(channel_id)
    updated["user_id"] = int(user_id)
    updated["bound_at"] = now_iso()
    atomic_json(CONFIG_PATH, updated)


def read_optional_json(path: Path) -> dict[str, Any] | None:
    try:
        return load_json(path) if path.exists() else None
    except Exception:
        return None


def list_jobs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not JOBS.exists():
        return rows
    for job_dir in sorted(JOBS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not job_dir.is_dir():
            continue
        state = read_optional_json(job_dir / "job_state.json")
        if not state:
            continue
        row = dict(state)
        row.setdefault("command_id", job_dir.name)
        rows.append(row)
    return rows


def agent_summary() -> str:
    heartbeat = read_optional_json(RUNTIME / "agent_heartbeat.json")
    state = read_optional_json(RUNTIME / "agent_state.json")
    jobs = list_jobs()
    active = [j for j in jobs if str(j.get("status", "")).upper() in ACTIVE_STATES]
    if heartbeat:
        status = str(heartbeat.get("status") or state.get("status") if state else heartbeat.get("status") or "ONLINE")
        updated = heartbeat.get("updated_at", "unknown")
    elif state:
        status = str(state.get("status", "UNKNOWN"))
        updated = state.get("updated_at", "unknown")
    else:
        status = "OFFLINE/NOT_STARTED"
        updated = "none"
    active_text = ", ".join(str(j.get("command_id")) for j in active[:5]) or "none"
    return (
        f"PROJECT RELAY: {status}\n"
        f"Heartbeat: {updated}\n"
        f"Active jobs: {active_text}\n"
        f"Known jobs: {len(jobs)}"
    )


class RelayDiscordBot(commands.Bot):
    def __init__(self, config: dict[str, Any]) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.relay_config = config
        self.stop_task: asyncio.Task[None] | None = None

    async def setup_hook(self) -> None:
        guild = discord.Object(id=int(self.relay_config["guild_id"]))
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        atomic_json(
            DISCORD_STATE,
            {
                "status": "STARTING",
                "guild_id": int(self.relay_config["guild_id"]),
                "synced_commands": [cmd.name for cmd in synced],
                "updated_at": now_iso(),
            },
        )
        self.stop_task = asyncio.create_task(self.stop_and_heartbeat_loop())

    async def on_ready(self) -> None:
        atomic_json(
            DISCORD_STATE,
            {
                "status": "ONLINE",
                "bot_user": str(self.user),
                "bot_user_id": int(self.user.id) if self.user else None,
                "guild_id": int(self.relay_config["guild_id"]),
                "channel_id": self.relay_config.get("channel_id"),
                "bound_user_id": self.relay_config.get("user_id"),
                "updated_at": now_iso(),
            },
        )
        print(f"PROJECT RELAY Discord transport ONLINE as {self.user}")

    async def stop_and_heartbeat_loop(self) -> None:
        while not self.is_closed():
            atomic_json(
                DISCORD_HEARTBEAT,
                {
                    "status": "ONLINE" if self.is_ready() else "STARTING",
                    "guild_id": int(self.relay_config["guild_id"]),
                    "channel_id": self.relay_config.get("channel_id"),
                    "bound_user_id": self.relay_config.get("user_id"),
                    "updated_at": now_iso(),
                },
            )
            if STOP_DISCORD.exists():
                try:
                    STOP_DISCORD.unlink()
                except OSError:
                    pass
                await self.close()
                break
            await asyncio.sleep(5)


config = load_config()
bot = RelayDiscordBot(config)
relay = app_commands.Group(name="relay", description="PROJECT RELAY control commands")


def guild_matches(interaction: discord.Interaction) -> bool:
    return interaction.guild_id == int(bot.relay_config["guild_id"])


def binding_matches(interaction: discord.Interaction) -> bool:
    if not guild_matches(interaction):
        return False
    channel_id = bot.relay_config.get("channel_id")
    user_id = bot.relay_config.get("user_id")
    if channel_id is None or user_id is None:
        return False
    return interaction.channel_id == int(channel_id) and interaction.user.id == int(user_id)


async def deny(interaction: discord.Interaction, message: str) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


@relay.command(name="bind", description="Bind PROJECT RELAY to this channel and administrator")
async def relay_bind(interaction: discord.Interaction) -> None:
    if not guild_matches(interaction):
        await deny(interaction, "This Discord server is not allowlisted for PROJECT RELAY.")
        return
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await deny(interaction, "This command must be used inside the allowlisted Discord server.")
        return
    if not (interaction.user.guild_permissions.administrator or interaction.guild.owner_id == interaction.user.id):
        await deny(interaction, "Only a server administrator/owner can bind PROJECT RELAY.")
        return
    if interaction.channel_id is None:
        await deny(interaction, "Could not determine the current channel.")
        return
    save_binding(bot.relay_config, channel_id=interaction.channel_id, user_id=interaction.user.id)
    bot.relay_config = load_config()
    await interaction.response.send_message(
        "PROJECT RELAY is now bound to this channel and your Discord user. "
        "Other channels/users will be rejected.",
        ephemeral=True,
    )


@relay.command(name="status", description="Show PROJECT RELAY local status")
async def relay_status(interaction: discord.Interaction) -> None:
    if not binding_matches(interaction):
        await deny(interaction, "PROJECT RELAY is not bound here. Run /relay bind in the approved control channel.")
        return
    await interaction.response.send_message(f"```\n{agent_summary()}\n```", ephemeral=True)


@relay.command(name="jobs", description="List recent PROJECT RELAY jobs")
async def relay_jobs(interaction: discord.Interaction) -> None:
    if not binding_matches(interaction):
        await deny(interaction, "This channel/user is not authorized for PROJECT RELAY.")
        return
    jobs = list_jobs()[:10]
    if not jobs:
        await interaction.response.send_message("No PROJECT RELAY jobs found.", ephemeral=True)
        return
    lines = []
    for job in jobs:
        lines.append(
            f"{job.get('command_id', '?')} | {job.get('status', '?')} | "
            f"{job.get('project', job.get('project_key', '?'))}"
        )
    await interaction.response.send_message("```\n" + "\n".join(lines) + "\n```", ephemeral=True)


@relay.command(name="stop", description="Request SOFT/HARD/EMERGENCY stop for one job")
@app_commands.describe(command_id="PROJECT RELAY command ID", mode="Stop level")
@app_commands.choices(
    mode=[
        app_commands.Choice(name="SOFT", value="SOFT"),
        app_commands.Choice(name="HARD", value="HARD"),
        app_commands.Choice(name="EMERGENCY", value="EMERGENCY"),
    ]
)
async def relay_stop(
    interaction: discord.Interaction,
    command_id: str,
    mode: app_commands.Choice[str],
) -> None:
    if not binding_matches(interaction):
        await deny(interaction, "This channel/user is not authorized for PROJECT RELAY.")
        return
    if not COMMAND_ID_RE.fullmatch(command_id):
        await deny(interaction, "Invalid command_id.")
        return
    job_dir = JOBS / command_id
    state_path = job_dir / "job_state.json"
    if not job_dir.is_dir() or not state_path.exists():
        await deny(interaction, f"Job not found: {command_id}")
        return
    state = read_optional_json(state_path) or {}
    if str(state.get("status", "")).upper() in FINAL_STATES:
        await deny(interaction, f"Job is already finalized: {state.get('status')}")
        return
    stop_path = job_dir / "STOP_REQUESTED.json"
    atomic_json(
        stop_path,
        {
            "mode": mode.value,
            "reason": "discord_control",
            "requested_by_user_id": interaction.user.id,
            "requested_at": now_iso(),
        },
    )
    await interaction.response.send_message(
        f"STOP requested: `{command_id}` [{mode.value}]",
        ephemeral=True,
    )


bot.tree.add_command(relay)


def main() -> int:
    token = os.environ.get("PROJECT_RELAY_DISCORD_TOKEN", "").strip()
    if not token:
        print("ERROR: PROJECT_RELAY_DISCORD_TOKEN is not set. Use START_DISCORD_BOT.bat after token setup.")
        return 2
    RUNTIME.mkdir(parents=True, exist_ok=True)
    if STOP_DISCORD.exists():
        try:
            STOP_DISCORD.unlink()
        except OSError:
            pass
    bot.run(token, log_handler=None)
    atomic_json(DISCORD_STATE, {"status": "OFFLINE", "updated_at": now_iso()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
