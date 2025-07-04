#!/usr/bin/python3

"""
ECW-Specific CAPTCHA and Login Handler Module
Navina Inc (c) 2025. All rights reserved.
"""

import asyncio
import toml
from pathlib import Path
from .turnstile_solver import attempt_capsolver_turnstile_solve, detect_captcha_in_frames

async def load_ecw_credentials():
    """Load ECW credentials from config file"""
    try:
        config_path = Path(".ghost/config.toml")
        if config_path.exists():
            config = toml.load(config_path)
            ecw_config = config.get('ecw', {})
            return {
                'username': ecw_config.get('user'),
                'password': ecw_config.get('password'),
                'uri': ecw_config.get('uri')
            }
        else:
            print("Config file not found at .ghost/config.toml")
            return None
    except Exception as e:
        print(f"Error loading ECW credentials: {e}")
        return None

async def find_and_click_next_button(page):
    """Find and click the next button with comprehensive fallback strategies"""
    print("*** Looking for Next Step button ***")
    
    # Enhanced Next Step button detection with multiple selectors
    next_button_selectors = [
        "input[id='nextStep']",
        "button[id='nextStep']",
        "input[value*='Next']",
        "input[value*='next']",
        "button[value*='Next']",
        "button[value*='next']",
        "input[type='submit']",
        "button[type='submit']",
        "input[class*='next']",
        "button[class*='next']",
        "input[onclick*='next']",
        "button[onclick*='next']",
        "a[href*='next']",
        "div[onclick*='next']",
        "span[onclick*='next']"
    ]
    
    # Try to find and click next button
    next_clicked = await page.evaluate("""
        (selectors) => {
            console.log('Searching for Next Step button...');
            
            // First try direct methods
            // Method 1: Try calling validateStep1Form function if available
            if (typeof validateStep1Form === 'function') {
                console.log('Found validateStep1Form function, calling it...');
                try {
                    validateStep1Form();
                    return { success: true, method: 'validateStep1Form' };
                } catch (e) {
                    console.log('validateStep1Form failed:', e);
                }
            }
            
            // Method 2: Look for next button with selectors
            for (const selector of selectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    console.log(`Checking selector '${selector}': found ${elements.length} elements`);
                    
                    for (const element of elements) {
                        if (element && element.offsetParent !== null && !element.disabled) {
                            const elementText = element.textContent || element.value || '';
                            const elementId = element.id || '';
                            const elementClass = element.className || '';
                            
                            console.log(`  - Visible element: text='${elementText}', id='${elementId}', class='${elementClass}'`);
                            
                            if (elementText.toLowerCase().includes('next') || 
                                elementId.toLowerCase().includes('next') ||
                                selector.toLowerCase().includes('next')) {
                                console.log(`    *** Clicking: ${selector} ***`);
                                element.click();
                                return { success: true, method: 'button_click', selector: selector };
                            }
                        }
                    }
                } catch (e) {
                    console.log(`Error with selector '${selector}':`, e);
                }
            }
            
            // Method 3: Debug all buttons and inputs
            console.log('Standard selectors failed, debugging all buttons...');
            const allButtons = document.querySelectorAll("button, input[type='button'], input[type='submit']");
            console.log(`Found ${allButtons.length} total buttons/inputs`);
            
            for (let i = 0; i < allButtons.length; i++) {
                const btn = allButtons[i];
                try {
                    const btnText = btn.textContent || btn.value || '';
                    const btnId = btn.id || '';
                    const btnClass = btn.className || '';
                    const btnType = btn.type || btn.tagName.toLowerCase();
                    const isVisible = btn.offsetParent !== null;
                    const isEnabled = !btn.disabled;
                    
                    console.log(`  Button ${i}: type='${btnType}', text='${btnText}', id='${btnId}', class='${btnClass}', visible=${isVisible}, enabled=${isEnabled}`);
                    
                    // If it looks like a next button, try to use it
                    if (isVisible && isEnabled && 
                        (btnText.toLowerCase().includes('next') || 
                         btnText.toLowerCase().includes('continue') || 
                         btnText.toLowerCase().includes('step'))) {
                        console.log(`    *** Clicking alternative next button ***`);
                        btn.click();
                        return { success: true, method: 'alternative_button', text: btnText };
                    }
                } catch (e) {
                    console.log(`Error analyzing button ${i}:`, e);
                }
            }
            
            return { success: false, method: 'none' };
        }
    """, next_button_selectors)
    
    if next_clicked['success']:
        print(f" Next Step button clicked successfully via: {next_clicked['method']}")
        return True
    else:
        print(" Could not find Next Step button with standard methods")
        
        # Fallback: Try pressing Enter on the username field
        print("Fallback: Trying to press Enter on username field...")
        enter_pressed = await page.evaluate("""
            () => {
                const usernameFields = document.querySelectorAll(
                    'input[name="doctorID"], input[id="doctorID"], ' +
                    'input[type="text"]:not([type="hidden"])'
                );
                
                for (const field of usernameFields) {
                    if (field && field.offsetParent !== null && field.value) {
                        console.log('Pressing Enter on username field...');
                        const event = new KeyboardEvent('keydown', { 
                            key: 'Enter', 
                            keyCode: 13, 
                            which: 13,
                            bubbles: true 
                        });
                        field.dispatchEvent(event);
                        
                        // Also try submitting the form
                        const form = field.closest('form');
                        if (form) {
                            try {
                                form.submit();
                            } catch(e) {
                                console.log('Form submit failed:', e);
                            }
                        }
                        
                        return true;
                    }
                }
                return false;
            }
        """)
        
        if enter_pressed:
            print(" Pressed Enter on username field")
            return True
        else:
            print(" Could not trigger next step via Enter key")
            return False

