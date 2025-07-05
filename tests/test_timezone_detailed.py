#!/usr/bin/python3

import asyncio
import sys
import os

# Add the crawler directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.base_browser import BaseBrowser

async def test_timezone_detailed():
    """Test detailed timezone detection patterns"""
    browser = BaseBrowser(headless=False, browser_type='chrome')
    await browser.launch_browser()
    
    print('Testing detailed timezone detection...')
    
    # Test on timezone-specific detection sites
    sites = [
        'https://bot.sannysoft.com',
        'https://arh.antoinevastel.com/bots/areyouheadless'
    ]
    
    for site in sites:
        try:
            print(f'\n--- Testing {site} ---')
            await browser.page.goto(site, wait_until='networkidle', timeout=15000)
            await asyncio.sleep(3)
            
            # Check all timezone-related properties
            timezone_data = await browser.page.evaluate('''
                () => {
                    const results = {};
                    
                    // Date timezone methods
                    const now = new Date();
                    results.getTimezoneOffset = now.getTimezoneOffset();
                    results.toString = now.toString();
                    results.toTimeString = now.toTimeString();
                    results.toLocaleString = now.toLocaleString();
                    results.toLocaleDateString = now.toLocaleDateString();
                    results.toLocaleTimeString = now.toLocaleTimeString();
                    
                    // Intl methods
                    try {
                        results.intlTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                        results.intlLocale = Intl.DateTimeFormat().resolvedOptions().locale;
                    } catch (e) {
                        results.intlError = e.message;
                    }
                    
                    // Check for timezone mentions in page content
                    const bodyText = document.body.innerText.toLowerCase();
                    const timezoneKeywords = ['timezone', 'time zone', 'utc', 'gmt', 'pst', 'est', 'cst', 'mst'];
                    results.pageTimezoneMatches = timezoneKeywords.filter(kw => bodyText.includes(kw));
                    
                    return results;
                }
            ''');
            
            print('Timezone detection results:')
            for key, value in timezone_data.items():
                print(f'  {key}: {value}')
                
        except Exception as e:
            print(f'Error testing {site}: {e}')
    
    await browser.close()

if __name__ == '__main__':
    asyncio.run(test_timezone_detailed())