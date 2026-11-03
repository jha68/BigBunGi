import { useState } from "react";
import { Check, Eye, Pencil } from "lucide-react";
import { GeminiNoteGenerator } from "./GeminiTutor.jsx";
import Markdown from "./Markdown.jsx";

export default function PracticeNotes({
  problem,
  code,
  result,
  value,
  onChange,
  onAppend,
  onOpenAI,
}) {
  const [editing, setEditing] = useState(!value);
  return (
    <>
      <GeminiNoteGenerator
        problem={problem}
        code={code}
        result={result}
        onOpenAI={onOpenAI}
        onAppend={(text) => {
          onAppend(text);
          setEditing(false);
        }}
      />
      <div className="notes-heading">
        <div className="section-label">나의 풀이 노트</div>
        <button type="button" onClick={() => setEditing((current) => !current)}>
          {editing ? <Eye size={13} /> : <Pencil size={13} />}
          {editing ? "노트 보기" : "노트 편집"}
        </button>
      </div>
      {editing ? (
        <>
          <p className="note-help">
            Markdown으로 작성할 수 있습니다. 코드 블록의 줄바꿈과 들여쓰기를
            그대로 저장합니다.
          </p>
          <textarea
            className="notes-editor"
            aria-label="풀이 노트"
            placeholder={
              "예: 표준편차의 ddof 기본값 확인하기\n\n1. 접근 방법\n2. 틀린 이유\n3. 기억할 한 줄"
            }
            value={value}
            onChange={(event) => onChange(event.target.value)}
            spellCheck={false}
          />
        </>
      ) : (
        <div className="saved-note" role="region" aria-label="저장된 풀이 노트">
          {value ? (
            <Markdown text={value} />
          ) : (
            <p className="note-help">노트 편집을 눌러 메모를 작성해 보세요.</p>
          )}
        </div>
      )}
      <span className="note-saved">
        <Check size={12} /> 이 브라우저에 자동 저장
      </span>
    </>
  );
}
