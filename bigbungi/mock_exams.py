"""Build round-based mock exams in a separate public content directory."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from textwrap import dedent

import numpy as np


ROUNDS = {
    2: ("2021-06-19", "이상치와 결측치 처리 · 택배 정시 도착 확률",
        [("수스의 백업 플레이", "https://backingup.tistory.com/35"),
         ("Data Doctor", "https://datadoctorblog.com/2021/06/19/etc-bigdata-analysis-engineer-cert-2nd-perf-test-review/")]),
    3: ("2021-12-04", "사분위수 · 결핵 유병률 · 구매 확률",
        [("It’s Life", "https://action-makes-fortune.tistory.com/entry/빅데이터분석기사-3회-실기-문제-복원-기출?category=857928")]),
    4: ("2022-06-25", "사분위범위 · 콘텐츠 조건 집계 · 고객군 분류",
        [("okjh 응시자 복기", "https://okjh.tistory.com/166"),
         ("datahwi 응시자 복기", "https://datahwi.tistory.com/m/74"),
         ("panda5176 응시자 복기", "https://panda5176.tistory.com/17?category=1035271"),
         ("이패스코리아 시행일 및 복원 안내", "https://m.epasskorea.com/Customer/news_detail.asp?bg_idx=5&bmode=detail&intB_idx=12047&link_idx=4144")]),
    5: ("2022-12-03", "종량제봉투 가격 · BMI · 중고차 가격",
        [("Velog 모래", "https://velog.io/@sujin1018/빅데이터분석기사-실기-합격"),
         ("data-science.tistory.com 복원·가답안", "https://data-science.tistory.com/3"),
         ("Ddolgom 응시자 복기", "https://aitzone.tistory.com/35"),
         ("꿈라CBT 작업형 복원", "https://quiz.dreaming-ryan.com/subjects/bigdata-practical/rounds/bigdata-practical-r5")]),
    6: ("2023-06-24", "출동 소요 시간 · 연령대 분류 · 카이제곱 검정",
        [("해모해모", "https://haemo-dev.tistory.com/58?category=1115935"),
         ("mj91 응시자 복기", "https://mj91.tistory.com/252"),
         ("데코_데이터분석가", "https://kkw-da.tistory.com/entry/Daily-제6회-빅데이터분석기사빅분기-실기-후기문제-및-난이도")]),
    7: ("2023-12-02", "수강 점수 표준화 · 제주 여행 매출 · 조개 성별",
        [("초록E", "https://nate9389.tistory.com/2397")]),
    8: ("2024-06-22", "국가별 소비량 · 지하철 이용객 · 고객 이탈",
        [("stranger95", "https://abluesnake.tistory.com/189"),
         ("bio-kcs 응시자 복기", "https://bio-kcs.tistory.com/entry/자격증-빅데이터분석기사-실기-8회-시험-후기-R-4일-독학")]),
    9: ("2024-11-30", "범죄 검거율 · 근속연수 · 다중분류",
        [("Data, Day By Day", "https://jesimsim.tistory.com/entry/빅데이터-분석기사-9회-실기-기출문제-복원-및-후기-답안-및-풀이코드-有")]),
    10: ("2025-06-21", "정답률 순위 · 연월별 매출 · 난방비 회귀",
         [("koreaioi", "https://koreaioi.tistory.com/155"),
          ("우당탕탕 현민 IT 사무소", "https://minny-it.tistory.com/26"),
          ("2realzoo 응시자 복기", "https://2realzoo.tistory.com/entry/2025년-제10회-빅데이터분석기사-실기-문제-복원")]),
    11: ("2025-11-29", "온실가스 배출량 · 게임 활성화 수준 · 당뇨",
         [("두루미의 스포츠 데이터분석실", "https://alicelog.tistory.com/225")]),
    12: ("2026-06-20", "합동표본분산 · RMSLE · 단측 신뢰구간",
         [("빅분기합격연구소", "https://bigdata-inst.tistory.com/1"),
          ("에이치데이터랩 복원 안내", "https://hdatalab.co.kr/notice/?bmode=view&idx=175762086")]),
}


@dataclass
class ExamQuestion:
    public: dict
    files: dict
    key: dict


def dataset(name, frame, descriptions):
    if list(frame.columns) != list(descriptions):
        raise ValueError(f"Column glossary does not match {name}.csv")
    return {
        "name": f"{name}.csv",
        "rows": len(frame),
        "columns": [{"name": column, "description": text} for column, text in descriptions.items()],
    }


def field(label, instruction, expression, decimals=3):
    return label, instruction, expression, decimals


def numeric(kind, title, scenario, name, frame, columns, setup, items, *, recalled=True):
    points = {1: 10, 3: 15}[kind]
    if points % len(items):
        raise ValueError(f"Uneven subquestion weights for {title}")
    fields, steps, expressions = [], [], []
    for i, (label, instruction, expression, decimals) in enumerate(items, 1):
        key = f"answer_{i}"
        format_hint = {None: "텍스트", 0: "정수"}.get(decimals, f"소수 {decimals}자리까지 반올림")
        fields.append({"key": key, "label": label, "decimals": decimals,
                       "format": format_hint, "points": points // len(items)})
        steps.append(instruction)
        if decimals is None:
            expression = f"str({expression})"
        elif decimals == 0:
            expression = f"int({expression})"
        else:
            expression = f"round(float({expression}), {decimals})"
        expressions.append(f'    "{key}": {expression},')
    code = "\n".join([
        "import numpy as np", "import pandas as pd", "",
        f'df = pd.read_csv("data/{name}.csv")', dedent(setup).strip(),
        "answers = {", *expressions, "}", "print(answers)", "",
    ])
    file = dataset(name, frame, columns)
    public = {"type": kind, "title": title, "scenario": scenario, "steps": steps,
              "files": [file], "fields": fields, "points": points, "recalled": recalled}
    return ExamQuestion(public, {file["name"]: frame}, {"code": code})


def short(instruction, answers, recalled):
    answer_field = {"key": "answer", "label": "답안", "format": "단답", "points": 3}
    expected = answers
    try:
        number = Decimal(answers[0])
        digits = max(0, -number.as_tuple().exponent)
        answer_field.update(decimals=digits, format="정수" if not digits else f"소수 {digits}자리까지")
        expected = float(number)
    except InvalidOperation:
        pass
    public = {"type": 0, "title": "단답형", "scenario": "", "steps": [instruction], "files": [],
              "fields": [answer_field],
              "points": 3, "recalled": recalled}
    return ExamQuestion(public, {}, {"expected": {"answer": expected}})


def prepare_mock_exams(root, reference_result, force):
    from .mock_predictions import prediction
    from .mock_questions import SHORT_QUESTIONS, work_questions

    sources = [Path(__file__).with_name(name) for name in (
        "mock_exams.py", "mock_questions.py", "mock_predictions.py", "datasets.py", "prepare.py",
    )]
    fingerprint = hashlib.sha256(b"".join(source.read_bytes() for source in sources)).hexdigest()
    marker = root / "build.json"
    if not force and marker.exists() and json.loads(marker.read_text())["fingerprint"] == fingerprint:
        print(f"Mock exams are current ({len(ROUNDS)} rounds).")
        return

    def write_json(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")

    index = []
    for round_number, (date, summary, sources) in reversed(ROUNDS.items()):
        rng = np.random.default_rng(4400 + round_number)
        first, third = work_questions(round_number, rng)
        questions = [short(*item) for item in SHORT_QUESTIONS.get(round_number, ())]
        questions.extend([*first, prediction(round_number, rng), *third])
        assert len(first) == 3 and len(third) == (2 if round_number >= 6 else 0)
        assert len(questions) == (6 if round_number >= 6 else 14)
        assert sum(q.public["points"] for q in questions) == 100
        answer_key = {}
        for i, question in enumerate(questions, 1):
            question_id = f"r{round_number:02d}-{i:02d}"
            question.public["id"] = question_id
            directory = root / "data" / question_id
            for filename, frame in question.files.items():
                directory.mkdir(parents=True, exist_ok=True)
                frame.to_csv(directory / filename, index=False, float_format="%.8f")
            if question.public["type"] in (1, 3):
                question.key["expected"] = reference_result(
                    {"solution": question.key["code"], "id": question_id}, directory,
                )
            answer_key[question_id] = question.key

        round_info = {
            "round": round_number, "date": date, "minutes": 180, "summary": summary,
            "questionCount": len(questions),
            "supplementalCount": sum(not q.public["recalled"] for q in questions),
            "sources": [{"name": name, "url": url} for name, url in sources],
        }
        index.append(round_info)
        write_json(root / "rounds" / f"{round_number}.json", {
            **round_info, "questions": [q.public for q in questions],
        })
        write_json(root / "keys" / f"{round_number}.json", answer_key)
    write_json(root / "index.json", index)
    write_json(marker, {"fingerprint": fingerprint})
    print(f"Built {len(index)} mock exams ({sum(r['questionCount'] for r in index)} questions).")
