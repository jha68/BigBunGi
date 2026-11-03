import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import {
  gradeNumeric,
  gradePrediction,
  rocAuc,
  macroF1,
} from "../src/grading.js";

test("numeric rounding tolerance accepts rounding, rejects blanks and NaN", () => {
  const spec = {
    expected: { result: 1.235 },
    fields: [{ key: "result", label: "값", decimals: 3 }],
  };
  assert.equal(gradeNumeric(spec, { result: "1.23455" }).passed, true);
  for (const result of ["", "   ", null, "NaN", Infinity, true, "1.234"])
    assert.equal(gradeNumeric(spec, { result }).passed, false);
});

test("AUC handles probability ties and constant predictions", () => {
  assert.equal(rocAuc([0, 1, 0, 1], [0.1, 0.8, 0.3, 0.9]), 1);
  assert.equal(rocAuc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]), 0.5);
  assert.equal(rocAuc([0, 1], [1, 0]), 0);
  assert.equal(macroF1([0, 1, 2], [0, 1, 2]), 1);
});

const spec = {
  ids: [10, 20, 30, 40],
  y: [0, 1, 0, 1],
  prediction: "p",
  metric: "roc_auc",
  higher: true,
  threshold: 0.75,
  baseline: 0.5,
};
const valid = {
  columns: ["id", "p"],
  rows: [
    { id: 40, p: 0.9 },
    { id: 10, p: 0.1 },
    { id: 20, p: 0.8 },
    { id: 30, p: 0.2 },
  ],
};
test("prediction grading aligns shuffled IDs instead of row order", () => {
  const result = gradePrediction(spec, valid);
  assert.equal(result.metric, 1);
  assert.equal(result.passed, true);
});
test("CSV rejects malformed headers, duplicates, missing IDs, bad probabilities and missing values", () => {
  assert.throws(() => gradePrediction(spec, null), /없습니다/);
  assert.throws(
    () =>
      gradePrediction(spec, { ...valid, columns: ["id", "p", "Unnamed: 0"] }),
    /두 열/,
  );
  assert.throws(
    () => gradePrediction(spec, { ...valid, rows: valid.rows.slice(1) }),
    /행 수/,
  );
  assert.throws(
    () =>
      gradePrediction(spec, {
        ...valid,
        rows: [{ id: 10, p: 0.5 }, ...valid.rows.slice(1)],
      }),
    /중복/,
  );
  assert.throws(
    () =>
      gradePrediction(spec, {
        ...valid,
        rows: [{ id: 99, p: 0.5 }, ...valid.rows.slice(1)],
      }),
    /없습니다/,
  );
  for (const p of [NaN, "", Infinity, 1.1, -0.1])
    assert.throws(() =>
      gradePrediction(spec, {
        ...valid,
        rows: [{ id: 40, p }, ...valid.rows.slice(1)],
      }),
    );
});
test("RMSE and macro F1 use their specified direction and labels", () => {
  const regression = {
    ...spec,
    metric: "rmse",
    higher: false,
    y: [1, 2, 3, 4],
    threshold: 1,
    baseline: 4,
  };
  assert.equal(
    gradePrediction(regression, {
      columns: ["id", "p"],
      rows: spec.ids.map((id, i) => ({ id, p: i + 1 })),
    }).metric,
    0,
  );
  const multi = { ...spec, metric: "macro_f1", y: [0, 1, 2, 1] };
  assert.throws(
    () =>
      gradePrediction(multi, {
        columns: ["id", "p"],
        rows: spec.ids.map((id) => ({ id, p: 4 })),
      }),
    /0, 1, 2/,
  );
});
for (const id of Array.from(
  { length: 10 },
  (_, index) => `t2-${String(index + 1).padStart(2, "0")}`,
)) {
  test(`real reference metric matches scikit-learn: ${id}`, () => {
    const path = new URL(`../../tests/fixtures/${id}.json`, import.meta.url);
    assert.ok(
      existsSync(path),
      "Run Python content tests first to generate metric fixtures.",
    );
    const { spec, submission, metric } = JSON.parse(readFileSync(path, "utf8"));
    const result = gradePrediction(spec, submission);
    assert.ok(
      Math.abs(result.metric - metric) < 1e-10,
      `${result.metric} != ${metric}`,
    );
    assert.equal(result.passed, true);
  });
}
