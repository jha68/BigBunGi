"""An original exam-style curriculum, reference solutions and explicit contracts."""
from textwrap import dedent


def code(text):
    return dedent(text).strip()+"\n"


def file(name, description, columns):
    return {"name":name+".csv", "description":description,
            "columns":[dict(zip(["name","type","description"],x.split("|",2))) for x in columns]}


def answer(key,label,decimals=3):
    return {"key":key,"label":label,"decimals":decimals,
            "format":"정수" if decimals==0 else f"소수 {decimals}자리까지 반올림"}


def question(pid,title,scenario,steps,files,fields,solution,hints,explanation,*,difficulty="중",minutes=12,tags=None):
    kind=int(pid[1]); number=int(pid.split("-")[1])
    starter="import pandas as pd\nimport numpy as np\n\n"+"\n".join(f"{f['name'][:-4]} = pd.read_csv(\"data/{f['name']}\")" for f in files)+"\n\n"+f"print({files[0]['name'][:-4]}.head())\n\n# 분석 코드를 작성하고 answers에 최종 답을 넣으세요.\nanswers = {{\n"+"".join(f"    \"{f['key']}\": None,  # {f['label']}\n" for f in fields)+"}\n"
    return {"id":pid,"type":kind,"number":number,"title":title,"scenario":scenario,"steps":steps,"files":files,"fields":fields,"solution":code(solution),"starter":starter,"hints":hints,"explanation":explanation,"difficulty":difficulty,"minutes":minutes,"tags":tags or [],"points":10 if kind==1 else 40 if kind==2 else 15}


