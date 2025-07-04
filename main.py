#!/usr/bin/python3

"""
Main Browser Automation Script with Modular CAPTCHA Solving
Navina Inc (c) 2025. All rights reserved.
"""

import sys
import asyncio
import time
import signal
from pathlib import Path
from datetime import datetime

from modules.base_browser import BaseBrowser, SessionLogger
from modules.capsolver import CapsSolver
from modules.turnstile_solver import detect_captcha_in_frames, attempt_capsolver_turnstile_solve, attempt_automatic_turnstile_click
from modules.ecw_solver import handle_ecw_login, verify_ecw_login_success

def is_ecw_site(url):
    """Check if URL is an ECW medical site"""
    ecw_indicators = [
        'ecwcloud.com',
        'ecw.com',
        'mobiledoc',
        'webemr'
    ]
    return any(indicator in url.lower() for indicator in ecw_indicators)

async def validate_sitekey(sitekey, url):
    """Comprehensive sitekey validation using the validation module"""
    from modules.sitekey_validator import validate_sitekey as validate_sk
    return await validate_sk(sitekey, url)


# Global browser reference for cleanup
current_browser = None

def signal_handler(sig, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown"""
    print("\nReceived shutdown signal...")
    if current_browser and current_browser.browser:
        try:
            import subprocess
            # Kill browser process based on type
            if hasattr(current_browser, 'browser_type'):
                if current_browser.browser_type == 'firefox':
                    subprocess.run(['pkill', '-f', 'firefox'], capture_output=True)
                else:
                    subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
            else:
                subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
        except:
            pass
    sys.exit(0)

async def main():
    """Main function"""
    global current_browser
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def show_help():
        """Display comprehensive help information"""
        print(" Enhanced Browser Automation & CAPTCHA Solver")
        print("=" * 50)
        print("Advanced browser automation with comprehensive Turnstile detection")
        print("and multi-method solving capabilities.")
        print("\n USAGE:")
        print("  python main.py <URL> [OPTIONS]")
        print("  python main.py <COMMAND> [OPTIONS]")
        print("\n COMMANDS:")
        print("  test_stealth       Test browser stealth capabilities")
        print("  start_server       Start Ghost Turnstile Server on port 8888")
        print("  stop_server        Stop Ghost Turnstile Server (kill -9)")
        print("  help, -h, --help   Show this help message")
        print("\n  OPTIONS:")
        print("  --browser=TYPE        Browser: 'chrome' (default) or 'firefox'")
        print("  --extract-sitekey     Extract sitekey and exit (for local server testing)")
        print("  --headless            Force headless mode (no browser window)")
        print("\n URL FORMATS:")
        print("  https://example.com                    Any website")
        print("  https://demo.ecwcloud.com              ECW medical portal")
        print("  https://site-with-turnstile.com        Auto-detects CAPTCHAs")
        print("\n CONFIGURATION:")
        print("  All API keys are loaded from: .ghost/config.toml")
        print("  Example config:")
        print("    [capsolver]")
        print("    api_key = \"your_capsolver_key_here\"")
        print("\n EXAMPLES:")
        print("  python main.py https://example.com")
        print("  python main.py https://site.com --browser=firefox")
        print("  python main.py test_stealth --browser=chrome")
        print("  python main.py https://demo.ecwcloud.com")
        print("\n  FEATURES:")
        print("   Comprehensive Turnstile detection (20+ patterns)")
        print("   Multi-method solving (in-page, server, injection, API)")
        print("   Advanced stealth (Firefox & Chrome support)")
        print("   ECW medical portal automation")
        print("   Local server for clean solving environment")
        print("   Session logging in ./log directory")
        print("\n LOCAL SERVER:")
        print("  Automatically starts at http://localhost:8888")
        print("  Manual test: http://localhost:8888/solve?sitekey=0x4AAAAAAA&url=https://example.com")
        print("\n TURNSTILE SOLVING METHODS:")
        print("  1. In-page solving     - Direct interaction with existing widgets")
        print("  2. Local server        - Clean HTML environment (most reliable)")
        print("  3. HTML injection      - Route interception with custom page")
        print("  4. CapSolver API       - Third-party solving service")
        print("\n SUPPORTED BROWSERS:")
        print("   Firefox  - Full support with enhanced stealth")
        print("   Chrome   - Full support with Chromium backend")
        print("\n DETECTION CAPABILITIES:")
        print("   Standard cf-turnstile classes")
        print("   data-sitekey attributes (immutable)")
        print("   Iframe source detection (challenges.cloudflare.com)")
        print("   Hidden response fields (cf-turnstile-response)")
        print("   JavaScript API objects (window.turnstile)")
        print("   Network request patterns")
        print("   Fallback DOM analysis for obfuscated implementations")
        print("\n SUPPORT:")
        print("  Issues: Create detailed bug reports with logs")
        print("  Logs: Check ./log/ directory for session details")
        print("\nNavina Inc (c) 2025. All rights reserved.")
    
    # Check for help flag or no arguments
    if len(sys.argv) < 2 or (len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']):
        show_help()
        sys.exit(0)
    
    
    # Parse arguments properly
    url = None

    # Google Chrome is the default browser however Google (and seemlesy by design) is not stealthy.
    # In fact Google set WebDriver to reveal it is an automated browser and i had to modify it and change it
    # It recommended to use firefox as an alternative since it is more stealthy and less "chatty"
    browser_type = 'chrome'
    
    # Parse all arguments
    extract_sitekey = False
    force_headless_flag = False
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith('--browser='):
            browser_type = arg.split('=')[1].lower()
            if browser_type not in ['chrome', 'firefox']:
                print(f"Error: Invalid browser type '{browser_type}'. Use 'chrome' or 'firefox'.")
                sys.exit(1)
        elif arg in ['--extract-sitekey', '--extract-sitekeys', '--sitekey']:
            extract_sitekey = True
        elif arg in ['--headless']:
            force_headless_flag = True
        elif arg.startswith('--'):
            # Skip other flags
            pass
        elif url is None:
            url = arg
        i += 1
    
    if url is None:
        show_help()
        sys.exit(1)
    
    # Handle special commands
    if url == "test_stealth":
        print(f"*** STEALTH TESTING MODE ({browser_type.upper()}) ***")
        browser = BaseBrowser(headless=False, browser_type=browser_type)
        
        try:
            await browser.launch_browser()
            await browser.test_stealth_detection()
            await browser.close()
        except Exception as e:
            print(f"Error during stealth testing: {e}")
            await browser.close()
        return
    
    elif url == "start_server":
        print(" Starting Ghost Turnstile Server...")
        from modules.turnstile_server import start_turnstile_server
        
        server = start_turnstile_server()
        if server.running:
            print(f" Server started successfully at http://localhost:8888")
            print(" Visit http://localhost:8888 for documentation")
            print(" Test with: http://localhost:8888/test")
            print("\n To stop: python main.py stop_server")
            
            try:
                # Keep server running
                import signal as sig_module
                def server_signal_handler(sig, frame):
                    print("\n Stopping server...")
                    server.stop()
                    sys.exit(0)
                
                sig_module.signal(sig_module.SIGINT, server_signal_handler)
                sig_module.signal(sig_module.SIGTERM, server_signal_handler)
                
                print("Press Ctrl+C to stop the server...")
                while server.running:
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n Stopping server...")
                server.stop()
        else:
            print(" Failed to start server")
            return 1
        return 0
    
    elif url == "stop_server":
        print(" Stopping Ghost Turnstile Server...")
        import subprocess
        import os
        
        try:
            # Find processes using port 8888
            result = subprocess.run(['lsof', '-i', ':8888'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                pids = []
                for line in lines:
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[1]
                            try:
                                pids.append(int(pid))
                            except ValueError:
                                continue
                
                if pids:
                    print(f" Found {len(pids)} process(es) using port 8888")
                    for pid in pids:
                        try:
                            # Kill aggressively with -9
                            os.kill(pid, 9)
                            print(f" Killed process {pid}")
                        except ProcessLookupError:
                            print(f"  Process {pid} already dead")
                        except PermissionError:
                            print(f" No permission to kill process {pid}")
                    
                    print(" Server stopped")
                else:
                    print("  No server process found on port 8888")
            else:
                print("  No server process found on port 8888")
                
        except FileNotFoundError:
            print(" lsof command not found, trying alternative method...")
            # Fallback method
            try:
                subprocess.run(['pkill', '-9', '-f', 'turnstile_server'], check=False)
                subprocess.run(['fuser', '-k', '8888/tcp'], check=False)
                print(" Server stop attempted")
            except FileNotFoundError:
                print(" Could not find tools to stop server. Try manually: pkill -f turnstile_server")
        
        return 0
    
    print(f"Received URL argument: '{url}'")
    
    # Initialize CapSolver with API key from config
    capsolver = CapsSolver()  # Will load from .ghost/config.toml
    if capsolver.api_key:
        print(f"CapSolver initialized with API key: {capsolver.api_key[:10]}...")
    else:
        print("No CapSolver API key available - automatic solving disabled")
    
    # Setup logging
    log_dir = Path("log")
    log_dir.mkdir(exist_ok=True)
    log_filename = log_dir / f"browser_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # For sitekey extraction, try simple HTTP fetch first
    if extract_sitekey:
        print(f"Extracting sitekey from: {url}")
        print(" Attempting HTTP fetch method...")
        
        try:
            # Try simple HTTP request first (faster)
            import urllib.request
            import re
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            print(" Fetching page content...")
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    print(" Page fetched successfully")
                    html_content = response.read().decode('utf-8', errors='ignore')
                    print(f" Page size: {len(html_content)} characters")
                    
                    # Use YARA-based sitekey detection (preferred method)
                    print(" Searching for sitekeys using YARA detection...")
                    from modules.yara_turnstile_detector import extract_sitekeys_yara, scan_for_turnstile_yara
                    
                    # First try YARA detection
                    found_sitekeys = extract_sitekeys_yara(html_content)
                    
                    # If YARA didn't find anything, fall back to regex
                    if not found_sitekeys:
                        print("  YARA found no sitekeys, trying regex fallback...")
                        import re
                        sitekey_patterns = [
                            r'data-sitekey=["\']([^"\']+)["\']',
                            r'"sitekey":\s*["\']([^"\']+)["\']',
                            r'sitekey:\s*["\']([^"\']+)["\']',
                        ]
                        
                        for pattern in sitekey_patterns:
                            matches = re.findall(pattern, html_content, re.IGNORECASE)
                            for match in matches:
                                if match and len(match) >= 10 and match != 'YOUR_SITE_KEY':
                                    found_sitekeys.append(match)
                    else:
                        print(f"  YARA found {len(found_sitekeys)} sitekeys")
                    
                    print(f" Found {len(found_sitekeys)} potential sitekeys")
                    
                    if found_sitekeys:
                        # Remove duplicates
                        unique_sitekeys = list(set(found_sitekeys))
                        print(f" SITEKEY(S) FOUND: {', '.join(unique_sitekeys)}")
                        
                        # Validate each sitekey found via HTTP method
                        for sitekey in unique_sitekeys:
                            print(f"\n Sitekey: {sitekey}")
                            await validate_sitekey(sitekey, url)
                        
                        return 0
                    
                    # Check if page has Turnstile references using YARA detection
                    yara_result = scan_for_turnstile_yara(html_content)
                    has_turnstile = yara_result.get('has_turnstile', False)
                    
                    if has_turnstile:
                        print(f" YARA Turnstile detection: {yara_result['total_matches']} patterns matched")
                        print(f" Confidence: {yara_result['confidence_score']}%")
                    else:
                        # Fallback to simple string search if YARA finds nothing
                        has_turnstile = 'turnstile' in html_content.lower() or 'cf-turnstile' in html_content
                        print(f" Fallback Turnstile references found: {has_turnstile}")
                    
                    if has_turnstile:
                        print("\n  Turnstile detected but no sitekey found in static HTML")
                        print("   Trying browser-based extraction...")
                    else:
                        print("\n ERROR: NO TURNSTILE DETECTED")
                        print("   No Turnstile references found in page")
                        return 1
                else:
                    print(f" HTTP Error: {response.status}")
                    print("   Falling back to browser-based extraction...")
                        
        except Exception as e:
            print(f"  HTTP fetch failed: {e}")
            print("   Falling back to browser-based extraction...")
    
    # Detect if we're running in a headless environment (no display available)
    def detect_headless_environment():
        """Detect if we're running without a display"""
        import os
        
        # Check for common headless indicators
        if os.environ.get('DISPLAY') is None and os.environ.get('WAYLAND_DISPLAY') is None:
            # No X11 or Wayland display
            return True
        
        # Check if we're in a container or CI environment
        if any(os.environ.get(var) for var in ['CI', 'GITHUB_ACTIONS', 'JENKINS_URL', 'BUILDKITE']):
            return True
        
        # Check if we're in Docker
        if os.path.exists('/.dockerenv'):
            return True
        
        # Check if we're in a server environment (no GUI packages)
        try:
            import tkinter
            # If tkinter import fails, likely no GUI
        except ImportError:
            return True
        
        # Try to detect if display is actually available
        try:
            if os.environ.get('DISPLAY'):
                import subprocess
                result = subprocess.run(['xdpyinfo'], capture_output=True, timeout=2)
                if result.returncode != 0:
                    return True  # Display not accessible
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True
        
        return False
    
    # Determine headless mode
    auto_headless = detect_headless_environment()
    headless_mode = extract_sitekey or force_headless_flag or auto_headless
    
    if auto_headless and not extract_sitekey and not force_headless_flag:
        print("  No display detected - automatically running in headless mode")
    elif force_headless_flag:
        print("  Headless mode forced via --headless flag")
    
    # Initialize browser
    browser = BaseBrowser(headless=headless_mode, browser_type=browser_type)
    current_browser = browser  # Set global reference for cleanup
    browser.session_logger = SessionLogger(log_filename)
    
    try:
        if extract_sitekey:
            print(" Using browser-based extraction...")
            print(" Starting headless browser for faster extraction...")
        else:
            print(f"Starting {browser_type} browser for: {url}")
        
        await browser.launch_browser()
        
        # Navigate to URL
        print(" Navigating to page...")
        await browser.navigate_to_url(url)
        
        if extract_sitekey:
            print(" Waiting for page to load...")
        
        # Determine handling strategy
        if is_ecw_site(url):
            # ECW-specific handling
            await handle_ecw_login(browser.page, capsolver, url)
            
            # Verify login success
            login_success = await verify_ecw_login_success(browser.page)
            if login_success:
                print(" ECW login process completed successfully")
            else:
                print(" ECW login verification failed")
                
        else:
            # Generic site handling
            if extract_sitekey:
                print("\n*** SITEKEY EXTRACTION MODE ***")
            else:
                print("\n*** GENERIC SITE HANDLING ***")
            
            # Scan for CAPTCHAs
            captcha_info = await detect_captcha_in_frames(browser.page)
            
            if captcha_info['found']:
                print(f"CAPTCHA DETECTED: {captcha_info['type'].upper()}")
                print(f"Details: {captcha_info['details']}")
                
                # Handle sitekey extraction mode
                if extract_sitekey:
                    # Extract sitekeys from the detection details immediately
                    sitekeys_found = []
                    for detail in captcha_info['details']:
                        if 'sitekey:' in detail:
                            # Extract sitekey from "Turnstile with sitekey: 3x00000000000000000000FF"
                            import re
                            match = re.search(r'sitekey:\s*([^\s,]+)', detail)
                            if match:
                                sitekey = match.group(1)
                                if sitekey not in sitekeys_found:
                                    sitekeys_found.append(sitekey)
                    
                    if sitekeys_found:
                        print(f"\n SITEKEY(S) FOUND: {', '.join(sitekeys_found)}")
                        
                        # Validate each sitekey
                        for sitekey in sitekeys_found:
                            print(f"\n Sitekey: {sitekey}")
                            await validate_sitekey(sitekey, url)
                        
                        # Exit after extraction
                        await browser.close()
                        return 0
                    
                    # If no sitekeys found in details, fall back to detailed extraction
                    if captcha_info['type'] == 'turnstile':
                        from modules.turnstile_solver import extract_turnstile_data
                        
                        print("\n Extracting Turnstile sitekey...")
                        turnstile_data = await extract_turnstile_data(browser.page)
                        
                        if turnstile_data['sitekeys'] and len(turnstile_data['sitekeys']) > 0:
                            # Filter out fake/invalid sitekeys
                            valid_sitekeys = []
                            for sk in turnstile_data['sitekeys']:
                                if sk and len(sk) >= 10 and sk != 'YOUR_SITE_KEY':
                                    valid_sitekeys.append(sk)
                            
                            if valid_sitekeys:
                                sitekey = valid_sitekeys[0]
                                print(f"\n SITEKEY FOUND: {sitekey}")
                                
                                # Just print the sitekey and exit - atomic operation
                                await browser.close()
                                # Return sitekey as exit code 0 with the key printed
                                return 0
                            else:
                                print("\n ERROR: No valid sitekey found")
                                print("   Possible reasons:")
                                print("   - Site uses fake/placeholder sitekeys")
                                print("   - Turnstile not properly configured")
                                print("   - Dynamic loading not complete")
                                
                                if turnstile_data['sitekeys']:
                                    print(f"\n   Found invalid sitekeys: {turnstile_data['sitekeys']}")
                        else:
                            print("\n ERROR: No sitekey found in Turnstile elements")
                            print("   The page has Turnstile but no data-sitekey attribute")
                    else:
                        print(f"\n ERROR: No Turnstile CAPTCHA detected")
                        print(f"   Found: {captcha_info['type'] if captcha_info['found'] else 'No CAPTCHA'}")
                    
                    # Exit with error code
                    await browser.close()
                    return 1
                
                if captcha_info['type'] == 'turnstile' and capsolver:
                    print("\n*** ATTEMPTING TURNSTILE SOLVING ***")
                    success = await attempt_capsolver_turnstile_solve(browser.page, capsolver, url)
                    
                    if success:
                        print(" Turnstile solved successfully")
                        
                        # Attempt automatic clicking after token injection
                        print("\n*** ATTEMPTING AUTOMATIC TURNSTILE CLICKING ***")
                        click_success = await attempt_automatic_turnstile_click(browser.page)
                        
                        if click_success:
                            print(" Automatic clicking completed")
                        else:
                            print(" Automatic clicking failed or no clickable elements found")
                        
                        # Verify solution
                        await asyncio.sleep(3)
                        post_solve_check = await detect_captcha_in_frames(browser.page)
                        if not post_solve_check['found']:
                            print(" CAPTCHA completely resolved")
                        else:
                            print(" CAPTCHA still present after solving")
                    else:
                        print(" Turnstile solving failed")
                else:
                    print(" No compatible solver available for this CAPTCHA type")
            else:
                if extract_sitekey:
                    print("\n ERROR: NO CAPTCHA DETECTED")
                    print("   No Turnstile widget found on the page")
                    print(f"   URL: {url}")
                    await browser.close()
                    return 1
                else:
                    print(" NO CAPTCHA DETECTED")
        
        # Save page content for analysis
        try:
            page_content = await browser.page.content()
            timestamp = int(time.time())
            filename = f"page_analysis_{timestamp}.html"
            full_path = log_dir / filename
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(page_content)
            print(f" Page content saved to: {full_path}")
        except Exception as e:
            print(f" Error saving page content: {e}")
        
        # For automated testing, don't keep browser open indefinitely
        print("\n*** SESSION COMPLETE ***")
        print("Closing browser...")
        await asyncio.sleep(2)
        
        await browser.close()
        print(f"Session log saved to: {log_filename}")
        
    except Exception as e:
        print(f"Error: {e}")
        try:
            await browser.close()
        except:
            pass  # Ignore browser close errors
        return 1
    
    finally:
        # Ensure browser is closed even if exceptions occur
        try:
            if 'browser' in locals() and browser.browser:
                await browser.close()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)