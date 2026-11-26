import { Play, Square } from "lucide-react";

export function TaskFiles({ files }) {
  if (!files.length) return null;
  return (
    <div className="mock-file-list" aria-label="실습 데이터 파일">
      {files.map((file) => (
        <details className="mock-dataset" key={file.name}>
          <summary><code>data/{file.name}</code><small>{file.rows}행</small></summary>
          <dl>
            {file.columns.map(({ name, description }) => (
              <div key={name}><dt><code>{name}</code></dt><dd>{description}</dd></div>
            ))}
          </dl>
        </details>
      ))}
    </div>
  );
}

export function ExamAnswerFields({ fields, values, onChange }) {
  return (
    <div className="mock-answer-fields">
      {fields.map((field, position) => (
        <label key={field.key}>
          <span>
            {fields.length > 1 && (position + 1) + ". "}
            {field.label}<small>{field.format} · {field.points}점</small>
          </span>
          <input
            type="text"
            inputMode={field.decimals == null ? "text" : "decimal"}
            aria-label={field.label}
            autoComplete="off"
            maxLength={300}
            value={values[field.key] ?? ""}
            onChange={(event) => onChange(field.key, event.target.value)}
          />
        </label>
      ))}
    </div>
  );
}

export function MockRunToolbar({ runner, runId, onRun }) {
  const { running, runtime } = runner;
  const canStop = running && (!runId || running.id === runId);
  return (
    <div className="mock-run-bar">
      <span role="status">{running?.stage || runtime.message}</span>
      {runtime.error ? (
        <button className="mock-secondary" onClick={runner.onRestartRuntime}>다시 시작</button>
      ) : canStop ? (
        <button className="mock-secondary" onClick={runner.onStop}><Square size={13} /> 중지</button>
      ) : (
        <button className="mock-primary" disabled={Boolean(running) || !runtime.ready} onClick={onRun}>
          <Play size={14} /> 코드 실행
        </button>
      )}
    </div>
  );
}

export function ExamConsole({ result }) {
  const { stdout, stderr, error, display, plots = [] } = result || {};
  return (
    <div className="mock-console" aria-live="polite">
      {stdout && <pre>{stdout}</pre>}
      {stderr && <pre className="warning-output">{stderr}</pre>}
      {error && <pre className="error-output">{error}</pre>}
      {display?.kind === "text" && <pre>{display.text}</pre>}
      {display?.kind === "table" && (
        <div className="table-scroll">
          <table>
            <thead><tr>{display.columns.map((column, i) => <th key={i}>{column}</th>)}</tr></thead>
            <tbody>{display.rows.map((row, i) => (
              <tr key={i}>{row.map((value, j) => <td key={j}>{String(value ?? "NaN")}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {plots.map((plot, index) => <img className="result-plot" key={index} src={"data:image/png;base64," + plot} alt={"분석 그래프 " + (index + 1)} />)}
      {!stdout && !stderr && !error && !display && !plots.length && (
        <p>{result ? "코드 실행 완료" : "코드 실행 결과가 여기에 표시됩니다."}</p>
      )}
    </div>
  );
}
