#!/usr/bin/python3

"""
Generic Turnstile CAPTCHA Solver Module
Navina Inc (c) 2025. All rights reserved.
"""

import asyncio
from .turnstile_patterns import TurnstilePatterns, TurnstileValidator
from .yara_turnstile_detector import get_yara_detector, scan_for_turnstile_yara, extract_sitekeys_yara

async def extract_turnstile_data_yara(page):
    """Extract Turnstile configuration data using YARA rules (preferred method)"""
    
    print("Extracting Turnstile data using YARA detection...")
    
    turnstile_data = {
        'found': False,
        'elements': [],
        'sitekeys': [],
        'config': {},
        'detection_method': 'YARA',
        'yara_results': None
    }
    
    try:
        # Get page content for YARA analysis
        page_content = await page.content()
        
        # Use YARA to scan for Turnstile patterns
        yara_results = scan_for_turnstile_yara(page_content)
        turnstile_data['yara_results'] = yara_results
        
        if yara_results.get('has_turnstile'):
            print(f"  YARA detected Turnstile: {yara_results['total_matches']} patterns matched")
            print(f"  Confidence: {yara_results['confidence_score']}%")
            print(f"  Categories: {', '.join(yara_results['categories'])}")
            
            turnstile_data['found'] = True
            
            # Extract sitekeys found by YARA
            yara_sitekeys = yara_results.get('sitekeys_found', [])
            if yara_sitekeys:
                turnstile_data['sitekeys'] = yara_sitekeys
                print(f"  YARA found sitekeys: {', '.join(yara_sitekeys)}")
            
            # Now use DOM scanning to get detailed element information
            # This gives us interactive elements that YARA patterns identified
            dom_elements = await page.evaluate("""
                (() => {
                    const elements = [];
                    
                    // Look for Turnstile containers based on YARA findings
                    const containerSelectors = [
                        '.cf-turnstile',
                        '[data-sitekey]',
                        '[class*="cf-turnstile"]',
                        'div[data-sitekey]'
                    ];
                    
                    containerSelectors.forEach(selector => {
                        try {
                            const widgets = document.querySelectorAll(selector);
                            widgets.forEach((widget, index) => {
                                const elementData = {
                                    index: elements.length,
                                    selector: selector,
                                    method: 'yara_dom_scan',
                                    tagName: widget.tagName,
                                    sitekey: widget.getAttribute('data-sitekey') || widget.dataset.sitekey,
                                    theme: widget.getAttribute('data-theme') || widget.dataset.theme,
                                    callback: widget.getAttribute('data-callback') || widget.dataset.callback,
                                    visible: widget.offsetParent !== null,
                                    id: widget.id,
                                    className: widget.className,
                                    boundingRect: widget.getBoundingClientRect(),
                                    source: 'YARA_DOM_SCAN'
                                };
                                
                                // Extract all data attributes
                                for (let attr of widget.attributes) {
                                    if (attr.name.startsWith('data-')) {
                                        elementData[attr.name] = attr.value;
                                    }
                                }
                                
                                elements.push(elementData);
                            });
                        } catch (e) {
                            console.warn('Error with selector', selector, e);
                        }
                    });
                    
                    return elements;
                })
            """)
            
            turnstile_data['elements'] = dom_elements or []
            
            # Merge sitekeys from DOM scan
            for element in turnstile_data['elements']:
                if element.get('sitekey') and element['sitekey'] not in turnstile_data['sitekeys']:
                    turnstile_data['sitekeys'].append(element['sitekey'])
            
            print(f"  Found {len(turnstile_data['elements'])} interactive elements")
            print(f"  Total sitekeys: {len(turnstile_data['sitekeys'])}")
            
        else:
            print("  YARA: No Turnstile patterns detected")
            
    except Exception as e:
        print(f"  YARA extraction error: {e}")
        print("  Falling back to regex-based detection...")
        # Fall back to the original method
        return await extract_turnstile_data_regex(page)
    
    return turnstile_data

