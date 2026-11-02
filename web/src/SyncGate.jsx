import React, { useCallback, useEffect, useRef, useState } from "react";
import { LockKeyhole, Loader2, Cloud, LogOut } from "lucide-react";
import {
  SYNC_URL,
  syncRequest,
  normalizeState,
  sameState,
  hasRecords,
  downloadState,
} from "./sync.js";
import "./sync.css";

export function SyncStatus({ controls }) {
  if (!controls) return null;
  const labels = {
    saved: "서버 저장됨",
    pending: "저장 대기 중",
    saving: "서버 저장 중…",
    error: "동기화 실패",
    conflict: "다른 기기와 기록 충돌",
  };
  return (
    <div className="sync-controls">
      <span role="status" className={`sync-status ${controls.status}`}>
        <Cloud size={13} />
        {labels[controls.status]}
      </span>
      {controls.status === "error" && (
        <button onClick={controls.retry}>다시 저장</button>
      )}
      <button onClick={controls.backup} title="현재 기록 내려받기">
        기록 백업
      </button>
      <button
        onClick={controls.logout}
        disabled={controls.status === "saving"}
        aria-label="로그아웃"
      >
        <LogOut size={14} />
      </button>
      {controls.error && (
        <span className="sync-error" role="alert">
          {controls.error}
        </span>
      )}
    </div>
  );
}

