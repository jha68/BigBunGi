"""Thirty-four original exercises extending the existing exam-style contracts."""


def additional_problems(q, f, a, prediction):
    problems = [
        q("t1-11", "사용자별 최신 기록과 중복 제거",
          "동일 사용자의 접속 기록이 여러 번 저장되었습니다. 사용자별 최신 상태를 한 건만 남긴 뒤 활성 사용자의 접속시간을 분석합니다.",
          ["updated_at을 날짜·시간으로 변환합니다.", "user_id별 updated_at이 가장 늦은 기록을 선택합니다. 시간이 같으면 record_id가 가장 큰 기록을 선택합니다.", "선택한 최신 기록 중 status가 active인 사용자 수와 minutes 평균을 구합니다. 활성 여부를 먼저 필터링하지 마세요."],
          [f("sessions", "사용자 상태 수정 이력", ["record_id|정수|중복 없는 기록 번호", "user_id|정수|사용자 번호", "updated_at|날짜|기록 수정 일시", "status|문자|active 또는 inactive", "minutes|실수|접속시간(분)"])],
          [a("count", "최신 상태가 active인 사용자 수", 0), a("mean_minutes", "해당 사용자의 평균 접속시간")],
          '''
          import pandas as pd
          df = pd.read_csv("data/sessions.csv")
          df["updated_at"] = pd.to_datetime(df["updated_at"])
          latest = df.sort_values(["updated_at", "record_id"], ascending=[False, False]).drop_duplicates("user_id")
          active = latest[latest["status"] == "active"]
          answers = {"count": int(len(active)), "mean_minutes": round(float(active["minutes"].mean()), 3)}
          print(answers)
          ''',
          ["정렬 후 drop_duplicates의 기본 keep='first'를 활용하세요.", "활성 여부는 최신 기록을 선택한 다음 확인해야 합니다."],
          "과거에 active였어도 최신 상태가 inactive라면 제외합니다. 시각 동률 처리까지 정렬 키에 포함해야 한 사용자당 정확히 한 행을 선택할 수 있습니다.", tags=["중복 제거", "날짜", "정렬"]),

        q("t1-12", "부서별 중앙값으로 성과급 결측치 대체",
          "직원 성과급 일부가 누락되었습니다. 부서별 분포 차이를 반영해 결측치를 대체하고 고평가 직원의 성과급 합계를 구합니다.",
          ["원본 전체 직원에서 department별 bonus 중앙값을 계산합니다. 결측치는 중앙값 계산에서 제외합니다.", "bonus 결측치를 같은 부서의 중앙값으로 대체합니다.", "그다음 rating이 3.5 이상인 직원을 선택하여 직원 수와 대체 후 bonus 합계를 구합니다."],
          [f("employees", "직원별 부서·성과급·평가", ["id|정수|직원 번호", "department|문자|소속 부서", "bonus|실수|성과급(만원), 결측치 포함", "rating|실수|평가 점수(1~5)"])],
          [a("count", "고평가 직원 수", 0), a("total_bonus", "고평가 직원의 대체 후 성과급 합계")],
          '''
          import pandas as pd
          df = pd.read_csv("data/employees.csv")
          medians = df.groupby("department")["bonus"].transform("median")
          df["bonus"] = df["bonus"].fillna(medians)
          selected = df[df["rating"] >= 3.5]
          answers = {"count": int(len(selected)), "total_bonus": round(float(selected["bonus"].sum()), 3)}
          print(answers)
          ''',
          ["transform('median')은 원래 행 수에 맞는 부서별 중앙값을 반환합니다.", "평가 점수로 먼저 필터링하면 대체에 사용하는 중앙값이 달라집니다."],
          "전체 중앙값 하나가 아닌 부서별 중앙값을 사용합니다. 결측치 대체 기준을 원본에서 확정한 후 평가 점수 조건을 적용합니다.", tags=["그룹별 결측치", "transform", "합계"]),

        q("t1-13", "결측 비율에 따른 열 제거와 완전 사례",
          "품질 측정 항목 k1~k5 중 결측 비율이 높은 항목을 제외하고, 남은 항목이 모두 관측된 행만 분석합니다. id는 식별자입니다.",
          ["원본 행 수를 분모로 k1~k5의 열별 결측 비율을 계산합니다.", "결측 비율이 0.20을 초과하는 측정 열을 제거합니다. 0.20과 같은 열은 유지합니다. id는 판단 대상에서 제외합니다.", "유지한 측정 열 중 하나라도 결측인 행을 제거합니다.", "남은 행 수와 남은 행의 k5 평균을 구합니다."],
          [f("quality", "품질 측정값", ["id|정수|측정 번호", "k1|실수|측정 항목 1", "k2|실수|측정 항목 2", "k3|실수|측정 항목 3", "k4|실수|측정 항목 4", "k5|실수|측정 항목 5"])],
          [a("count", "완전 사례의 행 수", 0), a("mean_k5", "완전 사례의 k5 평균")],
          '''
          import pandas as pd
          df = pd.read_csv("data/quality.csv")
          columns = ["k1", "k2", "k3", "k4", "k5"]
          kept = df[columns].isna().mean().loc[lambda x: x <= 0.20].index
          complete = df.dropna(subset=kept)
          answers = {"count": int(len(complete)), "mean_k5": round(float(complete["k5"].mean()), 3)}
          print(answers)
          ''',
          ["isna().mean()으로 열별 결측 비율을 구할 수 있습니다.", "dropna의 subset에는 제거 전 전체 열이 아니라 유지할 열만 넣습니다."],
          "행을 먼저 제거하면 원본의 열별 결측 비율을 구할 수 없습니다. 제외한 열의 결측치는 완전 사례 판단에도 사용하지 않습니다.", tags=["결측 비율", "열 제거", "완전 사례"]),

        q("t1-14", "분위수 경계 보정과 모집단 표준편차",
          "오른쪽 꼬리가 긴 측정값을 10~90백분위수 경계로 보정합니다. 행을 삭제하지 않고 극단값만 경계값으로 대체합니다.",
          ["결측치를 제외한 원본 value의 10백분위수와 90백분위수를 구합니다. quantile의 기본 linear 보간법을 사용합니다.", "하한 미만은 하한, 상한 초과는 상한으로 대체하며 경계와 같은 값은 바꾸지 않습니다. 결측치는 그대로 둡니다.", "값이 바뀐 행 수와 보정 후 value의 모집단 표준편차(ddof=0)를 구합니다. 표준편차 계산에서는 결측치를 제외합니다."],
          [f("readings", "극단값·결측치가 있는 측정값", ["id|정수|측정 번호", "value|실수|측정값, 결측치 포함"])],
          [a("changed", "경계값으로 대체된 행 수", 0), a("std_population", "보정 후 모집단 표준편차")],
          '''
          import pandas as pd
          x = pd.read_csv("data/readings.csv")["value"]
          low, high = x.quantile([0.1, 0.9])
          changed = ((x < low) | (x > high)).sum()
          corrected = x.clip(lower=low, upper=high)
          answers = {"changed": int(changed), "std_population": round(float(corrected.std(ddof=0)), 3)}
          print(answers)
          ''',
          ["clip은 경계를 벗어난 값만 바꾸고 결측치는 유지합니다.", "pandas std의 기본값은 ddof=1이므로 이 문제에서는 0을 명시하세요."],
          "분위수 범위 밖 행을 삭제하는 절사와 값 대체는 다릅니다. 모집단 표준편차는 표본 표준편차와 분모가 다릅니다.", tags=["분위수", "clip", "ddof"]),

        q("t1-15", "금액·할인율 문자열 정제",
          "결제액은 '12,500원', 할인율은 '10%' 같은 문자열로 저장되어 있습니다. 온라인에서 정상 결제한 거래의 할인 후 매출을 계산합니다.",
          ["amount에서 쉼표와 '원'을 제거하여 숫자로 변환합니다.", "discount에서 '%'를 제거하고 100으로 나누어 할인 비율로 변환합니다.", "channel이 온라인이고 status가 결제인 행만 선택합니다.", "각 거래의 할인 후 금액 = amount × (1 − 할인 비율)을 계산하여 합계와 거래 수를 구합니다. 거래별 반올림은 하지 않습니다."],
          [f("payments", "문자열 금액과 할인율", ["id|정수|결제 번호", "amount|문자|쉼표·원 단위가 포함된 금액", "discount|문자|퍼센트 문자열", "channel|문자|온라인 또는 매장", "status|문자|결제 또는 취소"])],
          [a("net_sales", "할인 후 온라인 결제액 합계"), a("count", "선택한 거래 수", 0)],
          '''
          import pandas as pd
          df = pd.read_csv("data/payments.csv")
          amount = df["amount"].str.replace(",", "", regex=False).str.replace("원", "", regex=False).astype(float)
          rate = df["discount"].str.replace("%", "", regex=False).astype(float)/100
          mask = (df["channel"] == "온라인") & (df["status"] == "결제")
          answers = {"net_sales": round(float((amount[mask]*(1-rate[mask])).sum()), 3), "count": int(mask.sum())}
          print(answers)
          ''',
          ["정제 전 문자열을 바로 astype(float)로 바꾸면 오류가 납니다.", "10%는 10이 아니라 0.1로 계산합니다."],
          "원 단위와 구분 기호를 없앤 뒤 계산합니다. 취소 금액을 더하지 않고 선택한 거래별 할인액을 각각 적용합니다.", tags=["문자열 정제", "형 변환", "할인율"]),

        q("t1-16", "평일 출고의 배송 지연 분석",
          "출고·도착 일시로 배송 소요시간을 계산합니다. 공휴일은 따로 고려하지 않고 월~금 출고만 분석합니다.",
          ["shipped_at과 arrived_at을 날짜·시간으로 변환합니다.", "출고 요일이 월요일(0)~금요일(4)인 행만 선택합니다.", "소요시간은 (도착 일시 − 출고 일시)의 전체 초를 3,600으로 나눈 시간으로 계산합니다.", "선택한 행의 소요시간 중앙값과 소요시간이 48시간을 초과하는 행 수를 구합니다."],
          [f("parcels", "출고와 도착 시각", ["id|정수|배송 번호", "shipped_at|날짜|출고 일시", "arrived_at|날짜|도착 일시"])],
          [a("median_hours", "평일 출고의 소요시간 중앙값"), a("late_count", "48시간 초과 배송 수", 0)],
          '''
          import pandas as pd
          df = pd.read_csv("data/parcels.csv")
          sent = pd.to_datetime(df["shipped_at"])
          arrived = pd.to_datetime(df["arrived_at"])
          hours = ((arrived-sent).dt.total_seconds()/3600)[sent.dt.dayofweek < 5]
          answers = {"median_hours": round(float(hours.median()), 3), "late_count": int((hours > 48).sum())}
          print(answers)
          ''',
          ["dt.seconds는 하루를 넘는 기간의 전체 초가 아닙니다. total_seconds를 사용하세요.", "요일 조건은 도착일이 아니라 출고일에 적용합니다."],
          "주말 배송을 모두 제외하는 조건이 아니라 주말 출고를 제외하는 조건입니다. 48시간과 같은 행은 지연 수에 포함하지 않습니다.", tags=["날짜 차이", "요일", "중앙값"]),

        q("t1-17", "월 매출의 전월 대비 증가율",
          "2024년 1월부터 2025년 6월까지 일별 매출입니다. 연도를 함께 구분하여 월별 매출 증가율을 비교합니다.",
          ["date를 날짜로 변환하고 연·월별 revenue 합계를 계산합니다.", "시간 순으로 정렬하여 전월 대비 증가율 = (이번 달 합계 / 전월 합계 − 1) × 100을 계산합니다.", "비교할 전월이 없는 첫 달은 제외합니다. 월이 다른 연도에 걸쳐도 연속해서 비교합니다.", "증가율이 가장 큰 연월을 YYYYMM 형식의 정수로 제출하고 증가율(%)을 구합니다. 동률이면 이른 연월을 선택합니다."],
          [f("retail", "18개월의 일별 매출", ["date|날짜|매출 발생일", "revenue|실수|일 매출(원)"])],
          [a("year_month", "최대 증가율의 연월 YYYYMM", 0), a("growth_pct", "전월 대비 증가율(%)")],
          '''
          import pandas as pd
          df = pd.read_csv("data/retail.csv")
          month = pd.to_datetime(df["date"]).dt.to_period("M")
          monthly = df.groupby(month)["revenue"].sum().sort_index()
          growth = (monthly/monthly.shift(1)-1)*100
          best = growth.dropna().idxmax()
          answers = {"year_month": int(str(best).replace("-", "")), "growth_pct": round(float(growth.loc[best]), 3)}
          print(answers)
          ''',
          ["dt.month만 사용하면 서로 다른 연도의 같은 월이 합쳐집니다.", "shift(1)로 이전 월의 매출을 정렬된 월별 합계와 나란히 놓을 수 있습니다."],
          "일별 증가율 평균이 아닌 월 합계의 증가율을 계산합니다. 시간순 정렬을 유지하면 idxmax는 동률 중 이른 월을 선택합니다.", difficulty="중상", minutes=15, tags=["월 집계", "shift", "증가율"]),

        q("t1-18", "지역별 상위 3명 점수 집계",
          "지역별로 우수 참가자 3명을 선정합니다. 점수가 같으면 참가자 번호가 작은 사람을 우선하므로 정확히 3명씩 선택해야 합니다.",
          ["region별 score 내림차순, 동점이면 id 오름차순으로 정렬합니다.", "각 지역에서 처음 3개 행을 선택합니다. 동점자 전체를 추가로 포함하지 않습니다.", "선택한 전체 참가자의 수와 score 평균을 구합니다."],
          [f("rankings", "참가자의 지역과 점수", ["id|정수|참가자 번호", "region|문자|참가 지역", "score|정수|획득 점수"])],
          [a("count", "선정된 참가자 수", 0), a("mean_score", "선정 참가자의 평균 점수")],
          '''
          import pandas as pd
          df = pd.read_csv("data/rankings.csv")
          selected = df.sort_values(["region", "score", "id"], ascending=[True, False, True]).groupby("region").head(3)
          answers = {"count": int(len(selected)), "mean_score": round(float(selected["score"].mean()), 3)}
          print(answers)
          ''',
          ["전체 데이터의 head(3)이 아니라 그룹마다 head(3)을 선택하세요.", "rank 방식에 따라 동점자 수가 달라지므로 두 정렬 키를 명시하는 것이 안전합니다."],
          "순위 3 이하인 모든 동점자를 뽑는 조건이 아닙니다. 지역마다 세 행만 뽑아야 하며 두 번째 정렬 기준은 id입니다.", tags=["그룹별 상위", "동률", "정렬"]),

        q("t1-19", "피벗 테이블로 온라인 매출 비중 비교",
          "매장별 온라인·오프라인 거래가 행으로 저장되어 있습니다. 두 채널을 모두 포함한 전체 매출에서 온라인 매출의 비중을 비교합니다.",
          ["store_id를 행, channel을 열로 하여 sales 합계 피벗 테이블을 만듭니다.", "매장별 온라인 비중 = 온라인 매출 / (온라인 + 오프라인 매출) × 100으로 계산합니다.", "온라인 비중이 가장 큰 store_id와 그 비중(%)을 구합니다. 동률이면 store_id가 작은 매장을 선택합니다."],
          [f("channels", "매장·채널별 거래", ["id|정수|거래 번호", "store_id|정수|매장 번호", "channel|문자|온라인 또는 오프라인", "sales|정수|매출(원)"])],
          [a("store_id", "온라인 매출 비중 1위 매장", 0), a("online_pct", "해당 매장의 온라인 비중(%)")],
          '''
          import pandas as pd
          df = pd.read_csv("data/channels.csv")
          pivot = df.pivot_table(index="store_id", columns="channel", values="sales", aggfunc="sum", fill_value=0)
          rates = (pivot["온라인"]/(pivot["온라인"]+pivot["오프라인"])*100).sort_index()
          best = rates.idxmax()
          answers = {"store_id": int(best), "online_pct": round(float(rates.loc[best]), 3)}
          print(answers)
          ''',
          ["pivot_table의 기본 aggfunc는 mean이므로 sum을 명시하세요.", "채널별 거래 건수가 아닌 매출 합계의 비중입니다."],
          "온라인 매출 자체가 가장 큰 매장과 온라인 비중이 가장 큰 매장은 다를 수 있습니다. 전체 두 채널 합계를 분모로 사용합니다.", tags=["피벗", "매출 비중", "동률"]),

        q("t1-20", "거래처 미등록 주문과 등급별 입고액",
          "매입 내역에 거래처 마스터에 등록되지 않은 번호가 포함되어 있습니다. 미등록 건수를 확인하고 우수 거래처의 입고액을 집계합니다.",
          ["purchases를 기준으로 suppliers를 supplier_id에 대해 왼쪽 결합합니다. suppliers의 키는 중복되지 않습니다.", "거래처가 매칭되지 않은 매입 행 수를 구합니다. 거래처 고유 번호 수가 아닌 매입 건수입니다.", "매칭된 행 중 grade가 A이고 status가 입고인 행의 cost 합계를 구합니다."],
          [f("suppliers", "등록 거래처 마스터", ["supplier_id|정수|중복 없는 거래처 번호", "grade|문자|거래처 등급 A, B, C"]), f("purchases", "매입·입고 기록", ["purchase_id|정수|매입 번호", "supplier_id|정수|거래처 번호", "cost|정수|매입액(원)", "status|문자|입고 또는 대기"])],
          [a("unmatched", "미등록 거래처의 매입 행 수", 0), a("total_cost", "A등급 입고액 합계", 0)],
          '''
          import pandas as pd
          orders = pd.read_csv("data/purchases.csv")
          suppliers = pd.read_csv("data/suppliers.csv")
          merged = orders.merge(suppliers, on="supplier_id", how="left", validate="many_to_one", indicator=True)
          selected = merged[(merged["grade"] == "A") & (merged["status"] == "입고")]
          answers = {"unmatched": int((merged["_merge"] == "left_only").sum()), "total_cost": int(selected["cost"].sum())}
          print(answers)
          ''',
          ["inner 결합을 사용하면 미등록 매입이 사라집니다.", "indicator=True로 매칭 여부를 확인하거나 결합 후 grade 결측을 확인하세요."],
          "거래처 수와 매입 행 수를 구분합니다. 원본 매입을 보존하는 left 결합이 필요하며, 매칭된 A등급에서 입고 완료 행만 합산합니다.", tags=["left join", "미매칭", "조건 집계"]),
    ]
    problems += [
        q("t1-21", "재고 수량을 가중치로 한 평균 단가",
          "품목별 단가와 재고 수량입니다. 재고가 없는 품목과 단가를 알 수 없는 품목을 제외하고 전체 재고의 평균 단가를 계산합니다.",
          ["quantity가 0보다 크고 unit_price가 결측이 아닌 행만 사용합니다.", "선택한 행의 quantity 합계를 구합니다.", "가중평균 단가 = sum(unit_price × quantity) / sum(quantity)로 계산합니다. 품목별 단순 평균을 사용하지 않습니다."],
          [f("inventory", "품목별 재고와 단가", ["id|정수|품목 번호", "unit_price|실수|개당 가격(원), 결측치 포함", "quantity|정수|재고 개수, 0 포함"])],
          [a("total_quantity", "유효 품목의 총 재고 개수", 0), a("weighted_price", "재고 가중평균 단가")],
          '''
          import pandas as pd
          df = pd.read_csv("data/inventory.csv")
          valid = df[(df["quantity"] > 0) & df["unit_price"].notna()]
          total = valid["quantity"].sum()
          mean = (valid["unit_price"]*valid["quantity"]).sum()/total
          answers = {"total_quantity": int(total), "weighted_price": round(float(mean), 3)}
          print(answers)
          ''',
          ["분자와 분모 모두 같은 유효 행 집합을 사용해야 합니다.", "단가가 결측인 품목의 수량을 분모에 남기면 평균이 작아집니다."],
          "개수가 서로 다른 품목의 단순 평균은 전체 재고의 평균 가격과 다릅니다. 단가 결측 행과 수량 0인 행을 먼저 제외합니다.", tags=["가중평균", "결측치", "조건 필터링"]),

        q("t1-22", "완료 주문 고객의 재구매율",
          "한 고객이 여러 주문을 할 수 있는 쇼핑몰 자료입니다. 주문 수 기준이 아니라 고객 수 기준으로 재구매율을 계산합니다.",
          ["status가 완료인 주문만 사용합니다.", "완료 주문이 한 건 이상 있는 고객을 분석 대상 고객으로 정의합니다.", "완료 주문이 2건 이상인 고객을 재구매 고객으로 정의합니다.", "재구매 고객 수와 재구매 고객 수 / 분석 대상 고객 수 × 100을 구합니다."],
          [f("orders", "고객의 완료·취소 주문", ["id|정수|중복 없는 주문 번호", "customer_id|정수|고객 번호", "status|문자|완료 또는 취소", "amount|정수|주문액(원)"])],
          [a("repeat_count", "재구매 고객 수", 0), a("repeat_pct", "완료 고객 기준 재구매율(%)")],
          '''
          import pandas as pd
          df = pd.read_csv("data/orders.csv")
          counts = df.loc[df["status"] == "완료"].groupby("customer_id").size()
          repeat = (counts >= 2).sum()
          answers = {"repeat_count": int(repeat), "repeat_pct": round(float(repeat/len(counts)*100), 3)}
          print(answers)
          ''',
          ["groupby().size()로 완료 주문 건수를 고객별로 계산하세요.", "분모는 전체 주문 수도, 취소 주문만 한 고객까지 포함한 고객 수도 아닙니다."],
          "재구매 고객의 주문이 5건이어도 고객 수에는 1명으로 계산합니다. 취소 주문은 구매 이력에 포함하지 않습니다.", tags=["고객별 집계", "재구매율", "고유 개수"]),

        q("t1-23", "상담 채널별 환불 비율 교차표",
          "전화·채팅·이메일 상담 결과입니다. refunded는 환불이면 1, 아니면 0이며 채널별 상담 건수가 서로 다릅니다.",
          ["channel과 refunded의 교차표를 만듭니다.", "채팅 상담 건수를 구합니다.", "채팅 상담 중 refunded=1인 비율을 백분율로 구합니다. 전체 상담 수가 아닌 채팅 상담 수를 분모로 사용합니다."],
          [f("claims", "상담 채널과 환불 처리 여부", ["id|정수|상담 번호", "channel|문자|전화, 채팅, 이메일", "refunded|정수|환불 1, 미환불 0"])],
          [a("chat_count", "채팅 상담 건수", 0), a("refund_pct", "채팅 상담 환불 비율(%)")],
          '''
          import pandas as pd
          df = pd.read_csv("data/claims.csv")
          table = pd.crosstab(df["channel"], df["refunded"])
          total = table.loc["채팅"].sum()
          answers = {"chat_count": int(total), "refund_pct": round(float(table.loc["채팅", 1]/total*100), 3)}
          print(answers)
          ''',
          ["crosstab에서 행이 채널, 열이 환불 여부가 되도록 넣으세요.", "normalize='index'를 사용하면 각 채널 행의 합이 1인 비율표가 됩니다."],
          "열 기준 정규화는 환불된 상담 중 각 채널의 구성비를 뜻합니다. 이 문제는 채팅 행 내부에서 환불 비율을 구합니다.", tags=["교차표", "행 정규화", "백분율"]),

        q("t1-24", "수율과 음의 상관관계가 가장 큰 변수",
          "실험의 네 가지 화학 측정값과 수율 점수가 있습니다. 결측치가 포함되어 있어 상관관계와 표준편차의 유효 행을 구분해야 합니다.",
          ["chem_a·chem_b·chem_c·chem_d 각각과 yield_score 사이의 Pearson 상관계수를 계산합니다. 변수 쌍별로 두 값이 모두 있는 행을 사용합니다.", "상관계수가 가장 작은, 즉 가장 음의 관계인 측정 변수를 선택합니다. 절댓값 최대가 아닙니다.", "선택한 상관계수를 부호를 유지해 제출합니다.", "선택한 변수와 yield_score가 모두 관측된 행만 사용하여 선택한 변수의 표본표준편차(ddof=1)를 구합니다."],
          [f("laboratory", "화학 측정과 수율", ["id|정수|실험 번호", "chem_a|실수|측정값 A, 결측치 포함", "chem_b|실수|측정값 B, 결측치 포함", "chem_c|실수|측정값 C, 결측치 포함", "chem_d|실수|측정값 D, 결측치 포함", "yield_score|실수|수율 점수, 결측치 포함"])],
          [a("correlation", "선택한 변수의 수율과 상관계수"), a("sample_std", "해당 유효 행의 선택 변수 표본표준편차")],
          '''
          import pandas as pd
          df = pd.read_csv("data/laboratory.csv")
          correlations = df[["chem_a", "chem_b", "chem_c", "chem_d"]].corrwith(df["yield_score"])
          selected = correlations.idxmin()
          paired = df[[selected, "yield_score"]].dropna()
          answers = {"correlation": round(float(correlations.loc[selected]), 3), "sample_std": round(float(paired[selected].std(ddof=1)), 3)}
          print(answers)
          ''',
          ["전체 열을 한꺼번에 dropna하면 변수 쌍별 유효 행과 달라집니다.", "상관계수 자체의 idxmin을 사용하고 abs는 사용하지 않습니다."],
          "최대 음의 관계는 상관계수가 수직선상 가장 작은 경우입니다. 표준편차에서도 선택 변수와 수율의 쌍별 유효 행 조건을 유지합니다.", difficulty="중상", minutes=15, tags=["상관계수", "쌍별 결측", "표준편차"]),

        q("t1-25", "나이 구간의 경계와 그룹 통계",
          "건강검진 대상자의 나이를 겹치지 않는 구간으로 나눕니다. 경계와 정확히 같은 나이는 어느 구간에 포함되는지 주의하세요.",
          ["구간 [18,30), [30,45), [45,60), [60,81)로 나이를 구분합니다. 각 구간의 왼쪽 경계는 포함하고 오른쪽 경계는 제외합니다.", "[45,60) 구간의 glucose 평균을 구합니다.", "[60,81) 구간에 속하는 사람 수를 구합니다. 나이가 60인 사람은 이 구간에 포함됩니다."],
          [f("health", "나이와 공복혈당", ["id|정수|대상자 번호", "age|정수|나이 18~80", "glucose|실수|공복혈당(mg/dL)"])],
          [a("mean_glucose", "45세 이상 60세 미만의 혈당 평균"), a("older_count", "60세 이상 81세 미만 인원", 0)],
          '''
          import pandas as pd
          df = pd.read_csv("data/health.csv")
          groups = pd.cut(df["age"], bins=[18, 30, 45, 60, 81], right=False, labels=["a", "b", "c", "d"])
          answers = {"mean_glucose": round(float(df.loc[groups == "c", "glucose"].mean()), 3), "older_count": int((groups == "d").sum())}
          print(answers)
          ''',
          ["pd.cut의 기본 right=True는 문제의 경계 조건과 다릅니다.", "범주 라벨을 부여하면 해당 구간을 불리언 조건으로 선택할 수 있습니다."],
          "60세를 45~59세 구간에 포함하면 답이 달라집니다. 구간의 닫힌 쪽을 직접 지정해 경계 나이를 정확히 배정합니다.", tags=["구간화", "cut", "경계 조건"]),

        q("t1-26", "매장별 전년 대비 매출 성장률",
          "100개 매장의 2024·2025년 상품별 매출입니다. 각 상품 행을 먼저 매장·연도 단위로 합친 뒤 성장률 1위 매장을 찾습니다.",
          ["store_id와 year별 sales 합계를 계산합니다. 세 상품을 모두 포함합니다.", "매장별 성장률 = (2025년 합계 − 2024년 합계) / 2024년 합계 × 100으로 구합니다.", "성장률이 가장 큰 매장 번호와 해당 성장률을 구합니다. 동률이면 store_id가 작은 매장을 선택합니다."],
          [f("annual_sales", "매장·연도·상품별 매출", ["store_id|정수|매장 번호 1~100", "year|정수|2024 또는 2025", "product|문자|상품 A, B, C", "sales|실수|매출(원)"])],
          [a("store_id", "성장률 1위 매장 번호", 0), a("growth_pct", "해당 매장 성장률(%)")],
          '''
          import pandas as pd
          df = pd.read_csv("data/annual_sales.csv")
          totals = df.pivot_table(index="store_id", columns="year", values="sales", aggfunc="sum").sort_index()
          growth = (totals[2025]-totals[2024])/totals[2024]*100
          best = growth.idxmax()
          answers = {"store_id": int(best), "growth_pct": round(float(growth.loc[best]), 3)}
          print(answers)
          ''',
          ["연도별 매출이 열로 배치되도록 pivot_table을 만들 수 있습니다.", "매장 내 상품별 성장률을 평균내지 말고 매장 총매출을 먼저 계산합니다."],
          "증가액 1위와 성장률 1위는 다를 수 있습니다. 2024년 합계를 분모로 사용하고 마지막에만 반올림합니다.", tags=["전년 대비", "피벗", "복합 집계"]),

        q("t1-27", "이메일 정규화와 중복 계정 분석",
          "이메일에 대소문자와 앞뒤 공백이 섞여 있고 같은 주소가 반복 저장되어 있습니다. 대소문자를 구분하지 않는 회사 계정을 집계합니다.",
          ["email의 앞뒤 공백을 제거하고 소문자로 변환합니다.", "공백이 없는 로컬명과 도메인이 @ 하나로 연결된 주소만 유효합니다. 정규식 [^@\\s]+@[^@\\s]+에 전체 문자열이 일치해야 합니다.", "정규화한 유효 이메일별로 CSV에서 처음 나타난 행만 남깁니다.", "도메인이 정확히 corp.co.kr인 계정 수와 해당 행들의 login_count 평균을 구합니다."],
          [f("accounts", "중복 이메일과 로그인 횟수", ["record_id|정수|기록 번호", "email|문자|대소문자·공백·잘못된 주소 포함", "login_count|정수|해당 기록의 로그인 횟수"])],
          [a("count", "정규화 후 회사 계정 수", 0), a("mean_logins", "해당 계정의 평균 로그인 횟수")],
          r'''
          import pandas as pd
          df = pd.read_csv("data/accounts.csv")
          df["normalized"] = df["email"].str.strip().str.lower()
          valid = df[df["normalized"].str.fullmatch(r"[^@\s]+@[^@\s]+", na=False)].drop_duplicates("normalized", keep="first")
          company = valid[valid["normalized"].str.endswith("@corp.co.kr")]
          answers = {"count": int(len(company)), "mean_logins": round(float(company["login_count"].mean()), 3)}
          print(answers)
          ''',
          ["공백 제거·소문자 변환을 중복 제거 전에 수행합니다.", "contains로 도메인 일부만 찾으면 다른 도메인이 포함될 수 있습니다."],
          "정규화 전 중복 제거는 같은 주소의 표기 차이를 제거하지 못합니다. 중복 기록의 로그인 횟수는 더하지 않고 첫 행의 값을 사용합니다.", tags=["문자열 정규화", "정규식", "중복 제거"]),

        q("t1-28", "7일 이동평균이 최대인 날",
          "2025년의 하루 한 건씩 기록한 전력 소비량입니다. 당일을 포함한 최근 7일 평균이 가장 높은 시점을 찾습니다.",
          ["date를 날짜로 변환하고 오름차순으로 정렬합니다.", "당일과 직전 6일의 consumption 평균을 계산합니다. 7개 행이 모두 있어야 하며 처음 6개 행은 제외합니다.", "이동평균이 최대인 날짜를 YYYYMMDD 정수로 제출하고 해당 이동평균을 구합니다. 동률이면 가장 이른 날짜를 선택합니다."],
          [f("energy", "연속된 일별 전력 소비량", ["date|날짜|관측 날짜", "consumption|실수|일별 소비량(kWh)"])],
          [a("date", "최대 이동평균 날짜 YYYYMMDD", 0), a("rolling_mean", "해당 날짜의 7일 이동평균")],
          '''
          import pandas as pd
          df = pd.read_csv("data/energy.csv")
          df["date"] = pd.to_datetime(df["date"])
          df = df.sort_values("date").reset_index(drop=True)
          rolling = df["consumption"].rolling(7, min_periods=7).mean()
          best = rolling.idxmax()
          answers = {"date": int(df.loc[best, "date"].strftime("%Y%m%d")), "rolling_mean": round(float(rolling.loc[best]), 3)}
          print(answers)
          ''',
          ["rolling의 center 기본값은 False라서 당일을 끝으로 한 과거 구간을 사용합니다.", "최초 6일에 짧은 구간 평균을 만들지 않도록 min_periods=7로 설정합니다."],
          "미래 6일을 포함하거나 centered 이동평균을 계산하는 조건이 아닙니다. 날짜순으로 정렬한 뒤 최댓값의 원래 날짜를 조회합니다.", tags=["이동평균", "시계열", "최댓값 날짜"]),

        q("t1-29", "고객별 누적 주문량의 최초 도달 시점",
          "고객별로 누적 주문량이 처음 100개 이상이 되는 주문을 찾습니다. 고객마다 주문 횟수와 날짜가 다릅니다.",
          ["각 고객의 주문을 ordered_at 오름차순, 같은 시각이면 order_id 오름차순으로 정렬합니다.", "고객별 quantity 누적합과 1부터 시작하는 주문 순번을 계산합니다.", "누적합이 처음 100 이상이 된 주문을 고객별 한 건만 선택합니다. 끝까지 도달하지 못한 고객은 제외합니다.", "도달 고객 수와 선택된 주문 순번의 평균을 구합니다."],
          [f("shipments", "고객별 주문 수량 이력", ["order_id|정수|주문 번호", "customer_id|정수|고객 번호", "ordered_at|날짜|주문 일시", "quantity|정수|해당 주문 수량"])],
          [a("customer_count", "누적 100개 도달 고객 수", 0), a("mean_order_number", "최초 도달 주문 순번의 평균")],
          '''
          import pandas as pd
          df = pd.read_csv("data/shipments.csv")
          df["ordered_at"] = pd.to_datetime(df["ordered_at"])
          df = df.sort_values(["customer_id", "ordered_at", "order_id"])
          df["cumulative"] = df.groupby("customer_id")["quantity"].cumsum()
          df["number"] = df.groupby("customer_id").cumcount()+1
          reached = df[df["cumulative"] >= 100].drop_duplicates("customer_id")
          answers = {"customer_count": int(len(reached)), "mean_order_number": round(float(reached["number"].mean()), 3)}
          print(answers)
          ''',
          ["전체 누적합이 아니라 고객별 cumsum을 사용하세요.", "100 이상인 모든 행을 평균내지 말고 각 고객의 첫 도달 행만 남겨야 합니다."],
          "CSV 행 순서나 전체 행 번호는 고객별 주문 순번이 아닙니다. 먼저 시간순으로 정렬한 뒤 그룹별 누적량과 순번을 계산합니다.", difficulty="중상", minutes=15, tags=["누적합", "cumcount", "최초 도달"]),

        q("t1-30", "왜도가 큰 금액 변수의 로그 변환",
          "세 금액 변수의 분포가 서로 다릅니다. 결측치를 제외한 표본 왜도로 가장 비대칭인 변수를 고르고 로그 변환 후 분산을 계산합니다.",
          ["amount_a·amount_b·amount_c 각각의 왜도를 pandas Series.skew 기본 방식으로 계산합니다. 열별 결측치는 제외합니다.", "왜도의 절댓값이 가장 큰 변수를 선택합니다. 동률이면 변수명 오름차순으로 선택합니다.", "선택한 변수의 원래 왜도는 부호를 유지하여 제출합니다.", "선택한 변수의 관측값만 남겨 np.log1p(x)를 적용하고 표본분산(ddof=1)을 구합니다."],
          [f("amounts", "세 종류 금액의 분포", ["id|정수|관측 번호", "amount_a|실수|금액 A, 양수·결측 포함", "amount_b|실수|금액 B, 양수·결측 포함", "amount_c|실수|금액 C, 양수·결측 포함"])],
          [a("skewness", "선택한 변수의 원래 왜도"), a("log_variance", "log1p 변환 후 표본분산")],
          '''
          import pandas as pd
          import numpy as np
          df = pd.read_csv("data/amounts.csv")
          skewness = df[["amount_a", "amount_b", "amount_c"]].skew().sort_index()
          selected = skewness.abs().idxmax()
          transformed = np.log1p(df[selected].dropna())
          answers = {"skewness": round(float(skewness[selected]), 3), "log_variance": round(float(transformed.var(ddof=1)), 3)}
          print(answers)
          ''',
          ["변수 선택에는 왜도의 절댓값, 제출에는 원래 부호가 있는 왜도를 사용합니다.", "log1p는 log(1+x)입니다. 원본 값의 분산과 구분하세요."],
          "pandas의 표본 왜도와 scipy의 기본 편향 왜도는 값이 다를 수 있습니다. 지정한 skew 함수를 쓰고 변환 후 표본분산을 계산합니다.", difficulty="중상", minutes=15, tags=["왜도", "로그 변환", "분산"]),
    ]
    problems += [
        prediction("t2-04", "퇴원 환자의 재입원 확률 예측",
          "환자의 입원 기간과 만성질환·과거 입원 이력으로 30일 이내 재입원 확률을 예측합니다. 수치·범주형 변수에 결측치가 있고 평가 자료에는 학습에서 보지 못한 퇴원 유형이 소수 포함됩니다.",
          ["age|실수|나이, 결측치 포함", "stay_days|실수|입원 일수, 결측치 포함", "prior_admissions|실수|과거 입원 횟수, 결측치 포함", "chronic_count|실수|만성질환 수, 결측치 포함", "discharge|문자|퇴원 유형 home, clinic, facility, other; 결측 포함", "followup|실수|후속 진료 예약 여부 0/1, 결측 포함"],
          "readmitted", "readmission_probability", "roc_auc", .76,
          'RandomForestClassifier(n_estimators=120, max_depth=9, min_samples_leaf=5, random_state=42, n_jobs=1)',
          'predictions = pipeline.predict_proba(test[X.columns])[:, list(pipeline.classes_).index(1)]',
          "재입원 1에 대한 확률을 제출합니다. 결측치를 대체한 뒤 범주형 변수를 인코딩하고, 평가 자료의 새 범주를 처리하도록 handle_unknown='ignore'를 지정합니다. 검증과 최종 평가 자료를 혼용하지 마세요."),

        prediction("t2-05", "중고차 판매 가격 회귀",
          "차량 연식·주행거리·브랜드·연료 정보를 이용해 중고차 판매 가격을 예측합니다. resale_price의 단위는 만 원이며 회귀 예측값을 원래 가격 단위로 제출합니다.",
          ["vehicle_age|실수|차량 연식(년), 결측 포함", "mileage_km|실수|주행거리(km), 결측 포함", "engine_cc|실수|배기량(cc), 결측 포함", "brand|문자|브랜드 A, B, C, D; 결측 포함", "fuel|문자|gas, diesel, hybrid; 결측 포함", "accidents|실수|사고 횟수, 결측 포함"],
          "resale_price", "predicted_price", "rmse", 340,
          'HistGradientBoostingRegressor(max_iter=140, max_leaf_nodes=15, l2_regularization=2, random_state=42)',
          'predictions = pipeline.predict(test[X.columns])',
          "식별자 id를 제외하고 수치형·범주형 전처리를 분리합니다. RMSE 340은 만 원 단위입니다. 가격을 정수 클래스로 분류하거나 학습 타깃을 평가 데이터에 합쳐 전처리하면 안 됩니다.", baseline=900),

        prediction("t2-06", "와인 품질 등급 다중분류",
          "와인의 화학 성분과 포도 유형으로 품질을 낮음(0), 보통(1), 높음(2)으로 분류합니다. 등급별 표본 수가 다르므로 Macro F1으로 세 등급을 같은 비중으로 평가합니다.",
          ["alcohol|실수|알코올 도수, 결측 포함", "acidity|실수|산도, 결측 포함", "residual_sugar|실수|잔당, 결측 포함", "sulphates|실수|황산염 지표, 결측 포함", "grape|문자|red, white, rose; 결측 포함", "region|문자|생산 지역 north, south, west; 결측 포함"],
          "quality_class", "quality_class", "macro_f1", .74,
          'RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=2, random_state=42, n_jobs=1)',
          'predictions = pipeline.predict(test[X.columns]).astype(int)',
          "확률 세 열이 아니라 예측한 등급 번호 한 열을 제출합니다. 품질 등급을 연속형으로 회귀한 뒤 반올림하기보다 분류 모델과 층화 검증으로 등급별 성능을 비교하세요.", class_description="0(낮음), 1(보통), 2(높음)"),

        prediction("t2-07", "마케팅 제안 응답 확률 예측",
          "고객의 이전 구매액과 최근 방문, 제안 할인율로 마케팅 제안에 응답할 확률을 예측합니다. responded=1은 응답이며 단순 정확도가 아닌 ROC AUC로 평가합니다.",
          ["previous_spend|실수|이전 구매액(달러), 결측 포함", "days_since_purchase|실수|마지막 구매 이후 일수, 결측 포함", "visits|실수|최근 방문 횟수, 결측 포함", "discount_pct|실수|제안 할인율(%), 결측 포함", "channel|문자|email, sms, app; 결측 포함", "device|문자|pc 또는 mobile, 결측 포함"],
          "responded", "response_probability", "roc_auc", .75,
          'RandomForestClassifier(n_estimators=120, max_depth=9, min_samples_leaf=5, random_state=42, n_jobs=1)',
          'predictions = pipeline.predict_proba(test[X.columns])[:, list(pipeline.classes_).index(1)]',
          "응답 확률의 순위가 평가 대상입니다. 임계값 0.5로 잘라 0/1 값만 제출하지 마세요. 검증에서는 동일한 y_valid에 대한 roc_auc_score를 사용하고 학습 데이터 전체 재학습 후 최종 확률을 만듭니다."),

        prediction("t2-08", "배달 완료 소요시간 예측",
          "배송 거리·교통 혼잡도·강수 여부로 배달 완료까지 걸리는 시간을 분 단위로 예측합니다. 숫자로 저장된 지표와 문자열 지역이 섞여 있고 결측치가 있습니다.",
          ["distance_km|실수|배송 거리(km), 결측 포함", "traffic_index|실수|혼잡도 0~1, 결측 포함", "weight_kg|실수|화물 무게(kg), 결측 포함", "rain|실수|강수 여부 0/1, 결측 포함", "zone|문자|central, east, west; 결측 포함", "hour|실수|출발 시각의 시(8~22), 결측 포함"],
          "duration_minutes", "predicted_minutes", "rmse", 7,
          'HistGradientBoostingRegressor(max_iter=140, max_leaf_nodes=15, l2_regularization=2, random_state=42)',
          'predictions = pipeline.predict(test[X.columns])',
          "RMSE의 단위는 분입니다. MSE와 RMSE를 혼동하지 말고 검증 오차의 제곱근을 계산하세요. hour와 rain은 이 기준 풀이에서는 수치형으로 처리하며, test의 열 순서를 학습 설명변수에 맞춥니다.", baseline=25),

        prediction("t2-09", "생산 설비 고장 확률 예측",
          "센서와 유지보수 기록으로 다음 점검 전 설비 고장 확률을 예측합니다. 고장 여부는 학습 데이터에만 있으며 센서값과 설비 유형에 결측치가 섞여 있습니다.",
          ["temperature|실수|운전 온도(℃), 결측 포함", "vibration|실수|진동 지표, 결측 포함", "operating_hours|실수|누적 운전시간, 결측 포함", "days_since_service|실수|정비 후 경과 일수, 결측 포함", "machine_type|문자|설비 유형 A, B, C; 결측 포함", "site|문자|east, west, south; 결측 포함"],
          "failed", "failure_probability", "roc_auc", .78,
          'RandomForestClassifier(n_estimators=120, max_depth=10, min_samples_leaf=4, random_state=42, n_jobs=1)',
          'predictions = pipeline.predict_proba(test[X.columns])[:, list(pipeline.classes_).index(1)]',
          "정상(0)이 아닌 고장(1)의 확률 열을 선택해야 합니다. 검증 AUC로 과적합을 확인하고, 센서 결측치는 학습 데이터에서 구한 대체값으로 처리합니다."),

        prediction("t2-10", "대출 고객 위험 등급 예측",
          "대출 고객의 신용 점수·부채 비율·연체 기록을 이용해 저위험(0), 중위험(1), 고위험(2) 등급을 예측합니다. 표본 분포와 결측치를 확인한 뒤 세 등급의 Macro F1을 개선하세요.",
          ["debt_ratio|실수|부채 비율 0~1, 결측 포함", "delinquencies|실수|연체 횟수, 결측 포함", "credit_score|실수|신용 점수, 결측 포함", "employment_years|실수|근속 연수, 결측 포함", "income|실수|연 소득(만원), 결측 포함", "residence|문자|own, rent, family; 결측 포함"],
          "risk_class", "risk_class", "macro_f1", .74,
          'RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=2, random_state=42, n_jobs=1)',
          'predictions = pipeline.predict(test[X.columns]).astype(int)',
          "신용 점수는 설명변수이고 예측 대상은 risk_class입니다. Macro F1은 클래스별 F1의 단순 평균이므로 다수 등급의 정확도만 높이는 전략을 주의하세요. 층화 검증으로 소수 등급도 확인합니다.", class_description="0(저위험), 1(중위험), 2(고위험)"),
    ]
    problems += [
        q("t3-04", "분산이 다른 두 교육 집단의 평균 비교",
          "독립적인 두 교육 집단 A·B의 시험 점수입니다. 일부 결측치가 있고 두 집단의 분산이 같다고 가정하지 않습니다. 유의수준은 0.05입니다.",
          ["집단별 score 결측치를 제외합니다. 서로 다른 사람의 점수이므로 대응 자료로 처리하지 않습니다.", "Levene 검정(center='median')의 p-value를 구합니다.", "A 점수, B 점수 순서로 양측 Welch 독립표본 t-검정(equal_var=False)을 수행하여 t 통계량과 p-value를 구합니다.", "반올림 전 Welch p-value가 0.05 미만이면 평균이 같다는 귀무가설 기각을 1, 아니면 0으로 제출합니다."],
          [f("results", "교육 집단과 시험 점수", ["id|정수|참가자 번호", "group|문자|독립 집단 A 또는 B", "score|실수|시험 점수, 결측치 포함"])],
          [a("levene_p", "Levene 검정 p-value", 6), a("t_stat", "Welch t 통계량(A − B)"), a("pvalue", "Welch 검정 p-value", 6), a("reject", "평균 동일 귀무가설 기각 여부", 0)],
          '''
          import pandas as pd
          from scipy import stats
          df = pd.read_csv("data/results.csv")
          x = df.loc[df["group"] == "A", "score"].dropna()
          y = df.loc[df["group"] == "B", "score"].dropna()
          levene = stats.levene(x, y, center="median")
          test = stats.ttest_ind(x, y, equal_var=False, alternative="two-sided")
          answers = {"levene_p": round(float(levene.pvalue), 6), "t_stat": round(float(test.statistic), 3), "pvalue": round(float(test.pvalue), 6), "reject": int(test.pvalue < 0.05)}
          print(answers)
          ''',
          ["같은 순번 행끼리 짝짓거나 두 집단을 합쳐 결측치를 제거하지 않습니다.", "Welch 검정은 ttest_ind의 equal_var=False이며 t 통계량의 부호는 입력 순서에 따릅니다."],
          "Levene은 분산의 동일성, Welch t-검정은 평균의 동일성을 다룹니다. 문제에서 Welch 방식을 지정했으므로 Levene 결과와 관계없이 equal_var=False를 사용합니다. 기각 여부는 반올림 전 p-value로 판단합니다.", minutes=20, tags=["Welch t-검정", "Levene", "기각 판단"]),

        q("t3-05", "유입 채널 분포의 카이제곱 적합도",
          "600명의 서비스 유입 채널이 과거 기준 분포와 같은지 검정합니다. 기준 비율은 검색 40%, 광고 30%, 직접 20%, 추천 10%이며 유의수준은 0.05입니다.",
          ["검색·광고·직접·추천 순서로 관측도수를 계산합니다.", "전체 관측 수에 기준 비율을 곱해 기대도수를 계산합니다.", "scipy.stats.chisquare로 적합도 검정을 수행하여 통계량과 p-value를 구합니다. 독립성 검정이 아닙니다.", "검정의 자유도와 반올림 전 p-value 기준 기각 여부(기각 1, 그 외 0)를 구합니다. 모수 추정에 따른 자유도 차감은 없습니다."],
          [f("acquisition", "고객별 최초 유입 채널", ["id|정수|고객 번호", "channel|문자|검색, 광고, 직접, 추천"])],
          [a("chi2", "카이제곱 적합도 통계량"), a("pvalue", "적합도 검정 p-value", 6), a("df", "자유도", 0), a("reject", "기각 여부", 0)],
          '''
          import pandas as pd
          import numpy as np
          from scipy import stats
          df = pd.read_csv("data/acquisition.csv")
          observed = df["channel"].value_counts().reindex(["검색", "광고", "직접", "추천"], fill_value=0)
          expected = len(df)*np.array([0.4, 0.3, 0.2, 0.1])
          test = stats.chisquare(observed, f_exp=expected)
          answers = {"chi2": round(float(test.statistic), 3), "pvalue": round(float(test.pvalue), 6), "df": int(len(observed)-1), "reject": int(test.pvalue < 0.05)}
          print(answers)
          ''',
          ["value_counts의 기본 빈도순 결과를 기대 비율 순서에 맞게 reindex하세요.", "기대 비율 자체가 아니라 기대도수 N×비율을 f_exp에 전달합니다."],
          "한 범주형 변수의 분포를 기준 비율과 비교하므로 적합도 검정을 사용합니다. chi2_contingency로 두 행의 비율을 교차표처럼 처리하면 다른 검정을 수행하게 됩니다.", minutes=20, tags=["카이제곱 적합도", "기대도수", "자유도"]),

        q("t3-06", "교육 시간의 단순회귀와 특정 값 예측",
          "교육 참가자의 교육 시간과 평가 점수를 분석합니다. 절편을 포함한 단순 OLS 회귀이며 id와 tenure는 설명변수로 사용하지 않습니다. 결측치는 없습니다.",
          ["score를 종속변수, hours만 설명변수로 하여 절편을 포함한 OLS 모형을 적합합니다.", "hours의 회귀계수와 해당 계수의 양측 p-value를 구합니다.", "모형의 결정계수 R²를 구합니다. 수정 결정계수가 아닙니다.", "hours=40인 참가자의 예측 점수를 구합니다. 예측 구간이나 신뢰구간이 아닌 예측 평균값을 제출합니다."],
          [f("training", "교육 시간과 평가 점수", ["id|정수|참가자 번호", "hours|실수|교육 시간", "tenure|정수|근속 연수(모형에서 제외)", "score|실수|교육 후 평가 점수"])],
          [a("coefficient", "hours 회귀계수"), a("pvalue", "hours 계수 p-value", 6), a("r_squared", "결정계수 R²"), a("prediction", "교육 시간 40의 예측 점수")],
          '''
          import pandas as pd
          import statsmodels.api as sm
          df = pd.read_csv("data/training.csv")
          model = sm.OLS(df["score"], sm.add_constant(df[["hours"]])).fit()
          new = pd.DataFrame({"const": [1.0], "hours": [40.0]})
          predicted = model.predict(new).iloc[0]
          answers = {"coefficient": round(float(model.params["hours"]), 3), "pvalue": round(float(model.pvalues["hours"]), 6), "r_squared": round(float(model.rsquared), 3), "prediction": round(float(predicted), 3)}
          print(answers)
          ''',
          ["statsmodels는 절편을 자동으로 넣지 않으므로 학습 설계행렬에 상수 열을 추가합니다.", "한 행을 예측할 때도 학습과 같은 const·hours 열과 열 순서를 준비하세요."],
          "회귀계수는 교육 시간이 1시간 증가할 때의 평균 점수 변화량입니다. 단일 행에 add_constant를 기본값으로 적용하면 상수 열이 추가되지 않을 수 있으므로 예측 설계행렬을 명시합니다.", minutes=20, tags=["단순 OLS", "회귀계수", "새 관측 예측"]),

        q("t3-07", "생활습관 로지스틱 회귀와 특이도",
          "건강검진 자료에서 나이·주간 운동·흡연 여부로 질환 발생 확률을 추정합니다. 벌점화하지 않은 로지스틱 회귀이며 절편을 포함합니다. id와 sugar는 모형에서 제외합니다.",
          ["age, exercise와 흡연 Yes 더미변수로 outcome을 예측하는 statsmodels.Logit 모형을 적합합니다. 흡연 기준 범주는 No입니다.", "같은 나이·운동량에서 흡연 Yes의 오즈비와 해당 계수의 양측 p-value를 구합니다.", "나이 40, 주간 운동 3회, 흡연 Yes인 사람의 outcome=1 예측 확률을 구합니다.", "전체 관측에서 예측 확률이 0.4 이상이면 양성으로 판정합니다. 특이도 TN/(TN+FP)를 구합니다."],
          [f("lifestyle", "생활습관과 질환 발생", ["id|정수|대상자 번호", "age|정수|나이", "exercise|정수|주간 운동 횟수", "smoker|문자|No 또는 Yes", "sugar|실수|참고용 혈당(모형에서 제외)", "outcome|정수|질환 발생 1, 미발생 0"])],
          [a("odds_ratio", "흡연 Yes의 오즈비"), a("pvalue", "흡연 Yes 계수 p-value", 6), a("probability", "지정 조건의 질환 발생 확률"), a("specificity", "임계값 0.4의 특이도")],
          '''
          import pandas as pd
          import numpy as np
          import statsmodels.api as sm
          df = pd.read_csv("data/lifestyle.csv")
          X = pd.DataFrame({"age": df["age"].astype(float), "exercise": df["exercise"].astype(float), "smoker_yes": (df["smoker"] == "Yes").astype(float)})
          design = sm.add_constant(X)
          model = sm.Logit(df["outcome"], design).fit(disp=False)
          probability = model.predict(design)
          new = pd.DataFrame({"const": [1.0], "age": [40.0], "exercise": [3.0], "smoker_yes": [1.0]})
          specificity = ((probability < 0.4) & (df["outcome"] == 0)).sum()/(df["outcome"] == 0).sum()
          answers = {"odds_ratio": round(float(np.exp(model.params["smoker_yes"])), 3), "pvalue": round(float(model.pvalues["smoker_yes"]), 6), "probability": round(float(model.predict(new).iloc[0]), 3), "specificity": round(float(specificity), 3)}
          print(answers)
          ''',
          ["오즈비는 exp(계수)이며, 기준 범주 No와 비교한 값입니다.", "특이도의 분모는 실제 음성인 관측 수입니다. 민감도나 정확도와 구분하세요."],
          "비벌점 조건을 맞추기 위해 Logit을 사용합니다. 특이도는 실제 미발생자 중 음성으로 판정한 비율이며 판정 경계 0.4는 양성에 포함합니다.", difficulty="상", minutes=25, tags=["로지스틱 회귀", "오즈비", "특이도"]),

        q("t3-08", "전환율의 단측 두 비율 검정",
          "서로 독립적인 A·B 화면 실험의 구매 전환 여부입니다. B의 전환율이 A보다 큰지 유의수준 0.05에서 검정하고 B의 전환율 신뢰구간을 구합니다.",
          ["집단별 전환 성공 수와 전체 관측 수를 계산합니다. converted=1이 성공입니다.", "B, A 순서로 성공 수와 관측 수 배열을 전달하여 statsmodels.stats.proportion.proportions_ztest를 수행합니다. alternative='larger'이며 value=0입니다.", "검정 z 통계량, 단측 p-value와 B 전환율 − A 전환율을 구합니다. 비율 차이는 백분율로 바꾸지 않습니다.", "B 전환율의 95% Wilson 신뢰구간(method='wilson')의 하한을 구합니다."],
          [f("experiment", "화면 실험의 전환 결과", ["id|정수|참여자 번호", "group|문자|실험 집단 A 또는 B", "converted|정수|전환 성공 1, 실패 0"])],
          [a("z_stat", "두 비율 z 통계량(B − A)"), a("pvalue", "B가 더 크다는 단측 p-value", 6), a("difference", "B 전환율 − A 전환율"), a("ci_lower", "B 전환율 Wilson 95% 하한")],
          '''
          import pandas as pd
          from statsmodels.stats.proportion import proportions_ztest, proportion_confint
          df = pd.read_csv("data/experiment.csv")
          table = df.groupby("group")["converted"].agg(["sum", "count"])
          count = table.loc[["B", "A"], "sum"].to_numpy()
          nobs = table.loc[["B", "A"], "count"].to_numpy()
          z, p = proportions_ztest(count, nobs, value=0, alternative="larger")
          lower, upper = proportion_confint(count[0], nobs[0], alpha=0.05, method="wilson")
          answers = {"z_stat": round(float(z), 3), "pvalue": round(float(p), 6), "difference": round(float(count[0]/nobs[0]-count[1]/nobs[1]), 3), "ci_lower": round(float(lower), 3)}
          print(answers)
          ''',
          ["검정 순서 B, A와 단측 방향 larger를 함께 맞추세요.", "신뢰구간은 비율 차이의 구간이 아니라 B 집단 전환율 하나의 구간입니다."],
          "proportions_ztest에 원자료 0/1 배열을 직접 넣지 않고 집단별 성공 수와 표본 수를 전달합니다. 정규근사 Wald 구간이 아니라 지정한 Wilson 구간을 사용합니다.", difficulty="중상", minutes=25, tags=["두 비율 z검정", "단측 검정", "Wilson 신뢰구간"]),

        q("t3-09", "결측치가 있는 자료의 순위 상관",
          "학습 시간과 시험 점수가 직선 관계가 아닐 수 있어 순위 상관과 선형 상관을 비교합니다. 일부 관측은 한쪽 값이 누락되어 있습니다.",
          ["study_hours와 score가 모두 관측된 행만 선택합니다. id는 분석에서 제외합니다.", "해당 두 변수로 양측 Spearman 순위 상관 검정을 수행합니다.", "유효 행 수, Spearman 상관계수와 p-value를 구합니다.", "같은 유효 행에서 Pearson 상관계수도 구합니다. 모든 상관계수는 부호를 유지합니다."],
          [f("study", "학습 시간과 시험 점수", ["id|정수|학습자 번호", "study_hours|실수|주간 학습 시간, 결측 포함", "score|실수|시험 점수, 결측 포함"])],
          [a("count", "두 변수가 모두 관측된 행 수", 0), a("spearman", "Spearman 상관계수"), a("pvalue", "Spearman 양측 p-value", 6), a("pearson", "같은 행의 Pearson 상관계수")],
          '''
          import pandas as pd
          from scipy import stats
          df = pd.read_csv("data/study.csv")[["study_hours", "score"]].dropna()
          rank = stats.spearmanr(df["study_hours"], df["score"], alternative="two-sided")
          linear = stats.pearsonr(df["study_hours"], df["score"])
          answers = {"count": int(len(df)), "spearman": round(float(rank.statistic), 3), "pvalue": round(float(rank.pvalue), 6), "pearson": round(float(linear.statistic), 3)}
          print(answers)
          ''',
          ["두 열을 각각 dropna한 뒤 배열로 합치면 다른 사람의 값을 잘못 짝지을 수 있습니다.", "Spearman은 순위의 단조 관계, Pearson은 선형 관계를 측정합니다."],
          "관측 쌍을 보존해 두 열 모두 완전한 행을 먼저 선택합니다. 상관계수 두 종류의 차이를 이해하고 id를 수치형 설명변수로 함께 계산하지 않습니다.", minutes=20, tags=["Spearman", "Pearson", "쌍별 결측치"]),

        q("t3-10", "설명변수 추가에 따른 회귀모형 개선",
          "매장의 면적·직원 수·광고비로 매출을 설명합니다. 광고비를 추가했을 때 모형이 유의하게 개선되는지 중첩 OLS 모형의 F검정으로 확인합니다. 모든 모형에 절편을 포함합니다.",
          ["축소모형은 sales ~ area + staff, 전체모형은 sales ~ area + staff + ad_spend로 적합합니다. id는 제외합니다.", "statsmodels.stats.anova.anova_lm(축소모형, 전체모형)으로 두 모형을 순서대로 비교합니다.", "광고비 추가에 대한 부분 F 통계량과 p-value를 구합니다.", "전체모형의 수정 결정계수(adjusted R²)와 ad_spend의 회귀계수를 구합니다. 단순 R²가 아닙니다."],
          [f("stores", "매장 규모·광고비·매출", ["id|정수|매장 번호", "area|실수|매장 면적(㎡)", "staff|정수|직원 수", "ad_spend|실수|광고비(만원)", "sales|실수|매출(만원)"])],
          [a("f_stat", "광고비 추가의 부분 F 통계량"), a("pvalue", "모형 비교 p-value", 6), a("adjusted_r2", "전체모형의 수정 결정계수"), a("coefficient", "전체모형 광고비 계수")],
          '''
          import pandas as pd
          import statsmodels.formula.api as smf
          from statsmodels.stats.anova import anova_lm
          df = pd.read_csv("data/stores.csv")
          reduced = smf.ols("sales ~ area + staff", data=df).fit()
          full = smf.ols("sales ~ area + staff + ad_spend", data=df).fit()
          comparison = anova_lm(reduced, full)
          answers = {"f_stat": round(float(comparison.iloc[1]["F"]), 3), "pvalue": round(float(comparison.iloc[1]["Pr(>F)"]), 6), "adjusted_r2": round(float(full.rsquared_adj), 3), "coefficient": round(float(full.params["ad_spend"]), 3)}
          print(answers)
          ''',
          ["formula API는 기본적으로 절편을 포함합니다. 모형 비교에는 축소모형을 먼저 넣습니다.", "전체모형 전체의 F 통계량과 광고비 한 변수를 추가한 부분 F 검정은 구분해야 합니다."],
          "추가 변수의 설명력을 다른 변수들을 통제한 상태에서 평가합니다. anova_lm 비교표의 두 번째 행을 사용하고, 수정 결정계수는 rsquared_adj로 조회합니다.", difficulty="상", minutes=25, tags=["중첩 OLS", "부분 F검정", "수정 결정계수"]),
    ]
    return problems
