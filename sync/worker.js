const COOKIE = "__Host-bigbungi-session";
const DAY = 86400;
const MAX_BODY = 1024 * 1024;
const encoder = new TextEncoder();
const hex = (bytes) =>
  [...new Uint8Array(bytes)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
const unhex = (str) =>
  Uint8Array.from(str.match(/../g), (x) => parseInt(x, 16));
const digest = async (text) =>
  hex(await crypto.subtle.digest("SHA-256", encoder.encode(text)));

async function settingsKey(passwordHash, purpose = "settings/owner") {
  const material = await crypto.subtle.importKey(
    "raw",
    encoder.encode(passwordHash),
    "HKDF",
    false,
    ["deriveKey"],
  );
  return crypto.subtle.deriveKey(
    {
      name: "HKDF",
      hash: "SHA-256",
      salt: encoder.encode("bigbungi-vault-v1"),
      info: encoder.encode(
        purpose === "settings/owner" ? "gemini-settings/owner" : purpose,
      ),
    },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}
export async function encryptSettings(
  settings,
  passwordHash,
  purpose = "settings/owner",
) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv,
      additionalData: encoder.encode(`bigbungi/${purpose}/v1`),
    },
    await settingsKey(passwordHash, purpose),
    encoder.encode(JSON.stringify(settings)),
  );
  return JSON.stringify({ version: 1, iv: hex(iv), data: hex(encrypted) });
}
export async function decryptSettings(
  data,
  passwordHash,
  purpose = "settings/owner",
) {
  const record = JSON.parse(data);
  if (
    record.version !== 1 ||
    !/^[a-f0-9]{24}$/.test(record.iv) ||
    !/^[a-f0-9]+$/.test(record.data) ||
    record.data.length % 2
  )
    throw new Error("invalid-vault");
  const decrypted = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: unhex(record.iv),
      additionalData: encoder.encode(`bigbungi/${purpose}/v1`),
    },
    await settingsKey(passwordHash, purpose),
    unhex(record.data),
  );
  return JSON.parse(new TextDecoder().decode(decrypted));
}
function validSettings(settings) {
  return (
    settings === null ||
    (settings &&
      typeof settings === "object" &&
      !Array.isArray(settings) &&
      Object.keys(settings).every((key) =>
        ["apiKey", "backupApiKey", "activeKeyIndex", "model"].includes(key),
      ) &&
      typeof settings.apiKey === "string" &&
      /^[\x21-\x7e]{1,512}$/.test(settings.apiKey) &&
      (settings.backupApiKey === undefined ||
        settings.backupApiKey === "" ||
        (typeof settings.backupApiKey === "string" &&
          /^[\x21-\x7e]{1,512}$/.test(settings.backupApiKey))) &&
      (settings.activeKeyIndex === undefined ||
        settings.activeKeyIndex === 0 ||
        (settings.activeKeyIndex === 1 && !!settings.backupApiKey)) &&
      typeof settings.model === "string" &&
      /^models\/gemini-[a-zA-Z0-9._-]{1,180}$/.test(settings.model))
  );
}

export function validConversation(turns) {
  if (!Array.isArray(turns) || turns.length > 200) return false;
  const ids = new Set();
  return turns.every((turn) => {
    if (!turn || typeof turn !== "object" || Array.isArray(turn)) return false;
    if (
      Object.keys(turn).some(
        (key) =>
          ![
            "id",
            "question",
            "answer",
            "error",
            "status",
            "model",
            "contextLines",
            "withExecution",
            "at",
            "truncated",
            "keyNumber",
            "retryError",
          ].includes(key),
      )
    )
      return false;
    if (
      typeof turn.id !== "string" ||
      !/^[a-zA-Z0-9_-]{1,120}$/.test(turn.id) ||
      ids.has(turn.id)
    )
      return false;
    ids.add(turn.id);
    return (
      typeof turn.question === "string" &&
      turn.question.length <= 4000 &&
      typeof turn.answer === "string" &&
      turn.answer.length <= 60000 &&
      typeof turn.error === "string" &&
      (turn.keyNumber === undefined || [1, 2].includes(turn.keyNumber)) &&
      (turn.retryError === undefined || typeof turn.retryError === "string") &&
      ["pending", "complete", "error"].includes(turn.status) &&
      typeof turn.model === "string" &&
      /^models\/gemini-[a-zA-Z0-9._-]{1,180}$/.test(turn.model) &&
      Number.isSafeInteger(turn.contextLines) &&
      turn.contextLines >= 0 &&
      typeof turn.withExecution === "boolean" &&
      typeof turn.at === "string" &&
      turn.at.length <= 40 &&
      (turn.truncated === undefined || typeof turn.truncated === "boolean")
    );
  });
}

