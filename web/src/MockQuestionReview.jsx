import { useRef, useState } from "react";
import { BookOpen, CheckCircle2, FileCode2, Sparkles } from "lucide-react";
import CodeEditor from "./CodeEditor.jsx";
import { GeminiTutor } from "./GeminiTutor.jsx";
import PracticeNotes from "./PracticeNotes.jsx";

const TABS = [
  { id: "solution", label: "풀이", icon: BookOpen },
  { id: "ai", label: "AI 질문", icon: Sparkles },
  { id: "note", label: "노트", icon: FileCode2 },
];

function QuestionSolution({ problem, grade, submittedCode, referenceCode }) {
  return (
    <>
      {problem.scenario && <p>{problem.scenario}</p>}
      <ol>{problem.steps.map((step) => <li key={step}>{step}</li>)}</ol>
      {grade.details?.map((detail) => (
        <div key={detail.key} className="mock-answer-review">
          {detail.correct ? (
            <CheckCircle2 size={17} aria-label="정답" />
          ) : (
            <span className="mock-error">오답</span>
          )}
          <strong>{detail.label}</strong>
          <span>제출 {detail.actual ?? "미입력"}</span>
          <span>정답 {detail.expected}</span>
          {detail.formatError && <small className="mock-error">{detail.formatError}</small>}
        </div>
      ))}
      {grade.metric != null && (
        <p>
          {grade.metricName} <strong>{grade.metric.toFixed(4)}</strong>
          {" · 모의 만점 기준 "}{grade.threshold.toFixed(4)} {grade.higher ? "이상" : "이하"}
        </p>
      )}
      {grade.error && <p className="mock-error">{grade.error}</p>}
      {(submittedCode || referenceCode) && (
        <div className="mock-review-code">
          {submittedCode && (
            <section aria-label="내 코드">
              <h3>내 코드</h3>
              <CodeEditor value={submittedCode} readOnly label="내 Python 코드" />
            </section>
          )}
          {referenceCode && (
            <section aria-label="기준 풀이 코드">
              <h3>기준 풀이 코드</h3>
              <CodeEditor value={referenceCode} readOnly />
            </section>
          )}
        </div>
      )}
    </>
  );
}

export default function MockQuestionReview({
  problem, round, questionNumber, grade, submittedCode, referenceCode, noteRecords,
}) {
  const [tab, setTab] = useState("solution");
  const [expanded, setExpanded] = useState(false);
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
    referenceCode,
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
        {tab === "solution" && <QuestionSolution {...{ problem, grade, submittedCode, referenceCode }} />}
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
