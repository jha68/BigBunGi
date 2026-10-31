/* Python is isolated in a browser worker; user code never executes on the host. */
const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
let runtime;

const executor = String.raw`
import ast, io, json, contextlib, traceback, os, shutil, csv, math, sys, base64

class _BoundedOutput(io.StringIO):
    def write(self, value):
        remaining = 40000-self.tell()
        if remaining <= 0:
            return len(value)
        super().write(value[:remaining])
        return len(value)

def _clean(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if hasattr(value, 'item'):
        return _clean(value.item())
    return str(value)

def _run_source(source):
    output, errors = _BoundedOutput(), _BoundedOutput()
    scope = {'__name__': '__main__'}
    result = {'stdout': '', 'stderr': '', 'error': None, 'answers': {}, 'submission': None, 'display': None, 'plots': []}
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        try:
            tree = ast.parse(source, filename='solution.py', mode='exec')
            last = tree.body.pop() if tree.body and isinstance(tree.body[-1], ast.Expr) else None
            exec(compile(tree, 'solution.py', 'exec'), scope)
            if last:
                value = eval(compile(ast.Expression(last.value), 'solution.py', 'eval'), scope)
                if value is not None:
                    if hasattr(value, 'to_json') and hasattr(value, 'columns'):
                        table = json.loads(value.head(20).to_json(orient='split', force_ascii=False))
                        result['display'] = {'kind': 'table', 'columns': table['columns'], 'rows': table['data'], 'total': len(value)}
                    else:
                        result['display'] = {'kind': 'text', 'text': repr(value)[:12000]}
            if isinstance(scope.get('answers'), dict):
                result['answers'] = _clean(scope['answers'])
            if os.path.isfile('submission.csv'):
                if os.path.getsize('submission.csv') > 1048576:
                    raise ValueError('submission.csv는 1MB 이하여야 합니다.')
                with open('submission.csv', encoding='utf-8-sig', newline='') as handle:
                    reader = csv.DictReader(handle)
                    rows = list(reader)
                    result['submission'] = {'columns': reader.fieldnames or [], 'rows': rows}
                result['submissionText'] = open('submission.csv', encoding='utf-8-sig').read()
            if 'matplotlib.pyplot' in sys.modules:
                plt = sys.modules['matplotlib.pyplot']
                for number in plt.get_fignums()[:4]:
                    buffer = io.BytesIO()
                    plt.figure(number).savefig(buffer, format='png', bbox_inches='tight', dpi=100)
                    result['plots'].append(base64.b64encode(buffer.getvalue()).decode('ascii'))
                plt.close('all')
        except BaseException:
            result['error'] = traceback.format_exc()[-12000:]
    result['stdout'] = output.getvalue() + ('\n[출력은 40,000자까지 표시됩니다.]' if output.tell() >= 40000 else '')
    result['stderr'] = errors.getvalue()
    return json.dumps(_clean(result), ensure_ascii=False, allow_nan=False)
`;

async function initialize() {
  postMessage({ type: "status", message: "Python 실행 환경 준비 중…" });
  importScripts(PYODIDE_URL + "pyodide.js");
  runtime = await loadPyodide({
    indexURL: PYODIDE_URL,
    stdout: () => {},
    stderr: () => {},
  });
  postMessage({ type: "status", message: "pandas · NumPy 불러오는 중…" });
  await runtime.loadPackage(["numpy", "pandas"]);
  runtime.runPython(executor);
  postMessage({
    type: "ready",
    version: runtime.runPython("sys.version.split()[0]"),
  });
}

self.onmessage = async ({ data }) => {
  if (data.type === "init") {
    try {
      await initialize();
    } catch (error) {
      postMessage({
        type: "fatal",
        message:
          "Python을 불러오지 못했습니다. 인터넷 연결을 확인한 뒤 실행 환경을 다시 시작하세요. " +
          error.message,
      });
    }
    return;
  }
  if (data.type !== "run" || !runtime) return;
  const { id, code, files } = data;
  try {
    postMessage({
      type: "packages",
      id,
      message: "필요한 라이브러리 확인 중…",
    });
    await runtime.loadPackagesFromImports(code);
    runtime.runPython(
      "os.chdir('/'); shutil.rmtree('/exam', ignore_errors=True); os.makedirs('/exam/data', exist_ok=True); os.chdir('/exam')",
    );
    for (const [name, content] of Object.entries(files))
      runtime.FS.writeFile("/exam/data/" + name, content, { encoding: "utf8" });
    postMessage({ type: "executing", id });
    const start = performance.now();
    runtime.globals.set("_source_text", code);
    const raw = await runtime.runPythonAsync("_run_source(_source_text)");
    runtime.globals.delete("_source_text");
    postMessage({
      type: "result",
      id,
      result: JSON.parse(raw),
      duration: (performance.now() - start) / 1000,
    });
  } catch (error) {
    postMessage({
      type: "result",
      id,
      result: {
        stdout: "",
        stderr: "",
        error: String(error.message || error),
        answers: {},
        submission: null,
        plots: [],
      },
      duration: 0,
    });
  }
};
