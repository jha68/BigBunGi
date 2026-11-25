"""Original wording and generated data based on each round's published recollections."""

import numpy as np
import pandas as pd

from .mock_exams import field, numeric


SHORT_QUESTIONS = {
    2: [
        ("다른 관측치의 전반적인 분포에서 크게 벗어난 관측값을 무엇이라 하는가?",
         ["이상치", "이상값", "outlier"], True),
        ("훈련 오차는 낮지만 새로운 데이터에서 성능이 급격히 낮아지는 현상을 쓰시오.",
         ["과적합", "overfitting"], True),
        ("분석에 사용하는 연속형 변수의 빈칸을 관측된 값들의 산술평균으로 채우는 방법을 쓰시오.",
         ["평균 대치", "평균값 대치", "평균 대체", "mean imputation"], True),
        ("변수 없이 시작해 기준을 가장 크게 개선하는 변수를 하나씩 추가하는 회귀 변수 선택법은?",
         ["전진 선택법", "전진선택", "forward selection"], True),
        ("이전 약한 분류기가 놓친 관측치의 가중치를 높이면서 새 분류기를 학습하는 대표적인 부스팅 알고리즘을 쓰시오.",
         ["AdaBoost", "adaptive boosting", "아다부스트"], True),
        ("이전 모형의 손실함수 음의 기울기를 다음 약한 학습기로 근사하는 부스팅 모형의 이름을 쓰시오.",
         ["그래디언트 부스팅", "경사 부스팅", "gradient boosting", "GBM", "gradient boosting machine"], True),
        ("분류 임곗값을 바꾸어 가며 거짓 양성 비율과 참 양성 비율을 나타낸 곡선을 쓰시오.",
         ["ROC", "ROC 곡선", "ROC curve"], True),
        ("레이블 없이 관측치의 구조나 군집을 탐색하는 학습 방식을 쓰시오.",
         ["비지도 학습", "unsupervised learning"], True),
        ("은닉층 출력이 0.3, 0.8이고 다음 노드의 연결 가중치는 각각 0.4, −0.3이다. 편향 0.2를 더한 뒤 ReLU를 적용한 출력값을 쓰시오.",
         ["0.08", ".08", "0.080"], True),
        ("모형 선택이 끝난 뒤 일반화 성능을 최종 평가하기 위해 따로 분리해 두는 데이터는?",
         ["테스트 데이터", "시험 데이터", "평가용 데이터", "test set", "test data"], False),
    ],
    3: [
        ("연관규칙에서 두 사건이 동시에 일어날 확률을 각 사건 발생확률의 곱으로 나눈 지표는?",
         ["향상도", "향상성", "lift"], True),
        ("최솟값과 최댓값만으로 범위를 변환할 때, 분포의 흩어진 정도를 나타내는 어떤 특성을 직접 사용하지 않는가? 제곱 편차의 평균으로 정의되는 값을 쓰시오.",
         ["분산", "variance"], True),
        ("k-NN이 새 관측치와 학습 관측치 사이의 가까움을 비교하는 데 사용하는 값은?",
         ["거리", "distance"], True),
        ("계층적 군집화에서 각 군집의 평균 좌표를 계산해 두 군집 사이의 거리를 판단하는 연결법은?",
         ["중심 연결법", "중심연결", "centroid linkage"], True),
        ("각 열의 최솟값을 0, 최댓값을 1로 대응시키는 데이터 변환 방식은?",
         ["최소 최대 정규화", "최소 최대 스케일링", "min max scaling", "min max normalization", "minmax"], True),
        ("일별 시계열의 간격을 월 단위로 바꿔 월별 합계를 구하는 작업을 무엇이라 하는가?",
         ["리샘플링", "resampling", "다운샘플링", "월별 집계", "재표본화"], True),
        ("대소 관계가 없는 국가 코드는 어떤 척도로 측정한 변수인가?",
         ["명목 척도", "명목형", "명목 변수", "nominal"], True),
        ("여러 분류기의 예측을 다수결로 합쳐 최종 클래스를 결정하는 기법의 이름은?",
         ["보팅", "투표", "voting", "다수결 투표", "하드 보팅", "hard voting"], True),
        ("은닉층의 두 출력 0.6, 0.2에 각각 가중치 0.4, −0.2를 곱하고 편향 0.1을 더한 선형합은?",
         ["0.3", ".3", "0.30"], True),
        ("결정 경계와 가장 가까운 표본 사이의 간격을 최대화하는 대표적인 지도학습 알고리즘은?",
         ["SVM", "서포트 벡터 머신", "지원 벡터 머신", "support vector machine"], True),
    ],
    4: [
        ("키와 값으로 구성된 객체를 중괄호로 나타내며 배열을 지원하는 텍스트 데이터 형식은?",
         ["JSON", "JavaScript Object Notation"], True),
        ("관측값과 예측값 사이 잔차의 제곱합을 최소화하는 회귀계수 추정법은?",
         ["최소제곱법", "최소자승법", "OLS", "least squares", "ordinary least squares"], True),
        ("양수 관측값의 왜도를 완화하기 위해 모수 λ를 정해 사용하는 대표적인 거듭제곱 변환은?",
         ["박스콕스", "박스콕스 변환", "Box Cox", "Box Cox 변환"], True),
        ("가능한 한 많은 정보를 유지하면서 변수 개수를 줄이는 기법들을 통칭하는 말은?",
         ["차원 축소", "dimensionality reduction", "dimension reduction"], True),
        ("고차원 자료의 이웃 관계를 보존하도록 경쟁학습으로 2차원 격자에 투영하는 신경망은?",
         ["자기조직화지도", "자기조직화 맵", "SOM", "self organizing map"], True),
        ("정규분포를 따른다는 모집단 가정을 무엇이라 하는가?",
         ["정규성", "normality"], True),
        ("마진을 최대화하는 분류 경계를 구하며 커널로 비선형 경계를 만들 수도 있는 모형은?",
         ["SVM", "서포트 벡터 머신", "지원 벡터 머신", "support vector machine"], True),
        ("신경망 훈련 중 일부 뉴런의 출력을 무작위로 0으로 만드는 정규화 방법은?",
         ["드롭아웃", "dropout"], True),
        ("관계형 데이터베이스와 Hadoop 사이의 대량 전송에 사용되던 Apache 도구의 이름은?",
         ["스쿱", "Sqoop", "Apache Sqoop"], True),
        ("이진 분류의 TP가 24, FP가 8, FN이 16일 때 F1 점수를 소수 셋째 자리까지 반올림하여 쓰시오.",
         ["0.667", ".667"], True),
    ],
    5: [
        ("대규모 분산 처리에서 먼저 키별 값을 만든 뒤 같은 키의 값을 모아 계산하는 두 단계 방식은?",
         ["맵리듀스", "MapReduce"], True),
        ("JSON처럼 데이터 안에 구조를 설명하는 정보는 있으나 고정된 표의 스키마를 요구하지 않는 형식은?",
         ["반정형 데이터", "반정형", "semi structured data"], True),
        ("불균형 분류에서 소수 클래스 표본을 늘려 학습 데이터의 비율을 보정하는 방법은?",
         ["오버샘플링", "과대표집", "과대 표본추출", "oversampling"], True),
        ("민감한 값의 일부를 가림 문자 등으로 바꿔 식별 위험을 낮추는 기법은?",
         ["데이터 마스킹", "마스킹", "data masking"], True),
        ("실제값이 21, 28, 39, 52이고 예측값은 20, 30, 40, 50이다. RMSE를 소수 셋째 자리까지 반올림해 쓰시오.",
         ["1.581", "1.5810"], True),
        ("입력이 음수일 때도 0보다 큰 작은 기울기를 유지해 ReLU의 비활성화 문제를 완화하는 함수는?",
         ["Leaky ReLU", "리키 렐루"], True),
        ("시계열에서 단기 변동을 완화해 기저 흐름을 알아보기 위한 일반적인 처리는?",
         ["평활화", "smoothing"], True),
        ("ε-이웃의 밀도를 기준으로 서로 연결된 관측치를 군집화하고 희박한 점은 잡음으로 분류하는 알고리즘은?",
         ["DBSCAN"], True),
        ("3시그마 규칙에서 관측값을 이상치로 판단하는 표준점수 절댓값 경계는?",
         ["3", "3.0"], True),
        ("TP가 30, FP가 15, FN이 25다. F1 점수를 소수 첫째 자리까지 반올림하여 쓰시오.",
         ["0.6", ".6", "0.60"], True),
    ],
}


