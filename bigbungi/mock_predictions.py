"""Deterministic practice CSVs and attainable scoring bands for work type 2."""

from textwrap import dedent

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import f1_score, mean_absolute_error, mean_squared_error
from sklearn.metrics import mean_squared_log_error, roc_auc_score

from .datasets import split_prediction
from .mock_exams import ExamQuestion, dataset


PREDICTION_TOPICS = {
    2: ("택배 정시 도착 예측", "배송 전까지 수집된 운송 정보로 정시 도착 확률을 예측하시오.",
        "on_time", "roc_auc", {"distance_km": "배송 거리(km)", "weight_kg": "화물 중량(kg)",
        "dispatch_hour": "출발 시각의 시간", "priority": "우선 배송 여부", "warehouse": "출발 물류센터"}),
    3: ("구매 확률 예측", "쇼핑몰 방문과 상품 정보로 각 방문의 구매 확률을 예측하시오.",
        "purchased", "roc_auc", {"pages": "조회한 페이지 수", "visit_minutes": "방문 지속시간(분)",
        "previous_orders": "이전 구매 횟수", "price": "상품 가격(천 원)", "channel": "방문 유입 경로"}),
    4: ("고객군 분류", "고객의 구매 이력과 인구통계 정보로 고객군을 예측하시오.",
        "segmentation", "macro_f1", {"age": "연령", "income": "연간 소득(백만 원)",
        "orders": "최근 1년 주문 건수", "household": "가구 인원", "region": "거주 권역"}),
    5: ("중고차 가격 예측", "중고차 매물의 제원과 이력으로 판매 가격을 예측하시오.",
        "price", "rmse", {"year": "출고 연도", "mileage_km": "누적 주행 거리(km)",
        "engine_cc": "배기량(cc)", "accidents": "사고 건수", "fuel": "연료 종류"}),
    6: ("설문 응답자 연령대 분류", "메타버스 서비스 설문 응답으로 연령대 구간을 분류하시오.",
        "age_group", "macro_f1", {"interest": "신규 기기 관심도(1~5)", "social": "커뮤니티 사용 빈도(1~5)",
        "game": "게임 경험 수준(1~5)", "purchase": "디지털 상품 구매 성향(1~5)", "access": "주 접속 기기"}),
    7: ("제주 여행 매출 예측", "제주 지역 여행 거래의 조건을 바탕으로 매출액을 예측하시오.",
        "amount", "rmse", {"visitors": "예약 인원", "nights": "숙박 일수",
        "rating": "상품 평점", "month": "예약월", "product": "여행 상품 종류"}),
    8: ("지하철 이용객 수 예측", "역과 시간대별 기상 조건으로 지하철 이용객 수를 예측하시오.",
        "passengers", "mae", {"hour": "관측 시간(0~23)", "weekday": "요일(월요일=0)",
        "temperature": "기온(℃)", "rain_mm": "강수량(mm)", "station": "역 코드"}),
    9: ("농업 관련 유형 분류", "지역, 농지 및 경영 정보로 농업 관련 유형을 분류하시오.",
        "category", "macro_f1", {"area": "농지 면적(아르)", "workers": "종사자 수", "years": "운영 기간(년)",
        "yield_tons": "연간 생산량(톤)", "province": "권역"}),
    10: ("건물 총난방비 예측", "건물 특성으로 연간 총난방비를 예측하시오. 학습용 총난방비가 0이면 측정 누락을 뜻한다.",
         "heating_cost", "rmse", {"area": "난방 면적(㎡)", "age": "건축물 연식(년)",
         "winter_days": "난방 필요 일수", "efficiency": "설비 효율", "insulation": "단열 수준"}),
    11: ("게임 활성화 수준 분류", "이용자의 게임 활동 이력으로 활성화 수준을 분류하시오.",
         "level", "macro_f1", {"hours": "주간 플레이 시간", "quests": "완료한 퀘스트 수",
         "win_rate": "경기 승률", "days": "최근 30일 중 접속 일수", "device": "주 이용 기기"}),
    12: ("주문 금액 예측", "주문 정보로 총 주문 금액을 예측하시오. 예측 대상과 변수는 RMSLE 실습용으로 구성했다.",
         "amount", "rmsle", {"quantity": "상품 수량", "unit_price": "단가(천 원)",
         "discount": "할인율", "order_hour": "주문 시각의 시간", "channel": "주문 채널"}),
}


