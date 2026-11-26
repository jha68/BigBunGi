import test from "node:test";
import assert from "node:assert/strict";
import { gradePrediction } from "../src/grading.js";
import { answerStatus, gradeExam, gradeMockQuestion, remainingTime, retryAnswersFromOutput } from "../src/mock-exam.js";

const trueClasses = [1, 2, 3, 4];
const makeFile = (values) => ({ columns: ["pred"], rows: values.map((pred) => ({ pred })) });
const predictionSpec = {
  ordered: true, filename: "result.csv", prediction: "pred", ids: [7, 3, 5, 4],
  metric: "macro_f1", labels: trueClasses, y: trueClasses, higher: true,
  baseline: 0.1, threshold: 0.9, scale: 100,
};

test("a four-class mock CSV uses the unchanged evaluation row order", () => {
  assert.equal(gradePrediction(predictionSpec, makeFile(trueClasses)).metric, 1);
  assert.equal(gradePrediction(predictionSpec, makeFile([4, 3, 2, 1])).metric, 0);
  assert.throws(() => gradePrediction(predictionSpec, makeFile([0, 2, 3, 4])), /중 하나/);
  assert.throws(() => gradePrediction(predictionSpec, makeFile([1, 2, 3])), /행 수/);
  assert.throws(() => gradePrediction(predictionSpec, {
    columns: ["pred"], rows: [{ pred: 1, id: 7 }, { pred: 2 }, { pred: 3 }, { pred: 4 }],
  }), /열 수/);
});

test("MAE and RMSLE apply their own formulas and RMSLE rejects negative values", () => {
  const spec = { ...predictionSpec, higher: false, y: [1, 3, 7, 15], baseline: 8, threshold: 1 };
  assert.equal(gradePrediction({ ...spec, metric: "mae" }, makeFile([1, 2, 8, 13])).metric, 1);
  const rmsle = { ...spec, metric: "rmsle" };
  assert.ok(Math.abs(gradePrediction(rmsle, makeFile([0, 1, 3, 7])).metric - Math.log(2)) < 1e-12);
  assert.throws(() => gradePrediction(rmsle, makeFile([-1, 1, 3, 7])), /음수가 아닌/);
});

test("a final exam combines short answers, subquestion points, and CSV points", () => {
  const questions = [
    { id: "text", type: 0, points: 3, fields: [{ key: "answer", label: "이름", points: 3 }] },
    { id: "numeric", type: 3, points: 15, fields: [
      { key: "a", label: "1", decimals: 2, points: 5 },
      { key: "b", label: "2", decimals: 2, points: 5 },
      { key: "c", label: "3", decimals: 2, points: 5 },
    ] },
    { id: "csv", type: 2, points: 40 },
  ];
  const answerKey = {
    text: { expected: { answer: ["Leaky ReLU"] } },
    numeric: { expected: { a: 2.17, b: 0.2, c: 0.3 } },
    csv: predictionSpec,
  };
  const attempt = {
    answers: { text: { answer: "leaky  ReLU" }, numeric: { a: "2.170", b: "-0.2" } },
    files: { csv: makeFile(trueClasses) },
  };
  assert.equal(answerStatus(questions[1], attempt), "partial");
  const result = gradeExam(questions, answerKey, attempt);
  assert.deepEqual(result.questions.map(({ earned }) => earned), [3, 5, 40]);
  assert.equal(result.total, 48);
});

test("the countdown derives from an absolute deadline and stops at zero", () => {
  assert.equal(remainingTime(10_800_000, 0), "03:00:00");
  assert.equal(remainingTime(10_800_000, 1_001), "02:59:59");
  assert.equal(remainingTime(10_800_000, 10_800_100), "00:00:00");
});

test("a review retry grades the revised answer without modifying the completed attempt", () => {
  const question = {
    id: "r12-01", type: 1, points: 10,
    fields: [{ key: "answer_1", label: "집계 행 수", decimals: 0, points: 10 }],
  };
  const spec = { expected: { answer_1: 12 } };
  const attempt = { answers: { [question.id]: { answer_1: "3" } }, files: {} };
  const result = { code: "print(12)", stdout: "12\n" };
  const answers = retryAnswersFromOutput(question.fields, result, result.code);
  assert.equal(gradeMockQuestion(question, spec, { answers }).earned, 10);
  assert.equal(gradeExam([question], { [question.id]: spec }, attempt).total, 0);
  assert.equal(attempt.answers[question.id].answer_1, "3");
});

test("retry answers can use current structured output or one unambiguous console value", () => {
  const fields = [{ key: "a", decimals: 2 }, { key: "b", decimals: null }];
  const result = { code: "trial", stdout: "some diagnostics\n3.21\n", answers: { a: 3.21, b: "서울" } };
  assert.deepEqual(retryAnswersFromOutput(fields, result, "trial"), { a: "3.21", b: "서울" });
  assert.deepEqual(retryAnswersFromOutput(fields, result, "edited"), {});
  assert.deepEqual(retryAnswersFromOutput(fields, { ...result, error: "Runtime error" }, "trial"), {});
  assert.deepEqual(retryAnswersFromOutput(fields, { code: "trial", stdout: "3.21\n" }, "trial"), {});
  assert.deepEqual(retryAnswersFromOutput(fields.slice(0, 1), { code: "trial", stdout: "debug\n3.21\n" }, "trial"), {});
  assert.deepEqual(retryAnswersFromOutput(fields.slice(0, 1), { code: "trial", stdout: "0\n" }, "trial"), { a: "0" });
  assert.deepEqual(retryAnswersFromOutput(fields.slice(1), { code: "trial", stdout: "서울\n" }, "trial"), { b: "서울" });
});
