import { test } from "node:test";
import assert from "node:assert/strict";
import {
  askGemini,
  listModels,
  makeContext,
  makeRequest,
  preferredModel,
} from "../src/gemini.js";

const key = "test-only-key-not-a-real-credential";
const problem = {
  id: "t1-01",
  type: 1,
  title: "조건별 평균",
  scenario: "데이터를 분석하세요",
  steps: ["평균 구하기"],
  fields: [{ key: "result", decimals: 3 }],
  files: [
    {
      name: "sample.csv",
      rows: 200,
      columns: [{ name: "age" }],
      preview: [{ age: 80 }],
    },
  ],
  solution: "DO_NOT_SEND",
  expected: "DO_NOT_SEND",
};
const ok = (body) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

test("context snapshots the current problem/code/schema and real execution, without reference answers", () => {
  const result = {
    code: "old code",
    stdout: "hello",
    error: "ValueError: test",
    answers: {},
    duration: 1,
  };
  const context = makeContext(problem, "new code", result);
  assert.equal(context.currentCode, "new code");
  assert.equal(context.lastExecution.matchesCurrentCode, false);
  assert.equal(context.lastExecution.error, "ValueError: test");
  assert.equal(context.problem.datasets[0].totalRows, 200);
  assert.equal(context.problem.datasets[0].previewOnly, true);
  assert.ok(!JSON.stringify(context).includes("DO_NOT_SEND"));
  assert.ok(!makeContext(problem, "x", result, false).lastExecution);
  assert.throws(() => makeContext(problem, "x".repeat(60001)), /60,000/);
});

test("multi-turn request uses only completed turns and latest code, and redacts a key accidentally pasted in context", () => {
  const context = makeContext(problem, `print('${key}')`);
  const history = [
    { question: "first", answer: "explanation" },
    { question: "failed", error: "quota" },
  ];
  const payload = makeRequest({
    context,
    question: `why ${key}?`,
    history,
    apiKey: key,
  });
  assert.deepEqual(
    payload.contents.map((c) => c.role),
    ["user", "model", "user"],
  );
  assert.ok(!JSON.stringify(payload).includes(key));
  assert.ok(JSON.stringify(payload).includes("API_KEY_REDACTED"));
  assert.ok(!JSON.stringify(payload).includes("failed"));
  assert.throws(() => makeRequest({ context, question: "  " }), /질문/);
  assert.throws(
    () => makeRequest({ context, question: "x".repeat(4001) }),
    /4,000/,
  );
});

test("model listing authenticates in a header, handles pagination and selects supported text models", async () => {
  const seen = [];
  const models = await listModels(key, undefined, async (url, options) => {
    seen.push({ url, options });
    return ok(
      seen.length === 1
        ? {
            models: [
              {
                name: "models/gemini-pro",
                supportedGenerationMethods: ["generateContent"],
              },
            ],
            nextPageToken: "second",
          }
        : {
            models: [
              {
                name: "models/gemini-flash-latest",
                displayName: "Flash",
                supportedGenerationMethods: ["generateContent"],
              },
              {
                name: "models/gemini-image",
                supportedGenerationMethods: ["generateContent"],
              },
              {
                name: "models/embedding",
                supportedGenerationMethods: ["embedContent"],
              },
            ],
          },
    );
  });
  assert.equal(models.length, 2);
  assert.equal(preferredModel(models), "models/gemini-flash-latest");
  assert.ok(seen[1].url.includes("pageToken=second"));
  for (const request of seen) {
    assert.equal(request.options.headers["x-goog-api-key"], key);
    assert.ok(!request.url.includes(key));
    assert.equal(request.options.cache, "no-store");
  }
});

test("generation sends exact latest context and conversational roles to the selected model", async () => {
  const context = makeContext(problem, "print(123)");
  const controller = new AbortController();
  let captured;
  const result = await askGemini(
    {
      apiKey: key,
      model: "models/gemini-flash-latest",
      context,
      question: "explain",
      signal: controller.signal,
    },
    async (url, options) => {
      captured = { url, options };
      return ok({
        candidates: [
          {
            content: {
              parts: [
                { thought: true, text: "internal reasoning" },
                { text: "한국어 답변" },
              ],
            },
            finishReason: "STOP",
          },
        ],
      });
    },
  );
  assert.equal(result.text, "한국어 답변");
  assert.equal(result.truncated, false);
  assert.ok(
    captured.url.endsWith("/models/gemini-flash-latest:generateContent"),
  );
  assert.equal(captured.options.method, "POST");
  assert.equal(captured.options.signal, controller.signal);
  assert.equal(captured.options.headers["x-goog-api-key"], key);
  assert.ok(!captured.options.body.includes(key));
  assert.ok(
    JSON.parse(captured.options.body)
      .contents.at(-1)
      .parts[0].text.includes("print(123)"),
  );
});

test("invalid credentials, quota, unsupported models and blocked responses have actionable errors", async () => {
  const params = {
    apiKey: key,
    model: "models/gemini-flash-latest",
    context: makeContext(problem, ""),
    question: "help",
  };
  await assert.rejects(
    () =>
      askGemini(
        params,
        async () =>
          new Response(
            JSON.stringify({ error: { message: "quota exceeded " + key } }),
            { status: 429 },
          ),
      ),
    (error) =>
      error.status === 429 &&
      error.message.includes("사용 한도") &&
      !error.message.includes(key),
  );
  await assert.rejects(
    () =>
      listModels(
        key,
        undefined,
        async () =>
          new Response(
            JSON.stringify({ error: { message: "not authorized" } }),
            { status: 403 },
          ),
      ),
    /프로젝트 권한/,
  );
  await assert.rejects(() => askGemini({ ...params, model: "../bad" }), /모델/);
  await assert.rejects(
    () =>
      askGemini(params, async () =>
        ok({ promptFeedback: { blockReason: "SAFETY" } }),
      ),
    /응답이 제한/,
  );
  await assert.rejects(
    () => askGemini(params, async () => ok({ candidates: [] })),
    /텍스트 답변/,
  );
  const limited = await askGemini(params, async () =>
    ok({
      candidates: [
        {
          content: { parts: [{ text: "partial" }] },
          finishReason: "MAX_TOKENS",
        },
      ],
    }),
  );
  assert.equal(limited.truncated, true);
});