export default function SyncGate({
  initialState,
  children,
  apiUrl = SYNC_URL,
}) {
  const [mode, setMode] = useState(apiUrl ? "checking" : "local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("saved");
  const [restored, setRestored] = useState(null);
  const [choice, setChoice] = useState(null);
  const snapshot = useRef(normalizeState(initialState));
  const baseline = useRef(null),
    revision = useRef(0),
    saving = useRef(false),
    blocked = useRef(false),
    timer = useRef(null);
  const mounted = useRef(true),
    active = useRef(false),
    flushRef = useRef(null);
  const api = useCallback(
    (path, method, data) => syncRequest(apiUrl, path, method, data),
    [apiUrl],
  );

  function activate(state, remote) {
    revision.current = remote.revision;
    baseline.current = remote.state ? normalizeState(remote.state) : null;
    snapshot.current = normalizeState(state);
    blocked.current = false;
    active.current = true;
    setRestored(snapshot.current);
    setError("");
    setChoice(null);
    setMode("active");
    setStatus(
      sameState(snapshot.current, baseline.current) ? "saved" : "pending",
    );
    clearTimeout(timer.current);
    timer.current = setTimeout(() => flushRef.current(), 800);
  }
  async function load() {
    const remote = await api("/state");
    if (!mounted.current) return;
    revision.current = remote.revision;
    if (
      remote.state &&
      (!hasRecords(snapshot.current) ||
        sameState(snapshot.current, remote.state))
    )
      activate(remote.state, remote);
    else if (!remote.state && !hasRecords(snapshot.current))
      activate(snapshot.current, remote);
    else {
      setChoice(remote);
      setMode("choose");
    }
  }
  useEffect(() => {
    mounted.current = true;
    if (!apiUrl) return;
    api("/session")
      .then(load)
      .catch((err) => {
        if (!mounted.current) return;
        setMode("login");
        if (err.status !== 401) setError(err.message);
      });
    return () => {
      mounted.current = false;
      active.current = false;
      clearTimeout(timer.current);
    };
  }, [api]);

  async function flush() {
    if (!active.current || saving.current || blocked.current) return false;
    if (baseline.current && sameState(snapshot.current, baseline.current))
      return true;
    saving.current = true;
    setStatus("saving");
    const sent = snapshot.current;
    try {
      const response = await api("/state", "PUT", {
        revision: revision.current,
        state: sent,
      });
      revision.current = response.revision;
      baseline.current = sent;
      if (!mounted.current) return false;
      setStatus(sameState(snapshot.current, sent) ? "saved" : "pending");
      setError("");
      return true;
    } catch (err) {
      if (!mounted.current) return false;
      blocked.current = true;
      setError(err.message);
      if (err.status === 401) {
        active.current = false;
        setMode("login");
      } else if (err.status === 409) setStatus("conflict");
      else setStatus("error");
      return false;
    } finally {
      saving.current = false;
      if (
        mounted.current &&
        active.current &&
        !blocked.current &&
        !sameState(snapshot.current, baseline.current)
      ) {
        clearTimeout(timer.current);
        timer.current = setTimeout(() => flushRef.current(), 800);
      }
    }
  }
  flushRef.current = flush;
  const changed = useCallback((state) => {
    snapshot.current = normalizeState(state);
    if (!active.current || blocked.current) return;
    if (!saving.current)
      setStatus(
        sameState(snapshot.current, baseline.current) ? "saved" : "pending",
      );
    clearTimeout(timer.current);
    timer.current = setTimeout(() => flushRef.current(), 800);
  }, []);
  useEffect(() => {
    if (mode !== "active") return;
    const warn = (event) => {
      if (!sameState(snapshot.current, baseline.current)) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    const visible = () => {
      if (document.visibilityState === "hidden") flushRef.current();
    };
    window.addEventListener("beforeunload", warn);
    document.addEventListener("visibilitychange", visible);
    return () => {
      window.removeEventListener("beforeunload", warn);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [mode]);

  async function login(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/login", "POST", { password });
      setPassword("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    if (saving.current) return;
    if (
      !(await flushRef.current()) ||
      !sameState(snapshot.current, baseline.current)
    )
      return;
    try {
      await api("/logout", "POST");
      active.current = false;
      clearTimeout(timer.current);
      setPassword("");
      setError("");
      setMode("login");
    } catch (err) {
      setError(err.message);
    }
  }
  async function resolveConflict(useLocal) {
    setBusy(true);
    setError("");
    try {
      const remote = await api("/state");
      // Recheck the revision on every explicit resolution; saving still uses CAS.
      if (useLocal) {
        revision.current = remote.revision;
        baseline.current = remote.state;
        blocked.current = false;
        await flushRef.current();
      } else {
        active.current = false;
        setChoice(remote);
        setMode("choose");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  if (mode === "local") return children(initialState, null, null);
  if (mode === "active")
    return (
      <>
        {children(restored, changed, {
          settingsApi: api,
          status,
          error,
          retry: () => {
            blocked.current = false;
            flushRef.current();
          },
          backup: () => downloadState(snapshot.current),
          logout,
        })}
        {status === "conflict" && (
          <div
            className="sync-overlay"
            role="dialog"
            aria-modal="true"
            aria-label="기록 충돌 해결"
          >
            <div className="sync-card">
              <h2>다른 기기에서 기록이 바뀌었습니다</h2>
              <p>
                현재 기록은 이 브라우저에 남아 있습니다. 덮어쓰기 전에 백업할 수
                있습니다.
              </p>
              <button onClick={() => downloadState(snapshot.current)}>
                현재 기록 백업
              </button>
              <button disabled={busy} onClick={() => resolveConflict(false)}>
                서버 기록 확인하기
              </button>
              <button
                disabled={busy}
                onClick={() => {
                  if (confirm("현재 브라우저 기록으로 서버 기록을 덮어쓸까요?"))
                    resolveConflict(true);
                }}
              >
                내 기록으로 서버 덮어쓰기
              </button>
              {error && <p role="alert">{error}</p>}
            </div>
          </div>
        )}
      </>
    );
  return (
    <main className="sync-screen">
      <div className="sync-card">
        <div className="sync-icon">
          <LockKeyhole size={25} />
        </div>
        <h1>나의 빅분기 연습실</h1>
        {mode === "checking" ? (
          <p>
            <Loader2 className="spin" size={16} /> 저장된 기록을 확인하고
            있어요…
          </p>
        ) : mode === "choose" ? (
          <>
            <h2>
              {choice.state
                ? "이어갈 기록을 선택하세요"
                : "기존 기록을 가져올까요?"}
            </h2>
            <p>
              {choice.state
                ? "이 브라우저와 서버 기록이 다릅니다. 선택하지 않은 기록은 백업으로 보관할 수 있습니다."
                : "이 브라우저에서 작성한 코드·노트·진행도를 서버로 옮길 수 있습니다."}
            </p>
            <button onClick={() => downloadState(snapshot.current)}>
              브라우저 기록 백업
            </button>
            {choice.state && (
              <button onClick={() => downloadState(choice.state)}>
                서버 기록 백업
              </button>
            )}
            <button
              className="primary"
              onClick={() => activate(choice.state || {}, choice)}
            >
              {choice.state ? "서버 기록으로 이어하기" : "빈 기록으로 시작하기"}
            </button>
            <button
              onClick={() => {
                if (
                  choice.state &&
                  !confirm("이 브라우저 기록으로 기존 서버 기록을 덮어쓸까요?")
                )
                  return;
                activate(snapshot.current, choice);
              }}
            >
              이 브라우저 기록 가져오기
            </button>
          </>
        ) : (
          <>
            <p>
              비밀번호로 로그인하면 코드·답안·노트·진행도를
              <br />
              다른 기기에서도 이어서 풀 수 있어요.
            </p>
            <form onSubmit={login}>
              <label htmlFor="practice-password">비밀번호</label>
              <input
                id="practice-password"
                type="password"
                autoComplete="current-password"
                required
                maxLength={128}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={busy}
                autoFocus
              />
              <button className="primary" disabled={busy || !password}>
                {busy ? "기록 불러오는 중…" : "로그인"}
              </button>
            </form>
            <small>서버 저장 전 변경 내용은 이 브라우저에도 보관됩니다.</small>
          </>
        )}
        {error && (
          <p className="sync-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </main>
  );
}
