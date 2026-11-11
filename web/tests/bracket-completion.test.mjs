import { test } from "node:test";
import assert from "node:assert/strict";
import { EditorState } from "@codemirror/state";
import {
  closeBrackets,
  deleteBracketPair,
  insertBracket,
} from "@codemirror/autocomplete";
import { python } from "@codemirror/lang-python";
import { completeComposedBracket } from "../src/bracket-completion.js";

const state = (doc, anchor = doc.length, extra = []) =>
  EditorState.create({
    doc,
    selection: { anchor },
    extensions: [python(), closeBrackets(), ...extra],
  });
const commit = (before, text) =>
  before.update({
    changes: {
      from: before.selection.main.from,
      to: before.selection.main.to,
      insert: text,
    },
    selection: { anchor: before.selection.main.from + text.length },
    userEvent: "input.type.compose",
  }).state;

test("committed IME delimiters pair inside the supplied answers dictionary", () => {
  const first =
    "    \"coefficient\": model.params['ad_spend'].round(3),  # ad_spend 회귀계수";
  for (const [prefix, opening, closing] of [
    ["answers = ", "{", "}"],
    ['answers = {\n    "coefficient": model.params', "[", "]"],
    ['answers = {\n    "coefficient": model.params[', "'", "'"],
    [
      "answers = {\n    \"coefficient\": model.params['ad_spend'].round",
      "(",
      ")",
    ],
    [`answers = {\n${first}\n    `, '"', '"'],
    [`answers = {\n${first}\n    "pvalue": model.pvalues`, "[", "]"],
    [`answers = {\n${first}\n    "r_squared": model.rsquared.round`, "(", ")"],
  ]) {
    const before = state(prefix + "\n}", prefix.length);
    const transaction = completeComposedBracket(
      commit(before, opening),
      before,
      opening,
    );
    assert.equal(
      transaction.newDoc.toString(),
      prefix + opening + closing + "\n}",
    );
    assert.equal(transaction.newSelection.main.head, prefix.length + 1);
    // Pair state must survive so typing the closer skips it normally.
    const skipped = insertBracket(transaction.state, closing);
    assert.equal(skipped.newDoc.toString(), transaction.newDoc.toString());
    assert.equal(skipped.newSelection.main.head, prefix.length + 2);
    let removed;
    assert.ok(
      deleteBracketPair({
        state: transaction.state,
        dispatch: (tr) => {
          removed = tr;
        },
      }),
    );
    assert.equal(removed.newDoc.toString(), before.doc.toString());
  }
});

test("IME closers reuse the original auto-closer instead of doubling it", () => {
  for (const [opening, closing] of [
    ["(", ")"],
    ["[", "]"],
    ["{", "}"],
    ["'", "'"],
    ['"', '"'],
  ]) {
    const before = insertBracket(state(""), opening).state;
    const transaction = completeComposedBracket(
      commit(before, closing),
      before,
      closing,
    );
    assert.equal(transaction.newDoc.toString(), opening + closing);
    assert.equal(transaction.newSelection.main.head, 2);
  }
});

test("completion honors Python string boundaries and preserves selected code", () => {
  const before = state('model.params["ad_spend');
  assert.equal(completeComposedBracket(commit(before, '"'), before, '"'), null);
  const selected = state("value").update({
    selection: { anchor: 0, head: 5 },
  }).state;
  const transaction = completeComposedBracket(
    commit(selected, "("),
    selected,
    "(",
  );
  assert.equal(transaction.newDoc.toString(), "(value)");
  assert.deepEqual(
    [transaction.newSelection.main.from, transaction.newSelection.main.to],
    [1, 6],
  );
});

test("cancelled/bulk IME, read-only state and intervening edits never get rewritten", () => {
  const before = state("answers = ");
  for (const text of ["", "한글", "[1, 2]", "한("])
    assert.equal(
      completeComposedBracket(commit(before, text), before, text),
      null,
    );
  assert.equal(completeComposedBracket(commit(before, "("), null, "("), null);
  const changed = commit(before, "(").update({
    changes: { from: 0, insert: "# edited\n" },
  }).state;
  assert.equal(completeComposedBracket(changed, before, "("), null);
  const moved = commit(before, "(").update({ selection: { anchor: 0 } }).state;
  assert.equal(completeComposedBracket(moved, before, "("), null);
  const readOnly = state("", 0, [EditorState.readOnly.of(true)]);
  assert.equal(
    completeComposedBracket(commit(readOnly, "("), readOnly, "("),
    null,
  );
});