async def extract_turnstile_data_regex(page):
    """Extract Turnstile configuration data using regex patterns (fallback method)"""
    
    print("Extracting Turnstile data using regex patterns (fallback)...")
    
    turnstile_data = {
        'found': False,
        'elements': [],
        'sitekeys': [],
        'config': {},
        'detection_method': 'REGEX_FALLBACK'
    }
    
    try:
        # Use comprehensive detection patterns (original regex method)
        patterns = TurnstilePatterns.get_comprehensive_selectors()
        
        # Convert Python dict to JavaScript object
        import json
        patterns_js = json.dumps(patterns)
        
        # First try standard pattern detection
        extraction_result = await page.evaluate(f"""
            (() => {{
                const elements = [];
                const patterns = {patterns_js};
                
                // Method 1: Container-based detection
                patterns.containers.forEach(selector => {{
                    try {{
                        const widgets = document.querySelectorAll(selector);
                        widgets.forEach(widget => {{
                            const elementData = {{
                                index: elements.length,
                                selector: selector,
                                method: 'container',
                                tagName: widget.tagName,
                                sitekey: widget.getAttribute('data-sitekey') || widget.dataset.sitekey,
                                theme: widget.getAttribute('data-theme') || widget.dataset.theme,
                                callback: widget.getAttribute('data-callback') || widget.dataset.callback,
                                visible: widget.offsetParent !== null,
                                id: widget.id,
                                className: widget.className,
                                boundingRect: widget.getBoundingClientRect(),
                                source: 'CONTAINER_SCAN'
                            }};
                            
                            // Extract all data attributes
                            for (let attr of widget.attributes) {{
                                if (attr.name.startsWith('data-')) {{
                                    elementData[attr.name] = attr.value;
                                }}
                            }}
                            
                            elements.push(elementData);
                        }});
                    }} catch (e) {{
                        console.warn('Error with selector', selector, e);
                    }}
                }});
                
                // Method 2: Iframe-based detection (immutable)
                patterns.iframes.forEach(selector => {{
                    try {{
                        const iframes = document.querySelectorAll(selector);
                        iframes.forEach(iframe => {{
                            elements.push({{
                                index: elements.length,
                                selector: selector,
                                method: 'iframe',
                                tagName: 'IFRAME',
                                src: iframe.src,
                                title: iframe.title,
                                name: iframe.name,
                                visible: iframe.offsetParent !== null,
                                boundingRect: iframe.getBoundingClientRect(),
                                source: 'IFRAME_SCAN'
                            }});
                        }});
                    }} catch (e) {{
                        console.warn('Error with iframe selector', selector, e);
                    }}
                }});
                
                // Method 3: Script-based detection
                patterns.scripts.forEach(selector => {{
                    try {{
                        const scripts = document.querySelectorAll(selector);
                        scripts.forEach(script => {{
                            elements.push({{
                                index: elements.length,
                                selector: selector,
                                method: 'script',
                                tagName: 'SCRIPT',
                                src: script.src,
                                async: script.async,
                                defer: script.defer,
                                source: 'SCRIPT_SCAN'
                            }});
                        }});
                    }} catch (e) {{
                        console.warn('Error with script selector', selector, e);
                    }}
                }});
                
                return {{
                    elements: elements,
                    found: elements.length > 0
                }};
            }})()
        """)
        
        # If standard detection fails, use fallback detection
        if not extraction_result.get('found'):
            print("Standard detection failed, trying fallback detection...")
            fallback_js = TurnstilePatterns.get_fallback_detection_js()
            fallback_result = await page.evaluate(fallback_js)
            
            if fallback_result.get('found'):
                extraction_result = {
                    'found': True,
                    'elements': fallback_result.get('elements', []),
                    'method': fallback_result.get('method'),
                    'details': fallback_result.get('details', {})
                }
        
        # Also check for network patterns
        network_js = TurnstilePatterns.get_network_detection_js()
        network_result = await page.evaluate(network_js)
        if network_result.get('found'):
            extraction_result['network_evidence'] = network_result
        
        if extraction_result['found']:
            turnstile_data['found'] = True
            turnstile_data['elements'] = extraction_result['elements']
            
            # Extract and validate unique sitekeys
            for element in turnstile_data['elements']:
                sitekey = element.get('sitekey') or element.get('data-sitekey')
                if sitekey and sitekey not in turnstile_data['sitekeys']:
                    if TurnstileValidator.validate_sitekey(sitekey):
                        turnstile_data['sitekeys'].append(sitekey)
                        turnstile_data['config'] = TurnstileValidator.extract_turnstile_config(element)
            
            # Add network evidence if found
            if 'network_evidence' in extraction_result:
                turnstile_data['network_evidence'] = extraction_result['network_evidence']
            
            # Enhanced reporting
            print(f" Found {len(turnstile_data['elements'])} Turnstile elements using comprehensive patterns")
            
            # Group by detection method
            methods = {}
            for element in turnstile_data['elements']:
                method = element.get('method', 'unknown')
                if method not in methods:
                    methods[method] = []
                methods[method].append(element)
            
            for method, elements in methods.items():
                print(f"  {method.upper()}: {len(elements)} element(s)")
                for element in elements[:3]:  # Show first 3 of each type
                    print(f"    - {element['tagName']} ({element['selector']})")
                    if element.get('sitekey'):
                        print(f"      Sitekey: {element['sitekey'][:20]}...")
                    if element.get('src'):
                        print(f"      Source: {element['src'][:50]}...")
            
            if turnstile_data['sitekeys']:
                print(f"  Valid Sitekeys: {len(turnstile_data['sitekeys'])}")
                for sitekey in turnstile_data['sitekeys']:
                    print(f"    - {sitekey}")
        else:
            print(" No Turnstile elements found with comprehensive detection")
    
    except Exception as e:
        print(f"Error extracting Turnstile data: {e}")
    
    return turnstile_data

