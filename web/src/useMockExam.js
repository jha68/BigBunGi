import { useCallback, useEffect, useRef, useState } from "react";
import { MOCK_STORAGE, mergeMockRecords, readMockExam } from "./mock-records.js";

export default function useMockExam(initialRecords) {
  const [saved, setSaved] = useState(() => {
    const local = readMockExam();
    return { active: local.active, ...mergeMockRecords(initialRecords, local) };
  });
  const [saveError, setSaveError] = useState(false);
  const restored = useRef(initialRecords);
  const current = useRef(saved);
  const storageFailed = useRef(false);
  const persist = useCallback((next) => {
    try {
      localStorage.setItem(MOCK_STORAGE, JSON.stringify(next));
      storageFailed.current = false;
    } catch {
      storageFailed.current = true;
    }
    setSaveError(storageFailed.current);
    current.current = next;
    setSaved(next);
  }, []);

  const changeSaved = useCallback((change) => {
    const previous = storageFailed.current ? current.current : readMockExam();
    const next = change(previous);
    if (next === previous) return false;
    persist(next);
    return true;
  }, [persist]);

  const finish = useCallback((id) => {
    changeSaved((previous) => {
      const attempt = previous.active;
      if (!attempt || attempt.id !== id) return previous;
      return {
        ...previous,
        active: null,
        completed: {
          ...previous.completed,
          [attempt.round]: { ...attempt, submittedAt: Math.min(Date.now(), attempt.deadline) },
        },
      };
    });
  }, [changeSaved]);

  const activeId = saved.active?.id;
  const deadline = saved.active?.deadline;
  useEffect(() => {
    if (!activeId) return;
    function expire() {
      if (Date.now() >= deadline) finish(activeId);
    }
    const timeout = setTimeout(expire, Math.max(0, deadline - Date.now()));
    document.addEventListener("visibilitychange", expire);
    return () => {
      clearTimeout(timeout);
      document.removeEventListener("visibilitychange", expire);
    };
  }, [activeId, deadline, finish]);

  useEffect(() => {
    persist(current.current);
    function refresh(event) {
      if (event.key !== MOCK_STORAGE || storageFailed.current) return;
      current.current = readMockExam();
      setSaved(current.current);
    }
    window.addEventListener("storage", refresh);
    return () => window.removeEventListener("storage", refresh);
  }, [persist]);

  useEffect(() => {
    if (initialRecords === restored.current) return;
    restored.current = initialRecords;
    persist({ ...current.current, ...mergeMockRecords(initialRecords, current.current) });
  }, [initialRecords, persist]);

  return { saved, saveError, changeSaved, finish };
}
