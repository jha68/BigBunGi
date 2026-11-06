"""Home AI and notebook highlights with real Worker/D1; Google replies are mocked.

Build with VITE_SYNC_API_URL=https://bigbungi-api.junununseo.com and serve
web/dist at 127.0.0.1:4230. Start a fresh `SYNC_TEST_PORT=4330 node
sync/test-server.mjs`, then run this script. SYNC_TEST_PORT / SYNC_TEST_WEB
override those local ports. No real password or Gemini credentials are used.
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright
from browser_sync import local_fetch, ORIGIN, API, PASSWORD, STORAGE

KEY = 'test-only-study-home-key'
NOTE = 'Q. 결측치 처리는?\nA. 중앙값으로 대체합니다.\n\n```python\ndf.fillna(0)\n```'
PHRASE = '중앙값으로 대체합니다.'
CODE = 'df.fillna(0)'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/usr/bin/chromium', headless=True)
        sent, errors = [], []
        async def context(seed=None):
            ctx = await browser.new_context(viewport={'width':1440,'height':1000})
            if seed:
                await ctx.add_init_script(f"if (!localStorage.getItem('{STORAGE}')) localStorage.setItem('{STORAGE}', {json.dumps(json.dumps(seed))});")
            async def proxy(route):
                req, url = route.request, route.request.url
                if url.startswith('https://generativelanguage.googleapis.com/'):
                    headers={'access-control-allow-origin':ORIGIN,'access-control-allow-headers':'content-type,x-goog-api-key','access-control-allow-methods':'GET,POST,OPTIONS'}
                    if req.method=='OPTIONS': await route.fulfill(status=204,headers=headers); return
                    assert req.headers.get('x-goog-api-key')==KEY
                    if req.method=='GET':
                        body={'models':[{'name':'models/gemini-2.5-flash-lite','displayName':'Flash Lite','supportedGenerationMethods':['generateContent']}]}
                        await route.fulfill(status=200,content_type='application/json',body=json.dumps(body),headers=headers);return
                    payload=req.post_data_json;sent.append(payload)
                    is_study='전체 학습 기록을 정리' in payload['systemInstruction']['parts'][0]['text']
                    if is_study:
                        text='HOME_ONLY: [결측치 문제](#t1-01)를 복습하세요. '+PHRASE
                    else: text='PROBLEM_ONLY: 결측치를 중앙값으로 대체하세요.'
                    body={'candidates':[{'content':{'parts':[{'text':text}]},'finishReason':'STOP'}]}
                    await route.fulfill(status=200,content_type='text/event-stream',body='data: '+json.dumps(body)+'\n\n',headers=headers);return
                if '/pyodide/' in url: await route.abort();return
                if url.startswith(API): target='http://127.0.0.1:'+os.environ.get('SYNC_TEST_PORT','4330')+url[len(API):]
                elif url.startswith(ORIGIN):target=os.environ.get('SYNC_TEST_WEB','http://127.0.0.1:4230')+url[len(ORIGIN):]
                else: await route.abort();return
                status,headers,body=await asyncio.to_thread(local_fetch,target,req.method,req.post_data_buffer,
                    {k:v for k,v in (await req.all_headers()).items() if k.lower() not in ('host','content-length','accept-encoding')})
                await route.fulfill(status=status,headers=headers,body=body)
            await ctx.route('**/*',proxy)
            return ctx
        async def login(page):
            page.on('pageerror',lambda error:errors.append(str(error)))
            await page.goto(ORIGIN)
            await page.get_by_label('비밀번호',exact=True).fill(PASSWORD)
            await page.get_by_role('button',name='로그인',exact=True).click()
        async def saved(page):await page.locator('.sync-status.saved').wait_for(timeout=15000)
        async def highlights_saved(page,count):
            for _ in range(100):
                remote=await api(page,'/state')
                items=remote['state'].get('highlights',{}).get('t1-01')
                if items is not None and len(items)==count:return
                await page.wait_for_timeout(100)
            raise AssertionError('Highlight was not synchronized')
        async def home(page):
            await page.locator('.brand').click();await page.locator('.home-intro').wait_for();await saved(page)
        async def home_ai(page):
            await page.locator('.home-ai-card').click();await page.locator('.home-ai-panel').wait_for()
            await page.locator('.gemini-status.ready').wait_for()
        async def ask(page,text):
            count=await page.locator('.gemini-turn').count()
            field=page.get_by_label('Gemini에게 질문',exact=True)
            await field.fill(text);await field.press('Enter')
            await page.wait_for_function('n => document.querySelectorAll(".gemini-turn").length===n+1 && !document.querySelector(".gemini-stop")',arg=count)
            await page.locator('.gemini-history-status.saved').wait_for(timeout=15000)
        async def api(page,path):
            return await page.evaluate("async url => (await (await fetch(url,{credentials:'include'})).json())",API+path)
        async def mark(page,phrase):
            await page.get_by_role('region',name='저장된 풀이 노트',exact=True).evaluate("""(root, phrase) => {
              const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),nodes=[];
              while(walker.nextNode()) nodes.push(walker.currentNode);
              const at=nodes.map(n=>n.data).join('').indexOf(phrase);
              if(at<0)throw new Error('highlight phrase not found');
              const range=document.createRange();let offset=0,started=false;
              for(const node of nodes){
                if(!started && at<offset+node.length){range.setStart(node,at-offset);started=true;}
                if(started && at+phrase.length<=offset+node.length){range.setEnd(node,at+phrase.length-offset);break;}
                offset+=node.length;
              }
              const selection=getSelection();selection.removeAllRanges();selection.addRange(range);document.dispatchEvent(new Event('selectionchange'));
            }""",phrase)
            await page.get_by_role('button',name='형광펜',exact=True).click()
        def last_context():
            return json.loads(sent[-1]['contents'][-1]['parts'][0]['text'].split('\n',1)[1])
        seed={'selected':'t1-01','drafts':{'t1-01':'print("KEEP_CODE")'},'notes':{'t1-01':NOTE,'t1-02':'다른 문제의 비강조 노트'},'answers':{},'progress':{}}
        a=await context(seed);page=await a.new_page();await login(page)
        await page.get_by_role('button',name='이 브라우저 기록 가져오기',exact=True).click();await saved(page)
        await page.get_by_role('tab',name='AI 질문',exact=True).click()
        await page.locator('#gemini-key').fill(KEY)
        await page.get_by_role('button',name='키 연결',exact=True).click()
        await page.locator('.gemini-status.ready').wait_for()
        await ask(page,'문제의 결측치 처리법은?')
        await page.get_by_role('tab',name='노트',exact=True).click()
        assert await page.get_by_role('button',name='AI 대화로 노트 생성',exact=True).is_enabled()
        await mark(page,PHRASE)
        await page.wait_for_function("CSS.highlights.get('practice-notes')?.size === 1")
        await saved(page)
        await highlights_saved(page,1)
        state=(await api(page,'/state'))['state']
        assert state['notes']['t1-01']==NOTE
        assert state['highlights']['t1-01'][0]['text']==PHRASE
        assert 'df.fillna(0)' in await page.locator('.saved-note .cm-content').inner_text()
        await mark(page,CODE)
        await highlights_saved(page,2)
        await page.wait_for_function("CSS.highlights.get('practice-notes')?.size === 2")
        await page.screenshot(path='/tmp/bigbungi-note-highlights.png',full_page=True)
        print('PASS: selecting rendered note text paints a real highlight, saves separately, and preserves Markdown/code.',flush=True)
        await home(page)
        assert await page.locator('.home-types > button').count()==3
        assert '강조한 내용 2' in ' '.join((await page.locator('.home-records').inner_text()).split())
        await page.screenshot(path='/tmp/bigbungi-study-home-desktop.png',full_page=True)
        await page.locator('.home-types > button').nth(1).click()
        await page.wait_for_function("document.querySelector('.problem-kicker')?.textContent.includes('2유형')")
        await page.get_by_role('tab',name='노트',exact=True).click()
        assert await page.get_by_role('button',name='AI 대화로 노트 생성',exact=True).is_disabled()
        await home(page);await home_ai(page)
        assert await page.locator('.gemini-turn').count()==0
        await ask(page,'내가 어려워했던 문제 중 AI 질문 사용 기록이 있는 문제만 찾아줘')
        data=last_context();first=next(p for p in data['problems'] if p['id']=='t1-01');second=next(p for p in data['problems'] if p['id']=='t1-02')
        assert first['aiQuestionCount']==1 and second['aiQuestionCount']==0
        assert first['note']==NOTE and first['highlightedNotes']==[PHRASE,CODE]
        assert 'PROBLEM_ONLY' not in await page.locator('.gemini-messages').inner_text()
        assert 'HOME_ONLY' in await page.locator('.gemini-messages').inner_text()
        assert len((await api(page,'/conversations/home'))['turns'])==1
        assert len((await api(page,'/conversations/t1-01'))['turns'])==1
        await page.locator('.gemini-answer a[href="#t1-01"]').click()
        await page.locator('.problem-heading').wait_for()
        assert 'KEEP_CODE' in await page.get_by_role('textbox',name='Python 코드 편집기',exact=True).inner_text()
        await page.get_by_role('tab',name='AI 질문',exact=True).click()
        assert 'HOME_ONLY' not in await page.locator('.gemini-messages').inner_text()
        assert 'PROBLEM_ONLY' in await page.locator('.gemini-messages').inner_text()
        await page.get_by_role('tab',name='노트',exact=True).click()
        await page.wait_for_function("CSS.highlights.get('practice-notes')?.size === 2")
        print('PASS: logo opens home, all type choices work, home AI retrieves saved usage/notes and links to problems while chats remain separate.',flush=True)
        await home(page);await home_ai(page)
        await ask(page,'노트에 기록했던 내용들을 종합하고 요약해줘')
        assert '다른 문제의 비강조 노트' in json.dumps(last_context(),ensure_ascii=False)
        await ask(page,'highlighted 된 노트 내용만 추려줘')
        data=last_context()
        assert data['highlightOnly'] is True
        assert all('note' not in p and 'recentQuestions' not in p for p in data['problems'])
        assert next(p for p in data['problems'] if p['id']=='t1-01')['highlightedNotes']==[PHRASE,CODE]
        assert '다른 문제의 비강조 노트' not in json.dumps(sent[-1],ensure_ascii=False)
        assert len(sent[-1]['contents'])==1
        assert KEY not in await page.evaluate('JSON.stringify({...localStorage})+JSON.stringify({...sessionStorage})')
        await page.reload();await saved(page);await home_ai(page)
        assert await page.locator('.gemini-turn').count()==3
        b=await context();other=await b.new_page();await login(other);await saved(other)
        await home_ai(other)
        assert await other.locator('.gemini-turn').count()==3
        other.once('dialog',lambda dialog:dialog.accept())
        await other.get_by_role('button',name='홈 AI 대화 지우기',exact=True).click()
        await other.wait_for_function('document.querySelectorAll(".gemini-turn").length===0')
        await other.locator('.gemini-history-status.saved').wait_for()
        assert len((await api(other,'/conversations/t1-01'))['turns'])==1
        await other.locator('.home-chat-heading button').click()
        await other.locator('.home-types > button').first.click()
        await other.get_by_role('tab',name='노트',exact=True).click()
        await other.wait_for_function("CSS.highlights.get('practice-notes')?.size === 2")
        await other.locator('.note-highlights-list summary').click()
        await other.get_by_role('button',name='강조 지우기',exact=True).first.click()
        await other.get_by_role('button',name='강조 지우기',exact=True).click();await saved(other)
        await highlights_saved(other,0)
        assert (await api(other,'/state'))['state']['highlights']['t1-01']==[]
        print('PASS: full-note and highlights-only retrieval, refresh/cross-device restore, independent home-chat deletion and highlight removal.',flush=True)
        await home(other);await home_ai(other)
        await other.set_viewport_size({'width':390,'height':844})
        await other.wait_for_function("getComputedStyle(document.querySelector('.main-shell')).marginLeft==='0px'")
        assert await other.evaluate('document.documentElement.scrollWidth<=innerWidth')
        await other.get_by_role('button',name='Gemini 연결 설정',exact=True).click()
        composer=await other.locator('.gemini-composer').bounding_box();panel=await other.locator('.home-ai-panel').bounding_box()
        assert composer['y']+composer['height']<=panel['y']+panel['height']+2,(composer,panel)
        await other.screenshot(path='/tmp/bigbungi-study-home-mobile.png',full_page=True)
        assert not errors,errors
        print('PASS: home AI remains usable on mobile; no browser errors.',flush=True)
        await browser.close()

asyncio.run(main())
