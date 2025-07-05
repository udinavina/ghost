#!/usr/bin/python3

import asyncio
import sys
import os

# Add the crawler directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.base_browser import BaseBrowser

async def detailed_test():
    """Test detailed stealth detection patterns"""
    browser = BaseBrowser(headless=True, browser_type='chrome')
    await browser.launch_browser()
    
    print('Testing bot.sannysoft.com detection...')
    await browser.page.goto('https://bot.sannysoft.com', wait_until='networkidle', timeout=15000)
    await asyncio.sleep(3)
    
    # Check webdriver property
    webdriver_value = await browser.page.evaluate('() => navigator.webdriver')
    webdriver_type = await browser.page.evaluate('() => typeof navigator.webdriver')
    webdriver_in_nav = await browser.page.evaluate('() => "webdriver" in navigator')
    
    print(f'Webdriver value: {webdriver_value}')
    print(f'Webdriver type: {webdriver_type}')
    print(f'Webdriver in navigator: {webdriver_in_nav}')
    
    # Check chrome object
    chrome_exists = await browser.page.evaluate('() => !!window.chrome')
    chrome_runtime = await browser.page.evaluate('() => !!(window.chrome && window.chrome.runtime)')
    
    print(f'Chrome object exists: {chrome_exists}')
    print(f'Chrome runtime exists: {chrome_runtime}')
    
    # Check plugins
    plugins_length = await browser.page.evaluate('() => navigator.plugins.length')
    mimetypes_length = await browser.page.evaluate('() => navigator.mimeTypes.length')
    
    print(f'Plugins count: {plugins_length}')
    print(f'MimeTypes count: {mimetypes_length}')
    
    # Check page content for detection messages
    body_text = await browser.page.evaluate('() => document.body.innerText.toLowerCase()')
    
    detection_keywords = ['webdriver', 'headless', 'phantom', 'automation', 'bot detected']
    detected_keywords = [kw for kw in detection_keywords if kw in body_text]
    
    print(f'Detected keywords in page: {detected_keywords}')
    
    # Check permissions API
    permissions_exists = await browser.page.evaluate('() => !!navigator.permissions')
    print(f'Permissions API exists: {permissions_exists}')
    
    await browser.close()

if __name__ == '__main__':
    asyncio.run(detailed_test())