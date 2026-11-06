// Per-problem snapshots with optimistic revisions. Only unsaved turn edits are
// merged on explicit retry, so a stale tab never resurrects a cleared transcript.
export function createConversationStore(api, notify, delay = 2000) {
  const records = new Map();
  let stopped = false;
  const entry = (pid) => {
    if (!records.has(pid))
      records.set(pid, {
        turns: [],
        revision: null,
        loaded: false,
        state: "loading",
        error: "",
        dirty: new Map(),
        clearing: null,
        timer: null,
        running: null,
        loading: null,
        urgent: false,
      });
    return records.get(pid);
  };
  const emit = (pid, e, state = e.state, error = "") => {
    e.state = state;
    e.error = error;
    if (!stopped) notify(pid, { turns: e.turns, state, error });
  };
  const dirty = (e) => !!e.clearing || e.dirty.size > 0;
  const restored = (turns) =>
    turns.map((turn) =>
      turn.status === "pending"
        ? {
            ...turn,
            status: "error",
            error:
              "이전 접속에서 응답이 중단됐습니다. 다시 시도할 수 있습니다.",
          }
        : turn,
    );
  const path = (pid) => `/conversations/${pid}`;
  async function load(pid) {
    const e = entry(pid);
    if (e.loaded) return true;
    if (e.loading) return e.loading;
    emit(pid, e, "loading");
    e.loading = (async () => {
      try {
        const result = api ? await api(path(pid)) : { turns: [], revision: 0 };
        if (stopped) return false;
        e.turns = restored(result.turns);
        e.revision = result.revision;
        e.loaded = true;
        emit(pid, e, api ? "saved" : "session");
        return true;
      } catch (error) {
        emit(pid, e, "error", error.message);
        return false;
      } finally {
        e.loading = null;
      }
    })();
    return e.loading;
  }
  function schedule(pid, e, wait = delay) {
    if (e.timer === null && !stopped)
      e.timer = setTimeout(() => {
        e.timer = null;
        flush(pid);
      }, wait);
  }
  function flush(pid) {
    const e = entry(pid);
    if (stopped || !api || !e.loaded || ["error", "conflict"].includes(e.state))
      return Promise.resolve(false);
    if (e.running) return e.running;
    if (!dirty(e)) return Promise.resolve(true);
    clearTimeout(e.timer);
    e.timer = null;
    const edits = new Map(e.dirty),
      clearing = e.clearing,
      target = e.turns;
    e.urgent = false;
    emit(pid, e, "saving");
    e.running = (async () => {
      try {
        const result = await api(path(pid), "PUT", {
          revision: e.revision,
          turns: target,
        });
        if (stopped) return false;
        e.revision = result.revision;
        for (const [id, value] of edits)
          if (e.dirty.get(id) === value) e.dirty.delete(id);
        if (e.clearing === clearing) e.clearing = null;
        emit(pid, e, dirty(e) ? "saving" : "saved");
        return true;
      } catch (error) {
        emit(
          pid,
          e,
          error.status === 409 ? "conflict" : "error",
          error.message,
        );
        return false;
      } finally {
        e.running = null;
        if (dirty(e) && e.state === "saving")
          schedule(pid, e, e.urgent ? 0 : delay);
      }
    })();
    return e.running;
  }
  function update(pid, change, immediate = false) {
    const e = entry(pid);
    if (stopped || !e.loaded) return false;
    const next = change(e.turns),
      previous = new Map(e.turns.map((turn) => [turn.id, turn]));
    if (!next.length) {
      e.clearing = {};
      e.dirty.clear();
    }
    for (const turn of next)
      if (previous.get(turn.id) !== turn) e.dirty.set(turn.id, turn);
    e.turns = next;
    if (!api) {
      e.dirty.clear();
      e.clearing = null;
      emit(pid, e, "session");
      return true;
    }
    if (["error", "conflict"].includes(e.state)) {
      emit(pid, e, e.state, e.error);
      return true;
    }
    emit(pid, e, "saving");
    if (immediate) {
      e.urgent = true;
      flush(pid);
    } else schedule(pid, e);
    return true;
  }
  async function retry(pid) {
    const e = entry(pid);
    if (!e.loaded) return load(pid);
    if (e.running) await e.running;
    try {
      const remote = await api(path(pid));
      if (stopped) return false;
      const merged = new Map(
        (e.clearing ? [] : restored(remote.turns)).map((turn) => [
          turn.id,
          turn,
        ]),
      );
      for (const [id, turn] of e.dirty) merged.set(id, turn);
      e.turns = [...merged.values()];
      e.revision = remote.revision;
      emit(pid, e, dirty(e) ? "saving" : "saved");
      return dirty(e) ? flush(pid) : true;
    } catch (error) {
      emit(pid, e, "error", error.message);
      return false;
    }
  }
  return {
    load,
    update,
    retry,
    snapshots: () =>
      Object.fromEntries(
        [...records].map(([pid, e]) => [
          pid,
          {
            turns: e.turns,
            unsaved: dirty(e),
            clearing: !!e.clearing,
            dirtyTurns: [...e.dirty.values()],
          },
        ]),
      ),
    flushAll: async () => {
      for (const [pid, e] of records) {
        if (e.running) await e.running;
        while (dirty(e)) {
          if (!(await flush(pid))) return false;
        }
      }
      return true;
    },
    ready: (pid) =>
      entry(pid).loaded && !["error", "conflict"].includes(entry(pid).state),
    hasUnsaved: () => !!api && [...records.values()].some(dirty),
    start: () => {
      stopped = false;
    },
    stop: () => {
      stopped = true;
      for (const e of records.values()) clearTimeout(e.timer);
    },
  };
}
