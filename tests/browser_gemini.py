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
        headers = {"access-control-allow-origin": "*", "access-control-allow-headers": "content-type,x-goog-api-key", "access-control-allow-methods": "GET,POST,OPTIONS"}

        async def cdn(route):
            body, kind = await asyncio.to_thread(verified_download, route.request.url)
            await route.fulfill(status=200, body=body, content_type=kind, headers={"access-control-allow-origin": "*"})

        async def gemini(route):
            nonlocal quota_once
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
                    {"name": "models/gemini-image", "displayName": "Image", "supportedGenerationMethods": ["generateContent"]},
                ]}
            else:
                payload = req.post_data_json
                question = payload["contents"][-1]["parts"][-1]["text"]
                if "할당량 테스트" in question and not quota_once:
                    quota_once = True
                    status, body = 429, {"error": {"message": "quota exceeded"}}
                else:
                    if "중지 테스트" in question:
                        await release.wait()
                    text = "현재 문제를 참고한 답변입니다.\n\n```python\nprint('Gemini 코드 예시')\n```\n\n<script>window.__gemini_xss = true</script>\n[unsafe](javascript:alert(1))"
                    body = {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}]}
            try:
                await route.fulfill(status=status, content_type="application/json", body=json.dumps(body), headers=headers)
            except PlaywrightError:
                if not release.is_set(): raise

        await context.route("https://cdn.jsdelivr.net/pyodide/**", cdn)
        await context.route("https://generativelanguage.googleapis.com/**", gemini)
        page = await context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto(os.environ.get("APP_URL", "http://127.0.0.1:4175/"), wait_until="networkidle")
        await page.wait_for_function("!document.querySelector('[data-testid=run-code]').disabled", timeout=120000)
        editor = page.get_by_role("textbox", name="Python 코드 편집기", exact=True)

        async def edit(source):
            await editor.click(); await editor.press("Control+a"); await page.keyboard.insert_text(source)

        source = 'print("CONTEXT_STDOUT")\nraise ValueError("CONTEXT_ERROR")'
        await edit(source)
        await editor.press("Control+Enter")
        await page.get_by_test_id("python-error").wait_for()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert await page.get_by_role("button", name="Gemini 질문 보내기").is_disabled()
        assert not requests, "API must not be called before key entry"
        await page.locator("#gemini-key").fill("invalid-test-key")
        await page.get_by_role("button", name="키 연결", exact=True).click()
        await page.wait_for_selector(".gemini-settings .gemini-error")
        assert "API" in await page.locator(".gemini-settings .gemini-error").inner_text()
        await page.locator("#gemini-key").fill(KEY)
        await page.get_by_role("button", name="키 연결", exact=True).click()
        await page.wait_for_selector(".gemini-status.ready")
        print("PASS: key required, credential error, real model-list request contract and connection state.", flush=True)

        async def ask(question):
            await page.get_by_role("textbox", name="Gemini에게 질문", exact=True).fill(question)
            await page.get_by_role("button", name="Gemini 질문 보내기").click()
            await page.wait_for_function("!document.querySelector('[aria-label=\"Gemini 응답 중지\"]')")

        await ask("내 코드의 오류 원인을 알려줘")
        await page.wait_for_selector(".gemini-answer .gemini-markdown")
        sent = [r for r in requests if r["body"]][-1]
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
        await page.screenshot(path="/tmp/bigbungi-gemini-mobile.png", full_page=True)

        stored = await page.evaluate("JSON.stringify({...localStorage}) + JSON.stringify({...sessionStorage})")
        assert KEY not in stored, "API key persisted in browser storage"
        await page.reload(wait_until="networkidle")
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert await page.locator("#gemini-key").input_value() == ""
        assert await page.get_by_role("button", name="Gemini 질문 보내기").is_disabled()
        await page.screenshot(path="/tmp/bigbungi-gemini-key-setup-mobile.png", full_page=True)
        assert not errors, errors
        print("PASS: cancellation, mobile layout, no key persistence and key cleared after reload.", flush=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