async def extract_turnstile_data(page):
    """
    Extract Turnstile configuration data from the page
    
    Uses YARA-based detection as the primary method, with regex fallback.
    This replaces the previous regex-only approach with a more robust solution.
    """
    
    print("🔍 Starting Turnstile data extraction...")
    
    try:
        # Try YARA-based detection first (preferred method)
        yara_detector = get_yara_detector()
        if yara_detector.rules_loaded:
            print("  Using YARA-based detection (primary method)")
            result = await extract_turnstile_data_yara(page)
            
            # If YARA found something, use it
            if result.get('found'):
                print(f"  ✅ YARA detection successful: {len(result.get('sitekeys', []))} sitekeys found")
                return result
            else:
                print("  ⚠️  YARA detection found no Turnstile patterns")
        else:
            print("  ⚠️  YARA rules not available, skipping YARA detection")
        
        # Fall back to regex-based detection
        print("  Using regex-based detection (fallback method)")
        result = await extract_turnstile_data_regex(page)
        
        if result.get('found'):
            print(f"  ✅ Regex detection successful: {len(result.get('sitekeys', []))} sitekeys found")
        else:
            print("  ❌ No Turnstile patterns found by either method")
        
        return result
        
    except Exception as e:
        print(f"  ❌ Error during Turnstile extraction: {e}")
        # Final fallback to regex if everything else fails
        try:
            return await extract_turnstile_data_regex(page)
        except Exception as regex_error:
            print(f"  ❌ Regex fallback also failed: {regex_error}")
            return {
                'found': False,
                'elements': [],
                'sitekeys': [],
                'config': {},
                'detection_method': 'FAILED',
                'error': str(e)
            }