async function validPassword(password, record) {
  if (typeof password !== "string" || password.length > 128) return false;
  const [version, salt, expected] = record.split(":");
  if (
    version !== "pbkdf2-100000" ||
    !/^[a-f0-9]{32}$/.test(salt) ||
    !/^[a-f0-9]{64}$/.test(expected)
  )
    return false;
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );
  const actual = hex(
    await crypto.subtle.deriveBits(
      {
        name: "PBKDF2",
        hash: "SHA-256",
        salt: unhex(salt),
        iterations: 100000,
      },
      key,
      256,
    ),
  );
  let difference = 0;
  for (let i = 0; i < expected.length; i++)
    difference |= actual.charCodeAt(i) ^ expected.charCodeAt(i);
  return difference === 0;
}

export function validState(state) {
  if (!state || typeof state !== "object" || Array.isArray(state)) return false;
  const fields = [
    "drafts",
    "answers",
    "notes",
    "progress",
    "selected",
    "highlights",
  ];
  if (Object.keys(state).some((key) => !fields.includes(key))) return false;
  if (
    state.selected != null &&
    state.selected !== "home" &&
    !/^t[123]-\d{2}$/.test(state.selected)
  )
    return false;
  for (const field of fields.slice(0, 4)) {
    const values = state[field];
    if (!values || typeof values !== "object" || Array.isArray(values))
      return false;
    if (
      Object.keys(values).length > 100 ||
      Object.keys(values).some((key) => !/^t[123]-\d{2}$/.test(key))
    )
      return false;
    if (
      (field === "drafts" || field === "notes") &&
      Object.values(values).some((value) => typeof value !== "string")
    )
      return false;
  }
  if (state.highlights !== undefined) {
    if (
      !state.highlights ||
      typeof state.highlights !== "object" ||
      Array.isArray(state.highlights) ||
      Object.keys(state.highlights).length > 100
    )
      return false;
    for (const [pid, items] of Object.entries(state.highlights)) {
      if (
        !/^t[123]-\d{2}$/.test(pid) ||
        !Array.isArray(items) ||
        items.length > 100
      )
        return false;
      if (
        items.some(
          (item) =>
            !item ||
            Object.keys(item).some(
              (key) =>
                ![
                  "id",
                  "text",
                  "quote",
                  "start",
                  "before",
                  "after",
                  "noteHash",
                ].includes(key),
            ) ||
            typeof item.id !== "string" ||
            !/^[a-zA-Z0-9_-]{1,120}$/.test(item.id) ||
            !["text", "quote", "before", "after", "noteHash"].every(
              (key) => typeof item[key] === "string",
            ) ||
            item.text.length > 6000 ||
            item.quote.length > 6000 ||
            !item.quote.trim() ||
            item.before.length > 64 ||
            item.after.length > 64 ||
            item.noteHash.length > 40 ||
            !Number.isSafeInteger(item.start) ||
            item.start < 0 ||
            item.start > 1000000,
        )
      )
        return false;
    }
  }
  return true;
}

