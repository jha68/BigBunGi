import { useEffect, useRef, useState } from "react";
import { Check, Eye, Pencil, Highlighter, X } from "lucide-react";
import { GeminiNoteGenerator } from "./GeminiTutor.jsx";
import Markdown from "./Markdown.jsx";
import {
  activeHighlights,
  noteHash,
  paintHighlights,
  rebaseHighlights,
  selectedHighlight,
} from "./note-highlights.js";

export default function PracticeNotes({
  problem,
  code,
  result,
  value,
  onChange,
  onAppend,
  onOpenAI,
  highlights = [],
  onHighlightsChange,
}) {
  const [editing, setEditing] = useState(!value);
  const [selection, setSelection] = useState(null),
    [highlightError, setHighlightError] = useState("");
  const preview = useRef(null),
    previous = useRef(value);
  useEffect(() => {
    if (previous.current !== value) {
      const next = rebaseHighlights(previous.current, value, highlights);
      if (next.some((item, index) => item !== highlights[index]))
        onHighlightsChange?.(next);
      previous.current = value;
    }
  }, [value, highlights, onHighlightsChange]);
  useEffect(() => {
    const changed = () =>
      setSelection(editing ? null : selectedHighlight(preview.current, value));
    document.addEventListener("selectionchange", changed);
    return () => document.removeEventListener("selectionchange", changed);
  }, [value, editing]);
  useEffect(() => {
    if (!preview.current || editing) return;
    const root = preview.current;
    const paint = () => paintHighlights(root, value, highlights);
    paint();
    const observer = new MutationObserver(paint);
    observer.observe(root, {
      childList: true,
      subtree: true,
      characterData: true,
    });
    return () => {
      observer.disconnect();
      globalThis.CSS?.highlights?.delete("practice-notes");
    };
  }, [value, editing, highlights]);
  function highlightSelection() {
    setHighlightError("");
    if (!selection || selection.noteHash !== noteHash(value)) return;
    if (selection.text.length > 6000 || selection.quote.length > 6000) {
      setHighlightError("강조할 내용은 6,000자 이내로 선택해 주세요.");
      return;
    }
    if (highlights.length >= 100) {
      setHighlightError("문제당 형광펜은 100개까지 저장할 수 있습니다.");
      return;
    }
    if (
      highlights.some(
        (item) =>
          item.quote === selection.quote &&
          item.start === selection.start &&
          item.noteHash === selection.noteHash,
      )
    )
      return;
    onHighlightsChange?.([
      ...highlights,
      {
        ...selection,
        id:
          crypto.randomUUID?.() ||
          `highlight-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      },
    ]);
    window.getSelection()?.removeAllRanges();
    setSelection(null);
  }
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
        <button
          type="button"
          className="note-highlight-add"
          disabled={editing || !selection}
          title="노트 보기에서 내용을 드래그한 뒤 눌러 주세요"
          onMouseDown={(event) => event.preventDefault()}
          onClick={highlightSelection}
        >
          <Highlighter size={13} /> 형광펜
        </button>
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
        <div
          ref={preview}
          className="saved-note"
          role="region"
          aria-label="저장된 풀이 노트"
        >
          {value ? (
            <Markdown text={value} />
          ) : (
            <p className="note-help">노트 편집을 눌러 메모를 작성해 보세요.</p>
          )}
        </div>
      )}
      {!editing && !!value && (
        <p className="note-highlight-help">
          문장이나 코드를 드래그한 뒤 형광펜을 누르면 강조가 저장됩니다.
        </p>
      )}
      {highlightError && (
        <p role="alert" className="gemini-form-error">
          {highlightError}
        </p>
      )}
      {!!highlights.length && (
        <details className="note-highlights-list">
          <summary>
            강조한 내용 {activeHighlights(value, highlights).length}개
          </summary>
          {highlights.map((item) => (
            <div key={item.id}>
              <mark>{item.text}</mark>
              {item.noteHash !== noteHash(value) && (
                <small>원문이 변경되어 다시 강조해야 합니다.</small>
              )}
              <button
                type="button"
                aria-label="강조 지우기"
                onClick={() =>
                  onHighlightsChange?.(
                    highlights.filter((entry) => entry.id !== item.id),
                  )
                }
              >
                <X size={13} />
              </button>
            </div>
          ))}
        </details>
      )}
      <span className="note-saved">
        <Check size={12} /> 이 브라우저에 자동 저장
      </span>
    </>
  );
}