def round_two(rng):
    n = 350
    scores = pd.DataFrame({"age": rng.integers(19, 93, n), "score": rng.normal(63, 9, n).round(4)})
    income = rng.lognormal(8, .43, 480).round(2)
    income[rng.choice(len(income), 64, replace=False)] = np.nan
    delivery = rng.normal(35, 7, 520).round(3)
    large = rng.choice(len(delivery), 24, replace=False)
    delivery[large] += rng.uniform(12, 30, len(large))
    return [
        numeric(1, "상위 점수 보정 후 평균", "고객별 나이와 점수가 주어져 있다.",
            "customer_scores", scores, {"age": "만 나이", "score": "고객 점수"}, '''
            top = df["score"].nlargest(10)
            df.loc[top.index, "score"] = top.iloc[-1]
            ''', [field("평균 점수", "score 상위 10개 행의 값을 10번째로 큰 점수로 대체하시오. 그 다음 만 80세 이상인 고객의 보정된 점수 평균을 구하시오.", 'df.loc[df["age"] >= 80, "score"].mean()')]),
        numeric(1, "결측치 대체와 표준편차", "소득 자료의 행 순서는 CSV에 기록된 순서를 따른다.",
            "income", pd.DataFrame({"income": income}), {"income": "소득(천 원)"}, '''
            x = df["income"].iloc[:int(len(df) * .7)]
            filled = x.fillna(x.median())
            ''', [field("표준편차의 차이", "첫 70%에 해당하는 행(행 수는 내림)을 사용한다. 해당 구간의 중앙값으로 결측을 채우기 전의 표본표준편차에서 채운 뒤의 표본표준편차를 빼시오.", "x.std() - filled.std()")]),
        numeric(1, "배달시간 이상치 합계", "배달 소요 시간이 분 단위로 주어져 있다.",
            "delivery_minutes", pd.DataFrame({"minutes": delivery}), {"minutes": "배달 소요 시간"}, '''
            x = df["minutes"]
            boundary = x.mean() + 1.5 * x.std()
            ''', [field("이상치의 합", "전체 표본의 평균보다 표본표준편차의 1.5배를 더한 경계를 구하시오. 그 경계를 초과하는 minutes 값의 합계를 구하시오.", "x[x > boundary].sum()")]),
    ]


def round_three(rng):
    sales = rng.integers(2, 280, 420).astype(float)
    sales[rng.choice(len(sales), 22, replace=False)] = np.nan
    rate = pd.DataFrame({"year": np.repeat([1999, 2000, 2001, 2002], 35),
                         "country": np.tile(np.arange(1, 36), 4),
                         "prevalence": rng.gamma(3, 25, 140).round(3)})
    quality = pd.DataFrame(rng.normal(30, 4, (230, 4)).round(4), columns=["length", "width", "height", "weight"])
    for column, missing in zip(quality, [10, 32, 8, 18]):
        quality.loc[rng.choice(quality.index, missing, replace=False), column] = np.nan
    return [
        numeric(1, "완전한 행의 제1사분위수", "판매 실적과 방문 건수 데이터다.",
            "sales", pd.DataFrame({"sales": sales, "visits": rng.integers(1, 150, len(sales))}),
            {"sales": "판매 수량", "visits": "방문 건수"}, '''
            complete = df.dropna()
            sample = complete.iloc[:int(len(complete) * .7)]
            ''', [field("제1사분위수", "결측치가 있는 행을 제거하고 남은 행을 기존 순서대로 앞에서부터 70%만 사용하시오. 행 수는 내림한다. sample의 sales 제1사분위수를 선형 보간으로 구하시오.", 'sample["sales"].quantile(.25)')]),
        numeric(1, "결핵 유병률의 국가별 비교", "특정 연도의 국가별 결핵 유병률을 비교한다.",
            "tuberculosis", rate, {"year": "관측 연도", "country": "국가 번호", "prevalence": "10만 명당 유병자 수"}, '''
            values = df.loc[df["year"] == 2000, "prevalence"]
            ''', [field("국가 수", "2000년 유병률을 기준으로, 해당 연도 국가 평균보다 유병률이 높은 국가 수를 구하시오.", "(values > values.mean()).sum()", 0)]),
        numeric(1, "결측 비율이 가장 높은 열", "제품 형태 측정에서 일부 값이 누락됐다.",
            "quality", quality, {"length": "길이", "width": "너비", "height": "높이", "weight": "무게"},
            "missing = df.isna().mean()",
            [field("열 이름", "각 변수의 결측 비율을 계산하시오. 비율이 가장 높은 열의 이름을 CSV에 적힌 그대로 입력하시오.", "missing.idxmax()", None)]),
    ]


def round_four(rng):
    n = 540
    total = rng.integers(100, 2000, n)
    shares = rng.multinomial(100, [.23, .23, .54], n) / 100
    views = pd.DataFrame({
        "total_views": total, "group_a": (total * shares[:, 0]).astype(int),
        "group_b": (total * shares[:, 1]).astype(int),
        "format": rng.choice(["video", "text", "image"], n),
    })
    shows = pd.DataFrame({
        "added_on": (pd.Timestamp("2017-12-01") + pd.to_timedelta(rng.integers(0, 120, n), unit="D")).strftime("%B %d, %Y"),
        "country": rng.choice(["United Kingdom", "United States", "France", "United Kingdom, France"], n),
    })
    return [
        numeric(1, "사분위범위의 정수 부분", "한 표본의 수치 관측값이 주어져 있다.",
            "measurements", pd.DataFrame({"value": rng.normal(90, 28, n).round(4)}),
            {"value": "수치 관측값"}, 'low, high = df["value"].quantile([.25, .75])',
            [field("사분위범위", "선형 보간을 사용하여 value의 제1사분위수와 제3사분위수를 구한다. 제3사분위수에서 제1사분위수를 뺀 뒤 소수 부분을 버리시오.", "high - low", 0)]),
        numeric(1, "영상 콘텐츠 조회 조건", "전체 조회수와 두 사용자 그룹 조회수가 제공된다.",
            "content_views", views, {"total_views": "전체 조회수", "group_a": "A그룹 조회수", "group_b": "B그룹 조회수", "format": "콘텐츠 형식"},
            'ratio = (df["group_a"] + df["group_b"]) / df["total_views"]',
            [field("해당 영상 수", "A·B 그룹 합산 조회수가 전체에서 차지하는 비율이 0.4보다 크고 0.5보다 작은 video 콘텐츠 수를 구하시오.", '((ratio > .4) & (ratio < .5) & df["format"].eq("video")).sum()', 0)]),
        numeric(1, "2018년 1월 영국 콘텐츠", "동영상 서비스에 추가된 콘텐츠 이력이다. 공동 제작 국가는 쉼표로 나열되어 있다.",
            "streaming", shows, {"added_on": "서비스에 추가된 날짜", "country": "제작 국가"},
            'dates = pd.to_datetime(df["added_on"], format="%B %d, %Y")',
            [field("해당 콘텐츠 건수", "2018년 1월에 추가된 콘텐츠 중 제작 국가가 영국(United Kingdom) 단독인 건수를 구하시오.", '((dates.dt.year == 2018) & (dates.dt.month == 1) & df["country"].eq("United Kingdom")).sum()', 0)]),
    ]


