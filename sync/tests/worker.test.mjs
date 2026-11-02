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
  mf.dispatchFetch("https://api.bigbungi.junununseo.com" + path, {
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
    bindings: { APP_ORIGIN: origin, PASSWORD_HASH: hash },
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
