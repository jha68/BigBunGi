import { test } from "node:test";
import assert from "node:assert/strict";
import {
  askGemini,
  listModels,
  makeContext,
  makeRequest,
  makeNoteRequest,
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

test("API failures preserve original errors and blocked responses, with credentials redacted", async () => {
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
      error.message.includes("HTTP 429") &&
      error.message.includes("quota exceeded [API_KEY_REDACTED]") &&
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
    /not authorized/,
  );
  await assert.rejects(() => askGemini({ ...params, model: "../bad" }), /모델/);
  await assert.rejects(
    () =>
      askGemini(params, async () =>
        ok({ promptFeedback: { blockReason: "SAFETY" } }),
      ),
    /SAFETY/,
  );
  await assert.rejects(
    () => askGemini(params, async () => ok({ candidates: [] })),
    /"candidates": \[\]/,
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

test("HTTP errors retain the full response, quota details and non-JSON bodies without translation or truncation", async () => {
  const params = {
    apiKey: key,
    model: "models/gemini-test",
    context: makeContext(problem, ""),
    question: "help",
  };
  const payload = {
    error: {
      code: 429,
      status: "RESOURCE_EXHAUSTED",
      message: "quota " + "x".repeat(2500) + key,
      details: [
        {
          "@type": "type.googleapis.com/google.rpc.RetryInfo",
          retryDelay: "32s",
        },
        {
          "@type": "type.googleapis.com/google.rpc.QuotaFailure",
          violations: [
            { quotaId: "GenerateRequestsPerDayPerProjectPerModel-FreeTier" },
          ],
        },
      ],
    },
  };
  const raw = JSON.stringify(payload, null, 2);
  await assert.rejects(
    () =>
      askGemini(
        params,
        async () =>
          new Response(raw, { status: 429, statusText: "Too Many Requests" }),
      ),
    (error) =>
      error.status === 429 &&
      error.message ===
        "HTTP 429 Too Many Requests\n" +
          raw.replaceAll(key, "[API_KEY_REDACTED]"),
  );
  const html =
    "<html>upstream unavailable\n<script>alert(1)</script> " + key + "</html>";
  await assert.rejects(
    () => askGemini(params, async () => new Response(html, { status: 503 })),
    (error) =>
      error.message ===
      "HTTP 503\n" + html.replaceAll(key, "[API_KEY_REDACTED]"),
  );
  await assert.rejects(
    () =>
      askGemini(
        params,
        async () =>
          new Response(null, { status: 502, statusText: "Bad Gateway" }),
      ),
    (error) => error.message === "HTTP 502 Bad Gateway",
  );
});

test("note generation summarizes all successful conversations, excludes failed turns and redacts credentials", async () => {
  const history = Array.from({ length: 8 }, (_, i) => ({
    question: `question-${i}`,
    answer:
      i === 0
        ? "평균으로 채우세요.\n```python\ndf.fillna(df.mean())\n```"
        : `answer-${i}`,
  }));
  history.push(
    { question: "pending", answer: "" },
    { question: "failed", answer: "bad", error: "quota" },
  );
  const context = makeContext(problem, `print('${key}')`);
  const payload = makeNoteRequest({ context, history, apiKey: key });
  const data = JSON.parse(payload.contents[0].parts[0].text);
  assert.equal(data.conversations.length, 8);
  assert.equal(data.conversations[0].question, "question-0");
  assert.ok(data.conversations[0].answer.includes("df.fillna(df.mean())"));
  assert.ok(
    payload.systemInstruction.parts[0].text.includes("핵심 Python 코드 1~3줄"),
  );
  assert.deepEqual(Object.keys(data), ["conversations"]);
  assert.equal(data.context, undefined);
  assert.ok(
    payload.systemInstruction.parts[0].text.includes("Q. 질문 요지 한 줄"),
  );
  assert.ok(
    !payload.systemInstruction.parts[0].text.includes("당신은 빅데이터"),
  );
  assert.ok(!JSON.stringify(payload).includes(key));
  assert.ok(!JSON.stringify(payload).includes("DO_NOT_SEND"));
  assert.throws(() => makeNoteRequest({ context, history: [] }), /질문·답변/);
  let sent;
  await askGemini(
    {
      apiKey: key,
      model: "models/gemini-2.5-pro",
      context,
      history,
      task: "notes",
    },
    async (url, options) => {
      sent = {
        url,
        body: JSON.parse(options.body),
        key: options.headers["x-goog-api-key"],
      };
      return ok({
        candidates: [
          {
            content: { parts: [{ text: "# 복습 노트" }] },
            finishReason: "STOP",
          },
        ],
      });
    },
  );
  assert.ok(sent.url.includes("models/gemini-2.5-pro:generateContent"));
  assert.equal(sent.key, key);
  assert.deepEqual(sent.body, payload);
});

test("note generation forwards optional user instructions separately and redacts both keys", async () => {
  const history = [{ question: "오류 원인?", answer: "수정 방법" }];
  const backup = "test-only-backup-key";
  const instructions = `  Z-score 공식과 ddof 차이를 포함해 줘. ${key} ${backup}  `;
  const payload = makeNoteRequest({ history, instructions, apiKey: [key, backup] });
  const data = JSON.parse(payload.contents[0].parts[0].text);
  assert.deepEqual(data.conversations, history);
  assert.equal(data.instructions, "Z-score 공식과 ddof 차이를 포함해 줘. [API_KEY_REDACTED] [API_KEY_REDACTED]");
  assert.ok(payload.systemInstruction.parts[0].text.includes("기본 요약 형식보다 우선 반영"));
  assert.deepEqual(Object.keys(JSON.parse(makeNoteRequest({ history, instructions: "  " }).contents[0].parts[0].text)), ["conversations"]);
  assert.throws(() => makeNoteRequest({ history, instructions: "가".repeat(2001) }), /2,000/);
  let sent;
  await askGemini({ apiKey: key, redactionKeys: [backup], model: "models/gemini-test", history, task: "notes", instructions }, async (url, options) => {
    sent = JSON.parse(options.body);
    return ok({ candidates: [{ content: { parts: [{ text: "요약" }] }, finishReason: "STOP" }] });
  });
  assert.deepEqual(sent, payload);
});
