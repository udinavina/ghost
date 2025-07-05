#!/usr/bin/python3

import asyncio
import sys
import os

# Add the crawler directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.base_browser import BaseBrowser

async def test_profile_stealth():
    """Test stealth detection with internal profile"""
    print("Testing stealth with internal Chrome profile...")
    
    browser = BaseBrowser(headless=False, browser_type='chrome', use_profile=True)
    await browser.launch_browser()
    
    print('Testing detection with profile...')
    await browser.page.goto('https://bot.sannysoft.com', wait_until='networkidle', timeout=15000)
    await asyncio.sleep(5)
    
    # Get the specific detection results
    detection_results = await browser.page.evaluate('''
        () => {
            const results = {};
            
            // Look for specific test results on the page
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                const rows = table.querySelectorAll('tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const testName = cells[0].textContent.trim();
                        const testResult = cells[1].textContent.trim();
                        if (testName && testResult) {
                            results[testName] = testResult;
                        }
                    }
                });
            });
            
            return results;
        }
    ''')
    
    print('\\nProfile-based stealth results:')
    suspicious_count = 0
    total_count = 0
    
    for test, result in detection_results.items():
        total_count += 1
        if any(keyword in result.lower() for keyword in ['true', 'present', 'failed', 'detected']):
            if not any(safe in test.lower() for safe in ['chrome', 'plugins', 'languages', 'webgl']):
                print(f'    {test}: {result}')
                suspicious_count += 1
            else:
                print(f'   {test}: {result}')
        else:
            print(f'   {test}: {result}')
    
    print(f'\\nStealth Score: {total_count - suspicious_count}/{total_count} tests passed')
    
    await asyncio.sleep(3)
    await browser.close()

if __name__ == '__main__':
    asyncio.run(test_profile_stealth())