async def wait_for_password_field(page, max_attempts=5):
    """Wait for password field to appear with multiple detection methods"""
    print("Waiting for password field to appear...")
    
    for attempt in range(max_attempts):
        print(f"  Password field check attempt {attempt + 1}/{max_attempts}...")
        
        # Check for password field
        password_check = await page.evaluate("""
            () => {
                // Check for password field multiple ways
                const passwordSelectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[id="password"]',
                    'input[name="passwordField"]',
                    'input[id="passwordField"]',
                    'input[name*="pass"]:not([type="hidden"])',
                    'input[id*="pass"]:not([type="hidden"])'
                ];
                
                let passwordField = null;
                let passwordFieldSelector = null;
                
                for (const selector of passwordSelectors) {
                    const field = document.querySelector(selector);
                    if (field && field.offsetParent !== null) {
                        passwordField = field;
                        passwordFieldSelector = selector;
                        break;
                    }
                }
                
                // Also check for "next screen" message
                const bodyText = document.body.textContent.toLowerCase();
                const hasNextScreenMessage = 
                    bodyText.includes('enter your password on next screen') || 
                    bodyText.includes('password on next') ||
                    bodyText.includes('next screen');
                
                return {
                    hasPasswordField: !!passwordField,
                    passwordFieldSelector: passwordFieldSelector,
                    hasNextScreenMessage: hasNextScreenMessage,
                    url: window.location.href,
                    allInputsCount: document.querySelectorAll('input').length
                };
            }
        """)
        
        if password_check['hasPasswordField']:
            print(f" Password field found via: {password_check['passwordFieldSelector']}")
            return True
        elif password_check['hasNextScreenMessage']:
            print(" Found 'Enter your password on next screen' message")
            print("  ECW requires manual navigation to password screen")
            return 'manual_required'
        else:
            print(f"  No password field yet (total inputs: {password_check['allInputsCount']})")
            await asyncio.sleep(2)
    
    return False

