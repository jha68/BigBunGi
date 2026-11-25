import { gradeNumeric, gradePrediction } from "./grading.js";

export const MOCK_STORAGE = "bigbungi.mock-exam.v1";
export const MOCK_CONTENT = "content/mock-exams";
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

export function gradeExam(questions, answerKey, attempt) {
  const questionsGraded = questions.map((question) => {
    const spec = answerKey[question.id];
    if (question.type === 2) {
      try {
        const result = gradePrediction(spec, attempt.files[question.id]);
        return { ...result, earned: Math.floor((result.score * question.points) / 500) * 5 };
      } catch (error) {
        return { earned: 0, error: error.message };
      }
    }
    const answers = attempt.answers[question.id] || {};
    const details = question.fields.map((field) => {
      if (field.decimals != null) return gradeNumeric({ fields: [field], expected: spec.expected }, answers).details[0];
      const accepted = spec.expected[field.key];
      const alternatives = Array.isArray(accepted) ? accepted : [accepted];
      const actual = (answers[field.key] || "").trim();
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
  });
  return {
    total: questionsGraded.reduce((points, question) => points + question.earned, 0),
    questions: questionsGraded,
  };
}

export function remainingTime(deadline, now) {
  const seconds = Math.max(0, Math.ceil((deadline - now) / 1000));
  return [Math.floor(seconds / 3600), Math.floor((seconds % 3600) / 60), seconds % 60]
    .map((part) => String(part).padStart(2, "0")).join(":");
}
