#!/usr/bin/python3

import asyncio
import sys
import os

# Add the crawler directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.base_browser import BaseBrowser

async def analyze_detection():
    """Analyze what specific webdriver indicators are being detected"""
    browser = BaseBrowser(headless=False, browser_type='chrome')
    await browser.launch_browser()
    
    print('Analyzing detection patterns on bot.sannysoft.com...')
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
    
    print('\\nDetection results from bot.sannysoft.com:')
    for test, result in detection_results.items():
        if 'webdriver' in test.lower() or 'present' in result.lower() or 'true' in result.lower():
            print(f'    {test}: {result}')
        else:
            print(f'   {test}: {result}')
    
    await browser.close()

if __name__ == '__main__':
    asyncio.run(analyze_detection())