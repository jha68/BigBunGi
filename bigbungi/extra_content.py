"""Thirty-four original exercises extending the existing exam-style contracts."""


def additional_problems(q, f, a, prediction):
    problems = [
        q(
            "t1-11",
            "사용자별 최신 기록의 평균 접속시간",
            "sessions.csv는 사용자 상태가 변경될 때마다 저장한 접속 이력이다.",
            [
                "사용자별로 updated_at이 가장 늦은 기록 한 건만 남기시오. 같은 시각의 기록은 record_id가 큰 것을 남긴다.",
                "남은 기록 중 status가 active인 사용자의 minutes 평균을 구하시오.",
            ],
            [
                f("sessions", "사용자 상태 수정 이력", [
                    "record_id|정수|중복 없는 기록 번호",
                    "user_id|정수|사용자 번호",
                    "updated_at|날짜|기록 수정 일시",
                    "status|문자|active 또는 inactive",
                    "minutes|실수|접속시간(분)",
                ]),
            ],
            [
                a("mean_minutes", "해당 사용자의 평균 접속시간", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/sessions.csv')
            df['updated_at'] = pd.to_datetime(df['updated_at'])
            latest = df.sort_values(['updated_at', 'record_id'], ascending=[False, False]).drop_duplicates('user_id')
            active = latest[latest['status'] == 'active']
            answers = {'mean_minutes': round(float(active['minutes'].mean()), 3)}
            print(answers)
            ''',
            [
                "최신 행을 먼저 고르고 나서 활성 여부를 확인합니다.",
                "전체 이력에서 최신 행을 고른 뒤 활성 여부를 판단합니다. 활성 행만 먼저 선택하면 최신 상태가 반영되지 않습니다.",
            ],
            "전체 이력에서 최신 행을 고른 뒤 활성 여부를 판단합니다. 활성 행만 먼저 선택하면 최신 상태가 반영되지 않습니다.",
            difficulty="중",
            minutes=12,
            tags=["중복 제거", "날짜", "정렬"],
        ),

        q(
            "t1-12",
            "부서별 결측치 대체 후 성과급 합계",
            "employees.csv는 직원의 부서, 성과급, 평가 점수 자료이다.",
            [
                "bonus의 결측치를 원본 자료의 같은 부서 bonus 중앙값으로 대체하시오.",
                "대체 후 rating이 3.5 이상인 직원의 bonus 합계를 구하시오.",
            ],
            [
                f("employees", "직원별 부서·성과급·평가", [
                    "id|정수|직원 번호",
                    "department|문자|소속 부서",
                    "bonus|실수|성과급(만원), 결측치 포함",
                    "rating|실수|평가 점수(1~5)",
                ]),
            ],
            [
                a("total_bonus", "고평가 직원의 대체 후 성과급 합계", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/employees.csv')
            medians = df.groupby('department')['bonus'].transform('median')
            df['bonus'] = df['bonus'].fillna(medians)
            selected = df[df['rating'] >= 3.5]
            answers = {'total_bonus': round(float(selected['bonus'].sum()), 3)}
            print(answers)
            ''',
            [
                "부서별 대체값은 rating 조건을 적용하기 전에 계산합니다.",
                "부서별 중앙값은 평가 점수로 행을 제외하기 전에 계산합니다. groupby와 transform을 이용하면 원래 행 순서대로 대체할 수 있습니다.",
            ],
            "부서별 중앙값은 평가 점수로 행을 제외하기 전에 계산합니다. groupby와 transform을 이용하면 원래 행 순서대로 대체할 수 있습니다.",
            difficulty="중",
            minutes=12,
            tags=["그룹별 결측치", "transform", "합계"],
        ),

        q(
            "t1-13",
            "결측 비율에 따른 열 제거 후 평균",
            "quality.csv는 다섯 측정 항목 k1~k5의 관측 자료이다.",
            [
                "원본 자료에서 결측 비율이 20%를 초과하는 측정 열을 제거하고, 남은 측정 열에 결측치가 있는 행을 제거하시오. id는 측정 열이 아니다.",
                "최종 자료의 k5 평균을 구하시오.",
            ],
            [
                f("quality", "품질 측정값", [
                    "id|정수|측정 번호",
                    "k1|실수|측정 항목 1",
                    "k2|실수|측정 항목 2",
                    "k3|실수|측정 항목 3",
                    "k4|실수|측정 항목 4",
                    "k5|실수|측정 항목 5",
                ]),
            ],
            [
                a("mean_k5", "완전 사례의 k5 평균", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/quality.csv')
            columns = ['k1', 'k2', 'k3', 'k4', 'k5']
            kept = df[columns].isna().mean().loc[lambda x: x <= 0.2].index
            complete = df.dropna(subset=kept)
            answers = {'mean_k5': round(float(complete['k5'].mean()), 3)}
            print(answers)
            ''',
            [
                "열을 제거하는 단계와 행을 제거하는 단계를 구분하세요.",
                "열별 결측 비율은 원본 행 수를 기준으로 구합니다. 남길 측정 열이 정해진 뒤 해당 열들의 완전 사례를 선택합니다.",
            ],
            "열별 결측 비율은 원본 행 수를 기준으로 구합니다. 남길 측정 열이 정해진 뒤 해당 열들의 완전 사례를 선택합니다.",
            difficulty="중",
            minutes=12,
            tags=["결측 비율", "열 제거", "완전 사례"],
        ),

        q(
            "t1-14",
            "분위수 경계 보정 후 표준편차",
            "readings.csv는 결측치와 극단값이 포함된 측정 자료이다.",
            [
                "value의 결측치를 제외하고 10백분위수와 90백분위수를 구하시오. 분위수 보간은 pandas 기본 방식으로 한다.",
                "하한 미만의 값은 하한으로, 상한 초과의 값은 상한으로 대체한 후 value의 모집단 표준편차를 구하시오. 결측치는 계산에서 제외한다.",
            ],
            [
                f("readings", "극단값·결측치가 있는 측정값", [
                    "id|정수|측정 번호",
                    "value|실수|측정값, 결측치 포함",
                ]),
            ],
            [
                a("std_population", "보정 후 모집단 표준편차", 3),
            ],
            '''
            import pandas as pd
            x = pd.read_csv('data/readings.csv')['value']
            low, high = x.quantile([0.1, 0.9])
            corrected = x.clip(lower=low, upper=high)
            answers = {'std_population': round(float(corrected.std(ddof=0)), 3)}
            print(answers)
            ''',
            [
                "보정 전 원본에서 분위수 경계를 구합니다.",
                "clip으로 경계 밖의 값만 보정하고 std(ddof=0)으로 모집단 표준편차를 계산합니다. 분위수는 보정 전 자료에서 구합니다.",
            ],
            "clip으로 경계 밖의 값만 보정하고 std(ddof=0)으로 모집단 표준편차를 계산합니다. 분위수는 보정 전 자료에서 구합니다.",
            difficulty="중",
            minutes=12,
            tags=["분위수", "clip", "ddof"],
        ),

        q(
            "t1-15",
            "문자형 금액 정제 후 결제액 합계",
            "payments.csv의 amount에는 쉼표와 원 단위가, discount에는 % 기호가 포함되어 있다.",
            [
                "channel이 온라인이고 status가 결제인 거래의 할인 적용 후 금액 합계를 구하시오.",
                "amount는 할인 전 금액이고 discount는 할인율(%)이다. 거래별 중간 반올림은 하지 않는다.",
            ],
            [
                f("payments", "문자열 금액과 할인율", [
                    "id|정수|결제 번호",
                    "amount|문자|쉼표·원 단위가 포함된 금액",
                    "discount|문자|퍼센트 문자열",
                    "channel|문자|온라인 또는 매장",
                    "status|문자|결제 또는 취소",
                ]),
            ],
            [
                a("net_sales", "할인 후 온라인 결제액 합계", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/payments.csv')
            amount = df['amount'].str.replace(',', '', regex=False).str.replace('원', '', regex=False).astype(float)
            rate = df['discount'].str.replace('%', '', regex=False).astype(float) / 100
            mask = (df['channel'] == '온라인') & (df['status'] == '결제')
            answers = {'net_sales': round(float((amount[mask] * (1 - rate[mask])).sum()), 3)}
            print(answers)
            ''',
            [
                "통화 기호와 %를 제거한 뒤 수치형으로 변환하세요.",
                "문자형 금액과 할인율을 수치로 바꿉니다. 할인율을 100으로 나눈 비율을 이용해 금액을 계산한 뒤 합산합니다.",
            ],
            "문자형 금액과 할인율을 수치로 바꿉니다. 할인율을 100으로 나눈 비율을 이용해 금액을 계산한 뒤 합산합니다.",
            difficulty="중",
            minutes=12,
            tags=["문자열 정제", "형 변환", "할인율"],
        ),

        q(
            "t1-16",
            "평일 출고 건의 배송 지연 수",
            "parcels.csv는 상품의 출고 일시와 도착 일시 자료이다.",
            [
                "월요일부터 금요일 사이에 출고된 상품 중 배송 소요시간이 48시간을 초과하는 건수를 정수로 구하시오.",
                "소요시간은 도착 일시와 출고 일시의 차이이며, 출고일 기준 요일을 사용한다. 공휴일은 고려하지 않는다.",
            ],
            [
                f("parcels", "출고와 도착 시각", [
                    "id|정수|배송 번호",
                    "shipped_at|날짜|출고 일시",
                    "arrived_at|날짜|도착 일시",
                ]),
            ],
            [
                a("late_count", "48시간 초과 배송 수", 0),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/parcels.csv')
            sent = pd.to_datetime(df['shipped_at'])
            arrived = pd.to_datetime(df['arrived_at'])
            hours = ((arrived - sent).dt.total_seconds() / 3600)[sent.dt.dayofweek < 5]
            answers = {'late_count': int((hours > 48).sum())}
            print(answers)
            ''',
            [
                "출고 요일과 두 일시 사이의 전체 경과시간을 사용하세요.",
                "출고 일시의 dayofweek로 평일을 선택합니다. 일시 차이의 total_seconds를 시간으로 환산하여 48시간과 비교합니다.",
            ],
            "출고 일시의 dayofweek로 평일을 선택합니다. 일시 차이의 total_seconds를 시간으로 환산하여 48시간과 비교합니다.",
            difficulty="중",
            minutes=12,
            tags=["날짜 차이", "요일", "중앙값"],
        ),

        q(
            "t1-17",
            "월 매출의 전월 대비 최대 증가율",
            "retail.csv는 2024년부터 2025년까지의 일별 매출 자료이다.",
            [
                "연·월별 revenue 합계를 구한 후 전월 대비 증가율(%)의 최댓값을 구하시오.",
                "증가율은 (이번 달 매출 / 전월 매출 − 1) × 100으로 한다. 비교할 전월이 없는 첫 달은 제외하며, 연도가 바뀌어도 전월을 이어서 비교한다.",
            ],
            [
                f("retail", "18개월의 일별 매출", [
                    "date|날짜|매출 발생일",
                    "revenue|실수|일 매출(원)",
                ]),
            ],
            [
                a("growth_pct", "전월 대비 증가율(%)", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/retail.csv')
            month = pd.to_datetime(df['date']).dt.to_period('M')
            monthly = df.groupby(month)['revenue'].sum().sort_index()
            growth = (monthly / monthly.shift(1) - 1) * 100
            best = growth.dropna().idxmax()
            answers = {'growth_pct': round(float(growth.loc[best]), 3)}
            print(answers)
            ''',
            [
                "일별 증가율이 아니라 월별 합계의 증가율입니다.",
                "연·월을 함께 사용해 집계하고 시간순으로 정렬합니다. 월 합계에 shift를 적용해야 일별 증가율 평균과 혼동하지 않습니다.",
            ],
            "연·월을 함께 사용해 집계하고 시간순으로 정렬합니다. 월 합계에 shift를 적용해야 일별 증가율 평균과 혼동하지 않습니다.",
            difficulty="중상",
            minutes=12,
            tags=["월 집계", "shift", "증가율"],
        ),

        q(
            "t1-18",
            "지역별 상위 참가자의 평균 점수",
            "rankings.csv는 지역별 대회 참가자의 점수 자료이다.",
            [
                "각 지역에서 score가 높은 순서로 3명씩 선정하고 선정된 전체 참가자의 score 평균을 구하시오.",
                "점수가 같으면 id가 작은 참가자를 우선 선정하며, 동점자를 추가로 포함하지 않는다.",
            ],
            [
                f("rankings", "참가자의 지역과 점수", [
                    "id|정수|참가자 번호",
                    "region|문자|참가 지역",
                    "score|정수|획득 점수",
                ]),
            ],
            [
                a("mean_score", "선정 참가자의 평균 점수", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/rankings.csv')
            selected = df.sort_values(['region', 'score', 'id'], ascending=[True, False, True]).groupby('region').head(3)
            answers = {'mean_score': round(float(selected['score'].mean()), 3)}
            print(answers)
            ''',
            [
                "정렬 후 지역별로 정확히 세 행씩 선택합니다.",
                "지역·점수·id 순서로 정렬한 뒤 지역별 head(3)을 선택합니다. 지역별 평균의 단순 평균이 아니라 선정된 모든 행의 평균을 구합니다.",
            ],
            "지역·점수·id 순서로 정렬한 뒤 지역별 head(3)을 선택합니다. 지역별 평균의 단순 평균이 아니라 선정된 모든 행의 평균을 구합니다.",
            difficulty="중",
            minutes=12,
            tags=["그룹별 상위", "동률", "정렬"],
        ),

        q(
            "t1-19",
            "온라인 매출 비중이 가장 큰 매장",
            "channels.csv는 매장별 온라인·오프라인 판매 기록이다.",
            [
                "매장별 전체 매출 중 온라인 매출이 차지하는 비율이 가장 큰 store_id를 정수로 구하시오.",
                "매출액은 sales를 사용한다. 비율이 같으면 store_id가 작은 매장을 선택한다.",
            ],
            [
                f("channels", "매장·채널별 거래", [
                    "id|정수|거래 번호",
                    "store_id|정수|매장 번호",
                    "channel|문자|온라인 또는 오프라인",
                    "sales|정수|매출(원)",
                ]),
            ],
            [
                a("store_id", "온라인 매출 비중 1위 매장", 0),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/channels.csv')
            pivot = df.pivot_table(index='store_id', columns='channel', values='sales', aggfunc='sum', fill_value=0)
            rates = (pivot['온라인'] / (pivot['온라인'] + pivot['오프라인']) * 100).sort_index()
            best = rates.idxmax()
            answers = {'store_id': int(best)}
            print(answers)
            ''',
            [
                "판매 건수가 아니라 sales 합계의 비율입니다.",
                "매장·채널별 매출을 합산한 후 온라인 매출을 온라인·오프라인 합계로 나눕니다. 비율 계산 전 반올림하지 않습니다.",
            ],
            "매장·채널별 매출을 합산한 후 온라인 매출을 온라인·오프라인 합계로 나눕니다. 비율 계산 전 반올림하지 않습니다.",
            difficulty="중",
            minutes=12,
            tags=["피벗", "매출 비중", "동률"],
        ),

        q(
            "t1-20",
            "거래처 정보가 없는 매입 건수",
            "purchases.csv는 매입 내역이고 suppliers.csv는 등록된 거래처 목록이다. suppliers의 supplier_id는 유일하다.",
            [
                "매입 내역 중 등록된 거래처 목록에 supplier_id가 없는 행의 개수를 정수로 구하시오.",
                "거래처의 고유 개수가 아니라 해당 매입 행의 개수를 제출한다.",
            ],
            [
                f("suppliers", "등록 거래처 마스터", [
                    "supplier_id|정수|중복 없는 거래처 번호",
                    "grade|문자|거래처 등급 A, B, C",
                ]),
                f("purchases", "매입·입고 기록", [
                    "purchase_id|정수|매입 번호",
                    "supplier_id|정수|거래처 번호",
                    "cost|정수|매입액(원)",
                    "status|문자|입고 또는 대기",
                ]),
            ],
            [
                a("unmatched", "미등록 거래처의 매입 행 수", 0),
            ],
            '''
            import pandas as pd
            orders = pd.read_csv('data/purchases.csv')
            suppliers = pd.read_csv('data/suppliers.csv')
            merged = orders.merge(suppliers, on='supplier_id', how='left', validate='many_to_one', indicator=True)
            answers = {'unmatched': int((merged['_merge'] == 'left_only').sum())}
            print(answers)
            ''',
            [
                "등록 목록에 없는 supplier_id를 가진 매입 행을 셉니다.",
                "매입 내역을 기준으로 왼쪽 결합한 뒤 매칭되지 않은 행을 셉니다. isin으로 등록 여부를 검사해도 같은 답을 얻습니다.",
            ],
            "매입 내역을 기준으로 왼쪽 결합한 뒤 매칭되지 않은 행을 셉니다. isin으로 등록 여부를 검사해도 같은 답을 얻습니다.",
            difficulty="중",
            minutes=12,
            tags=["left join", "미매칭", "조건 집계"],
        ),
    ]
    problems += [
        q(
            "t1-21",
            "재고 수량을 반영한 가중평균 단가",
            "inventory.csv는 품목별 단가와 재고 수량 자료이다.",
            [
                "quantity가 0보다 크고 unit_price가 결측이 아닌 품목을 대상으로, quantity를 가중치로 한 unit_price의 가중평균을 구하시오.",
            ],
            [
                f("inventory", "품목별 재고와 단가", [
                    "id|정수|품목 번호",
                    "unit_price|실수|개당 가격(원), 결측치 포함",
                    "quantity|정수|재고 개수, 0 포함",
                ]),
            ],
            [
                a("weighted_price", "재고 가중평균 단가", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/inventory.csv')
            valid = df[(df['quantity'] > 0) & df['unit_price'].notna()]
            total = valid['quantity'].sum()
            mean = (valid['unit_price'] * valid['quantity']).sum() / total
            answers = {'weighted_price': round(float(mean), 3)}
            print(answers)
            ''',
            [
                "단가와 수량의 곱의 합을 수량 합으로 나눕니다.",
                "유효한 행에서 단가와 수량의 곱을 합산하고, 같은 행들의 수량 합계로 나눕니다. 단가의 단순 평균과 다릅니다.",
            ],
            "유효한 행에서 단가와 수량의 곱을 합산하고, 같은 행들의 수량 합계로 나눕니다. 단가의 단순 평균과 다릅니다.",
            difficulty="중",
            minutes=12,
            tags=["가중평균", "결측치", "조건 필터링"],
        ),

        q(
            "t1-22",
            "완료 주문 고객의 재구매율",
            "orders.csv는 고객별 주문 내역이며, 완료와 취소 상태가 함께 저장되어 있다.",
            [
                "완료 주문이 한 건 이상인 고객 중 완료 주문이 두 건 이상인 고객의 비율(%)을 구하시오.",
                "분모와 분자는 모두 중복을 제거한 고객 수로 계산한다. 취소 주문은 사용하지 않는다.",
            ],
            [
                f("orders", "고객의 완료·취소 주문", [
                    "id|정수|중복 없는 주문 번호",
                    "customer_id|정수|고객 번호",
                    "status|문자|완료 또는 취소",
                    "amount|정수|주문액(원)",
                ]),
            ],
            [
                a("repeat_pct", "완료 고객 기준 재구매율(%)", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/orders.csv')
            counts = df.loc[df['status'] == '완료'].groupby('customer_id').size()
            repeat = (counts >= 2).sum()
            answers = {'repeat_pct': round(float(repeat / len(counts) * 100), 3)}
            print(answers)
            ''',
            [
                "완료 주문만 남긴 뒤 고객별 주문 건수를 구합니다.",
                "완료 주문만 고객별로 집계합니다. 두 건 이상인 고객 수를 완료 주문 고객 수로 나누고 100을 곱합니다.",
            ],
            "완료 주문만 고객별로 집계합니다. 두 건 이상인 고객 수를 완료 주문 고객 수로 나누고 100을 곱합니다.",
            difficulty="중",
            minutes=12,
            tags=["고객별 집계", "재구매율", "고유 개수"],
        ),

        q(
            "t1-23",
            "채팅 상담의 환불 비율",
            "claims.csv는 상담 채널과 환불 여부 자료이다. refunded가 1이면 환불, 0이면 미환불이다.",
            [
                "채팅 채널의 전체 상담 중 환불 처리된 상담의 비율(%)을 구하시오.",
            ],
            [
                f("claims", "상담 채널과 환불 처리 여부", [
                    "id|정수|상담 번호",
                    "channel|문자|전화, 채팅, 이메일",
                    "refunded|정수|환불 1, 미환불 0",
                ]),
            ],
            [
                a("refund_pct", "채팅 상담 환불 비율(%)", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/claims.csv')
            table = pd.crosstab(df['channel'], df['refunded'])
            total = table.loc['채팅'].sum()
            answers = {'refund_pct': round(float(table.loc['채팅', 1] / total * 100), 3)}
            print(answers)
            ''',
            [
                "분모는 채팅 상담 건수입니다.",
                "분모는 전체 상담 수가 아니라 채팅 상담 수입니다. 교차표 또는 채팅 행의 refunded 평균으로 계산할 수 있습니다.",
            ],
            "분모는 전체 상담 수가 아니라 채팅 상담 수입니다. 교차표 또는 채팅 행의 refunded 평균으로 계산할 수 있습니다.",
            difficulty="중",
            minutes=12,
            tags=["교차표", "행 정규화", "백분율"],
        ),

        q(
            "t1-24",
            "음의 상관관계가 가장 큰 변수의 표준편차",
            "laboratory.csv는 네 가지 측정 항목과 생산 수율 자료이다.",
            [
                "chem_a~chem_d 중 yield_score와의 Pearson 상관계수가 가장 작은 변수를 선택하시오. 각 상관계수는 해당 두 값이 모두 있는 행으로 계산한다.",
                "선택한 변수와 yield_score가 모두 관측된 행에서 선택한 변수의 표본 표준편차를 구하시오.",
            ],
            [
                f("laboratory", "화학 측정과 수율", [
                    "id|정수|실험 번호",
                    "chem_a|실수|측정값 A, 결측치 포함",
                    "chem_b|실수|측정값 B, 결측치 포함",
                    "chem_c|실수|측정값 C, 결측치 포함",
                    "chem_d|실수|측정값 D, 결측치 포함",
                    "yield_score|실수|수율 점수, 결측치 포함",
                ]),
            ],
            [
                a("sample_std", "해당 유효 행의 선택 변수 표본표준편차", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/laboratory.csv')
            correlations = df[['chem_a', 'chem_b', 'chem_c', 'chem_d']].corrwith(df['yield_score'])
            selected = correlations.idxmin()
            paired = df[[selected, 'yield_score']].dropna()
            answers = {'sample_std': round(float(paired[selected].std(ddof=1)), 3)}
            print(answers)
            ''',
            [
                "가장 작은 상관계수를 찾으며 절댓값 최댓값을 찾는 것이 아닙니다.",
                "음의 상관관계가 가장 크다는 것은 상관계수 자체가 가장 작다는 뜻입니다. 선택 후에도 수율과의 쌍별 유효 행을 유지하고 ddof=1로 계산합니다.",
            ],
            "음의 상관관계가 가장 크다는 것은 상관계수 자체가 가장 작다는 뜻입니다. 선택 후에도 수율과의 쌍별 유효 행을 유지하고 ddof=1로 계산합니다.",
            difficulty="중상",
            minutes=15,
            tags=["상관계수", "쌍별 결측", "표준편차"],
        ),

        q(
            "t1-25",
            "연령 구간별 혈당 평균",
            "health.csv는 나이와 혈당 측정 자료이다.",
            [
                "나이를 [18,30), [30,45), [45,60), [60,81) 구간으로 구분하시오.",
                "45세 이상 60세 미만 구간에 속한 사람의 glucose 평균을 구하시오. 각 구간은 왼쪽 경계를 포함하고 오른쪽 경계는 제외한다.",
            ],
            [
                f("health", "나이와 공복혈당", [
                    "id|정수|대상자 번호",
                    "age|정수|나이 18~80",
                    "glucose|실수|공복혈당(mg/dL)",
                ]),
            ],
            [
                a("mean_glucose", "45세 이상 60세 미만의 혈당 평균", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/health.csv')
            groups = pd.cut(df['age'], bins=[18, 30, 45, 60, 81], right=False, labels=['a', 'b', 'c', 'd'])
            answers = {'mean_glucose': round(float(df.loc[groups == 'c', 'glucose'].mean()), 3)}
            print(answers)
            ''',
            [
                "45세는 포함하고 60세는 제외합니다.",
                "pd.cut의 right=False로 왼쪽 경계를 포함하는 구간을 만듭니다. 60세는 평균 계산 대상에 포함하지 않습니다.",
            ],
            "pd.cut의 right=False로 왼쪽 경계를 포함하는 구간을 만듭니다. 60세는 평균 계산 대상에 포함하지 않습니다.",
            difficulty="중",
            minutes=12,
            tags=["구간화", "cut", "경계 조건"],
        ),

        q(
            "t1-26",
            "전년 대비 매출 성장률의 최댓값",
            "annual_sales.csv는 매장·연도·상품별 매출 자료이다.",
            [
                "모든 상품의 매출을 포함하여 매장별 2024년과 2025년 매출을 각각 합산하시오.",
                "매장별 전년 대비 매출 성장률(%) 중 최댓값을 구하시오. 성장률은 (2025년 매출 − 2024년 매출) / 2024년 매출 × 100이다.",
            ],
            [
                f("annual_sales", "매장·연도·상품별 매출", [
                    "store_id|정수|매장 번호 1~100",
                    "year|정수|2024 또는 2025",
                    "product|문자|상품 A, B, C",
                    "sales|실수|매출(원)",
                ]),
            ],
            [
                a("growth_pct", "매장별 전년 대비 성장률 최댓값(%)", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/annual_sales.csv')
            totals = df.pivot_table(index='store_id', columns='year', values='sales', aggfunc='sum').sort_index()
            growth = (totals[2025] - totals[2024]) / totals[2024] * 100
            best = growth.idxmax()
            answers = {'growth_pct': round(float(growth.loc[best]), 3)}
            print(answers)
            ''',
            [
                "상품별로 계산하기 전에 매장·연도별 매출을 합산합니다.",
                "연도별 총매출을 먼저 구하고 매장별로 같은 행에서 비교합니다. 상품별 성장률의 평균을 사용하지 않습니다.",
            ],
            "연도별 총매출을 먼저 구하고 매장별로 같은 행에서 비교합니다. 상품별 성장률의 평균을 사용하지 않습니다.",
            difficulty="중",
            minutes=12,
            tags=["전년 대비", "피벗", "복합 집계"],
        ),

        q(
            "t1-27",
            "이메일 정제 후 회사 계정의 로그인 평균",
            "accounts.csv는 이메일 표기가 일정하지 않고 중복 계정이 포함된 자료이다.",
            [
                "email의 앞뒤 공백을 제거하고 소문자로 통일하시오. @가 하나이며 양쪽에 공백 없는 문자열이 있는 주소만 유효하다.",
                "유효한 이메일별로 CSV에서 처음 나타난 행만 남긴 뒤, 도메인이 정확히 corp.co.kr인 계정의 login_count 평균을 구하시오.",
            ],
            [
                f("accounts", "중복 이메일과 로그인 횟수", [
                    "record_id|정수|기록 번호",
                    "email|문자|대소문자·공백·잘못된 주소 포함",
                    "login_count|정수|해당 기록의 로그인 횟수",
                ]),
            ],
            [
                a("mean_logins", "해당 계정의 평균 로그인 횟수", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/accounts.csv')
            df['normalized'] = df['email'].str.strip().str.lower()
            valid = df[df['normalized'].str.fullmatch(r'[^@\\s]+@[^@\\s]+', na=False)].drop_duplicates('normalized', keep='first')
            company = valid[valid['normalized'].str.endswith('@corp.co.kr')]
            answers = {'mean_logins': round(float(company['login_count'].mean()), 3)}
            print(answers)
            ''',
            [
                "문자열 정제 후 이메일별 첫 행을 남깁니다.",
                "문자열을 정제한 후 유효 주소를 판정하고 중복을 제거합니다. 부분 문자열이 아닌 @corp.co.kr로 끝나는 주소를 선택합니다.",
            ],
            "문자열을 정제한 후 유효 주소를 판정하고 중복을 제거합니다. 부분 문자열이 아닌 @corp.co.kr로 끝나는 주소를 선택합니다.",
            difficulty="중",
            minutes=12,
            tags=["문자열 정규화", "정규식", "중복 제거"],
        ),

        q(
            "t1-28",
            "7일 이동평균이 최대인 날짜",
            "energy.csv는 날짜마다 한 행씩 기록한 일별 사용량 자료이다.",
            [
                "날짜순으로 정렬한 후 당일과 직전 6일을 포함한 consumption의 이동평균을 구하시오. 7일치 관측이 없는 날짜는 제외한다.",
                "이동평균이 가장 큰 날짜를 YYYYMMDD 형식의 정수로 제출하시오. 동률이면 이른 날짜를 선택한다.",
            ],
            [
                f("energy", "연속된 일별 전력 소비량", [
                    "date|날짜|관측 날짜",
                    "consumption|실수|일별 소비량(kWh)",
                ]),
            ],
            [
                a("date", "최대 이동평균 날짜 YYYYMMDD", 0),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/energy.csv')
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            rolling = df['consumption'].rolling(7, min_periods=7).mean()
            best = rolling.idxmax()
            answers = {'date': int(df.loc[best, 'date'].strftime('%Y%m%d'))}
            print(answers)
            ''',
            [
                "일자를 정렬한 후 7개 관측값으로 이동평균을 구합니다.",
                "날짜순 정렬 후 rolling(7)로 이동평균을 계산합니다. 최댓값에 해당하는 원본 날짜를 조회해 정수로 변환합니다.",
            ],
            "날짜순 정렬 후 rolling(7)로 이동평균을 계산합니다. 최댓값에 해당하는 원본 날짜를 조회해 정수로 변환합니다.",
            difficulty="중",
            minutes=12,
            tags=["이동평균", "시계열", "최댓값 날짜"],
        ),

        q(
            "t1-29",
            "누적 주문량의 최초 도달 순번",
            "shipments.csv는 고객별 주문 일시와 주문 수량 자료이다.",
            [
                "고객별로 ordered_at이 이른 순서, 같은 시각이면 order_id가 작은 순서로 주문을 정렬하시오.",
                "누적 quantity가 처음 100 이상이 되는 주문의 고객별 주문 순번(1부터 시작)을 구하고, 그 순번의 평균을 구하시오. 끝까지 100에 도달하지 못한 고객은 제외한다.",
            ],
            [
                f("shipments", "고객별 주문 수량 이력", [
                    "order_id|정수|주문 번호",
                    "customer_id|정수|고객 번호",
                    "ordered_at|날짜|주문 일시",
                    "quantity|정수|해당 주문 수량",
                ]),
            ],
            [
                a("mean_order_number", "최초 도달 주문 순번의 평균", 3),
            ],
            '''
            import pandas as pd
            df = pd.read_csv('data/shipments.csv')
            df['ordered_at'] = pd.to_datetime(df['ordered_at'])
            df = df.sort_values(['customer_id', 'ordered_at', 'order_id'])
            df['cumulative'] = df.groupby('customer_id')['quantity'].cumsum()
            df['number'] = df.groupby('customer_id').cumcount() + 1
            reached = df[df['cumulative'] >= 100].drop_duplicates('customer_id')
            answers = {'mean_order_number': round(float(reached['number'].mean()), 3)}
            print(answers)
            ''',
            [
                "고객별 누적 수량과 고객별 주문 순번을 각각 계산하세요.",
                "정렬 후 고객별 cumsum과 cumcount를 계산합니다. 누적합이 100 이상인 행 중 고객별 첫 행만 남겨 평균을 구합니다.",
            ],
            "정렬 후 고객별 cumsum과 cumcount를 계산합니다. 누적합이 100 이상인 행 중 고객별 첫 행만 남겨 평균을 구합니다.",
            difficulty="중상",
            minutes=15,
            tags=["누적합", "cumcount", "최초 도달"],
        ),

        q(
            "t1-30",
            "왜도가 큰 변수의 로그 변환 후 분산",
            "amounts.csv는 세 종류의 거래 금액 자료이다.",
            [
                "amount_a~amount_c 중 pandas 기본 표본 왜도의 절댓값이 가장 큰 변수를 선택하시오. 동률이면 변수명 오름차순으로 선택한다.",
                "선택한 변수의 결측치를 제외하고 log(1+x) 변환을 적용한 값의 표본분산을 구하시오. log는 자연로그이다.",
            ],
            [
                f("amounts", "세 종류 금액의 분포", [
                    "id|정수|관측 번호",
                    "amount_a|실수|금액 A, 양수·결측 포함",
                    "amount_b|실수|금액 B, 양수·결측 포함",
                    "amount_c|실수|금액 C, 양수·결측 포함",
                ]),
            ],
            [
                a("log_variance", "log1p 변환 후 표본분산", 3),
            ],
            '''
            import pandas as pd
            import numpy as np
            df = pd.read_csv('data/amounts.csv')
            skewness = df[['amount_a', 'amount_b', 'amount_c']].skew().sort_index()
            selected = skewness.abs().idxmax()
            transformed = np.log1p(df[selected].dropna())
            answers = {'log_variance': round(float(transformed.var(ddof=1)), 3)}
            print(answers)
            ''',
            [
                "왜도 비교는 원자료에서 하고, 변환은 선택한 한 열에만 합니다.",
                "원본 열별 skew()를 비교해 변수를 고릅니다. 선택된 원자료에 np.log1p를 적용하고 var(ddof=1)로 표본분산을 구합니다.",
            ],
            "원본 열별 skew()를 비교해 변수를 고릅니다. 선택된 원자료에 np.log1p를 적용하고 var(ddof=1)로 표본분산을 구합니다.",
            difficulty="중상",
            minutes=15,
            tags=["왜도", "로그 변환", "분산"],
        ),
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
        q(
            "t3-04",
            "두 독립 집단의 평균 점수 비교",
            "results.csv는 서로 다른 참가자로 구성된 교육 집단 A와 B의 점수 자료이다. 결측 점수는 제외한다. 두 집단은 정규성을 만족하지만 등분산은 가정하지 않는다. 모평균이 같은지 유의수준 0.05에서 양측 검정하시오.",
            [
                "검정 통계량을 구하시오. 평균 차이의 방향은 A − B로 한다.",
                "p-value를 구하시오.",
                "p-value가 0.05 미만이면 귀무가설 기각을 1, 그렇지 않으면 0으로 제출하시오.",
            ],
            [
                f("results", "교육 집단과 시험 점수", [
                    "id|정수|참가자 번호",
                    "group|문자|독립 집단 A 또는 B",
                    "score|실수|시험 점수, 결측치 포함",
                ]),
            ],
            [
                a("t_stat", "검정 통계량", 3),
                a("pvalue", "p-value", 6),
                a("reject", "귀무가설 기각 여부", 0),
            ],
            '''
            import pandas as pd
            from scipy import stats
            df = pd.read_csv("data/results.csv")
            a = df.loc[df["group"] == "A", "score"].dropna()
            b = df.loc[df["group"] == "B", "score"].dropna()
            result = stats.ttest_ind(a, b, equal_var=False, alternative="two-sided")
            answers = {"t_stat": round(float(result.statistic), 3), "pvalue": round(float(result.pvalue), 6), "reject": int(result.pvalue < 0.05)}
            print(answers)
            ''',
            [
                "독립표본이며 등분산을 가정하지 않으므로 Welch 검정을 사용합니다.",
                "A와 B 입력 순서와 반올림 전 p-value를 확인하세요.",
            ],
            "Welch 독립표본 t-검정은 equal_var=False로 수행합니다. 같은 사람의 전후 관측이 아니므로 대응표본 검정을 사용하지 않습니다.",
            difficulty="중",
            minutes=20,
            tags=["독립표본 t-검정", "Welch", "가설 판단"],
        ),

        q(
            "t3-05",
            "유입 채널 분포의 적합도 검정",
            "acquisition.csv는 방문자의 유입 채널 자료이다. 모집단의 채널 비율이 검색 40%, 광고 30%, 직접 20%, 추천 10%라는 가설을 유의수준 0.05에서 검정하시오. 비율은 사전에 주어진 값이며 자료에서 추정하지 않는다.",
            [
                "검정 통계량을 구하시오.",
                "p-value를 구하시오.",
                "p-value가 0.05 미만이면 귀무가설 기각을 1, 그렇지 않으면 0으로 제출하시오.",
            ],
            [
                f("acquisition", "고객별 최초 유입 채널", [
                    "id|정수|고객 번호",
                    "channel|문자|검색, 광고, 직접, 추천",
                ]),
            ],
            [
                a("chi2", "검정 통계량", 3),
                a("pvalue", "p-value", 6),
                a("reject", "귀무가설 기각 여부", 0),
            ],
            '''
            import pandas as pd
            from scipy import stats
            df = pd.read_csv("data/acquisition.csv")
            observed = df["channel"].value_counts().reindex(["검색", "광고", "직접", "추천"], fill_value=0)
            expected = len(df) * pd.Series([0.4, 0.3, 0.2, 0.1], index=observed.index)
            result = stats.chisquare(observed, f_exp=expected)
            answers = {"chi2": round(float(result.statistic), 3), "pvalue": round(float(result.pvalue), 6), "reject": int(result.pvalue < 0.05)}
            print(answers)
            ''',
            [
                "한 범주형 변수의 관측 비율과 주어진 비율을 비교하는 적합도 검정입니다.",
                "채널 순서에 맞춰 관측도수와 기대도수를 정렬하세요.",
            ],
            "기대도수는 전체 행 수에 주어진 채널 비율을 곱한 값입니다. 모수를 자료에서 추정하지 않았으므로 자유도는 범주 수 − 1인 3입니다.",
            difficulty="중",
            minutes=20,
            tags=["카이제곱 적합도", "기대도수", "가설 판단"],
        ),

        q(
            "t3-06",
            "교육 시간과 점수의 단순선형회귀",
            "training.csv에서 score를 종속변수, hours를 설명변수로 하는 절편 포함 단순선형회귀모형을 최소제곱법으로 적합하시오. id와 tenure는 사용하지 않는다.",
            [
                "hours의 회귀계수를 구하시오.",
                "모형의 결정계수 R²를 구하시오.",
                "교육 시간이 40시간인 참가자의 예측 점수를 구하시오.",
            ],
            [
                f("training", "교육 시간과 평가 점수", [
                    "id|정수|참가자 번호",
                    "hours|실수|교육 시간",
                    "tenure|정수|근속 연수(모형에서 제외)",
                    "score|실수|교육 후 평가 점수",
                ]),
            ],
            [
                a("coefficient", "hours 회귀계수", 3),
                a("r_squared", "결정계수 R²", 3),
                a("prediction", "40시간 교육의 예측 점수", 3),
            ],
            '''
            import pandas as pd
            import statsmodels.formula.api as smf
            df = pd.read_csv("data/training.csv")
            model = smf.ols("score ~ hours", data=df).fit()
            prediction = model.predict(pd.DataFrame({"hours": [40]})).iloc[0]
            answers = {"coefficient": round(float(model.params["hours"]), 3), "r_squared": round(float(model.rsquared), 3), "prediction": round(float(prediction), 3)}
            print(model.summary())
            print(answers)
            ''',
            [
                "formula API에서는 기본적으로 절편을 포함합니다.",
                "예측할 설명변수 이름을 학습에 사용한 hours와 맞추세요.",
            ],
            "예측 점수는 적합된 절편과 기울기에 40시간을 대입한 값입니다. 회귀계수를 미리 반올림하면 예측값이 달라질 수 있으므로 최종 답만 반올림합니다.",
            difficulty="중",
            minutes=20,
            tags=["단순선형회귀", "결정계수", "예측"],
        ),

        q(
            "t3-07",
            "흡연과 질환 발생의 로지스틱 회귀",
            "lifestyle.csv에서 outcome을 종속변수로, age·exercise·smoker를 설명변수로 하는 로지스틱 회귀모형을 적합하시오. 절편을 포함하고 벌점화는 적용하지 않는다. smoker의 기준 범주는 No이다. id와 sugar는 제외한다.",
            [
                "smoker가 Yes인 범주의 오즈비를 구하시오.",
                "smoker Yes 회귀계수의 양측 p-value를 구하시오.",
                "나이 40세, 주간 운동 3회, 흡연 Yes인 사람의 outcome=1 예측 확률을 구하시오.",
            ],
            [
                f("lifestyle", "생활습관과 질환 발생", [
                    "id|정수|대상자 번호",
                    "age|정수|나이",
                    "exercise|정수|주간 운동 횟수",
                    "smoker|문자|No 또는 Yes",
                    "sugar|실수|참고용 혈당(모형에서 제외)",
                    "outcome|정수|질환 발생 1, 미발생 0",
                ]),
            ],
            [
                a("odds_ratio", "흡연 Yes의 오즈비", 3),
                a("pvalue", "흡연 Yes 계수의 p-value", 6),
                a("probability", "지정 조건의 예측 확률", 3),
            ],
            '''
            import pandas as pd
            import numpy as np
            import statsmodels.formula.api as smf
            df = pd.read_csv("data/lifestyle.csv")
            model = smf.logit("outcome ~ age + exercise + C(smoker, Treatment(reference='No'))", data=df).fit(disp=False)
            term = "C(smoker, Treatment(reference='No'))[T.Yes]"
            probability = model.predict(pd.DataFrame({"age": [40], "exercise": [3], "smoker": ["Yes"]})).iloc[0]
            answers = {"odds_ratio": round(float(np.exp(model.params[term])), 3), "pvalue": round(float(model.pvalues[term]), 6), "probability": round(float(probability), 3)}
            print(model.summary())
            print(answers)
            ''',
            [
                "범주형 설명변수의 기준을 No로 지정하세요.",
                "새 관측의 예측 확률은 적합한 모형의 predict로 구할 수 있습니다.",
            ],
            "로지스틱 회귀계수는 로그 오즈 단위이므로 지수를 취해 오즈비를 구합니다. 확률과 오즈비는 서로 다른 값이며 확률은 0~1 범위입니다.",
            difficulty="중상",
            minutes=20,
            tags=["로지스틱 회귀", "오즈비", "예측 확률"],
        ),

        q(
            "t3-08",
            "화면 유형과 구매 전환의 독립성 검정",
            "experiment.csv는 화면 A 또는 B를 본 방문자의 구매 전환 여부 자료이다. converted가 1이면 전환, 0이면 미전환이다. 화면 유형과 구매 전환이 독립인지 유의수준 0.05에서 검정하시오. 연속성 보정은 적용하지 않는다.",
            [
                "검정 통계량을 구하시오.",
                "p-value를 구하시오.",
                "p-value가 0.05 미만이면 독립이라는 귀무가설 기각을 1, 그렇지 않으면 0으로 제출하시오.",
            ],
            [
                f("experiment", "화면 실험의 전환 결과", [
                    "id|정수|참여자 번호",
                    "group|문자|실험 집단 A 또는 B",
                    "converted|정수|전환 성공 1, 실패 0",
                ]),
            ],
            [
                a("chi2", "검정 통계량", 3),
                a("pvalue", "p-value", 6),
                a("reject", "귀무가설 기각 여부", 0),
            ],
            '''
            import pandas as pd
            from scipy import stats
            df = pd.read_csv("data/experiment.csv")
            table = pd.crosstab(df["group"], df["converted"])
            result = stats.chi2_contingency(table, correction=False)
            answers = {"chi2": round(float(result.statistic), 3), "pvalue": round(float(result.pvalue), 6), "reject": int(result.pvalue < 0.05)}
            print(answers)
            ''',
            [
                "두 범주형 변수의 관계이므로 교차표를 사용합니다.",
                "chi2_contingency의 연속성 보정 옵션을 확인하세요.",
            ],
            "카이제곱 독립성 검정에 2×2 관측도수 표를 전달합니다. 이 문제는 연속성 보정을 사용하지 않는 조건이므로 correction=False로 계산합니다.",
            difficulty="중",
            minutes=20,
            tags=["카이제곱 독립성", "교차표", "가설 판단"],
        ),

        q(
            "t3-09",
            "학습 시간과 점수의 상관관계 검정",
            "study.csv에서 study_hours와 score 사이의 선형 상관관계가 있는지 유의수준 0.05에서 양측 Pearson 상관 검정을 하시오. 두 값이 모두 관측된 행만 사용하며, 검정의 가정은 만족한다고 본다. id는 사용하지 않는다.",
            [
                "상관계수를 부호를 유지하여 구하시오.",
                "모상관계수가 0이라는 귀무가설에 대한 p-value를 구하시오.",
                "p-value가 0.05 미만이면 귀무가설 기각을 1, 그렇지 않으면 0으로 제출하시오.",
            ],
            [
                f("study", "학습 시간과 시험 점수", [
                    "id|정수|학습자 번호",
                    "study_hours|실수|주간 학습 시간, 결측 포함",
                    "score|실수|시험 점수, 결측 포함",
                ]),
            ],
            [
                a("correlation", "Pearson 상관계수", 3),
                a("pvalue", "p-value", 6),
                a("reject", "귀무가설 기각 여부", 0),
            ],
            '''
            import pandas as pd
            from scipy import stats
            df = pd.read_csv("data/study.csv").dropna(subset=["study_hours", "score"])
            result = stats.pearsonr(df["study_hours"], df["score"], alternative="two-sided")
            answers = {"correlation": round(float(result.statistic), 3), "pvalue": round(float(result.pvalue), 6), "reject": int(result.pvalue < 0.05)}
            print(answers)
            ''',
            [
                "두 변수의 결측치를 같은 행 기준으로 제거해 관측 쌍을 유지하세요.",
                "상관계수 크기와 검정의 p-value를 구분합니다.",
            ],
            "두 열을 각각 결측 제거하면 관측 쌍이 달라질 수 있습니다. 쌍별 완전 사례에 Pearson 검정을 적용하며, 상관계수에 절댓값을 취하지 않습니다.",
            difficulty="중",
            minutes=20,
            tags=["Pearson 상관", "결측치", "가설 판단"],
        ),

        q(
            "t3-10",
            "매장 규모별 평균 매출의 분산분석",
            "stores.csv의 매장을 area가 100 미만인 소형, 100 이상 180 미만인 중형, 180 이상인 대형으로 구분하시오. 세 규모 집단의 sales 모평균이 모두 같은지 유의수준 0.05에서 검정하시오. 각 집단의 정규성·등분산성과 관측의 독립성은 만족한다고 가정한다. 다른 변수는 사용하지 않는다.",
            [
                "일원배치 분산분석의 F 통계량을 구하시오.",
                "p-value를 구하시오.",
                "p-value가 0.05 미만이면 세 모평균이 같다는 귀무가설 기각을 1, 그렇지 않으면 0으로 제출하시오.",
            ],
            [
                f("stores", "매장 규모·광고비·매출", [
                    "id|정수|매장 번호",
                    "area|실수|매장 면적(㎡)",
                    "staff|정수|직원 수",
                    "ad_spend|실수|광고비(만원)",
                    "sales|실수|매출(만원)",
                ]),
            ],
            [
                a("f_stat", "F 통계량", 3),
                a("pvalue", "p-value", 6),
                a("reject", "귀무가설 기각 여부", 0),
            ],
            '''
            import pandas as pd
            from scipy import stats
            df = pd.read_csv("data/stores.csv")
            small = df.loc[df["area"] < 100, "sales"]
            medium = df.loc[(df["area"] >= 100) & (df["area"] < 180), "sales"]
            large = df.loc[df["area"] >= 180, "sales"]
            result = stats.f_oneway(small, medium, large)
            answers = {"f_stat": round(float(result.statistic), 3), "pvalue": round(float(result.pvalue), 6), "reject": int(result.pvalue < 0.05)}
            print(answers)
            ''',
            [
                "세 독립 집단의 평균을 비교하는 일원배치 분산분석입니다.",
                "100과 180의 경계가 속하는 집단을 확인하세요.",
            ],
            "세 집단을 겹치지 않게 나누어 f_oneway에 전달합니다. 유의한 결과는 적어도 한 집단의 모평균이 다르다는 뜻이며 모든 집단 쌍이 다르다는 뜻은 아닙니다.",
            difficulty="중",
            minutes=20,
            tags=["일원배치 분산분석", "F 통계량", "가설 판단"],
        ),
    ]
    return problems
