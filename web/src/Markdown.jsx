import React, { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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

export default memo(function Markdown({ text }) {
  return (
    <div className="gemini-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
        skipHtml
      >
        {text}
      </ReactMarkdown>
    </div>
  );
});