async def detect_captcha_in_frames(page):
    """Detect CAPTCHA presence in page and iframes"""
    
    captcha_info = {
        'found': False,
        'type': None,
        'confidence': 'low',
        'details': [],
        'js_events': []
    }
    
    try:
        # Use comprehensive Turnstile patterns for detection
        patterns = TurnstilePatterns.get_comprehensive_selectors()
        
        detection_result = await page.evaluate("""
            (() => {
                const results = {
                    turnstile: [],
                    recaptcha: [],
                    hcaptcha: [],
                    generic: []
                };
                
                // Enhanced Turnstile detection using comprehensive patterns
                const allTurnstileSelectors = [
                    // Container selectors
                    'div.cf-turnstile', '.cf-turnstile', '[class*="cf-turnstile"]',
                    '[data-sitekey]', 'div[data-sitekey]', '*[data-sitekey]',
                    '.turnstile-widget', '.captcha-widget[data-sitekey]', '.cf-widget',
                    '.cloudflare-turnstile', '[class*="turnstile"]', '[id*="turnstile"]',
                    'div[data-sitekey^="0x"]', 'div[data-sitekey^="1x"]',
                    '[data-sitekey^="0x"]', '[data-sitekey^="1x"]',
                    'input[name="cf-turnstile-response"]', 'input[id*="cf-chl-widget"]',
                    
                    // Iframe selectors
                    'iframe[src*="challenges.cloudflare.com"]',
                    'iframe[src*="challenges.cloudflare.com/turnstile"]',
                    'iframe[src*="challenges.cloudflare.com/cdn-cgi"]',
                    'iframe[src*="/turnstile/"]', 'iframe[title*="turnstile"]',
                    'iframe[title*="cloudflare"]', 'iframe[name*="cf-chl"]',
                    
                    // Script selectors  
                    'script[src*="challenges.cloudflare.com/turnstile"]',
                    'script[src*="challenges.cloudflare.com/turnstile/v0/api.js"]',
                    'script[src*="turnstile/v0/api.js"]'
                ];
                
                allTurnstileSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        results.turnstile.push({
                            selector: selector,
                            sitekey: el.getAttribute('data-sitekey') || '',
                            visible: el.offsetParent !== null,
                            src: el.src || ''
                        });
                    });
                });
                
                // reCAPTCHA detection
                const recaptchaSelectors = [
                    '.g-recaptcha',
                    'iframe[src*="recaptcha"]',
                    '[data-recaptcha]'
                ];
                
                recaptchaSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        results.recaptcha.push({
                            selector: selector,
                            sitekey: el.getAttribute('data-sitekey') || '',
                            visible: el.offsetParent !== null
                        });
                    });
                });
                
                // hCaptcha detection
                const hcaptchaSelectors = [
                    '.h-captcha',
                    'iframe[src*="hcaptcha"]'
                ];
                
                hcaptchaSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        results.hcaptcha.push({
                            selector: selector,
                            sitekey: el.getAttribute('data-sitekey') || '',
                            visible: el.offsetParent !== null
                        });
                    });
                });
                
                return results;
            })()
        """)
        
        # Analyze results and determine confidence
        confidence_score = 0
        detected_types = []
        all_details = []
        
        # DOM scan analysis
        if detection_result['turnstile']:
            detected_types.append('turnstile')
            confidence_score += 3
            for item in detection_result['turnstile']:
                if item['sitekey']:
                    confidence_score += 2
                    all_details.append(f"Turnstile with sitekey: {item['sitekey']}")
                else:
                    all_details.append("Turnstile element detected")
        
        if detection_result['recaptcha']:
            detected_types.append('recaptcha')
            confidence_score += 3
            for item in detection_result['recaptcha']:
                if item['sitekey']:
                    confidence_score += 2
                    all_details.append(f"reCAPTCHA with sitekey: {item['sitekey']}")
                else:
                    all_details.append("reCAPTCHA element detected")
        
        if detection_result['hcaptcha']:
            detected_types.append('hcaptcha')
            confidence_score += 3
            for item in detection_result['hcaptcha']:
                if item['sitekey']:
                    confidence_score += 2
                    all_details.append(f"hCaptcha with sitekey: {item['sitekey']}")
                else:
                    all_details.append("hCaptcha element detected")
        
        captcha_info['details'] = all_details
        
        # Set confidence level
        if confidence_score >= 5:
            captcha_info['confidence'] = 'high'
        elif confidence_score >= 2:
            captcha_info['confidence'] = 'medium'
        else:
            captcha_info['confidence'] = 'low'
        
        if detected_types:
            captcha_info['found'] = True
            # Prioritize Turnstile > reCAPTCHA > hCaptcha
            if 'turnstile' in detected_types:
                captcha_info['type'] = 'turnstile'
            elif 'recaptcha' in detected_types:
                captcha_info['type'] = 'recaptcha'
            elif 'hcaptcha' in detected_types:
                captcha_info['type'] = 'hcaptcha'
            else:
                captcha_info['type'] = 'generic'
    
    except Exception as e:
        print(f"Error in CAPTCHA detection: {e}")
        captcha_info['details'].append(f"Detection error: {e}")
    
    return captcha_info