def sample_prediction(round_number, rng):
    n = 1200
    integer = lambda low, high: rng.integers(low, high, n)
    uniform = lambda low, high: rng.uniform(low, high, n).round(3)
    choose = lambda options: rng.choice(options, n)
    noise = lambda scale: rng.normal(0, scale, n)
    if round_number == 2:
        distance, weight, hour, priority = uniform(3, 260), uniform(0.2, 32), integer(5, 21), integer(0, 2)
        zone = choose(["A", "B", "C"])
        target = rng.binomial(1, expit(2.9 - .021 * distance - .75 * (hour > 16) + 1.1 * priority - .09 * weight + .8 * (zone == "A")))
        return (distance, weight, hour, priority, zone), target
    if round_number == 3:
        pages, minutes, orders, price = integer(1, 30), uniform(0.2, 50), integer(0, 7), uniform(5, 180)
        channel = choose(["검색", "광고", "직접"])
        target = rng.binomial(1, expit(-2.9 + .14 * pages + .06 * minutes + .53 * orders - .026 * price + .7 * (channel == "직접")))
        return (pages, minutes, orders, price, channel), target
    if round_number == 4:
        age, income, orders, household = integer(18, 78), uniform(18, 150), integer(0, 36), integer(1, 7)
        region = choose(["수도권", "중부", "남부"])
        score = .5 * income + 1.4 * orders - .54 * age + 2 * household + 7 * (region == "수도권") + noise(8)
        return (age, income, orders, household, region), np.digitize(score, [23, 44, 66]) + 1
    if round_number == 5:
        year, mileage, engine, accident = integer(2008, 2023), integer(1200, 240000), integer(950, 4400), integer(0, 4)
        fuel = choose(["가솔린", "디젤", "하이브리드"])
        target = 4300 + (year - 2015) * 280 - .013 * mileage + .72 * engine - 410 * accident + 900 * (fuel == "하이브리드") + noise(350)
        return (year, mileage, engine, accident, fuel), np.maximum(250, target).round(2)
    if round_number == 6:
        group = integer(0, 3)
        interest = np.clip(np.rint(4.7 - group * 1.3 + noise(.8)), 1, 5)
        social = np.clip(np.rint(2.8 + (group == 1) * 1.4 + noise(.9)), 1, 5)
        game = np.clip(np.rint(4.8 - group * 1.5 + noise(1)), 1, 5)
        purchases = np.clip(np.rint(2 + group * 1.1 + noise(.9)), 1, 5)
        access = np.where(rng.random(n) < .66, np.array(["모바일", "PC", "태블릿"])[group], choose(["모바일", "PC", "태블릿"]))
        return (interest, social, game, purchases, access), group
    if round_number == 7:
        visitors, nights, rating, month = integer(1, 31), integer(1, 9), uniform(2, 5), integer(1, 13)
        product = choose(["숙박", "체험", "패키지"])
        rate = np.select([product == "숙박", product == "패키지"], [68_000, 126_000], default=34_000)
        target = 300_000 + rate * visitors * nights + 70_000 * rating + 200_000 * np.isin(month, [7, 8]) + noise(214_000)
        return (visitors, nights, rating, month, product), np.maximum(45_000, target).round(2)
    if round_number == 8:
        hour, weekday, temperature = integer(0, 24), integer(0, 7), uniform(-6, 35)
        rain = rng.gamma(.6, 7, n).round(3)
        station = choose(["A", "B"])
        peak = np.exp(-((hour - 8) / 2) ** 2) + .74 * np.exp(-((hour - 18) / 2.5) ** 2)
        target = 180 + 520 * (station == "A") + (1160 - 440 * (weekday >= 5)) * peak + 7 * temperature - 8 * rain + noise(104)
        return (hour, weekday, temperature, rain, station), np.maximum(10, target).round()
    if round_number == 9:
        area, workers, years, tons = uniform(1, 180), integer(1, 20), integer(1, 37), uniform(1, 30)
        province = choose(["수도권", "호남", "영남", "충청"])
        score = .42 * area + 4 * workers + 1.12 * tons - years + 17 * (province == "호남") + noise(10)
        return (area, workers, years, tons, province), np.digitize(score, [100, 137])
    if round_number == 10:
        area, age, days, efficiency = uniform(35, 280), integer(0, 44), integer(80, 185), uniform(.55, .96)
        insulation = choose(["우수", "보통", "낮음"])
        target = 240 + .021 * area * days / efficiency + age * 10 + 290 * (insulation == "낮음") + noise(85)
        return (area, age, days, efficiency, insulation), np.maximum(60, target).round(2)
    if round_number == 11:
        hours, quests, win, days = uniform(0, 45), integer(0, 45), uniform(.14, .9), integer(1, 31)
        device = choose(["모바일", "PC", "콘솔"])
        score = .82 * hours + 1.13 * quests + 22 * win + .8 * days + 9 * (device == "PC") + noise(10)
        return (hours, quests, win, days, device), np.digitize(score, [60, 85])
    quantity, price, discount, hour = integer(1, 25), uniform(1, 75), uniform(0, .48), integer(0, 24)
    channel = choose(["매장", "앱", "웹"])
    target = quantity * price * (1 - discount) * np.exp(noise(.24)) + 6 + 35 * (channel == "매장")
    return (quantity, price, discount, hour, channel), target.round(2)


