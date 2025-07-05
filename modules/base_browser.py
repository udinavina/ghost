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
from .enhanced_stealth import EnhancedStealth

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
    
    def __init__(self, headless=False, browser_type='chrome', use_profile=False):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless
        self.browser_type = browser_type
        self.session_logger = None
        self.use_profile = use_profile
        self.profile_path = None
        
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
                
                # Handle profile loading vs regular browser launch
                if self.use_profile:
                    self.profile_path = EnhancedStealth.get_crawler_profile_path()
                    # Create the profile if it doesn't exist
                    EnhancedStealth.create_realistic_profile(self.profile_path)
                    print(f"Using internal crawler profile: {self.profile_path}")
                    
                    # Use launch_persistent_context for profile-based browsing
                    chrome_args = EnhancedStealth.get_enhanced_chrome_args()
                    # Remove user-data-dir from args since we pass it separately
                    chrome_args = [arg for arg in chrome_args if not arg.startswith('--user-data-dir')]
                    chrome_args.extend([
                        '--window-size=1920,1080',
                        '--start-maximized',
                    ])
                    
                    user_agent = EnhancedStealth.get_random_user_agent(self.browser_type)
                    viewport = EnhancedStealth.get_realistic_viewport()
                    screen = EnhancedStealth.get_realistic_screen()
                    extra_headers = EnhancedStealth.get_enhanced_headers(self.browser_type)
                    
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        user_data_dir=self.profile_path,
                        headless=self.headless,
                        channel='chromium' if self.browser_type == 'chrome' else None,
                        args=chrome_args,
                        user_agent=user_agent,
                        viewport=viewport,
                        screen=screen,
                        device_scale_factor=1,
                        has_touch=False,
                        is_mobile=False,
                        java_script_enabled=True,
                        timezone_id='America/Los_Angeles',
                        locale='en-US',
                        geolocation=None,
                        permissions=[],
                        extra_http_headers=extra_headers
                    )
                    
                    # For persistent context, the browser is not directly accessible
                    self.browser = None
                    
                else:
                    # Regular browser launch without profile
                    chrome_args = EnhancedStealth.get_enhanced_chrome_args()
                    chrome_args.extend([
                        '--window-size=1920,1080',
                        '--start-maximized',
                    ])
                    
                    self.browser = await self.playwright.chromium.launch(
                        headless=self.headless,
                        channel='chromium' if self.browser_type == 'chrome' else None,
                        args=chrome_args
                    )
            
            # Create context with stealth configuration using EnhancedStealth
            if not self.use_profile:
                # Only create context if not using profile (profile already creates persistent context)
                user_agent = EnhancedStealth.get_random_user_agent(self.browser_type)
                viewport = EnhancedStealth.get_realistic_viewport()
                screen = EnhancedStealth.get_realistic_screen()
                
                # Get enhanced headers from EnhancedStealth
                extra_headers = EnhancedStealth.get_enhanced_headers(self.browser_type)
                
                self.context = await self.browser.new_context(
                    user_agent=user_agent,
                    viewport=viewport,
                    screen=screen,
                    device_scale_factor=1,
                    has_touch=False,
                    is_mobile=False,
                    java_script_enabled=True,
                    timezone_id='America/Los_Angeles',
                    locale='en-US',
                    geolocation=None,
                    permissions=[],
                    extra_http_headers=extra_headers
                )
            
            # Add comprehensive stealth JavaScript from EnhancedStealth at context level
            await self.context.add_init_script(EnhancedStealth.get_stealth_js())
            
            # Create new page
            self.page = await self.context.new_page()
            
            # Apply stealth measures  
            stealth_instance = Stealth()
            await stealth_instance.apply_stealth_async(self.page)
            
            # Add enhanced page-level stealth measures
            await self.page.add_init_script(EnhancedStealth.get_webgl_vendor_override())
            await self.page.add_init_script(EnhancedStealth.get_battery_api_override())
            
            # Setup additional stealth measures
            await self._setup_stealth()
            
            # Setup network logging
            await self._setup_network_logging()
            
            print("Browser launched successfully")
            
        except Exception as e:
            print(f"Error launching browser: {e}")
            raise
    
    async def _setup_stealth(self):
        """Setup additional stealth measures - comprehensive stealth is already applied"""
        # The main stealth JavaScript is already applied from EnhancedStealth
        # This method is kept for any additional page-specific stealth measures
        pass
    
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
            if self.use_profile:
                # For persistent context, close the context directly
                if self.context:
                    await self.context.close()
            else:
                # For regular browser, close context then browser
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