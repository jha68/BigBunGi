"""Real keyboard, mouse selection and read-only solution regressions."""
import asyncio
import os

from playwright.async_api import async_playwright

from browser_smoke import verified_download


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium"),
            headless=True,
            proxy={"server": os.environ["HTTPS_PROXY"], "bypass": "localhost,127.0.0.1"}
            if os.environ.get("HTTPS_PROXY") else None,
        )
        errors = []

        async def open_page(platform):
            context = await browser.new_context(viewport={"width": 1512, "height": 1080})
            await context.add_init_script(
                f"Object.defineProperty(navigator, 'platform', {{get: () => {platform!r}}});"
            )

            async def bridge(route):
                body, kind = await asyncio.to_thread(verified_download, route.request.url)
                await route.fulfill(status=200, body=body, content_type=kind,
                                    headers={"access-control-allow-origin": "*", "cross-origin-resource-policy": "cross-origin"})

            await context.route("https://cdn.jsdelivr.net/pyodide/**", bridge)
            page = await context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            await page.goto(os.environ.get("APP_URL", "http://127.0.0.1:4175/"), wait_until="networkidle")
            await page.wait_for_function("!document.querySelector('[data-testid=run-code]').disabled", timeout=120000)
            return context, page

        async def replace_code(page, source):
            editor = page.get_by_role("textbox", name="Python 코드 편집기", exact=True)
            await editor.click()
            await editor.press("Control+a")
            if source:
                await page.keyboard.insert_text(source)
            else:
                await editor.press("Backspace")
            return editor

        async def expect_code(page, source):
            await page.wait_for_function(
                "source => [...document.querySelectorAll('.code-editor .cm-line')].map(line => line.textContent).join('\\n') === source",
                arg=source,
            )

        async def check_brackets(page):
            for opening, closing in [("(", ")"), ("[", "]"), ("{", "}"), ("'", "'"), ('"', '"')]:
                for stale_composition in [False, True]:
                    editor = await replace_code(page, "")
                    if stale_composition:
                        # Model a missed compositionend followed by a real,
                        # non-composing beforeinput from the browser.
                        await editor.dispatch_event("compositionstart")
                    await page.keyboard.type(opening)
                    await expect_code(page, opening + closing)
                    await editor.press("Backspace")
                    await expect_code(page, "")
                    await page.keyboard.type(opening + closing)
                    await expect_code(page, opening + closing)

            editor = await replace_code(page, "value")
            await editor.press("Control+a")
            await page.keyboard.type("(")
            await expect_code(page, "(value)")
            await replace_code(page, "pasted = [1, (2, 3)]")
            await expect_code(page, "pasted = [1, (2, 3)]")

            editor = await replace_code(page, "")
            await editor.evaluate("e => { window.imeEnds = 0; e.addEventListener('compositionend', () => window.imeEnds++); }")
            cdp = await page.context.new_cdp_session(page)
            for syllable in ["ㅎ", "하", "한"]:
                await cdp.send("Input.imeSetComposition", {"text": syllable, "selectionStart": 1, "selectionEnd": 1})
                await expect_code(page, syllable)
            assert await page.evaluate("imeEnds") == 0, "Actual Korean composition was interrupted"
            await page.keyboard.type("[")
            await expect_code(page, "한[]")
            await page.keyboard.type("]")
            await expect_code(page, "한[]")
            assert await page.evaluate("imeEnds") == 1
            await cdp.send("Input.imeSetComposition", {"text": "", "selectionStart": 0, "selectionEnd": 0})
            await cdp.detach()
            print("PASS: brackets/quotes pair, skip closers, delete as pairs and wrap selection; paste is preserved. Missing IME-end recovery preserves live Korean composition.", flush=True)

        async def run_shortcut(page, editor, shortcut, marker):
            before = await editor.inner_text()
            await editor.press(shortcut)
            await page.wait_for_function(
                "marker => document.querySelector('.console-output')?.textContent.includes(marker)", arg=marker, timeout=30000,
            )
            await page.wait_for_function("!!document.querySelector('[data-testid=run-code]') && !document.querySelector('[data-testid=run-code]').disabled")
            assert await editor.inner_text() == before, "Run shortcut changed the source / inserted a blank line"
            assert await page.get_by_test_id("python-error").count() == 0

        context, page = await open_page("Win32")
        await check_brackets(page)
        editor = await replace_code(page, 'print("WINDOWS_CTRL_ENTER_OK")\n')
        await run_shortcut(page, editor, "Control+Enter", "WINDOWS_CTRL_ENTER_OK")
        before = await editor.inner_text()
        await editor.press("Control+End")
        await editor.press("Enter")
        assert await editor.inner_text() != before, "Plain Enter must still insert a newline"
        print("PASS: Windows Ctrl+Enter runs real Python without modifying code; plain Enter still edits.", flush=True)

        editor = await replace_code(page, '# 선택 영역 테스트\nimport pandas as pd\ncustomers = pd.read_csv("data/customers.csv")\nprint(customers.head())\n')
        lines = page.locator(".code-editor .cm-line")
        first, last = await lines.nth(1).bounding_box(), await lines.nth(3).bounding_box()
        await page.mouse.move(first["x"]+10, first["y"]+first["height"]/2)
        await page.mouse.down()
        await page.mouse.move(last["x"]+160, last["y"]+last["height"]/2, steps=12)
        await page.mouse.up()
        await page.wait_for_function("document.querySelectorAll('.code-editor .cm-selectionBackground').length >= 2")
        selected = await page.evaluate("getSelection().toString()")
        assert "read_csv" in selected, selected
        focused = await page.locator(".code-editor .cm-selectionBackground").first.evaluate(
            "e => ({background: getComputedStyle(e).backgroundColor, outline: getComputedStyle(e).boxShadow})"
        )
        assert focused["background"] == "rgb(53, 111, 172)", focused
        assert focused["outline"] != "none", focused
        await page.screenshot(path="/tmp/bigbungi-code-selection.png", full_page=True)
        await page.get_by_role("button", name="코드 글자 크기 키우기").click()
        blurred = await page.locator(".code-editor .cm-selectionBackground").first.evaluate("e => getComputedStyle(e).backgroundColor")
        assert blurred == "rgb(60, 102, 153)", blurred
        print("PASS: mouse-drag selection stays clearly highlighted while focused and after blur.", flush=True)

        await page.get_by_role("button", name="해설 보기", exact=True).click()
        reference = page.get_by_role("textbox", name="Python 기준 풀이", exact=True)
        await reference.wait_for()
        assert await reference.get_attribute("contenteditable") == "false"
        assert await reference.get_attribute("aria-readonly") == "true"
        assert await page.locator(".reference-code .cm-lineNumbers .cm-gutterElement").count() > 5
        colors = await page.locator(".reference-code .cm-line span").evaluate_all(
            "nodes => [...new Set(nodes.map(n => getComputedStyle(n).color))]"
        )
        assert len(colors) >= 4, colors
        before = await reference.inner_text()
        await reference.click()
        await reference.press("End")
        await page.keyboard.insert_text("SHOULD_NOT_EDIT")
        assert await reference.inner_text() == before, "Reference solution must remain read-only"
        assert await page.locator(".reference-code .cm-scroller").evaluate("e => e.scrollWidth <= e.clientWidth + 1"), "Long solution lines should wrap"
        await page.screenshot(path="/tmp/bigbungi-syntax-solution.png", full_page=True)
        print("PASS: solution has syntax colors, line numbers and cannot be edited.", flush=True)

        page.once("dialog", lambda dialog: dialog.accept())
        await page.get_by_role("button", name="에디터에 적용").click()
        await editor.click()
        before = await editor.inner_text()
        await editor.press("Control+Enter")
        await page.wait_for_function("!!document.querySelector('.collected-answers')", timeout=30000)
        await page.wait_for_function("!!document.querySelector('[data-testid=run-code]') && !document.querySelector('[data-testid=run-code]').disabled")
        assert await editor.inner_text() == before
        await page.get_by_test_id("grade-code").click()
        await page.wait_for_selector('[data-testid=grade-result].passed')
        print("PASS: highlighted solution still applies, runs via Ctrl+Enter and grades correctly.", flush=True)
        await context.close()

        mac_context, mac_page = await open_page("MacIntel")
        mac_editor = await replace_code(mac_page, 'print("MAC_CMD_ENTER_OK")\n')
        await run_shortcut(mac_page, mac_editor, "Meta+Enter", "MAC_CMD_ENTER_OK")
        print("PASS: macOS Cmd+Enter binding remains functional.", flush=True)
        assert not errors, errors
        await mac_context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
