#!/usr/bin/python3

"""
Base Browser Module using Playwright
Navina Inc (c) 2025. All rights reserved.
"""

import asyncio
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError, Error
from playwright_stealth import Stealth

class SessionLogger:
    """Enhanced session logger for debugging browser interactions"""
    
    def __init__(self, log_file):
        self.log_file = log_file
        self.start_time = datetime.now()
        self.network_requests = []
        self.network_responses = []
        self.logger = logging.getLogger(__name__)
        
        # Setup file logging
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)
        self.logger.info(f"Session logging started - Log file: {log_file}")
        
    def log_event(self, event_type, message, data=None):
        """Log an event with timestamp and optional data"""
        timestamp = datetime.now()
        elapsed = (timestamp - self.start_time).total_seconds()
        
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'elapsed_seconds': elapsed,
            'event_type': event_type,
            'message': message
        }
        
        if data:
            log_entry['data'] = data
            
        self.logger.debug(f"[{event_type}] {message}" + (f" - Data: {json.dumps(data)[:200]}" if data else ""))

class BaseBrowser:
    """Base browser class using Playwright with stealth capabilities"""
    
    def __init__(self, headless=False, browser_type='chrome'):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless
        self.browser_type = browser_type
        self.session_logger = None
        
    async def launch_browser(self):
        """Launch browser with stealth configuration"""
        try:
            print(f"Launching Playwright {self.browser_type} browser...")
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser based on type
            if self.browser_type == 'firefox':
                print("Launching Firefox browser...")
                self.browser = await self.playwright.firefox.launch(
                    headless=self.headless
                )
            else:
                print("Launching Chrome/Chromium browser...")
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    channel='chromium' if self.browser_type == 'chrome' else None,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-dev-shm-usage',
                        '--window-size=1920,1080',
                        '--start-maximized',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--flag-switches-begin',
                        '--flag-switches-end',
                        '--disable-site-isolation-trials',
                        '--exclude-switches=enable-automation',
                        '--disable-extensions-file-access-check',
                        '--disable-extensions-http-throttling',
                        '--disable-component-extensions-with-background-pages',
                        '--disable-default-apps',
                        '--disable-sync',
                        '--no-service-autorun',
                        '--password-store=basic',
                        '--use-mock-keychain',
                        '--no-sandbox',
                        '--disable-gpu-sandbox',
                        '--disable-software-rasterizer',
                        '--disable-background-networking',
                        '--disable-client-side-phishing-detection',
                        '--disable-component-update',
                        '--disable-domain-reliability',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
            
            # Create context with stealth configuration
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            if self.browser_type == 'firefox':
                user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'
            
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080},
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
                java_script_enabled=True,
                timezone_id='America/Los_Angeles',
                locale='en-US',
                geolocation=None,
                permissions=[],
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Sec-Ch-Ua': '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            # Add aggressive webdriver removal at context level
            await self.context.add_init_script("""
                // Advanced webdriver removal - run before anything else
                (() => {
                    'use strict';
                    
                    // Delete webdriver property immediately
                    delete navigator.webdriver;
                    delete Object.getPrototypeOf(navigator).webdriver;
                    
                    // Override property descriptors to hide webdriver completely
                    const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
                    Object.getOwnPropertyDescriptor = function(obj, prop) {
                        if (prop === 'webdriver') {
                            return undefined;
                        }
                        return originalGetOwnPropertyDescriptor.apply(this, arguments);
                    };
                    
                    const originalGetOwnPropertyNames = Object.getOwnPropertyNames;
                    Object.getOwnPropertyNames = function(obj) {
                        const names = originalGetOwnPropertyNames.apply(this, arguments);
                        return names.filter(name => name !== 'webdriver');
                    };
                    
                    const originalKeys = Object.keys;
                    Object.keys = function(obj) {
                        const keys = originalKeys.apply(this, arguments);
                        return keys.filter(key => key !== 'webdriver');
                    };
                    
                    // Override hasOwnProperty to hide webdriver
                    const originalHasOwnProperty = Object.prototype.hasOwnProperty;
                    Object.prototype.hasOwnProperty = function(prop) {
                        if (prop === 'webdriver') {
                            return false;
                        }
                        return originalHasOwnProperty.apply(this, arguments);
                    };
                    
                    // Make webdriver always undefined with a non-configurable property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        set: () => {},
                        enumerable: false,
                        configurable: false
                    });
                })();
            """)
            
            # Create new page
            self.page = await self.context.new_page()
            
            # Apply stealth measures  
            stealth_instance = Stealth()
            await stealth_instance.apply_stealth_async(self.page)
            
            # Add page-level webdriver removal and additional stealth
            await self.page.add_init_script("""
                (() => {
                    'use strict';
                    
                    // Final webdriver cleanup
                    delete navigator.webdriver;
                    delete Object.getPrototypeOf(navigator).webdriver;
                    
                    // Ensure webdriver property is completely hidden
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        set: () => {},
                        enumerable: false,
                        configurable: false
                    });
                    
                    // Remove automation-related properties
                    const automationProps = [
                        '__webdriver_evaluate', '__selenium_evaluate', '__webdriver_script_function',
                        '__webdriver_script_func', '__webdriver_script_fn', '__fxdriver_evaluate',
                        '__driver_unwrapped', '__webdriver_unwrapped', '__driver_evaluate',
                        '__selenium_unwrapped', '__fxdriver_unwrapped', '_phantom', 'phantom',
                        'callPhantom', '_Selenium_IDE_Recorder', '__nightmare',
                        '__playwright__', '__pw_manual', '__playwright_target__'
                    ];
                    
                    automationProps.forEach(prop => {
                        try {
                            delete window[prop];
                            delete document[prop];
                            delete navigator[prop];
                        } catch (e) {}
                    });
                    
                    // Remove CDP runtime detection
                    try {
                        delete window.chrome?._CDP;
                        delete window.document?.$cdc_asdjflasutopfhvcZLmcfl_;
                        delete window.$chrome_asyncScriptInfo;
                    } catch (e) {}
                })();
            """)            
            
            # Setup additional stealth measures
            await self._setup_stealth()
            
            # Setup network logging
            await self._setup_network_logging()
            
            print("Browser launched successfully")
            
        except Exception as e:
            print(f"Error launching browser: {e}")
            raise
    
    async def _setup_stealth(self):
        """Setup stealth measures to avoid detection"""
        
        # Enhanced stealth measures for Playwright
        stealth_js = """
            // Enhanced stealth measures for Playwright
            
            // Remove webdriver indicators more thoroughly
            delete navigator.webdriver;
            delete Object.getPrototypeOf(navigator).webdriver;
            
            // Override the getter to always return undefined
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                set: () => {},
                enumerable: false,
                configurable: false
            });
            
            // Remove all automation properties
            const propsToDelete = [
                '__webdriver_evaluate', '__selenium_evaluate', '__webdriver_script_function',
                '__webdriver_script_func', '__webdriver_script_fn', '__fxdriver_evaluate', 
                '__driver_unwrapped', '__webdriver_unwrapped', '__driver_evaluate', 
                '__selenium_unwrapped', '__fxdriver_unwrapped', '_phantom', 'phantom',
                'callPhantom', '_Selenium_IDE_Recorder', '__nightmare', '__puppeteer_evaluation_script__',
                '__playwright__', '__pw_manual', '__playwright_target__', '__playwrightTestConfig__'
            ];
            
            propsToDelete.forEach(prop => {
                delete window[prop];
                delete document[prop];
                delete navigator[prop];
            });
            
            // Remove Playwright detection patterns
            delete window.__playwright;
            delete window.__pw_manual;
            delete window.__playwright_target__;
            delete window.Buffer;
            delete window.process;
            
            // Override permissions API to avoid detection
            const originalQuery = navigator.permissions?.query;
            if (originalQuery) {
                navigator.permissions.query = function(parameters) {
                    return parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission || 'denied' }) :
                        originalQuery.apply(this, arguments);
                };
            }
            
            // Override navigator properties to look more human
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true,
                enumerable: true
            });
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
                configurable: true,
                enumerable: true
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
                configurable: true,
                enumerable: true
            });
            
            // Create realistic plugins array
            const mockPlugins = {
                0: {
                    name: 'PDF Viewer',
                    filename: 'internal-pdf-viewer',
                    description: 'Portable Document Format',
                    version: '1.0.0.0'
                },
                1: {
                    name: 'Chrome PDF Viewer',
                    filename: 'internal-pdf-viewer',
                    description: 'Portable Document Format',
                    version: '1.0.0.0'
                },
                2: {
                    name: 'Chromium PDF Viewer',
                    filename: 'internal-pdf-viewer', 
                    description: 'Portable Document Format',
                    version: '1.0.0.0'
                },
                3: {
                    name: 'Microsoft Edge PDF Viewer',
                    filename: 'internal-pdf-viewer',
                    description: 'Portable Document Format',
                    version: '1.0.0.0'
                },
                4: {
                    name: 'WebKit built-in PDF',
                    filename: 'internal-pdf-viewer',
                    description: 'Portable Document Format',
                    version: '1.0.0.0'
                },
                length: 5,
                item: function(index) { return this[index] || null; },
                namedItem: function(name) {
                    for (let i = 0; i < this.length; i++) {
                        if (this[i] && this[i].name === name) return this[i];
                    }
                    return null;
                },
                refresh: function() { return undefined; }
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => mockPlugins,
                configurable: true,
                enumerable: true
            });
            
            // Create realistic mimeTypes
            const mockMimeTypes = {
                0: {
                    type: 'application/pdf',
                    suffixes: 'pdf',
                    description: 'Portable Document Format',
                    enabledPlugin: mockPlugins[0]
                },
                length: 1,
                item: function(index) { return this[index] || null; },
                namedItem: function(name) {
                    for (let i = 0; i < this.length; i++) {
                        if (this[i] && this[i].type === name) return this[i];
                    }
                    return null;
                }
            };
            
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => mockMimeTypes,
                configurable: true,
                enumerable: true
            });
        """
        
        # Add Firefox-specific stealth measures
        if self.browser_type == 'firefox':
            firefox_stealth_js = """
                // Firefox-specific stealth measures
                
                // Remove Firefox automation indicators
                const firefoxProps = [
                    '_firefox', '__firefox__', 'domAutomation',
                    'domAutomationController', '__fxdriver_evaluate',
                    '__fxdriver_unwrapped', '_Selenium_IDE_Recorder'
                ];
                
                firefoxProps.forEach(prop => {
                    delete window[prop];
                    delete document[prop];
                    delete navigator[prop];
                });
                
                // Remove Chrome object for Firefox
                delete window.chrome;
                Object.defineProperty(window, 'chrome', {
                    get: () => undefined,
                    set: () => {},
                    enumerable: false,
                    configurable: false
                });
                
                // Override Firefox-specific properties
                Object.defineProperty(navigator, 'oscpu', {
                    get: () => 'Windows NT 10.0; Win64; x64'
                });
                
                Object.defineProperty(navigator, 'productSub', {
                    get: () => '20100101'
                });
                
                Object.defineProperty(navigator, 'vendor', {
                    get: () => ''
                });
                
                Object.defineProperty(navigator, 'vendorSub', {
                    get: () => ''
                });
            """
            stealth_js += firefox_stealth_js
        
        await self.page.add_init_script(stealth_js)
    
    async def _setup_network_logging(self):
        """Setup network request/response logging"""
        if self.session_logger:
            def handle_request(request):
                self.session_logger.network_requests.append(request.url)
            
            def handle_response(response):
                self.session_logger.network_responses.append(response.url)
            
            self.page.on('request', handle_request)
            self.page.on('response', handle_response)
    
    async def navigate_to_url(self, url):
        """Navigate to URL with error handling"""
        try:
            print(f"Navigating to: {url}")
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            print("Page loaded successfully")
        except TimeoutError:
            print("Timeout waiting for page to load, trying with domcontentloaded...")
            await self.page.goto(url, wait_until='domcontentloaded', timeout=15000)
            print("Page loaded with domcontentloaded")
        except Exception as e:
            print(f"Navigation error: {e}")
            print("Trying simple load...")
            await self.page.goto(url, timeout=15000)
            print("Page loaded with simple navigation")
        
        # Wait for dynamic content
        await asyncio.sleep(3)
    
    async def test_stealth_detection(self):
        """Test stealth capabilities against detection sites"""
        print("\n*** STEALTH DETECTION TESTS ***")
        
        detection_sites = [
            "https://bot.sannysoft.com",
            "https://pixelscan.net/",
            "https://arh.antoinevastel.com/bots/areyouheadless",
            "https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html"
        ]
        
        for site in detection_sites:
            try:
                print(f"\nTesting stealth against: {site}")
                await self.page.goto(site, wait_until='networkidle', timeout=15000)
                
                # Wait for detection scripts to run
                await asyncio.sleep(3)
                
                # Check for detection indicators
                detection_result = await self.page.evaluate("""
                    () => {
                        const indicators = {
                            webdriverDetected: navigator.webdriver === true,
                            phantomDetected: !!window._phantom || !!window.callPhantom,
                            playwrightDetected: !!window.__playwright || !!window.__pw_manual,
                            automationDetected: !!window.chrome && !!window.chrome.runtime && !!window.chrome.runtime.onConnect,
                            headlessDetected: /headless/i.test(navigator.userAgent),
                            chromeDetected: !!window.chrome,
                            pluginsCount: navigator.plugins.length,
                            languagesCount: navigator.languages.length
                        };
                        
                        // Look for specific detection messages in page content
                        const bodyText = document.body.textContent.toLowerCase();
                        const detectionMessages = [
                            'headless', 'automation', 'webdriver', 'phantom', 'playwright',
                            'bot detected', 'you are a bot', 'automated'
                        ];
                        
                        const foundMessages = detectionMessages.filter(msg => bodyText.includes(msg));
                        
                        return {
                            ...indicators,
                            detectionMessages: foundMessages,
                            bodySnippet: document.body.textContent.substring(0, 500)
                        };
                    }
                """)
                
                # Analyze results
                detected = (
                    detection_result['webdriverDetected'] or
                    detection_result['phantomDetected'] or
                    detection_result['playwrightDetected'] or
                    detection_result['headlessDetected'] or
                    len(detection_result['detectionMessages']) > 0
                )
                
                if detected:
                    print(f"   DETECTION POSSIBLE:")
                    if detection_result['webdriverDetected']:
                        print("    - WebDriver property detected")
                    if detection_result['phantomDetected']:
                        print("    - Phantom properties detected")
                    if detection_result['playwrightDetected']:
                        print("    - Playwright properties detected")
                    if detection_result['headlessDetected']:
                        print("    - Headless user agent detected")
                    if detection_result['detectionMessages']:
                        print(f"    - Detection messages: {detection_result['detectionMessages']}")
                else:
                    print(f"   STEALTH SUCCESSFUL")
                    print(f"    - Plugins: {detection_result['pluginsCount']}")
                    print(f"    - Languages: {detection_result['languagesCount']}")
                    print(f"    - Chrome object: {detection_result['chromeDetected']}")
                    
            except Exception as e:
                print(f"   Error testing {site}: {e}")
            
            # Wait between tests
            await asyncio.sleep(2)
    
    async def close(self):
        """Close the browser safely"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                print("Browser closed")
        except Exception as e:
            print(f"Browser close error (non-critical): {e}")
            try:
                # Force kill browser processes if normal close fails
                import subprocess
                if self.browser_type == 'firefox':
                    subprocess.run(['pkill', '-f', 'firefox'], capture_output=True)
                else:
                    subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
            except:
                pass
