import { test } from "node:test";
import assert from "node:assert/strict";
import { createConversationStore } from "../src/gemini-history.js";

const turn = (id, status = "complete") => ({
  id,
  question: `질문 ${id}`,
  answer: `답변 ${id}`,
  error: "",
  status,
});
const tick = () => new Promise((resolve) => setTimeout(resolve, 5));
function server() {
  const records = new Map(),
    writes = [];
  let offline = false;
  const api = async (path, method, value) => {
    await tick();
    if (offline) throw new Error("offline");
    const old = records.get(path) || { revision: 0, turns: [] };
    if (method !== "PUT") return structuredClone(old);
    if (value.revision !== old.revision)
      throw Object.assign(new Error("conflict"), { status: 409 });
    const next = {
      revision: old.revision + 1,
      turns: structuredClone(value.turns),
    };
    records.set(path, next);
    writes.push(next);
    return { revision: next.revision };
  };
  return {
    api,
    records,
    writes,
    setOffline: (value) => {
      offline = value;
    },
  };
}
test("history restores per problem, turns interrupted streams into retryable errors and clears durably", async () => {
  const s = server(),
    status = new Map();
  let store = createConversationStore(
    s.api,
    (pid, record) => status.set(pid, record),
    5,
  );
  assert.equal(store.ready("t1-01"), false);
  await store.load("t1-01");
  store.update("t1-01", () => [turn("a", "pending")], true);
  assert.equal(store.hasUnsaved(), true);
  await store.flushAll();
  store.stop();
  store = createConversationStore(
    s.api,
    (pid, record) => status.set(pid, record),
    5,
  );
  await store.load("t1-01");
  await store.load("t1-02");
  assert.equal(status.get("t1-01").turns[0].status, "error");
  assert.match(status.get("t1-01").turns[0].error, /중단/);
  assert.deepEqual(status.get("t1-02").turns, []);
  store.update("t1-01", () => [], true);
  await store.flushAll();
  assert.deepEqual(s.records.get("/conversations/t1-01").turns, []);
  assert.equal(store.hasUnsaved(), false);
  store.stop();
});
test("stream updates coalesce and the final answer is saved even during an in-flight write", async () => {
  const s = server();
  const store = createConversationStore(s.api, () => {}, 10);
  await store.load("t1-01");
  store.update("t1-01", () => [turn("a", "pending")], true);
  for (let i = 0; i < 100; i++)
    store.update("t1-01", () => [
      { ...turn("a", "pending"), answer: `partial-${i}` },
    ]);
  store.update("t1-01", () => [{ ...turn("a"), answer: "final answer" }], true);
  await store.flushAll();
  assert.equal(
    s.records.get("/conversations/t1-01").turns[0].answer,
    "final answer",
  );
  assert.ok(s.writes.length <= 3);
  assert.equal(store.hasUnsaved(), false);
  store.stop();
});
test("explicit conflict retry merges only new edits and never resurrects remotely deleted conversations", async () => {
  const s = server();
  let stateA, stateB;
  const a = createConversationStore(
    s.api,
    (_, r) => {
      stateA = r;
    },
    5,
  );
  const b = createConversationStore(
    s.api,
    (_, r) => {
      stateB = r;
    },
    5,
  );
  await a.load("t1-01");
  await b.load("t1-01");
  a.update("t1-01", () => [turn("a")], true);
  await a.flushAll();
  b.update("t1-01", () => [turn("b")], true);
  assert.equal(await b.flushAll(), false);
  assert.equal(stateB.state, "conflict");
  await b.retry("t1-01");
  await b.flushAll();
  assert.deepEqual(
    stateB.turns.map((t) => t.id),
    ["a", "b"],
  );
  a.update("t1-01", () => [], true);
  await a.flushAll();
  assert.equal(stateA.state, "conflict");
  await a.retry("t1-01");
  await a.flushAll();
  b.update("t1-01", (old) => [...old, turn("c")], true);
  await b.flushAll();
  await b.retry("t1-01");
  await b.flushAll();
  assert.deepEqual(
    stateB.turns.map((t) => t.id),
    ["c"],
  );
  a.stop();
  b.stop();
});
test("offline failures retain the unsaved transcript and can be retried without browser storage", async () => {
  const s = server();
  let state;
  const store = createConversationStore(
    s.api,
    (_, r) => {
      state = r;
    },
    5,
  );
  await store.load("t1-01");
  s.setOffline(true);
  store.update("t1-01", () => [turn("a")], true);
  assert.equal(await store.flushAll(), false);
  assert.equal(state.state, "error");
  assert.equal(state.turns[0].id, "a");
  assert.equal(store.hasUnsaved(), true);
  s.setOffline(false);
  await store.retry("t1-01");
  await store.flushAll();
  assert.equal(state.state, "saved");
  store.stop();
});
