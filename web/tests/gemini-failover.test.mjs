import { test } from "node:test";
import assert from "node:assert/strict";
import { withKeyFallback } from "../src/gemini-failover.js";
import { GeminiError } from "../src/gemini.js";

test("a failed key switches once to the other key and returns the successful index", async () => {
  const calls = [],
    attempts = [],
    keys = ["first-key", "second-key"];
  const result = await withKeyFallback({
    keys,
    timeout: 0,
    onAttempt: (attempt) => attempts.push(attempt),
    run: async (key) => {
      calls.push(key);
      if (key === keys[0])
        throw new GeminiError("HTTP 429\n" + keys.join(" "), 429);
      return "answer";
    },
  });
  assert.deepEqual(calls, keys);
  assert.equal(result.result, "answer");
  assert.equal(result.index, 1);
  assert.match(attempts[1].previousError, /HTTP 429/);
  assert.ok(!keys.some((key) => attempts[1].previousError.includes(key)));
});
test("the last successful key is tried first, both failures retain original errors, and retries are bounded", async () => {
  const calls = [],
    keys = ["first", "second"];
  await assert.rejects(
    () =>
      withKeyFallback({
        keys,
        activeIndex: 1,
        timeout: 0,
        run: async (key, index) => {
          calls.push(index);
          throw new GeminiError(
            `HTTP ${index === 1 ? 503 : 429}\n${key} quota detail`,
            index === 1 ? 503 : 429,
          );
        },
      }),
    (error) =>
      error.status === 429 &&
      error.message.includes("API 키 2\nHTTP 503") &&
      error.message.includes("API 키 1\nHTTP 429") &&
      !keys.some((key) => error.message.includes(key)),
  );
  assert.deepEqual(calls, [1, 0]);
});
test("single and duplicate keys make one attempt; cancelling never triggers a fallback", async () => {
  for (const keys of [["only"], ["only", "only"]]) {
    let count = 0;
    await assert.rejects(
      () =>
        withKeyFallback({
          keys,
          timeout: 0,
          run: async () => {
            count++;
            throw new GeminiError("HTTP 403\noriginal", 403);
          },
        }),
      (error) => error.message === "HTTP 403\noriginal",
    );
    assert.equal(count, 1);
  }
  const controller = new AbortController();
  let count = 0;
  await assert.rejects(
    () =>
      withKeyFallback({
        keys: ["one", "two"],
        signal: controller.signal,
        timeout: 0,
        run: async () => {
          count++;
          controller.abort();
          controller.signal.throwIfAborted();
        },
      }),
    (error) => error.name === "AbortError",
  );
  assert.equal(count, 1);
});
test("a timeout belongs to one attempt and allows the other key to succeed", async () => {
  const result = await withKeyFallback({
    keys: ["one", "two"],
    timeout: 10,
    run: async (_, index, signal) =>
      index === 1
        ? "ok"
        : new Promise((resolve, reject) => {
            const keepAlive = setTimeout(resolve, 1000);
            signal.addEventListener(
              "abort",
              () => {
                clearTimeout(keepAlive);
                reject(signal.reason);
              },
              { once: true },
            );
          }),
  });
  assert.equal(result.index, 1);
  assert.match(result.previousError, /TimeoutError/);
});
