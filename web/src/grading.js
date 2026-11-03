// This is a transparent learning app, not a secure examination platform.
// Reference answers and held-out labels ship as static assets on GitHub Pages.

export function gradeNumeric(spec, answers) {
  const details = spec.fields.map((field) => {
    const raw = answers?.[field.key];
    const text = typeof raw === "string" || typeof raw === "number"
      ? String(raw).trim() : "";
    const decimal = text.match(/^[+-]?(\d+(?:\.\d*)?|\.\d+)(?:e([+-]?\d+))?$/i);
    const value = decimal ? Number(text) : NaN;
    const expected = spec.expected[field.key];
    // Count effective decimal places, allowing trailing zeros and scientific
    // notation without rounding the submitted value on the learner's behalf.
    const coefficient = decimal?.[1] || "";
    const fraction = coefficient.split(".")[1] || "";
    const trailingZeros = coefficient.replace(".", "").match(/0*$/)[0].length;
    const places = Math.max(0, fraction.length - Number(decimal?.[2] || 0) - trailingZeros);
    const precisionValid = !!decimal && places <= field.decimals;
    return {
      key: field.key,
      label: field.label,
      actual: Number.isFinite(value) ? value : null,
      expected,
      formatError: Number.isFinite(value) && !precisionValid
        ? field.decimals === 0
          ? "정수로 제출하세요."
          : `소수 ${field.decimals}자리까지 반올림해 제출하세요.`
        : "",
      correct:
        Number.isFinite(value) && precisionValid && value === expected,
    };
  });
  const count = details.filter((x) => x.correct).length;
  return {
    passed: count === details.length,
    score: Math.round((count / details.length) * 100),
    message: `${details.length}개 답안 중 ${count}개 정답`,
    details,
  };
}

export function rocAuc(truth, predictions) {
  const pairs = truth
    .map((y, i) => ({ y, p: predictions[i] }))
    .sort((a, b) => a.p - b.p);
  const positives = truth.filter((y) => y === 1).length;
  const negatives = truth.length - positives;
  if (!positives || !negatives)
    throw new Error("AUC 평가에는 양성·음성 데이터가 모두 필요합니다.");
  let sum = 0;
  for (let i = 0; i < pairs.length; ) {
    let end = i + 1;
    while (end < pairs.length && pairs[end].p === pairs[i].p) end++;
    const rank = (i + 1 + end) / 2;
    for (let j = i; j < end; j++) if (pairs[j].y === 1) sum += rank;
    i = end;
  }
  return (sum - (positives * (positives + 1)) / 2) / (positives * negatives);
}

export function macroF1(truth, predictions) {
  return (
    [0, 1, 2].reduce((total, label) => {
      let tp = 0,
        fp = 0,
        fn = 0;
      truth.forEach((y, i) => {
        const p = predictions[i];
        if (y === label && p === label) tp++;
        else if (p === label) fp++;
        else if (y === label) fn++;
      });
      const denominator = 2 * tp + fp + fn;
      return total + (denominator ? (2 * tp) / denominator : 0);
    }, 0) / 3
  );
}

export function gradePrediction(spec, submission) {
  if (!submission)
    throw new Error(
      "submission.csv가 없습니다. 코드를 실행해 파일을 먼저 저장하세요.",
    );
  const { columns, rows } = submission;
  if (
    !Array.isArray(columns) ||
    columns.length !== 2 ||
    !columns.includes("id") ||
    !columns.includes(spec.prediction)
  ) {
    throw new Error(
      `CSV에는 id, ${spec.prediction} 두 열만 있어야 합니다. index=False로 저장했는지 확인하세요.`,
    );
  }
  if (rows.length !== spec.ids.length)
    throw new Error(
      `제출 행 수가 다릅니다. 필요: ${spec.ids.length}행, 제출: ${rows.length}행`,
    );
  const byId = new Map();
  for (const row of rows) {
    if (
      Object.keys(row).length !== 2 ||
      !Object.hasOwn(row, "id") ||
      !Object.hasOwn(row, spec.prediction)
    )
      throw new Error(
        "CSV 행의 열 수가 헤더와 다릅니다. 구분자와 쉼표를 확인하세요.",
      );
    const id = Number(row.id);
    const value =
      row[spec.prediction] === "" || row[spec.prediction] == null
        ? NaN
        : Number(row[spec.prediction]);
    if (!Number.isSafeInteger(id) || String(row.id).trim() === "")
      throw new Error("id는 누락되지 않은 정수여야 합니다.");
    if (byId.has(id)) throw new Error(`중복된 id가 있습니다: ${id}`);
    if (!Number.isFinite(value))
      throw new Error(
        `예측값에 결측치 또는 숫자가 아닌 값이 있습니다. id=${id}`,
      );
    if (spec.metric === "roc_auc" && (value < 0 || value > 1))
      throw new Error("이탈 확률은 0과 1 사이여야 합니다.");
    if (spec.metric === "macro_f1" && ![0, 1, 2].includes(value))
      throw new Error("level은 0, 1, 2 중 하나여야 합니다.");
    byId.set(id, value);
  }
  const predictions = spec.ids.map((id) => {
    if (!byId.has(id))
      throw new Error(`test.csv에 있는 id가 제출 파일에 없습니다: ${id}`);
    return byId.get(id);
  });
  const metric =
    spec.metric === "roc_auc"
      ? rocAuc(spec.y, predictions)
      : spec.metric === "macro_f1"
        ? macroF1(spec.y, predictions)
        : Math.sqrt(
            spec.y.reduce((s, y, i) => s + (y - predictions[i]) ** 2, 0) /
              spec.y.length,
          );
  const passed = spec.higher
    ? metric >= spec.threshold
    : metric <= spec.threshold;
  const ratio = spec.higher
    ? (metric - spec.baseline) / (spec.threshold - spec.baseline)
    : (spec.baseline - metric) / (spec.baseline - spec.threshold);
  return {
    passed,
    metric,
    metricName: spec.metric.toUpperCase(),
    score: Math.round(Math.max(0, Math.min(100, ratio * 70))),
    threshold: spec.threshold,
    higher: spec.higher,
    rows: predictions.length,
    message: passed
      ? "연습 통과 기준을 달성했습니다."
      : "전처리와 검증 성능을 점검하고 다시 도전해 보세요.",
    details: [],
  };
}
