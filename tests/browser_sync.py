"""Real Worker + D1 integration with two browser sessions; no Cloudflare credentials.

Build web with VITE_SYNC_API_URL=https://bigbungi-api.junununseo.com, serve its
dist at :4195, and run `node sync/test-server.mjs` before this script.
"""
import asyncio
import json
import os
import urllib.request
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

ORIGIN = "https://bigbungi.junununseo.com"
API = "https://bigbungi-api.junununseo.com"
PASSWORD = "test-only-sync-password"
GEMINI_KEY = "test-only-persisted-gemini-key"
GEMINI_MODEL = "models/gemini-2.5-flash"
STORAGE = "bigbungi.practice.v1"

def local_fetch(url, method, body, headers):
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, {key: value for key, value in response.headers.items() if key.lower() not in ("content-length", "connection", "transfer-encoding")}, response.read()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", headless=True)
        offline = False
        async def context(seed=None):
            ctx = await browser.new_context()
            if seed:
                await ctx.add_init_script(f"if (!localStorage.getItem('{STORAGE}')) localStorage.setItem('{STORAGE}', {json.dumps(json.dumps(seed))});")
            async def proxy(route):
                url = route.request.url
                if url.startswith("https://generativelanguage.googleapis.com/"):
                    headers = {"access-control-allow-origin": ORIGIN, "access-control-allow-headers":"content-type,x-goog-api-key", "access-control-allow-methods":"GET,POST,OPTIONS"}
                    if route.request.method == "OPTIONS":
                        await route.fulfill(status=204,headers=headers); return
                    assert route.request.headers.get("x-goog-api-key") == GEMINI_KEY
                    if route.request.method == "POST":
                        reply = {"candidates":[{"content":{"parts":[{"text":"중앙값으로 결측값을 채우세요.\n```python\ndf.fillna(df.median(numeric_only=True))\n```"}]},"finishReason":"STOP"}]}
                        if ":streamGenerateContent" in url:
                            await route.fulfill(status=200,content_type="text/event-stream",body="data: " + json.dumps(reply) + "\n\n",headers=headers)
                        else:
                            await route.fulfill(status=200,content_type="application/json",body=json.dumps(reply),headers=headers)
                        return
                    body = {"models":[{"name":"models/gemini-2.5-flash-lite","displayName":"Flash Lite","supportedGenerationMethods":["generateContent"]},{"name":GEMINI_MODEL,"displayName":"Gemini 2.5 Flash","supportedGenerationMethods":["generateContent"]}]}
                    await route.fulfill(status=200,content_type="application/json",body=json.dumps(body),headers=headers); return
                if url.startswith(API):
                    if offline and route.request.method == "PUT":
                        await route.abort(); return
                    target = "http://127.0.0.1:" + os.environ.get("SYNC_TEST_PORT", "4301") + url[len(API):]
                elif url.startswith(ORIGIN):
                    target = os.environ.get("SYNC_TEST_WEB", "http://127.0.0.1:4195") + url[len(ORIGIN):]
                else:
                    await route.abort(); return
                status, headers, body = await asyncio.to_thread(local_fetch, target, route.request.method, route.request.post_data_buffer,
                    {key: value for key, value in (await route.request.all_headers()).items() if key.lower() not in ("host", "content-length", "accept-encoding")})
                await route.fulfill(status=status, headers=headers, body=body)
            await ctx.route("**/*", proxy)
            return ctx
        async def login(page, password=PASSWORD):
            await page.get_by_label("비밀번호", exact=True).fill(password)
            await page.get_by_role("button", name="로그인", exact=True).click()
        async def saved(page):
            await page.locator(".sync-status.saved").wait_for(timeout=15000)
            await page.locator(".problem-heading").wait_for()
            try:
                await page.get_by_role("button", name="이어서 풀기", exact=True).wait_for(timeout=800)
                await page.get_by_role("button", name="이어서 풀기", exact=True).click()
            except PlaywrightTimeoutError:
                pass
        async def edit(page, text):
            editor = page.get_by_role("textbox", name="Python 코드 편집기", exact=True)
            await editor.click(); await editor.press("Control+a"); await page.keyboard.insert_text(text)
        async def conversation_saved(page):
            await page.locator(".gemini-history-status.saved").wait_for(timeout=15000)
            await page.wait_for_function("!document.querySelector('.gemini-stop')")
        async def ask(page, question):
            await page.get_by_label("Gemini에게 질문", exact=True).fill(question)
            await page.get_by_label("Gemini에게 질문", exact=True).press("Enter")
            await page.wait_for_function("!document.querySelector('.gemini-stop') && document.querySelector('.gemini-input-wrap textarea').value === ''")
        seed = {"drafts": {"t1-01": "print('import me')"}, "notes": {"t1-01": "내 기존 노트"}, "answers": {"t1-01": {"result": "42"}}, "progress": {"t1-01": {"passed": True}}, "selected": "t1-01"}
        a = await context(seed); page = await a.new_page(); await page.goto(ORIGIN)
        assert await page.locator(".coding-panel").count() == 0
        await login(page, "wrong")
        await page.get_by_role("alert").wait_for()
        assert "비밀번호" in await page.get_by_role("alert").inner_text()
        await login(page)
        await page.get_by_role("button", name="이 브라우저 기록 가져오기", exact=True).click()
        await saved(page)
        await edit(page, 'print("DEVICE_ONE")'); await saved(page)

        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        await page.locator("#gemini-key").fill(GEMINI_KEY)
        await page.get_by_role("button", name="키 연결", exact=True).click()
        await page.wait_for_selector(".gemini-status.ready")
        await page.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        await page.locator("#gemini-model").select_option(GEMINI_MODEL)
        await page.wait_for_function("document.querySelector('.gemini-persistence').textContent.includes('계정에 저장됨')")
        await ask(page, "결측값은 어떻게 처리해?"); await conversation_saved(page)
        await page.reload()
        await saved(page)
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        await page.wait_for_selector(".gemini-status.ready")
        await page.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        assert await page.locator("#gemini-model").input_value() == GEMINI_MODEL
        assert await page.locator("#gemini-key").input_value() == GEMINI_KEY
        assert "결측값은 어떻게 처리해?" in await page.locator(".gemini-messages").inner_text()
        assert "중앙값으로 결측값을 채우세요." in await page.locator(".gemini-messages").inner_text()
        assert await page.locator(".gemini-answer .cm-editor").count() == 1
        await page.locator(".question-link").first.click()
        await page.get_by_role("button", name="코드만 초기화", exact=True).click()
        await saved(page)
        assert "결측값은 어떻게 처리해?" in await page.locator(".gemini-messages").inner_text()
        await edit(page, 'print("DEVICE_ONE")'); await saved(page)
        await page.get_by_role("tab", name="노트", exact=True).click()
        assert await page.get_by_role("button", name="AI 대화로 노트 생성", exact=True).is_enabled()
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert GEMINI_KEY not in await page.evaluate("JSON.stringify({...localStorage}) + JSON.stringify({...sessionStorage})")
        print("PASS: encrypted Gemini key and selected model automatically restore after refresh without browser storage.", flush=True)
        print("PASS: AI questions, answers and code blocks restore after refresh, survive code-only reset and remain available to note generation.", flush=True)

        b = await context(); other = await b.new_page(); await other.goto(ORIGIN); await login(other)
        await saved(other)
        await other.get_by_role("tab", name="AI 질문", exact=True).click()
        await other.wait_for_selector(".gemini-status.ready")
        assert "Gemini 2.5 Flash" in await other.locator(".gemini-selected-model").inner_text()
        assert "결측값은 어떻게 처리해?" in await other.locator(".gemini-messages").inner_text()
        await ask(other, "다른 기기에서 질문"); await conversation_saved(other)
        await ask(page, "기존 기기에서 질문 " + GEMINI_KEY)
        await page.locator(".gemini-history-status.conflict").wait_for()
        assert GEMINI_KEY not in await page.locator(".gemini-messages").inner_text()
        await page.get_by_role("button", name="현재 변경 다시 저장", exact=True).click(); await conversation_saved(page)
        assert await page.locator(".gemini-turn").count() == 3
        assert "다른 기기에서 질문" in await page.locator(".gemini-messages").inner_text()
        assert "기존 기기에서 질문" in await page.locator(".gemini-messages").inner_text()
        offline = True
        await ask(page, "오프라인 저장 재시도")
        await page.locator(".gemini-history-status.error").wait_for()
        assert await page.locator(".gemini-turn").count() == 4
        offline = False
        await page.get_by_role("button", name="대화 저장·복원 재시도", exact=True).click(); await conversation_saved(page)
        browser_storage = await page.evaluate("JSON.stringify({...localStorage}) + JSON.stringify({...sessionStorage})")
        assert "결측값은 어떻게 처리해?" not in browser_storage and GEMINI_KEY not in browser_storage
        print("PASS: another device restores AI history; concurrent edits merge explicitly, offline retry retains answers, and API keys are redacted.", flush=True)
        await saved(other)
        assert "DEVICE_ONE" in await other.get_by_role("textbox", name="Python 코드 편집기", exact=True).inner_text()
        assert await other.locator(".question-link .solved-icon").count() == 1
        await other.get_by_role("tab", name="노트", exact=True).click()
        assert await other.get_by_role("textbox", name="풀이 노트", exact=True).input_value() == "내 기존 노트"
        assert "42" in await other.evaluate(f"localStorage.getItem('{STORAGE}')")
        await edit(other, 'print("DEVICE_TWO")'); await saved(other)
        print("PASS: password gate, existing records imported, code/answers/notes/progress restored on another device.", flush=True)

        await edit(page, 'print("STALE_DEVICE")')
        await page.get_by_role("dialog", name="기록 충돌 해결").wait_for()
        await page.get_by_role("button", name="서버 기록 확인하기", exact=True).click()
        await page.get_by_role("button", name="서버 기록으로 이어하기", exact=True).click()
        await saved(page)
        assert "DEVICE_TWO" in await page.get_by_role("textbox", name="Python 코드 편집기", exact=True).inner_text()
        print("PASS: stale device cannot silently overwrite server records; explicit conflict resolution restores the chosen state.", flush=True)

        offline = True
        await edit(page, 'print("OFFLINE_EDIT")')
        await page.locator(".sync-status.error").wait_for()
        assert "OFFLINE_EDIT" in await page.evaluate(f"localStorage.getItem('{STORAGE}')")
        offline = False
        await page.get_by_role("button", name="다시 저장", exact=True).click(); await saved(page)
        await a.clear_cookies()
        await edit(page, 'print("EXPIRED_SESSION_EDIT")')
        await page.get_by_role("button", name="로그인", exact=True).wait_for()
        assert "EXPIRED_SESSION_EDIT" in await page.evaluate(f"localStorage.getItem('{STORAGE}')")
        await login(page)
        page.once("dialog", lambda dialog: dialog.accept())
        await page.get_by_role("button", name="이 브라우저 기록 가져오기", exact=True).click(); await saved(page)
        assert "EXPIRED_SESSION_EDIT" in await page.get_by_role("textbox", name="Python 코드 편집기", exact=True).inner_text()
        print("PASS: network errors and expired sessions preserve edits, retry and re-login restore synchronization.", flush=True)

        await page.set_viewport_size({"width": 390, "height": 844})
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        await page.get_by_role("button", name="로그아웃", exact=True).click()
        await page.get_by_role("button", name="로그인", exact=True).wait_for()
        assert await page.locator(".coding-panel").count() == 0
        assert PASSWORD not in await page.evaluate("JSON.stringify({...localStorage}) + JSON.stringify({...sessionStorage})")
        assert not any(cookie["name"] == "__Host-bigbungi-session" for cookie in await a.cookies())
        await page.screenshot(path="/tmp/bigbungi-sync-login.png")
        await login(page)
        await saved(page)
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        await page.wait_for_selector(".gemini-status.ready")
        await page.get_by_role("button", name="Gemini 연결 설정", exact=True).click()
        assert await page.locator("#gemini-model").input_value() == GEMINI_MODEL
        assert await page.locator(".gemini-turn").count() == 4
        await page.get_by_role("button", name="저장된 키·모델 삭제", exact=True).click()
        await page.wait_for_function("document.querySelector('.gemini-persistence').textContent.includes('키를 연결하면')")
        await page.reload()
        await saved(page)
        await page.get_by_role("tab", name="AI 질문", exact=True).click()
        assert await page.locator("#gemini-key").input_value() == ""
        assert await page.get_by_role("button", name="Gemini 질문 보내기").is_disabled()
        assert await page.locator(".gemini-turn").count() == 4
        page.once("dialog", lambda dialog: dialog.accept())
        await page.get_by_role("button", name="이 문제의 AI 대화 지우기", exact=True).click(); await conversation_saved(page)
        await page.reload(); await saved(page)
        await page.get_by_role("tab", name="AI 질문", exact=True).click(); await conversation_saved(page)
        assert await page.locator(".gemini-turn").count() == 0
        print("PASS: AI history survives logout/login and Gemini key deletion; explicit conversation deletion persists after refresh.", flush=True)
        print("PASS: key/model survive logout and another device; explicit deletion persists after refresh.", flush=True)
        print("PASS: mobile layout, logout removes session and app access, password never stored in browser storage.", flush=True)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
