import React, { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import CodeEditor from "./CodeEditor.jsx";

const components = {
  pre({ children }) {
    const child = React.Children.toArray(children)[0];
    if (
      React.isValidElement(child) &&
      /language-(python|py)\b/.test(child.props.className || "")
    ) {
      return (
        <CodeEditor
          value={String(child.props.children).replace(/\n$/, "")}
          readOnly
          fontSize={11}
          label="Python 코드 예시"
        />
      );
    }
    return <pre>{children}</pre>;
  },
  a({ href, children }) {
    return /^https?:\/\//.test(href || "") ? (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    ) : (
      <span>{children}</span>
    );
  },
  img({ alt }) {
    return <span>{alt || "이미지"}</span>;
  },
};

export default memo(function Markdown({ text, onSelectProblem }) {
  const renderers = onSelectProblem
    ? {
        ...components,
        a({ href, children }) {
          const match = /^#(t[123]-\d{2})$/.exec(href || "");
          return match ? (
            <a
              href={href}
              onClick={(event) => {
                event.preventDefault();
                onSelectProblem(match[1]);
              }}
            >
              {children}
            </a>
          ) : (
            components.a({ href, children })
          );
        },
      }
    : components;
  return (
    <div className="gemini-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, { trust: false }]]}
        components={renderers}
        skipHtml
      >
        {text}
      </ReactMarkdown>
    </div>
  );
});
