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
    /응답 형식/,
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
    /사용 한도/,
  );
});