def round_five(rng):
    n = 520
    bags = pd.DataFrame({
        "kind": rng.choice(["규격봉투", "특수봉투"], n), "usage": rng.choice(["음식물쓰레기", "생활쓰레기"], n),
        "price_2l": rng.choice([0, 100, 120, 130, 150, 180, 200], n),
    })
    bodies = pd.DataFrame({"height_cm": rng.normal(166, 9, n).round(2), "weight_kg": rng.normal(65, 11, n).round(2)})
    schools = pd.DataFrame({
        "school_id": np.arange(1, n + 1), "transfer_in": rng.integers(0, 94, n),
        "transfer_out": rng.integers(0, 75, n), "student_count": rng.integers(80, 760, n),
    })
    return [
        numeric(1, "2L 음식물 쓰레기봉투 가격", "종량제봉투의 종류와 용도, 2L 판매 가격이 담겨 있다.",
            "trash_bag_price", bags, {"kind": "봉투 종류", "usage": "봉투 용도", "price_2l": "2L 판매가(원), 0은 미판매"}, '''
            valid = df[df["kind"].eq("규격봉투") & df["usage"].eq("음식물쓰레기") & df["price_2l"].gt(0)]
            ''', [field("평균 가격", "음식물쓰레기용 규격봉투 가운데 2L 가격이 0원이 아닌 행의 평균 2L 가격을 계산하고 가장 가까운 정수로 반올림하시오.", 'round(valid["price_2l"].mean())', 0)]),
        numeric(1, "BMI 정상과 과체중 인원", "키와 몸무게를 이용해 BMI를 계산한다.",
            "body", bodies, {"height_cm": "키(cm)", "weight_kg": "몸무게(kg)"},
            'bmi = df["weight_kg"] / (df["height_cm"] / 100) ** 2',
            [field("인원 차이", "BMI = 체중(kg) ÷ 키(m)²이다. 정상은 18.5 이상 23 미만, 과체중은 23 이상 25 미만이다. 두 집단 인원 차이의 절댓값을 구하시오.", "abs(bmi.between(18.5, 23, inclusive='left').sum() - bmi.between(23, 25, inclusive='left').sum())", 0)]),
        numeric(1, "순전입 학생 수 최대 학교", "학교별 전입·전출 현황과 전체 재학생 수가 있다.",
            "school_transfers", schools, {"school_id": "학교 번호", "transfer_in": "전입 학생 수", "transfer_out": "전출 학생 수", "student_count": "전체 재학생 수"}, '''
            net = df["transfer_in"] - df["transfer_out"]
            top = df.loc[net.eq(net.max())].sort_values("school_id").iloc[0]
            ''', [field("해당 학교 재학생 수", "전입에서 전출을 뺀 순전입 학생 수가 가장 많은 학교의 전체 재학생 수를 구하시오. 동점이면 학교 번호가 작은 학교를 고르시오.", 'top["student_count"]', 0)]),
    ]


def regression_frame(rng, n, features, target, coefficients, intercept, noise):
    inputs = {name: rng.uniform(low, high, n).round(4) for name, (low, high) in features.items()}
    frame = pd.DataFrame(inputs)
    frame[target] = (intercept + frame.to_numpy() @ coefficients + rng.normal(0, noise, n)).round(4)
    return frame


def emails(rng, n):
    words = np.array("보고서 확인 신청 할인 무료 특가 재고 회의 내일 자료 전달 수정 안내 상품".split())
    data = []
    for label, mean in (("ham", 13), ("spam", 8)):
        data.extend((label, " ".join(rng.choice(words, length))) for length in rng.poisson(mean, n) + 1)
    return pd.DataFrame(data, columns=["label", "body"]).sample(frac=1, random_state=42)


def round_six(rng):
    n = 420
    calls = pd.Timestamp("2023-02-01") + pd.to_timedelta(rng.integers(0, 28 * 24 * 60, n), unit="m")
    fire = pd.DataFrame({
        "station": rng.integers(1, 18, n), "reported_at": calls,
        "dispatched_at": calls + pd.to_timedelta(rng.integers(15, 780, n), unit="s"),
    })
    schools = pd.DataFrame({"school_id": np.arange(1, 58), "teachers": rng.integers(11, 52, 57),
                            "students": rng.integers(180, 950, 57)})
    crime = pd.DataFrame([(year, month, *rng.integers(6, 81, 3)) for year in range(2003, 2023)
                          for month in range(1, 13)], columns=["year", "month", "theft", "assault", "fraud"])
    first = [
        numeric(1, "소방서 출동 소요 시간", "각 행은 한 번의 신고와 출동 기록이다.",
            "fire_dispatch", fire, {"station": "소방서 번호", "reported_at": "신고 시각", "dispatched_at": "출동 시각"}, '''
            minutes = (pd.to_datetime(df["dispatched_at"]) - pd.to_datetime(df["reported_at"])).dt.total_seconds() / 60
            averages = minutes.groupby(df["station"]).mean()
            ''', [field("가장 긴 평균 소요 시간(분)", "출동 시각에서 신고 시각을 뺀 값을 분으로 바꿔 소방서별 평균을 구하시오. 가장 큰 평균을 정수로 반올림하시오.", "round(averages.max())", 0)]),
        numeric(1, "교사 한 명당 학생 수", "학교별 교사와 학생 수가 주어져 있다.",
            "schools", schools, {"school_id": "학교 번호", "teachers": "교사 수", "students": "학생 수"}, '''
            ratio = df["students"] / df["teachers"]
            top = df.loc[ratio.eq(ratio.max())].sort_values("school_id").iloc[0]
            ''', [field("해당 학교 교사 수", "교사 1명당 학생 수가 가장 큰 학교의 교사 수를 구하시오. 비율이 같으면 학교 번호가 작은 곳을 택하시오.", 'top["teachers"]', 0)]),
        numeric(1, "연평균 월 범죄 건수", "월별 세 가지 범죄의 발생 건수를 집계한다.",
            "monthly_crime", crime, {"year": "연도", "month": "월", "theft": "절도 건수", "assault": "폭행 건수", "fraud": "사기 건수"}, '''
            monthly = df[["theft", "assault", "fraud"]].sum(axis=1)
            by_year = monthly.groupby(df["year"]).mean()
            ''', [field("가장 큰 월평균", "세 범죄의 건수를 더해 월별 총건수를 구한 뒤 연도별 월평균을 계산하시오. 가장 큰 연도의 월평균을 구하시오.", "by_year.max()")]),
    ]
    outcomes = pd.DataFrame({"choice": rng.choice([1, 2, 3, 4], 330, p=[.22, .29, .3, .19])})
    sales = regression_frame(rng, 340, {"temperature": (9, 35), "visitors": (50, 300),
                                       "ad_spend": (3, 45)}, "sales", [1.8, .84, 2.7], 65, 22)
    third = [
        numeric(3, "선호 유형의 적합도 검정", "표본에서 선택지 1~4의 응답 비율이 각각 25%인지 검정한다.",
            "preferences", outcomes, {"choice": "응답 선택지"}, '''
            from scipy.stats import chisquare
            counts = df["choice"].value_counts().reindex([1, 2, 3, 4], fill_value=0)
            expected = len(df) / 4
            test = chisquare(counts)
            ''', [
                field("선택지별 기대도수", "귀무가설 아래 각 선택지의 기대도수를 구하시오.", "expected", 2),
                field("카이제곱 통계량", "관측도수를 이용해 카이제곱 적합도 검정통계량을 구하시오.", "test.statistic"),
                field("p값", "위 검정통계량의 p값을 구하시오.", "test.pvalue", 4),
            ]),
        numeric(3, "다중선형회귀의 계수와 구간", "세 설명변수로 sales를 설명하는 절편 포함 OLS 모형을 적합한다.",
            "daily_sales", sales, {"temperature": "기온", "visitors": "방문객 수", "ad_spend": "광고비", "sales": "일 판매액"}, '''
            import statsmodels.formula.api as smf
            model = smf.ols("sales ~ temperature + visitors + ad_spend", data=df).fit()
            ''', [
                field("광고비 회귀계수", "ad_spend의 회귀계수를 구하시오.", 'model.params["ad_spend"]'),
                field("기온 계수의 p값", "temperature 계수가 0이라는 양측 검정의 p값을 구하시오.", 'model.pvalues["temperature"]', 4),
                field("광고비 계수의 95% 하한", "ad_spend 계수의 95% 양측 신뢰구간 하한을 구하시오.", 'model.conf_int().loc["ad_spend", 0]'),
            ]),
    ]
    return first, third


