import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Bot,
  Check,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  KeyRound,
  Loader2,
  Maximize2,
  Minimize2,
  RotateCcw,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Square,
  Trash2,
  XCircle,
} from "lucide-react";
import Answer from "./Markdown.jsx";
import {
  modelPriceLabel,
  modelPriceDetail,
  pricingSource,
  affordableModels,
  freeTierLabel,
} from "./model-pricing.js";
import { askGemini, listModels, makeContext, redactSecrets } from "./gemini.js";
import { withKeyFallback } from "./gemini-failover.js";
import "./gemini.css";
import { createSettingsStore } from "./gemini-settings.js";
import { createConversationStore } from "./gemini-history.js";

const TutorContext = createContext(null);

export function GeminiProvider({
  children,
  settingsApi,
  registerBeforeLogout,
}) {
  const [access, setAccess] = useState(null);
  const accessPromise = useRef(null);
  useEffect(() => {
    accessPromise.current = fetch(
      import.meta.env.BASE_URL + "content/model-access.json",
      { cache: "no-store", signal: AbortSignal.timeout(15000) },
    )
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setAccess(data);
        return data;
      })
      .catch(() => null);
  }, []);
  // Plaintext credentials and conversations stay out of browser storage/backups.
  const [persistence, setPersistence] = useState({
    state: settingsApi ? "loading" : "session",
    error: "",
  });
  const store = useMemo(
    () =>
      settingsApi ? createSettingsStore(settingsApi, setPersistence) : null,
    [settingsApi],
  );
  const preferred = useRef(""),
    providerLive = useRef(true);
  const [keyDraft, setKeyDraft] = useState("");
  const [backupKeyDraft, setBackupKeyDraft] = useState("");
  const [activeKeyIndex, setActiveKeyIndex] = useState(0);
  const [connection, setConnection] = useState({ status: "idle", error: "" });
  const [models, setModels] = useState([]),
    [model, setModel] = useState("");
  const [turns, setTurns] = useState({}),
    [drafts, setDrafts] = useState({});
  const [conversationStates, setConversationStates] = useState({});
  const historyStore = useMemo(
    () =>
      createConversationStore(settingsApi, (pid, record) => {
        setTurns((previous) => ({ ...previous, [pid]: record.turns }));
        setConversationStates((previous) => ({ ...previous, [pid]: record }));
      }),
    [settingsApi],
  );
  const [pending, setPending] = useState(null);
  const [noteGenerations, setNoteGenerations] = useState({});
  const activeKey = useRef(""),
    configuredKeys = useRef([]),
    activeIndex = useRef(0),
    request = useRef(null),
    connecting = useRef(null);

  async function restoreSettings() {
    if (!store) return;
    try {
      const saved = await store.load();
      if (providerLive.current && saved.settings) {
        preferred.current = saved.settings.model;
        setKeyDraft(saved.settings.apiKey);
        setBackupKeyDraft(saved.settings.backupApiKey || "");
        await connect({
          key: saved.settings.apiKey,
          backupKey: saved.settings.backupApiKey || "",
          activeKeyIndex: saved.settings.activeKeyIndex || 0,
          rememberedModel: saved.settings.model,
          persist: false,
        });
      }
    } catch {
      /* The persistence status exposes a retry without erasing saved data. */
    }
  }
  useEffect(() => {
    if (!store) return;
    let live = true;
    store.start();
    store
      .load()
      .then((saved) => {
        if (!live || !saved.settings) return;
        preferred.current = saved.settings.model;
        setKeyDraft(saved.settings.apiKey);
        setBackupKeyDraft(saved.settings.backupApiKey || "");
        connect({
          key: saved.settings.apiKey,
          backupKey: saved.settings.backupApiKey || "",
          activeKeyIndex: saved.settings.activeKeyIndex || 0,
          rememberedModel: saved.settings.model,
          persist: false,
        });
      })
      .catch(() => {});
    return () => {
      live = false;
      store.stop();
    };
  }, [store]);

  useEffect(() => {
    providerLive.current = true;
    return () => {
      providerLive.current = false;
      request.current?.abort();
      connecting.current?.abort();
      connecting.current = null;
    };
  }, []);
  useEffect(() => {
    historyStore.start();
    const warn = (event) => {
      if (historyStore.hasUnsaved()) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => {
      window.removeEventListener("beforeunload", warn);
      historyStore.stop();
    };
  }, [historyStore]);
  useEffect(
    () =>
      registerBeforeLogout?.(async () => {
        request.current?.abort();
        return historyStore.flushAll();
      }),
    [historyStore, registerBeforeLogout],
  );
  function updateKey(value, index = 0) {
    activeKey.current = "";
    if (index === 1) setBackupKeyDraft(value);
    else setKeyDraft(value);
    setModels([]);
    setModel("");
    setConnection({ status: "idle", error: "" });
  }
  function saveKeys(chosenModel = preferred.current) {
    if (configuredKeys.current[0] && chosenModel)
      store?.save({
        apiKey: configuredKeys.current[0],
        backupApiKey: configuredKeys.current[1] || "",
        activeKeyIndex: activeIndex.current,
        model: chosenModel,
      });
  }
  async function connect(options = {}) {
    if (request.current || connecting.current) return;
    const keys = [
        (options.key ?? keyDraft).trim(),
        (options.backupKey ?? backupKeyDraft).trim(),
      ],
      controller = new AbortController();
    connecting.current = controller;
    const timer = setTimeout(() => controller.abort(), 20000);
    setConnection({ status: "checking", error: "" });
    try {
      const [outcomes, policy] = await Promise.all([
        Promise.allSettled(
          keys.map((key, index) =>
            key && (index === 0 || key !== keys[0])
              ? listModels(key, controller.signal)
              : Promise.resolve([]),
          ),
        ),
        accessPromise.current,
      ]);
      const listed = [
        ...new Map(
          outcomes
            .flatMap((outcome) =>
              outcome.status === "fulfilled" ? outcome.value : [],
            )
            .map((item) => [item.name, item]),
        ).values(),
      ];
      if (!listed.length)
        throw new Error(
          redactSecrets(
            outcomes
              .map((outcome, index) =>
                outcome.status === "rejected"
                  ? `API 키 ${index + 1}\n${outcome.reason.message}`
                  : "",
              )
              .filter(Boolean)
              .join("\n\n"),
            keys,
          ),
        );
      const available = affordableModels(listed, policy);
      if (!available.length)
        throw new Error(
          "무료 플랜 지원 또는 입력·출력 중 하나가 $1 미만인 사용 가능 모델이 없습니다.",
        );
      if (connecting.current !== controller) return;
      configuredKeys.current = keys;
      const rememberedIndex = options.activeKeyIndex || 0;
      const usable = (index) =>
        outcomes[index]?.status === "fulfilled" &&
        outcomes[index].value.length > 0;
      const index = usable(rememberedIndex)
        ? rememberedIndex
        : usable(0)
          ? 0
          : 1;
      activeIndex.current = index;
      activeKey.current = keys[index];
      setActiveKeyIndex(index);
      setModels(available);
      const remembered = options.rememberedModel || preferred.current;
      const chosen =
        available.find((item) => item.name === remembered)?.name ||
        available[0].name;
      setModel(chosen);
      preferred.current = chosen;
      setConnection({ status: "ready", error: "" });
      if (options.persist !== false) saveKeys(chosen);
      if (remembered && chosen !== remembered)
        setPersistence((current) => ({
          ...current,
          error:
            "저장한 모델을 현재 사용할 수 없어 가장 저렴한 사용 가능 모델을 선택했습니다.",
        }));
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
    configuredKeys.current = [];
    activeIndex.current = 0;
    setActiveKeyIndex(0);
    setKeyDraft("");
    setBackupKeyDraft("");
    setModel("");
    preferred.current = "";
    setModels([]);
    setConnection({ status: "idle", error: "" });
    store?.save(null);
  }
  function chooseModel(value) {
    setModel(value);
    preferred.current = value;
    if (activeKey.current) saveKeys(value);
  }
  async function requestWithKeys(params, onAttempt) {
    const keys = configuredKeys.current.slice();
    const response = await withKeyFallback({
      keys,
      activeIndex: activeIndex.current,
      signal: params.signal,
      onAttempt,
      run: (key, index, signal) =>
        askGemini({ ...params, apiKey: key, signal, redactionKeys: keys }),
    });
    if (providerLive.current && activeIndex.current !== response.index) {
      activeIndex.current = response.index;
      activeKey.current = keys[response.index];
      setActiveKeyIndex(response.index);
      saveKeys(params.model);
    }
    return response.result;
  }
  function updateTurn(pid, id, change) {
    const safe = { ...change };
    for (const field of ["question", "answer", "error", "retryError"])
      if (typeof safe[field] === "string")
        safe[field] = redactSecrets(safe[field], configuredKeys.current);
    historyStore.update(
      pid,
      (current) =>
        current.map((turn) => (turn.id === id ? { ...turn, ...safe } : turn)),
      !!safe.status,
    );
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
    if (!historyStore.ready(problem.id))
      return "AI 대화 저장·복원이 완료된 뒤 다시 보내 주세요.";
    let context;
    try {
      context = makeContext(problem, code, result, includeExecution);
    } catch (error) {
      return error.message;
    }
    if (!question.trim()) return "질문을 입력해 주세요.";
    if (question.length > 4000) return "질문은 4,000자 이내로 입력해 주세요.";
    const pid = problem.id,
      id =
        retryId ||
        globalThis.crypto?.randomUUID?.() ||
        `turn-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      controller = new AbortController();
    const history = (turns[pid] || []).filter(
      (turn) => turn.id !== retryId && turn.answer && !turn.error,
    );
    const turn = {
      id,
      question: redactSecrets(question.trim(), configuredKeys.current),
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
      historyStore.update(pid, (current) => [...current, turn], true);
      setDrafts((previous) => ({ ...previous, [pid]: "" }));
    }
    request.current = controller;
    setPending({ pid, id });
    try {
      const response = await requestWithKeys(
        {
          model,
          context,
          question,
          history,
          signal: controller.signal,
          onText: (text) => updateTurn(pid, id, { answer: text }),
        },
        ({ index, previousError }) => {
          updateTurn(pid, id, {
            answer: "",
            keyNumber: index + 1,
            retryError: previousError,
          });
          setPending({
            pid,
            id,
            keyNumber: index + 1,
            retrying: !!previousError,
          });
        },
      );
      updateTurn(pid, id, {
        answer: response.text,
        truncated: response.truncated,
        status: "complete",
      });
    } catch (error) {
      const message =
        error.name === "AbortError"
          ? "응답 생성을 중지했습니다."
          : error instanceof TypeError
            ? `${error.name}: ${error.message}`
            : error.message;
      updateTurn(pid, id, { error: message, status: "error" });
    } finally {
      if (request.current === controller) {
        request.current = null;
        setPending(null);
      }
    }
  }
  async function generateNote({ problem, code, result }) {
    if (request.current || connection.status !== "ready") return;
    if (!historyStore.ready(problem.id)) return;
    const pid = problem.id;
    const controller = new AbortController();
    const update = (change) =>
      setNoteGenerations((previous) => ({
        ...previous,
        [pid]: { ...previous[pid], ...change },
      }));
    request.current = controller;
    setPending({ pid, kind: "note" });
    update({ status: "pending", error: "" });
    try {
      const response = await requestWithKeys(
        {
          model,
          task: "notes",
          history: turns[pid] || [],
          signal: controller.signal,
        },
        ({ index, previousError }) => {
          update({ keyNumber: index + 1, retryError: previousError });
          setPending({
            pid,
            kind: "note",
            keyNumber: index + 1,
            retrying: !!previousError,
          });
        },
      );
      update({
        status: "complete",
        text: response.text,
        truncated: response.truncated,
        model: models.find((item) => item.name === model)?.label || model,
      });
    } catch (error) {
      update({
        status: "error",
        error:
          error.name === "AbortError"
            ? "노트 생성을 중지했습니다."
            : error instanceof TypeError
              ? `${error.name}: ${error.message}`
              : error.message,
      });
    } finally {
      if (request.current === controller) {
        request.current = null;
        setPending(null);
      }
    }
  }
  return (
    <TutorContext.Provider
      value={{
        access,
        keyDraft,
        backupKeyDraft,
        activeKeyIndex,
        updateKey,
        connection,
        models,
        model,
        setModel: chooseModel,
        connect: () => connect(),
        disconnect,
        settingsEnabled: !!store,
        persistence,
        retrySettings: () =>
          store?.hasIntent ? store.retry() : restoreSettings(),
        turns,
        historyStore,
        conversationStates,
        drafts,
        setDrafts,
        pending,
        send,
        generateNote,
        noteGenerations,
        clearNote: (pid) =>
          setNoteGenerations((previous) => ({ ...previous, [pid]: null })),
        cancel: () => request.current?.abort(),
        clear: (pid) => {
          historyStore.update(pid, () => [], true);
          if (!historyStore.ready(pid)) historyStore.retry(pid);
        },
      }}
    >
      {children}
    </TutorContext.Provider>
  );
}

export function GeminiNoteGenerator({
  problem,
  code,
  result,
  onAppend,
  onOpenAI,
}) {
  const tutor = useContext(TutorContext);
  const generation = tutor.noteGenerations[problem.id];
  const count = (tutor.turns[problem.id] || []).filter(
    (turn) => turn.answer && !turn.error,
  ).length;
  const ready = tutor.connection.status === "ready";
  const busy = !!tutor.pending;
  const generating =
    tutor.pending?.kind === "note" && tutor.pending.pid === problem.id;
  return (
    <section className="note-ai" aria-label="AI 복습 노트">
      <div className="note-ai-heading">
        <strong>
          <Sparkles size={14} /> AI 복습 노트
        </strong>
        <button
          className="note-ai-generate"
          disabled={
            !ready || !count || busy || !tutor.historyStore.ready(problem.id)
          }
          onClick={() => tutor.generateNote({ problem, code, result })}
        >
          {generating ? (
            <Loader2 size={13} className="spin" />
          ) : (
            <Sparkles size={13} />
          )}
          {generating ? "노트 생성 중…" : "AI 대화로 노트 생성"}
        </button>
      </div>
      <p>
        이 문제의 질문·답변 {count}개를 질문 한 줄·답변 한 문장과 핵심 코드
        1~3줄로 짧게 저장합니다.
      </p>
      {ready ? (
        <small>
          AI 질문과 동일한 모델:{" "}
          {tutor.models.find((item) => item.name === tutor.model)?.label} · 같은
          API 키의 할당량·요금 적용
        </small>
      ) : (
        <button className="note-ai-link" onClick={onOpenAI}>
          AI 질문에서 키와 모델 연결하기
        </button>
      )}
      {ready && !count && <p>먼저 AI 질문에서 이 문제에 대해 질문해 보세요.</p>}
      {busy && !generating && (
        <p role="status">다른 AI 요청이 끝난 뒤 생성할 수 있습니다.</p>
      )}
      {generating && (
        <button className="note-ai-link" onClick={tutor.cancel}>
          노트 생성 중지
        </button>
      )}
      {generation?.error && (
        <p className="gemini-form-error gemini-api-error" role="alert">
          {generation.error}
        </p>
      )}
      {generation?.retryError && generation.status !== "error" && (
        <details className="gemini-key-retry">
          <summary>
            {generation.keyNumber}번 API 키로 재시도
            {generating ? " 중…" : "했습니다."}
          </summary>
          <pre>{generation.retryError}</pre>
        </details>
      )}
      {generation?.text && (
        <div className="note-ai-preview">
          <strong>생성된 노트 미리보기 · {generation.model}</strong>
          <Answer text={generation.text} />
          {generation.truncated && (
            <p className="gemini-limit">
              길이 제한으로 일부 내용이 생략됐을 수 있습니다.
            </p>
          )}
          <div className="note-ai-actions">
            <button
              disabled={generating}
              onClick={() => {
                onAppend(generation.text);
                tutor.clearNote(problem.id);
              }}
            >
              내 노트에 추가
            </button>
            <button
              disabled={generating}
              onClick={() => tutor.clearNote(problem.id)}
            >
              미리보기 버리기
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export function GeminiTutor({
  problem,
  code,
  result,
  hidden,
  expanded = false,
  onExpandedChange,
}) {
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
  const conversation = tutor.conversationStates[problem.id] || {
    state: "loading",
  };
  const historyReady = tutor.historyStore.ready(problem.id);
  const checking =
      tutor.connection.status === "checking" ||
      tutor.persistence.state === "loading",
    busy = !!tutor.pending;
  useEffect(() => {
    tutor.historyStore.load(problem.id);
  }, [problem.id, tutor.historyStore]);
  useEffect(() => {
    if (!hidden && messages.current)
      messages.current.scrollTop = messages.current.scrollHeight;
  }, [currentTurns, hidden]);
  useEffect(() => {
    if (!expanded || hidden) return;
    const collapse = (event) => {
      if (
        event.key === "Escape" &&
        !event.isComposing &&
        !event.defaultPrevented
      ) {
        event.preventDefault();
        onExpandedChange?.(false);
      }
    };
    document.addEventListener("keydown", collapse);
    return () => document.removeEventListener("keydown", collapse);
  }, [expanded, hidden, onExpandedChange]);
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
          <small className={ready ? "gemini-selected-model" : ""}>
            {ready ? (
              <>
                <span>
                  {tutor.models.find((m) => m.name === tutor.model)?.label}
                </span>
                <span
                  className="gemini-inline-price"
                  title={modelPriceDetail(tutor.model)}
                >
                  {modelPriceLabel(tutor.model, true)}
                </span>
                <span
                  className={`gemini-free-tier ${freeTierLabel(tutor.model, tutor.access) === "무료 플랜 지원" ? "supported" : ""}`}
                >
                  {freeTierLabel(tutor.model, tutor.access)}
                </span>
              </>
            ) : (
              "내 문제와 코드를 함께 보는 AI"
            )}
          </small>
        </div>
        <span className={`gemini-status ${ready ? "ready" : ""}`}>
          {ready ? "연결됨" : "키 연결 필요"}
        </span>
        <button
          className="gemini-expand-toggle"
          aria-label={expanded ? "AI 대화 축소" : "AI 대화 확대"}
          title={expanded ? "대화 축소 (Esc)" : "문제 패널 전체로 대화 확대"}
          aria-expanded={expanded}
          aria-controls={`gemini-messages-${problem.id}`}
          onClick={() => onExpandedChange?.(!expanded)}
        >
          {expanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
        </button>
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
            내 Gemini API 키 1{" "}
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
          <label htmlFor="gemini-backup-key">Gemini API 키 2 (선택)</label>
          <div className="gemini-key-row">
            <KeyRound size={14} />
            <input
              id="gemini-backup-key"
              type="password"
              autoComplete="off"
              spellCheck={false}
              placeholder="실패 시 재시도할 보조 API 키"
              value={tutor.backupKeyDraft}
              disabled={checking || busy}
              onChange={(event) => tutor.updateKey(event.target.value, 1)}
            />
          </div>
          <small>
            키를 입력·수정한 뒤 키 연결을 누르세요. 요청 실패 시 다른 키로 한 번
            재시도합니다. 같은 프로젝트의 키는 할당량을 공유할 수 있습니다.
          </small>
          {ready && (
            <p className="gemini-active-key">
              현재 {tutor.activeKeyIndex + 1}번 API 키 사용 · 성공한 키로 다음
              요청을 시작합니다.
            </p>
          )}
          {ready && (
            <>
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
                      {model.label} · {modelPriceLabel(model.name)} ·{" "}
                      {freeTierLabel(model.name, tutor.access)}
                    </option>
                  ))}
                </select>
                <button onClick={tutor.disconnect} disabled={busy}>
                  {tutor.settingsEnabled ? "저장된 키·모델 삭제" : "연결 해제"}
                </button>
              </div>
              <div className="gemini-price-info">
                <p>
                  무료 플랜 지원 또는 입력·출력 중 하나라도 $1 미만 · 입력 단가
                  오름차순, 동률이면 출력 단가순
                </p>
                <p>
                  {freeTierLabel(tutor.model, tutor.access)} · 공개 모델 정책
                  기준이며, 키별 지역·할당량·잔여 무료 한도는 별도입니다.
                </p>
                <a
                  href={tutor.access?.source || pricingSource.officialUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  무료 플랜 공식 안내
                </a>
                <p>{modelPriceDetail(tutor.model)}</p>
                <small>
                  무료 한도·캐시·배치 요금은 별도이며, latest 별칭의 가격은
                  변경될 수 있습니다.
                </small>
                <span>
                  조회 {pricingSource.retrievedAt} ·{" "}
                  <a
                    href={pricingSource.sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {pricingSource.sourceName}
                  </a>{" "}
                  ·{" "}
                  <a
                    href={pricingSource.officialUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Google 공식 요금
                    <ExternalLink size={10} />
                  </a>
                </span>
              </div>
            </>
          )}
          <p>
            <ShieldCheck size={12} />
            {tutor.settingsEnabled
              ? "키·모델과 문제별 AI 대화를 계정에 암호화해 저장하고 자동 복원합니다."
              : "키·AI 대화는 이 탭에서만 유지하며 새로고침하면 지워집니다."}
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
      {tutor.settingsEnabled && (
        <div className="gemini-persistence" role="status">
          <span>
            {
              {
                loading: "저장된 Gemini 설정 확인 중…",
                saving: "키·모델 암호화 저장 중…",
                saved: "키·모델이 계정에 저장됨",
                empty: "키를 연결하면 선택 모델과 함께 자동 저장됩니다.",
                error: "Gemini 설정 저장·복원 확인 필요",
              }[tutor.persistence.state]
            }
          </span>
          {tutor.persistence.error && (
            <span className="gemini-form-error">{tutor.persistence.error}</span>
          )}
          {tutor.persistence.state === "error" && (
            <button onClick={tutor.retrySettings} disabled={busy || checking}>
              설정 저장·복원 재시도
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
        id={`gemini-messages-${problem.id}`}
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
                    {tutor.pending?.id === turn.id && tutor.pending.retrying
                      ? `${tutor.pending.keyNumber}번 키로 재시도 중…`
                      : "답변 작성 중…"}
                  </span>
                )}
              </span>
              {turn.answer && <Answer text={turn.answer} />}
              {turn.retryError && turn.status === "complete" && (
                <details className="gemini-key-retry">
                  <summary>{turn.keyNumber}번 API 키로 재시도했습니다.</summary>
                  <pre>{turn.retryError}</pre>
                </details>
              )}
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
        {tutor.settingsEnabled && (
          <div
            className={`gemini-history-status ${conversation.state}`}
            role="status"
          >
            <span>
              {
                {
                  loading: "AI 대화 불러오는 중…",
                  saving: "AI 대화 저장 중…",
                  saved: "AI 대화 저장됨",
                  error: "AI 대화 저장·복원 실패",
                  conflict: "다른 기기와 AI 대화 충돌",
                }[conversation.state]
              }
            </span>
            {conversation.error && (
              <span className="gemini-form-error">{conversation.error}</span>
            )}
            {["error", "conflict"].includes(conversation.state) && (
              <>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => tutor.historyStore.retry(problem.id)}
                >
                  {conversation.state === "conflict"
                    ? "현재 변경 다시 저장"
                    : "대화 저장·복원 재시도"}
                </button>
                {conversation.state === "conflict" && (
                  <small>
                    다른 기기의 새 대화와 현재 변경을 합칩니다. 대화 지우기를
                    눌렀다면 삭제를 다시 적용합니다.
                  </small>
                )}
                {!!currentTurns.length && (
                  <button
                    type="button"
                    onClick={() => {
                      const url = URL.createObjectURL(
                        new Blob(
                          [
                            JSON.stringify(
                              { problem: problem.id, turns: currentTurns },
                              null,
                              2,
                            ),
                          ],
                          { type: "application/json" },
                        ),
                      );
                      const link = document.createElement("a");
                      link.href = url;
                      link.download = `${problem.id}-ai-history.json`;
                      link.click();
                      setTimeout(() => URL.revokeObjectURL(url), 1000);
                    }}
                  >
                    현재 대화 내려받기
                  </button>
                )}
              </>
            )}
          </div>
        )}
        {busy && tutor.pending.kind === "note" && (
          <p className="gemini-other-pending" role="status">
            복습 노트를 생성 중입니다. 완료 후 질문하거나 생성을 중지해 주세요.
          </p>
        )}
        {busy &&
          tutor.pending.kind !== "note" &&
          tutor.pending.pid !== problem.id && (
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
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing &&
                event.nativeEvent.keyCode !== 229
              ) {
                event.preventDefault();
                if (ready && historyReady && !busy) submit();
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
              disabled={!ready || !historyReady || !draft.trim()}
            >
              <Send size={15} />
            </button>
          )}
        </div>
        <div className="gemini-composer-note">
          <span>질문·첨부 내용은 Google Gemini로 전송됩니다.</span>
          <span>Enter 전송 · Shift+Enter 줄바꿈</span>
        </div>
      </form>
    </section>
  );
}
