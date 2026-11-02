// Secrets remain in memory here; the authenticated server encrypts them at rest.
export function createSettingsStore(api, notify) {
  let revision = null,
    queued,
    lastTarget,
    running = null,
    stopped = false;
  const emit = (state, error = "") => {
    if (!stopped) notify({ state, error });
  };
  async function load() {
    emit("loading");
    try {
      const result = await api("/settings");
      revision = result.revision;
      emit(
        result.unreadable ? "error" : result.settings ? "saved" : "empty",
        result.unreadable
          ? "로그인 비밀번호 변경 등으로 저장된 키를 복원하지 못했습니다. 키를 다시 연결해 주세요."
          : "",
      );
      return result;
    } catch (error) {
      emit("error", error.message);
      throw error;
    }
  }
  async function flush() {
    while (queued !== undefined && !stopped) {
      const target = queued;
      queued = undefined;
      emit("saving");
      try {
        if (revision === null) revision = (await api("/settings")).revision;
        const result = await api("/settings", "PUT", {
          revision,
          settings: target,
        });
        revision = result.revision;
        emit(
          queued !== undefined ? "saving" : target === null ? "empty" : "saved",
        );
      } catch (error) {
        if (error.status === 409) revision = null;
        queued = undefined;
        emit(
          "error",
          error.status === 409
            ? "다른 기기에서 Gemini 설정이 바뀌었습니다. 다시 저장하면 현재 설정으로 변경합니다."
            : error.message,
        );
        return false;
      }
    }
    return true;
  }
  function save(target) {
    if (stopped) return Promise.resolve(false);
    lastTarget = target;
    queued = target;
    if (!running)
      running = flush().finally(() => {
        running = null;
      });
    return running;
  }
  return {
    load,
    save,
    retry: () => save(lastTarget),
    get hasIntent() {
      return lastTarget !== undefined;
    },
    start: () => {
      stopped = false;
    },
    stop: () => {
      stopped = true;
      queued = undefined;
      lastTarget = undefined;
    },
  };
}
