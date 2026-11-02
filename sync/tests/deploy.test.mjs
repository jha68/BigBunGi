import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

test("deployment cannot create resources without explicit Free-plan verification", () => {
  const run = spawnSync(
    process.execPath,
    [new URL("../deploy.mjs", import.meta.url).pathname],
    {
      env: {
        ...process.env,
        SYNC_FREE_PLAN_CONFIRMED: "",
        CLOUDFLARE_API_TOKEN: "test-only-not-a-token",
        CLOUDFLARE_ACCOUNT_ID: "test-only-not-an-account",
        SYNC_PASSWORD: "test-only-password",
      },
      encoding: "utf8",
      timeout: 5000,
    },
  );
  assert.equal(run.status, 1);
  assert.match(run.stderr, /stopped before creating resources/);
  assert.ok(!run.stderr.includes("test-only-not-a-token"));
  assert.equal(run.stdout, "");
});