def evaluate(metric, truth, predicted):
    if metric == "roc_auc":
        return roc_auc_score(truth, predicted)
    if metric == "macro_f1":
        return f1_score(truth, predicted, average="macro")
    if metric == "mae":
        return mean_absolute_error(truth, predicted)
    if metric == "rmsle":
        return mean_squared_log_error(truth, predicted) ** .5
    return mean_squared_error(truth, predicted) ** .5


def prediction(round_number, rng):
    title, scenario, target, metric, columns = PREDICTION_TOPICS[round_number]
    features, values = sample_prediction(round_number, rng)
    frame = pd.DataFrame(dict(zip(columns, features)))
    frame.insert(0, "id", np.arange(1, len(frame) + 1))
    higher = metric in ("roc_auc", "macro_f1")
    pid = f"mock-{round_number}"
    datasets, private = {}, {}
    split_prediction(pid, frame, values, target, datasets, private, classification=higher)
    train, test = datasets[pid]["train"], datasets[pid]["test"]
    if round_number == 10:
        train.loc[rng.choice(train.index, 30, replace=False), target] = 0
        fit_train = train[train[target] != 0]
    else:
        fit_train = train
    combined = pd.get_dummies(pd.concat([fit_train[list(columns)], test[list(columns)]], ignore_index=True))
    model_type = RandomForestClassifier if higher else RandomForestRegressor
    model = model_type(n_estimators=100, random_state=42, n_jobs=1)
    model.fit(combined.iloc[:len(fit_train)], fit_train[target])
    evaluation = combined.iloc[len(fit_train):]
    predict_code = "model.predict_proba(x_test)[:, 1]" if metric == "roc_auc" else "model.predict(x_test)"
    results = model.predict_proba(evaluation)[:, 1] if metric == "roc_auc" else model.predict(evaluation)
    truth = private[pid]["y"]
    if metric == "roc_auc":
        constant = .5
    elif metric == "macro_f1":
        constant = int(fit_train[target].mode().iloc[0])
    elif metric == "mae":
        constant = float(fit_train[target].median())
    elif metric == "rmsle":
        constant = float(np.expm1(np.log1p(fit_train[target]).mean()))
    else:
        constant = float(fit_train[target].mean())
    baseline = float(evaluate(metric, truth, np.full(len(truth), constant)))
    reference = float(evaluate(metric, truth, results))
    if not (reference > baseline if higher else reference < baseline):
        raise ValueError(f"Reference model for round {round_number} must improve the baseline")
    spec = {
        "target": target, "prediction": "pred", "filename": "result.csv",
        "ordered": True, "metric": metric, "higher": higher, "scale": 100,
        "baseline": baseline, "threshold": baseline + .78 * (reference - baseline),
        **private[pid],
    }
    if metric == "macro_f1":
        spec["labels"] = sorted(np.unique(values).tolist())
    description = {"id": "레코드 번호. 모델 학습에서 제외", **columns}
    classes = ", ".join(str(label) for label in spec.get("labels", []))
    target_description = {
        "roc_auc": "실제 결과(0=아니요, 1=예)",
        "macro_f1": f"실제 분류값({classes})",
    }.get(metric, "실제 연속형 값")
    submission_format = {
        "roc_auc": "0에서 1 사이의 양성 확률을 기록하시오.",
        "macro_f1": f"예측 클래스 {classes} 중 하나를 기록하시오.",
        "rmsle": "0 이상의 예측값을 기록하시오.",
    }.get(metric, "예측한 수치를 기록하시오.")
    files = [dataset("train", train, {**description, target: target_description}),
             dataset("test", test, description)]
    public = {
        "type": 2, "title": title, "scenario": scenario, "points": 40, "recalled": True,
        "files": files, "fields": [],
        "steps": [
            f"data/train.csv에는 정답 열 {target}이 있다. data/test.csv의 각 행을 예측하시오.",
            f"평가 지표는 {metric.upper()}이다. {submission_format}",
            "평가 데이터의 행 순서대로 pred 열 한 개만 만들고, 인덱스를 제외해 result.csv로 저장하시오.",
        ],
        "submission": {key: spec[key] for key in ("filename", "prediction", "metric")},
    }
    drop_zero = f'train = train[train["{target}"] != 0]\n' if round_number == 10 else ""
    spec["code"] = dedent(f'''
        import pandas as pd
        from sklearn.ensemble import {model_type.__name__}

        train = pd.read_csv("data/train.csv")
        test = pd.read_csv("data/test.csv")
        {{filter}}features = test.columns.drop("id")
        encoded = pd.get_dummies(pd.concat([train[features], test[features]], ignore_index=True))
        x_train = encoded.iloc[:len(train)]
        x_test = encoded.iloc[len(train):]

        model = {model_type.__name__}(n_estimators=100, random_state=42, n_jobs=1)
        model.fit(x_train, train["{target}"])
        predictions = {predict_code}
        pd.DataFrame({{"pred": predictions}}).to_csv("result.csv", index=False)
    ''').strip().replace("{filter}", drop_zero) + "\n"
    return ExamQuestion(public, {"train.csv": train, "test.csv": test}, spec)