def round_seven(rng):
    n = 430
    score = pd.DataFrame({"subject": rng.choice(["통계", "프로그래밍", "데이터베이스"], n, p=[.45, .31, .24]),
                          "score": rng.normal(64, 13, n).round(3)})
    score.loc[rng.choice(score.index, 26, replace=False), "score"] = np.nan
    x = rng.normal(17, 3, n)
    corr = pd.DataFrame({"measure": x, "x1": .54 * x + rng.normal(3, 1.1, n),
                         "x2": -.2 * x + rng.normal(2, 2.5, n), "x3": rng.normal(6, 1.7, n)})
    value = rng.normal(64, 12, n)
    value[rng.choice(n, 25, replace=False)] += 80
    first = [
        numeric(1, "수강 인원 1위 과목의 표준점수", "한 학생이 한 과목을 수강하면 한 행으로 기록한다.",
            "course_scores", score, {"subject": "과목명", "score": "취득 점수"}, '''
            complete = df.dropna(subset=["score"])
            subject = complete["subject"].value_counts().idxmax()
            values = complete.loc[complete["subject"].eq(subject), "score"]
            ''', [field("표준점수 최댓값", "점수가 결측인 행을 제거하고 수강 인원이 가장 많은 과목을 고르시오. 그 과목의 평균과 모집단 표준편차로 과목 내 점수를 표준화한 뒤 최댓값을 구하시오.", "((values - values.mean()) / values.std(ddof=0)).max()")]),
        numeric(1, "상관계수가 가장 큰 변수", "measure와 세 개의 수치형 측정 변수가 주어져 있다.",
            "correlations", corr, {"measure": "기준 변수", "x1": "측정 A", "x2": "측정 B", "x3": "측정 C"}, '''
            correlations = df.corr(method="pearson")["measure"].drop("measure")
            ''', [field("해당 열의 평균", "measure와 피어슨 상관계수가 가장 큰 열을 찾아 해당 열의 평균을 구하시오. 상관계수는 부호를 유지해 비교한다.", "df[correlations.idxmax()].mean()")]),
        numeric(1, "사분위범위 이상치 개수", "물류 측정값에 극단값이 포함돼 있다.",
            "measurements", pd.DataFrame({"value": value}), {"value": "측정값"}, '''
            x = df["value"]
            q1, q3 = x.quantile([.25, .75])
            iqr = q3 - q1
            ''', [field("이상치 개수", "value 중 Q1−1.5×IQR보다 작거나 Q3+1.5×IQR보다 큰 관측값의 개수를 구하시오.", "((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum()", 0)]),
    ]
    shells = regression_frame(rng, 300, {"length": (5, 16), "width": (3, 7), "height": (1, 4)},
                              "weight", [1.1, .7, .9], 1.3, 1.8)
    shells["female"] = rng.binomial(1, 1 / (1 + np.exp(-(-2.5 + .17 * shells["length"] + .32 * shells["height"] - .15 * shells["weight"]))))
    stores = regression_frame(rng, 320, {"visitors": (10, 180), "hours": (3, 12),
                                         "discount": (.02, .4)}, "sales", [3.4, 7.1, -220], 450, 36)
    third = [
        numeric(3, "조개 성별 로지스틱 회귀", "CSV의 처음 210행으로 학습하고 나머지 90행으로 평가한다. 모든 모형에 절편을 포함한다.",
            "shellfish", shells, {"length": "길이(cm)", "width": "너비(cm)", "height": "높이(cm)", "weight": "무게(g)", "female": "성별(암컷 1, 수컷 0)"}, '''
            import statsmodels.api as sm
            import statsmodels.formula.api as smf
            train, test = df.iloc[:210], df.iloc[210:]
            simple = smf.logit("female ~ weight", data=train).fit(disp=False)
            full = smf.glm("female ~ length + width + height + weight", data=train,
                           family=sm.families.Binomial()).fit()
            predicted = simple.predict(test).ge(.5)
            ''', [
                field("무게의 오즈비", "무게만 사용한 이항 로지스틱 회귀에서 무게가 1g 증가할 때의 오즈비를 구하시오.", 'np.exp(simple.params["weight"])'),
                field("잔차 이탈도", "길이, 너비, 높이, 무게를 모두 사용한 모형의 잔차 이탈도를 구하시오.", "full.deviance"),
                field("평가 자료 오분류율", "무게만 사용한 모형에서 확률이 0.5 이상이면 1로 예측한다. 평가 자료의 오분류 비율을 구하시오.", '(predicted != test["female"]).mean()'),
            ]),
        numeric(3, "매출 상관관계와 다중회귀", "세 설명변수를 이용해 매출을 분석한다.",
            "store_sales", stores, {"visitors": "방문객 수", "hours": "영업시간", "discount": "평균 할인율", "sales": "일 매출"}, '''
            import statsmodels.formula.api as smf
            correlations = df.corr()["sales"].drop("sales")
            model = smf.ols("sales ~ visitors + hours + discount", data=df).fit()
            ''', [
                field("가장 큰 상관계수", "sales와 세 변수의 피어슨 상관계수 중 가장 큰 값을 구하시오.", "correlations.max()"),
                field("방문객 수 회귀계수", "절편을 포함한 다중선형회귀에서 visitors 회귀계수를 구하시오.", 'model.params["visitors"]'),
                field("결정계수", "같은 모형의 결정계수 R²를 구하시오.", "model.rsquared"),
            ]),
    ]
    return first, third