PROBLEMS=[
question("t1-01","고객 점수 상위 10건 보정",
 "고객관리 시스템에서 추출한 360명의 고객 정보입니다. 일부 우수 고객에게 점수가 과하게 부여되어, 상위 고객의 점수를 보정한 후 고령 고객의 평균을 분석하려고 합니다.",
 ["score를 내림차순, 동점이면 id를 오름차순으로 정렬하여 상위 10개 행을 선택합니다.","원본 데이터에서 선택된 10개 행의 score를, 선택된 10개 score 중 최솟값으로 모두 대체합니다.","전체 보정 데이터에서 age가 80 이상인 고객의 score 평균을 구합니다."],
 [file("customers","고객별 나이·점수·거주 지역",["id|정수|중복 없는 고객 번호","age|정수|나이(세)","score|실수|고객 점수","region|문자|거주 지역"])],
 [answer("result","80세 이상 고객의 보정 후 평균 점수")],
 '''
 import pandas as pd
 df = pd.read_csv("data/customers.csv")
 top = df.sort_values(["score", "id"], ascending=[False, True]).head(10)
 df.loc[top.index, "score"] = top["score"].min()
 result = df.loc[df["age"] >= 80, "score"].mean()
 print(result)
 answers = {"result": round(float(result), 3)}
 ''',
 ["head(10)으로 뽑은 행의 index를 기억해 두세요.","보정은 전체 고객 데이터에 적용하고, 나이 조건은 그다음에 적용합니다."],
 "상위 10개 행만 남기고 평균을 구하는 문제가 아닙니다. 원본의 해당 행들을 loc로 보정한 뒤 전체 데이터에 나이 조건을 적용합니다.",tags=["정렬","조건 필터링","값 대체"]),
question("t1-02","결측치 대체 전후 표준편차",
 "회원 소득 데이터 일부가 누락되어 있습니다. 데이터의 앞부분만 사용하여 중앙값 대체가 분산에 미치는 영향을 비교합니다. CSV에 저장된 행 순서를 유지합니다.",
 ["members.csv에서 앞에서부터 전체 행 수의 70%만 선택합니다. 행 수는 내림하여 정수로 계산합니다.","선택한 데이터의 income에 대해 결측치를 제외한 표본표준편차(ddof=1)를 구합니다.","선택한 데이터의 income 중앙값으로 결측치를 채운 뒤 표본표준편차를 다시 구합니다.","대체 전 표준편차에서 대체 후 표준편차를 뺀 값을 구합니다. 다른 열은 사용하지 않습니다."],
 [file("members","480명의 회원 소득과 소비",["member_id|정수|회원 번호","age|정수|나이","income|실수|연 소득(만원), 결측치 포함","spending|정수|월 소비액(만원)"])],
 [answer("result","대체 전 − 대체 후 표본표준편차")],
 '''
 import pandas as pd
 df = pd.read_csv("data/members.csv")
 x = df.iloc[:int(len(df)*0.7)]["income"]
 result = x.std(ddof=1) - x.fillna(x.median()).std(ddof=1)
 print(result)
 answers = {"result": round(float(result), 3)}
 ''',["iloc로 원래 행 순서를 유지하세요.","std()는 기본적으로 결측치를 제외하며 ddof=1입니다. 대체할 중앙값도 선택한 70%에서 계산합니다."],
 "전체 데이터의 중앙값을 사용하거나 dropna로 행을 먼저 제거하면 다른 표본을 분석하게 됩니다. 두 표준편차 모두 같은 70% 구간을 대상으로 계산합니다.",tags=["결측치","표준편차","행 추출"]),
question("t1-03","IQR 기준 배달시간 이상치",
 "620건의 배달 기록에서 지나치게 긴 배달시간과 짧은 배달시간을 함께 탐지합니다. 이상치 기준은 전체 배달시간 분포에서 한 번만 계산합니다.",
 ["delivery_minutes의 제1사분위수(Q1)와 제3사분위수(Q3)를 구합니다. pandas quantile의 기본 linear 보간법을 사용합니다.","IQR = Q3 − Q1로 정의합니다.","Q1 − 1.5×IQR 미만 또는 Q3 + 1.5×IQR 초과인 행을 이상치로 정합니다. 경계와 같은 값은 제외합니다.","이상치 개수와 이상치 행의 delivery_minutes 합을 구합니다."],
 [file("deliveries","배달시간과 배달 거리",["order_id|정수|주문 번호","region|문자|배송 지역","delivery_minutes|실수|배달 소요시간(분)","distance_km|실수|배송 거리(km)"])],
 [answer("count","이상치 행 개수",0),answer("total","이상치 배달시간 합")],
 '''
 import pandas as pd
 df = pd.read_csv("data/deliveries.csv")
 x = df["delivery_minutes"]
 q1, q3 = x.quantile([0.25, 0.75])
 iqr = q3-q1
 outliers = x[(x < q1-1.5*iqr) | (x > q3+1.5*iqr)]
 answers = {"count": int(len(outliers)), "total": round(float(outliers.sum()), 3)}
 print(answers)
 ''',["전체 데이터의 Q1·Q3를 먼저 구하세요.","두 조건은 |로 연결하고 각각 괄호로 감쌉니다."],
 "IQR은 최댓값−최솟값이 아니라 Q3−Q1입니다. 이상치를 제거한 후 기준을 다시 계산하지 않습니다.",tags=["IQR","이상치","집계"]),
question("t1-04","취소 거래를 반영한 순매출",
 "온라인 쇼핑몰의 1,200건 거래 내역입니다. 취소 거래의 amount도 양수로 저장되어 있어 부호 보정 후 고객별 순매출을 구해야 합니다.",
 ["transaction_code가 C로 시작하면 취소 거래로 간주합니다.","취소 거래의 amount는 음수, 나머지 거래의 amount는 양수로 하여 net_amount를 만듭니다.","customer_id별 net_amount 합계를 계산합니다.","순매출이 가장 큰 고객의 번호와 그 고객의 순매출을 구합니다. 동률이면 customer_id가 가장 작은 고객을 선택합니다."],
 [file("transactions","구매와 취소 거래 내역",["transaction_code|문자|C: 취소, T: 일반 거래","customer_id|정수|고객 번호(여러 거래 가능)","product_code|문자|상품 코드","amount|정수|거래 금액(원), 항상 양수"])],
 [answer("customer_id","순매출 1위 고객 번호",0),answer("net_sales","해당 고객의 순매출(원)",0)],
 '''
 import pandas as pd
 import numpy as np
 df = pd.read_csv("data/transactions.csv")
 df["net_amount"] = np.where(df["transaction_code"].str.startswith("C"), -df["amount"], df["amount"])
 totals = df.groupby("customer_id", as_index=False)["net_amount"].sum()
 best = totals.sort_values(["net_amount", "customer_id"], ascending=[False, True]).iloc[0]
 answers = {"customer_id": int(best["customer_id"]), "net_sales": int(best["net_amount"])}
 print(answers)
 ''',["str.startswith('C')와 np.where를 조합해 보세요.","그룹별 합계를 구한 뒤 두 열로 정렬하면 동률 조건도 해결할 수 있습니다."],
 "취소 건을 삭제하는 것과 취소 금액을 차감하는 것은 다릅니다. 고객별 합계에 취소 거래도 음수로 포함해야 합니다.",tags=["문자열","groupby","정렬"]),
question("t1-05","월별 구매 전환율 비교",
 "2025년 웹사이트 방문 900건을 분석합니다. 구매 금액이 0보다 크면 구매 전환으로 정의하며, 방문 건수 기준의 전환율을 사용합니다.",
 ["visited_at을 날짜·시간 형식으로 변환하고 월을 추출합니다.","channel이 광고인 행만 선택합니다.","월별 방문 건수와 구매 전환 건수를 구한 뒤 전환율 = 구매 전환 건수 / 방문 건수 × 100으로 계산합니다.","전환율이 가장 높은 월과 해당 전환율(%)을 구합니다. 동률이면 가장 이른 월을 선택합니다."],
 [file("visits","방문 일시·유입 경로·구매액",["visit_id|정수|방문 번호","visited_at|날짜|2025년 방문 일시","channel|문자|검색, 광고, 직접","purchase_amount|정수|구매액(원), 0은 미구매"])],
 [answer("month","전환율이 가장 높은 월",0),answer("rate","해당 월 전환율(%)")],
 '''
 import pandas as pd
 df = pd.read_csv("data/visits.csv")
 df["month"] = pd.to_datetime(df["visited_at"]).dt.month
 df = df[df["channel"] == "광고"].copy()
 df["converted"] = df["purchase_amount"] > 0
 rates = (df.groupby("month")["converted"].mean()*100).reset_index()
 best = rates.sort_values(["converted", "month"], ascending=[False, True]).iloc[0]
 answers = {"month": int(best["month"]), "rate": round(float(best["converted"]), 3)}
 print(answers)
 ''',["불리언 열의 평균은 True의 비율입니다.","비율을 백분율로 바꾸려면 100을 곱하세요. 반올림은 마지막에만 합니다."],
 "구매액 합계나 고객별 중복 제거가 아니라 방문 행별 구매 여부로 계산하는 문제입니다. 광고 채널을 먼저 필터링합니다.",tags=["날짜 처리","비율","그룹 집계"]),
question("t1-06","회원 등급과 주문 데이터 결합",
 "서로 다른 시스템에 저장된 회원 정보와 주문 정보를 결합합니다. 주문 한 건당 한 행이며, 고객은 여러 주문을 할 수 있습니다.",
 ["orders와 customers를 customer_id 기준으로 결합합니다. customers의 customer_id는 유일합니다.","status가 완료이며 grade가 VIP인 주문만 남깁니다.","지역별 amount 평균을 구합니다. 고객별 평균이 아닌 주문 건당 평균입니다.","평균 주문액이 가장 큰 지역의 평균 주문액을 구합니다."],
 [file("customers","고객별 회원 등급·지역",["customer_id|정수|중복 없는 고객 번호","grade|문자|일반, 우수, VIP","region|문자|서울, 경기, 부산"]),file("orders","주문 내역",["order_id|정수|주문 번호","customer_id|정수|고객 번호","amount|정수|주문액(원)","status|문자|완료 또는 취소"])],
 [answer("result","VIP 완료 주문의 지역별 평균 중 최댓값")],
 '''
 import pandas as pd
 customers = pd.read_csv("data/customers.csv")
 orders = pd.read_csv("data/orders.csv")
 merged = orders.merge(customers, on="customer_id", validate="many_to_one")
 selected = merged[(merged["status"] == "완료") & (merged["grade"] == "VIP")]
 result = selected.groupby("region")["amount"].mean().max()
 answers = {"result": round(float(result), 3)}
 print(answers)
 ''',["merge의 on에 공통 키를 명시하세요.","필터링 후 region별 amount의 평균을 계산합니다."],
 "중복 고객을 제거하면 여러 주문의 정보가 사라집니다. many_to_one 결합으로 주문 행을 유지한 채 주문 단위 평균을 구합니다.",minutes=15,tags=["merge","복합 조건","그룹 평균"]),
question("t1-07","Min-Max 변환 후 조건 집계",
 "420개 센서의 온도·습도·에너지 사용량입니다. 온도와 습도를 서로 독립적으로 0~1 범위로 변환한 후 특정 환경의 에너지 평균을 구합니다.",
 ["전체 데이터의 temperature와 humidity를 각 열별로 Min-Max 정규화합니다. 공식은 (x − min)/(max − min)입니다.","정규화한 temperature가 0.7 이상이고 humidity가 0.4 미만인 행만 선택합니다.","선택한 행의 원본 energy 평균을 구합니다. energy는 정규화하지 않습니다."],
 [file("sensors","센서별 환경과 에너지 사용량",["sensor_id|정수|센서 번호","temperature|실수|온도(℃)","humidity|실수|상대습도(%)","energy|실수|에너지 사용량(kWh)"])],
 [answer("result","조건을 만족하는 센서의 원본 energy 평균")],
 '''
 import pandas as pd
 df = pd.read_csv("data/sensors.csv")
 cols = df[["temperature", "humidity"]]
 scaled = (cols-cols.min())/(cols.max()-cols.min())
 selected = (scaled["temperature"] >= 0.7) & (scaled["humidity"] < 0.4)
 answers = {"result": round(float(df.loc[selected, "energy"].mean()), 3)}
 print(answers)
 ''',["열마다 서로 다른 최솟값·최댓값을 사용해야 합니다.","조건은 변환한 데이터에서 만들고, 평균은 원본 energy에서 계산하세요."],
 "전체 행렬에 하나의 최솟값·최댓값을 적용하지 않습니다. 정규화 전 원본을 유지하면 변환한 열과 원본 열을 혼동하지 않을 수 있습니다.",tags=["정규화","복합 조건","평균"]),
question("t1-08","상품군별 매출 피벗과 순위",
 "6개 지점의 760건 판매 기록을 이용해 식품 매출 상위 지점을 뽑습니다. sales는 행별 총매출이므로 quantity를 다시 곱하지 않습니다.",
 ["store를 행, category를 열, sales의 합계를 값으로 하는 피벗 테이블을 만듭니다. 누락된 조합은 0으로 채웁니다.","식품 매출을 내림차순으로 정렬하여 상위 3개 지점을 선택합니다. 동률이면 지점명 오름차순으로 선택합니다.","선택한 3개 지점의 생활 매출 합계를 구합니다."],
 [file("sales","지점·상품군별 판매 내역",["record_id|정수|판매 기록 번호","store|문자|지점명","category|문자|식품, 생활, 가전","sales|정수|해당 행 총매출(원)","quantity|정수|판매 수량(추가 곱셈 불필요)"])],
 [answer("result","식품 상위 3개 지점의 생활 매출 합계",0)],
 '''
 import pandas as pd
 df = pd.read_csv("data/sales.csv")
 pivot = df.pivot_table(index="store", columns="category", values="sales", aggfunc="sum", fill_value=0).reset_index()
 top = pivot.sort_values(["식품", "store"], ascending=[False, True]).head(3)
 answers = {"result": int(top["생활"].sum())}
 print(answers)
 ''',["pivot_table의 aggfunc 기본값은 mean입니다. sum을 지정하세요.","상위 지점을 고르는 기준 열과 최종 합계를 구하는 열이 다릅니다."],
 "식품 매출로 순위를 정하고 생활 매출을 합산하는 순서를 구분하세요. sales가 이미 총매출이므로 quantity를 곱하면 안 됩니다.",minutes=15,tags=["피벗 테이블","순위","다단계 집계"]),
question(
    "t1-09",
    "Z-score 이상치 제거 후 중앙값",
    "measurements.csv는 배치별 측정 자료이다.",
    [
        "전체 value의 평균과 모집단 표준편차를 기준으로 Z-score를 계산하고, 절댓값이 2.5를 초과하는 행을 제외하시오.",
        "남은 자료에서 batch가 B인 행의 value 중앙값을 구하시오. 이상치 기준은 한 번만 계산한다.",
    ],
    [
        file("measurements", "장비 측정값과 배치", [
            "id|정수|관측 번호",
            "value|실수|장비 측정값",
            "batch|문자|배치 A, B, C",
        ]),
    ],
    [
        answer("result", "이상치 제거 후 B 배치의 중앙값", 3),
    ],
    '''
    import pandas as pd
    df = pd.read_csv('data/measurements.csv')
    z = (df['value'] - df['value'].mean()) / df['value'].std(ddof=0)
    result = df.loc[(z.abs() <= 2.5) & (df['batch'] == 'B'), 'value'].median()
    answers = {'result': round(float(result), 3)}
    print(answers)
    ''',
    [
        "Z-score 기준은 batch를 나누기 전 전체 자료에서 계산합니다.",
        "전체 자료에서 이상치를 판정한 다음 배치 조건을 적용합니다. std(ddof=0)을 사용합니다.",
    ],
    "전체 자료에서 이상치를 판정한 다음 배치 조건을 적용합니다. std(ddof=0)을 사용합니다.",
    difficulty="중",
    minutes=12,
    tags=["표준화", "이상치", "중앙값"],
),
question(
    "t1-10",
    "연도별 배출량 1위 국가 집계",
    "emissions.csv는 국가·산업별 월간 배출량 자료이다.",
    [
        "연도별로 국가의 전체 산업·월 배출량을 합산하고, 배출량이 가장 큰 국가를 한 곳씩 선정하시오. 동률이면 국가명 오름차순으로 선정한다.",
        "선정 횟수가 가장 많은 국가의 선정 횟수를 정수로 구하시오.",
    ],
    [
        file("emissions", "국가·산업별 월간 배출량", [
            "year|정수|연도(2020~2025)",
            "month|정수|월(1~12)",
            "country|문자|국가명",
            "sector|문자|제조 또는 운송",
            "emission|실수|배출량(천 톤)",
        ]),
    ],
    [
        answer("wins", "최다 1위 국가의 1위 횟수", 0),
    ],
    '''
    import pandas as pd
    df = pd.read_csv('data/emissions.csv')
    totals = df.groupby(['year', 'country'], as_index=False)['emission'].sum()
    first = totals.sort_values(['year', 'emission', 'country'], ascending=[True, False, True]).drop_duplicates('year')
    counts = first.groupby('country').size().reset_index(name='wins')
    wins = counts.sort_values(['wins', 'country'], ascending=[False, True]).iloc[0]['wins']
    answers = {'wins': int(wins)}
    print(answers)
    ''',
    [
        "연도·국가별 합계를 먼저 구한 뒤 각 연도의 1위 국가를 고릅니다.",
        "연도·국가별 합계를 정렬한 뒤 연도별 한 행을 선택합니다. 국가별 선정 횟수의 최댓값이 최종 답입니다.",
    ],
    "연도·국가별 합계를 정렬한 뒤 연도별 한 행을 선택합니다. 국가별 선정 횟수의 최댓값이 최종 답입니다.",
    difficulty="중상",
    minutes=15,
    tags=["복합 집계", "동률 처리", "빈도"],
),
]

