// Runs only in GitHub Actions with repository secrets; never outputs credentials.
import { createHash, pbkdf2Sync, randomBytes } from "node:crypto";
import { mkdtemp, writeFile, rm, appendFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import {
  safeDiagnostic,
  errorAnnotation,
  commandFailure,
} from "./diagnostics.mjs";

const account = process.env.CLOUDFLARE_ACCOUNT_ID;
const token = process.env.CLOUDFLARE_API_TOKEN;
const password = process.env.SYNC_PASSWORD;
const sensitive = [account, token, password];
process.on("uncaughtException", (error) => {
  console.error(errorAnnotation(error.message, sensitive));
  process.exit(1);
});
if (process.env.SYNC_FREE_PLAN_CONFIRMED !== "true")
  throw new Error(
    "Deployment stopped before creating resources: first verify that this account uses Workers/D1 Free, then set SYNC_FREE_PLAN_CONFIRMED=true. Paid plans are not supported by this setup.",
  );
const root = fileURLToPath(new URL(".", import.meta.url));
const domain = "bigbungi-api.junununseo.com";
function configurationError(message) {
  // Surface the actionable cause in the Actions summary without secret values.
  console.error(`::error title=Sync configuration::${message}`);
  process.exit(1);
}
const missing = [
  ["CLOUDFLARE_ACCOUNT_ID", account],
  ["CLOUDFLARE_API_TOKEN", token],
  ["SYNC_PASSWORD", password],
]
  .filter(([, value]) => !value)
  .map(([name]) => name);
if (missing.length)
  configurationError(
    `Missing repository Actions secret: ${missing.join(", ")}. Add each secret separately using its exact name.`,
  );
if (password.length < 12 || password.length > 128)
  configurationError(
    "SYNC_PASSWORD must contain 12-128 characters. Update only the SYNC_PASSWORD repository Actions secret, then rerun this workflow. Cloudflare has not been contacted.",
  );
const api = async (path, data, allowMissing = false) => {
  const response = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${account}${path}`,
    {
      method: data === undefined ? "GET" : "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: data === undefined ? undefined : JSON.stringify(data),
      signal: AbortSignal.timeout(30000),
    },
  );
  const body = await response.json();
  if (response.status === 404 && allowMissing) return [];
  if (!response.ok || !body.success)
    throw new Error(
      `Cloudflare ${path.split("?")[0]} failed (HTTP ${response.status}): ${JSON.stringify(body.errors || [])}. Check token permissions and account ID.`,
    );
  return body.result;
};
const wrangler = (args, input) => {
  const run = spawnSync(
    process.execPath,
    [join(root, "node_modules/wrangler/bin/wrangler.js"), ...args],
    {
      cwd: root,
      env: process.env,
      input,
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
      maxBuffer: 10 * 1024 * 1024,
    },
  );
  if (run.stdout) process.stdout.write(safeDiagnostic(run.stdout, sensitive));
  if (run.stderr) process.stderr.write(safeDiagnostic(run.stderr, sensitive));
  if (run.status !== 0)
    throw new Error(commandFailure(args[0], run.stdout, run.stderr));
};
const dir = await mkdtemp(join(tmpdir(), "bigbungi-sync-"));
try {
  console.log("::notice::Sync setup: checking Cloudflare D1 access.");
  const databases = await api("/d1/database?name=bigbungi-sync");
  const database =
    databases.find((entry) => entry.name === "bigbungi-sync") ||
    (await api("/d1/database", { name: "bigbungi-sync" }));
  const config = join(dir, "wrangler.json");
  await writeFile(
    config,
    JSON.stringify({
      name: "bigbungi-sync",
      main: join(root, "worker.js"),
      compatibility_date: "2026-11-01",
      workers_dev: false,
      preview_urls: false,
      routes: [{ pattern: domain, custom_domain: true }],
      vars: { APP_ORIGIN: "https://bigbungi.junununseo.com" },
      d1_databases: [
        {
          binding: "DB",
          database_name: "bigbungi-sync",
          database_id: database.uuid,
        },
      ],
      observability: { enabled: false },
    }),
  );
  wrangler([
    "d1",
    "execute",
    "bigbungi-sync",
    "--remote",
    "--file",
    join(root, "schema.sql"),
    "--config",
    config,
  ]);
  // A unique, stable per-account/application salt avoids logging everyone out on
  // every frontend deployment. Changing the password invalidates all sessions.
  const salt = createHash("sha256")
    .update(account + ":bigbungi-sync")
    .digest()
    .subarray(0, 16);
  const hash = `pbkdf2-100000:${salt.toString("hex")}:${pbkdf2Sync(password, salt, 100000, 32, "sha256").toString("hex")}`;
  sensitive.push(hash);
  // A separate stable secret keeps conversations readable when the login password
  // changes. Wrangler preserves existing secret bindings on every deployment.
  const bindings = await api(
    "/workers/scripts/bigbungi-sync/secrets",
    undefined,
    true,
  );
  const secretValues = { PASSWORD_HASH: hash };
  if (!bindings.some((binding) => binding.name === "HISTORY_KEY")) {
    const records = await api(`/d1/database/${database.uuid}/query`, {
      sql: "SELECT COUNT(*) AS count FROM conversations WHERE data IS NOT NULL",
    });
    if (records[0]?.results?.[0]?.count !== 0)
      throw new Error(
        "HISTORY_KEY is missing while saved conversations exist. Restore the existing Worker secret; refusing to replace the encryption key.",
      );
    secretValues.HISTORY_KEY = randomBytes(32).toString("hex");
    sensitive.push(secretValues.HISTORY_KEY);
  }
  const secrets = join(dir, "secrets.json");
  await writeFile(secrets, JSON.stringify(secretValues), {
    mode: 0o600,
  });
  wrangler(["deploy", "--config", config, "--secrets-file", secrets]);
  // Smoke test real authentication without printing passwords or session cookies.
  let verified = false;
  let lastFailure = "unknown";
  const responseFailure = async (stage, response) => {
    const body = safeDiagnostic(await response.text(), sensitive);
    const detail = body.match(/<title>([\s\S]*?)<\/title>/i)?.[1] || body;
    return new Error(
      `${stage} HTTP ${response.status}: ${detail.slice(0, 800)}`,
    );
  };
  for (let attempt = 0; attempt < 24; attempt++) {
    try {
      const response = await fetch(`https://${domain}/login`, {
        method: "POST",
        headers: {
          Origin: "https://bigbungi.junununseo.com",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
        signal: AbortSignal.timeout(12000),
      });
      if (!response.ok) throw await responseFailure("Login", response);
      const cookie = response.headers.get("set-cookie")?.split(";")[0];
      if (!cookie) throw new Error("Login returned no session cookie");
      sensitive.push(cookie, cookie.slice(cookie.indexOf("=") + 1));
      const state = await fetch(`https://${domain}/state`, {
        headers: { Cookie: cookie },
        signal: AbortSignal.timeout(12000),
      });
      if (!state.ok) throw await responseFailure("Authenticated state", state);
      const conversation = await fetch(
        `https://${domain}/conversations/t1-01`,
        {
          headers: { Cookie: cookie },
          signal: AbortSignal.timeout(12000),
        },
      );
      if (!conversation.ok)
        throw await responseFailure("Authenticated conversation", conversation);
      await fetch(`https://${domain}/logout`, {
        method: "POST",
        headers: { Cookie: cookie, Origin: "https://bigbungi.junununseo.com" },
        signal: AbortSignal.timeout(12000),
      });
      verified = true;
      break;
    } catch (error) {
      lastFailure = `${error.message}${error.cause?.code ? " (" + error.cause.code + ")" : ""}`;
      if (attempt === 0 || attempt % 6 === 5)
        console.log(
          `::notice::Waiting for sync HTTPS: ${safeDiagnostic(
            lastFailure,
            sensitive,
          )
            .replace(/[\r\n]/g, " ")
            .slice(0, 900)}`,
        );
      if (/Login HTTP (400|401|403|429):/.test(lastFailure)) break;
      if (attempt < 23)
        await new Promise((resolve) => setTimeout(resolve, 10000));
    }
  }
  if (!verified)
    throw new Error(
      `Sync HTTPS/login verification failed: ${lastFailure}. Frontend password login has not been enabled.`,
    );
  if (process.env.GITHUB_OUTPUT)
    await appendFile(process.env.GITHUB_OUTPUT, `api_url=https://${domain}\n`);
  console.log(
    "::notice::SYNC VERIFIED: HTTPS password login, record and encrypted conversation access at https://" +
      domain,
  );
} finally {
  await rm(dir, { recursive: true, force: true });
}
