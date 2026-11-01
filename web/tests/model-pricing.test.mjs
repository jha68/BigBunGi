import { test } from "node:test";
import assert from "node:assert/strict";
import {
  modelPrice,
  modelPriceLabel,
  modelPriceDetail,
  pricingSource,
} from "../src/model-pricing.js";

test("prices show input/output separately in USD per million tokens", () => {
  assert.equal(
    modelPriceLabel("models/gemini-2.5-flash", true),
    "입력 $0.30 / 출력 $2.50 · USD/100만 토큰",
  );
  assert.deepEqual(modelPrice("models/gemini-flash-latest"), {
    input: 0.75,
    output: 3.75,
  });
  assert.equal(pricingSource.tokensPerUnit, 1_000_000);
  assert.equal(pricingSource.currency, "USD");
});

test("long-context rates display both tiers rather than advertising only the lower rate", () => {
  const label = modelPriceLabel("models/gemini-2.5-pro");
  for (const amount of ["$1.25", "$2.50", "$10.00", "$15.00"])
    assert.ok(label.includes(amount));
  const detail = modelPriceDetail("models/gemini-2.5-pro");
  assert.ok(detail.includes("200,000"));
  assert.ok(detail.includes("초과"));
});

test("unpriced IDs and aliases are never guessed or presented as free", () => {
  for (const name of [
    "models/gemini-unreleased",
    "models/gemini-2.5-flash-unknown",
    "constructor",
    "",
  ]) {
    assert.equal(modelPrice(name), null);
    assert.equal(modelPriceLabel(name), "가격 확인 필요");
  }
});

test("pricing snapshot has traceable provenance and valid amounts", () => {
  assert.match(
    pricingSource.sourceUrl,
    /github.com\/BerriAI\/litellm\/blob\/[a-f0-9]{40}\//,
  );
  assert.equal(
    pricingSource.officialUrl,
    "https://ai.google.dev/gemini-api/docs/pricing",
  );
  assert.match(pricingSource.retrievedAt, /^\d{4}-\d{2}-\d{2}$/);
  for (const price of Object.values(pricingSource.models)) {
    assert.ok(Number.isFinite(price.input) && price.input > 0);
    assert.ok(Number.isFinite(price.output) && price.output > 0);
    if (price.longContext) {
      assert.ok(price.longContext.above > 0);
      assert.ok(price.longContext.input >= price.input);
      assert.ok(price.longContext.output >= price.output);
    }
  }
});
