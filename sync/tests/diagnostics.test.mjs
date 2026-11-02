import { test } from "node:test";
import assert from "node:assert/strict";
import {
  safeDiagnostic,
  errorAnnotation,
  commandFailure,
} from "../diagnostics.mjs";

test("deployment diagnostics redact secrets and hashes before truncation or logging", () => {
  const secrets = [
    "fake-account-identifier",
    "fake-token-value",
    "fake-password-value",
  ];
  const hash = "pbkdf2-100000:" + "a".repeat(32) + ":" + "b".repeat(64);
  const input =
    "\u001b[31mERROR\u001b[0m auth " + secrets.join(" ") + " " + hash;
  const result = safeDiagnostic(input, secrets);
  for (const value of [...secrets, hash]) assert.ok(!result.includes(value));
  assert.ok(!result.includes("\u001b"));
  assert.ok(result.includes("ERROR auth"));
  const annotation = errorAnnotation("x".repeat(1990) + secrets[1], secrets);
  assert.ok(!annotation.includes("fake-token"));
});
test("multiline errors become a single safe Actions annotation with the actionable CLI cause", () => {
  const failure = commandFailure(
    "d1",
    "Wrangler log",
    "ERROR D1 access denied [code: 10000]\npermission required",
  );
  const result = errorAnnotation(failure + "\n::notice::test 100%", []);
  assert.match(
    result,
    /^::error title=Cloudflare sync deployment::Cloudflare d1 failed:/,
  );
  assert.ok(result.includes("code: 10000"));
  assert.ok(result.includes("%0A"));
  assert.ok(result.includes("100%25"));
  assert.equal(result.split("\n").length, 1);
});
