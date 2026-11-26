import { Bookmark } from "lucide-react";

export default function RetryMark({ marked, onToggle, problemTitle, compact = false }) {
  const label = "다시 풀기 표시";
  return (
    <button
      type="button"
      className={`retry-mark${compact ? " retry-mark-compact" : ""}`}
      aria-label={problemTitle ? `${problemTitle} ${label}` : label}
      aria-pressed={marked}
      title={marked ? "다시 풀기 표시 해제" : label}
      onClick={onToggle}
    >
      <Bookmark size={15} aria-hidden="true" />
      {!compact && <span>{label}</span>}
    </button>
  );
}
