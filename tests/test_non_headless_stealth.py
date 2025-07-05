#!/usr/bin/python3

import asyncio
import sys
import os

# Add the crawler directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.base_browser import BaseBrowser

async def test_non_headless():
    """Test stealth detection with non-headless browser"""
    browser = BaseBrowser(headless=False, browser_type='chrome')  # Non-headless
    await browser.launch_browser()
    
    print('Testing bot.sannysoft.com detection in non-headless mode...')
    await browser.page.goto('https://bot.sannysoft.com', wait_until='networkidle', timeout=15000)
    await asyncio.sleep(5)  # Give more time for detection scripts
    
    # Check page content for detection messages
    body_text = await browser.page.evaluate('() => document.body.innerText.toLowerCase()')
    
    detection_keywords = ['webdriver', 'headless', 'phantom', 'automation', 'bot detected']
    detected_keywords = [kw for kw in detection_keywords if kw in body_text]
    
    print(f'Detected keywords in page: {detected_keywords}')
    
    # Check webdriver property hiding
    webdriver_in_nav = await browser.page.evaluate('() => "webdriver" in navigator')
    webdriver_value = await browser.page.evaluate('() => navigator.webdriver')
    
    print(f'Webdriver in navigator: {webdriver_in_nav}')
    print(f'Webdriver value: {webdriver_value}')
    
    # Wait before closing to see the browser
    await asyncio.sleep(3)
    await browser.close()

if __name__ == '__main__':
    asyncio.run(test_non_headless())