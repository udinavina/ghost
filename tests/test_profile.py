#!/usr/bin/python3

import asyncio
import sys
import os

# Add the crawler directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.base_browser import BaseBrowser

async def test_profile():
    """Test browser with real Chrome profile"""
    print("Testing browser with Chrome profile...")
    
    browser = BaseBrowser(headless=False, browser_type='chrome', use_profile=True)
    await browser.launch_browser()
    
    print('Testing stealth with real Chrome profile...')
    await browser.page.goto('https://bot.sannysoft.com', wait_until='networkidle', timeout=15000)
    await asyncio.sleep(5)
    
    # Check if profile data is being used
    profile_indicators = await browser.page.evaluate('''
        () => {
            const results = {};
            
            // Check if there are cookies (indicating profile usage)
            results.hasCookies = document.cookie.length > 0;
            
            // Check if localStorage has data
            results.localStorageKeys = Object.keys(localStorage).length;
            
            // Check user agent
            results.userAgent = navigator.userAgent;
            
            // Check plugins count
            results.pluginsCount = navigator.plugins.length;
            
            // Check webdriver detection
            results.webdriverExists = 'webdriver' in navigator;
            results.webdriverValue = navigator.webdriver;
            
            return results;
        }
    ''')
    
    print('Profile indicators:')
    for key, value in profile_indicators.items():
        print(f'  {key}: {value}')
    
    # Wait a bit to see the browser window
    await asyncio.sleep(3)
    await browser.close()

async def test_without_profile():
    """Test browser without profile for comparison"""
    print("\nTesting browser without profile for comparison...")
    
    browser = BaseBrowser(headless=False, browser_type='chrome', use_profile=False)
    await browser.launch_browser()
    
    print('Testing stealth without profile...')
    await browser.page.goto('https://bot.sannysoft.com', wait_until='networkidle', timeout=15000)
    await asyncio.sleep(5)
    
    # Check profile indicators
    profile_indicators = await browser.page.evaluate('''
        () => {
            const results = {};
            results.hasCookies = document.cookie.length > 0;
            results.localStorageKeys = Object.keys(localStorage).length;
            results.userAgent = navigator.userAgent;
            results.pluginsCount = navigator.plugins.length;
            results.webdriverExists = 'webdriver' in navigator;
            results.webdriverValue = navigator.webdriver;
            return results;
        }
    ''')
    
    print('Without profile:')
    for key, value in profile_indicators.items():
        print(f'  {key}: {value}')
    
    await asyncio.sleep(3)
    await browser.close()

if __name__ == '__main__':
    asyncio.run(test_profile())
    asyncio.run(test_without_profile())