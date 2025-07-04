#!/usr/bin/python3

"""
Turnstile Detection Patterns Module
Navina Inc (c) 2025. All rights reserved.

Comprehensive patterns for detecting Cloudflare Turnstile CAPTCHA across various implementations.
Based on instruction.txt requirements for robust detection.
"""

class TurnstilePatterns:
    """
    Comprehensive Turnstile detection patterns that handle various implementations
    including renamed classes, wrapped containers, and obfuscated setups.
    """
    
    # Primary container selectors (most reliable)
    CONTAINER_SELECTORS = [
        # Standard cf-turnstile class (most common)
        'div.cf-turnstile',
        '.cf-turnstile',
        '[class*="cf-turnstile"]',
        
        # Data-sitekey attribute (always present and immutable)
        '[data-sitekey]',
        'div[data-sitekey]',
        '*[data-sitekey]',  # Any element with sitekey
        
        # Common wrapper patterns and variations
        '.turnstile-widget',
        '.captcha-widget[data-sitekey]',
        '.cf-widget',
        '.cloudflare-turnstile',
        '[class*="turnstile"]',
        '[id*="turnstile"]',
        '[class*="cloudflare"]',
        
        # Sitekey patterns (from research - most start with 0x)
        'div[data-sitekey^="0x"]',  # Standard: 0x4AAAAAAA...
        'div[data-sitekey^="1x"]',  # Alternative format
        '[data-sitekey^="0x"]',     # Any element
        '[data-sitekey^="1x"]',
        
        # Hidden response field detection
        'input[name="cf-turnstile-response"]',
        'input[id*="cf-chl-widget"]',
        'input[name*="turnstile"]',
    ]
    
    # Iframe source patterns (immutable - cannot be changed by web admins)
    IFRAME_SELECTORS = [
        # Primary Cloudflare challenge domain
        'iframe[src*="challenges.cloudflare.com"]',
        'iframe[src*="challenges.cloudflare.com/turnstile"]',
        'iframe[src*="challenges.cloudflare.com/cdn-cgi"]',
        
        # Specific turnstile iframe patterns
        'iframe[src*="/turnstile/"]',
        'iframe[title*="turnstile"]',
        'iframe[title*="cloudflare"]',
        'iframe[name*="cf-chl"]',
        
        # Generic iframe patterns for turnstile
        'iframe[src*="cf-chl"]',
        'iframe[src*="challenge-platform"]',
    ]
    
    # Script source patterns for turnstile loader
    SCRIPT_SELECTORS = [
        # Standard API script patterns
        'script[src*="challenges.cloudflare.com/turnstile"]',
        'script[src*="challenges.cloudflare.com/turnstile/v0/api.js"]',
        'script[src*="turnstile/v0/api.js"]',
        'script[src="https://challenges.cloudflare.com/turnstile/v0/api.js"]',
        
        # With callback patterns (explicit rendering)
        'script[src*="challenges.cloudflare.com/turnstile/v0/api.js?onload"]',
        'script[src*="onloadTurnstileCallback"]',
        
        # Generic patterns
        'script[src*="cf-turnstile"]',
        'script[src*="cloudflare"]',
    ]
    
    # Network request patterns
    NETWORK_PATTERNS = [
        'challenges.cloudflare.com/cdn-cgi/challenge-platform',
        'challenges.cloudflare.com/turnstile',
        'challenges.cloudflare.com/turnstile/v0',
        '/cdn-cgi/challenge-platform/h/g/turnstile/',
        '/turnstile/if/ov2/',
        'cf-chl-ctx',
    ]
    
    # JavaScript detection patterns
    JS_DETECTION_PATTERNS = {
        'turnstile_render': 'turnstile.render',
        'turnstile_object': 'window.turnstile',
        'cf_turnstile': 'cf-turnstile',
        'sitekey_attribute': 'data-sitekey',
        'challenge_callback': 'callback',
    }
    
    # Data attribute patterns
    DATA_ATTRIBUTES = [
        'data-sitekey',
        'data-theme',
        'data-callback',
        'data-error-callback',
        'data-expired-callback',
        'data-timeout-callback',
        'data-before-interactive-callback',
        'data-after-interactive-callback',
        'data-unsupported-callback',
        'data-size',
        'data-tabindex',
        'data-response-field',
        'data-response-field-name',
        'data-appearance',
        'data-execution',
        'data-refresh-expired',
        'data-retry',
        'data-retry-interval',
        'data-language',
    ]
    
    # Common sitekey patterns (for validation)
    SITEKEY_PATTERNS = [
        r'^0x[0-9A-Fa-f]+$',  # Standard format: 0x4AAAAAAAxxxxxxxxxxxxxx
        r'^1x[0-9A-Fa-f]+$',  # Alternative format
        r'^[0-9a-zA-Z_-]+$',  # Generic alphanumeric
    ]
    
    @classmethod
    def get_comprehensive_selectors(cls):
        """Get all selectors for comprehensive detection"""
        return {
            'containers': cls.CONTAINER_SELECTORS,
            'iframes': cls.IFRAME_SELECTORS,
            'scripts': cls.SCRIPT_SELECTORS,
            'data_attributes': cls.DATA_ATTRIBUTES,
        }
    
    @classmethod
    def get_fallback_detection_js(cls):
        """
        JavaScript code for fallback detection when standard selectors fail.
        This covers edge cases where containers are heavily obfuscated.
        """
        return """
        (() => {
            const detectionResults = {
                found: false,
                method: '',
                details: {},
                elements: [],
                confidence: 'low'
            };
            
            // Method 1: Check for data-sitekey anywhere in DOM (most reliable)
            const sitekeyElements = document.querySelectorAll('[data-sitekey]');
            if (sitekeyElements.length > 0) {
                detectionResults.found = true;
                detectionResults.method = 'data-sitekey';
                detectionResults.confidence = 'high';
                detectionResults.details.count = sitekeyElements.length;
                detectionResults.elements = Array.from(sitekeyElements).map(el => ({
                    tagName: el.tagName,
                    className: el.className,
                    sitekey: el.getAttribute('data-sitekey'),
                    theme: el.getAttribute('data-theme'),
                    callback: el.getAttribute('data-callback'),
                    selector: el.tagName.toLowerCase() + (el.className ? '.' + el.className.split(' ').join('.') : '')
                }));
                return detectionResults;
            }
            
            // Method 2: Check for cf-turnstile-response hidden inputs (proof of solved)
            const responseInputs = document.querySelectorAll('input[name="cf-turnstile-response"], input[id*="cf-chl-widget"]');
            if (responseInputs.length > 0) {
                detectionResults.found = true;
                detectionResults.method = 'response_token';
                detectionResults.confidence = 'high';
                detectionResults.details.count = responseInputs.length;
                detectionResults.elements = Array.from(responseInputs).map(input => ({
                    tagName: input.tagName,
                    name: input.name,
                    id: input.id,
                    value: input.value ? 'TOKEN_PRESENT' : 'NO_TOKEN',
                    hasValue: !!input.value
                }));
                return detectionResults;
            }
            
            // Method 3: Check for turnstile iframes (immutable)
            const turnstileIframes = document.querySelectorAll('iframe[src*="challenges.cloudflare.com"], iframe[src*="turnstile"]');
            if (turnstileIframes.length > 0) {
                detectionResults.found = true;
                detectionResults.method = 'iframe';
                detectionResults.confidence = 'high';
                detectionResults.details.count = turnstileIframes.length;
                detectionResults.elements = Array.from(turnstileIframes).map(iframe => ({
                    src: iframe.src,
                    title: iframe.title,
                    name: iframe.name,
                    visible: iframe.offsetParent !== null
                }));
                return detectionResults;
            }
            
            // Method 4: Check for turnstile scripts
            const turnstileScripts = document.querySelectorAll('script[src*="turnstile"], script[src*="challenges.cloudflare.com"]');
            if (turnstileScripts.length > 0) {
                detectionResults.found = true;
                detectionResults.method = 'script';
                detectionResults.confidence = 'medium';
                detectionResults.details.count = turnstileScripts.length;
                detectionResults.elements = Array.from(turnstileScripts).map(script => ({
                    src: script.src,
                    async: script.async,
                    defer: script.defer
                }));
                return detectionResults;
            }
            
            // Method 5: Check for turnstile JavaScript object and API
            if (typeof window.turnstile !== 'undefined') {
                detectionResults.found = true;
                detectionResults.method = 'javascript_api';
                detectionResults.confidence = 'high';
                detectionResults.details.turnstileObject = typeof window.turnstile;
                detectionResults.details.methods = Object.getOwnPropertyNames(window.turnstile || {});
                return detectionResults;
            }
            
            // Method 6: Check for onloadTurnstileCallback function
            if (typeof window.onloadTurnstileCallback !== 'undefined') {
                detectionResults.found = true;
                detectionResults.method = 'callback_function';
                detectionResults.confidence = 'medium';
                detectionResults.details.callbackType = typeof window.onloadTurnstileCallback;
                return detectionResults;
            }
            
            // Method 7: Search for turnstile-related text content and classes
            const bodyText = document.body.textContent || document.body.innerText || '';
            if (bodyText.includes('turnstile') || bodyText.includes('cf-turnstile')) {
                const cfElements = document.querySelectorAll('*[class*="turnstile"], *[id*="turnstile"]');
                if (cfElements.length > 0) {
                    detectionResults.found = true;
                    detectionResults.method = 'text_content';
                    detectionResults.confidence = 'low';
                    detectionResults.details.count = cfElements.length;
                    detectionResults.elements = Array.from(cfElements).map(el => ({
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id
                    }));
                    return detectionResults;
                }
            }
            
            // Method 8: Check for common cloudflare patterns in DOM
            const cfPatterns = ['cf-', 'cloudflare', 'challenge'];
            for (const pattern of cfPatterns) {
                const elements = document.querySelectorAll(`*[class*="${pattern}"], *[id*="${pattern}"]`);
                if (elements.length > 0) {
                    // Verify if any contain sitekey or turnstile-related attributes
                    for (const el of elements) {
                        if (el.hasAttribute('data-sitekey') || 
                            el.textContent.includes('turnstile') ||
                            el.innerHTML.includes('turnstile')) {
                            detectionResults.found = true;
                            detectionResults.method = 'pattern_match';
                            detectionResults.confidence = 'medium';
                            detectionResults.details.pattern = pattern;
                            detectionResults.elements = [{
                                tagName: el.tagName,
                                className: el.className,
                                id: el.id
                            }];
                            return detectionResults;
                        }
                    }
                }
            }
            
            return detectionResults;
        })()
        """
    
    @classmethod
    def get_network_detection_js(cls):
        """JavaScript to detect turnstile-related network requests"""
        return """
        (() => {
            const networkPatterns = [
                'challenges.cloudflare.com',
                'turnstile',
                'cf-chl-ctx',
                'challenge-platform'
            ];
            
            // Check for existing requests in performance API
            if (window.performance && window.performance.getEntriesByType) {
                const resources = window.performance.getEntriesByType('resource');
                const turnstileRequests = resources.filter(resource => 
                    networkPatterns.some(pattern => resource.name.includes(pattern))
                );
                
                if (turnstileRequests.length > 0) {
                    return {
                        found: true,
                        method: 'network_requests',
                        requests: turnstileRequests.map(req => ({
                            url: req.name,
                            type: req.initiatorType,
                            duration: req.duration
                        }))
                    };
                }
            }
            
            return { found: false };
        })()
        """

class TurnstileValidator:
    """Validate detected turnstile elements and extract metadata"""
    
    @staticmethod
    def validate_sitekey(sitekey):
        """Validate if a sitekey looks like a valid Turnstile sitekey"""
        if not sitekey:
            return False
        
        import re
        for pattern in TurnstilePatterns.SITEKEY_PATTERNS:
            if re.match(pattern, sitekey):
                return True
        return False
    
    @staticmethod
    def extract_turnstile_config(element_data):
        """Extract Turnstile configuration from detected element"""
        config = {}
        
        if 'sitekey' in element_data:
            config['sitekey'] = element_data['sitekey']
        
        # Extract other data attributes
        for attr in TurnstilePatterns.DATA_ATTRIBUTES:
            attr_key = attr.replace('data-', '')
            if attr_key in element_data:
                config[attr_key] = element_data[attr_key]
        
        return config