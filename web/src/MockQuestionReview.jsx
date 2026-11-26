import { useRef, useState } from "react";
import { BookOpen, FileCode2, Sparkles } from "lucide-react";
import { GeminiTutor } from "./GeminiTutor.jsx";
import MockQuestionSolution from "./MockQuestionSolution.jsx";
import PracticeNotes from "./PracticeNotes.jsx";

const TABS = [
  { id: "solution", label: "풀이", icon: BookOpen },
  { id: "ai", label: "AI 질문", icon: Sparkles },
  { id: "note", label: "노트", icon: FileCode2 },
];

export default function MockQuestionReview({
  problem, round, questionNumber, grade, submittedCode, gradingSpec, noteRecords,
  retry, updateRetry, runner, runId,
}) {
  const [tab, setTab] = useState("solution");
  const [expanded, setExpanded] = useState(false);
  const [retrying, setRetrying] = useState(Boolean(retry));
  const tabList = useRef(null);
  const { id } = problem;
  const code = submittedCode || "";
  const aiExpanded = tab === "ai" && expanded;
  const examReview = {
    round,
    questionNumber,
    earnedPoints: grade.earned,
    availablePoints: problem.points,
    answers: grade.details,
    referenceCode: gradingSpec.code,
    submissionError: grade.error,
    ...(grade.metric != null && {
      prediction: {
        metric: grade.metricName,
        value: grade.metric,
        threshold: grade.threshold,
        higher: grade.higher,
      },
    }),
  };

  function changeTab(event) {
    const current = TABS.findIndex(({ id }) => id === tab);
    const position = {
      ArrowLeft: (current + TABS.length - 1) % TABS.length,
      ArrowRight: (current + 1) % TABS.length,
      Home: 0,
      End: TABS.length - 1,
    }[event.key];
    if (position === undefined) return;
    event.preventDefault();
    setTab(TABS[position].id);
    tabList.current.children[position]?.focus();
  }

  return (
    <div className="mock-question-review">
      {!aiExpanded && (
        <div className="panel-tabs mock-review-tabs" role="tablist"
          aria-label={`${questionNumber}번 복습`} ref={tabList} onKeyDown={changeTab}>
          {TABS.map(({ id: name, label, icon: Icon }) => (
            <button key={name} id={`${id}-tab-${name}`} type="button" role="tab"
              aria-selected={tab === name} aria-controls={`${id}-panel-${name}`}
              tabIndex={tab === name ? 0 : -1}
              className={[tab === name && "active", name === "ai" && "gemini-tab"].filter(Boolean).join(" ")}
              onClick={() => setTab(name)}>
              <Icon size={15} /> {label}
            </button>
          ))}
        </div>
      )}
      <div id={`${id}-panel-solution`} role="tabpanel" aria-labelledby={`${id}-tab-solution`}
        className="mock-review-body" hidden={tab !== "solution"}>
        {tab === "solution" && (
          <MockQuestionSolution
            problem={problem}
            grade={grade}
            submittedCode={submittedCode}
            gradingSpec={gradingSpec}
            retry={retry}
            updateRetry={updateRetry}
            retrying={retrying}
            onRetryingChange={setRetrying}
            runner={runner}
            runId={runId}
          />
        )}
      </div>
      <div id={`${id}-panel-ai`} role="tabpanel" aria-label="AI 질문" hidden={tab !== "ai"}
        className={`mock-review-ai${aiExpanded ? " gemini-expanded" : ""}`}>
        <GeminiTutor problem={problem} code={code} result={null} examReview={examReview}
          hidden={tab !== "ai"} expanded={aiExpanded} onExpandedChange={setExpanded} />
      </div>
      <div id={`${id}-panel-note`} role="tabpanel" aria-labelledby={`${id}-tab-note`}
        className="mock-review-body" hidden={tab !== "note"}>
        {tab === "note" && (
          <PracticeNotes problem={problem} code={code} result={null}
            value={noteRecords.notes[id] || ""}
            highlights={noteRecords.highlights[id] || []}
            onHighlightsChange={(items) => noteRecords.updateHighlights(id, items)}
            onChange={(value) => noteRecords.updateNote(id, value)}
            onAppend={(value) => noteRecords.appendNote(id, value)}
            onOpenAI={() => {
              setTab("ai");
              tabList.current.children[1]?.focus();
            }} />
        )}
      </div>
    </div>
  );
}
