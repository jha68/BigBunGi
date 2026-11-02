"""Gemini UI/HTTP contract tests using mocked Google replies and real Python.

No paid Gemini request is made. Test credentials are deliberately nonfunctional.
"""
import asyncio
import json
import os

from playwright.async_api import async_playwright, Error as PlaywrightError
from browser_smoke import verified_download

KEY = "test-only-gemini-key-not-real"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium"), headless=True,
            proxy={"server": os.environ["HTTPS_PROXY"], "bypass": "localhost,127.0.0.1"} if os.environ.get("HTTPS_PROXY") else None)
        context = await browser.new_context(viewport={"width": 1512, "height": 1080})
        # randomUUID is unavailable on an HTTP origin; IDs must still work.
        await context.add_init_script("Object.defineProperty(crypto, 'randomUUID', {value: undefined});")
        errors, requests = [], []
        release = asyncio.Event()
        quota_once = False
        note_attempts = 0
        note_release = asyncio.Event()
        headers = {"access-control-allow-origin": "*", "access-control-allow-headers": "content-type,x-goog-api-key", "access-control-allow-methods": "GET,POST,OPTIONS"}

        async def cdn(route):
            body, kind = await asyncio.to_thread(verified_download, route.request.url)
            await route.fulfill(status=200, body=body, content_type=kind, headers={"access-control-allow-origin": "*"})

        async def gemini(route):
            nonlocal quota_once, note_attempts
            req = route.request
            if req.method == "OPTIONS":
                await route.fulfill(status=204, headers=headers); return
            requests.append({"url": req.url, "key": req.headers.get("x-goog-api-key"), "body": req.post_data_json if req.method == "POST" else None})
            status = 200
            if req.headers.get("x-goog-api-key") != KEY:
                status, body = 400, {"error": {"message": "API key not valid"}}
            elif req.method == "GET":
                body = {"models": [
                    {"name": "models/gemini-flash-latest", "displayName": "Gemini Flash", "supportedGenerationMethods": ["generateContent"]},
                    {"name": "models/gemini-pro", "displayName": "Gemini Pro", "supportedGenerationMethods": ["generateContent"]},
                    {"name": "models/gemini-2.5-flash-lite", "displayName": "Flash Lite", "supportedGenerationMethods": ["generateContent"]},
                    {"name": "models/gemini-2.5-pro", "displayName": "Gemini 2.5 Pro", "supportedGenerationMethods": ["generateContent"]},
                    {"name": "models/gemini-image", "displayName": "Image", "supportedGenerationMethods": ["generateContent"]},
                ]}
            else:
                payload = req.post_data_json
                question = payload["contents"][-1]["parts"][-1]["text"]
                if "입력된 질문과 AI 답변만 아주 짧게 요약" in json.dumps(payload, ensure_ascii=False):
                    note_attempts += 1
                    if note_attempts == 1:
                        status, body = 429, {"error": {"message": "quota exceeded"}}
                    else:
                        await note_release.wait()
                        body = {"candidates": [{"content": {"parts": [{"text": "Q. 오류 원인은?\nA. 출력 예시를 확인하세요.\n\n```python\nprint('Gemini 코드 예시')\n```"}]}, "finishReason": "STOP"}]}
                elif "할당량 테스트" in question and not quota_once:
                    quota_once = True
                    status, body = 429, {"error": {"message": "quota exceeded"}}
                else:
                    if "중지 테스트" in question:
                        await release.wait()
                    text = "현재 문제를 참고한 답변입니다.\n\n```python\nprint('Gemini 코드 예시')\n```\n\n<script>window.__gemini_xss = true</script>\n[unsafe](javascript:alert(1))"
                    body = {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}]}
            try:
                streamed = status == 200 and "streamGenerateContent" in req.url
                await route.fulfill(status=status, content_type="text/event-stream" if streamed else "application/json", body=("data: " + json.dumps(body) + "\n\n") if streamed else json.dumps(body), headers=headers)
            except PlaywrightError:
                if not release.is_set(): raise

        async def access(route):
            await route.fulfill(status=200,content_type="application/json",body=json.dumps({"source":"https://ai.google.dev/gemini-api/docs/pricing","models":{"gemini-2.5-flash-lite":{"available":True},"gemini-2.5-pro":{"available":True},"gemini-pro":{"available":True}}}))
        await context.route("**/content/model-access.json", access)
        await context.route("https://cdn.jsdelivr.net/pyodide/**", cdn)
        await context.route("https://generativelanguage.googleapis.com/**", gemini)
        page = await context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto(os.environ.get("APP_URL", "http://127.0.0.1:4175/"), wait_until="networkidle")
        assert await page.locator(".page-intro, .practice-strip, .focus-timer, .dataset-callout, .topic-tags").count() == 0
        assert await page.get_by_role("tablist", name="문제 정보", exact=True).get_by_role("tab", name="AI 질문", exact=True).count() == 1
        result_tabs = page.get_by_role("tablist", name="실행과 제출", exact=True)
        assert [text.strip() for text in await result_tabs.get_by_role("tab").all_text_contents()] == ["실행 결과", "답안 제출"]
        await page.wait_for_function("!document.querySelector('[data-testid=run-code]').disabled", timeout=120000)
        editor = page.get_by_role("textbox", name="Python 코드 편집기", exact=True)

        async def edit(source):
            await editor.click(); await editor.press("Control+a"); await page.keyboard.insert_text(source)

        source = 'print("CONTEXT_STDOUT")\nraise ValueError("CONTEXT_ERROR")'
        await edit(source)
        await editor.press("Control+Enter")
        await page.get_by_test_id("python-error").wait_for()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert await page.locator(".problem-panel .gemini-panel").count() == 1
        assert await page.get_by_role("button", name="Gemini 질문 보내기").is_disabled()
        assert not requests, "API must not be called before key entry"
        await page.locator("#gemini-key").fill("invalid-test-key")
        await page.get_by_role("button", name="키 연결", exact=True).click()
        await page.wait_for_selector(".gemini-settings .gemini-error")
        assert "API" in await page.locator(".gemini-settings .gemini-error").inner_text()
        await page.locator("#gemini-key").fill(KEY)
        await page.get_by_role("button", name="키 연결", exact=True).click()
        await page.wait_for_selector(".gemini-status.ready")
        assert "USD/100만 토큰" in await page.locator(".gemini-inline-price").inner_text()
        await page.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        options = await page.locator("#gemini-model option").all_text_contents()
        assert len(options) == 4, options
        assert "Gemini Flash" in options[1] and "$3.75" in options[1]
        assert "Gemini 2.5 Pro" in options[2] and "무료 플랜 지원" in options[2]
        assert "Gemini Pro" in options[3] and "가격 확인 필요" in options[3]
        assert "Flash Lite" in options[0] and "$0.10" in options[0] and "$0.40" in options[0]
        assert "무료 플랜 지원" in options[0]
        assert "무료 플랜 지원" in await page.locator(".gemini-free-tier").inner_text()
        await page.get_by_role("button", name="설정 접기", exact=True).click()
        print("PASS: left AI tab, union of free-tier and either sub-dollar rate models, price and free-tier labels.", flush=True)
        print("PASS: key required, credential error, real model-list request contract and connection state.", flush=True)

        async def ask(question):
            await page.get_by_role("textbox", name="Gemini에게 질문", exact=True).fill(question)
            await page.get_by_role("button", name="Gemini 질문 보내기").click()
            await page.wait_for_function("!document.querySelector('[aria-label=\"Gemini 응답 중지\"]')")

        question_box = page.get_by_role("textbox", name="Gemini에게 질문", exact=True)
        await question_box.fill("한글 입력 중")
        before = len([r for r in requests if r["body"]])
        await question_box.evaluate("e => e.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',keyCode:229,isComposing:true,bubbles:true,cancelable:true}))")
        await question_box.press("Shift+Enter")
        assert len([r for r in requests if r["body"]]) == before
        assert "\n" in await question_box.input_value()
        await question_box.fill("내 코드의 오류 원인을 알려줘")
        await question_box.press("Enter")
        await page.wait_for_function("!document.querySelector('[aria-label=\"Gemini 응답 중지\"]')")
        await page.wait_for_selector(".gemini-answer .gemini-markdown")
        sent = [r for r in requests if r["body"]][-1]
        assert "streamGenerateContent?alt=sse" in sent["url"]
        assert await page.locator(".gemini-question").first.evaluate("e=>getComputedStyle(e).backgroundColor") == "rgb(223, 242, 255)"
        payload = sent["body"]
        raw = payload["contents"][-1]["parts"][0]["text"]
        snapshot = json.loads(raw[raw.index("{"):])
        assert snapshot["currentCode"] == source
        assert snapshot["problem"]["id"] == "t1-01"
        assert snapshot["problem"]["datasets"][0]["totalRows"] == 360
        assert "CONTEXT_ERROR" in snapshot["lastExecution"]["error"]
        assert "CONTEXT_STDOUT" in snapshot["lastExecution"]["stdout"]
        assert snapshot["lastExecution"]["matchesCurrentCode"] is True
        assert KEY not in json.dumps(payload)
        assert await page.get_by_role("textbox", name="Gemini Python 예시").get_attribute("contenteditable") == "false"
        assert not await page.evaluate("window.__gemini_xss || false")
        assert not await page.locator('.gemini-markdown a[href^="javascript:"]').count()
        await page.screenshot(path="/tmp/bigbungi-gemini.png", full_page=True)
        print("PASS: current problem, edited code and actual Python traceback sent; Markdown/code render safely.", flush=True)

        await question_box.fill("확대해도 남아야 하는 질문 초안")
        normal_height = (await page.locator(".gemini-messages").bounding_box())["height"]
        generation_count = len([r for r in requests if r["body"]])
        await page.get_by_role("button", name="AI 대화 확대", exact=True).click()
        assert await page.get_by_role("button", name="AI 대화 축소", exact=True).get_attribute("aria-expanded") == "true"
        for selector in [".problem-heading", ".panel-tabs", ".problem-footer", ".gemini-context-bar", ".gemini-status"]:
            assert not await page.locator(".problem-panel " + selector).is_visible(), selector
        panel = await page.locator(".problem-panel").bounding_box()
        messages = await page.locator(".gemini-messages").bounding_box()
        composer = await page.locator(".gemini-composer").bounding_box()
        assert abs(messages["y"] - panel["y"] - 1) < 2, (panel, messages)
        assert abs(composer["y"] + composer["height"] - panel["y"] - panel["height"] + 1) < 2, (panel, composer)
        assert messages["height"] > normal_height + 100
        assert await question_box.input_value() == "확대해도 남아야 하는 질문 초안"
        assert len([r for r in requests if r["body"]]) == generation_count
        await page.screenshot(path="/tmp/bigbungi-gemini-expanded.png", full_page=True)
        await question_box.press("Escape")
        assert await page.locator(".problem-heading").is_visible()
        assert await question_box.input_value() == "확대해도 남아야 하는 질문 초안"
        await page.get_by_role("button", name="AI 대화 확대", exact=True).click()
        await page.get_by_role("button", name="AI 대화 축소", exact=True).click()
        assert await page.get_by_role("tablist", name="문제 정보", exact=True).is_visible()
        assert await page.locator(".gemini-turn").count() == 1
        print("PASS: expanded chat and bottom composer fill the whole problem panel; Escape/collapse preserve draft and conversation.", flush=True)

        await edit('print("UPDATED_CODE")')
        await ask("할당량 테스트")
        await page.wait_for_selector(".gemini-turn .gemini-error")
        assert "사용 한도" in await page.locator(".gemini-turn .gemini-error").inner_text()
        await edit('print("RETRY_LATEST_CODE")')
        await page.get_by_role("button", name="다시 시도", exact=True).click()
        await page.wait_for_function("document.querySelectorAll('.gemini-answer .gemini-markdown').length === 2")
        assert await page.locator(".gemini-turn").count() == 2
        retried = [r["body"] for r in requests if r["body"]][-1]
        assert len(retried["contents"]) == 3
        assert "RETRY_LATEST_CODE" in retried["contents"][-1]["parts"][0]["text"]
        assert '"matchesCurrentCode":false' in retried["contents"][-1]["parts"][0]["text"]
        print("PASS: quota feedback, retry without duplicate turns, latest code snapshot and multi-turn history.", flush=True)

        await page.locator(".question-link").nth(1).click()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert not await page.locator(".gemini-turn").count()
        await ask("두 번째 문제 힌트")
        body = [r["body"] for r in requests if r["body"]][-1]
        assert len(body["contents"]) == 1
        assert '"id":"t1-02"' in body["contents"][0]["parts"][0]["text"]
        await page.locator(".question-link").nth(0).click()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert await page.locator(".gemini-turn").count() == 2
        print("PASS: conversations and contexts remain separate when changing problems.", flush=True)

        # Notes use the same selected model and key, with no second settings form.
        await page.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        await page.locator("#gemini-model").select_option("models/gemini-2.5-pro")
        await page.get_by_role("button", name="설정 접기", exact=True).click()
        await page.get_by_role("tab", name="노트", exact=True).click()
        assert await page.locator("#gemini-model:visible, #gemini-key:visible").count() == 0
        await page.get_by_role("textbox", name="풀이 노트", exact=True).fill("직접 작성한 메모")
        await page.get_by_role("button", name="AI 대화로 노트 생성", exact=True).click()
        await page.wait_for_selector(".note-ai [role=alert]")
        assert "사용 한도" in await page.locator(".note-ai [role=alert]").inner_text()
        assert await page.get_by_role("textbox", name="풀이 노트", exact=True).input_value() == "직접 작성한 메모"
        await page.get_by_role("button", name="AI 대화로 노트 생성", exact=True).click()
        await page.get_by_role("button", name="노트 생성 중지", exact=True).wait_for()
        await page.get_by_role("textbox", name="풀이 노트", exact=True).fill("생성 중 수정한 메모")
        await page.locator(".question-link").nth(1).click()
        await page.get_by_role("tab", name="노트", exact=True).click()
        assert not await page.locator(".note-ai-preview").count()
        await page.get_by_role("textbox", name="풀이 노트", exact=True).fill("두 번째 문제 메모")
        note_release.set()
        await page.locator(".question-link").nth(0).click()
        await page.get_by_role("tab", name="노트", exact=True).click()
        await page.wait_for_selector(".note-ai-preview")
        assert await page.get_by_role("textbox", name="Gemini Python 예시", exact=True).get_attribute("contenteditable") == "false"
        sent_note = [r for r in requests if r["body"]][-1]
        assert sent_note["url"].endswith("models/gemini-2.5-pro:generateContent")
        assert sent_note["key"] == KEY
        note_data = json.loads(sent_note["body"]["contents"][0]["parts"][0]["text"])
        assert len(note_data["conversations"]) == 2
        assert list(note_data) == ["conversations"]
        assert "두 번째 문제 힌트" not in json.dumps(note_data,ensure_ascii=False)
        await page.get_by_role("button", name="내 노트에 추가", exact=True).click()
        note = await page.get_by_role("textbox", name="풀이 노트", exact=True).input_value()
        assert note.startswith("생성 중 수정한 메모\n\nQ. 오류 원인은?")
        assert "```python\nprint('Gemini 코드 예시')\n```" in note
        assert not await page.locator(".note-ai-preview").count()
        await page.locator(".question-link").nth(1).click()
        await page.get_by_role("tab", name="노트", exact=True).click()
        assert await page.get_by_role("textbox", name="풀이 노트", exact=True).input_value() == "두 번째 문제 메모"
        await page.locator(".question-link").nth(0).click()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert await page.locator(".gemini-turn").count() == 2
        print("PASS: AI notes share model/key, include only this problem's completed chats, handle quota and preserve concurrent edits across navigation.", flush=True)

        await page.get_by_role("textbox", name="Gemini에게 질문", exact=True).fill("중지 테스트")
        await page.get_by_role("button", name="Gemini 질문 보내기").click()
        await page.get_by_role("button", name="Gemini 응답 중지").click()
        await page.wait_for_function("document.querySelector('.gemini-messages').textContent.includes('중지했습니다')")
        release.set()
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_function("document.querySelector('.sidebar').getBoundingClientRect().right <= 0.1")
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        await page.get_by_role("textbox", name="Gemini에게 질문", exact=True).scroll_into_view_if_needed()
        assert await page.get_by_role("textbox", name="Gemini에게 질문", exact=True).is_visible()
        await ask("모바일 질문 테스트")
        await page.get_by_role("button", name="AI 대화 확대", exact=True).click()
        assert await page.locator(".problem-panel.gemini-expanded .gemini-composer").is_visible()
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        await page.screenshot(path="/tmp/bigbungi-gemini-expanded-mobile.png", full_page=True)
        await page.get_by_role("button", name="AI 대화 축소", exact=True).click()
        await page.screenshot(path="/tmp/bigbungi-gemini-mobile.png", full_page=True)

        stored = await page.evaluate("JSON.stringify({...localStorage}) + JSON.stringify({...sessionStorage})")
        assert KEY not in stored, "API key persisted in browser storage"
        await page.reload(wait_until="networkidle")
        await page.get_by_role("tab", name="노트", exact=True).click()
        assert await page.get_by_role("textbox", name="풀이 노트", exact=True).input_value() == note
        assert await page.get_by_role("button", name="AI 대화로 노트 생성", exact=True).is_disabled()
        await page.get_by_role("button", name="AI 질문에서 키와 모델 연결하기", exact=True).click()
        assert await page.locator("#gemini-key").input_value() == ""
        assert await page.get_by_role("button", name="Gemini 질문 보내기").is_disabled()
        await page.screenshot(path="/tmp/bigbungi-gemini-key-setup-mobile.png", full_page=True)
        assert not errors, errors
        print("PASS: cancellation, mobile layout, no key persistence and key cleared after reload.", flush=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
