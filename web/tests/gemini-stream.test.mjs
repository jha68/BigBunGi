import { test } from "node:test";
import assert from "node:assert/strict";
import { askGemini, makeContext } from "../src/gemini.js";
const encoder = new TextEncoder();
const params = {
  apiKey: "test-only-secret-key",
  model: "models/gemini-test",
  context: makeContext({ id: "t1-01", files: [] }, "print(1)"),
  question: "why?",
};
const frame = (text, finishReason) =>
  "data: " +
  JSON.stringify({
    candidates: [
      {
        content: { parts: [{ text }] },
        ...(finishReason ? { finishReason } : {}),
      },
    ],
  }) +
  "\r\n\r\n";

test("SSE renders text before completion, decodes fragmented Korean, and uses the streaming endpoint", async () => {
  let controller, releaseFirst;
  const first = new Promise((resolve) => {
    releaseFirst = resolve;
  });
  const seen = [];
  const body = new ReadableStream({
    start(c) {
      controller = c;
    },
  });
  let requested;
  const result = askGemini(
    {
      ...params,
      onText: (text) => {
        seen.push(text);
        releaseFirst();
      },
    },
    async (url, options) => {
      requested = { url, options };
      return new Response(body);
    },
  );
  const bytes = encoder.encode(frame("한글 첫 부분"));
  for (let i = 0; i < bytes.length; i++)
    controller.enqueue(bytes.slice(i, i + 1));
  await first;
  assert.deepEqual(seen, ["한글 첫 부분"]);
  controller.enqueue(encoder.encode(frame(" 이어지는 답변", "STOP")));
  controller.close();
  assert.equal((await result).text, "한글 첫 부분 이어지는 답변");
  assert.match(requested.url, /streamGenerateContent\?alt=sse$/);
  assert.equal(requested.options.headers["x-goog-api-key"], params.apiKey);
});
test("streaming redacts API keys split across frames and reports output limits", async () => {
  const seen = [];
  const chunks = [
    frame("example: test-only-"),
    frame("secret-key", "MAX_TOKENS"),
  ];
  const response = await askGemini(
    { ...params, onText: (text) => seen.push(text) },
    async () => new Response(chunks.join("")),
  );
  assert.equal(response.text, "example: [API_KEY_REDACTED]");
  assert.ok(response.truncated);
  assert.ok(seen.every((text) => !text.includes("test-only-")));
});
test("broken streams retain delivered text but never count as a completed answer", async () => {
  const seen = [];
  await assert.rejects(
    () =>
      askGemini(
        { ...params, onText: (text) => seen.push(text) },
        async () => new Response(frame("partial")),
      ),
    /완료되기 전/,
  );
  assert.deepEqual(seen, ["partial"]);
  await assert.rejects(
    () =>
      askGemini(
        { ...params, onText() {} },
        async () => new Response("data: invalid-json\n\n"),
      ),
    /invalid-json/,
  );
  await assert.rejects(
    () =>
      askGemini(
        { ...params, onText() {} },
        async () =>
          new Response(JSON.stringify({ error: { message: "quota" } }), {
            status: 429,
          }),
      ),
    /quota/,
  );
});

test("in-band SSE errors preserve all provider details and already streamed text", async () => {
  const seen = [],
    raw = JSON.stringify({
      error: {
        code: 429,
        status: "RESOURCE_EXHAUSTED",
        message: "quota " + params.apiKey,
        details: [{ retryDelay: "45s", quotaId: "FreeTier" }],
      },
    });
  await assert.rejects(
    () =>
      askGemini(
        { ...params, onText: (text) => seen.push(text) },
        async () => new Response(frame("partial") + "data: " + raw + "\n\n"),
      ),
    (error) =>
      error.message ===
      "HTTP 200\n" + raw.replaceAll(params.apiKey, "[API_KEY_REDACTED]"),
  );
  assert.deepEqual(seen, ["partial"]);
  await assert.rejects(
    () =>
      askGemini(
        { ...params, onText() {} },
        async () =>
          new Response(raw, {
            headers: { "content-type": "application/json" },
          }),
      ),
    (error) =>
      error.message.includes('"retryDelay":"45s"') &&
      !error.message.includes(params.apiKey),
  );
});

test("blocked SSE responses retain the provider's finish reason and safety ratings", async () => {
  const raw = JSON.stringify({
    candidates: [
      {
        finishReason: "RECITATION",
        citationMetadata: { reason: "provider detail" },
      },
    ],
  });
  await assert.rejects(
    () =>
      askGemini(
        { ...params, onText() {} },
        async () => new Response("data: " + raw + "\n\n"),
      ),
    (error) => error.message === "HTTP 200\n" + raw,
  );
});

test("complete keys with overlapping prefix and suffix are masked before partial-key holdback", async () => {
  const apiKey = "A-test-secret-A",
    seen = [];
  const result = await askGemini(
    { ...params, apiKey, onText: (text) => seen.push(text) },
    async () => new Response(frame("answer: " + apiKey, "STOP")),
  );
  assert.equal(result.text, "answer: [API_KEY_REDACTED]");
  assert.deepEqual(seen, ["answer: [API_KEY_REDACTED]"]);
});

test("both configured keys are masked in outbound context and across streamed frames", async () => {
  const backup = "backup-secret-value",
    seen = [];
  let payload;
  const result = await askGemini(
    {
      ...params,
      question: `${params.apiKey} ${backup}`,
      redactionKeys: [backup],
      onText: (text) => seen.push(text),
    },
    async (_, options) => {
      payload = options.body;
      return new Response(
        frame("keys: test-only-secret-key backup-sec") +
          frame("ret-value", "STOP"),
      );
    },
  );
  assert.ok(!payload.includes(params.apiKey) && !payload.includes(backup));
  assert.equal(result.text, "keys: [API_KEY_REDACTED] [API_KEY_REDACTED]");
  assert.ok(
    seen.every(
      (text) => !text.includes("backup-sec") && !text.includes(params.apiKey),
    ),
  );
});
