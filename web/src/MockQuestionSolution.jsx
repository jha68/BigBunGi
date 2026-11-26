import { CheckCircle2, ClipboardCheck, Pencil, Terminal } from "lucide-react";
import CodeEditor from "./CodeEditor.jsx";
import { ExamAnswerFields, ExamConsole, MockRunToolbar, TaskFiles } from "./MockExamControls.jsx";
import {
  gradeMockQuestion,
  MOCK_PREDICTION_FILE,
  MOCK_STARTER,
  retryAnswersFromOutput,
} from "./mock-exam.js";

function QuestionGrade({ grade }) {
  return (
    <>
      {grade.details?.map((detail) => (
        <div key={detail.key} className="mock-answer-review">
          {detail.correct ? (
            <CheckCircle2 size={17} aria-label="정답" />
          ) : (
            <span className="mock-error">오답</span>
          )}
          <strong>{detail.label}</strong>
          <span>제출 {detail.actual ?? "미입력"}</span>
          <span>정답 {detail.expected}</span>
          {detail.formatError && <small className="mock-error">{detail.formatError}</small>}
        </div>
      ))}
      {grade.metric != null && (
        <p>
          {grade.metricName} <strong>{grade.metric.toFixed(4)}</strong>
          {" · 모의 만점 기준 "}{grade.threshold.toFixed(4)} {grade.higher ? "이상" : "이하"}
        </p>
      )}
      {grade.error && <p className="mock-error">{grade.error}</p>}
    </>
  );
}

function verdict(problem, grade) {
  if (grade.error) return "제출 형식 확인";
  if (problem.type === 2) return grade.passed ? "모의 만점 기준 달성" : "모의 만점 기준 미달";
  if (grade.earned === problem.points) return "정답";
  return grade.earned ? "일부 정답" : "오답";
}

const hasAnswer = (answers) => Object.values(answers).some((value) => String(value ?? "").trim());

