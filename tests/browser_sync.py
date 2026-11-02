"""Real Worker + D1 integration with two browser sessions; no Cloudflare credentials.

Build web with VITE_SYNC_API_URL=https://bigbungi-api.junununseo.com, serve its
dist at :4195, and run `node sync/test-server.mjs` before this script.
"""
import asyncio
import json
import urllib.request
from playwright.async_api import async_playwright

ORIGIN = "https://bigbungi.junununseo.com"
API = "https://bigbungi-api.junununseo.com"
PASSWORD = "test-only-sync-password"
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
                if url.startswith(API):
                    if offline and route.request.method == "PUT":
                        await route.abort(); return
                    target = "http://127.0.0.1:4301" + url[len(API):]
                elif url.startswith(ORIGIN):
                    target = "http://127.0.0.1:4195" + url[len(ORIGIN):]
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
        async def edit(page, text):
            editor = page.get_by_role("textbox", name="Python 코드 편집기", exact=True)
            await editor.click(); await editor.press("Control+a"); await page.keyboard.insert_text(text)
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

        b = await context(); other = await b.new_page(); await other.goto(ORIGIN); await login(other)
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
        print("PASS: mobile layout, logout removes session and app access, password never stored in browser storage.", flush=True)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
