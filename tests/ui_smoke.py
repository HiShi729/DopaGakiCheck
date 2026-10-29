"""Test the playable offline web preview with Chromium (native Android SDK unavailable)."""
from __future__ import annotations
from pathlib import Path
import base64
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1] / 'web-demo'
html=(root / 'index.html').read_text()
engine=(root / 'game-engine.js').read_text()
html=html.replace('<script src="./game-engine.js"></script>',f'<script>{engine}</script>')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,has_touch=True,is_mobile=True)
    console_errors=[]
    page.on('pageerror',lambda e: console_errors.append(str(e)))
    page.goto('about:blank')
    page.set_content(html)
    assert page.locator('.intro h1').count()==1
    page.locator('#start').click()
    assert page.locator('#clip-video').count()==1
    first_clip=page.evaluate('session.videoOrder[0]')
    assert page.locator('#clip-video').get_attribute('src')==f'./clips/clip{first_clip+1:02d}.mp4'
    for i in range(10):
        assert page.locator('#skip').count()==1, f'Expected skip button for clip {i}'
        page.locator('#skip').click()
    assert page.locator('.quiz h2').count()==1
    assert page.evaluate('document.querySelector(".quiz").scrollHeight <= window.innerHeight + 2')
    assert page.evaluate('session.questions.filter(q=>q.isOrderQuestion).length')==2
    # When a clip is used for an order question, its identifying still is actually shown.
    took_quiz_preview = False
    for i in range(10):
        is_order = page.evaluate('session.questions[quiz].isOrderQuestion')
        if is_order:
            expected=page.evaluate('session.questions[quiz].videoId+1')
            still=page.locator('.quiz-still')
            assert still.count()==1
            assert still.get_attribute('src')==f'./stills/still{expected:02d}.jpg'
            bytes_=(root/'stills'/f'still{expected:02d}.jpg').read_bytes()
            img_url='data:image/jpeg;base64,'+base64.b64encode(bytes_).decode()
            still.evaluate('(el, url) => { el.src=url; }', img_url)
            assert still.evaluate('el => el.complete && el.naturalWidth>0')
            if not took_quiz_preview:
                page.screenshot(path='/mnt/data/DopaGakiCheck_quiz_preview.png',full_page=False)
                took_quiz_preview=True
        else:
            assert page.locator('.quiz-still').count()==0
        choice=page.evaluate('session.questions[quiz].correctIndex')
        page.locator(f'[data-answer="{choice}"]').click()
        page.locator('#next').click()
    assert page.locator('.result .score strong').inner_text()=='0'
    assert '10問完走' in page.locator('.mini').inner_text()
    assert page.locator('.review-card').count()==10
    page.screenshot(path='/mnt/data/DopaGakiCheck_result_preview.png',full_page=True)
    # Second round: quit after 3 correct answers and check penalty + unanswered review.
    page.locator('#again').click()
    page.locator('#start').click()
    for i in range(10): page.locator('#skip').click()
    for i in range(3):
        choice=page.evaluate('session.questions[quiz].correctIndex')
        page.locator(f'[data-answer="{choice}"]').click()
        page.locator('#next').click()
    page.once('dialog',lambda dialog: dialog.accept())
    page.locator('#quit-top').click()
    assert page.locator('.result .score strong').inner_text()=='80'
    assert '途中終了' in page.locator('.score-type').inner_text()
    assert page.locator('.review-card').filter(has_text='未回答').count()==7
    assert page.locator('.review-card').count()==10
    page.screenshot(path='/mnt/data/DopaGakiCheck_quit_preview.png',full_page=True)
    assert not console_errors,console_errors
    browser.close()
print('Chromium UI smoke: video order, stills, 10 answers, score=0, quit after 3 answers score=80 PASSED')
