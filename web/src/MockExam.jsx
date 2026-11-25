import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowLeft, ArrowRight, CheckCircle2, ChevronDown, ClipboardCheck,
  Clock3, ExternalLink, FileSpreadsheet, Flag, Loader2, Play, Square, Terminal,
} from "lucide-react";
import CodeEditor from "./CodeEditor.jsx";
import {
  answerStatus, EXAM_SECTIONS, gradeExam, MOCK_CONTENT, MOCK_STORAGE, remainingTime,
} from "./mock-exam.js";
import "./mock-exam.css";

const CSV_NAME = "result.csv";
const STARTER = "# Python 코드를 작성하세요.\n";
const dateFormat = new Intl.DateTimeFormat("ko-KR", {
  year: "numeric", month: "long", day: "numeric", timeZone: "UTC",
});
const examDate = (date) => dateFormat.format(new Date(date));
const runPrefix = (attempt) => "mock:" + attempt.id + ":";

function readAttempts() {
  try {
    const stored = JSON.parse(localStorage.getItem(MOCK_STORAGE));
    if (stored?.completed && typeof stored.completed === "object") return stored;
  } catch {
    // This browser might block storage or contain an older value.
  }
  return { active: null, completed: {} };
}

function useExamFile(load, path) {
  const [response, setResponse] = useState(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!path) return;
    let active = true;
    load(MOCK_CONTENT + "/" + path).then(
      (data) => { if (active) setResponse({ path, data }); },
      () => { if (active) setResponse({ path, failed: true }); },
    );
    return () => { active = false; };
  }, [load, path, retry]);

  return {
    response: response?.path === path ? response : null,
    retry: () => {
      setResponse(null);
      setRetry((count) => count + 1);
    },
  };
}

function LoadState({ response, retry, children }) {
  if (response?.failed) {
    return (
      <div className="mock-status" role="alert">
        <p>시험 자료를 불러오지 못했습니다.</p>
        <button className="mock-secondary" onClick={retry}>다시 불러오기</button>
      </div>
    );
  }
  if (!response) {
    return <p className="mock-status" role="status"><Loader2 size={17} className="spin" /> 시험 자료 불러오는 중</p>;
  }
  return children(response.data);
}

function SourceLinks({ exam }) {
  return (
    <details className="mock-sources">
      <summary>복기 출처</summary>
      <ul>
        {exam.sources.map(({ name, url }) => (
          <li key={url}>
            <a href={url} target="_blank" rel="noreferrer">{name}<ExternalLink size={13} aria-hidden="true" /></a>
          </li>
        ))}
      </ul>
    </details>
  );
}

