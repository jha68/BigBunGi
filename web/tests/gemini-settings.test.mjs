import { test } from "node:test";
import assert from "node:assert/strict";
import { createSettingsStore } from "../src/gemini-settings.js";

test("saved key/model load once and rapid model edits serialize with the newest choice preserved", async () => {
  const original = { apiKey: "test-key", model: "models/gemini-a" };
  const events = [],
    writes = [];
  let release,
    revision = 7;
  const gate = new Promise((resolve) => {
    release = resolve;
  });
  const store = createSettingsStore(
    async (path, method, body) => {
      assert.equal(path, "/settings");
      if (!method) return { revision, settings: original, unreadable: false };
      writes.push(body);
      if (writes.length === 1) await gate;
      assert.equal(body.revision, revision);
      return { revision: ++revision };
    },
    (event) => events.push(event),
  );
  assert.deepEqual((await store.load()).settings, original);
  const first = store.save({ ...original, model: "models/gemini-b" });
  store.save({ ...original, model: "models/gemini-c" });
  store.save({ ...original, model: "models/gemini-d" });
  release();
  assert.equal(await first, true);
  assert.deepEqual(
    writes.map((w) => w.revision),
    [7, 8],
  );
  assert.equal(writes.at(-1).settings.model, "models/gemini-d");
  await store.save(null);
  assert.equal(writes.at(-1).settings, null);
  assert.equal(events.at(-1).state, "empty");
});
test("conflicting device settings do not overwrite silently; explicit retry refreshes the revision", async () => {
  const events = [],
    calls = [];
  let reads = 0,
    fail = true;
  const store = createSettingsStore(
    async (path, method, body) => {
      calls.push({ method, body });
      if (!method) return { revision: ++reads === 1 ? 2 : 9, settings: null };
      if (fail) {
        fail = false;
        const error = new Error("conflict");
        error.status = 409;
        throw error;
      }
      assert.equal(body.revision, 9);
      return { revision: 10 };
    },
    (e) => events.push(e),
  );
  assert.equal(
    await store.save({ apiKey: "test-key", model: "models/gemini-a" }),
    false,
  );
  assert.equal(events.at(-1).state, "error");
  assert.equal(calls.length, 2);
  assert.equal(await store.retry(), true);
  assert.equal(calls.length, 4);
});
test("unreadable vaults are preserved until explicitly replaced; stopped stores cannot write", async () => {
  const events = [],
    calls = [];
  const store = createSettingsStore(
    async (path, method) => {
      calls.push(method);
      return { revision: 3, settings: null, unreadable: true };
    },
    (e) => events.push(e),
  );
  await store.load();
  assert.equal(events.at(-1).state, "error");
  assert.equal(store.hasIntent, false);
  assert.deepEqual(calls, [undefined]);
  store.stop();
  assert.equal(await store.save(null), false);
  assert.deepEqual(calls, [undefined]);
});
