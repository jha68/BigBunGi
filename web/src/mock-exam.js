import { DECIMAL_ANSWER, gradeNumeric, gradePrediction } from "./grading.js";
import { retryEarned } from "./mock-records.js";

export const MOCK_CONTENT = "content/mock-exams";
export const MOCK_PREDICTION_FILE = "result.csv";
export const MOCK_STARTER = "# Python 코드를 작성하세요.\n";
export const EXAM_SECTIONS = {
  0: "단답형",
  1: "작업형 제1유형",
  2: "작업형 제2유형",
  3: "작업형 제3유형",
};

export function answerStatus(question, attempt) {
  if (question.type === 2) return attempt.files[question.id] ? "complete" : "empty";
  const answers = attempt.answers[question.id] || {};
  const count = question.fields.filter(({ key }) => String(answers[key] ?? "").trim()).length;
  if (!count) return "empty";
  return count === question.fields.length ? "complete" : "partial";
}

function normalizeAnswer(value) {
  return String(value ?? "").normalize("NFKC").toLowerCase().replace(/[\s-]+/g, "");
}

export function gradeMockQuestion(question, spec, { answers = {}, submission }) {
  if (question.type === 2) {
    try {
      const result = gradePrediction(spec, submission);
      return { ...result, earned: Math.floor((result.score * question.points) / 500) * 5 };
    } catch (error) {
      return { earned: 0, error: error.message };
    }
  }
  const details = question.fields.map((field) => {
    if (field.decimals != null) {
      return gradeNumeric({ fields: [field], expected: spec.expected }, answers).details[0];
    }
    const accepted = spec.expected[field.key];
    const alternatives = Array.isArray(accepted) ? accepted : [accepted];
    const actual = String(answers?.[field.key] ?? "").trim();
    return {
      key: field.key,
      label: field.label,
      actual: actual || null,
      expected: alternatives[0],
      correct: Boolean(actual) && alternatives.some(
        (answer) => normalizeAnswer(answer) === normalizeAnswer(actual),
      ),
    };
  });
  const earned = question.fields.reduce(
    (points, field, index) => points + (details[index].correct ? field.points : 0), 0,
  );
  return { details, earned };
}

export function gradeExam(questions, answerKey, attempt) {
  const questionsGraded = questions.map((question) => {
    const { id, points } = question;
    const original = gradeMockQuestion(question, answerKey[id], {
      answers: attempt.answers[id],
      submission: attempt.files[id],
    });
    const adjustedEarned = Math.max(original.earned, Math.min(points, retryEarned(attempt.retries?.[id])));
    return { ...original, adjustedEarned };
  });
  return {
    total: questionsGraded.reduce((points, question) => points + question.adjustedEarned, 0),
    originalTotal: questionsGraded.reduce((points, question) => points + question.earned, 0),
    questions: questionsGraded,
  };
}

export function retryAnswersFromOutput(fields, result, code) {
  if (!result || result.error || result.code !== code) return {};
  const answers = {};
  for (const { key } of fields) {
    const value = result.answers?.[key];
    if (typeof value === "number" || (typeof value === "string" && value.trim())) {
      answers[key] = String(value);
    }
  }
  if (fields.length === 1) {
    const { key, decimals } = fields[0];
    const output = result.stdout?.trim();
    if (
      !(key in answers) && output && output.length <= 300 && !output.includes("\n") &&
      (decimals == null || DECIMAL_ANSWER.test(output))
    ) {
      answers[key] = output;
    }
  }
  return answers;
}

export function remainingTime(deadline, now) {
  const seconds = Math.max(0, Math.ceil((deadline - now) / 1000));
  return [Math.floor(seconds / 3600), Math.floor((seconds % 3600) / 60), seconds % 60]
    .map((part) => String(part).padStart(2, "0")).join(":");
}
