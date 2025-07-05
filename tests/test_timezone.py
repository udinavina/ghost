#!/usr/bin/python3

import asyncio
import sys
import os

# Add the crawler directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.base_browser import BaseBrowser

async def test_timezone():
    """Test timezone detection"""
    browser = BaseBrowser(headless=False, browser_type='chrome')
    await browser.launch_browser()
    
    print('Testing timezone detection...')
    await browser.page.goto('https://bot.sannysoft.com', wait_until='networkidle', timeout=15000)
    await asyncio.sleep(3)
    
    # Check timezone information
    timezone_info = await browser.page.evaluate('''
        () => {
            const results = {};
            
            // Check Date timezone offset
            results.timezoneOffset = new Date().getTimezoneOffset();
            
            // Check Intl timezone
            try {
                results.intlTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            } catch (e) {
                results.intlTimezone = 'error: ' + e.message;
            }
            
            // Check timezone from page content
            const body = document.body.innerText.toLowerCase();
            if (body.includes('timezone')) {
                const lines = document.body.innerText.split('\\n');
                results.pageTimezoneInfo = lines.filter(line => 
                    line.toLowerCase().includes('timezone') || 
                    line.toLowerCase().includes('time zone')
                );
            }
            
            return results;
        }
    ''')
    
    print('Timezone detection results:')
    for key, value in timezone_info.items():
        print(f'  {key}: {value}')
    
    await browser.close()

if __name__ == '__main__':
    asyncio.run(test_timezone())