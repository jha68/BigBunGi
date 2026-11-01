import React, {
  createContext,
  memo,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Bot,
  Check,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  KeyRound,
  Loader2,
  RotateCcw,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Square,
  Trash2,
  XCircle,
} from "lucide-react";
import CodeEditor from "./CodeEditor.jsx";
import {
  askGemini,
  listModels,
  makeContext,
  preferredModel,
} from "./gemini.js";
import "./gemini.css";

const TutorContext = createContext(null);

export function GeminiProvider({ children }) {
  // Credentials and conversation stay in memory, outside the app's saved state.
  const [keyDraft, setKeyDraft] = useState("");
  const [connection, setConnection] = useState({ status: "idle", error: "" });
  const [models, setModels] = useState([]),
    [model, setModel] = useState("");
  const [turns, setTurns] = useState({}),
    [drafts, setDrafts] = useState({});
  const [pending, setPending] = useState(null);
  const activeKey = useRef(""),
    request = useRef(null),
    connecting = useRef(null);

  useEffect(
    () => () => {
      request.current?.abort();
      connecting.current?.abort();
    },
    [],
  );
  function updateKey(value) {
    activeKey.current = "";
    setKeyDraft(value);
    setModels([]);
    setModel("");
    setConnection({ status: "idle", error: "" });
  }
  async function connect() {
    if (request.current || connecting.current) return;
    const key = keyDraft.trim(),
      controller = new AbortController();
    connecting.current = controller;
    const timer = setTimeout(() => controller.abort(), 20000);
    setConnection({ status: "checking", error: "" });
    try {
      const available = await listModels(key, controller.signal);
      if (connecting.current !== controller) return;
      activeKey.current = key;
      setModels(available);
      setModel(preferredModel(available));
      setConnection({ status: "ready", error: "" });
    } catch (error) {
      if (connecting.current !== controller) return;
      activeKey.current = "";
      setConnection({
        status: "error",
        error:
          error.name === "AbortError"
            ? "연결 시간이 초과됐습니다. 네트워크를 확인해 주세요."
            : error.message || "연결하지 못했습니다.",
      });
    } finally {
      clearTimeout(timer);
      if (connecting.current === controller) connecting.current = null;
    }
  }
  function disconnect() {
    request.current?.abort();
    connecting.current?.abort();
    connecting.current = null;
    activeKey.current = "";
    setKeyDraft("");
    setModel("");
    setModels([]);
    setConnection({ status: "idle", error: "" });
  }
  function updateTurn(pid, id, change) {
    setTurns((previous) => ({
      ...previous,
      [pid]: (previous[pid] || []).map((turn) =>
        turn.id === id ? { ...turn, ...change } : turn,
      ),
    }));
  }
  async function send({
    problem,
    code,
    result,
    question,
    includeExecution,
    retryId,
  }) {
    if (request.current || connection.status !== "ready") return;
    let context;
    try {
      context = makeContext(problem, code, result, includeExecution);
    } catch (error) {
      return error.message;
    }
    if (!question.trim()) return "질문을 입력해 주세요.";
    if (question.length > 4000) return "질문은 4,000자 이내로 입력해 주세요.";
    const pid = problem.id,
      id = retryId || globalThis.crypto?.randomUUID?.() ||
        `turn-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      controller = new AbortController();
    const history = (turns[pid] || []).filter(
      (turn) => turn.id !== retryId && turn.answer && !turn.error,
    );
    const turn = {
      id,
      question: question.trim(),
      status: "pending",
      answer: "",
      error: "",
      model,
      contextLines: code.split("\n").length,
      withExecution: !!context.lastExecution,
      at: new Date().toISOString(),
    };
    if (retryId) updateTurn(pid, id, turn);
    else {
      setTurns((previous) => ({
        ...previous,
        [pid]: [...(previous[pid] || []), turn],
      }));
      setDrafts((previous) => ({ ...previous, [pid]: "" }));
    }
    request.current = controller;
    setPending({ pid, id });
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 90000);
    try {
      const response = await askGemini({
        apiKey: activeKey.current,
        model,
        context,
        question,
        history,
        signal: controller.signal,
      });
      updateTurn(pid, id, {
        answer: response.text,
        truncated: response.truncated,
        status: "complete",
      });
    } catch (error) {
      const message =
        error.name === "AbortError"
          ? timedOut
            ? "응답 시간이 초과됐습니다. 잠시 후 다시 시도해 주세요."
            : "응답 생성을 중지했습니다."
          : error instanceof TypeError
            ? "네트워크 연결을 확인해 주세요. Gemini에 요청을 보내지 못했습니다."
            : error.message;
      updateTurn(pid, id, { error: message, status: "error" });
    } finally {
      clearTimeout(timer);
      if (request.current === controller) {
        request.current = null;
        setPending(null);
      }
    }
  }
  return (
    <TutorContext.Provider
      value={{
        keyDraft,
        updateKey,
        connection,
        models,
        model,
        setModel,
        connect,
        disconnect,
        turns,
        drafts,
        setDrafts,
        pending,
        send,
        cancel: () => request.current?.abort(),
        clear: (pid) => setTurns((previous) => ({ ...previous, [pid]: [] })),
      }}
    >
      {children}
    </TutorContext.Provider>
  );
}

const markdownComponents = {
  pre({ children }) {
    const child = React.Children.toArray(children)[0];
    if (
      React.isValidElement(child) &&
      /language-(python|py)\b/.test(child.props.className || "")
    ) {
      return (
        <CodeEditor
          value={String(child.props.children).replace(/\n$/, "")}
          readOnly
          fontSize={11}
          label="Gemini Python 예시"
        />
      );
    }
    return <pre>{children}</pre>;
  },
  a({ href, children }) {
    return /^https?:\/\//.test(href || "") ? (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    ) : (
      <span>{children}</span>
    );
  },
  img({ alt }) {
    return <span>{alt || "이미지"}</span>;
  },
};
const Answer = memo(function Answer({ text }) {
  return (
    <div className="gemini-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={markdownComponents}
        skipHtml
      >
        {text}
      </ReactMarkdown>
    </div>
  );
});

export function GeminiTutor({ problem, code, result, hidden }) {
  const tutor = useContext(TutorContext);
  const [settingsOpen, setSettingsOpen] = useState(false),
    [contextOpen, setContextOpen] = useState(false);
  const [includeExecution, setIncludeExecution] = useState(true),
    [formError, setFormError] = useState("");
  const messages = useRef(null),
    input = useRef(null);
  const currentTurns = tutor.turns[problem.id] || [],
    draft = tutor.drafts[problem.id] || "";
  const ready = tutor.connection.status === "ready",
    showSettings = settingsOpen || !ready;
  const checking = tutor.connection.status === "checking",
    busy = !!tutor.pending;
  useEffect(() => {
    if (!hidden && messages.current)
      messages.current.scrollTop = messages.current.scrollHeight;
  }, [currentTurns, hidden]);
  if (hidden) return null;
  async function submit(question = draft, retryId) {
    setFormError("");
    const error = await tutor.send({
      problem,
      code,
      result,
      question,
      includeExecution,
      retryId,
    });
    if (error) setFormError(error);
  }
  const setDraft = (value) =>
    tutor.setDrafts((previous) => ({ ...previous, [problem.id]: value }));
  return (
    <section className="gemini-panel" aria-label="Gemini 튜터">
      <div className="gemini-heading">
        <span className="gemini-avatar">
          <Sparkles size={17} />
        </span>
        <div>
          <strong>Gemini 튜터</strong>
          <small>
            {ready
              ? tutor.models.find((m) => m.name === tutor.model)?.label
              : "내 문제와 코드를 함께 보는 AI"}
          </small>
        </div>
        <span className={`gemini-status ${ready ? "ready" : ""}`}>
          {ready ? "연결됨" : "키 연결 필요"}
        </span>
        <button
          aria-label="Gemini 연결 설정"
          title="연결 설정"
          onClick={() => setSettingsOpen((value) => !value)}
        >
          <Settings2 size={15} />
        </button>
        <button
          aria-label="이 문제의 AI 대화 지우기"
          title="이 문제의 대화 지우기"
          disabled={busy || !currentTurns.length}
          onClick={() => {
            if (confirm("이 문제의 AI 대화를 지울까요?"))
              tutor.clear(problem.id);
          }}
        >
          <Trash2 size={14} />
        </button>
      </div>
      {showSettings && (
        <div className="gemini-settings">
          <label htmlFor="gemini-key">
            내 Gemini API 키{" "}
            <a
              href="https://aistudio.google.com/apikey"
              target="_blank"
              rel="noreferrer"
            >
              키 발급
              <ExternalLink size={10} />
            </a>
          </label>
          <div className="gemini-key-row">
            <KeyRound size={14} />
            <input
              id="gemini-key"
              type="password"
              autoComplete="off"
              spellCheck={false}
              placeholder="Google AI Studio API 키"
              value={tutor.keyDraft}
              disabled={checking || busy}
              onChange={(event) => tutor.updateKey(event.target.value)}
            />
            <button
              onClick={tutor.connect}
              disabled={checking || busy || !tutor.keyDraft.trim()}
            >
              {checking ? (
                <Loader2 size={13} className="spin" />
              ) : ready ? (
                <Check size={13} />
              ) : null}
              {checking ? "확인 중" : ready ? "다시 연결" : "키 연결"}
            </button>
          </div>
          {ready && (
            <div className="gemini-model-row">
              <label htmlFor="gemini-model">모델</label>
              <select
                id="gemini-model"
                value={tutor.model}
                onChange={(e) => tutor.setModel(e.target.value)}
                disabled={busy}
              >
                {tutor.models.map((model) => (
                  <option key={model.name} value={model.name}>
                    {model.label}
                  </option>
                ))}
              </select>
              <button onClick={tutor.disconnect} disabled={busy}>
                연결 해제
              </button>
            </div>
          )}
          <p>
            <ShieldCheck size={12} />
            키·AI 대화는 이 탭에서만 유지하며 새로고침하면 지워집니다.
            <br />
            입력한 키의 할당량·요금 정책이 적용됩니다.
          </p>
          {tutor.connection.error && (
            <div className="gemini-error" role="alert">
              <XCircle size={14} />
              <span>{tutor.connection.error}</span>
            </div>
          )}
          {ready && (
            <button
              className="gemini-settings-done"
              onClick={() => setSettingsOpen(false)}
            >
              설정 접기
              <ChevronUp size={12} />
            </button>
          )}
        </div>
      )}
      <div className="gemini-context-bar">
        <button
          aria-expanded={contextOpen}
          onClick={() => setContextOpen((value) => !value)}
        >
          <span className="context-dot" />
          현재 문제 + 최신 코드 {code.split("\n").length}줄 첨부
          {contextOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>
      </div>
      {contextOpen && (
        <div className="gemini-context-detail">
          <strong>{problem.title}</strong>
          <p>수행 조건 · 변수 설명 · 데이터 미리보기 · 현재 코드</p>
          <label>
            <input
              type="checkbox"
              checked={includeExecution}
              onChange={(e) => setIncludeExecution(e.target.checked)}
            />
            최근 실행 결과·오류도 첨부
            {result && result.code !== code && <em>이전 코드의 실행 결과</em>}
          </label>
          <small>전체 CSV와 기준 풀이·정답 키는 보내지 않습니다.</small>
        </div>
      )}
      <div
        className="gemini-messages"
        ref={messages}
        role="log"
        aria-label="이 문제의 AI 대화"
        aria-live="polite"
      >
        {!currentTurns.length && (
          <div className="gemini-empty">
            <Bot size={27} />
            <strong>어디에서 막혔나요?</strong>
            <p>
              질문할 때마다 지금 작성한 코드와
              <br />
              현재 문제를 함께 읽고 답해 드려요.
            </p>
            <div>
              {[
                "정답 말고 다음 단계 힌트만 줘",
                "내 코드의 오류 원인을 알려줘",
                "문제 조건을 놓친 부분이 있어?",
              ].map((question) => (
                <button
                  key={question}
                  onClick={() => {
                    setDraft(question);
                    input.current?.focus();
                  }}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
        {currentTurns.map((turn) => (
          <div className="gemini-turn" key={turn.id}>
            <div className="gemini-question">
              <p>{turn.question}</p>
              <small>
                문제 + 코드 {turn.contextLines}줄
                {turn.withExecution ? " + 실행 결과" : ""}
              </small>
            </div>
            <div className="gemini-answer">
              <span className="gemini-answer-label">
                <Sparkles size={12} />
                Gemini
                {turn.status === "pending" && (
                  <span>
                    <Loader2 size={11} className="spin" />
                    답변 작성 중…
                  </span>
                )}
              </span>
              {turn.answer && <Answer text={turn.answer} />}
              {turn.truncated && (
                <p className="gemini-limit">
                  답변 길이 제한에 도달했습니다. 이어서 설명해 달라고 질문해
                  보세요.
                </p>
              )}
              {turn.error && (
                <div className="gemini-error" role="alert">
                  <XCircle size={14} />
                  <span>{turn.error}</span>
                  <button
                    disabled={busy || !ready}
                    onClick={() => submit(turn.question, turn.id)}
                  >
                    <RotateCcw size={12} />
                    다시 시도
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <form
        className="gemini-composer"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        {busy && tutor.pending.pid !== problem.id && (
          <p className="gemini-other-pending">
            다른 문제의 답변을 작성 중입니다. 기다리거나 중지해 주세요.
          </p>
        )}
        {formError && (
          <p className="gemini-form-error" role="alert">
            {formError}
          </p>
        )}
        <div className="gemini-input-wrap">
          <textarea
            ref={input}
            aria-label="Gemini에게 질문"
            rows={2}
            maxLength={4000}
            placeholder={
              ready
                ? "현재 문제나 코드에 대해 질문하세요…"
                : "키를 연결한 뒤 질문을 보내세요…"
            }
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                event.preventDefault();
                if (ready && !busy) submit();
              }
            }}
          />
          {busy ? (
            <button
              type="button"
              className="gemini-stop"
              aria-label="Gemini 응답 중지"
              onClick={tutor.cancel}
            >
              <Square size={14} />
            </button>
          ) : (
            <button
              type="submit"
              aria-label="Gemini 질문 보내기"
              disabled={!ready || !draft.trim()}
            >
              <Send size={15} />
            </button>
          )}
        </div>
        <div className="gemini-composer-note">
          <span>질문·첨부 내용은 Google Gemini로 전송됩니다.</span>
          <span>Ctrl / ⌘ ↵ 전송</span>
        </div>
      </form>
    </section>
  );
}
