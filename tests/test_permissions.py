#!/usr/bin/python3

import asyncio
import sys
import os

# Add the crawler directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.base_browser import BaseBrowser

async def test_permissions():
    """Test permissions API behavior"""
    browser = BaseBrowser(headless=False, browser_type='chrome')
    await browser.launch_browser()
    
    print('Testing permissions API...')
    await browser.page.goto('https://bot.sannysoft.com', wait_until='networkidle', timeout=15000)
    await asyncio.sleep(3)
    
    # Test permissions API behavior
    permissions_data = await browser.page.evaluate('''
        async () => {
            const results = {};
            
            // Check if permissions API exists
            results.permissionsExists = !!navigator.permissions;
            
            if (navigator.permissions) {
                try {
                    // Test various permission queries
                    const permissions = ['notifications', 'geolocation', 'camera', 'microphone'];
                    
                    for (const perm of permissions) {
                        try {
                            const result = await navigator.permissions.query({name: perm});
                            results[perm] = result.state;
                        } catch (e) {
                            results[perm + '_error'] = e.message;
                        }
                    }
                    
                    // Check Notification permission specifically
                    if (window.Notification) {
                        results.notificationPermission = Notification.permission;
                    }
                    
                } catch (e) {
                    results.permissionsError = e.message;
                }
            }
            
            return results;
        }
    ''')
    
    print('Permissions API results:')
    for key, value in permissions_data.items():
        print(f'  {key}: {value}')
    
    # Also check what the detection site specifically shows
    page_content = await browser.page.evaluate('''
        () => {
            // Look for permissions-related content on the page
            const tables = document.querySelectorAll('table');
            const permissionResults = [];
            
            tables.forEach(table => {
                const rows = table.querySelectorAll('tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const testName = cells[0].textContent.trim();
                        const testResult = cells[1].textContent.trim();
                        if (testName.toLowerCase().includes('permission')) {
                            permissionResults.push({test: testName, result: testResult});
                        }
                    }
                });
            });
            
            return permissionResults;
        }
    ''')
    
    print('\nPermissions test results from detection site:')
    for result in page_content:
        print(f'  {result["test"]}: {result["result"]}')
    
    await browser.close()

if __name__ == '__main__':
    asyncio.run(test_permissions())