async function readBody(request, limit = MAX_BODY) {
  if (Number(request.headers.get("content-length")) > limit)
    throw new Error("too-large");
  const reader = request.body?.getReader();
  if (!reader) throw new Error("bad-json");
  let size = 0;
  const chunks = [];
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > limit) {
      await reader.cancel();
      throw new Error("too-large");
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.length;
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("origin");
    const headers = {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      Vary: "Origin",
      ...(origin === env.APP_ORIGIN
        ? {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
          }
        : {}),
    };
    const reply = (data, status = 200, extra = {}) =>
      new Response(JSON.stringify(data), {
        status,
        headers: { ...headers, ...extra },
      });
    if (origin && origin !== env.APP_ORIGIN)
      return reply({ error: "허용되지 않은 요청입니다." }, 403);
    if (request.method === "OPTIONS")
      return reply({}, 200, {
        "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      });
    if (!env.DB || !env.PASSWORD_HASH)
      return reply({ error: "동기화 서버 설정이 완료되지 않았습니다." }, 503);
    if (!["GET", "HEAD"].includes(request.method) && origin !== env.APP_ORIGIN)
      return reply({ error: "요청 출처를 확인할 수 없습니다." }, 403);
    const path = new URL(request.url).pathname;
    const now = Math.floor(Date.now() / 1000);
    try {
      if (path === "/login" && request.method === "POST") {
        const ip = await digest(
          request.headers.get("CF-Connecting-IP") || "unknown",
        );
        const attempt = await env.DB.prepare(
          "SELECT failures, expires FROM login_attempts WHERE ip = ?",
        )
          .bind(ip)
          .first();
        if (attempt?.expires > now && attempt.failures >= 5)
          return reply(
            { error: "로그인 시도가 많습니다. 15분 후 다시 시도해 주세요." },
            429,
            { "Retry-After": String(attempt.expires - now) },
          );
        const { password } = await readBody(request, 2048);
        if (!(await validPassword(password, env.PASSWORD_HASH))) {
          await env.DB.prepare(
            "INSERT INTO login_attempts (ip, failures, expires) VALUES (?, 1, ?) ON CONFLICT(ip) DO UPDATE SET failures = CASE WHEN expires <= ? THEN 1 ELSE failures + 1 END, expires = CASE WHEN expires <= ? THEN excluded.expires ELSE expires END",
          )
            .bind(ip, now + 900, now, now)
            .run();
          return reply({ error: "비밀번호가 맞지 않습니다." }, 401);
        }
        const token = hex(crypto.getRandomValues(new Uint8Array(32)));
        // Only session token hashes are stored. Expired rows never authorize access.
        await env.DB.batch([
          env.DB.prepare(
            "DELETE FROM login_attempts WHERE ip = ? OR expires <= ?",
          ).bind(ip, now),
          env.DB.prepare("DELETE FROM sessions WHERE expires <= ?").bind(now),
          env.DB.prepare(
            "INSERT INTO sessions (token, expires, auth_version) VALUES (?, ?, ?)",
          ).bind(
            await digest(token),
            now + 7 * DAY,
            await digest(env.PASSWORD_HASH),
          ),
        ]);
        return reply({ ok: true }, 200, {
          "Set-Cookie": `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${7 * DAY}`,
        });
      }
      const token = request.headers
        .get("cookie")
        ?.split(";")
        .map((v) => v.trim())
        .find((v) => v.startsWith(COOKIE + "="))
        ?.slice(COOKIE.length + 1);
      const tokenHash =
        token && /^[a-f0-9]{64}$/.test(token) ? await digest(token) : null;
      const session =
        tokenHash &&
        (await env.DB.prepare(
          "SELECT expires, auth_version FROM sessions WHERE token = ?",
        )
          .bind(tokenHash)
          .first());
      if (
        !session ||
        session.expires <= now ||
        session.auth_version !== (await digest(env.PASSWORD_HASH))
      )
        return reply({ error: "비밀번호를 입력해 로그인해 주세요." }, 401);
      if (path === "/session" && request.method === "GET")
        return reply({ ok: true });
      if (path === "/logout" && request.method === "POST") {
        await env.DB.prepare("DELETE FROM sessions WHERE token = ?")
          .bind(tokenHash)
          .run();
        return reply({ ok: true }, 200, {
          "Set-Cookie": `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`,
        });
      }
      if (path === "/settings" && request.method === "GET") {
        const row = await env.DB.prepare(
          "SELECT revision, data FROM gemini_settings WHERE id = 'owner'",
        ).first();
        let settings = null,
          unreadable = false;
        if (row?.data) {
          try {
            settings = await decryptSettings(row.data, env.PASSWORD_HASH);
          } catch {
            unreadable = true;
          }
        }
        return reply({ revision: row?.revision || 0, settings, unreadable });
      }
      if (path === "/settings" && request.method === "PUT") {
        const { revision, settings } = await readBody(request, 4096);
        if (
          !Number.isSafeInteger(revision) ||
          revision < 0 ||
          !validSettings(settings)
        )
          return reply(
            { error: "저장할 Gemini 설정의 형식이 올바르지 않습니다." },
            400,
          );
        const encrypted =
          settings === null
            ? null
            : await encryptSettings(settings, env.PASSWORD_HASH);
        const changed = await env.DB.prepare(
          "UPDATE gemini_settings SET data = ?, revision = revision + 1, updated_at = ? WHERE id = 'owner' AND revision = ?",
        )
          .bind(encrypted, new Date().toISOString(), revision)
          .run();
        if (changed.meta.changes !== 1)
          return reply(
            { error: "다른 기기에서 Gemini 설정이 변경되었습니다." },
            409,
          );
        return reply({ revision: revision + 1 });
      }
      if (path === "/conversations" && request.method === "GET") {
        if (!/^[a-f0-9]{64}$/.test(env.HISTORY_KEY || ""))
          return reply(
            { error: "AI 대화 저장소 설정이 완료되지 않았습니다." },
            503,
          );
        const rows = await env.DB.prepare(
          "SELECT id, data, updated_at FROM conversations WHERE id LIKE 't%' AND data IS NOT NULL",
        ).all();
        const records = [],
          unavailable = [];
        for (const row of rows.results) {
          if (!/^t[123]-\d{2}$/.test(row.id)) continue;
          try {
            const turns = await decryptSettings(
              row.data,
              env.HISTORY_KEY,
              `conversations/${row.id}`,
            );
            records.push({
              id: row.id,
              turnIds: turns.map((turn) => turn.id),
              updatedAt: row.updated_at,
              questions: turns
                .slice(-5)
                .map(({ id, question, answer, status }) => ({
                  id,
                  question: question.slice(0, 1000),
                  answer: answer.slice(0, 1500),
                  status,
                })),
            });
          } catch {
            unavailable.push(row.id);
          }
        }
        return reply({ records, unavailable });
      }
      const conversation = /^\/conversations\/(t[123]-\d{2}|home)$/.exec(path);
      if (conversation && ["GET", "PUT"].includes(request.method)) {
        const pid = conversation[1];
        if (!/^[a-f0-9]{64}$/.test(env.HISTORY_KEY || ""))
          return reply(
            { error: "AI 대화 저장소 설정이 완료되지 않았습니다." },
            503,
          );
        if (request.method === "GET") {
          const row = await env.DB.prepare(
            "SELECT revision, data FROM conversations WHERE id = ?",
          )
            .bind(pid)
            .first();
          try {
            const turns = row?.data
              ? await decryptSettings(
                  row.data,
                  env.HISTORY_KEY,
                  `conversations/${pid}`,
                )
              : [];
            return reply({ revision: row?.revision || 0, turns });
          } catch {
            return reply(
              {
                error:
                  "저장된 AI 대화를 복호화하지 못했습니다. 기존 기록은 보존됩니다.",
              },
              500,
            );
          }
        }
        const { revision, turns } = await readBody(request, 512 * 1024);
        if (
          !Number.isSafeInteger(revision) ||
          revision < 0 ||
          !validConversation(turns)
        )
          return reply(
            {
              error:
                "대화는 문제당 200개, 질문 4,000자·답변 60,000자 이내여야 합니다.",
            },
            400,
          );
        const encrypted = turns.length
          ? await encryptSettings(
              turns,
              env.HISTORY_KEY,
              `conversations/${pid}`,
            )
          : null;
        // Retain an empty tombstone so an older device cannot resurrect deleted history.
        const updated =
          revision === 0
            ? await env.DB.prepare(
                "INSERT INTO conversations (id, revision, data, updated_at) VALUES (?, 1, ?, ?) ON CONFLICT(id) DO NOTHING",
              )
                .bind(pid, encrypted, new Date().toISOString())
                .run()
            : await env.DB.prepare(
                "UPDATE conversations SET revision = revision + 1, data = ?, updated_at = ? WHERE id = ? AND revision = ?",
              )
                .bind(encrypted, new Date().toISOString(), pid, revision)
                .run();
        if (updated.meta.changes !== 1)
          return reply(
            { error: "다른 기기에서 이 문제의 AI 대화가 변경되었습니다." },
            409,
          );
        return reply({ revision: revision + 1 });
      }
      if (path === "/state" && request.method === "GET") {
        const row = await env.DB.prepare(
          "SELECT revision, data, updated_at FROM practice WHERE id = 'owner'",
        ).first();
        return reply({
          revision: row?.revision || 0,
          state: row?.data ? JSON.parse(row.data) : null,
          updatedAt: row?.updated_at || null,
        });
      }
      if (path === "/state" && request.method === "PUT") {
        const { revision, state } = await readBody(request);
        if (
          !Number.isSafeInteger(revision) ||
          revision < 0 ||
          !validState(state)
        )
          return reply(
            { error: "저장할 기록의 형식이 올바르지 않습니다." },
            400,
          );
        const updatedAt = new Date().toISOString();
        const changed = await env.DB.prepare(
          "UPDATE practice SET data = ?, revision = revision + 1, updated_at = ? WHERE id = 'owner' AND revision = ?",
        )
          .bind(JSON.stringify(state), updatedAt, revision)
          .run();
        if (changed.meta.changes !== 1)
          return reply({ error: "다른 기기에서 기록이 변경되었습니다." }, 409);
        return reply({ revision: revision + 1, updatedAt });
      }
      return reply({ error: "요청한 경로를 찾을 수 없습니다." }, 404);
    } catch (error) {
      if (error.message === "too-large")
        return reply(
          {
            error: path.startsWith("/conversations/")
              ? "AI 대화가 512KiB를 초과했습니다. 현재 대화를 내려받은 뒤 대화를 지워 주세요."
              : "기록이 너무 큽니다. 1MB 이내로 줄여 주세요.",
          },
          413,
        );
      if (error instanceof SyntaxError || error.message === "bad-json")
        return reply({ error: "요청 형식이 올바르지 않습니다." }, 400);
      return reply(
        {
          error: "기록 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        },
        500,
      );
    }
  },
};
