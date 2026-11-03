import React, { useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  CheckCheck,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  Clock3,
  Code2,
  Database,
  ExternalLink,
  FileCode2,
  FileSpreadsheet,
  Flag,
  FlaskConical,
  Lightbulb,
  Loader2,
  Maximize2,
  Minus,
  Play,
  Plus,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Square,
  Terminal,
  X,
  XCircle,
} from "lucide-react";
import CodeEditor from "./CodeEditor.jsx";
import { GeminiProvider, GeminiTutor } from "./GeminiTutor.jsx";
import PracticeNotes from "./PracticeNotes.jsx";
import { gradeNumeric, gradePrediction } from "./grading.js";
import SyncGate, { SyncStatus } from "./SyncGate.jsx";
import "./styles.css";

const BASE = import.meta.env.BASE_URL;
const STORAGE = "bigbungi.practice.v1";
const TYPE_INFO = {
  1: {
    name: "데이터 전처리",
    icon: Database,
  },
  2: {
    name: "머신러닝 모델링",
    icon: FlaskConical,
  },
  3: {
    name: "통계 분석",
    icon: BookOpen,
  },
};

function savedState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE)) || {};
  } catch {
    return {};
  }
}
const initial = savedState();
async function jsonFile(path) {
  const r = await fetch(BASE + path);
  if (!r.ok)
    throw new Error(
      `자료를 불러오지 못했습니다 (${r.status}). 새로고침해 주세요.`,
    );
  return r.json();
}