def round_eight(rng):
    n = 120
    continents = np.repeat(["아시아", "유럽", "아프리카", "아메리카"], 30)
    beer = rng.integers(12, 156, n) + 94 * (continents == "유럽")
    drinks = pd.DataFrame({"country_id": np.arange(1, n + 1), "continent": continents,
                           "beer": beer, "wine": rng.integers(12, 120, n)})
    earlier = rng.integers(100, 850, n)
    tourism = pd.DataFrame({"country_id": np.arange(1, n + 1), "tourists_2022": earlier,
                            "tourists_2023": earlier + rng.integers(-65, 150, n),
                            "domestic": rng.integers(100, 920, n), "foreign": rng.integers(23, 400, n)})
    environment = pd.DataFrame({"temperature": rng.normal(20, 4, n), "humidity": rng.uniform(34, 83, n)})
    first = [
        numeric(1, "국가별 맥주 소비량 비교", "각 행은 한 국가의 1인당 연간 음주 소비량을 나타낸다.",
            "drinks", drinks, {"country_id": "국가 번호", "continent": "대륙", "beer": "맥주 소비량", "wine": "와인 소비량"}, '''
            continent = df.groupby("continent")["beer"].mean().idxmax()
            values = df.loc[df["continent"].eq(continent), "beer"].drop_duplicates().nlargest(2)
            ''', [field("두 번째로 큰 소비량", "1인당 맥주 소비량의 국가 평균이 가장 큰 대륙을 고른다. 그 대륙 안에서 중복 소비량은 하나로 간주하고 두 번째로 큰 맥주 소비량을 구하시오.", "values.iloc[1]", 0)]),
        numeric(1, "관광객 증가율과 두 집계값", "국가별 관광객과 국내·해외 집계 항목이 제공된다.",
            "tourism", tourism, {"country_id": "국가 번호", "tourists_2022": "2022년 관광객 수", "tourists_2023": "2023년 관광객 수", "domestic": "국내 방문자 수", "foreign": "해외 방문자 수"}, '''
            df["growth"] = df["tourists_2023"] / df["tourists_2022"] - 1
            df["total_visits"] = df["domestic"] + df["foreign"]
            top = df.sort_values(["growth", "country_id"], ascending=[False, True]).iloc[0]
            ''', [field("해당 국가 방문자 합계", "2022년 대비 2023년 관광객 증가율과 국내·해외 방문자 합계를 각각 계산하시오. 증가율이 가장 높은 국가의 방문자 합계를 구하시오. 동률이면 국가 번호가 작은 곳을 고른다.", 'top["total_visits"]', 0)]),
        numeric(1, "최소 최대 변환과 표준편차", "기온과 습도 측정값을 독립적으로 최소 최대 변환한다.",
            "environment", environment, {"temperature": "기온(℃)", "humidity": "상대습도(%)"}, '''
            transformed = (df - df.min()) / (df.max() - df.min())
            spread = transformed.std(ddof=1)
            ''', [field("두 표준편차 차이", "각 열의 범위를 0~1로 변환하시오. 변환한 기온과 습도의 표본표준편차 차이의 절댓값을 구하시오.", 'abs(spread["temperature"] - spread["humidity"])')]),
    ]
    customers = regression_frame(rng, 490, {"tenure": (1, 62), "monthly_fee": (30, 110), "contacts": (0, 8)},
                                 "churn", [-.05, .016, .47], -1.5, 0)
    customers["churn"] = rng.binomial(1, 1 / (1 + np.exp(-customers["churn"])))
    students = regression_frame(rng, 320, {"memory": (35, 86), "logic": (32, 87), "speed": (27, 91)},
                                "iq", [.45, .61, .08], 30, 6)
    third = [
        numeric(3, "고객 이탈 로지스틱 분석", "churn이 1일 확률을 예측한다. 규제 없이 절편을 포함하고 유의수준은 5%다.",
            "churn", customers, {"tenure": "가입 기간(개월)", "monthly_fee": "월 이용료", "contacts": "문의 횟수", "churn": "이탈 여부"}, '''
            import statsmodels.api as sm
            features = ["tenure", "monthly_fee", "contacts"]
            model = sm.Logit(df["churn"], sm.add_constant(df[features])).fit(disp=False)
            kept = [name for name in features if model.pvalues[name] < .05]
            reduced = sm.Logit(df["churn"], sm.add_constant(df[kept])).fit(disp=False)
            ''', [
                field("유의하지 않은 설명변수 수", "세 설명변수로 적합한 모형에서 p값이 0.05 이상인 설명변수 개수를 구하시오.", "len(features) - len(kept)", 0),
                field("유의한 설명변수 회귀계수 합", "유의한 설명변수만 사용해 다시 적합하고 설명변수들의 계수를 합하시오. 절편은 합계에서 제외한다.", "reduced.params.drop('const').sum()"),
                field("5개월 증가의 오즈비", "처음 모형에서 다른 변수를 고정하고 tenure가 5 증가할 때의 오즈비를 구하시오.", 'np.exp(5 * model.params["tenure"])'),
            ]),
        numeric(3, "인지 검사 결과 다중회귀", "기억, 논리, 처리속도 점수로 IQ를 예측하는 절편 포함 선형회귀를 적합한다.",
            "iq", students, {"memory": "기억 점수", "logic": "논리 점수", "speed": "처리속도 점수", "iq": "측정 IQ"}, '''
            import statsmodels.formula.api as smf
            model = smf.ols("iq ~ memory + logic + speed", data=df).fit()
            best = model.pvalues.drop("Intercept").idxmin()
            example = pd.DataFrame({"memory": [62], "logic": [72], "speed": [51]})
            ''', [
                field("p값 최소 설명변수의 계수", "설명변수 중 p값이 가장 작은 변수의 회귀계수를 구하시오.", "model.params[best]"),
                field("결정계수", "모형의 결정계수 R²를 구하시오.", "model.rsquared"),
                field("예측 IQ", "memory=62, logic=72, speed=51인 사람의 예측 IQ를 구하시오.", "model.predict(example).iloc[0]"),
            ]),
    ]
    return first, third


