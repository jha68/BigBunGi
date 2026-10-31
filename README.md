# 빅분기 · 실기 연습실

빅데이터분석기사 실기 스타일의 **직접 만든 16문제**를 풀고, 브라우저에서 실제 Python을 실행하는 학습 웹앱입니다.

배포 주소: **https://bigbungi.junununseo.com**

## 제공 기능

- **1유형 10문제:** 조건 추출, 결측치, IQR·Z-score, 취소 거래, 날짜·전환율, merge, 정규화, 피벗, CAGR.
- **2유형 3문제:** 이진분류(ROC AUC), 회귀(RMSE), 다중분류(Macro F1). 결측치·범주형·잡음이 있는 학습/평가 데이터와 CSV 제출 채점.
- **3유형 3문제:** 대응·단일표본 t-검정, ANOVA, 상관분석, OLS, 카이제곱, 비벌점 로지스틱 회귀, 오즈비·민감도.
- 코드 편집기, `Ctrl/Cmd+Enter` 실행, stdout·경고·Python traceback, 데이터프레임·그래프 표시, 실행 중지와 60초 제한.
- 데이터 미리보기·변수 설명·CSV 다운로드, 단계별 힌트, 기준 풀이, 풀이 노트, 진행률, 180분 타이머, 모바일 화면.
- 코드·노트·진행률은 브라우저의 localStorage에 자동 저장됩니다. 다른 기기·브라우저로 동기화되지는 않습니다.

## 실행 구조

React + CodeMirror + Vite의 **정적 사이트**입니다. Python 3.12(Pyodide)는 Web Worker 안에서 실행되므로 사용자 코드가 서버나 개발 환경에서 실행되지 않습니다. GitHub Pages만으로 동작하며 백엔드나 API 키가 필요 없습니다.

첫 접속에는 jsDelivr에서 Python 런타임과 pandas·NumPy를 다운로드합니다. scipy·scikit-learn·statsmodels·matplotlib는 코드의 import에 따라 추가 로드됩니다. 첫 실행에는 인터넷이 필요하며 이후 브라우저 캐시를 활용합니다. multiprocessing·임의의 네이티브 패키지·서버 파일 접근은 지원하지 않습니다. 각 실행은 새로운 풀이 네임스페이스와 새로운 `data/` 작업 폴더를 사용합니다.

데이터와 문제는 고정 시드로 직접 생성한 합성 자료이며 실제 응시자의 정보나 원본 기출 데이터는 포함하지 않습니다. 공개된 최근 기출 복원 자료의 유형·문제 형식만 참고했습니다. 공식 기출문제나 공식 채점 시스템이 아닙니다.

정적 학습 사이트의 특성상 정답·평가 라벨도 배포 파일에 포함됩니다. 이는 자기 학습용 채점이며 부정행위 방지가 필요한 시험·인증 용도로 사용하면 안 됩니다. 2유형의 점수·통과 기준은 연습용이고, 모델의 정확한 지표도 함께 표시합니다.

## 로컬 개발

Python 3.12와 Node.js 22 이상을 사용합니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m bigbungi.prepare
cd web
npm ci
npm run dev -- --port 5173
```

`bigbungi.prepare`는 CSV, 정답, 해설, 미리보기를 `web/public/content/`에 생성합니다. 소스가 달라질 때만 재생성하며 `--force`로 강제로 갱신할 수 있습니다. 기준 정답은 반올림된 실제 배포 CSV를 읽어 다시 계산합니다. 생성 파일은 Git에 넣지 않고 배포 시 재현합니다.

```sh
# 저장소 루트: 실제 CSV로 16개 기준 풀이와 모델 성능 검증
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v

# 위 검증이 만드는 scikit-learn 지표 fixture와 JavaScript 채점 결과 비교
cd web
npm test
npm run build
npm run preview -- --port 4173 --strictPort
```

브라우저 통합 테스트는 개발 서버를 실행한 뒤 저장소 루트에서 실행합니다.

```sh
CHROMIUM_PATH=/usr/bin/chromium .venv/bin/python tests/browser_smoke.py
```

실제 WebAssembly Python에서 16개 기준 풀이를 실행하고 채점하며 오류·DataFrame·그래프·중지·자동 저장·모바일 탐색을 검증합니다. 클라우드 프록시의 CA를 Chromium이 신뢰하지 않는 경우 테스트는 Python의 검증된 TLS 전송으로 CDN만 연결합니다. TLS 및 Pyodide 패키지 해시 검증은 유지합니다.

## 문제 풀이

1. 문제를 선택하고 `data/파일명.csv`로 데이터를 읽습니다.
2. 1·3유형은 문제에 안내된 키로 `answers` 딕셔너리를 작성합니다. 실행 후 답안 입력란에 자동 반영되며 직접 수정할 수도 있습니다.
3. 2유형은 `id`와 지정된 예측 열로 `submission.csv`를 저장합니다. `index=False`를 사용합니다.
4. **코드 실행 → 채점하기** 순서로 확인합니다. 코드가 바뀌면 다시 실행해야 합니다.
5. 막히면 단계별 힌트나 해설을 열어 보고 다시 작성합니다.

## GitHub Pages / 도메인

`main`에 push하면 `.github/workflows/pages.yml`이 다음을 수행합니다.

1. 고정 버전 Python·Node 환경에서 원본 데이터와 정답 생성.
2. Python 문제·모델 검증 및 JavaScript 채점 검증.
3. Vite 빌드 후 GitHub Pages 아티팩트 배포.
4. Pages의 사용자 지정 도메인을 `bigbungi.junununseo.com`으로 설정.
5. TLS 인증서가 준비되면 HTTPS 강제 적용. 인증서 준비가 늦으면 워크플로에 안내를 남기며 이후 Pages 설정에서 Enforce HTTPS를 활성화합니다.

Cloudflare DNS 레코드는 다음과 같습니다. DNS 레코드를 직접 설정한 경우 Cloudflare API 토큰은 필요하지 않습니다.

| 종류 | 이름 | 대상 | 프록시 |
|---|---|---|---|
| CNAME | `bigbungi` | `jha68.github.io` | DNS 전용 |

저장소 Pages 설정의 Source는 GitHub Actions입니다. 최초 Pages 활성화 권한이 거부되면 저장소 관리자가 Settings → Pages에서 GitHub Actions를 선택한 뒤 실패한 워크플로를 다시 실행합니다. DNS 전파와 GitHub의 인증서 발급은 별도로 시간이 걸릴 수 있습니다.

## 파일 구성

| 경로 | 역할 |
|---|---|
| `bigbungi/content.py` | 16문제의 문제문·조건·스키마·힌트·기준 풀이 |
| `bigbungi/datasets.py` | 합성 데이터 생성 |
| `bigbungi/prepare.py` | 배포 자료와 정답 생성 |
| `web/src/main.jsx` | 연습 화면·자동 저장·실행 관리 |
| `web/public/python-worker.js` | 실제 Python 실행·결과 수집 |
| `web/src/grading.js` | 수치 답안·CSV 검증·AUC/F1/RMSE 채점 |
| `tests/` · `web/tests/` | 콘텐츠·채점·실제 브라우저 검증 |

MIT License. 문제·합성 데이터·코드에 적용됩니다. 각 의존 라이브러리의 라이선스는 별도로 적용됩니다.