function ExamList({ exams, saved, onSelect, onResume, onResults }) {
  return (
    <>
      <div className="mock-intro">
        <h1>모의시험 연습하기</h1>
        <p>실기 복기 자료를 바탕으로 만든 회차별 모의시험입니다. 문제 조건과 실습용 CSV는 재구성했습니다.</p>
        <div className="mock-meta">
          <span><Clock3 size={16} /> 180분</span>
          <span><ClipboardCheck size={16} /> 100점 만점 · 60점 기준</span>
        </div>
      </div>
      {saved.active && (
        <section className="mock-resume" aria-label="진행 중인 시험">
          <div>
            <strong>제{saved.active.round}회 응시 중</strong>
            <p>답안은 이 브라우저에 자동 저장되며 시간은 계속 흐릅니다.</p>
          </div>
          <button className="mock-primary" onClick={onResume}>이어서 응시 <ArrowRight size={16} /></button>
        </section>
      )}
      <div className="mock-rounds" aria-label="회차 목록">
        {exams.map((exam) => (
          <article className="mock-round" key={exam.round}>
            <header>
              <h2>제{exam.round}회</h2>
              <time dateTime={exam.date}>{examDate(exam.date)}</time>
            </header>
            <p>{exam.summary}</p>
            <div className="mock-round-format">
              {exam.questionCount}문항 · {exam.round < 6 ? "단답형 및 작업형 1·2유형" : "작업형 1·2·3유형"}
            </div>
            <SourceLinks exam={exam} />
            <div className="mock-round-actions">
              {saved.completed[exam.round] && (
                <button className="mock-secondary" onClick={() => onResults(exam.round)}>최근 결과</button>
              )}
              <button
                className="mock-primary"
                disabled={Boolean(saved.active && saved.active.round !== exam.round)}
                onClick={() => saved.active ? onResume() : onSelect(exam.round)}
              >
                {saved.active?.round === exam.round ? "이어서 응시" : "응시 준비"}
                <ArrowRight size={15} />
              </button>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

function ExamReady({ exam, runtime, onStart, onRestart }) {
  return (
    <section className="mock-ready mock-panel" aria-labelledby="mock-ready-heading">
      <time dateTime={exam.date}>{examDate(exam.date)} 시행</time>
      <h1 id="mock-ready-heading">제{exam.round}회 실기 모의시험</h1>
      <p>시험 시작과 함께 180분이 주어집니다. 시간이 끝나면 저장된 답안이 자동 제출됩니다.</p>
      <dl className="mock-breakdown">
        {Object.entries(EXAM_SECTIONS).map(([type, name]) => {
          const items = exam.questions.filter((question) => question.type === Number(type));
          if (!items.length) return null;
          return (
            <div key={type}>
              <dt>{name}</dt>
              <dd>{items.length}문항 · {items.reduce((sum, question) => sum + question.points, 0)}점</dd>
            </div>
          );
        })}
      </dl>
      <ul className="mock-ready-rules">
        <li>수치와 텍스트는 답안란에 입력하세요. 작업형 제2유형은 코드로 <code>{CSV_NAME}</code>를 만든 뒤 답안에 등록하세요.</li>
        <li>답안과 코드는 이 브라우저에 저장됩니다. 화면을 나가거나 새로고침해도 남은 시간은 계속 줄어듭니다.</li>
        <li>작업형 제2유형의 점수 구간은 이 실습 데이터 기준으로 계산합니다.</li>
        {exam.supplementalCount > 0 && (
          <li>공개 복기에서 확인하기 어려운 {exam.supplementalCount}문항은 보완 문제로 표시했습니다.</li>
        )}
      </ul>
      <SourceLinks exam={exam} />
      <div className="mock-ready-actions">
        <span className={runtime.error ? "mock-error" : ""} role="status">{runtime.message}</span>
        {runtime.error && <button className="mock-secondary" onClick={onRestart}>Python 다시 준비</button>}
        <button className="mock-primary" disabled={!runtime.ready} onClick={onStart}>
          <Play size={15} /> 시험 시작
        </button>
      </div>
    </section>
  );
}

function ExamClock({ deadline }) {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const ticker = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(ticker);
  }, [deadline]);
  return (
    <span className={"mock-clock" + (deadline - now <= 600_000 ? " mock-clock-low" : "")}>
      <Clock3 size={17} aria-hidden="true" />
      <span>남은 시간</span>
      <strong role="timer" aria-label="시험 남은 시간">{remainingTime(deadline, now)}</strong>
    </span>
  );
}

function TaskFiles({ files }) {
  if (!files.length) return null;
  return (
    <div className="mock-file-list" aria-label="실습 데이터 파일">
      {files.map((file) => (
        <details className="mock-dataset" key={file.name}>
          <summary><code>data/{file.name}</code><small>{file.rows}행</small></summary>
          <dl>
            {file.columns.map(({ name, description }) => (
              <div key={name}><dt><code>{name}</code></dt><dd>{description}</dd></div>
            ))}
          </dl>
        </details>
      ))}
    </div>
  );
}

function PredictionAnswer({ item, result, savedFile, onRegister }) {
  const candidate = !result?.error && result?.submission;
  const expectedRows = item.files.find(({ name }) => name === "test.csv").rows;
  const formatError = candidate && (
    candidate.columns.length !== 1 || candidate.columns[0] !== item.submission.prediction
      ? "pred 열 한 개만 저장하세요."
      : candidate.rows.length !== expectedRows
        ? "평가 데이터와 제출 파일의 행 수가 일치해야 합니다."
        : ""
  );
  return (
    <div className="mock-prediction">
      <div>
        <FileSpreadsheet size={20} aria-hidden="true" />
        <span>
          <strong>{CSV_NAME}</strong>
          <small>{savedFile ? "답안 등록됨 · " + savedFile.rows.length + "행" : "파일을 만든 뒤 답안에 등록하세요."}</small>
        </span>
      </div>
      <button className="mock-secondary" disabled={!candidate || Boolean(formatError)}
        onClick={() => onRegister(candidate)}>
        {savedFile ? "새 파일로 교체" : "답안 파일 등록"}
      </button>
      {formatError && <p role="alert" className="mock-error">{formatError}</p>}
    </div>
  );
}

function ExamConsole({ result }) {
  const { stdout, stderr, error, display, plots = [] } = result || {};
  return (
    <div className="mock-console" aria-live="polite">
      {stdout && <pre>{stdout}</pre>}
      {stderr && <pre className="warning-output">{stderr}</pre>}
      {error && <pre className="error-output">{error}</pre>}
      {display?.kind === "text" && <pre>{display.text}</pre>}
      {display?.kind === "table" && (
        <div className="table-scroll">
          <table>
            <thead><tr>{display.columns.map((column, i) => <th key={i}>{column}</th>)}</tr></thead>
            <tbody>{display.rows.map((row, i) => (
              <tr key={i}>{row.map((value, j) => <td key={j}>{String(value ?? "NaN")}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {plots.map((plot, index) => <img className="result-plot" key={index} src={"data:image/png;base64," + plot} alt={"분석 그래프 " + (index + 1)} />)}
      {!stdout && !stderr && !error && !display && !plots.length && (
        <p>{result ? "코드 실행 완료" : "코드 실행 결과가 여기에 표시됩니다."}</p>
      )}
    </div>
  );
}

function ExamWorkspace({ exam, attempt, update, onSubmit, runner }) {
  const { questions } = exam;
  const index = attempt.index;
  const item = questions[index];
  const runId = runPrefix(attempt) + item.id;
  const result = runner.results[runId];
  const code = attempt.code[item.id] ?? STARTER;
  const complete = questions.filter((question) => answerStatus(question, attempt) === "complete").length;
  const marked = attempt.flags[item.id] === true;
  const moreThanOne = item.fields.length > 1;
  function move(index) {
    update((previous) => ({ ...previous, index }));
    window.scrollTo({ top: 0 });
  }
  function run() {
    if (Date.now() >= attempt.deadline || runner.running || !runner.runtime.ready) return;
    runner.onRun({ id: runId, code, files: item.files, dataId: item.id, submissionName: CSV_NAME });
  }

  return (
    <section className="mock-exam">
      <header className="mock-exam-header">
        <div>
          <h1>제{exam.round}회 실기 모의시험</h1>
          <time dateTime={exam.date}>{examDate(exam.date)} 시행</time>
        </div>
        <div>
          <ExamClock key={attempt.id} deadline={attempt.deadline} />
          <button className="mock-primary" onClick={() => onSubmit(complete)}>
            <ClipboardCheck size={16} /> 최종 제출
          </button>
        </div>
      </header>
      <nav aria-label="시험 문항" className="mock-navigator">
        <div className="mock-question-numbers">
          {questions.map((question, position) => {
            const status = answerStatus(question, attempt);
            const label = { complete: "작성 완료", partial: "일부 작성", empty: "미작성" }[status];
            const flagged = attempt.flags[question.id];
            return (
              <button key={question.id} aria-current={position === index ? "step" : undefined}
                className={"mock-number is-" + status}
                aria-label={(position + 1) + "번 · " + label + (flagged ? " · 검토 표시" : "")}
                onClick={() => move(position)}>
                {position + 1}{flagged && <Flag size={10} aria-hidden="true" />}
              </button>
            );
          })}
        </div>
        <small>답안 작성 {complete} / {questions.length}</small>
      </nav>
      <div className={"mock-workspace" + (item.type === 0 ? " mock-short-workspace" : "")}>
        <article className="mock-question mock-panel" key={item.id}>
          <header>
            <div className="mock-question-meta">
              <span>{EXAM_SECTIONS[item.type]}</span>
              <span>{item.points}점</span>
              {!item.recalled && <span className="mock-supplemental">보완 문항</span>}
            </div>
            <button className="mock-flag" aria-pressed={marked}
              onClick={() => update((previous) => ({ ...previous, flags: { ...previous.flags, [item.id]: !marked } }))}>
              <Flag size={15} /> 검토 표시
            </button>
          </header>
          <h2>{index + 1}. {item.title}</h2>
          {item.scenario && <p>{item.scenario}</p>}
          {item.steps.length === 1
            ? <p>{item.steps[0]}</p>
            : <ol>{item.steps.map((step) => <li key={step}>{step}</li>)}</ol>}
          <TaskFiles files={item.files} />
          {item.type === 2 ? (
            <PredictionAnswer item={item} result={result} savedFile={attempt.files[item.id]}
              onRegister={(file) => update((previous) => ({
                ...previous, files: { ...previous.files, [item.id]: file },
              }))} />
          ) : (
            <div className="mock-answer-fields">
              {item.fields.map((field, position) => (
                <label key={field.key}>
                  <span>{moreThanOne ? (position + 1) + ". " : ""}{field.label}<small>{field.format} · {field.points}점</small></span>
                  <input type="text" inputMode={field.decimals == null ? "text" : "decimal"}
                    aria-label={field.label} autoComplete="off" maxLength={300}
                    value={attempt.answers[item.id]?.[field.key] ?? ""}
                    onChange={(event) => {
                      const value = event.target.value;
                      update((previous) => ({
                        ...previous,
                        answers: { ...previous.answers, [item.id]: { ...previous.answers[item.id], [field.key]: value } },
                      }));
                    }} />
                </label>
              ))}
            </div>
          )}
        </article>
        {item.type !== 0 && (
          <div className="mock-editor mock-panel">
            <header><strong>solution.py</strong><span>Python</span></header>
            <CodeEditor key={runId} value={code} onRun={run}
              onChange={(value) => update((previous) => ({ ...previous, code: { ...previous.code, [item.id]: value } }))} />
            <div className="mock-run-bar">
              <span role="status">{runner.running?.stage || runner.runtime.message}</span>
              {runner.runtime.error ? (
                <button className="mock-secondary" onClick={runner.onRestartRuntime}>다시 시작</button>
              ) : runner.running ? (
                <button className="mock-secondary" onClick={runner.onStop}><Square size={13} /> 중지</button>
              ) : (
                <button className="mock-primary" disabled={!runner.runtime.ready} onClick={run}>
                  <Play size={14} /> 코드 실행
                </button>
              )}
            </div>
            <div className="mock-console-heading"><Terminal size={15} /> 실행 결과</div>
            <ExamConsole result={result} />
          </div>
        )}
      </div>
      <div className="mock-pagination">
        <button className="mock-secondary" disabled={index === 0} onClick={() => move(index - 1)}><ArrowLeft size={15} /> 이전 문항</button>
        <button className="mock-secondary" disabled={index + 1 === questions.length} onClick={() => move(index + 1)}>다음 문항 <ArrowRight size={15} /></button>
      </div>
      <details className="mock-memo">
        <summary>시험 메모장</summary>
        <textarea aria-label="시험 메모장" value={attempt.memo ?? ""} maxLength={10000}
          onChange={(event) => {
            const memo = event.target.value;
            update((previous) => ({ ...previous, memo }));
          }} />
      </details>
    </section>
  );
}

function ExamResults({ exam, attempt, load }) {
  const info = useExamFile(load, "keys/" + exam.round + ".json");
  return (
    <LoadState {...info}>
      {(keys) => {
        const grade = gradeExam(exam.questions, keys, attempt);
        return (
          <section className="mock-results">
            <header className="mock-panel mock-result-header">
              <div>
                <time dateTime={exam.date}>{examDate(exam.date)} 시행</time>
                <h1>제{exam.round}회 채점 결과</h1>
                <p>{attempt.submittedAt >= attempt.deadline ? "시간 종료로 자동 제출됨" : "시험 제출 완료"} · 60점 이상 모의시험 통과</p>
              </div>
              <div className={grade.total >= 60 ? "mock-score passed" : "mock-score"}>
                <strong>{grade.total}</strong><span> / 100점</span>
              </div>
            </header>
            <SourceLinks exam={exam} />
            <div className="mock-review">
              {exam.questions.map((item, index) => {
                const evaluated = grade.questions[index];
                const solution = keys[item.id].code;
                return (
                  <details className="mock-panel" key={item.id}>
                    <summary>
                      <span><strong>{index + 1}. {item.title}</strong><small>{EXAM_SECTIONS[item.type]}{!item.recalled && " · 보완 문항"}</small></span>
                      <span>{evaluated.earned} / {item.points}점 <ChevronDown size={15} aria-hidden="true" /></span>
                    </summary>
                    <div className="mock-review-body">
                      {item.scenario && <p>{item.scenario}</p>}
                      <ol>{item.steps.map((step) => <li key={step}>{step}</li>)}</ol>
                      {evaluated.details?.map((detail) => (
                        <div key={detail.key} className="mock-answer-review">
                          {detail.correct ? <CheckCircle2 size={17} /> : <span className="mock-error">오답</span>}
                          <strong>{detail.label}</strong>
                          <span>제출 {detail.actual ?? "미입력"}</span>
                          <span>정답 {detail.expected}</span>
                          {detail.formatError && <small className="mock-error">{detail.formatError}</small>}
                        </div>
                      ))}
                      {evaluated.metric != null && (
                        <p>{evaluated.metricName} <strong>{evaluated.metric.toFixed(4)}</strong> · 모의 만점 기준 {evaluated.threshold.toFixed(4)} {evaluated.higher ? "이상" : "이하"}</p>
                      )}
                      {evaluated.error && <p className="mock-error">{evaluated.error}</p>}
                      {solution && <details className="mock-solution"><summary>기준 풀이 코드</summary><pre>{solution}</pre></details>}
                      {attempt.code[item.id] && <details className="mock-solution"><summary>내 코드</summary><pre>{attempt.code[item.id]}</pre></details>}
                    </div>
                  </details>
                );
              })}
            </div>
          </section>
        );
      }}
    </LoadState>
  );
}

export default function MockExam({ load, ...runner }) {
  const [saved, setSaved] = useState(readAttempts);
  const [view, setView] = useState(() => saved.active
    ? { mode: "attempt", round: saved.active.round }
    : { mode: "list" });
  const [saveError, setSaveError] = useState(false);
  const state = useRef(saved);
  const storageFailed = useRef(false);
  const activeId = saved.active?.id;
  const deadline = saved.active?.deadline;
  const index = useExamFile(load, "index.json");
  const round = useExamFile(load, view.round ? "rounds/" + view.round + ".json" : null);

  const changeSaved = useCallback((change) => {
    const previous = storageFailed.current ? state.current : readAttempts();
    const next = change(previous);
    if (next === previous) return false;
    try {
      localStorage.setItem(MOCK_STORAGE, JSON.stringify(next));
      storageFailed.current = false;
      setSaveError(false);
    } catch {
      storageFailed.current = true;
      setSaveError(true);
    }
    state.current = next;
    setSaved(next);
    return true;
  }, []);

  useEffect(() => {
    const sync = (event) => {
      if (event.key !== MOCK_STORAGE || storageFailed.current) return;
      state.current = readAttempts();
      setSaved(state.current);
    };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);

  const finish = useCallback((id) => {
    changeSaved((previous) => {
      const attempt = previous.active;
      if (!attempt || attempt.id !== id) return previous;
      return {
        active: null,
        completed: {
          ...previous.completed,
          [attempt.round]: { ...attempt, submittedAt: Math.min(Date.now(), attempt.deadline) },
        },
      };
    });
  }, [changeSaved]);

  useEffect(() => {
    if (!activeId) return;
    function expire() {
      if (Date.now() >= deadline) finish(activeId);
    }
    const timeout = setTimeout(expire, Math.max(0, deadline - Date.now()));
    const interval = setInterval(expire, 1000);
    document.addEventListener("visibilitychange", expire);
    return () => {
      clearTimeout(timeout);
      clearInterval(interval);
      document.removeEventListener("visibilitychange", expire);
    };
  }, [activeId, deadline, finish]);

  const runnerRef = useRef(runner);
  runnerRef.current = runner;
  useEffect(() => {
    if (!activeId) return;
    const prefix = "mock:" + activeId + ":";
    return () => {
      const current = runnerRef.current;
      if (current.running?.id.startsWith(prefix)) current.onStop();
      current.onClearResults(prefix);
    };
  }, [activeId]);

  const goTo = (mode, roundNumber) => {
    setView({ mode, round: roundNumber });
    window.scrollTo({ top: 0 });
  };
  const start = (exam) => {
    const startedAt = Date.now();
    const attempt = {
      id: crypto.randomUUID(), round: exam.round, startedAt,
      deadline: startedAt + exam.minutes * 60_000,
      index: 0, answers: {}, code: {}, files: {}, flags: {}, memo: "",
    };
    if (changeSaved((previous) => previous.active ? previous : { ...previous, active: attempt })) {
      goTo("attempt", exam.round);
    }
  };
  const update = (change) => {
    changeSaved((previous) => {
      const attempt = previous.active;
      if (!attempt || attempt.id !== activeId || Date.now() >= attempt.deadline) return previous;
      return { ...previous, active: change(attempt) };
    });
  };
  function submit(complete, count) {
    const pending = count - complete;
    if (window.confirm((pending ? "답안을 모두 작성하지 않은 문항 " + pending + "개가 있습니다. " : "") + "시험을 종료하고 최종 제출할까요?")) {
      finish(activeId);
      window.scrollTo({ top: 0 });
    }
  }

  const attempt = saved.active?.round === view.round ? saved.active : null;
  const submitted = saved.completed[view.round];
  return (
    <div className={"mock-page" + (view.mode === "attempt" && attempt ? " mock-taking" : "")}>
      {view.mode !== "list" && (
        <button className="mock-back" onClick={() => goTo("list")}>
          <ArrowLeft size={16} /> 회차 목록
        </button>
      )}
      {saveError && <p className="mock-error" role="alert">브라우저에 저장하지 못했습니다. 이 탭을 닫으면 작성한 내용이 사라질 수 있습니다.</p>}
      {view.mode === "list" ? (
        <LoadState {...index}>
          {(exams) => (
            <ExamList exams={exams} saved={saved}
              onSelect={(round) => goTo("prepare", round)}
              onResume={() => goTo("attempt", saved.active.round)}
              onResults={(round) => goTo("result", round)} />
          )}
        </LoadState>
      ) : (
        <LoadState {...round}>
          {(exam) => {
            if (view.mode === "prepare") {
              return <ExamReady exam={exam} runtime={runner.runtime} onRestart={runner.onRestartRuntime} onStart={() => start(exam)} />;
            }
            if (view.mode === "attempt" && attempt) {
              return (
                <ExamWorkspace exam={exam} attempt={attempt} runner={runner} update={update}
                  onSubmit={(complete) => submit(complete, exam.questions.length)} />
              );
            }
            if (submitted) return <ExamResults key={submitted.id} exam={exam} attempt={submitted} load={load} />;
            return <p className="mock-status">응시 기록이 없습니다.</p>;
          }}
        </LoadState>
      )}
    </div>
  );
}