def round_nine(rng):
    loans = pd.DataFrame({
        "region_code": np.tile(np.repeat(np.arange(1101, 1113), 20), 5),
        "year": np.repeat(np.arange(2019, 2024), 240),
        "sex": np.tile(np.repeat([0, 1], 10), 60),
        "house": rng.integers(800, 8800, 1200), "other": rng.integers(150, 2200, 1200),
    })
    rows = []
    for year in range(2005, 2021):
        total = rng.integers(80, 370, 3)
        rows.append((year, "발생", *total))
        rows.append((year, "검거", *np.rint(total * rng.uniform(.34, .98, 3)).astype(int)))
    crime = pd.DataFrame(rows, columns=["year", "kind", "theft", "assault", "fraud"])
    n = 460
    tenure = pd.DataFrame({"department": rng.choice(["IT", "인사", "영업"], n),
                           "grade": rng.choice(["A", "B", "C"], n),
                           "tenure": rng.integers(1, 30, n).astype(float)})
    tenure.loc[rng.choice(tenure.index, 135, replace=False), "tenure"] = np.nan
    first = [
        numeric(1, "성별 대출액 합계 차이", "대출액은 주택 대출과 기타 대출의 합으로 정의한다.",
            "loans", loans, {"region_code": "지역 코드", "year": "연도", "sex": "성별 코드", "house": "주택 대출액", "other": "기타 대출액"}, '''
            df["total"] = df["house"] + df["other"]
            grouped = df.groupby(["year", "region_code", "sex"])["total"].sum().unstack()
            difference = (grouped[0] - grouped[1]).abs()
            ''', [field("지역 코드", "연도와 지역마다 성별 총대출액 합계를 계산한다. 두 성별 합계 차이의 절댓값이 가장 큰 연도·지역 조합의 지역 코드를 구하시오. 동률이면 연도, 지역 코드의 오름차순 첫 조합을 고른다.", "difference.sort_index().idxmax()[1]", 0)]),
        numeric(1, "연도별 최대 검거율", "각 연도에 발생 건수 행과 검거 건수 행이 하나씩 있다. 각 범죄는 별도의 열이다.",
            "crime", crime, {"year": "연도", "kind": "발생 또는 검거", "theft": "절도", "assault": "폭행", "fraud": "사기"}, '''
            crime_types = ["theft", "assault", "fraud"]
            occurred = df[df["kind"].eq("발생")].set_index("year")[crime_types]
            captured = df[df["kind"].eq("검거")].set_index("year")[crime_types]
            first = (captured / occurred).idxmax(axis=1)
            ''', [field("선정된 검거 건수의 합계", "매년 범죄별로 검거율(검거 건수 ÷ 발생 건수)을 구한다. 각 해에서 검거율이 가장 높은 범죄의 검거 건수를 골라 모두 더하시오. 검거율 동률은 파일 열 순서를 따른다.", "sum(captured.loc[year, kind] for year, kind in first.items())", 0)]),
        numeric(1, "근속연수의 그룹별 결측 대체", "부서와 인사등급이 같은 직원들을 하나의 그룹으로 본다.",
            "employee_tenure", tenure, {"department": "소속 부서", "grade": "인사등급", "tenure": "근속연수(년)"}, '''
            medians = df.groupby(["department", "grade"])["tenure"].transform("median")
            filled = df["tenure"].fillna(np.trunc(medians))
            first = filled[df["department"].eq("IT") & df["grade"].eq("A")].mean()
            second = filled[df["department"].eq("영업") & df["grade"].eq("C")].mean()
            ''', [field("두 그룹 평균의 합", "같은 부서·등급의 근속연수 중앙값으로 결측을 대체하되 중앙값의 소수 부분을 버리시오. 대체 후 IT 부서 A등급의 평균과 영업 부서 C등급의 평균을 더하시오.", "first + second")]),
    ]
    design = regression_frame(rng, 220, {"tenure": (1, 20), "practice": (1, 60),
                                         "age": (20, 65), "portfolio": (2, 21)},
                              "design", [0, 1.9, 0, 2.2], 30, 11)
    clients = regression_frame(rng, 460, {"fee": (25, 90), "visits": (1, 18)},
                               "churn", [.034, -.06], -2.6, 0)
    clients.insert(0, "phone_service", rng.integers(0, 2, len(clients)))
    clients["churn"] = rng.binomial(1, 1 / (1 + np.exp(-(clients["churn"] + .83 * clients["phone_service"]))))
    third = [
        numeric(3, "디자인 시험 점수 회귀", "파일의 처음 140행은 학습용, 나머지는 평가용이다. 모형에 절편을 포함한다.",
            "design", design, {"tenure": "경력(년)", "practice": "연습시간", "age": "나이", "portfolio": "포트폴리오 작품 수", "design": "디자인 시험 점수"}, '''
            import statsmodels.formula.api as smf
            train, test = df.iloc[:140], df.iloc[140:]
            full = smf.ols("design ~ tenure + practice + age + portfolio", data=train).fit()
            reduced = smf.ols("design ~ practice + portfolio", data=train).fit()
            train_corr = reduced.predict(train).corr(train["design"])
            test_corr = reduced.predict(test).corr(test["design"])
            ''', [
                field("유의하지 않은 설명변수 수", "학습용 데이터와 모든 설명변수로 OLS를 적합하시오. 유의수준 5%에서 p값이 0.05 이상인 설명변수 개수를 구하시오.", '(full.pvalues.drop("Intercept") >= .05).sum()', 0),
                field("학습용 피어슨 상관계수", "practice와 portfolio만 사용한 모형을 학습용 자료로 적합하시오. 학습용 자료의 실제 점수와 예측값 간 피어슨 상관계수를 구하시오.", "train_corr"),
                field("평가용 피어슨 상관계수", "두 변수 모형을 평가용 자료에 적용해 실제 점수와 예측값 간 피어슨 상관계수를 구하시오.", "test_corr"),
            ]),
        numeric(3, "이탈 로지스틱 회귀와 모형 검정", "고객의 요금과 방문 횟수 및 전화 서비스 가입 여부로 이탈을 설명한다.",
            "client_churn", clients, {"phone_service": "전화 서비스 이용 여부", "fee": "요금", "visits": "방문 횟수", "churn": "이탈 여부"}, '''
            import statsmodels.formula.api as smf
            model = smf.logit("churn ~ phone_service + fee + visits", data=df).fit(disp=False)
            ''', [
                field("요금 계수의 p값", "절편을 포함해 모형을 적합한 뒤 fee 계수의 양측 검정 p값을 구하시오.", 'model.pvalues["fee"]', 4),
                field("전화 서비스의 오즈비", "다른 변수가 고정일 때 phone_service가 0에서 1로 바뀌면 이탈 오즈가 몇 배가 되는지 구하시오.", 'np.exp(model.params["phone_service"])'),
                field("우도비 검정통계량", "절편만 있는 모형과 전체 모형을 비교하는 카이제곱 우도비 검정통계량을 구하시오.", "model.llr"),
            ]),
    ]
    return first, third


def round_ten(rng):
    n = 580
    topics = rng.integers(1, 9, n)
    quiz = pd.DataFrame({"topic": topics, "correct": rng.binomial(1, .25 + .062 * topics)})
    dates = pd.Timestamp("2022-01-01") + pd.to_timedelta(rng.integers(0, 610, n), unit="D")
    sales = pd.DataFrame({"order_date": dates, "category": rng.choice(["서적", "잡지", "교재"], n),
                          "price": rng.integers(4, 104, n) * 1000})
    first = [
        numeric(1, "소주제별 정답률의 3위", "학습자가 문항에 응답할 때마다 정답 여부를 한 행으로 남긴다.",
            "quiz", quiz, {"topic": "소주제 번호", "correct": "정답은 1, 오답은 0"}, '''
            rates = df.groupby("topic")["correct"].mean().drop_duplicates().nlargest(3)
            ''', [field("세 번째로 높은 정답률", "소주제별 정답 수를 응답 수로 나누시오. 동일한 정답률은 하나의 등수로 세고 세 번째로 높은 정답률을 0~1 비율로 구하시오.", "rates.iloc[2]")]),
        numeric(1, "연월별 매출 순위", "날짜, 상품 유형, 거래금액이 포함된 매출 데이터다.",
            "sales", sales, {"order_date": "주문 날짜", "category": "상품 유형", "price": "거래금액(원)"}, '''
            df["month"] = pd.to_datetime(df["order_date"]).dt.to_period("M")
            ranked = df.groupby("month")["price"].sum().sort_index().sort_values(ascending=False, kind="stable")
            target_month = ranked.index[3]
            category_max = df[df["month"].eq(target_month)].groupby("category")["price"].sum().max()
            ''', [
                field("월별 매출 2위 합계", "거래금액을 연도와 월 단위로 합산해 내림차순으로 정렬하시오. 합계가 같으면 이른 달을 먼저 둔다. 두 번째 달의 총매출을 구하시오.", "ranked.iloc[1]", 0),
                field("매출 4위 달의 유형별 최대 매출", "네 번째 달의 거래금액을 상품 유형별로 합산해 가장 큰 유형 매출을 구하시오.", "category_max", 0),
            ]),
        numeric(1, "스팸과 정상 메일의 단어 수", "메일 본문에서 단어는 공백 하나로 구분되어 있다.",
            "messages", emails(rng, 160), {"label": "메일 유형(spam 또는 ham)", "body": "본문"}, '''
            words = df["body"].str.count(" ") + 1
            means = words.groupby(df["label"]).mean()
            ''', [field("평균 단어 수 차이", "메일별 단어 수를 셈하고 spam과 ham의 평균 단어 수 차이의 절댓값을 구하시오.", 'abs(means["spam"] - means["ham"])')]),
    ]
    employees = regression_frame(rng, 640, {"age": (22, 62), "overtime": (0, 48), "training": (0, 56)},
                                 "leaves", [-.036, .067, 0], -1.05, 0)
    employees["leaves"] = rng.binomial(1, 1 / (1 + np.exp(-employees["leaves"])))
    costs = regression_frame(rng, 360, {"area": (10, 100), "wall": (1, 42), "outside": (-8, 17)},
                             "energy", [1.8, 0, -3.7], 125, 14)
    third = [
        numeric(3, "이직 로지스틱 회귀", "leaves가 1이면 이직, 0이면 잔류다. 모형에 절편을 포함한다.",
            "turnover", employees, {"age": "만 나이", "overtime": "월 초과근무 시간", "training": "연간 교육시간", "leaves": "이직 여부"}, '''
            import statsmodels.api as sm
            variables = ["age", "overtime", "training"]
            full = sm.Logit(df["leaves"], sm.add_constant(df[variables])).fit(disp=False)
            kept = [column for column in variables if full.pvalues[column] < .05]
            model = sm.Logit(df["leaves"], sm.add_constant(df[kept])).fit(disp=False)
            example = {"age": 35, "overtime": 18, "training": 12}
            x = pd.DataFrame([{column: example[column] for column in kept}])
            ''', [
                field("유의한 설명변수의 계수 합", "모든 설명변수로 적합하고 p값이 0.05 미만인 설명변수의 회귀계수를 더하시오. 절편은 제외한다.", "full.params[kept].sum()"),
                field("나이 1년 증가 오즈비", "모든 변수를 사용한 모형에서 다른 변수 값이 같을 때 나이가 1년 늘면 이직 오즈(이직 확률 ÷ 잔류 확률)가 몇 배가 되는지 구하시오.", 'np.exp(full.params["age"])'),
                field("지정 직원의 이직 확률", "유의한 설명변수만 남겨 다시 적합하시오. age=35, overtime=18, training=12인 직원의 이직 확률을 구하시오.", 'model.predict(sm.add_constant(x, has_constant="add")).iloc[0]'),
            ]),
        numeric(3, "에너지 소비량 다중회귀", "건물의 수치형 변수로 energy를 설명한다. 모든 모형에 절편을 포함한다.",
            "energy", costs, {"area": "면적", "wall": "외벽 지표", "outside": "외부 기온", "energy": "에너지 소비량"}, '''
            import statsmodels.api as sm
            features = ["area", "wall", "outside"]
            full = sm.OLS(df["energy"], sm.add_constant(df[features])).fit()
            kept = [column for column in features if full.pvalues[column] < .05]
            reduced = sm.OLS(df["energy"], sm.add_constant(df[kept])).fit()
            ''', [
                field("설명변수 회귀계수 합", "모든 설명변수로 적합한 모형에서 절편을 제외한 계수의 합을 구하시오.", "full.params[features].sum()"),
                field("축소 모형 결정계수", "유의수준 5%에서 유의한 설명변수만 남겨 다시 적합하시오. 그 모형의 결정계수를 구하시오.", "reduced.rsquared"),
                field("면적 10 증가 시 예측 변화량", "축소 모형에서 다른 변수를 고정하고 area가 10 늘 때 예측 energy의 변화량을 구하시오.", '10 * reduced.params["area"]'),
            ]),
    ]
    return first, third


