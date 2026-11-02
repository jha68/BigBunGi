import { test } from "node:test";
import assert from "node:assert/strict";
import {
  syncRequest,
  sameState,
  normalizeState,
  hasRecords,
} from "../src/sync.js";

test("sync sends credentials as cookies, keeps passwords out of URLs and exposes conflicts", async () => {
  let captured;
  await syncRequest(
    "https://sync.example",
    "/login",
    "POST",
    { password: "test-only" },
    async (url, options) => {
      captured = { url, options };
      return Response.json({ ok: true });
    },
  );
  assert.equal(captured.url, "https://sync.example/login");
  assert.equal(captured.options.credentials, "include");
  assert.equal(captured.options.cache, "no-store");
  await assert.rejects(
    () =>
      syncRequest("", "/state", "PUT", {}, async () =>
        Response.json({ error: "conflict" }, { status: 409 }),
      ),
    (e) => e.status === 409,
  );
  await assert.rejects(
    () =>
      syncRequest("", "/state", "GET", undefined, async () => {
        throw new TypeError();
      }),
    (e) => e.status === 0 && e.message.includes("기록은 유지"),
  );
});
test("record comparison tolerates ordering but preserves cleared code, notes and progress", () => {
  assert.ok(sameState(null, {}));
  assert.ok(
    sameState(
      { notes: { "t1-02": "b", "t1-01": "a" } },
      { notes: { "t1-01": "a", "t1-02": "b" } },
    ),
  );
  assert.ok(
    !sameState({ drafts: { "t1-01": "code" } }, { drafts: { "t1-01": "" } }),
  );
  assert.ok(!hasRecords({ selected: "t1-02" }));
  assert.ok(hasRecords({ notes: { "t1-01": "note" } }));
  assert.deepEqual(Object.keys(normalizeState({ apiKey: "must-not-copy" })), [
    "drafts",
    "answers",
    "notes",
    "progress",
    "selected",
  ]);
});
