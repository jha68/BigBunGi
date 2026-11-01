# 빅분기 · 실기 연습실

빅데이터분석기사 실기 스타일의 **직접 만든 16문제**를 풀고, 브라우저에서 실제 Python을 실행하는 학습 웹앱입니다.

배포 주소: **https://bigbungi.junununseo.com**

## 제공 기능

- **1유형 10문제:** 조건 추출, 결측치, IQR·Z-score, 취소 거래, 날짜·전환율, merge, 정규화, 피벗, CAGR.
- **2유형 3문제:** 이진분류(ROC AUC), 회귀(RMSE), 다중분류(Macro F1). 결측치·범주형·잡음이 있는 학습/평가 데이터와 CSV 제출 채점.
- **3유형 3문제:** 대응·단일표본 t-검정, ANOVA, 상관분석, OLS, 카이제곱, 비벌점 로지스틱 회귀, 오즈비·민감도.
- 코드 편집기, `Ctrl/Cmd+Enter` 실행, stdout·경고·Python traceback, 데이터프레임·그래프 표시, 실행 중지와 60초 제한.
- 선택 영역의 파란색 강조·테두리, 줄 번호·Python 문법 강조·자동 줄바꿈이 있는 읽기 전용 기준 풀이.
- 데이터 미리보기·변수 설명·CSV 다운로드, 단계별 힌트, 기준 풀이, 풀이 노트, 진행률, 180분 타이머, 모바일 화면.
- 코드·노트·진행률은 브라우저의 localStorage에 자동 저장됩니다. 다른 기기·브라우저로 동기화되지는 않습니다.
- **Gemini 튜터:** 현재 문제·작성 중인 코드·실행 결과를 첨부하는 문제별 AI 대화. 개인 API 키, 모델 선택, 코드 문법 강조, 오류 안내·재시도·응답 중지.

## Gemini 질문하기

