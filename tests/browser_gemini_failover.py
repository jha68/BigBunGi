"""Two-key failover against the real local Worker/D1 and mocked Google API.

Build web with VITE_SYNC_API_URL, serve dist, and run sync/test-server.mjs.
Set SYNC_TEST_WEB and SYNC_TEST_PORT to those local servers. No paid API calls.
"""
import asyncio
import json
import os

from playwright.async_api import async_playwright, Error as PlaywrightError
from browser_sync import local_fetch, ORIGIN, API, PASSWORD

KEYS = ["test-only-primary-gemini-key", "test-only-secondary-gemini-key"]
MODEL = "models/gemini-2.5-flash"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", headless=True)
        modes = {key: "success" for key in KEYS}
        sent, page_errors = [], []
        release = asyncio.Event()
        cors = {"access-control-allow-origin": ORIGIN, "access-control-allow-headers": "content-type,x-goog-api-key", "access-control-allow-methods": "GET,POST,OPTIONS"}
        failure = {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "quota " + "diagnostic " * 200 + " ".join(KEYS), "details": [{"retryDelay": "32s", "quotaId": "FreeTier"}]}}

        async def proxy(route):
            req, url = route.request, route.request.url
            if url.startswith("https://generativelanguage.googleapis.com/"):
                if req.method == "OPTIONS":
                    await route.fulfill(status=204, headers=cors); return
                key = req.headers.get("x-goog-api-key")
                assert key in KEYS
                if req.method == "GET":
                    await route.fulfill(status=200, content_type="application/json", headers=cors, body=json.dumps({"models": [
                        {"name": "models/gemini-2.5-flash-lite", "supportedGenerationMethods": ["generateContent"]},
                        {"name": MODEL, "supportedGenerationMethods": ["generateContent"]},
                    ]})); return
                payload = req.post_data_json
                sent.append({"key": key, "url": url, "payload": payload})
                assert not any(secret in json.dumps(payload) for secret in KEYS)
                mode = modes[key]
                if mode == "hang":
                    await release.wait()
                if mode == "http-error":
                    body = {"error": {**failure["error"], "code": 503 if key == KEYS[1] else 429}}
                    await route.fulfill(status=body["error"]["code"], content_type="application/json", headers=cors, body=json.dumps(body)); return
                streaming = ":streamGenerateContent" in url
                if mode == "stream-error":
                    partial = {"candidates": [{"content": {"parts": [{"text": "폐기할 이전 응답 조각"}]}}]}
                    await route.fulfill(status=200, content_type="text/event-stream", headers=cors, body="data: " + json.dumps(partial) + "\n\ndata: " + json.dumps(failure) + "\n\n"); return
                answer = f"{KEYS.index(key) + 1}번 키의 정상 답변" if streaming else "Q. 핵심은?\nA. 결측치를 대체하세요.\n```python\ndf.fillna(0)\n```"
                body = {"candidates": [{"content": {"parts": [{"text": answer}]}, "finishReason": "STOP"}]}
                try:
                    await route.fulfill(status=200, content_type="text/event-stream" if streaming else "application/json", headers=cors, body=("data: " + json.dumps(body) + "\n\n") if streaming else json.dumps(body))
                except PlaywrightError:
                    if mode != "hang": raise
                return
            if url.startswith(API):
                target = "http://127.0.0.1:" + os.environ.get("SYNC_TEST_PORT", "4312") + url[len(API):]
            elif url.startswith(ORIGIN):
                target = os.environ.get("SYNC_TEST_WEB", "http://127.0.0.1:4213") + url[len(ORIGIN):]
            else:
                await route.abort(); return
            status, headers, body = await asyncio.to_thread(local_fetch, target, req.method, req.post_data_buffer,
                {key: value for key, value in (await req.all_headers()).items() if key.lower() not in ("host", "content-length", "accept-encoding")})
            await route.fulfill(status=status, headers=headers, body=body)

        async def new_page():
            ctx = await browser.new_context(viewport={"width": 1440, "height": 1000})
            await ctx.route("**/*", proxy)
            page = await ctx.new_page(); page.on("pageerror", lambda error: page_errors.append(str(error)))
            await page.goto(ORIGIN)
            await page.get_by_label("비밀번호", exact=True).fill(PASSWORD)
            await page.get_by_role("button", name="로그인", exact=True).click()
            await page.locator(".sync-status.saved").wait_for()
            await page.get_by_role("tab", name="AI 질문", exact=True).click()
            return ctx, page

        async def history_saved(page):
            await page.locator(".gemini-history-status.saved").wait_for(timeout=15000)
            await page.wait_for_function("!document.querySelector('.gemini-stop')")

        async def ask(page, text):
            count = await page.locator(".gemini-turn").count()
            field = page.get_by_label("Gemini에게 질문", exact=True)
            await field.fill(text); await field.press("Enter")
            await page.wait_for_function("count => document.querySelectorAll('.gemini-turn').length === count + 1 && !document.querySelector('.gemini-stop')", arg=count)
            await history_saved(page)

        async def vault(page):
            await page.wait_for_function("document.querySelector('.gemini-persistence').textContent.includes('계정에 저장됨')")
            return await page.evaluate("async api => (await (await fetch(api + '/settings', {credentials:'include'})).json()).settings", API)

        ctx, page = await new_page()
        await page.locator("#gemini-key").fill(KEYS[0])
        await page.locator("#gemini-backup-key").fill(KEYS[1])
        await page.get_by_role("button", name="키 연결", exact=True).click()
        await page.locator(".gemini-status.ready").wait_for()
        await page.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        await page.locator("#gemini-model").select_option(MODEL)
        assert await vault(page) == {"apiKey": KEYS[0], "backupApiKey": KEYS[1], "activeKeyIndex": 0, "model": MODEL}
        modes[KEYS[0]] = "stream-error"
        await ask(page, "질문에 붙인 키도 숨겨줘 " + " ".join(KEYS))
        assert [request["key"] for request in sent] == KEYS
        assert sent[0]["payload"] == sent[1]["payload"]
        assert all(MODEL in request["url"] for request in sent)
        assert await page.locator(".gemini-turn").count() == 1
        answer = await page.locator(".gemini-answer").inner_text()
        assert "2번 키의 정상 답변" in answer and "폐기할 이전 응답 조각" not in answer
        assert "HTTP 200" in await page.locator(".gemini-key-retry pre").text_content()
        transcript = await page.locator(".gemini-messages").text_content()
        assert not any(secret in transcript for secret in KEYS)
        assert (await vault(page))["activeKeyIndex"] == 1
        print("PASS: partial streaming failure retries once with the same model/context and second key, without duplicate or mixed answers.", flush=True)

        await page.reload()
        await page.locator(".sync-status.saved").wait_for()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        await page.locator(".gemini-status.ready").wait_for()
        await page.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        assert await page.locator("#gemini-key").input_value() == KEYS[0]
        assert await page.locator("#gemini-backup-key").input_value() == KEYS[1]
        assert await page.locator("#gemini-model").input_value() == MODEL
        before = len(sent); await ask(page, "다음 질문")
        assert [request["key"] for request in sent[before:]] == [KEYS[1]]
        other_ctx, other = await new_page()
        await other.locator(".gemini-status.ready").wait_for()
        await other.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        assert await other.locator("#gemini-backup-key").input_value() == KEYS[1]
        assert (await vault(other))["activeKeyIndex"] == 1
        await other_ctx.close()
        print("PASS: both keys, model, successful key choice and retry history restore after refresh and on another device.", flush=True)

        modes[KEYS[0]], modes[KEYS[1]] = "success", "http-error"
        before = len(sent)
        await page.get_by_role("tab", name="노트", exact=True).click()
        await page.get_by_role("button", name="AI 대화로 노트 생성", exact=True).click()
        await page.locator(".note-ai-preview").wait_for()
        assert [request["key"] for request in sent[before:]] == [KEYS[1], KEYS[0]]
        assert sent[-1]["payload"] == sent[-2]["payload"]
        assert "1번 API 키로 재시도" in await page.locator(".note-ai .gemini-key-retry").inner_text()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert (await vault(page))["activeKeyIndex"] == 0

        modes[KEYS[0]] = modes[KEYS[1]] = "http-error"
        before = len(sent); await ask(page, "두 키 모두 실패")
        assert [request["key"] for request in sent[before:]] == KEYS
        failure_text = await page.locator(".gemini-turn").last.locator(".gemini-error > span").text_content()
        assert "API 키 1\nHTTP 429" in failure_text and "API 키 2\nHTTP 503" in failure_text
        assert "retryDelay" in failure_text and not any(key in failure_text for key in KEYS)
        stored = await page.evaluate("async api => (await (await fetch(api + '/conversations/t1-01', {credentials:'include'})).json()).turns", API)
        assert stored[-1]["error"] == failure_text and len(failure_text) > 1500
        print("PASS: AI notes share failover settings; two failed keys show and persist both complete original errors.", flush=True)

        modes[KEYS[0]] = "hang"; modes[KEYS[1]] = "success"
        before = len(sent)
        field = page.get_by_label("Gemini에게 질문", exact=True)
        await field.fill("사용자 중지"); await field.press("Enter")
        await page.wait_for_function("!!document.querySelector('.gemini-stop')")
        for _ in range(50):
            if len(sent) > before: break
            await page.wait_for_timeout(20)
        await page.get_by_role("button", name="Gemini 응답 중지", exact=True).click()
        await history_saved(page); release.set()
        assert [request["key"] for request in sent[before:]] == [KEYS[0]]
        modes[KEYS[0]] = "success"
        if not await page.locator("#gemini-backup-key").is_visible():
            await page.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        await page.locator("#gemini-backup-key").fill("")
        await page.get_by_role("button", name="키 연결", exact=True).click()
        await page.locator(".gemini-status.ready").wait_for()
        assert (await vault(page))["backupApiKey"] == ""
        storage = await page.evaluate("JSON.stringify({...localStorage}) + JSON.stringify({...sessionStorage})")
        assert not any(key in storage for key in KEYS)
        await page.set_viewport_size({"width": 390, "height": 844})
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        await page.screenshot(path="/tmp/bigbungi-two-keys-mobile.png", full_page=True)
        await page.get_by_role("button", name="저장된 키·모델 삭제", exact=True).click()
        await page.wait_for_function("document.querySelector('.gemini-persistence').textContent.includes('키를 연결하면')")
        await page.reload(); await page.locator(".sync-status.saved").wait_for()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert await page.locator("#gemini-key").input_value() == ""
        assert await page.locator("#gemini-backup-key").input_value() == ""
        assert not page_errors, page_errors
        print("PASS: cancel never retries, removing a backup is saved, both keys stay out of browser storage, mobile fits, and vault deletion clears both keys.", flush=True)
        await ctx.close(); await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
