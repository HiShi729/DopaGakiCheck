"""Smoke-test silent picture-book quiz and responsive layouts with Chromium.
Run: python tests/ui_smoke.py (requires playwright and Chromium).
"""
from pathlib import Path
import base64
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1] / 'web-demo'
html = (root/'index.html').read_text(encoding='utf-8')
for name in ('stories.js','game-engine.js'):
    html = html.replace(f'<script src="./{name}"></script>',
                        '<script>' + (root/name).read_text(encoding='utf-8') + '</script>')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',
                                args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    for width,height,label in ((390,844,'phone'),(360,640,'small_phone'),
                               (800,1280,'tablet_portrait'),(1280,800,'tablet_landscape')):
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('about:blank')
        page.set_content(html)
        assert page.locator('.quiz-notice').count()==1
        page.locator('#start').click()
        assert page.evaluate('session.videoOrder.length')==10
        assert page.evaluate('new Set(session.videoOrder).size')==10
        assert page.locator('#clip-video').count()==1
        # Exercise actual H.264 decoding without a network server.
        id=page.evaluate('session.videoOrder[0]')
        content=(root/'clips'/f'clip{id+1:02d}.mp4').read_bytes()
        data='data:video/mp4;base64,'+base64.b64encode(content).decode('ascii')
        page.evaluate('src=>{const v=document.querySelector("#clip-video");v.src=src;v.load();v.play();}',data)
        page.wait_for_function('document.querySelector("#clip-video").readyState>=2',timeout=15000)
        dims=page.evaluate('''() => {const v=document.querySelector('#clip-video');
         const r=document.querySelector('#feed-inner').getBoundingClientRect();
         return {video:[v.videoWidth,v.videoHeight],box:[r.x,r.y,r.width,r.height]};}''')
        assert dims['video']==[432,768],dims
        assert dims['box'][2]<=width+1 and dims['box'][3]<=height+1,dims
        if label=='tablet_landscape':assert abs(dims['box'][2]-450)<5,dims
        for i in range(10):
            assert page.locator('#skip').count()==1
            page.locator('#skip').click()
        assert page.locator('.quiz h2').count()==1
        assert page.evaluate('session.questions.length')==10
        assert page.evaluate('session.questions.every(q=>q.isOrderQuestion===undefined)')
        for i in range(10):
            q=page.evaluate('session.questions[quiz]')
            assert page.locator('.quiz-still').count()==1, (label,i)
            src=f'./stills/still{q["videoId"]+1:02d}.jpg'
            assert page.locator('.quiz-still').get_attribute('src')==src,(label,i)
            thumb=(root/'stills'/f'still{q["videoId"]+1:02d}.jpg').read_bytes()
            data='data:image/jpeg;base64,'+base64.b64encode(thumb).decode('ascii')
            page.locator('.quiz-still').evaluate('(el,src)=>{el.src=src}',data)
            page.wait_for_function('document.querySelector(".quiz-still").naturalWidth>0')
            assert page.locator('.options-grid .option').count()==4
            geom=page.evaluate('''() => ({docWidth:document.documentElement.scrollWidth,
                 columns:getComputedStyle(document.querySelector('.options-grid')).gridTemplateColumns})''')
            assert geom['docWidth']<=width+1,(label,i,geom)
            if 'tablet' in label:
                assert len(geom['columns'].split(' '))==2,(label,geom)
            else:
                assert len(geom['columns'].split(' '))==1,(label,geom)
            if i==0 and label in ('phone','tablet_landscape'):
                page.screenshot(path=f'/mnt/data/DopaGakiCheck_v3_{label}_quiz.png',full_page=True)
            page.locator(f'[data-answer="{q["correctIndex"]}"]').click()
            page.locator('#next').click()
        assert page.locator('.result .score strong').inner_text()=='0'
        assert page.locator('.review-card').count()==10
        # Rechallenge and quit: previous penalty remains intact.
        page.locator('#again').click()
        page.locator('#start').click()
        for i in range(10):page.locator('#skip').click()
        for i in range(3):
            q=page.evaluate('session.questions[quiz]')
            page.locator(f'[data-answer="{q["correctIndex"]}"]').click()
            page.locator('#next').click()
        page.once('dialog',lambda d:d.accept())
        page.locator('#quit-top').click()
        assert page.locator('.result .score strong').inner_text()=='80'
        assert page.locator('.review-card').count()==10
        assert not errors,(label,errors)
        print(f'{label}: 20-pool, MP4 decode, 10 opening stills, layout, score, early quit PASS')
        page.close()
    browser.close()
