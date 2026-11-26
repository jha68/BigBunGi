"""Verify mock-exam retry marks and scores in a browser with generated content."""
import asyncio
import json
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright, expect


STORAGE = "bigbungi.mock-exam.v1"
KEYS = Path(__file__).resolve().parents[1] / "web/public/content/mock-exams/keys"


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path=os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium"),
            headless=True,
        )
        page = await browser.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        completed = {
            str(round_number): {
                "id": f"old-attempt-{round_number}", "round": round_number,
                "startedAt": 1000, "deadline": 10801000, "submittedAt": 2000,
                "index": 0, "answers": {}, "code": {}, "files": {}, "flags": {}, "memo": "",
            }
            for round_number in (11, 12)
        }
        seed = json.dumps({"active": None, "completed": completed})
        await page.add_init_script(
            f"if (!localStorage.getItem('{STORAGE}')) localStorage.setItem('{STORAGE}', {json.dumps(seed)});"
        )
        await page.goto(os.environ.get("APP_URL", "http://127.0.0.1:4175/") + "#mock-exam")

        def round_card(number):
            return page.locator(".mock-round").filter(has=page.get_by_role("heading", name=f"제{number}회", exact=True))

        review = page.get_by_role("region", name="채점 문항")
        first_mark = review.get_by_role("button", name=re.compile(r"^1번 .* 다시 풀기 표시$"))
        second_mark = review.get_by_role("button", name=re.compile(r"^2번 .* 다시 풀기 표시$"))
        marked_only = page.get_by_role("button", name="다시 풀 문항만 보기")
        round_bookmark = round_card(12).get_by_role("button", name=re.compile(r"^다시 풀기 \d+문항$"))
        back = page.get_by_role("button", name="회차 목록", exact=True)

        await round_card(12).get_by_role("button", name="최근 결과").click()
        await expect(first_mark).to_have_attribute("aria-pressed", "false")
        await first_mark.press("Space")
        await second_mark.click()
        await expect(first_mark).to_have_attribute("aria-pressed", "true")
        await expect(review.get_by_role("button", name="다시 풀기", exact=True)).to_have_count(0)
        await back.click()
        await expect(round_bookmark).to_have_text("다시 풀기 2문항")
        await expect(round_card(11).get_by_role("button", name=re.compile("다시 풀기"))).to_have_count(0)

        await page.set_viewport_size({"width": 390, "height": 844})
        await page.reload()
        await round_bookmark.click()
        await expect(marked_only).to_have_attribute("aria-pressed", "true")
        await expect(review.get_by_role("button", name=re.compile("다시 풀기 표시$"))).to_have_count(2)
        assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        first_question = review.get_by_role("button", name=re.compile(r"^1\. "))
        await first_question.click()
        await review.get_by_role("button", name="다시 풀기", exact=True).click()
        correct_answer = json.loads((KEYS / "12.json").read_text())["r12-01"]["expected"]["answer_1"]
        editor = review.get_by_role("textbox", name="내 Python 코드 수정", exact=True)
        await editor.press("Control+a")
        await page.keyboard.insert_text(f"print({correct_answer})")
        await review.get_by_role("button", name="코드 실행", exact=True).click(timeout=120000)
        retry_submit = review.get_by_role("button", name="다시 제출 · 채점", exact=True)
        await retry_submit.click(timeout=120000)
        score = page.locator(".mock-score strong")
        await expect(score).to_have_text("10")
        await expect(first_question).to_contain_text("10 / 10점")
        await expect(page.locator(".mock-score")).to_contain_text("최초 제출 0점")
        await review.get_by_role("form", name="재제출 답안").get_by_role("textbox").fill(str(correct_answer + 1))
        await expect(score).to_have_text("10")
        await retry_submit.click()
        await expect(review.get_by_role("status", name="재채점 결과")).to_contain_text("오답")
        await expect(score).to_have_text("10")
        await page.reload()
        await round_bookmark.click()
        await expect(score).to_have_text("10")
        await second_mark.click()
        await expect(second_mark).to_have_count(0)
        await expect(marked_only).to_be_focused()
        await back.click()
        await expect(round_bookmark).to_have_text("다시 풀기 1문항")

        await round_card(12).get_by_role("button", name="응시 준비").click()
        await page.get_by_role("button", name="시험 시작", exact=True).click(timeout=120000)
        page.once("dialog", lambda dialog: dialog.accept())
        await page.get_by_role("button", name="최종 제출", exact=True).click()
        await expect(first_mark).to_have_attribute("aria-pressed", "true")
        result = await page.evaluate("key => JSON.parse(localStorage.getItem(key))", STORAGE)
        assert result["active"] is None
        assert result["completed"]["12"]["id"] != completed["12"]["id"]
        await back.click()
        await expect(round_bookmark).to_have_text("다시 풀기 1문항")

        await round_bookmark.click()
        await first_mark.click()
        await expect(review.get_by_text("다시 풀기 표시를 한 문항이 없습니다.")).to_be_visible()
        await back.click()
        await expect(round_bookmark).to_have_count(0)

        expired = {**completed["11"], "id": "expired-off-screen", "round": 10}
        expired.pop("submittedAt")
        await page.evaluate("""([key, attempt]) => {
            const saved = JSON.parse(localStorage.getItem(key));
            localStorage.setItem(key, JSON.stringify({ ...saved, active: attempt }));
            history.replaceState(null, '', '#home');
        }""", [STORAGE, expired])
        await page.reload()
        await page.wait_for_function("""key => {
            const saved = JSON.parse(localStorage.getItem(key));
            return !saved.active && saved.completed['10']?.id === 'expired-off-screen';
        }""", arg=STORAGE)
        await browser.close()
        print("PASS: retry scores update the round total and survive a lower result and reload; mock question marks still work.")


if __name__ == "__main__":
    asyncio.run(main())