async def attempt_automatic_turnstile_click(page):
    """Attempt to automatically click the Turnstile checkbox/widget"""
    try:
        print("Searching for clickable Turnstile elements...")
        
        success_count = 0
        
        # First, try to find and click inside Turnstile iframes
        print("  Looking for Turnstile iframes...")
        iframe_selectors = [
            "iframe[src*='challenges.cloudflare.com']",
            "iframe[src*='turnstile']",
            "iframe[title*='turnstile']",
            "iframe[title*='cloudflare']"
        ]
        
        for iframe_selector in iframe_selectors:
            try:
                iframes = await page.query_selector_all(iframe_selector)
                if iframes:
                    print(f"    Found {len(iframes)} iframe(s) with selector: {iframe_selector}")
                    
                    for i, iframe in enumerate(iframes):
                        try:
                            print(f"    Attempting to access iframe #{i+1}...")
                            
                            # Get iframe content
                            iframe_content = await iframe.content_frame()
                            if iframe_content:
                                print(f"    Successfully accessed iframe #{i+1} content")
                                
                                # Look for clickable elements inside the iframe
                                click_targets = [
                                    "input[type='checkbox']",
                                    "button",
                                    "div[role='button']",
                                    "label",
                                    ".challenge-form input",
                                    ".challenge-form button",
                                    "[class*='checkbox']",
                                    "[class*='button']"
                                ]
                                
                                for target_selector in click_targets:
                                    try:
                                        elements = await iframe_content.query_selector_all(target_selector)
                                        if elements:
                                            print(f"      Found {len(elements)} clickable element(s): {target_selector}")
                                            
                                            for j, element in enumerate(elements):
                                                try:
                                                    # Check if element is visible
                                                    is_visible = await iframe_content.evaluate('(element) => {return element.offsetParent !== null}', element)
                                                    
                                                    if is_visible:
                                                        print(f"      Clicking element #{j+1} ({target_selector})...")
                                                        
                                                        # Human-like interaction
                                                        await element.hover()
                                                        await asyncio.sleep(0.5)
                                                        await element.click()
                                                        success_count += 1
                                                        
                                                        print(f"       Successfully clicked element #{j+1}")
                                                        
                                                        # Wait to see if anything happens
                                                        await asyncio.sleep(2)
                                                        
                                                    else:
                                                        print(f"      Element #{j+1} not visible, skipping")
                                                except Exception as e:
                                                    print(f"       Failed to click element #{j+1}: {e}")
                                                    continue
                                    except Exception as e:
                                        print(f"      Error finding {target_selector}: {e}")
                                        continue
                            else:
                                print(f"    Cannot access iframe #{i+1} content")
                                
                        except Exception as e:
                            print(f"    Error accessing iframe #{i+1}: {e}")
                            continue
            except Exception as e:
                print(f"  Error with iframe selector {iframe_selector}: {e}")
                continue
        
        # If iframe clicking didn't work, try clicking the main page elements
        if success_count == 0:
            print("  No iframe clicks successful, trying main page elements...")
            
            main_page_strategies = [
                (".cf-turnstile", "Turnstile widget container"),
                ("[data-sitekey]", "Widget with sitekey"),
                ("input[type='checkbox'][id*='cf-chl']", "Cloudflare challenge checkbox"),
                ("input[type='checkbox'][name*='turnstile']", "Turnstile checkbox"),
                ("label[for*='cf-chl']", "Cloudflare challenge label"),
                ("label[for*='turnstile']", "Turnstile label"),
                ("[class*='turnstile']", "Turnstile class elements")
            ]
            
            for selector, description in main_page_strategies:
                try:
                    print(f"  Trying strategy: {description} ({selector})")
                    
                    # Find elements with Puppeteer
                    elements = await page.query_selector_all(selector)
                    
                    if elements:
                        print(f"    Found {len(elements)} {description} element(s)")
                        
                        for i, element in enumerate(elements):
                            try:
                                # Check if element is visible
                                is_visible = await page.evaluate('(element) => {return element.offsetParent !== null}', element)
                                
                                if is_visible:
                                    print(f"    Clicking {description} #{i+1}...")
                                    
                                    # Human-like interaction
                                    await element.hover()
                                    await asyncio.sleep(0.5)
                                    await element.click()
                                    success_count += 1
                                    
                                    print(f"     Successfully clicked {description} #{i+1}")
                                    
                                    # Wait to see if anything happens
                                    await asyncio.sleep(2)
                                    
                                else:
                                    print(f"    Element #{i+1} not visible, skipping")
                            except Exception as e:
                                print(f"     Failed to click {description} #{i+1}: {e}")
                                continue
                    else:
                        print(f"    No {description} elements found")
                        
                except Exception as e:
                    print(f"    Error with strategy {description}: {e}")
                    continue
        
        print(f"Automatic Turnstile clicking completed. Total successful actions: {success_count}")
        return success_count > 0
        
    except Exception as e:
        print(f"Error in automatic Turnstile clicking: {e}")
        return False

