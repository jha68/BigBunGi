import {
  ArrowLeft,
  ArrowRight,
  Database,
  FlaskConical,
  BookOpen,
  Sparkles,
  Highlighter,
} from "lucide-react";
import { GeminiTutor } from "./GeminiTutor.jsx";
import { HOME_PROBLEM } from "./study-context.js";
import { activeHighlights } from "./note-highlights.js";
import "./home.css";

const TYPES = [
  {
    type: 1,
    title: "데이터 전처리",
    icon: Database,
    description: "조건 필터링, 결측치, 그룹 집계와 데이터 변환",
  },
  {
    type: 2,
    title: "머신러닝 모델링",
    icon: FlaskConical,
    description: "전처리부터 학습·예측·제출까지 연습하기",
  },
  {
    type: 3,
    title: "통계 분석",
    icon: BookOpen,
    description: "가설 검정과 회귀분석 결과 해석하기",
  },
];

export default function HomeScreen({
  catalog,
  notes,
  highlights,
  progress,
  mode,
  onModeChange,
  onSelect,
  onSelectType,
  syncStatus,
}) {
  const studyData = { catalog, notes, highlights, progress, syncStatus };
  const highlightCount = Object.entries(highlights).reduce(
    (sum, [pid, items]) =>
      sum + activeHighlights(notes[pid] || "", items).length,
    0,
  );
  const solved = catalog.filter(
    (problem) => progress[problem.id]?.passed,
  ).length;
  return (
    <section
      className={`study-home ${mode === "ai" ? "study-chat" : ""}`}
      aria-label="학습 홈"
    >
      {mode === "ai" ? (
        <>
          <div className="home-chat-heading">
            <button onClick={() => onModeChange("overview")}>
              <ArrowLeft size={15} /> 학습 홈
            </button>
            <span>문제별 대화와 별도로 저장되는 전체 학습 대화</span>
          </div>
          <div className="home-ai-panel">
            <GeminiTutor
              problem={HOME_PROBLEM}
              code=""
              result={null}
              studyData={studyData}
              onSelectProblem={onSelect}
            />
          </div>
        </>
      ) : (
        <>
          <div className="home-intro">
            <span>BIG DATA, BIG STEP</span>
            <h1>오늘은 무엇을 연습할까요?</h1>
            <p>유형별로 문제를 풀고, 쌓인 학습 기록을 AI와 함께 복습하세요.</p>
          </div>
          <div className="home-records">
            <span>
              완료한 문제{" "}
              <strong>
                {solved} / {catalog.length}
              </strong>
            </span>
            <span>
              작성한 노트{" "}
              <strong>
                {Object.values(notes).filter((note) => note.trim()).length}
              </strong>
            </span>
            <span>
              <Highlighter size={14} /> 강조한 내용{" "}
              <strong>{highlightCount}</strong>
            </span>
          </div>
          <div className="home-types">
            {TYPES.map(({ type, title, icon: Icon, description }) => {
              const problems = catalog.filter(
                (problem) => problem.type === type,
              );
              return (
                <button
                  key={type}
                  onClick={() => onSelectType(type)}
                  disabled={!problems.length}
                >
                  <Icon size={25} />
                  <small>
                    작업형 {type}유형 · {problems.length}문제
                  </small>
                  <h2>{title}</h2>
                  <p>{description}</p>
                  <span>
                    연습 시작 <ArrowRight size={15} />
                  </span>
                </button>
              );
            })}
          </div>
          <button className="home-ai-card" onClick={() => onModeChange("ai")}>
            <Sparkles size={29} />
            <div>
              <h2>AI 질문하기</h2>
              <p>
                AI에게 질문했던 문제를 찾고, 전체 노트와 형광펜 내용을 모아
                복습하세요.
              </p>
              <small>
                문제별 AI와 같은 키·모델을 사용하고 대화는 별도로 저장합니다.
              </small>
            </div>
            <ArrowRight size={21} />
          </button>
        </>
      )}
    </section>
  );
}