1. 문제를 선택하고 **AI 질문** 탭을 엽니다.
2. [Google AI Studio](https://aistudio.google.com/apikey)에서 발급한 **본인의 API 키**를 입력하고 **키 연결**을 누릅니다. 키는 채팅이나 저장소에 올리지 마세요.
3. 키로 사용 가능한 텍스트 모델을 조회합니다. 기본은 공식 SDK의 `gemini-flash-latest` 별칭을 우선 사용하며, 없으면 조회된 Flash 모델을 선택합니다. 연결 설정에서 다른 모델도 선택할 수 있습니다.
4. 질문을 입력하고 전송 버튼이나 `Ctrl/Cmd+Enter`로 보냅니다. **전송 순간의 최신 문제·코드·변수 설명·데이터 미리보기**가 자동 첨부됩니다. 최근 실행 결과·오류는 첨부 내용에서 켜고 끌 수 있습니다.
5. 같은 문제의 최근 6개 성공한 질의·응답을 함께 참고합니다. 다른 문제로 바꿔도 대화는 섞이지 않습니다.

키와 AI 대화는 현재 탭 메모리에만 보관하며, localStorage·sessionStorage·URL·배포 파일에 저장하지 않습니다. **새로고침하면 키와 AI 대화가 지워집니다.** 기존 코드·풀이 노트·진행률 자동 저장은 유지됩니다. API 키는 Google API의 `x-goog-api-key` 헤더에만 보내고, 프롬프트에 우연히 포함된 동일한 키는 마스킹합니다.

요청은 브라우저에서 Google Gemini로 직접 전송되며 입력한 키의 할당량과 요금 정책이 적용됩니다. 공용 API 키나 별도 서버는 사용하지 않습니다. API 키에 웹사이트 제한을 설정한 경우 운영 도메인을 허용해야 합니다. 키를 코드나 GitHub Secrets, `VITE_*` 환경변수에 넣지 마세요.

전체 CSV·기준 풀이·정답 키·평가 정답 라벨은 첨부하지 않습니다. Gemini는 Python을 직접 실행하지 않으므로 제안 코드는 에디터에서 직접 실행하여 확인하세요. 답변의 코드 블록은 읽기 전용이며 자동으로 실행하지 않습니다.

## 실행 구조

React + CodeMirror + Vite의 **정적 사이트**입니다. Python 3.12(Pyodide)는 Web Worker 안에서 실행되므로 사용자 코드가 서버나 개발 환경에서 실행되지 않습니다. Python 풀이와 채점은 API 키 없이 작동하며, 선택 기능인 Gemini 튜터에만 개인 키가 필요합니다. 별도 백엔드는 없습니다.

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
# Ctrl/Cmd+Enter, 드래그 선택 강조, 읽기 전용 해설의 문법 강조 검증
CHROMIUM_PATH=/usr/bin/chromium .venv/bin/python tests/browser_editor.py
# Gemini 컨텍스트·대화 분리·키 보관·오류·모바일 UI 검증 (Google 응답은 모의 데이터)
APP_URL=http://127.0.0.1:5173/ CHROMIUM_PATH=/usr/bin/chromium .venv/bin/python tests/browser_gemini.py
```

실제 WebAssembly Python에서 16개 기준 풀이를 실행하고 채점하며 오류·DataFrame·그래프·중지·자동 저장·모바일 탐색을 검증합니다. 클라우드 프록시의 CA를 Chromium이 신뢰하지 않는 경우 테스트는 Python의 검증된 TLS 전송으로 CDN만 연결합니다. TLS 및 Pyodide 패키지 해시 검증은 유지합니다.

Gemini 테스트는 Google의 HTTP 응답을 모의 처리하고 실제 Python 오류를 컨텍스트에 넣어 검증합니다. 유효한 개인 키가 없는 개발 환경에서는 실제 Gemini 답변 생성까지 검증했다고 간주하지 않습니다.

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
4. Pages의 도메인 설정을 확인하고, 공개 HTTPS 주소의 HTML·스크립트·Python worker·16문제 카탈로그를 실제 요청으로 검증.

Cloudflare DNS 레코드는 다음과 같습니다. DNS 레코드를 직접 설정한 경우 Cloudflare API 토큰은 필요하지 않습니다.

| 종류 | 이름 | 대상 | 프록시 |
|---|---|---|---|
| CNAME | `bigbungi` | `jha68.github.io` | DNS 전용 |

저장소 관리자는 Settings → Pages에서 Source를 GitHub Actions로 선택하고 Custom domain에 `bigbungi.junununseo.com`을 저장합니다. 이 관리 설정은 GitHub 기본 배포 토큰으로 수정할 수 없습니다. 인증서 발급 후 Enforce HTTPS를 활성화합니다. DNS 전파와 인증서 발급은 별도로 시간이 걸릴 수 있습니다. 상대 경로로 빌드하므로 기본 주소 `https://jha68.github.io/BigBunGi/`와 사용자 지정 도메인에서 모두 실행할 수 있습니다.

## 파일 구성

| 경로 | 역할 |
|---|---|
| `bigbungi/content.py` | 16문제의 문제문·조건·스키마·힌트·기준 풀이 |
| `bigbungi/datasets.py` | 합성 데이터 생성 |
| `bigbungi/prepare.py` | 배포 자료와 정답 생성 |
| `web/src/main.jsx` | 연습 화면·자동 저장·실행 관리 |
| `web/src/CodeEditor.jsx` | 공용 Python 편집기·읽기 전용 코드 표시 |
| `web/src/GeminiTutor.jsx` | 키 연결·문제별 대화·질문 UI |
| `web/src/gemini.js` | Google REST 호출·컨텍스트 구성·오류 처리 |
| `web/public/python-worker.js` | 실제 Python 실행·결과 수집 |
| `web/src/grading.js` | 수치 답안·CSV 검증·AUC/F1/RMSE 채점 |
| `tests/` · `web/tests/` | 콘텐츠·채점·실제 브라우저 검증 |

MIT License. 문제·합성 데이터·코드에 적용됩니다. 각 의존 라이브러리의 라이선스는 별도로 적용됩니다.