async def handle_ecw_login(page, capsolver, url):
    """Handle ECW-specific login process with improved navigation"""
    try:
        print("\n*** ECW LOGIN HANDLING ***")
        
        # Load credentials
        credentials = await load_ecw_credentials()
        if not credentials or not credentials['username'] or not credentials['password']:
            print("ECW credentials not found in config")
            return False
        
        print(f"Loaded ECW credentials for user: {credentials['username']}")
        
        # Wait for page to load completely
        print("Waiting for ECW page to load completely...")
        await asyncio.sleep(3)
        
        # Check if we're already on password step
        current_step = await page.evaluate("""
            () => {
                const passwordField = document.querySelector('input[type="password"], input[name="passwordField"]');
                const usernameField = document.querySelector('input[name="doctorID"], input[id="doctorID"]');
                const usernameHidden = document.querySelector('input[name="doctorID"][type="hidden"]');
                
                return {
                    hasPasswordField: !!passwordField && passwordField.offsetParent !== null,
                    hasUsernameField: !!usernameField && usernameField.offsetParent !== null,
                    hasHiddenUsername: !!usernameHidden,
                    url: window.location.href
                };
            }
        """)
        
        print(f"Current page state: Password field: {current_step['hasPasswordField']}, Username field: {current_step['hasUsernameField']}")
        
        # Handle based on current step
        if current_step['hasPasswordField'] and not current_step['hasUsernameField']:
            print("Already on password entry step")
            # Fill password directly
            password_filled = await page.evaluate(f"""
                (password) => {{
                    const selectors = [
                        'input[name="passwordField"]',
                        'input[id="passwordField"]',
                        'input[type="password"]'
                    ];
                    
                    for (const selector of selectors) {{
                        const field = document.querySelector(selector);
                        if (field && field.offsetParent !== null) {{
                            field.value = password;
                            field.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            field.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            console.log('Password filled via:', selector);
                            return selector;
                        }}
                    }}
                    return false;
                }}
            """, credentials['password'])
            
            if password_filled:
                print(f" Password filled via {password_filled}")
            else:
                print(" Could not fill password field")
                return False
                
        else:
            # Step 1: Fill username
            print("Step 1: Filling username...")
            username_filled = await page.evaluate(f"""
                (username) => {{
                    const selectors = [
                        'input[name="doctorID"]',
                        'input[id="doctorID"]',
                        'input[name="username"]',
                        'input[type="text"]:first-of-type'
                    ];
                    
                    for (const selector of selectors) {{
                        const field = document.querySelector(selector);
                        if (field && field.offsetParent !== null) {{
                            // Clear field first
                            field.value = '';
                            field.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            
                            // Set new value
                            field.value = username;
                            field.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            field.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            
                            // Focus and blur to trigger validation
                            field.focus();
                            field.blur();
                            
                            console.log('Username filled via:', selector);
                            return selector;
                        }}
                    }}
                    return false;
                }}
            """, credentials['username'])
            
            if not username_filled:
                print(" Could not find username field")
                return False
                
            print(f" Username filled via {username_filled}")
            
            # Wait for any dynamic content
            await asyncio.sleep(2)
            
            # Check for CAPTCHA after username entry
            print("Checking for CAPTCHA after username entry...")
            captcha_info = await detect_captcha_in_frames(page)
            
            if captcha_info['found']:
                print(f"CAPTCHA detected: {captcha_info['type']}")
                
                if captcha_info['type'] == 'turnstile' and capsolver:
                    print("Attempting to solve Turnstile CAPTCHA...")
                    solve_success = await attempt_capsolver_turnstile_solve(page, capsolver, url)
                    
                    if solve_success:
                        print(" CAPTCHA solved successfully")
                        await asyncio.sleep(2)
                    else:
                        print(" CAPTCHA solving failed")
                        return False
            
            # Click Next Step button
            next_clicked = await find_and_click_next_button(page)
            
            if next_clicked:
                # Wait for navigation/password field
                await asyncio.sleep(3)
                
                # Wait for password field to appear
                password_field_status = await wait_for_password_field(page)
                
                if password_field_status == True:
                    # Fill password
                    print("Step 2: Filling password...")
                    password_filled = await page.evaluate(f"""
                        (password) => {{
                            const selectors = [
                                'input[name="passwordField"]',
                                'input[id="passwordField"]',
                                'input[type="password"]'
                            ];
                            
                            for (const selector of selectors) {{
                                const field = document.querySelector(selector);
                                if (field && field.offsetParent !== null) {{
                                    field.value = password;
                                    field.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    field.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    console.log('Password filled via:', selector);
                                    return selector;
                                }}
                            }}
                            return false;
                        }}
                    """, credentials['password'])
                    
                    if password_filled:
                        print(f" Password filled via {password_filled}")
                    else:
                        print(" Could not fill password field")
                        return False
                        
                elif password_field_status == 'manual_required':
                    print("\nECW Security Notice:")
                    print("  The site shows 'Enter your password on next screen'")
                    print("  Manual navigation to password screen is required")
                    print("  This is an ECW security feature that cannot be automated")
                    return True  # Consider this a successful first step
                else:
                    print(" Password field did not appear after clicking Next")
                    return False
            else:
                print(" Could not proceed to password step")
                return False
        
        # Check for final CAPTCHA before submission
        print("Checking for CAPTCHA before final submission...")
        final_captcha = await detect_captcha_in_frames(page)
        
        if final_captcha['found']:
            print(f"Final CAPTCHA detected: {final_captcha['type']}")
            
            if final_captcha['type'] == 'turnstile' and capsolver:
                print("Solving final CAPTCHA...")
                final_solve = await attempt_capsolver_turnstile_solve(page, capsolver, url)
                
                if final_solve:
                    print(" Final CAPTCHA solved")
                    await asyncio.sleep(2)
                else:
                    print(" Final CAPTCHA solving failed")
                    return False
        
        # Submit login form
        print("Submitting ECW login form...")
        submit_success = await page.evaluate("""
            () => {
                // Try multiple submission methods
                const methods = [
                    // Method 1: Click submit button
                    () => {
                        const submitButtons = document.querySelectorAll(
                            'input[type="submit"], button[type="submit"], ' +
                            'input[value*="Login"], input[value*="Sign"], ' +
                            'button:contains("Login"), button:contains("Sign")'
                        );
                        for (const btn of submitButtons) {
                            if (btn.offsetParent !== null && !btn.disabled) {
                                btn.click();
                                return 'submit_button';
                            }
                        }
                        return null;
                    },
                    
                    // Method 2: Submit form directly
                    () => {
                        const forms = document.querySelectorAll('form');
                        for (const form of forms) {
                            const hasPassword = form.querySelector('input[type="password"]');
                            if (hasPassword || forms.length === 1) {
                                form.submit();
                                return 'form_submit';
                            }
                        }
                        return null;
                    },
                    
                    // Method 3: Press Enter on password field
                    () => {
                        const passwordField = document.querySelector('input[type="password"]');
                        if (passwordField) {
                            const event = new KeyboardEvent('keydown', { 
                                key: 'Enter', 
                                keyCode: 13,
                                bubbles: true 
                            });
                            passwordField.dispatchEvent(event);
                            return 'enter_key';
                        }
                        return null;
                    }
                ];
                
                for (const method of methods) {
                    const result = method();
                    if (result) {
                        console.log('Form submitted via:', result);
                        return result;
                    }
                }
                
                return null;
            }
        """)
        
        if submit_success:
            print(f" Form submitted via: {submit_success}")
            await asyncio.sleep(5)  # Wait for login processing
            return True
        else:
            print(" Could not submit login form")
            return False
            
    except Exception as e:
        print(f"Error in ECW login handling: {e}")
        return False

