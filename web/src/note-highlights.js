export function noteHash(text = "") {
  let hash = 2166136261;
  for (let i = 0; i < text.length; i++)
    hash = Math.imul(hash ^ text.charCodeAt(i), 16777619);
  return `${text.length}:${(hash >>> 0).toString(16)}`;
}
export const activeHighlights = (note, highlights = []) =>
  highlights.filter((item) => item.noteHash === noteHash(note));

export function rebaseHighlights(previous, next, highlights = []) {
  const unique = (text) =>
    text &&
    next.includes(text) &&
    next.indexOf(text) === next.lastIndexOf(text);
  return highlights.map((item) => {
    if (item.noteHash === noteHash(next)) return item;
    if (
      (item.noteHash === noteHash(previous) && next.startsWith(previous)) ||
      unique(item.text) ||
      unique(item.quote)
    )
      return { ...item, noteHash: noteHash(next) };
    return item;
  });
}

function textNodes(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (
      !node.parentElement.closest(
        ".cm-gutters, .katex-mathml, button, [data-highlight-ignore]",
      )
    )
      nodes.push(node);
  }
  return nodes;
}

export function selectedHighlight(root, note) {
  const selection = window.getSelection();
  if (!selection?.rangeCount || selection.isCollapsed) return null;
  const range = selection.getRangeAt(0);
  if (
    !root?.contains(range.startContainer) ||
    !root.contains(range.endContainer)
  )
    return null;
  const nodes = textNodes(root),
    flat = nodes.map((node) => node.data).join("");
  let offset = 0,
    start = null,
    quote = "",
    text = "",
    block = null;
  for (const node of nodes) {
    if (range.intersectsNode(node)) {
      const from = node === range.startContainer ? range.startOffset : 0;
      const to = node === range.endContainer ? range.endOffset : node.length;
      const part = node.data.slice(from, to);
      if (part) {
        if (start === null) start = offset + from;
        const nextBlock = node.parentElement.closest(
          ".cm-line, p, li, pre, h1, h2, h3, td",
        );
        if (block && nextBlock && block !== nextBlock) text += "\n";
        text += part;
        quote += part;
        block = nextBlock;
      }
    }
    offset += node.length;
  }
  if (start === null || !quote.trim()) return null;
  return {
    text,
    quote,
    start,
    before: flat.slice(Math.max(0, start - 64), start),
    after: flat.slice(start + quote.length, start + quote.length + 64),
    noteHash: noteHash(note),
  };
}

export function paintHighlights(root, note, highlights) {
  if (!globalThis.CSS?.highlights || !globalThis.Highlight || !root) return;
  const nodes = textNodes(root),
    flat = nodes.map((node) => node.data).join(""),
    ranges = [];
  for (const item of activeHighlights(note, highlights)) {
    let at = flat.indexOf(item.quote, item.start),
      best = -1;
    if (at === item.start) best = at;
    else {
      at = flat.indexOf(item.quote);
      while (at !== -1) {
        if (
          (!item.before ||
            flat.slice(Math.max(0, at - item.before.length), at) ===
              item.before) &&
          (!item.after ||
            flat.slice(
              at + item.quote.length,
              at + item.quote.length + item.after.length,
            ) === item.after)
        ) {
          best = at;
          break;
        }
        at = flat.indexOf(item.quote, at + 1);
      }
    }
    if (best < 0 && flat.indexOf(item.quote) === flat.lastIndexOf(item.quote))
      best = flat.indexOf(item.quote);
    if (best < 0) continue;
    let offset = 0,
      range = document.createRange(),
      started = false;
    for (const node of nodes) {
      if (!started && best < offset + node.length) {
        range.setStart(node, best - offset);
        started = true;
      }
      if (started && best + item.quote.length <= offset + node.length) {
        range.setEnd(node, best + item.quote.length - offset);
        ranges.push(range);
        break;
      }
      offset += node.length;
    }
  }
  CSS.highlights.set("practice-notes", new Highlight(...ranges));
}
