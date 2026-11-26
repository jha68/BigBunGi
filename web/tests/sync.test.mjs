import { test } from "node:test";
import assert from "node:assert/strict";
import {
  syncRequest,
  sameState,
  normalizeState,
  hasRecords,
} from "../src/sync.js";
import { mergeMockRecords } from "../src/mock-records.js";

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
    "highlights",
    "progress",
    "selected",
  ]);
});

test("exam migration preserves rounds, newer submissions and removed bookmarks", () => {
  const remote = {
    completed: { 11: { id: "remote", startedAt: 1, submittedAt: 4 } },
    retryMarks: { 11: [] }, retryMarkTimes: { 11: 8 },
  };
  const local = {
    completed: {
      11: { id: "replaced", startedAt: 2, submittedAt: 3, updatedAt: 5 },
      12: { id: "legacy", startedAt: 1, submittedAt: 6 },
    },
    retryMarks: { 11: ["r11-01"], 12: ["r12-01"] },
  };
  const merged = mergeMockRecords(remote, local);
  assert.deepEqual(merged.completed, { ...remote.completed, 12: local.completed[12] });
  assert.deepEqual(merged.retryMarks, { 11: [], 12: ["r12-01"] });
  assert.deepEqual(normalizeState({ mockExam: merged }).mockExam, merged);
  const updated = { ...remote.completed[11], updatedAt: 9, retries: {} };
  assert.equal(mergeMockRecords(remote, { completed: { 11: updated } }).completed[11], updated);
});