async def verify_ecw_login_success(page):
    """Verify if ECW login was successful"""
    try:
        print("Verifying ECW login success...")
        
        # Wait for page to settle
        await asyncio.sleep(3)
        
        # Check for success indicators
        success_indicators = await page.evaluate("""
            () => {
                const indicators = {
                    url: window.location.href,
                    title: document.title,
                    hasLogoutButton: !!document.querySelector('a[href*="logout"]') || 
                                    !!Array.from(document.querySelectorAll('button, a')).find(el => el.textContent.toLowerCase().includes('logout')),
                    hasUserMenu: !!document.querySelector('[class*="user"], [id*="user"], [class*="profile"]'),
                    hasMainContent: !!document.querySelector('main, [id="main"], [class*="main"], [class*="dashboard"]'),
                    noLoginForm: !document.querySelector('input[type="password"]'),
                    bodyText: document.body.textContent.toLowerCase()
                };
                
                // Check for error messages
                indicators.hasErrorMessage = 
                    indicators.bodyText.includes('invalid') ||
                    indicators.bodyText.includes('error') ||
                    indicators.bodyText.includes('failed') ||
                    indicators.bodyText.includes('incorrect');
                
                // Check for welcome/success messages
                indicators.hasWelcomeMessage = 
                    indicators.bodyText.includes('welcome') ||
                    indicators.bodyText.includes('dashboard') ||
                    indicators.bodyText.includes('home');
                
                return indicators;
            }
        """)
        
        # Analyze indicators
        success_score = 0
        
        if success_indicators['hasLogoutButton']:
            success_score += 3
            print(" Logout button found")
        
        if success_indicators['hasUserMenu']:
            success_score += 2
            print(" User menu found")
        
        if success_indicators['hasMainContent']:
            success_score += 2
            print(" Main content area found")
        
        if success_indicators['noLoginForm']:
            success_score += 2
            print(" No login form present")
        
        if success_indicators['hasWelcomeMessage']:
            success_score += 1
            print(" Welcome message detected")
        
        if success_indicators['hasErrorMessage']:
            success_score -= 3
            print(" Error message detected")
        
        # Check URL changes
        if 'login' not in success_indicators['url'].lower():
            success_score += 1
            print(" URL changed from login page")
        
        login_successful = success_score >= 3
        
        print(f"Login verification score: {success_score}")
        if login_successful:
            print(" ECW login appears successful")
        else:
            print(" ECW login verification failed")
            print(f"  Current URL: {success_indicators['url']}")
            print(f"  Page title: {success_indicators['title']}")
        
        return login_successful
        
    except Exception as e:
        print(f"Error verifying ECW login: {e}")
        return False