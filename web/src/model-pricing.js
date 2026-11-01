import snapshot from "./gemini-prices.json" with { type: "json" };

export const pricingSource = snapshot;

export function affordableModels(models, lookup = modelPrice) {
  const maximum = (price, field) =>
    Math.max(price[field], price.longContext?.[field] ?? price[field]);
  return models
    .filter((model) => {
      const price = lookup(model.name);
      return (
        price && maximum(price, "input") < 1 && maximum(price, "output") < 1
      );
    })
    .sort((a, b) => {
      const x = lookup(a.name),
        y = lookup(b.name);
      return (
        maximum(x, "input") - maximum(y, "input") ||
        maximum(x, "output") - maximum(y, "output") ||
        a.name.localeCompare(b.name)
      );
    });
}

export function freeTierLabel(name, access) {
  const entry = access?.models?.[(name || "").replace(/^models\//, "")];
  return entry?.available === true
    ? "무료 플랜 지원"
    : entry?.available === false
      ? "유료 전용"
      : "무료 지원 미확인";
}

export function modelPrice(name) {
  const id = (name || "").replace(/^models\//, "");
  return Object.hasOwn(snapshot.models, id) ? snapshot.models[id] : null;
}

function dollars(value) {
  return (
    "$" +
    value.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 3,
    })
  );
}

function range(first, second) {
  return second == null || second === first
    ? dollars(first)
    : `${dollars(first)}–${dollars(second)}`;
}

export function modelPriceLabel(name, withUnit = false) {
  const price = modelPrice(name);
  if (!price) return "가격 확인 필요";
  return (
    `입력 ${range(price.input, price.longContext?.input)} / 출력 ${range(price.output, price.longContext?.output)}` +
    (withUnit ? " · USD/100만 토큰" : "")
  );
}

export function modelPriceDetail(name) {
  const price = modelPrice(name);
  if (!price)
    return "확인된 참고 단가가 없습니다. Google 공식 요금표를 확인해 주세요.";
  if (!price.longContext)
    return "일반 유료 텍스트 요청의 USD/100만 토큰 참고 단가입니다.";
  const tier = price.longContext;
  return `입력 ${tier.above.toLocaleString("ko-KR")}토큰 이하: 입력 ${dollars(price.input)} / 출력 ${dollars(price.output)}. 초과: 입력 ${dollars(tier.input)} / 출력 ${dollars(tier.output)}. (USD/100만 토큰)`;
}
