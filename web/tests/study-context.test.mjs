import { test } from "node:test";
import assert from "node:assert/strict";
import {
  activeHighlights,
  noteHash,
  rebaseHighlights,
} from "../src/note-highlights.js";
import { makeStudyContext } from "../src/study-context.js";
import { makeStudyRequest } from "../src/gemini.js";

const note =
  "Q. 결측치는?\nA. 중앙값으로 대체합니다.\n```python\ndf.fillna(df.median())\n```";
const highlight = {
  id: "h1",
  text: "중앙값으로 대체합니다.",
  quote: "중앙값으로 대체합니다.",
  start: 14,
  before: "",
  after: "",
  noteHash: noteHash(note),
};
const data = {
  catalog: [
    { id: "t1-01", title: "결측치", type: 1 },
    { id: "t1-02", title: "집계", type: 1 },
  ],
  notes: { "t1-01": note },
  highlights: { "t1-01": [highlight] },
  progress: {},
  serverEnabled: true,
};

test("home context uses all usage IDs and merges unsaved questions without counting its own home chat", () => {
  const context = makeStudyContext(
    data,
    {
      records: [
        {
          id: "t1-01",
          turnIds: ["a", "b"],
          questions: [
            { id: "b", question: "왜?", answer: "해설", status: "complete" },
          ],
        },
      ],
    },
    {
      "t1-01": {
        unsaved: true,
        clearing: false,
        dirtyTurns: [
          { id: "c", question: "다음 질문", answer: "", status: "pending" },
        ],
      },
      home: { turns: [{ id: "own", question: "홈 질문" }] },
    },
    "AI 질문 사용 문제 찾아줘",
  );
  assert.equal(context.problems[0].aiQuestionCount, 3);
  assert.equal(context.problems[1].aiQuestionCount, 0);
  assert.ok(context.problems[0].note.includes("fillna"));
  assert.deepEqual(context.problems[0].highlightedNotes, [highlight.text]);
  assert.ok(!JSON.stringify(context).includes("홈 질문"));
});
test("highlight-only requests exclude full notes and stale highlights, and removed source text is not recycled", () => {
  const stale = {
    ...highlight,
    id: "stale",
    text: "원문에 없는 내용",
    noteHash: "old",
  };
  const context = makeStudyContext(
    { ...data, highlights: { "t1-01": [highlight, stale] } },
    { records: [] },
    {},
    "highlighted 된 노트 내용만 추려줘",
  );
  assert.equal(context.highlightOnly, true);
  assert.equal(context.problems[0].note, undefined);
  assert.equal(context.problems[0].recentQuestions, undefined);
  assert.deepEqual(context.problems[0].highlightedNotes, [highlight.text]);
  const appended = note + "\n\n새 메모";
  assert.equal(
    activeHighlights(appended, rebaseHighlights(note, appended, [highlight]))
      .length,
    1,
  );
  assert.equal(
    activeHighlights(
      "완전히 다른 메모",
      rebaseHighlights(note, "완전히 다른 메모", [highlight]),
    ).length,
    0,
  );
  assert.equal(activeHighlights(note, [highlight])[0].text, highlight.text);
});
test("missing history stays unknown and long context reports omissions", () => {
  const context = makeStudyContext(
    { ...data, notes: { "t1-01": "a".repeat(140000) } },
    null,
    {},
    "노트 요약",
    "network error",
  );
  assert.equal(context.problems[1].aiQuestionCount, null);
  assert.deepEqual(context.coverage.truncated, ["t1-01"]);
  assert.equal(context.coverage.loadError, "network error");
});
test("home requests use separate study instructions and redact both keys without reference solutions or code drafts", () => {
  const context = makeStudyContext(
    { ...data, notes: { "t1-01": "secret-one secret-two" } },
    { records: [] },
    {},
    "노트 요약",
  );
  const request = makeStudyRequest({
    context,
    question: "요약해줘",
    history: [{ question: "홈 이전 질문", answer: "홈 답변" }],
    apiKey: ["secret-one", "secret-two"],
  });
  assert.match(request.systemInstruction.parts[0].text, /전체 학습 기록/);
  assert.equal(request.contents.length, 3);
  assert.equal(request.contents[0].parts[0].text, "홈 이전 질문");
  assert.ok(!JSON.stringify(request).includes("secret-one"));
  assert.ok(!JSON.stringify(request).includes("secret-two"));
  assert.ok(!JSON.stringify(request).includes("currentCode"));
});