PREDICTION_PRELUDE=code('''
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, mean_squared_error
train = pd.read_csv("data/train.csv")
test = pd.read_csv("data/test.csv")
''')


def prediction(pid,title,scenario,columns,target,prediction_name,metric,threshold,model,final,explanation,*,class_description=None,baseline=None):
    shared=["id|정수|중복 없는 식별자"]+columns
    files=[file("train","학습 데이터: 예측 대상 열 포함",shared+[f"{target}|수치|학습 정답(예측 대상)"]),file("test","평가 데이터: 예측 대상 열 없음",shared)]
    higher=metric!="rmse"
    steps=[f"train.csv의 {target}을 예측하는 모형을 만들고, test.csv의 모든 관측에 대한 예측 결과를 제출하시오. id는 식별자이며 설명변수에서 제외한다.",
           f"평가 지표는 {metric.upper()}이다. 전처리와 학습 방법 및 모형은 자유롭게 선택하되, 제공된 학습 자료만 사용한다.",
           f"제출 파일 이름은 submission.csv이며 열은 id, {prediction_name} 순서로 구성한다. 행 인덱스는 저장하지 않으며, test.csv의 id를 누락·중복 없이 포함해야 한다."]
    if metric=="roc_auc": steps.insert(1,f"예측 결과는 {target}=1의 발생 확률(0~1)로 제출하시오. 0 또는 1로 판정한 분류값을 제출하지 않는다.")
    if metric=="macro_f1": steps.insert(1,f"{target}의 클래스는 {class_description or '0(초급), 1(중급), 2(고급)'}이다. 예측 확률이 아닌 최종 클래스 번호를 제출하시오.")
    sol=PREDICTION_PRELUDE+f'\ntarget = "{target}"\n'+code('''
X = train.drop(columns=["id", target])
y = train[target]
numeric = X.select_dtypes(include="number").columns.tolist()
categorical = X.select_dtypes(exclude="number").columns.tolist()
preprocessor = ColumnTransformer([
    ("numeric", SimpleImputer(strategy="median"), numeric),
    ("category", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ]), categorical)
])
''')+f"model = {model}\n"+code('''
pipeline = Pipeline([("preprocess", preprocessor), ("model", model)])
X_train, X_valid, y_train, y_valid = train_test_split(
    X, y, test_size=0.2, random_state=42,
    stratify=STRATIFY_TARGET
)
pipeline.fit(X_train, y_train)
if METRIC_NAME == "roc_auc":
    valid_prediction = pipeline.predict_proba(X_valid)[:, 1]
    print("검증 ROC AUC:", roc_auc_score(y_valid, valid_prediction))
elif METRIC_NAME == "macro_f1":
    print("검증 Macro F1:", f1_score(y_valid, pipeline.predict(X_valid), average="macro"))
else:
    print("검증 RMSE:", mean_squared_error(y_valid, pipeline.predict(X_valid))**0.5)
# 검증 후 전체 학습 데이터로 다시 학습합니다. test의 정답은 사용하지 않습니다.
pipeline.fit(X, y)
''')+final+f'\npd.DataFrame({{"id": test["id"], "{prediction_name}": predictions}}).to_csv("submission.csv", index=False)\nprint("submission.csv 저장 완료:", len(predictions), "행")\n'
    sol=sol.replace("STRATIFY_TARGET", "None" if metric=="rmse" else "y").replace("METRIC_NAME",repr(metric))
    p=question(pid,title,scenario,steps,files,[],sol,["범주형 변수는 OneHotEncoder, 수치형 결측치는 SimpleImputer로 처리할 수 있습니다. Pipeline은 데이터 누수를 줄여 줍니다.","분류는 stratify를 사용한 검증 분할을 권장합니다. 회귀의 RMSE는 MSE의 제곱근입니다. 먼저 기준 모델을 만든 뒤 개선하세요."],explanation,difficulty="중상",minutes=35,tags=[{"roc_auc":"이진 분류","rmse":"회귀","macro_f1":"다중 분류"}[metric],"전처리","CSV 제출"])
    p["submission"]={"target":target,"prediction":prediction_name,"metric":metric,"threshold":threshold,"higher":higher,"baseline":baseline if baseline is not None else .5 if metric=="roc_auc" else .333 if metric=="macro_f1" else 1500,"filename":"submission.csv"}
    p["starter"] = 'import pandas as pd\n\ntrain = pd.read_csv("data/train.csv")\ntest = pd.read_csv("data/test.csv")\n\n# 분석 코드를 작성하고 submission.csv를 저장하세요.\n'
    return p


