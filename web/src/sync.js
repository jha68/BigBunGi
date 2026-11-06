export const SYNC_URL = (import.meta.env?.VITE_SYNC_API_URL || "").replace(
  /\/$/,
  "",
);

export class SyncError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}
export async function syncRequest(
  base,
  path,
  method = "GET",
  data,
  fetcher = fetch,
) {
  let response;
  try {
    response = await fetcher(base + path, {
      method,
      credentials: "include",
      cache: "no-store",
      headers: data === undefined ? {} : { "Content-Type": "application/json" },
      body: data === undefined ? undefined : JSON.stringify(data),
      signal: AbortSignal.timeout(20000),
    });
  } catch {
    throw new SyncError(
      "동기화 서버에 연결하지 못했습니다. 이 브라우저의 기록은 유지됩니다.",
      0,
    );
  }
  let body;
  try {
    body = await response.json();
  } catch {
    throw new SyncError(
      "서버 응답을 확인하지 못했습니다. 다시 시도해 주세요.",
      response.status,
    );
  }
  if (!response.ok)
    throw new SyncError(
      body.error || "기록을 동기화하지 못했습니다.",
      response.status,
    );
  return body;
}
export function normalizeState(value = {}) {
  value ||= {};
  return {
    drafts: value.drafts || {},
    answers: value.answers || {},
    notes: value.notes || {},
    highlights: value.highlights || {},
    progress: value.progress || {},
    selected: value.selected || "t1-01",
  };
}
export function sameState(a, b) {
  const stable = (value) =>
    value && typeof value === "object"
      ? Array.isArray(value)
        ? value.map(stable)
        : Object.fromEntries(
            Object.keys(value)
              .sort()
              .map((key) => [key, stable(value[key])]),
          )
      : value;
  return (
    JSON.stringify(stable(normalizeState(a))) ===
    JSON.stringify(stable(normalizeState(b)))
  );
}
export function hasRecords(value) {
  return ["drafts", "answers", "notes", "highlights", "progress"].some(
    (key) => Object.keys(value?.[key] || {}).length > 0,
  );
}
export function downloadState(value) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(normalizeState(value), null, 2)], {
      type: "application/json",
    }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = "bigbungi-records-backup.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
