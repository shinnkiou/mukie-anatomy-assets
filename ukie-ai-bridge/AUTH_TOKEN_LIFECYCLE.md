# UKIE AI Virtual Browser — Google Auth / Token Lifecycle

Status: OAuth P0 passed; long-lived unattended Google API access is not yet claimed READY.

## Fixed policy

Broad Google OAuth scopes remain intentionally enabled during the dedicated development phase for future expansion. Scope breadth and browser/Windows control are separate authorization domains.

OAuth success only proves:

`Google consent -> Supabase callback -> authenticated Supabase session -> production Base44 origin`

It does not prove every Google API capability or indefinite provider-token availability.

## Health states

Base44 `AuthHealth` stores metadata only, never provider token values.

- `CONNECTED` — Supabase Google session exists.
- `TOKEN_READY` — reserved for later: long-lived provider-token refresh path has been proven.
- `TOKEN_EXPIRING` — session or conservative testing reauth window is near its threshold.
- `REAUTH_REQUIRED` — user must run Google consent again.
- `ERROR` — auth/token lifecycle failure.

## Current P0.1 mitigation

Until a server-side encrypted provider-token vault is implemented:

1. Supabase session persistence/auto-refresh remains enabled.
2. Base44 records session expiry and auth events in `AuthHealth`.
3. A conservative reauthentication deadline is tracked for the Google Testing phase.
4. The system degrades to `REAUTH_REQUIRED` rather than pretending long-lived automation is READY.
5. Provider access/refresh token values are not rendered, logged, or copied to Base44 entities.

## Target P0.5 architecture

`Browser OAuth callback -> server-side token intake -> encrypted token vault -> scheduled refresh -> health probe -> Google API capability test`

Requirements:

- tokens never persist in frontend UI state beyond the provider SDK/session flow needed to hand them to a secure server endpoint;
- refresh secrets are encrypted at rest;
- refresh operations are auditable without logging token bodies;
- token rotation/refresh failure sets `REAUTH_REQUIRED`;
- each Google service gets an independent capability result (`READY`, `DEGRADED`, `BLOCKED`);
- Gmail send, destructive Drive actions, permission changes, publishing, purchase, or other consequential actions remain separately gated.

## Acceptance gate for long-lived Google automation

Do not set `TOKEN_READY` until all are true:

- encrypted server-side vault exists;
- refresh token lifecycle is demonstrated without exposing the secret;
- refresh survives browser reload and Base44 restart;
- failed/revoked token is detected;
- reauthorization path works;
- Drive read/write/readback test passes;
- requested API scopes are capability-tested individually.
