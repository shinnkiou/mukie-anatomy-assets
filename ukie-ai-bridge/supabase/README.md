# UKIE AI Virtual Browser — dedicated Supabase auth vault

Status: **SOURCE PREPARED / NOT DEPLOYED BY CHATGPT CONNECTOR**.

The connected Supabase management plugin currently exposes only the legacy project `vbuokbwglauibabinaqs`. The Virtual Browser application uses a different Supabase project (`zketzuymvgonmnbhbkrb` in the current Base44 configuration). To avoid damaging JONYCON/legacy auth, these files MUST NOT be applied to the legacy project.

## Files

- `001_token_vault.sql` — service-only encrypted provider-token vault and refresh audit table. RLS enabled; no authenticated-client policies are intentionally created.
- `functions/google-token-broker/index.ts` — JWT-protected Edge Function skeleton. It can store a Google provider refresh credential encrypted with AES-GCM, report metadata-only health, and perform a refresh probe without returning provider tokens to the UI.

## Required Edge Function secrets

Set these in the dedicated Virtual Browser Supabase project only:

- `UKIE_TOKEN_VAULT_KEY_B64` — exactly 32 random bytes encoded as base64. Do not store this value in GitHub, Base44 entities, Google Drive, logs, or job manifests.
- `GOOGLE_CLIENT_ID` — dedicated UKIE AI Virtual Browser OAuth client ID.
- `GOOGLE_CLIENT_SECRET` — dedicated OAuth client secret. Never paste it into ChatGPT or commit it.

The standard Supabase function variables `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` are consumed server-side.

## Deployment gate

1. Confirm target project ref is the dedicated Virtual Browser project, not JONYCON.
2. Apply `001_token_vault.sql` as a migration.
3. Run Supabase security advisor and confirm the vault has RLS enabled and no client read policy.
4. Configure the three secrets above in the project secret store.
5. Deploy `google-token-broker` with JWT verification **enabled**.
6. Run `health` before storing credentials; expect `CONNECTED`/no refresh credential.
7. Immediately after a fresh Google OAuth consent flow, send the transient provider refresh token to `store_refresh` over authenticated HTTPS. Do not log it and do not save it in browser storage.
8. Run `refresh_probe`; accept PASS only if metadata says `TOKEN_READY`, `refresh_available=true`, and `secret_returned=false`.
9. Base44 may persist only metadata in `AuthHealth`. It must never persist `provider_token`, `provider_refresh_token`, ciphertext, vault key, or OAuth client secret.

## Future Google API execution

The preferred end state is a server-side Google API broker: decrypt/refesh access tokens in the Edge Function and execute allowlisted Drive/Gmail/Calendar/Tasks/Docs/Sheets/Slides operations there. Raw access tokens should not be returned to the Base44 UI or stored in Drive artifacts.