PROBLEMS += [
prediction("t2-01","통신 고객 이탈 확률 예측",
 "통신사의 고객 계약·이용 정보를 이용해 다음 달 이탈 확률을 예측합니다. 수치형 결측치와 범주형 변수가 섞여 있으며, 이탈 여부는 학습 데이터에만 제공됩니다.",
 ["age|실수|나이, 결측치 포함","tenure_months|정수|가입 기간(월)","monthly_charge|실수|월 청구액(달러)","contract|문자|monthly, annual, two_year","support_calls|정수|최근 고객센터 문의 건수","usage_gb|실수|월 사용량(GB), 결측치 포함"],
 "churn","churn_probability","roc_auc",.75,
 'RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=5, random_state=42, n_jobs=1)',
 'predictions = pipeline.predict_proba(test[X.columns])[:, list(pipeline.classes_).index(1)]',
 "ROC AUC는 확률의 순위를 평가합니다. 0/1 결과만 제출하면 순위 정보가 사라집니다. 해설 코드는 기준 모델이며, 검증 세트를 분리해 깊이·최소 리프 크기를 조절해 보세요."),
prediction("t2-02","주거 매물 월세 예측",
 "주거 매물의 면적, 방 수, 연식과 입지를 이용해 월세를 예측합니다. 일부 수치형 값이 누락되어 있고 district는 범주형 변수입니다. monthly_rent 단위는 천 원입니다.",
 ["area_m2|실수|전용 면적(㎡), 결측치 포함","rooms|정수|방 수","building_age|정수|준공 후 연수","station_km|실수|역까지 거리(km), 결측치 포함","district|문자|central, north, south, west","floor|정수|층수"],
 "monthly_rent","monthly_rent","rmse",420,
 'HistGradientBoostingRegressor(max_iter=140, max_leaf_nodes=15, l2_regularization=2, random_state=42)',
 'predictions = pipeline.predict(test[X.columns])',
 "RMSE는 낮을수록 좋고 정답과 같은 단위를 가집니다. 타깃을 로그 변환했다면 제출 전에 역변환이 필요합니다. 해설 모델은 전처리와 비선형 회귀를 하나의 Pipeline으로 묶습니다."),
prediction("t2-03","게임 이용자 레벨 분류",
 "온라인 게임 이용자의 플레이 기록을 바탕으로 초급(0), 중급(1), 고급(2) 레벨을 분류합니다. Macro F1은 세 클래스의 F1을 같은 비중으로 평균하므로 소수 클래스의 성능도 중요합니다.",
 ["weekly_hours|실수|주간 플레이 시간, 결측치 포함","win_rate|실수|승률(0~1)","quests_completed|정수|최근 완료 퀘스트 수","spend_usd|실수|최근 결제액(달러)","device|문자|pc, mobile, console","days_active|정수|가입 후 활동 일수"],
 "level","level","macro_f1",.72,
 'RandomForestClassifier(n_estimators=100, max_depth=12, min_samples_leaf=2, random_state=42, n_jobs=1)',
 'predictions = pipeline.predict(test[X.columns]).astype(int)',
 "Macro F1은 accuracy와 다릅니다. predict 결과인 클래스 번호를 제출하고, 검증 시 f1_score(y_valid, pred, average='macro')로 비교하세요. 클래스별 성능을 함께 살피는 것이 좋습니다."),
question(
    "t3-01",
    "치료 전후 혈압의 평균 차이 검정",
    "treatment.csv는 같은 환자의 치료 전(before)과 치료 후(after) 혈압 자료이다. 전체 환자의 치료 전후 평균 혈압이 다른지 유의수준 0.05에서 양측 검정하시오. 집단 구분(group)은 사용하지 않는다. 혈압 차이는 정규성을 만족한다고 가정한다.",
    [
        "검정 통계량을 구하시오. 차이의 방향은 before − after로 한다.",
        "p-value를 구하시오.",
        "귀무가설의 기각 여부를 구하시오. p-value가 0.05 미만이면 기각 1, 그렇지 않으면 0으로 제출한다.",
    ],
    [
        file("treatment", "환자별 치료 전후 혈압", [
            "patient_id|정수|환자 번호",
            "group|문자|치료 그룹 A, B, C",
            "before|실수|치료 전 혈압(mmHg)",
            "after|실수|치료 후 혈압(mmHg)",
        ]),
    ],
    [
        answer("t_stat", "검정 통계량", 3),
        answer("pvalue", "p-value", 6),
        answer("reject", "귀무가설 기각 여부", 0),
    ],
    '''
    import pandas as pd
    from scipy import stats
    df = pd.read_csv("data/treatment.csv")
    result = stats.ttest_rel(df["before"], df["after"], alternative="two-sided")
    answers = {"t_stat": round(float(result.statistic), 3), "pvalue": round(float(result.pvalue), 6), "reject": int(result.pvalue < 0.05)}
    print(answers)
    ''',
    [
        "같은 사람의 전후 관측이므로 대응표본 검정입니다.",
        "판정은 반올림 전 p-value로 합니다.",
    ],
    "대응표본 t-검정의 귀무가설은 before − after의 모평균이 0이라는 것입니다. 두 입력의 순서를 바꾸면 통계량의 부호가 바뀝니다.",
    difficulty="중",
    minutes=20,
    tags=["대응표본 t-검정", "p-value", "가설 판단"],
),
question(
    "t3-02",
    "홍보 지표와 매출의 다중선형회귀",
    "promotion.csv에서 sales를 종속변수로, ad_spend·visits·page_time·clicks를 설명변수로 사용하는 절편 포함 다중선형회귀모형을 최소제곱법으로 적합하시오. 변수 변환이나 제거는 하지 않는다.",
    [
        "ad_spend의 회귀계수를 구하시오.",
        "ad_spend 회귀계수에 대한 양측 검정의 p-value를 구하시오.",
        "모형의 결정계수 R²를 구하시오.",
    ],
    [
        file("promotion", "홍보 활동과 매출", [
            "ad_spend|실수|광고비(만원)",
            "visits|실수|방문 지표",
            "page_time|실수|페이지 평균 체류시간(초)",
            "clicks|실수|광고 클릭 지표",
            "sales|실수|매출액(만원)",
        ]),
    ],
    [
        answer("coefficient", "ad_spend 회귀계수", 3),
        answer("pvalue", "ad_spend 계수의 p-value", 6),
        answer("r_squared", "결정계수 R²", 3),
    ],
    '''
    import pandas as pd
    import statsmodels.api as sm
    df = pd.read_csv("data/promotion.csv")
    X = sm.add_constant(df[["ad_spend", "visits", "page_time", "clicks"]])
    model = sm.OLS(df["sales"], X).fit()
    answers = {"coefficient": round(float(model.params["ad_spend"]), 3), "pvalue": round(float(model.pvalues["ad_spend"]), 6), "r_squared": round(float(model.rsquared), 3)}
    print(model.summary())
    print(answers)
    ''',
    [
        "statsmodels의 OLS를 사용할 수 있습니다. 절편을 포함하세요.",
        "params, pvalues, rsquared에서 필요한 값을 확인합니다.",
    ],
    "ad_spend의 계수는 다른 설명변수들을 일정하게 두었을 때의 매출 변화를 뜻합니다. 계수의 p-value와 모형 전체 F검정의 p-value를 구분합니다.",
    difficulty="중",
    minutes=20,
    tags=["다중선형회귀", "회귀계수", "결정계수"],
),
question(
    "t3-03",
    "가족력과 질환 발생의 로지스틱 회귀",
    "screening.csv에서 outcome을 종속변수로, age와 history를 설명변수로 사용하는 로지스틱 회귀모형을 적합하시오. 절편을 포함하고 벌점화는 적용하지 않는다. history의 기준 범주는 No이며, 나머지 범주는 Pre와 Yes이다. id와 glucose는 설명변수에서 제외한다.",
    [
        "history가 Pre인 범주의 회귀계수를 구하시오.",
        "history가 No인 경우에 대한 Pre의 오즈비를 구하시오.",
        "전체 관측의 민감도를 구하시오. 예측 확률이 0.5 이상이면 양성(1)으로 판정한다.",
    ],
    [
        file("screening", "건강검진 정보와 질환 발생 여부", [
            "id|정수|환자 번호",
            "age|정수|나이",
            "history|문자|가족력 No, Pre, Yes",
            "glucose|정수|공복 혈당(참고용, 모델에서 제외)",
            "outcome|정수|질환 발생: 1, 미발생: 0",
        ]),
    ],
    [
        answer("coefficient", "history Pre의 회귀계수", 3),
        answer("odds_ratio", "history Pre의 오즈비", 3),
        answer("sensitivity", "민감도", 3),
    ],
    '''
    import pandas as pd
    import numpy as np
    import statsmodels.api as sm
    df = pd.read_csv("data/screening.csv")
    X = pd.DataFrame({"age": df["age"].astype(float), "Pre": (df["history"] == "Pre").astype(float), "Yes": (df["history"] == "Yes").astype(float)})
    model = sm.Logit(df["outcome"], sm.add_constant(X)).fit(disp=False)
    probability = model.predict(sm.add_constant(X))
    sensitivity = ((probability >= 0.5) & (df["outcome"] == 1)).sum() / (df["outcome"] == 1).sum()
    answers = {"coefficient": round(float(model.params["Pre"]), 3), "odds_ratio": round(float(np.exp(model.params["Pre"])), 3), "sensitivity": round(float(sensitivity), 3)}
    print(model.summary())
    print(answers)
    ''',
    [
        "No를 기준으로 Pre와 Yes 더미변수를 만듭니다.",
        "오즈비는 회귀계수의 지수이고 민감도의 분모는 실제 양성 수입니다.",
    ],
    "statsmodels.Logit으로 비벌점 최대우도 추정을 수행합니다. 오즈비 계산에는 반올림 전 계수를 사용합니다. 민감도는 실제 양성 중 양성으로 예측한 비율입니다.",
    difficulty="중상",
    minutes=20,
    tags=["로지스틱 회귀", "오즈비", "민감도"],
),
]

from .extra_content import additional_problems
PROBLEMS += additional_problems(question, file, answer, prediction)
PROBLEMS.sort(key=lambda p: (p["type"], p["number"]))
PROBLEM_MAP={p["id"]:p for p in PROBLEMS}
