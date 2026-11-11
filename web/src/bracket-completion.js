import { insertBracket } from "@codemirror/autocomplete";

// The normal closeBrackets input handler skips IME updates. Once a single
// delimiter has actually been committed, apply the same language-aware behavior
// to it, including selection wrapping and skipping an existing auto-closer.
export function completeComposedBracket(current, before, text) {
  if (
    !before ||
    current.readOnly ||
    !/^[()[\]{}'"]$/.test(text || "") ||
    before.selection.ranges.length !== 1 ||
    current.selection.ranges.length !== 1
  )
    return null;
  const range = before.selection.main;
  const typed = before.changes({
    from: range.from,
    to: range.to,
    insert: text,
  });
  if (
    !typed.apply(before.doc).eq(current.doc) ||
    !current.selection.main.empty ||
    current.selection.main.head !== range.from + 1
  )
    return null;

  const paired = insertBracket(before, text);
  if (!paired) return null;
  return current.update({
    changes: typed.invert(before.doc).compose(paired.changes),
    selection: paired.newSelection,
    effects: paired.effects,
    userEvent: "input.type.compose",
    scrollIntoView: true,
  });
}