def round_eleven(rng):
    n = 300
    readings = pd.DataFrame({"temperature": rng.normal(25, 3, n), "light": rng.normal(450, 32, n),
                             "noise": rng.normal(36, 4, n), "co2": rng.normal(720, 114, n)})
    for column, count in zip(readings, [56, 35, 18, 22]):
        readings.loc[rng.choice(readings.index, count, replace=False), column] = np.nan
    base = rng.uniform(180, 670, 12)
    growth = rng.uniform(-.034, .087, 12)
    emissions = pd.DataFrame({
        "country_id": np.repeat(np.arange(1, 13), 21), "year": np.tile(np.arange(2001, 2022), 12),
        "emission": (base[:, None] * (1 + growth[:, None]) ** np.arange(21) * rng.uniform(.94, 1.08, (12, 21))).ravel(),
    })
    canceled = rng.random(n) < .23
    order_id = rng.integers(1, 71, n)
    trades = pd.DataFrame({
        "invoice": [f"{'C' if flag else 'N'}{code:04d}" for code, flag in zip(order_id, canceled)],
        "customer_id": rng.integers(1, 55, n), "qty": rng.integers(1, 8, n),
        "price": rng.integers(11, 110, n) * 50,
    })
    first = [
        numeric(1, "실내 측정값의 결측치 보정", "온도, 조도, 소음, 이산화탄소를 측정한 자료다.",
            "indoor_sensors", readings, {"temperature": "실내 온도", "light": "조도", "noise": "소음", "co2": "이산화탄소 농도"}, '''
            column = df.isna().sum().idxmax()
            filled = df[column].fillna(df[column].median())
            ''', [field("대체 후 평균", "결측치가 가장 많은 열을 찾으시오. 그 열의 중앙값으로 해당 열의 결측치를 채운 뒤 대체된 열의 평균을 구하시오.", "filled.mean()")]),
        numeric(1, "국가별 온실가스 배출량", "2001년부터 2021년까지 국가별 온실가스 배출량이 있다.",
            "emissions", emissions, {"country_id": "국가 번호", "year": "연도", "emission": "온실가스 배출량"}, '''
            leaders = df.sort_values(["year", "emission", "country_id"], ascending=[True, False, True]).drop_duplicates("year")
            wide = df.pivot(index="country_id", columns="year", values="emission")
            growth = (wide[2021] / wide[2001]) ** (1 / 20) - 1
            ''', [
                field("최다 1위 횟수", "해마다 배출량 1위 국가를 고르고, 21년 동안 가장 자주 1위를 한 국가의 1위 횟수를 구하시오. 동률이면 국가 번호가 작은 곳을 고른다.", 'leaders["country_id"].value_counts().max()', 0),
                field("최대 연평균 성장률", "국가별로 (2021년 배출량 ÷ 2001년 배출량)^(1/20)−1을 구하시오. 가장 큰 성장률을 0~1 비율로 입력하시오.", "growth.max()"),
            ]),
        numeric(1, "취소 주문의 금액 처리", "주문은 여러 품목을 포함할 수 있다. 주문 번호가 C로 시작하면 취소 항목이다.",
            "transactions", trades, {"invoice": "주문 번호", "customer_id": "고객 번호", "qty": "수량", "price": "단가(원)"}, '''
            canceled = df["invoice"].str.startswith("C")
            signed = (df["qty"] * df["price"]).where(~canceled, -df["qty"] * df["price"])
            refunds = signed[canceled].groupby(df.loc[canceled, "invoice"]).sum().sort_index()
            net = signed.groupby(df["customer_id"]).sum()
            ''', [
                field("취소액이 가장 큰 주문 번호", "수량에 단가를 곱한 거래액을 취소 건은 음수로 처리한다. 취소 건만 주문 번호별로 합산해 가장 작은 음수인 주문 번호를 구하시오. 동점이면 번호가 빠른 것을 고른다.", "refunds.idxmin()", None),
                field("고객별 최대 순매출", "전체 거래를 사용해 취소액을 차감한 고객별 순매출을 구하고 그중 가장 큰 금액을 입력하시오.", "net.max()", 0),
            ]),
    ]
    health = regression_frame(rng, 570, {"age": (25, 79), "bmi": (18, 39), "glucose": (78, 185)},
                              "outcome", [.018, .074, .024], -6.22, 0)
    health.insert(2, "history", rng.integers(0, 2, len(health)))
    health["outcome"] = rng.binomial(1, 1 / (1 + np.exp(-(health["outcome"] + .78 * health["history"]))))
    marketing = regression_frame(rng, 310, {"monthly_visits": (1, 20), "page_minutes": (2, 18), "spend": (5, 75)},
                                 "sales", [50, 0, 22], 400, 173)
    third = [
        numeric(3, "당뇨 데이터 로지스틱 분석", "보건소 검사 자료의 outcome은 당뇨 여부다. 로지스틱 모형에는 절편을 포함한다.",
            "health", health, {"age": "나이", "bmi": "체질량지수", "history": "가족력 여부", "glucose": "공복 혈당", "outcome": "당뇨 여부"}, '''
            import statsmodels.formula.api as smf
            model = smf.logit("outcome ~ age + bmi + history + glucose", data=df).fit(disp=False)
            actual = df["outcome"].eq(1)
            predicted = model.predict(df).ge(.5)
            ''', [
                field("가족력의 오즈비", "모형을 적합한 뒤 history가 0에서 1이 될 때의 오즈비를 구하시오.", 'np.exp(model.params["history"])'),
                field("당뇨군 평균 혈당", "관측된 outcome이 1인 대상자의 평균 공복 혈당을 계산하시오.", 'df.loc[actual, "glucose"].mean()'),
                field("민감도", "예측 확률 0.5 이상을 양성으로 간주하여 모형의 민감도를 계산하시오.", "(actual & predicted).sum() / actual.sum()"),
            ]),
        numeric(3, "홍보와 판매액의 관계", "방문 횟수, 체류 시간, 홍보비가 집계된 판매 자료다.",
            "marketing", marketing, {"monthly_visits": "월 방문 횟수", "page_minutes": "페이지 체류 시간", "spend": "홍보비", "sales": "판매액"}, '''
            import statsmodels.formula.api as smf
            model = smf.ols("sales ~ monthly_visits + page_minutes + spend", data=df).fit()
            correlations = df.corr()["sales"].drop("sales")
            significant = model.params[model.pvalues < .05].drop("Intercept")
            ''', [
                field("체류 시간 계수의 p값", "절편이 있는 다중회귀에서 page_minutes 계수의 양측 p값을 구하시오.", 'model.pvalues["page_minutes"]', 4),
                field("가장 큰 피어슨 상관계수", "판매액과 설명변수 세 개 사이 피어슨 상관계수 중 가장 큰 값을 구하시오.", "correlations.max()"),
                field("유의한 회귀계수 합", "5% 수준에서 유의한 설명변수의 회귀계수 합을 구하시오. 절편을 제외한다.", "significant.sum()"),
            ]),
    ]
    return first, third


