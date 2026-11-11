import { useEffect, useRef } from "react";
import { EditorView, basicSetup } from "codemirror";
import { EditorState, Prec } from "@codemirror/state";
import { keymap } from "@codemirror/view";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";
import { completeComposedBracket } from "./bracket-completion.js";

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
    let composition = null,
      compositionVersion = 0,
      alive = true;
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
        EditorView.domEventHandlers({
          compositionstart(_event, editor) {
            composition = editor.state;
            compositionVersion++;
            return false;
          },
          compositionend(event, editor) {
            const before = composition,
              version = ++compositionVersion;
            composition = null;
            // Let CodeMirror flush the final IME change before comparing it
            // with the state at compositionstart. Never edit active preedit.
            queueMicrotask(() => {
              if (
                !alive ||
                version !== compositionVersion ||
                editor.compositionStarted
              )
                return;
              const transaction = completeComposedBracket(
                editor.state,
                before,
                event.data,
              );
              if (transaction) editor.dispatch(transaction);
            });
            return false;
          },
          beforeinput(event, editor) {
            // Chrome/Edge can deliver confirmed text before compositionend
            // after Korean IME input. Close the stale DOM composition before
            // CodeMirror's bracket handler sees that text. Actual IME updates
            // (insertCompositionText / isComposing) must remain untouched.
            if (
              !editor.state.readOnly &&
              !editor.contentDOM.editContext &&
              editor.compositionStarted &&
              event.inputType === "insertText" &&
              event.isComposing === false
            ) {
              editor.contentDOM.dispatchEvent(
                new CompositionEvent("compositionend", { bubbles: true }),
              );
            }
            return false;
          },
        }),
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
    return () => {
      alive = false;
      view.current?.destroy();
    };
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
