"""Run real browser/WASM exercises with all cross-origin HTTP requests blocked."""
import asyncio
import json
import os
from pathlib import Path
import urllib.request
import hashlib
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parent.parent
CACHE=ROOT/'.runtime'/'cdn-cache'
CACHE.mkdir(parents=True,exist_ok=True)


def verified_download(url):
    digest=hashlib.sha256(url.encode()).hexdigest()
    path=CACHE/digest;meta=CACHE/(digest+'.json')
    if path.exists() and meta.exists():return path.read_bytes(),json.loads(meta.read_text())['type']
    with urllib.request.urlopen(url,timeout=90) as response:
        body=response.read();kind=response.headers.get('Content-Type','application/octet-stream')
    path.write_bytes(body);meta.write_text(json.dumps({'type':kind}))
    return body,kind


async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,
            proxy={'server':os.environ['HTTPS_PROXY'],'bypass':'localhost,127.0.0.1'} if os.environ.get('HTTPS_PROXY') else None)
        context=await browser.new_context(viewport={'width':1512,'height':1080},service_workers='block')
        base=os.environ.get('APP_URL','http://127.0.0.1:5173')
        origin=urlsplit(base).netloc
        foreign_requests=[]
        async def same_origin_only(route):
            url=urlsplit(route.request.url)
            if url.scheme in ('http','https') and url.netloc!=origin:
                foreign_requests.append(route.request.url)
                await route.abort()
            else:
                await route.continue_()
        await context.route('**/*',same_origin_only)
        page=await context.new_page()
        page_errors=[]
        page.on('pageerror',lambda e:page_errors.append(str(e)))
        await page.goto(base,wait_until='networkidle')
        await page.wait_for_function("!document.querySelector('[data-testid=run-code]').disabled",timeout=120000)
        print('REAL RUNTIME READY:',await page.get_by_test_id('runtime-status').inner_text(),flush=True)
        await page.screenshot(path='/tmp/bigbungi-desktop.png',full_page=True)
        async def check_mobile():
            await page.set_viewport_size({'width':390,'height':844})
            await page.wait_for_function("getComputedStyle(document.querySelector('.main-shell')).marginLeft === '0px'")
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile overflow'
            await page.get_by_role('button',name='문제 목록 열기').click()
            await page.wait_for_function("document.querySelector('.sidebar').getBoundingClientRect().x >= -0.1")
            await page.get_by_role('button',name='문제 목록 닫기',exact=True).click()
            await page.wait_for_function("!document.querySelector('.sidebar').classList.contains('open')")
            await page.screenshot(path='/tmp/bigbungi-mobile.png',full_page=True)
            print('Mobile overflow, drawer opening/closing and layout passed.',flush=True)
        if os.environ.get('BROWSER_MODE')=='mobile':
            await check_mobile();assert not page_errors,page_errors;assert not foreign_requests,foreign_requests;await browser.close();return
        assert await page.get_by_role('tab',name='데이터').count()==0
        assert await page.get_by_role('button',name='막혔다면 힌트 보기').count()==0
        assert await page.locator('.problem-datasets .table-scroll tbody tr').count()==8
        await page.get_by_role('tab',name='노트',exact=True).click()
        await page.get_by_label('풀이 노트').fill('E2E: ddof 조건 확인')
        await page.reload(wait_until='networkidle')
        await page.get_by_role('tab',name='노트',exact=True).click()
        assert 'E2E: ddof 조건 확인' in await page.get_by_role('region',name='저장된 풀이 노트',exact=True).inner_text()
        await page.get_by_role('button',name='노트 편집',exact=True).click()
        assert await page.get_by_label('풀이 노트').input_value()=='E2E: ddof 조건 확인'
        await page.get_by_role('tab',name='문제',exact=True).click()
        assert await page.locator('.problem-datasets .table-scroll tbody tr').count()==8

        async def put_code(source):
            editor=page.get_by_role('textbox',name='Python 코드 편집기')
            await editor.click();await page.keyboard.press('Control+a');await page.keyboard.insert_text(source)

        async def execute(source):
            await put_code(source)
            await page.wait_for_function("!!document.querySelector('[data-testid=run-code]') && !document.querySelector('[data-testid=run-code]').disabled",timeout=120000)
            await page.get_by_test_id('run-code').click()
            await page.wait_for_selector('.execution-badge',timeout=120000)
            await page.wait_for_function("!!document.querySelector('[data-testid=run-code]') && !document.querySelector('[data-testid=run-code]').disabled",timeout=150000)

        await execute('print("hello real Python")\nraise ValueError("실제 오류 확인")')
        assert 'ValueError: 실제 오류 확인' in await page.get_by_test_id('python-error').inner_text()
        print('Real stdout and Python exception verified.',flush=True)
        await execute('import pandas as pd\npd.read_csv("data/customers.csv").head(3)')
        assert await page.locator('.console-output tbody tr').count()==3

        titles={p['id']:p['title'] for p in json.loads((ROOT/'web/public/content/catalog.json').read_text())}
        curriculum=[(1,1)] if os.environ.get('BROWSER_MODE')=='quick' else [(1,30),(2,10),(3,10)]
        for kind,count in curriculum:
            for number in range(1,count+1):
                pid=f't{kind}-{number:02d}'
                if kind!=int((await page.locator('.problem-kicker .badge').inner_text())[4]):
                    await page.locator('.type-button').nth(kind-1).click()
                await page.locator('.question-link').nth(number-1).click()
                await page.wait_for_function("title => document.querySelector('.problem-heading h2')?.textContent === title",arg=titles[pid])
                await page.wait_for_selector('.code-editor .cm-content')
                solution=json.loads((ROOT/'web/public/content/solutions'/f'{pid}.json').read_text())
                await execute(solution['code'])
                errors=page.get_by_test_id('python-error')
                if await errors.count(): raise AssertionError(pid+': '+await errors.inner_text())
                await page.get_by_test_id('grade-code').click()
                await page.get_by_test_id('grade-result').wait_for()
                text=await page.get_by_test_id('grade-result').inner_text()
                assert '정답입니다' in text,(pid,text)
                print('BROWSER PASS:',pid,text.splitlines()[0],flush=True)
                if kind==2:await page.screenshot(path=f'/tmp/bigbungi-{pid}.png',full_page=True)
        expected=sum(count for _,count in curriculum)
        assert f'{expected} / 50' in await page.locator('.progress-caption strong').inner_text()
        await page.screenshot(path='/tmp/bigbungi-complete.png',full_page=True)
        await execute('import matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as plt\nplt.plot([1,2,3],[1,4,9])\nplt.title("Real Python plot")\nplt.show()')
        assert await page.locator('.result-plot').count()==1
        # Interrupted code must stop the worker and recover without losing code.
        await put_code('while True:\n    pass')
        await page.get_by_test_id('run-code').click()
        await page.get_by_role('button',name='중지',exact=True).wait_for()
        await page.wait_for_function("document.querySelector('[data-testid=runtime-status]').textContent.includes('코드 실행 중')")
        await page.get_by_role('button',name='중지',exact=True).click()
        await page.wait_for_function("!!document.querySelector('[data-testid=run-code]') && !document.querySelector('[data-testid=run-code]').disabled",timeout=120000)
        assert 'while True' in await page.locator('.cm-content').inner_text()
        print('Worker stop/recovery and draft preservation verified.',flush=True)
        await check_mobile()
        assert not page_errors,page_errors
        assert not foreign_requests,foreign_requests
        await browser.close()
        print(f'{expected} browser reference executions, grading, data preview, notes, errors, worker stop and mobile layout passed with zero external HTTP requests.',flush=True)


if __name__=='__main__':asyncio.run(main())
