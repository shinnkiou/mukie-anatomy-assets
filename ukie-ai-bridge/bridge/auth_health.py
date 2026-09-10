"""Provider-token health state machine for UKIE AI BRIDGE / Virtual Browser.

This module stores and evaluates TOKEN METADATA ONLY. Provider access tokens,
refresh tokens, OAuth client secrets, and Supabase service-role keys must never be
written to Base44 entities, job logs, or Drive artifacts.

The actual token vault/refresh adapter is intentionally separate and server-side.
This state machine exists now so the UI, alerts, and Bridge protocol have stable
semantics before the vault is connected.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any


AUTH_STATES = {
    "UNKNOWN",
    "CONNECTED",
    "TOKEN_READY",
    "TOKEN_EXPIRING",
    "REAUTH_REQUIRED",
    "ERROR",
}


@dataclass(frozen=True)
class AuthHealthResult:
    provider: str
    status: str
    checked_at: str
    token_expires_at: str | None
    refresh_available: bool
    refresh_attempt_due: bool
    reauth_due: bool
    seconds_remaining: int | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def evaluate_auth_health(
    *,
    provider: str,
    session_connected: bool,
    token_expires_at: str | None,
    refresh_available: bool,
    refresh_failed: bool = False,
    now: datetime | None = None,
    refresh_before_seconds: int = 15 * 60,
    reauth_before_seconds: int = 5 * 60,
) -> AuthHealthResult:
    """Evaluate metadata without seeing or returning any secret token value."""
    now = (now or utc_now()).astimezone(timezone.utc)
    checked_at = now.isoformat()

    if refresh_failed:
        return AuthHealthResult(
            provider=provider,
            status="REAUTH_REQUIRED",
            checked_at=checked_at,
            token_expires_at=token_expires_at,
            refresh_available=refresh_available,
            refresh_attempt_due=False,
            reauth_due=True,
            seconds_remaining=None,
            reason="provider refresh failed; require interactive re-authentication",
        )

    if not session_connected:
        return AuthHealthResult(
            provider=provider,
            status="REAUTH_REQUIRED",
            checked_at=checked_at,
            token_expires_at=token_expires_at,
            refresh_available=refresh_available,
            refresh_attempt_due=False,
            reauth_due=True,
            seconds_remaining=None,
            reason="no authenticated provider session",
        )

    expires = _parse_utc(token_expires_at)
    if expires is None:
        return AuthHealthResult(
            provider=provider,
            status="CONNECTED",
            checked_at=checked_at,
            token_expires_at=None,
            refresh_available=refresh_available,
            refresh_attempt_due=False,
            reauth_due=False,
            seconds_remaining=None,
            reason="session connected; provider-token expiry metadata not yet verified",
        )

    remaining = int((expires - now).total_seconds())
    if remaining <= 0:
        status = "REAUTH_REQUIRED"
        return AuthHealthResult(
            provider=provider,
            status=status,
            checked_at=checked_at,
            token_expires_at=expires.isoformat(),
            refresh_available=refresh_available,
            refresh_attempt_due=refresh_available,
            reauth_due=not refresh_available,
            seconds_remaining=remaining,
            reason="provider token expired",
        )

    if remaining <= reauth_before_seconds and not refresh_available:
        return AuthHealthResult(
            provider=provider,
            status="REAUTH_REQUIRED",
            checked_at=checked_at,
            token_expires_at=expires.isoformat(),
            refresh_available=False,
            refresh_attempt_due=False,
            reauth_due=True,
            seconds_remaining=remaining,
            reason="token near expiry and no refresh credential is available",
        )

    if remaining <= refresh_before_seconds:
        return AuthHealthResult(
            provider=provider,
            status="TOKEN_EXPIRING",
            checked_at=checked_at,
            token_expires_at=expires.isoformat(),
            refresh_available=refresh_available,
            refresh_attempt_due=refresh_available,
            reauth_due=not refresh_available and remaining <= reauth_before_seconds,
            seconds_remaining=remaining,
            reason="provider token is within proactive refresh window",
        )

    return AuthHealthResult(
        provider=provider,
        status="TOKEN_READY",
        checked_at=checked_at,
        token_expires_at=expires.isoformat(),
        refresh_available=refresh_available,
        refresh_attempt_due=False,
        reauth_due=False,
        seconds_remaining=remaining,
        reason="provider token metadata is healthy",
    )


def next_health_check(
    *,
    token_expires_at: str | None,
    now: datetime | None = None,
    normal_interval_seconds: int = 15 * 60,
    expiring_interval_seconds: int = 60,
) -> str:
    now = (now or utc_now()).astimezone(timezone.utc)
    expires = _parse_utc(token_expires_at)
    interval = normal_interval_seconds
    if expires is not None and expires - now <= timedelta(minutes=30):
        interval = expiring_interval_seconds
    return (now + timedelta(seconds=interval)).isoformat()
