#!/usr/bin/python3

"""
Turnstile CAPTCHA Testing Script
Tests enhanced Turnstile solving without modifying original files
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
from modules.turnstile_solver import detect_captcha_in_frames
from modules.turnstile_test import test_turnstile_interaction

# Global browser reference for cleanup
current_browser = None

def signal_handler(sig, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown"""
    print("\nReceived shutdown signal...")
    if current_browser and current_browser.browser:
        try:
            import subprocess
            subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
        except:
            pass
    sys.exit(0)

async def main():
    """Main testing function"""
    global current_browser
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if len(sys.argv) < 2:
        print("Usage: python test_turnstile.py <URL> [capsolver_api_key]")
        sys.exit(1)
    
    url = sys.argv[1]
    capsolver_api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Testing Turnstile interaction on: {url}")
    
    # Initialize CapSolver
    capsolver = CapsSolver(capsolver_api_key)
    if capsolver.api_key:
        print(f"CapSolver initialized with API key: {capsolver.api_key[:10]}...")
    else:
        print("No CapSolver API key available - testing will be limited")
    
    # Setup logging
    log_dir = Path("log")
    log_dir.mkdir(exist_ok=True)
    log_filename = log_dir / f"turnstile_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Initialize browser
    browser = BaseBrowser(headless=False)
    current_browser = browser
    browser.session_logger = SessionLogger(log_filename)
    
    try:
        print(f"Starting browser for: {url}")
        await browser.launch_browser()
        
        # Navigate to URL
        await browser.navigate_to_url(url)
        
        # Wait for page to load completely
        await asyncio.sleep(3)
        
        # Scan for CAPTCHAs
        print("\n=== INITIAL CAPTCHA SCAN ===")
        captcha_info = await detect_captcha_in_frames(browser.page)
        
        if captcha_info['found']:
            print(f"CAPTCHA DETECTED: {captcha_info['type'].upper()}")
            print(f"Details: {captcha_info['details']}")
            
            if captcha_info['type'] == 'turnstile' and capsolver and capsolver.api_key:
                print("\n=== STARTING ENHANCED TURNSTILE TEST ===")
                
                # Test the enhanced interaction
                success = await test_turnstile_interaction(browser.page, capsolver, url)
                
                if success:
                    print("\n TURNSTILE TEST SUCCESSFUL!")
                    print("The enhanced interaction resolved the CAPTCHA")
                else:
                    print("\n TURNSTILE TEST INCOMPLETE")
                    print("The CAPTCHA was not fully resolved")
                    
            else:
                print("\n Cannot test - either not Turnstile or no API key")
        else:
            print("\n NO CAPTCHA DETECTED")
            print("No Turnstile CAPTCHAs found to test")
        
        # Save page content for analysis
        try:
            page_content = await browser.page.content()
            timestamp = int(time.time())
            filename = f"turnstile_test_{timestamp}.html"
            full_path = log_dir / filename
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(page_content)
            print(f"\nPage content saved to: {full_path}")
        except Exception as e:
            print(f"Error saving page content: {e}")
        
        # Keep browser open for manual inspection
        print("\n=== TEST COMPLETE ===")
        print("Browser will remain open for 30 seconds for manual inspection...")
        await asyncio.sleep(30)
        
        await browser.close()
        print(f"Test log saved to: {log_filename}")
        
    except Exception as e:
        print(f"Error: {e}")
        try:
            await browser.close()
        except:
            pass
        return 1
    
    finally:
        # Ensure browser is closed
        try:
            if 'browser' in locals() and browser.browser:
                await browser.close()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)