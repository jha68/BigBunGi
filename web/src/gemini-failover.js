import { GeminiError, redactSecrets } from "./gemini.js";

const message = (error) =>
  ["TypeError", "TimeoutError"].includes(error.name)
    ? `${error.name}: ${error.message}`
    : error.message || String(error);

// Try each distinct configured key once. The same request/context/model is used;
// only the authentication header changes. Cancelling stops the whole request.
export async function withKeyFallback({
  keys,
  activeIndex = 0,
  signal,
  onAttempt,
  run,
  timeout = 90000,
}) {
  const order = [activeIndex, 0, 1].filter(
    (index, position, all) =>
      keys[index] &&
      all.indexOf(index) === position &&
      !all.slice(0, position).some((other) => keys[other] === keys[index]),
  );
  const failures = [];
  for (const index of order) {
    signal?.throwIfAborted();
    const previousError = failures
      .map(({ index, error }) => `API 키 ${index + 1}\n${error}`)
      .join("\n\n");
    onAttempt?.({ index, previousError });
    const attemptSignal =
      timeout > 0
        ? AbortSignal.any(
            [signal, AbortSignal.timeout(timeout)].filter(Boolean),
          )
        : signal;
    try {
      const result = await run(keys[index], index, attemptSignal);
      signal?.throwIfAborted();
      return { result, index, previousError };
    } catch (error) {
      if (signal?.aborted) throw error;
      failures.push({
        index,
        error: redactSecrets(message(error), keys),
        status: error.status || 0,
      });
    }
  }
  throw new GeminiError(
    failures.length === 1
      ? failures[0].error
      : failures
          .map(({ index, error }) => `API 키 ${index + 1}\n${error}`)
          .join("\n\n") || "API 키를 먼저 연결해 주세요.",
    failures.at(-1)?.status || 0,
  );
}