async def attempt_server_turnstile_solve(page, sitekey, website_url):
    """Attempt to solve Turnstile using local server"""
    try:
        from .turnstile_server import start_turnstile_server
        
        print("  Starting local Turnstile server for solving...")
        server = start_turnstile_server()
        
        # Create solve URL
        solve_url = f"http://localhost:8888/solve?sitekey={sitekey}&url={website_url}"
        
        # Open solve page in new tab
        browser = page.browser
        solve_page = await browser.new_page()
        await solve_page.goto(solve_url)
        
        # Wait for solution
        print("  Waiting for Turnstile solution from local server...")
        max_wait = 30  # seconds
        start_time = asyncio.get_event_loop().time()
        
        while True:
            sessions = server.get_all_sessions()
            for session_id, session_data in sessions.items():
                if session_data.get('status') == 'completed' and session_data.get('token'):
                    token = session_data['token']
                    print(f"   Got token from local server: {token[:50]}...")
                    
                    # Close solve page
                    await solve_page.close()
                    
                    # Return the token
                    return token
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > max_wait:
                print("   Timeout waiting for local server solution")
                await solve_page.close()
                return None
            
            await asyncio.sleep(0.5)
            
    except Exception as e:
        print(f"  Error with local server solving: {e}")
        return None

async def attempt_capsolver_turnstile_solve(page, capsolver, website_url):
    """Attempt to solve Turnstile using CapSolver API for generic sites"""
    try:
        print("Extracting Turnstile data for CapSolver...")
        
        # Extract Turnstile data from the page
        turnstile_data = await extract_turnstile_data(page)
        
        if not turnstile_data['elements']:
            print("  No Turnstile elements found for solving")
            return False
        
        success_count = 0
        
        for element in turnstile_data['elements']:
            if not element['visible']:
                print(f"  Skipping invisible element {element['index']}")
                continue
                
            sitekey = element['sitekey']
            action = element.get('action')
            cdata = element.get('cdata')
            
            if not sitekey:
                print(f"  Element {element['index']} has no sitekey, skipping")
                continue
            
            print(f"  Solving Turnstile element {element['index']}:")
            print(f"    Site Key: {sitekey}")
            print(f"    Action: {action}")
            print(f"    CData: {cdata}")
            
            # Solve with CapSolver API
            try:
                token = capsolver.solve_turnstile(
                    website_url=website_url,
                    website_key=sitekey,
                    action=action,
                    cdata=cdata
                )
                
                if token:
                    print(f"     Got solution token: {token[:50]}...")
                    
                    # Inject the solution using multiple methods
                    injection_success = await page.evaluate(f"""
                        (token) => {{
                            try {{
                                let injected = false;
                                console.log('Injecting Turnstile token via multiple methods...');
                                
                                // Method 1: Standard Turnstile response field
                                const responseField = document.querySelector('input[name="cf-turnstile-response"]');
                                if (responseField) {{
                                    responseField.value = token;
                                    console.log('Token injected into cf-turnstile-response field');
                                    injected = true;
                                }}
                                
                                // Method 2: Generic form fields
                                const formFields = document.querySelectorAll('input[name*="turnstile"], input[name*="captcha"]');
                                formFields.forEach(field => {{
                                    field.value = token;
                                    console.log('Token injected into form field:', field.name);
                                    injected = true;
                                }});
                                
                                // Method 3: Use Turnstile API if available
                                if (window.turnstile && typeof window.turnstile.setResponse === 'function') {{
                                    try {{
                                        window.turnstile.setResponse('0', token);
                                        console.log('Token set via Turnstile API');
                                        injected = true;
                                    }} catch(e) {{
                                        console.log('Turnstile API error:', e);
                                    }}
                                }}
                                
                                return injected;
                            }} catch(e) {{
                                console.log('Token injection error:', e);
                                return false;
                            }}
                        }}
                    """, token)
                    
                    if injection_success:
                        print(f"     Token injection successful")
                        success_count += 1
                    else:
                        print(f"     Token injection failed")
                else:
                    print(f"     CapSolver failed to solve this element")
                    
                    # Try local server as fallback
                    print(f"     Trying local server as fallback...")
                    server_token = await attempt_server_turnstile_solve(page, sitekey, website_url)
                    
                    if server_token:
                        # Inject the server token
                        injection_success = await page.evaluate(f"""
                            (token) => {{
                                try {{
                                    let injected = false;
                                    console.log('Injecting server token...');
                                    
                                    // Standard Turnstile response field
                                    const responseField = document.querySelector('input[name="cf-turnstile-response"]');
                                    if (responseField) {{
                                        responseField.value = token;
                                        console.log('Token injected into cf-turnstile-response field');
                                        injected = true;
                                    }}
                                    
                                    // Generic form fields
                                    const formFields = document.querySelectorAll('input[name*="turnstile"], input[name*="captcha"]');
                                    formFields.forEach(field => {{
                                        field.value = token;
                                        console.log('Token injected into form field:', field.name);
                                        injected = true;
                                    }});
                                    
                                    return injected;
                                }} catch(e) {{
                                    console.log('Token injection error:', e);
                                    return false;
                                }}
                            }}
                        """, server_token)
                        
                        if injection_success:
                            print(f"     Server token injection successful")
                            success_count += 1
                        else:
                            print(f"     Server token injection failed")
                    else:
                        print(f"     Local server also failed")
                    
            except Exception as e:
                print(f"     Error solving element {element['index']}: {e}")
                continue
        
        print(f"CapSolver solving completed. Successfully solved {success_count} elements.")
        return success_count > 0
        
    except Exception as e:
        print(f"Error in CapSolver Turnstile solving: {e}")
        return False