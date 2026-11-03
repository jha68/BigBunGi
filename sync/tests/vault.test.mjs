import { test } from "node:test";
import assert from "node:assert/strict";
import { encryptSettings, decryptSettings } from "../worker.js";

test("vault requires the same password-derived server secret and authenticates its ciphertext", async () => {
  const settings = { apiKey: "test-only-key", model: "models/gemini-test" };
  const secret = "test-only-password-derived-secret";
  const a = await encryptSettings(settings, secret),
    b = await encryptSettings(settings, secret);
  assert.notEqual(a, b);
  assert.deepEqual(await decryptSettings(a, secret), settings);
  await assert.rejects(() => decryptSettings(a, secret + "-rotated"));
  const record = JSON.parse(a);
  record.iv = "0".repeat(24);
  await assert.rejects(() => decryptSettings(JSON.stringify(record), secret));
});

test("conversation encryption is bound to its problem and independent of the login password", async () => {
  const stableHistorySecret = "a".repeat(64),
    turns = [{ question: "test", answer: "sample" }];
  const encrypted = await encryptSettings(
    turns,
    stableHistorySecret,
    "conversations/t1-01",
  );
  assert.deepEqual(
    await decryptSettings(
      encrypted,
      stableHistorySecret,
      "conversations/t1-01",
    ),
    turns,
  );
  await assert.rejects(() =>
    decryptSettings(encrypted, stableHistorySecret, "conversations/t1-02"),
  );
  await assert.rejects(() =>
    decryptSettings(
      encrypted,
      "different-password-hash",
      "conversations/t1-01",
    ),
  );
});
