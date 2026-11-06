import { activeHighlights } from "./note-highlights.js";

export const HOME_PROBLEM = {
  id: "home",
  title: "전체 학습 AI",
  files: [],
  steps: [],
  fields: [],
};
export const STUDY_PROMPTS = [
  "내가 어려워했던 문제 중 문제별 AI 질문 기록이 있는 문제만 찾아줘.",
  "노트에 기록했던 내용들을 종합하고 짧게 요약해줘.",
  "highlighted 된 노트 내용만 추려줘.",
];

export function makeStudyContext(
  data,
  records,
  snapshots,
  question,
  loadError = "",
) {
  const highlightOnly =
    /highlight|형광|강조|하이라이트/i.test(question) &&
    /만|only|추려|모아/i.test(question);
  const index = new Map(
    (records?.records || []).map((record) => [record.id, record]),
  );
  const unavailable = records?.unavailable || [];
  let budget = 120000;
  const truncated = [];
  const take = (text, pid) => {
    text ||= "";
    const result = text.slice(0, Math.max(0, budget));
    budget -= result.length;
    if (result.length < text.length && !truncated.includes(pid))
      truncated.push(pid);
    return result;
  };
  const problems = data.catalog.map((problem) => {
    const pid = problem.id,
      remote = index.get(pid),
      local = snapshots[pid];
    let ids = new Set(remote?.turnIds || []),
      recent = remote?.questions || [];
    if (
      (!data.serverEnabled ||
        ((loadError || unavailable.includes(pid)) && !remote)) &&
      local
    ) {
      ids = new Set(local.turns.map((turn) => turn.id));
      recent = local.turns;
    } else if (local?.unsaved) {
      if (local.clearing) {
        ids = new Set();
        recent = [];
      }
      const merged = new Map(recent.map((turn) => [turn.id, turn]));
      for (const turn of local.dirtyTurns) {
        ids.add(turn.id);
        merged.set(turn.id, turn);
      }
      recent = [...merged.values()];
    }
    const note = data.notes[pid] || "";
    const highlights = activeHighlights(note, data.highlights?.[pid]).map(
      (item) => take(item.text, pid),
    );
    return {
      id: pid,
      title: problem.title,
      type: problem.type,
      tags: problem.tags,
      passed: !!data.progress[pid]?.passed,
      attempts: data.progress[pid]?.attempts || 0,
      aiQuestionCount:
        (loadError || unavailable.includes(pid)) && !local ? null : ids.size,
      pendingLocalChanges: !!local?.unsaved,
      highlightedNotes: highlights,
      ...(highlightOnly
        ? {}
        : {
            note: take(note, pid),
            recentQuestions: recent.slice(-5).map((turn) => ({
              question: take(turn.question?.slice(0, 1000), pid),
              answer: take(turn.answer?.slice(0, 1500), pid),
              status: turn.status,
            })),
          }),
    };
  });
  return {
    scope: "study",
    highlightOnly,
    problems,
    coverage: {
      totalProblems: data.catalog.length,
      truncated,
      unavailable,
      loadError,
      notesLoadError: data.notesLoadError || "",
      noteSource: data.noteSource || "current-browser",
      recentQuestionsPerProblem: 5,
    },
    capturedAt: new Date().toISOString(),
  };
}