def round_twelve(rng):
    n = 275
    words = pd.DataFrame({"description": rng.choice([
        "Python 데이터 처리", "파이썬 판다스", "데이터베이스 설계", "PYTHON통계",
        "R 데이터 분석", "pyTHon 시각화", "SQL 그룹 집계", None,
    ], n)})
    measures = pd.DataFrame({"group": rng.choice(["A", "B"], n, p=[.56, .44]),
                             "score": rng.normal(65, 12, n)})
    area = rng.choice(["서부", "동부", "남부"], n)
    count = rng.integers(1, 25, n)
    amount = rng.integers(5, 170, n) * 100
    shifted = rng.random(n) < .18
    raw = pd.DataFrame({
        "record_id": np.arange(1, n + 1),
        "area": np.where(shifted, "", area),
        "count": np.where(shifted, area, count.astype(str)),
        "amount": np.where(shifted, count, amount),
        "extra": np.where(shifted, amount.astype(str), ""),
    })
    first = [
        numeric(1, "강좌 설명의 문자열 검색", "사이트에 등록된 온라인 강좌 설명이다. 설명이 비어 있는 등록도 있다.",
            "courses", words, {"description": "강좌 설명"}, "",
            [field("검색 조건에 해당하는 강좌 수", "설명에 Python 또는 파이썬이 포함된 행의 개수를 구하시오. 영문은 대소문자를 구분하지 않고, 설명 하나가 두 조건을 모두 만족해도 한 번만 센다.", 'df["description"].str.contains("Python|파이썬", case=False, na=False).sum()', 0)]),
        numeric(1, "두 집단의 합동표본분산", "독립적인 A·B 표본의 점수 변동을 합동표본분산으로 요약한다.",
            "scores", measures, {"group": "집단 구분", "score": "점수"}, '''
            stats = df.groupby("group")["score"].agg(["count", "var"])
            weights = stats["count"] - 1
            ''', [field("합동표본분산", "집단별 표본수 n과 표본분산 s²을 구하시오. 합동표본분산은 [(nA−1)sA²+(nB−1)sB²] ÷ (nA+nB−2)이다.", '(weights * stats["var"]).sum() / weights.sum()')]),
        numeric(1, "한 칸 밀린 지역별 집계", "일부 행은 area가 빈 채로 지역, 수량, 금액이 오른쪽으로 한 칸씩 밀려 있다.",
            "shifted_orders", raw, {"record_id": "기록 번호", "area": "지역", "count": "수량", "amount": "금액(원)", "extra": "밀린 행의 원래 금액"}, '''
            shifted = df["extra"].notna()
            df.loc[shifted, ["area", "count", "amount"]] = df.loc[shifted, ["count", "amount", "extra"]].to_numpy()
            df["count"] = pd.to_numeric(df["count"])
            df["amount"] = pd.to_numeric(df["amount"])
            select = df["area"].eq("서부") & df["count"].ge(10)
            ''', [field("조건에 맞는 금액 합계", "extra가 채워진 행의 지역·수량·금액을 원위치로 돌리시오. 서부이며 수량이 10 이상인 행의 금액을 모두 더하시오.", 'df.loc[select, "amount"].sum()', 0)]),
    ]
    time = pd.DataFrame({"group": np.repeat(["A", "B"], [78, 84]),
                         "minutes": np.r_[rng.normal(27, 5.2, 78), rng.normal(25.5, 7.4, 84)]})
    patients = regression_frame(rng, 520, {"age": (25, 74), "pressure": (88, 165), "exercise": (0, 8)},
                                "risk", [.038, .03, -.24], -5.15, 0)
    patients["risk"] = rng.binomial(1, 1 / (1 + np.exp(-patients["risk"])))
    third = [
        numeric(3, "독립표본 검정과 단측 신뢰구간", "두 집단의 처리 시간이 독립이다. 등분산을 가정하지 않는다.",
            "processing_time", time, {"group": "A 또는 B", "minutes": "처리 시간(분)"}, '''
            from scipy.stats import ttest_ind
            a = df.loc[df["group"].eq("A"), "minutes"]
            b = df.loc[df["group"].eq("B"), "minutes"]
            test = ttest_ind(a, b, equal_var=False, alternative="greater")
            ''', [
                field("Welch t 통계량", "A의 모평균에서 B의 모평균을 뺀 차이가 0인지 Welch 검정의 t 통계량을 구하시오.", "test.statistic"),
                field("단측 p값", "대립가설이 A의 모평균이 더 크다는 것일 때의 p값을 구하시오.", "test.pvalue", 4),
                field("95% 단측 신뢰하한", "A−B 모평균 차이의 95% 단측 신뢰구간 하한을 구하시오.", "test.confidence_interval(.95).low"),
            ]),
        numeric(3, "이항 로지스틱 회귀 해석", "건강 검진 항목으로 위험군 여부를 설명한다.",
            "checkups", patients, {"age": "나이", "pressure": "수축기 혈압", "exercise": "주 운동 시간", "risk": "위험군 여부"}, '''
            import statsmodels.formula.api as smf
            model = smf.logit("risk ~ age + pressure + exercise", data=df).fit(disp=False)
            sample = pd.DataFrame({"age": [50], "pressure": [132], "exercise": [4]})
            ''', [
                field("운동 시간 회귀계수", "절편을 포함하여 이항 로지스틱 회귀를 적합하고 exercise의 계수를 구하시오.", 'model.params["exercise"]'),
                field("혈압 5 증가의 오즈비", "다른 변수는 같고 pressure가 5 증가할 때 위험군 오즈의 배수를 구하시오.", 'np.exp(5 * model.params["pressure"])'),
                field("예측 확률", "age=50, pressure=132, exercise=4인 사람의 위험군 확률을 구하시오.", "model.predict(sample).iloc[0]"),
            ]),
    ]
    return first, third


EARLY_WORK = {2: round_two, 3: round_three, 4: round_four, 5: round_five}
MODERN_WORK = {
    6: round_six, 7: round_seven, 8: round_eight, 9: round_nine,
    10: round_ten, 11: round_eleven, 12: round_twelve,
}


def work_questions(round_number, rng):
    if round_number in EARLY_WORK:
        return EARLY_WORK[round_number](rng), []
    return MODERN_WORK[round_number](rng)
