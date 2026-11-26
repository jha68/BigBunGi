export const MOCK_STORAGE = "bigbungi.mock-exam.v1";

function record(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

export function mockRecords(value) {
  return {
    completed: record(value?.completed),
    retryMarks: record(value?.retryMarks),
    retryMarkTimes: record(value?.retryMarkTimes),
  };
}

export function readMockExam() {
  try {
    const value = JSON.parse(localStorage.getItem(MOCK_STORAGE));
    return { active: value?.active || null, ...mockRecords(value) };
  } catch {
    return { active: null, ...mockRecords() };
  }
}

export function mergeMockRecords(server, browser) {
  const remote = mockRecords(server);
  const local = mockRecords(browser);
  const completed = { ...remote.completed };
  for (const [round, attempt] of Object.entries(local.completed)) {
    const other = completed[round];
    if (!other || isNewerAttempt(attempt, other))
      completed[round] = attempt;
  }
  const retryMarks = { ...remote.retryMarks };
  const retryMarkTimes = { ...remote.retryMarkTimes };
  for (const [round, ids] of Object.entries(local.retryMarks)) {
    const localTime = local.retryMarkTimes[round] ?? 0;
    const remoteTime = retryMarkTimes[round] ?? 0;
    if (localTime > remoteTime) {
      retryMarks[round] = ids;
      retryMarkTimes[round] = localTime;
    } else if (!localTime && !remoteTime) {
      retryMarks[round] = [...new Set([...(retryMarks[round] || []), ...ids])];
    }
  }
  return { completed, retryMarks, retryMarkTimes };
}

function isNewerAttempt(attempt, other) {
  if (attempt.id === other.id) return (attempt.updatedAt ?? 0) > (other.updatedAt ?? 0);
  return attempt.submittedAt > other.submittedAt || (
    attempt.submittedAt === other.submittedAt && attempt.startedAt > other.startedAt
  );
}
