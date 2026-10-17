import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const enc = new TextEncoder();
const dec = new TextDecoder();

function b64(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
}

function unb64(value: string): Uint8Array {
  const s = atob(value);
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}

async function vaultKey(): Promise<CryptoKey> {
  const raw = unb64(Deno.env.get("UKIE_TOKEN_VAULT_KEY_B64") ?? "");
  if (raw.byteLength !== 32) throw new Error("VAULT_KEY_INVALID");
  return crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]);
}

async function seal(value: string): Promise<{ ciphertext: string; iv: string }> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await vaultKey(), enc.encode(value));
  return { ciphertext: b64(new Uint8Array(encrypted)), iv: b64(iv) };
}

async function open(ciphertext: string, iv: string): Promise<string> {
  const plain = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: unb64(iv) },
    await vaultKey(),
    unb64(ciphertext),
  );
  return dec.decode(plain);
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

Deno.serve(async (req: Request) => {
  try {
    if (req.method !== "POST") return json({ status: "ERROR", error_code: "METHOD_NOT_ALLOWED" }, 405);

    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const auth = req.headers.get("authorization") ?? "";
    if (!auth.toLowerCase().startsWith("bearer ")) return json({ status: "ERROR", error_code: "AUTH_REQUIRED" }, 401);

    const userClient = createClient(supabaseUrl, anonKey, { global: { headers: { Authorization: auth } } });
    const { data: userData, error: userError } = await userClient.auth.getUser();
    if (userError || !userData.user) return json({ status: "ERROR", error_code: "AUTH_INVALID" }, 401);
    const userId = userData.user.id;

    const service = createClient(supabaseUrl, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const body = await req.json();
    const op = body?.op;

    if (op === "store_refresh") {
      const refreshToken = body?.provider_refresh_token;
      if (typeof refreshToken !== "string" || refreshToken.length < 20) {
        return json({ status: "ERROR", error_code: "REFRESH_TOKEN_MISSING" }, 400);
      }
      const sealed = await seal(refreshToken);
      const { error } = await service.from("ukie_provider_token_vault").upsert({
        user_id: userId,
        provider: "google",
        token_kind: "refresh",
        ciphertext: sealed.ciphertext,
        iv: sealed.iv,
        key_version: "v1",
        expires_at: null,
        metadata: { source: "supabase_google_oauth", stored_at: new Date().toISOString() },
        updated_at: new Date().toISOString(),
      }, { onConflict: "user_id,provider,token_kind" });
      if (error) throw new Error(`VAULT_WRITE_FAILED:${error.code ?? "unknown"}`);
      await service.from("ukie_auth_refresh_events").insert({
        user_id: userId, provider: "google", event_type: "REFRESH_TOKEN_STORED", status: "SUCCESS",
        metadata: { secret_returned: false },
      });
      return json({ status: "TOKEN_READY", provider: "google", refresh_available: true, secret_returned: false });
    }

    if (op === "health") {
      const { data, error } = await service.from("ukie_provider_token_vault")
        .select("token_kind,expires_at,updated_at,key_version")
        .eq("user_id", userId).eq("provider", "google");
      if (error) throw new Error(`VAULT_HEALTH_FAILED:${error.code ?? "unknown"}`);
      const kinds = new Set((data ?? []).map((x) => x.token_kind));
      const access = (data ?? []).find((x) => x.token_kind === "access");
      return json({
        status: kinds.has("refresh") ? "TOKEN_READY" : "CONNECTED",
        provider: "google",
        refresh_available: kinds.has("refresh"),
        access_cached: kinds.has("access"),
        token_expires_at: access?.expires_at ?? null,
        secret_returned: false,
      });
    }

    if (op === "refresh_probe") {
      const { data: row, error: readError } = await service.from("ukie_provider_token_vault")
        .select("ciphertext,iv")
        .eq("user_id", userId).eq("provider", "google").eq("token_kind", "refresh").maybeSingle();
      if (readError) throw new Error(`VAULT_READ_FAILED:${readError.code ?? "unknown"}`);
      if (!row) return json({ status: "REAUTH_REQUIRED", provider: "google", error_code: "NO_REFRESH_CREDENTIAL", secret_returned: false }, 409);

      const refreshToken = await open(row.ciphertext, row.iv);
      const clientId = Deno.env.get("GOOGLE_CLIENT_ID") ?? "";
      const clientSecret = Deno.env.get("GOOGLE_CLIENT_SECRET") ?? "";
      if (!clientId || !clientSecret) throw new Error("GOOGLE_OAUTH_SERVER_SECRET_MISSING");

      const form = new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        refresh_token: refreshToken,
        grant_type: "refresh_token",
      });
      const response = await fetch("https://oauth2.googleapis.com/token", {
        method: "POST",
        headers: { "content-type": "application/x-www-form-urlencoded" },
        body: form,
      });
      const tokenResult = await response.json();
      if (!response.ok || typeof tokenResult?.access_token !== "string") {
        await service.from("ukie_auth_refresh_events").insert({
          user_id: userId, provider: "google", event_type: "REFRESH_PROBE", status: "FAILED",
          error_code: String(tokenResult?.error ?? `HTTP_${response.status}`),
          metadata: { secret_returned: false },
        });
        return json({ status: "REAUTH_REQUIRED", provider: "google", error_code: "GOOGLE_REFRESH_FAILED", secret_returned: false }, 409);
      }

      const accessSealed = await seal(tokenResult.access_token);
      const expiresAt = new Date(Date.now() + Number(tokenResult.expires_in ?? 3600) * 1000).toISOString();
      const { error: writeError } = await service.from("ukie_provider_token_vault").upsert({
        user_id: userId,
        provider: "google",
        token_kind: "access",
        ciphertext: accessSealed.ciphertext,
        iv: accessSealed.iv,
        key_version: "v1",
        expires_at: expiresAt,
        metadata: { refreshed_at: new Date().toISOString(), scope: tokenResult.scope ?? null },
        updated_at: new Date().toISOString(),
      }, { onConflict: "user_id,provider,token_kind" });
      if (writeError) throw new Error(`ACCESS_VAULT_WRITE_FAILED:${writeError.code ?? "unknown"}`);

      await service.from("ukie_auth_refresh_events").insert({
        user_id: userId, provider: "google", event_type: "REFRESH_PROBE", status: "SUCCESS",
        token_expires_at: expiresAt, metadata: { secret_returned: false },
      });
      return json({ status: "TOKEN_READY", provider: "google", token_expires_at: expiresAt, refresh_available: true, secret_returned: false });
    }

    return json({ status: "ERROR", error_code: "UNKNOWN_OPERATION" }, 400);
  } catch (error) {
    // Never include request bodies or secret values in errors.
    const message = error instanceof Error ? error.message : "UNKNOWN";
    return json({ status: "ERROR", error_code: message.split(":", 1)[0], secret_returned: false }, 500);
  }
});
