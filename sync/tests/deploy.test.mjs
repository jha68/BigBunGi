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

test("invalid password length identifies only SYNC_PASSWORD without exposing credentials or contacting Cloudflare", () => {
  for (const password of ["short-only", "x".repeat(129)]) {
    const run = spawnSync(
      process.execPath,
      [new URL("../deploy.mjs", import.meta.url).pathname],
      {
        env: {
          ...process.env,
          SYNC_FREE_PLAN_CONFIRMED: "true",
          CLOUDFLARE_API_TOKEN: "test-only-not-a-token",
          CLOUDFLARE_ACCOUNT_ID: "test-only-not-an-account",
          SYNC_PASSWORD: password,
        },
        encoding: "utf8",
        timeout: 5000,
      },
    );
    assert.equal(run.status, 1);
    assert.match(
      run.stderr,
      /::error title=Sync configuration::SYNC_PASSWORD must contain 12-128 characters/,
    );
    assert.match(run.stderr, /Cloudflare has not been contacted/);
    for (const value of [
      password,
      "test-only-not-a-token",
      "test-only-not-an-account",
    ])
      assert.ok(!run.stderr.includes(value));
    assert.equal(run.stdout, "");
  }
});

test("missing secret errors name the missing field without exposing supplied secrets", () => {
  const run = spawnSync(
    process.execPath,
    [new URL("../deploy.mjs", import.meta.url).pathname],
    {
      env: {
        ...process.env,
        SYNC_FREE_PLAN_CONFIRMED: "true",
        CLOUDFLARE_API_TOKEN: "",
        CLOUDFLARE_ACCOUNT_ID: "test-only-not-an-account",
        SYNC_PASSWORD: "test-only-password",
      },
      encoding: "utf8",
      timeout: 5000,
    },
  );
  assert.equal(run.status, 1);
  assert.match(
    run.stderr,
    /Missing repository Actions secret: CLOUDFLARE_API_TOKEN/,
  );
  assert.ok(!run.stderr.includes("test-only-password"));
  assert.ok(!run.stderr.includes("test-only-not-an-account"));
});