function Badge({ children, tone = "" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
function Empty({ icon: Icon = Terminal, title, children }) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon size={23} />
      </div>
      <strong>{title}</strong>
      <p>{children}</p>
    </div>
  );
}
function DataTable({ columns, rows }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((c, j) => (
                <td key={c}>
                  {(Array.isArray(row) ? row[j] : row[c]) == null ? (
                    <span className="null-value">NaN</span>
                  ) : (
                    String(Array.isArray(row) ? row[j] : row[c])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RetryProblemDialog({ problem, onContinue, onReset }) {
  const dialog = useRef(null);
  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    return () => element.close();
  }, []);
  return (
    <dialog
      ref={dialog}
      className="retry-problem-dialog"
      aria-labelledby="retry-problem-title"
      onCancel={(event) => {
        event.preventDefault();
        onContinue();
      }}
    >
      <h2 id="retry-problem-title">다시 풀기</h2>
      <strong>{problem.title}</strong>
      <p>이전에 풀이한 문제입니다. 코드를 초기화하고 다시 풀까요?</p>
      <p>노트·AI 대화·제출 답안·진행도는 그대로 두고 코드만 초기화합니다.</p>
      <div>
        <button autoFocus onClick={onContinue}>
          이어서 풀기
        </button>
        <button className="retry-reset" onClick={onReset}>
          코드만 초기화
        </button>
      </div>
    </dialog>
  );
}

function App({ initialState = initial, onStateChange, syncControls }) {
  const [catalog, setCatalog] = useState([]),
    [selected, setSelected] = useState(
      location.hash.slice(1) || initialState.selected || "t1-01",
    );
  const [problem, setProblem] = useState(null),
    [fetchError, setFetchError] = useState("");
  const [drafts, setDrafts] = useState(initialState.drafts || {}),
    [answers, setAnswers] = useState(initialState.answers || {}),
    [notes, setNotes] = useState(initialState.notes || {}),
    [progress, setProgress] = useState(initialState.progress || {});
  const [leftTab, setLeftTab] = useState("problem"),
    [bottomTab, setBottomTab] = useState("output");
  const [aiExpanded, setAiExpanded] = useState(false);
  const [retryProblem, setRetryProblem] = useState(null);
  const [solutions, setSolutions] = useState({}),
    [hintCount, setHintCount] = useState({}),
    [fileIndex, setFileIndex] = useState(0);
  const [runtime, setRuntime] = useState({
      ready: false,
      message: "Python 실행 환경 준비 중…",
    }),
    [running, setRunning] = useState(null),
    [results, setResults] = useState({});
  const [grades, setGrades] = useState({}),
    [grading, setGrading] = useState(false),
    [fontSize, setFontSize] = useState(13);
  const [search, setSearch] = useState(""),
    [navOpen, setNavOpen] = useState(false),
    [toast, setToast] = useState(""),
    [solutionLoading, setSolutionLoading] = useState(false);
  const worker = useRef(null),
    timeout = useRef(null),
    runMeta = useRef(null),
    fileCache = useRef({}),
    gradingCache = useRef(null),
    toastTimer = useRef(null);
  const problemRef = useRef(problem),
    codeRef = useRef("");
  problemRef.current = problem;
  const currentCode = problem ? (drafts[selected] ?? problem.starter) : "";
  codeRef.current = currentCode;
  const notify = useCallback((text) => {
    setToast(text);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 5000);
  }, []);
  const terminateRun = useRef(null);
  const problemBody = useRef(null), shortcutFocus = useRef(false);

  useEffect(() => {
    const switchQuestionTab = (event) => {
      if (
        !problem || !event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
        event.code !== "KeyQ" || event.isComposing || event.keyCode === 229 ||
        event.repeat || event.defaultPrevented || document.querySelector("dialog[open]")
      ) return;
      event.preventDefault();
      shortcutFocus.current = true;
      setAiExpanded(false);
      setLeftTab((tab) => tab === "ai" ? "problem" : "ai");
    };
    document.addEventListener("keydown", switchQuestionTab);
    return () => document.removeEventListener("keydown", switchQuestionTab);
  }, [problem]);

  useEffect(() => {
    if (!shortcutFocus.current) return;
    shortcutFocus.current = false;
    const target = leftTab === "ai"
      ? problemBody.current?.querySelector('textarea[aria-label="Gemini에게 질문"]')
      : problemBody.current;
    target?.focus();
  }, [leftTab]);

  useEffect(() => {
    jsonFile("content/catalog.json")
      .then(setCatalog)
      .catch((e) => setFetchError(e.message));
    return () => clearTimeout(toastTimer.current);
  }, []);
  useEffect(() => {
    if (!navOpen) return;
    const close = (e) => {
      if (e.key === "Escape") setNavOpen(false);
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [navOpen]);
  useEffect(() => {
    let live = true;
    setProblem(null);
    setFetchError("");
    setFileIndex(0);
    setLeftTab("problem");
    setAiExpanded(false);
    jsonFile(`content/problems/${selected}.json`)
      .then((p) => {
        if (live) setProblem(p);
      })
      .catch((e) => {
        if (live) setFetchError(e.message);
      });
    return () => {
      live = false;
    };
  }, [selected]);
  useEffect(() => {
    // Re-entering a graded problem prompts once; grading the open problem does
    // not interrupt the current attempt. Saved drafts alone remain resumable.
    if (
      problem &&
      (progress[problem.id]?.passed || progress[problem.id]?.attempts > 0)
    )
      setRetryProblem(problem);
  }, [problem?.id]);
  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE,
        JSON.stringify({ drafts, answers, notes, progress, selected }),
      );
    } catch {
      notify(
        "브라우저 저장 공간이 부족해 자동 저장하지 못했습니다. 코드를 다운로드해 주세요.",
      );
    }
    onStateChange?.({ drafts, answers, notes, progress, selected });
  }, [drafts, answers, notes, progress, selected, notify, onStateChange]);

  const startWorker = useCallback(() => {
    worker.current?.terminate();
    clearTimeout(timeout.current);
    runMeta.current = null;
    setRunning(null);
    setRuntime({ ready: false, message: "Python 실행 환경 준비 중…" });
    const w = new Worker(BASE + "python-worker.js");
    worker.current = w;
    timeout.current = setTimeout(() => {
      w.terminate();
      setRuntime({
        ready: false,
        error: true,
        message:
          "실행 환경 준비 시간이 초과됐습니다. 인터넷 연결을 확인하고 다시 시작하세요.",
      });
    }, 120000);
    w.onerror = (event) => {
      clearTimeout(timeout.current);
      setRuntime({
        ready: false,
        error: true,
        message: "실행 환경 오류: " + event.message,
      });
      setRunning(null);
    };
    w.onmessage = ({ data }) => {
      if (data.type === "status") {
        setRuntime({ ready: false, message: data.message });
        return;
      }
      if (data.type === "ready") {
        clearTimeout(timeout.current);
        setRuntime({ ready: true, message: `Python ${data.version} · 준비됨` });
        return;
      }
      if (data.type === "fatal") {
        clearTimeout(timeout.current);
        setRuntime({ ready: false, error: true, message: data.message });
        return;
      }
      if (data.type === "packages") {
        setRunning({ id: data.id, stage: "라이브러리 준비 중…" });
        return;
      }
      if (data.type === "executing") {
        clearTimeout(timeout.current);
        setRunning({ id: data.id, stage: "코드 실행 중…" });
        timeout.current = setTimeout(
          () =>
            terminateRun.current?.(
              "실행 시간이 60초를 초과했습니다. 반복문 또는 모델 크기를 확인하세요.",
            ),
          60000,
        );
        return;
      }
      if (data.type === "result") {
        clearTimeout(timeout.current);
        const meta = runMeta.current;
        setResults((prev) => ({
          ...prev,
          [data.id]: {
            ...data.result,
            duration: data.duration,
            code: meta?.code,
          },
        }));
        if (!data.result.error && data.result.answers)
          setAnswers((prev) => ({
            ...prev,
            [data.id]: {
              ...prev[data.id],
              ...Object.fromEntries(
                Object.entries(data.result.answers).map(([k, v]) => [
                  k,
                  v == null ? "" : String(v),
                ]),
              ),
            },
          }));
        setRunning(null);
        setRuntime((prev) => ({ ...prev, ready: true }));
        runMeta.current = null;
      }
    };
    w.postMessage({ type: "init" });
  }, []);
  terminateRun.current = (
    message = "실행을 중지했습니다. 코드는 보존됩니다.",
  ) => {
    const meta = runMeta.current;
    clearTimeout(timeout.current);
    worker.current?.terminate();
    if (meta)
      setResults((prev) => ({
        ...prev,
        [meta.id]: {
          stdout: "",
          stderr: "",
          error: message,
          code: meta.code,
          duration: 0,
          answers: {},
        },
      }));
    setRunning(null);
    runMeta.current = null;
    startWorker();
  };
  useEffect(() => {
    startWorker();
    return () => {
      worker.current?.terminate();
      clearTimeout(timeout.current);
    };
  }, [startWorker]);

  function select(id) {
    if (id === selected) {
      if (problem && (progress[id]?.passed || progress[id]?.attempts > 0))
        setRetryProblem(problem);
      return;
    }
    setRetryProblem(null);
    setSelected(id);
    history.replaceState(null, "", "#" + id);
    setNavOpen(false);
  }
  async function runCode() {
    const p = problemRef.current;
    if (!p || runMeta.current) return;
    if (!runtime.ready) {
      notify(
        runtime.error
          ? "실행 환경을 다시 시작한 뒤 코드를 실행해 주세요."
          : "Python 실행 환경을 준비 중입니다. 준비가 끝나면 다시 실행해 주세요.",
      );
      return;
    }
    const source = codeRef.current;
    runMeta.current = { id: p.id, code: source };
    setRunning({ id: p.id, stage: "데이터 준비 중…" });
    setBottomTab("output");
    clearTimeout(timeout.current);
    timeout.current = setTimeout(
      () =>
        terminateRun.current?.(
          "데이터 또는 라이브러리를 준비하지 못했습니다. 네트워크 상태를 확인하세요.",
        ),
      120000,
    );
    try {
      const pairs = await Promise.all(
        p.files.map(async (f) => {
          const key = `${p.id}/${f.name}`;
          if (!fileCache.current[key]) {
            const r = await fetch(BASE + "content/data/" + key);
            if (!r.ok) throw new Error(`${f.name} 다운로드 실패`);
            fileCache.current[key] = await r.text();
          }
          return [f.name, fileCache.current[key]];
        }),
      );
      if (runMeta.current?.code !== source || runMeta.current?.id !== p.id)
        return;
      worker.current.postMessage({
        type: "run",
        id: p.id,
        code: source,
        files: Object.fromEntries(pairs),
      });
    } catch (e) {
      clearTimeout(timeout.current);
      runMeta.current = null;
      setRunning(null);
      setResults((prev) => ({
        ...prev,
        [p.id]: {
          error: e.message,
          code: source,
          duration: 0,
          stdout: "",
          stderr: "",
        },
      }));
    }
  }
  async function grade() {
    if (!problem || grading) return;
    const result = results[selected];
    if (!result || result.code !== currentCode) {
      notify(
        "현재 코드를 먼저 실행해 주세요. 실행 후 답안을 채점할 수 있습니다.",
      );
      return;
    }
    if (result.error) {
      notify("실행 오류를 수정한 뒤 다시 실행해 주세요.");
      return;
    }
    setBottomTab("submit");
    setGrading(true);
    try {
      if (!gradingCache.current)
        gradingCache.current = await jsonFile("content/grading.json");
      const spec = gradingCache.current[selected];
      const evaluated =
        problem.type === 2
          ? gradePrediction(spec, result.submission)
          : gradeNumeric(spec, answers[selected] || {});
      setGrades((prev) => ({ ...prev, [selected]: evaluated }));
      setProgress((prev) => ({
        ...prev,
        [selected]: {
          ...prev[selected],
          attempts: (prev[selected]?.attempts || 0) + 1,
          passed: prev[selected]?.passed || evaluated.passed,
          score: evaluated.score,
          at: new Date().toISOString(),
        },
      }));
      if (evaluated.passed) notify("정답입니다! 한 걸음 더 가까워졌어요.");
    } catch (e) {
      setGrades((prev) => ({ ...prev, [selected]: { error: e.message } }));
    } finally {
      setGrading(false);
    }
  }
  async function reveal() {
    if (solutions[selected]) {
      setLeftTab("solution");
      return;
    }
    setSolutionLoading(true);
    try {
      const result = await jsonFile(`content/solutions/${selected}.json`);
      setSolutions((prev) => ({ ...prev, [selected]: result }));
      setLeftTab("solution");
      setProgress((prev) => ({
        ...prev,
        [selected]: { ...prev[selected], viewed: true },
      }));
    } catch (e) {
      notify(e.message);
    } finally {
      setSolutionLoading(false);
    }
  }
  function downloadCode() {
    const a = document.createElement("a");
    const url = URL.createObjectURL(
      new Blob([currentCode], { type: "text/x-python;charset=utf-8" }),
    );
    a.href = url;
    a.download = `${selected}_solution.py`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const result = results[selected],
    gradeResult = grades[selected];
  const solved = catalog.filter((p) => progress[p.id]?.passed).length;
  const totalProblems = catalog.length;
  const typeCounts = Object.fromEntries(
    [1, 2, 3].map((type) => [
      type,
      catalog.filter((p) => p.type === type).length,
    ]),
  );
  const kind = problem?.type || Number(selected[1]) || 1;
  const visible = catalog.filter(
    (p) =>
      p.type === kind &&
      (!search || `${p.title} ${p.tags.join(" ")}`.includes(search)),
  );
  const index = catalog.findIndex((p) => p.id === selected);
  const currentAnswers = answers[selected] || {};

  return (
    <div className="app-shell">
      <aside className={`sidebar ${navOpen ? "open" : ""}`}>
        <button
          className="mobile-nav-close"
          aria-label="문제 목록 닫기"
          onClick={() => setNavOpen(false)}
        >
          <X size={19} />
        </button>
        <a
          className="brand"
          href="#t1-01"
          onClick={(e) => {
            e.preventDefault();
            select("t1-01");
          }}
          aria-label="빅분기 첫 문제"
        >
          <span className="brand-mark">
            <span />
            <span />
            <span />
            <span />
          </span>
          <span>
            빅분기<span className="brand-dot">.</span>
            <small>BIG DATA, BIG STEP</small>
          </span>
        </a>
        <div className="sidebar-label">
          나의 실기 연습실 <Badge tone="muted">BETA</Badge>
        </div>
        <div className="type-nav">
          {[1, 2, 3].map((type) => {
            const Icon = TYPE_INFO[type].icon;
            const passed = catalog.filter(
              (p) => p.type === type && progress[p.id]?.passed,
            ).length;
            return (
              <button
                key={type}
                className={`type-button ${kind === type ? "active" : ""}`}
                onClick={() =>
                  select(
                    catalog.find((p) => p.type === type)?.id || `t${type}-01`,
                  )
                }
              >
                <Icon size={18} />
                <span>
                  <strong>작업형 {type}유형</strong>
                  <small>{TYPE_INFO[type].name}</small>
                </span>
                <span className="type-count">
                  {passed}
                  <em>/{typeCounts[type]}</em>
                </span>
              </button>
            );
          })}
        </div>
        <div className="question-list-heading">
          <span>문제 목록</span>
          <span>{typeCounts[kind]}문제</span>
        </div>
        <div className="search-field">
          <Search size={14} />
          <input
            aria-label="문제 검색"
            placeholder="제목 또는 키워드 검색"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <button aria-label="검색 지우기" onClick={() => setSearch("")}>
              <X size={12} />
            </button>
          )}
        </div>
        <nav className="question-list" aria-label="문제 목록">
          {visible.map((p) => (
            <button
              key={p.id}
              onClick={() => select(p.id)}
              className={`question-link ${selected === p.id ? "selected" : ""}`}
              aria-current={selected === p.id ? "page" : undefined}
            >
              <span className="question-number">
                {String(p.number).padStart(2, "0")}
              </span>
              <span className="question-name">{p.title}</span>
              {progress[p.id]?.passed ? (
                <CheckCircle2 size={14} className="solved-icon" />
              ) : selected === p.id ? (
                <span className="current-dot" />
              ) : (
                <Circle size={12} className="pending-icon" />
              )}
            </button>
          ))}
          {!visible.length && (
            <p className="no-search">검색 결과가 없습니다.</p>
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="progress-caption">
            <span>차곡차곡, 나의 학습 기록</span>
            <strong>
              {solved}
              <span> / {totalProblems}</span>
            </strong>
          </div>
          <div className="progress-track">
            <i
              style={{
                width: `${(solved / Math.max(totalProblems, 1)) * 100}%`,
              }}
            />
          </div>
          <p>
            <ShieldCheck size={13} /> 풀이 기록은 이 브라우저에 저장돼요
          </p>
        </div>
      </aside>
      {navOpen && (
        <button
          className="nav-backdrop"
          aria-label="목록 바깥 영역을 눌러 닫기"
          onClick={() => setNavOpen(false)}
        />
      )}
      <main className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-menu"
              onClick={() => setNavOpen(true)}
              aria-label="문제 목록 열기"
            >
              <BookOpen size={19} />
            </button>
            <span>실기 연습실</span>
            <ChevronRight size={14} />
            <strong>작업형 {kind}유형</strong>
          </div>
          <div className="topbar-right">
            {syncControls ? (
              <SyncStatus controls={syncControls} />
            ) : (
              <span className="autosave">
                <span />
                자동 저장됨
              </span>
            )}
            <a
              href="https://github.com/jha68/BigBunGi"
              target="_blank"
              rel="noreferrer"
              aria-label="GitHub 저장소 열기"
            >
              <Code2 size={17} />
            </a>
          </div>
        </header>
        {fetchError ? (
          <div className="fetch-error">
            <XCircle />
            <strong>{fetchError}</strong>
            <button onClick={() => location.reload()}>다시 불러오기</button>
          </div>
        ) : !problem ? (
          <div className="page-loading">
            <Loader2 className="spin" /> 문제를 불러오고 있어요
          </div>
        ) : (
          <>
            <section className="workspace">
              <div
                className={`problem-panel ${aiExpanded && leftTab === "ai" ? "gemini-expanded" : ""}`}
              >
                <div className="problem-heading">
                  <div className="problem-kicker">
                    <Badge tone={`type${kind}`}>작업형 {kind}유형</Badge>
                    <span>문제 {String(problem.number).padStart(2, "0")}</span>
                    {progress[selected]?.passed && (
                      <span className="solved-label">
                        <CheckCheck size={14} />
                        해결 완료
                      </span>
                    )}
                  </div>
                  <h2>{problem.title}</h2>
                  <div className="problem-meta">
                    <span
                      className={`difficulty difficulty-${problem.difficulty}`}
                    >
                      <i />
                      <i />
                      <i /> 난이도 {problem.difficulty}
                    </span>
                    <span>
                      <Clock3 size={13} />
                      {problem.minutes}분 권장
                    </span>
                    <span>
                      <Flag size={13} />
                      {problem.points}점 형식
                    </span>
                  </div>
                </div>
                <div
                  className="panel-tabs"
                  role="tablist"
                  aria-label="문제 정보"
                >
                  <button
                    role="tab"
                    aria-selected={leftTab === "problem"}
                    className={leftTab === "problem" ? "active" : ""}
                    onClick={() => setLeftTab("problem")}
                  >
                    <BookOpen size={14} />
                    문제
                  </button>
                  <button
                    role="tab"
                    aria-selected={leftTab === "data"}
                    className={leftTab === "data" ? "active" : ""}
                    onClick={() => setLeftTab("data")}
                  >
                    <Database size={14} />
                    데이터<span>{problem.files.length}</span>
                  </button>
                  <button
                    role="tab"
                    aria-selected={leftTab === "note"}
                    className={leftTab === "note" ? "active" : ""}
                    onClick={() => setLeftTab("note")}
                  >
                    <FileCode2 size={14} />
                    노트
                  </button>
                  <button
                    role="tab"
                    aria-selected={leftTab === "ai"}
                    aria-label="AI 질문"
                    aria-keyshortcuts="Alt+Q"
                    title="Alt + Q: 문제 ↔ AI 질문 전환"
                    className={
                      leftTab === "ai" ? "active gemini-tab" : "gemini-tab"
                    }
                    onClick={() => setLeftTab("ai")}
                  >
                    <Sparkles size={14} />
                    AI 질문
                    <small className="ai-tab-shortcut" aria-hidden="true">
                      Alt + Q로 탭 전환
                    </small>
                  </button>
                  {solutions[selected] && (
                    <button
                      role="tab"
                      aria-selected={leftTab === "solution"}
                      className={leftTab === "solution" ? "active" : ""}
                      onClick={() => setLeftTab("solution")}
                    >
                      해설
                    </button>
                  )}
                </div>
                <div
                  className={`problem-body ${leftTab === "ai" ? "gemini-mode" : ""}`}
                  ref={problemBody}
                  tabIndex={-1}
                >
                  <GeminiTutor
                    problem={problem}
                    code={currentCode}
                    result={result}
                    hidden={leftTab !== "ai"}
                    expanded={aiExpanded && leftTab === "ai"}
                    onExpandedChange={setAiExpanded}
                  />

                  {leftTab === "problem" && (
                    <>
                      <div className="section-label">문제 설명</div>
                      <p className="scenario">{problem.scenario}</p>
                      <div className="section-label steps-heading">
                        수행 조건
                      </div>
                      <ol className="step-list">
                        {problem.steps.map((s, i) => (
                          <li key={i}>
                            <span>{i + 1}</span>
                            <p>{s}</p>
                          </li>
                        ))}
                      </ol>
                      <div className="section-label">제출 형식</div>
                      {problem.type === 2 ? (
                        <div className="submission-contract">
                          <code>submission.csv</code>
                          <p>
                            열: <code>id</code>,{" "}
                            <code>{problem.submission.prediction}</code>
                            <br />
                            평가 데이터의 모든 행을 포함하고 인덱스는 저장하지
                            않습니다.
                          </p>
                        </div>
                      ) : (
                        <div className="answer-contract">
                          {problem.fields.map((f) => (
                            <div key={f.key}>
                              <code>{f.key}</code>
                              <span>
                                {f.label}
                                <small>{f.format}</small>
                              </span>
                            </div>
                          ))}
                          <p>
                            <Code2 size={13} />
                            코드의 <code>answers</code>에 넣으면 답안에 자동
                            반영됩니다.
                          </p>
                        </div>
                      )}
                      <div className="hint-area">
                        <button
                          onClick={() =>
                            setHintCount((prev) => ({
                              ...prev,
                              [selected]: Math.min(
                                (prev[selected] || 0) + 1,
                                problem.hints.length,
                              ),
                            }))
                          }
                          disabled={
                            (hintCount[selected] || 0) >= problem.hints.length
                          }
                        >
                          <Lightbulb size={15} />
                          <span>막혔다면 힌트 보기</span>
                          <small>
                            {hintCount[selected] || 0}/{problem.hints.length}
                          </small>
                          <ChevronDown size={14} />
                        </button>
                        {problem.hints
                          .slice(0, hintCount[selected] || 0)
                          .map((hint, i) => (
                            <p key={i}>
                              <strong>힌트 {i + 1}</strong>
                              {hint}
                            </p>
                          ))}
                      </div>
                    </>
                  )}
                  {leftTab === "data" && (
                    <>
                      <div className="section-label">
                        제공 데이터셋{" "}
                        <span className="muted-text">처음 8행 미리보기</span>
                      </div>
                      <div className="file-switcher">
                        {problem.files.map((f, i) => (
                          <button
                            key={f.name}
                            className={fileIndex === i ? "active" : ""}
                            onClick={() => setFileIndex(i)}
                          >
                            <FileSpreadsheet size={14} />
                            {f.name}
                          </button>
                        ))}
                      </div>
                      {(() => {
                        const f = problem.files[fileIndex] || problem.files[0];
                        return (
                          <>
                            <div className="dataset-info">
                              <strong>{f.description}</strong>
                              <div>
                                <Badge>{f.rows.toLocaleString()}행</Badge>
                                <Badge>{f.columns.length}열</Badge>
                                <Badge tone={f.missing ? "amber" : ""}>
                                  결측 {f.missing}개
                                </Badge>
                                <a
                                  className="download-link"
                                  href={`${BASE}content/data/${selected}/${f.name}`}
                                  download={f.name}
                                >
                                  <ArrowDownToLine size={14} />
                                  CSV 다운로드
                                </a>
                              </div>
                            </div>
                            <DataTable
                              columns={f.columns.map((c) => c.name)}
                              rows={f.preview}
                            />
                            <div className="section-label column-title">
                              변수 설명
                            </div>
                            <div className="column-definitions">
                              {f.columns.map((c) => (
                                <div key={c.name}>
                                  <code>{c.name}</code>
                                  <Badge>{c.type}</Badge>
                                  <p>{c.description}</p>
                                </div>
                              ))}
                            </div>
                            <div className="read-example">
                              <span>불러오기</span>
                              <code>pd.read_csv("data/{f.name}")</code>
                            </div>
                          </>
                        );
                      })()}
                    </>
                  )}
                  {leftTab === "note" && (
                    <PracticeNotes
                      key={problem.id}
                      problem={problem}
                      code={currentCode}
                      result={result}
                      value={notes[problem.id] || ""}
                      onChange={(text) =>
                        setNotes((previous) => ({
                          ...previous,
                          [problem.id]: text,
                        }))
                      }
                      onOpenAI={() => setLeftTab("ai")}
                      onAppend={(text) =>
                        setNotes((previous) => ({
                          ...previous,
                          [problem.id]: [previous[problem.id], text]
                            .filter(Boolean)
                            .join("\n\n"),
                        }))
                      }
                    />
                  )}
                  {leftTab === "solution" && solutions[selected] && (
                    <>
                      <div className="section-label">풀이 해설</div>
                      <p className="scenario">
                        {solutions[selected].explanation}
                      </p>
                      <div className="solution-warning">
                        <Lightbulb size={17} />
                        <p>
                          풀이를 읽은 뒤, 빈 에디터에서 다시 작성해 보세요. 다른
                          풀이도 조건과 답이 같으면 정답입니다.
                        </p>
                      </div>
                      <div className="solution-code-heading">
                        <strong>기준 풀이 · Python</strong>
                        <button
                          onClick={() => {
                            if (confirm("현재 코드를 기준 풀이로 바꿀까요?")) {
                              setDrafts((prev) => ({
                                ...prev,
                                [selected]: solutions[selected].code,
                              }));
                              notify(
                                "기준 풀이를 에디터에 넣었습니다. 실행해 결과를 확인해 보세요.",
                              );
                            }
                          }}
                        >
                          에디터에 적용
                          <ArrowRight size={13} />
                        </button>
                      </div>
                      <CodeEditor
                        key={`solution-${selected}`}
                        value={solutions[selected].code}
                        fontSize={12}
                        readOnly
                      />
                    </>
                  )}
                </div>
                <footer className="problem-footer">
                  <button onClick={reveal} disabled={solutionLoading}>
                    <BookOpen size={14} />
                    {solutionLoading ? "불러오는 중…" : "해설 보기"}
                  </button>
                  <span>직접 만든 시험형 연습문제</span>
                </footer>
              </div>
              <div className="coding-panel">
                <div className="editor-topbar">
                  <div className="file-tab">
                    <FileCode2 size={16} />
                    <strong>solution.py</strong>
                    <span className="file-dot" />
                  </div>
                  <div className="editor-tools">
                    <button
                      aria-label="코드 글자 크기 줄이기"
                      onClick={() => setFontSize((n) => Math.max(11, n - 1))}
                    >
                      <Minus size={14} />
                    </button>
                    <span>{fontSize}</span>
                    <button
                      aria-label="코드 글자 크기 키우기"
                      onClick={() => setFontSize((n) => Math.min(20, n + 1))}
                    >
                      <Plus size={14} />
                    </button>
                    <i />
                    <button aria-label="코드 다운로드" onClick={downloadCode}>
                      <ArrowDownToLine size={15} />
                    </button>
                    <button
                      aria-label="코드 초기화"
                      onClick={() => {
                        if (confirm("이 문제의 코드를 처음 상태로 되돌릴까요?"))
                          setDrafts((prev) => ({
                            ...prev,
                            [selected]: problem.starter,
                          }));
                      }}
                    >
                      <RotateCcw size={15} />
                    </button>
                  </div>
                </div>
                <CodeEditor
                  key={selected}
                  value={currentCode}
                  onChange={(value) =>
                    setDrafts((prev) => ({ ...prev, [selected]: value }))
                  }
                  onRun={runCode}
                  fontSize={fontSize}
                />
                <div className="run-toolbar">
                  <div
                    className={`runtime-status ${runtime.error ? "error" : ""}`}
                    title={runtime.message}
                  >
                    <span
                      className={runtime.ready ? "ready-dot" : "loading-dot"}
                    />
                    <span data-testid="runtime-status">
                      {running ? running.stage : runtime.message}
                    </span>
                    {runtime.error && (
                      <button onClick={startWorker}>다시 시작</button>
                    )}
                  </div>
                  <span className="keyboard-hint">⌘ / Ctrl ↵</span>
                  {running ? (
                    <button
                      className="stop-button"
                      onClick={() => terminateRun.current()}
                    >
                      <Square size={13} />
                      중지
                    </button>
                  ) : (
                    <button
                      className="run-button"
                      data-testid="run-code"
                      disabled={!runtime.ready}
                      onClick={runCode}
                    >
                      {runtime.ready ? (
                        <Play size={14} fill="currentColor" />
                      ) : (
                        <Loader2 size={14} className="spin" />
                      )}
                      코드 실행
                    </button>
                  )}
                </div>
                <div className="results-panel">
                  <div className="results-tabs">
                    <div role="tablist" aria-label="실행과 제출">
                      <button
                        role="tab"
                        aria-selected={bottomTab === "output"}
                        className={bottomTab === "output" ? "active" : ""}
                        onClick={() => setBottomTab("output")}
                      >
                        <Terminal size={14} />
                        실행 결과
                        {result?.error && <span className="error-dot" />}
                      </button>
                      <button
                        role="tab"
                        aria-selected={bottomTab === "submit"}
                        className={bottomTab === "submit" ? "active" : ""}
                        onClick={() => setBottomTab("submit")}
                      >
                        <CheckCheck size={15} />
                        답안 제출
                        {gradeResult?.passed && (
                          <CheckCircle2 size={13} className="solved-icon" />
                        )}
                      </button>
                    </div>
                    {result && (
                      <span
                        className={`execution-badge ${result.error ? "failed" : "success"}`}
                      >
                        {result.error ? (
                          <XCircle size={12} />
                        ) : (
                          <CheckCircle2 size={12} />
                        )}{" "}
                        {result.error
                          ? "실행 오류"
                          : `${result.duration.toFixed(2)}초`}
                      </span>
                    )}
                  </div>
                  <div className="result-content" aria-live="polite">
                    {bottomTab === "output" &&
                      (!result ? (
                        running?.id === selected ? (
                          <Empty icon={Loader2} title={running.stage}>
                            처음 사용하는 라이브러리는 준비에 시간이 걸릴 수
                            있어요.
                          </Empty>
                        ) : (
                          <Empty title="분석의 첫 줄을 실행해 보세요">
                            위의 실행 버튼 또는 <kbd>Ctrl</kbd> +{" "}
                            <kbd>Enter</kbd>를 누르면
                            <br />
                            실행 결과와 오류가 여기에 표시됩니다.
                          </Empty>
                        )
                      ) : (
                        <div className="console-output">
                          {result.code !== currentCode && (
                            <div className="stale-notice">
                              코드가 수정되었습니다. 아래는 이전 실행
                              결과입니다.
                            </div>
                          )}
                          {result.stdout && (
                            <>
                              <div className="console-label">STDOUT</div>
                              <pre>{result.stdout}</pre>
                            </>
                          )}
                          {result.stderr && (
                            <>
                              <div className="console-label warning-label">
                                안내 / 경고
                              </div>
                              <pre className="warning-output">
                                {result.stderr}
                              </pre>
                            </>
                          )}
                          {result.error && (
                            <>
                              <div className="console-label error-label">
                                <XCircle size={12} /> PYTHON ERROR
                              </div>
                              <pre
                                className="error-output"
                                data-testid="python-error"
                              >
                                {result.error}
                              </pre>
                            </>
                          )}
                          {result.display?.kind === "table" && (
                            <>
                              <div className="console-label">
                                결과 미리보기 · 총 {result.display.total}행
                              </div>
                              <DataTable
                                columns={result.display.columns}
                                rows={result.display.rows}
                              />
                            </>
                          )}
                          {result.display?.kind === "text" && (
                            <pre>{result.display.text}</pre>
                          )}
                          {Object.keys(result.answers || {}).length > 0 &&
                            !result.error && (
                              <div className="collected-answers">
                                <span>
                                  <Check size={13} />
                                  answers에서 답안을 가져왔습니다
                                </span>
                                <pre>
                                  {JSON.stringify(result.answers, null, 2)}
                                </pre>
                              </div>
                            )}
                          {result.submission && !result.error && (
                            <div className="submission-found">
                              <FileSpreadsheet size={20} />
                              <span>
                                <strong>submission.csv 생성 완료</strong>
                                <small>
                                  {result.submission.rows.length}행 ·{" "}
                                  {result.submission.columns.join(", ")}
                                </small>
                              </span>
                              <button onClick={() => setBottomTab("submit")}>
                                제출하기
                                <ArrowRight size={14} />
                              </button>
                            </div>
                          )}
                          {(result.plots || []).map((plot, i) => (
                            <img
                              className="result-plot"
                              key={i}
                              src={"data:image/png;base64," + plot}
                              alt={`분석 그래프 ${i + 1}`}
                            />
                          ))}
                          {!result.stdout &&
                            !result.error &&
                            !result.display &&
                            !result.submission &&
                            !Object.keys(result.answers || {}).length && (
                              <p className="no-output">
                                실행이 완료되었습니다. print()로 값을 출력하거나
                                마지막 줄에 데이터프레임을 작성해 보세요.
                              </p>
                            )}
                        </div>
                      ))}
                    {bottomTab === "submit" && (
                      <div className="answer-form">
                        <div className="answer-form-heading">
                          <strong>
                            {problem.type === 2
                              ? "예측 파일 제출"
                              : "최종 답안"}
                          </strong>
                          <span>
                            {problem.type === 2
                              ? "CSV 형식과 지표를 함께 확인해요"
                              : "answers에서 가져온 값을 수정할 수도 있어요"}
                          </span>
                        </div>
                        {problem.type === 2 ? (
                          <div className="prediction-submit">
                            {result?.submission ? (
                              <>
                                <div className="file-ready">
                                  <FileSpreadsheet size={24} />
                                  <div>
                                    <strong>submission.csv</strong>
                                    <span>
                                      {result.submission.rows.length}행 ·{" "}
                                      {result.submission.columns.join(", ")}
                                    </span>
                                  </div>
                                  <CheckCircle2 size={19} />
                                </div>
                                <DataTable
                                  columns={result.submission.columns}
                                  rows={result.submission.rows.slice(0, 5)}
                                />
                              </>
                            ) : (
                              <div className="submission-missing">
                                <FileSpreadsheet size={21} />
                                <p>
                                  코드에서 <code>submission.csv</code>를
                                  저장하고 실행하세요.
                                </p>
                              </div>
                            )}
                            <p className="grading-note">
                              {problem.submission.metric.toUpperCase()}{" "}
                              {problem.submission.threshold}{" "}
                              {problem.submission.higher ? "이상" : "이하"}이면
                              연습 기준 통과 · 실제 시험 점수와는 다릅니다.
                            </p>
                          </div>
                        ) : (
                          <div className="numeric-answers">
                            {problem.fields.map((f, i) => (
                              <label key={f.key}>
                                <span>
                                  <b>{i + 1}</b>
                                  {f.label}
                                </span>
                                <div>
                                  <input
                                    type="text"
                                    inputMode="decimal"
                                    aria-label={f.label}
                                    placeholder="답을 입력하세요"
                                    value={currentAnswers[f.key] ?? ""}
                                    onChange={(e) =>
                                      setAnswers((prev) => ({
                                        ...prev,
                                        [selected]: {
                                          ...prev[selected],
                                          [f.key]: e.target.value,
                                        },
                                      }))
                                    }
                                  />
                                  <small>{f.format}</small>
                                </div>
                              </label>
                            ))}
                          </div>
                        )}
                        {gradeResult && (
                          <div
                            className={`grade-result ${gradeResult.error ? "invalid" : gradeResult.passed ? "passed" : "retry"}`}
                            data-testid="grade-result"
                          >
                            {gradeResult.error ? (
                              <>
                                <XCircle size={17} />
                                <p>{gradeResult.error}</p>
                              </>
                            ) : (
                              <>
                                <div className="grade-result-title">
                                  {gradeResult.passed ? (
                                    <CheckCircle2 size={20} />
                                  ) : (
                                    <RotateCcw size={19} />
                                  )}
                                  <strong>
                                    {gradeResult.passed
                                      ? "잘하셨어요, 정답입니다!"
                                      : "한 번 더 도전해 볼까요?"}
                                  </strong>
                                  <span>{gradeResult.score}점</span>
                                </div>
                                <p>{gradeResult.message}</p>
                                {gradeResult.metric != null && (
                                  <div className="metric-value">
                                    {gradeResult.metricName}
                                    <strong>
                                      {gradeResult.metric.toFixed(4)}
                                    </strong>
                                    <span>
                                      기준 {gradeResult.threshold}{" "}
                                      {gradeResult.higher ? "이상" : "이하"}
                                    </span>
                                  </div>
                                )}
                                {gradeResult.details?.map((d) => (
                                  <div className="grade-detail" key={d.key}>
                                    {d.correct ? (
                                      <Check size={13} />
                                    ) : (
                                      <X size={13} />
                                    )}
                                    <span>{d.label}</span>
                                    <strong>
                                      {d.correct
                                        ? "정답"
                                        : `정답 ${d.expected}`}
                                    </strong>
                                  </div>
                                ))}
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="submission-bar">
                    <span>
                      <ShieldCheck size={13} />
                      {problem.type === 2
                        ? "예측값은 정답 데이터로 평가합니다"
                        : "반올림 오차를 고려해 채점합니다"}
                    </span>
                    <button
                      className="grade-button"
                      data-testid="grade-code"
                      disabled={!!running || grading}
                      onClick={grade}
                    >
                      {grading ? (
                        <Loader2 size={14} className="spin" />
                      ) : (
                        <Check size={15} />
                      )}
                      채점하기
                    </button>
                  </div>
                </div>
              </div>
            </section>
            <div className="workspace-footer">
              <span>
                <CheckCircle2 size={13} />
                원본 기출을 복제하지 않은 합성 데이터 기반 문제입니다.
              </span>
              <div>
                <button
                  disabled={index <= 0}
                  onClick={() => select(catalog[index - 1].id)}
                >
                  <ArrowLeft size={14} />
                  이전 문제
                </button>
                <button
                  disabled={index < 0 || index >= catalog.length - 1}
                  onClick={() => select(catalog[index + 1].id)}
                >
                  다음 문제
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          </>
        )}
        <footer className="site-footer">
          <span>
            빅분기<span className="brand-dot">.</span>{" "}
            <small>작은 연습이, 큰 실력이 되도록.</small>
          </span>
          <span>Python · pandas · scikit-learn · scipy · statsmodels</span>
        </footer>
      </main>
      {retryProblem && (
        <RetryProblemDialog
          problem={retryProblem}
          onContinue={() => setRetryProblem(null)}
          onReset={() => {
            setDrafts((previous) => ({
              ...previous,
              [retryProblem.id]: retryProblem.starter,
            }));
            setRetryProblem(null);
          }}
        />
      )}
      {toast && (
        <div className="toast" role="status">
          <CheckCircle2 size={17} />
          <span>{toast}</span>
          <button aria-label="알림 닫기" onClick={() => setToast("")}>
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(
  <SyncGate initialState={initial}>
    {(restored, onStateChange, syncControls) => (
      <GeminiProvider
        settingsApi={syncControls?.settingsApi}
        registerBeforeLogout={syncControls?.registerBeforeLogout}
      >
        <App
          initialState={restored}
          onStateChange={onStateChange}
          syncControls={syncControls}
        />
      </GeminiProvider>
    )}
  </SyncGate>,
);