export default function MockQuestionSolution({
  problem, grade, submittedCode, gradingSpec, retry, updateRetry, retrying,
  onRetryingChange, runner, runId,
}) {
  const coding = problem.type !== 0;
  const prediction = problem.type === 2;
  const referenceCode = gradingSpec.code;
  const initialCode = submittedCode || MOCK_STARTER;
  const code = retry?.code ?? initialCode;
  const result = runner.results[runId];
  const currentResult = result?.code === code && !result.error ? result : null;
  const runningHere = runner.running?.id === runId;
  const automaticAnswers = retryAnswersFromOutput(problem.fields, currentResult, code);
  const answers = { ...automaticAnswers, ...retry?.answers };
  const canSubmit = !runningHere && (
    prediction ? Boolean(currentResult?.submission) : (!coding || Boolean(currentResult)) && hasAnswer(answers)
  );
  const retryGrade = retry?.grade;
  const retryPassed = retryGrade && (
    prediction ? retryGrade.passed : retryGrade.earned === problem.points
  );
  const toggle = (
    <button className="mock-secondary mock-retry-toggle" type="button"
      aria-expanded={retrying} aria-controls={problem.id + "-retry-submission"}
      onClick={() => onRetryingChange(!retrying)}>
      {!retrying && <Pencil size={14} aria-hidden="true" />}
      {retrying ? (coding ? "제출 코드 보기" : "다시 풀기 닫기") : "다시 풀기"}
    </button>
  );

  function run() {
    if (runner.running || !runner.runtime.ready) return;
    updateRetry((previous) => previous.grade ? { ...previous, grade: undefined } : previous);
    runner.onRun({
      id: runId,
      code,
      files: problem.files,
      dataId: problem.id,
      submissionName: MOCK_PREDICTION_FILE,
    });
  }

  function submit(event) {
    event.preventDefault();
    if (!canSubmit) return;
    updateRetry((previous) => {
      if (coding && (!currentResult || currentResult.code !== (previous.code ?? initialCode))) return previous;
      const submittedAnswers = { ...automaticAnswers, ...previous.answers };
      if (!prediction && !hasAnswer(submittedAnswers)) return previous;
      return {
        ...previous,
        grade: gradeMockQuestion(problem, gradingSpec, {
          answers: submittedAnswers,
          submission: currentResult?.submission,
        }),
      };
    });
  }

  return (
    <>
      {problem.scenario && <p>{problem.scenario}</p>}
      <ol>{problem.steps.map((step) => <li key={step}>{step}</li>)}</ol>
      {grade.adjustedEarned > grade.earned && (
        <p className="mock-original-score">최초 제출 {grade.earned}점 · 재채점 반영 {grade.adjustedEarned}점</p>
      )}
      <QuestionGrade grade={grade} />
      {retrying && <TaskFiles files={problem.files} />}
      {coding ? (
        <div className="mock-review-code">
          <section aria-label="내 코드">
            <div className="mock-review-code-heading"><h3>내 코드</h3>{toggle}</div>
            {retrying ? (
              <div className="mock-retry-editor">
                <CodeEditor
                  key="retry"
                  value={code}
                  label="내 Python 코드 수정"
                  onRun={run}
                  onChange={(value) => updateRetry((previous) => (
                    (previous.code ?? initialCode) === value
                      ? previous
                      : { ...previous, code: value, answers: {}, grade: undefined }
                  ))}
                />
                <MockRunToolbar runner={runner} runId={runId} onRun={run} />
                {(runningHere || result) && (
                  <>
                    <div className="mock-console-heading"><Terminal size={15} /> 실행 결과</div>
                    {result && result.code !== code && (
                      <p className="mock-retry-stale">현재 코드의 실행값을 확인하려면 다시 실행하세요.</p>
                    )}
                    <ExamConsole result={result} />
                  </>
                )}
              </div>
            ) : submittedCode ? (
              <CodeEditor key="submitted" value={submittedCode} readOnly label="내 Python 코드" />
            ) : (
              <p className="mock-retry-no-code">작성한 코드가 없습니다.</p>
            )}
          </section>
          {referenceCode && (
            <section aria-label="기준 풀이 코드">
              <div className="mock-review-code-heading"><h3>기준 풀이 코드</h3></div>
              <CodeEditor value={referenceCode} readOnly />
            </section>
          )}
        </div>
      ) : (
        <div className="mock-retry-short">{toggle}</div>
      )}
      <div id={problem.id + "-retry-submission"} hidden={!retrying}>
        {retrying && (
          <form className="mock-retry-submission" aria-label="재제출 답안" onSubmit={submit}>
            {prediction ? (
              <p>
                <code>{MOCK_PREDICTION_FILE}</code>
                {currentResult?.submission
                  ? ` 생성됨 · ${currentResult.submission.rows.length}행`
                  : "를 생성하는 코드를 실행하세요."}
              </p>
            ) : (
              <ExamAnswerFields fields={problem.fields} values={answers}
                onChange={(key, value) => updateRetry((previous) => ({
                  ...previous,
                  answers: { ...previous.answers, [key]: value },
                  grade: undefined,
                }))} />
            )}
            <div className="mock-retry-submit-actions">
              {coding && !prediction && !currentResult && <span>수정한 코드를 실행한 뒤 채점하세요.</span>}
              <button type="submit" className="mock-primary" disabled={!canSubmit}>
                <ClipboardCheck size={16} /> 다시 제출 · 채점
              </button>
            </div>
          </form>
        )}
      </div>
      {retryGrade && (
        <section className="mock-retry-grade" data-passed={Boolean(retryPassed)}
          role="status" aria-label="재채점 결과">
          <div className="mock-retry-grade-heading">
            <h3>재채점 결과</h3>
            <strong>{verdict(problem, retryGrade)} · {retryGrade.earned} / {problem.points}점</strong>
          </div>
          <QuestionGrade grade={retryGrade} />
        </section>
      )}
    </>
  );
}
