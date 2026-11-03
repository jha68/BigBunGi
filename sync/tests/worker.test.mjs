import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { pbkdf2Sync } from "node:crypto";
import { Miniflare } from "miniflare";

const origin = "https://bigbungi.junununseo.com";
const password = "test-only-password-never-used-in-production";
const salt = "abcdef1234567890abcdef1234567890";
const hash = `pbkdf2-100000:${salt}:${pbkdf2Sync(password, Buffer.from(salt, "hex"), 100000, 32, "sha256").toString("hex")}`;
const state = {
  drafts: { "t1-01": "print(123)" },
  answers: { "t1-01": { result: "5" } },
  notes: { "t1-01": "복습" },
  progress: { "t1-01": { passed: true } },
  selected: "t1-01",
};
let mf, db, cookie;
const call = (path, method = "GET", body, auth = cookie, extra = {}) =>
  mf.dispatchFetch("https://bigbungi-api.junununseo.com" + path, {
    method,
    headers: {
      Origin: origin,
      "Content-Type": "application/json",
      ...(auth ? { Cookie: auth } : {}),
      ...extra,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
before(async () => {
  mf = new Miniflare({
    modules: true,
    scriptPath: new URL("../worker.js", import.meta.url).pathname,
    compatibilityDate: "2026-07-01",
    cf: false,
    d1Databases: ["DB"],
    bindings: {
      APP_ORIGIN: origin,
      PASSWORD_HASH: hash,
      HISTORY_KEY: "1".repeat(64),
    },
  });
  db = await mf.getD1Database("DB");
  await db.exec(
    await readFile(new URL("../schema.sql", import.meta.url), "utf8"),
  );
});
after(async () => mf?.dispose());

test("unauthenticated records are private; password login issues a secure server-side session", async () => {
  assert.equal((await call("/state", "GET", undefined, null)).status, 401);
  assert.equal(
    (await call("/login", "POST", { password: "wrong" }, null)).status,
    401,
  );
  const login = await call("/login", "POST", { password }, null);
  assert.equal(login.status, 200);
  const header = login.headers.get("set-cookie");
  for (const attribute of [
    "__Host-",
    "HttpOnly",
    "Secure",
    "SameSite=Strict",
    "Path=/",
  ])
    assert.ok(header.includes(attribute));
  cookie = header.split(";")[0];
  assert.equal((await call("/session")).status, 200);
  const row = await db.prepare("SELECT token FROM sessions").first();
  assert.ok(!cookie.includes(row.token));
  assert.equal(login.headers.get("cache-control"), "no-store");
});
test("records survive two independent sessions and stale revisions cannot overwrite them", async () => {
  assert.deepEqual(await (await call("/state")).json(), {
    revision: 0,
    state: null,
    updatedAt: null,
  });
  const saved = await call("/state", "PUT", { revision: 0, state });
  assert.equal(saved.status, 200);
  const other = (await call("/login", "POST", { password }, null)).headers
    .get("set-cookie")
    .split(";")[0];
  assert.deepEqual(
    (await (await call("/state", "GET", undefined, other)).json()).state,
    state,
  );
  const changes = await Promise.all([
    call("/state", "PUT", {
      revision: 1,
      state: { ...state, notes: { "t1-01": "first device" } },
    }),
    call(
      "/state",
      "PUT",
      { revision: 1, state: { ...state, notes: { "t1-01": "second device" } } },
      other,
    ),
  ]);
  assert.deepEqual(changes.map((r) => r.status).sort(), [200, 409]);
  assert.equal((await (await call("/state")).json()).revision, 2);
});
test("cross-site writes, malformed state, leaked API keys and oversized bodies are rejected", async () => {
  assert.equal(
    (
      await call("/state", "PUT", { revision: 2, state }, cookie, {
        Origin: "https://evil.example",
      })
    ).status,
    403,
  );
  assert.equal(
    (
      await call("/state", "PUT", {
        revision: 2,
        state: { ...state, apiKey: "must-not-save" },
      })
    ).status,
    400,
  );
  assert.equal(
    (await call("/state", "PUT", { revision: -1, state })).status,
    400,
  );
  assert.equal(
    (
      await call("/state", "PUT", {
        revision: 2,
        state: { ...state, drafts: [] },
      })
    ).status,
    400,
  );
  assert.equal(
    (
      await call("/state", "PUT", {
        revision: 2,
        state: { ...state, notes: { "t1-01": "x".repeat(1024 * 1024) } },
      })
    ).status,
    413,
  );
  assert.equal((await (await call("/state")).json()).revision, 2);
});
test("Gemini settings are encrypted at rest, private, revision protected and isolated from study backups", async () => {
  const settings = {
    apiKey: "test-only-gemini-key",
    model: "models/gemini-2.5-flash-lite",
  };
  assert.equal((await call("/settings", "GET", undefined, null)).status, 401);
  assert.deepEqual(await (await call("/settings")).json(), {
    revision: 0,
    settings: null,
    unreadable: false,
  });
  assert.equal(
    (await call("/settings", "PUT", { revision: 0, settings })).status,
    200,
  );
  const row = await db
    .prepare("SELECT data FROM gemini_settings WHERE id = 'owner'")
    .first();
  assert.ok(!row.data.includes(settings.apiKey));
  assert.ok(!row.data.includes(settings.model));
  const login = await call("/login", "POST", { password }, null);
  const other = login.headers.get("set-cookie").split(";")[0];
  const restored = await call("/settings", "GET", undefined, other);
  assert.equal(restored.headers.get("cache-control"), "no-store");
  assert.deepEqual((await restored.json()).settings, settings);
  assert.ok(
    !JSON.stringify(await (await call("/state")).json()).includes(
      settings.apiKey,
    ),
  );
  assert.equal(
    (await call("/settings", "PUT", { revision: 0, settings })).status,
    409,
  );
  assert.equal(
    (
      await call("/settings", "PUT", { revision: 1, settings }, cookie, {
        Origin: "https://evil.example",
      })
    ).status,
    403,
  );
  assert.equal(
    (
      await call("/settings", "PUT", {
        revision: 1,
        settings: { ...settings, password: "do-not-store" },
      })
    ).status,
    400,
  );
  assert.equal(
    (
      await call("/settings", "PUT", {
        revision: 1,
        settings: { ...settings, apiKey: "bad\nkey" },
      })
    ).status,
    400,
  );
  const corrupted = JSON.parse(row.data);
  corrupted.data =
    (corrupted.data[0] === "a" ? "b" : "a") + corrupted.data.slice(1);
  await db
    .prepare("UPDATE gemini_settings SET data = ? WHERE id = 'owner'")
    .bind(JSON.stringify(corrupted))
    .run();
  assert.deepEqual(await (await call("/settings")).json(), {
    revision: 1,
    settings: null,
    unreadable: true,
  });
  assert.equal(
    (await call("/settings", "PUT", { revision: 1, settings })).status,
    200,
  );
  const updated = await db
    .prepare("SELECT data FROM gemini_settings WHERE id = 'owner'")
    .first();
  assert.notEqual(updated.data, row.data);
  assert.equal(
    (await call("/settings", "PUT", { revision: 2, settings: null })).status,
    200,
  );
  assert.deepEqual(await (await call("/settings")).json(), {
    revision: 3,
    settings: null,
    unreadable: false,
  });
});

test("two keys and the active choice are encrypted together; legacy settings and input validation remain supported", async () => {
  const settings = {
    apiKey: "primary-test-key",
    backupApiKey: "backup-test-key",
    activeKeyIndex: 1,
    model: "models/gemini-2.5-flash",
  };
  assert.equal(
    (await call("/settings", "PUT", { revision: 3, settings })).status,
    200,
  );
  const raw = (
    await db
      .prepare("SELECT data FROM gemini_settings WHERE id = 'owner'")
      .first()
  ).data;
  assert.ok(
    !raw.includes(settings.apiKey) && !raw.includes(settings.backupApiKey),
  );
  assert.deepEqual((await (await call("/settings")).json()).settings, settings);
  for (const invalid of [
    { ...settings, thirdApiKey: "no" },
    { ...settings, activeKeyIndex: 2 },
    { ...settings, backupApiKey: "bad\nkey" },
    { ...settings, backupApiKey: "", activeKeyIndex: 1 },
  ])
    assert.equal(
      (await call("/settings", "PUT", { revision: 4, settings: invalid }))
        .status,
      400,
    );
  assert.equal(
    (await call("/settings", "PUT", { revision: 4, settings: null })).status,
    200,
  );
});

test("per-problem conversations are encrypted, private, CAS protected and retain deletion revisions", async () => {
  const turn = {
    id: "test-turn-1",
    question: "결측값은 어떻게 처리해?",
    answer: "중앙값을 사용하세요.",
    error: "",
    status: "complete",
    model: "models/gemini-2.5-flash",
    contextLines: 4,
    withExecution: true,
    at: "2026-11-03T00:00:00Z",
  };
  const path = "/conversations/t1-01";
  assert.equal((await call(path, "GET", undefined, null)).status, 401);
  assert.deepEqual(await (await call(path)).json(), { revision: 0, turns: [] });
  assert.equal(
    (await call(path, "PUT", { revision: 0, turns: [turn] })).status,
    200,
  );
  const ciphertext = (
    await db
      .prepare("SELECT data FROM conversations WHERE id = 't1-01'")
      .first()
  ).data;
  assert.ok(
    !ciphertext.includes(turn.question) && !ciphertext.includes(turn.answer),
  );
  const other = (await call("/login", "POST", { password }, null)).headers
    .get("set-cookie")
    .split(";")[0];
  assert.deepEqual(
    (await (await call(path, "GET", undefined, other)).json()).turns,
    [turn],
  );
  assert.deepEqual(
    (await (await call("/conversations/t1-02")).json()).turns,
    [],
  );
  assert.equal(
    (await call(path, "PUT", { revision: 0, turns: [] })).status,
    409,
  );
  assert.equal(
    (await call(path, "PUT", { revision: 1, turns: [turn, turn] })).status,
    400,
  );
  assert.equal(
    (
      await call(path, "PUT", {
        revision: 1,
        turns: [{ ...turn, apiKey: "not-allowed" }],
      })
    ).status,
    400,
  );
  assert.equal(
    (
      await call(path, "PUT", {
        revision: 1,
        turns: [{ ...turn, answer: "a".repeat(60001) }],
      })
    ).status,
    400,
  );
  assert.equal(
    (
      await call(path, "PUT", {
        revision: 1,
        turns: Array.from({ length: 201 }, (_, i) => ({
          ...turn,
          id: `turn-${i}`,
        })),
      })
    ).status,
    400,
  );
  assert.equal(
    (
      await call(path, "PUT", { revision: 1, turns: [turn] }, cookie, {
        Origin: "https://evil.example",
      })
    ).status,
    403,
  );
  // Ciphertext copied to another problem fails authenticated decryption.
  await db
    .prepare(
      "INSERT INTO conversations (id, revision, data) VALUES ('t1-02', 1, ?)",
    )
    .bind(ciphertext)
    .run();
  assert.equal((await call("/conversations/t1-02")).status, 500);
  await db.prepare("DELETE FROM conversations WHERE id = 't1-02'").run();
  assert.equal(
    (await call(path, "PUT", { revision: 1, turns: [] })).status,
    200,
  );
  assert.deepEqual(await (await call(path)).json(), { revision: 2, turns: [] });
  assert.equal(
    (await call(path, "PUT", { revision: 1, turns: [turn] })).status,
    409,
  );
  assert.equal(
    (await call(path, "PUT", { revision: 2, turns: [turn] })).status,
    200,
  );
  const second = (
    await db
      .prepare("SELECT data FROM conversations WHERE id = 't1-01'")
      .first()
  ).data;
  assert.notEqual(ciphertext, second);
  const failed = {
    ...turn,
    keyNumber: 2,
    retryError: "API 키 1\nHTTP 429\nfirst error",
    status: "error",
    answer: "partial",
    error:
      "HTTP 429\n" +
      JSON.stringify({
        error: { message: "quota exceeded", details: "x".repeat(5000) },
      }),
  };
  assert.equal(
    (await call(path, "PUT", { revision: 3, turns: [failed] })).status,
    200,
  );
  assert.deepEqual((await (await call(path)).json()).turns, [failed]);
});

test("logout invalidates sessions, expired sessions are rejected, and wrong passwords are rate limited", async () => {
  assert.equal((await call("/logout", "POST", {})).status, 200);
  assert.equal((await call("/session")).status, 401);
  const expired = (await call("/login", "POST", { password }, null)).headers
    .get("set-cookie")
    .split(";")[0];
  await db.prepare("UPDATE sessions SET expires = 0").run();
  assert.equal((await call("/state", "GET", undefined, expired)).status, 401);
  for (let i = 0; i < 5; i++)
    assert.equal(
      (await call("/login", "POST", { password: "wrong" }, null)).status,
      401,
    );
  const locked = await call("/login", "POST", { password }, null);
  assert.equal(locked.status, 429);
  assert.ok(Number(locked.headers.get("retry-after")) > 0);
});
