import { useEffect, useRef } from "react";
import { EditorView, basicSetup } from "codemirror";
import { EditorState, Prec } from "@codemirror/state";
import { keymap } from "@codemirror/view";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";

export default function CodeEditor({
  value,
  onChange,
  onRun,
  fontSize = 13,
  readOnly = false,
  label,
}) {
  const host = useRef(null),
    view = useRef(null),
    change = useRef(onChange),
    run = useRef(onRun);
  change.current = onChange;
  run.current = onRun;
  useEffect(() => {
    view.current = new EditorView({
      doc: value,
      extensions: [
        // basicSetup binds Mod-Enter to insertBlankLine. Our run command must
        // take precedence over that keymap on Windows, Linux and macOS.
        ...(readOnly
          ? []
          : [
              Prec.highest(
                keymap.of(
                  ["Mod-Enter", "Ctrl-Enter"].map((key) => ({
                    key,
                    run: () => {
                      run.current?.();
                      return true;
                    },
                    preventDefault: true,
                  })),
                ),
              ),
            ]),
        basicSetup,
        python(),
        oneDark,
        EditorState.readOnly.of(readOnly),
        EditorView.editable.of(!readOnly),
        ...(readOnly ? [EditorView.lineWrapping] : []),
        EditorView.contentAttributes.of({
          "aria-label":
            label || (readOnly ? "Python 기준 풀이" : "Python 코드 편집기"),
          "aria-readonly": String(readOnly),
          ...(readOnly ? { tabindex: "0" } : {}),
          spellcheck: "false",
        }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) change.current?.(update.state.doc.toString());
        }),
      ],
      parent: host.current,
    });
    return () => view.current?.destroy();
  }, []);
  useEffect(() => {
    const editor = view.current;
    if (editor && editor.state.doc.toString() !== value)
      editor.dispatch({
        changes: { from: 0, to: editor.state.doc.length, insert: value },
      });
  }, [value]);
  return (
    <div
      ref={host}
      className={readOnly ? "reference-code" : "code-editor"}
      style={{ "--code-font-size": `${fontSize}px` }}
    />
  );
}
