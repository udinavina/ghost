#!/usr/bin/python3

"""
Example usage of YARA-based Turnstile detection
Navina Inc (c) 2025. All rights reserved.
"""

from modules.yara_turnstile_detector import (
    scan_for_turnstile_yara,
    extract_sitekeys_yara,
    validate_sitekey_yara,
    get_yara_detection_summary,
    get_module_info
)

def main():
    """Demonstrate YARA-based Turnstile detection capabilities"""
    
    print(" YARA Turnstile Detection Example")
    print("=" * 50)
    
    # Display module info
    info = get_module_info()
    print(f"Module: {info['name']} v{info['version']}")
    print(f"YARA Available: {info['yara_available']}")
    print(f"Rules Loaded: {info['rules_loaded']}")
    print(f"Rules Source: {info['rules_source']}")
    print()
    
    # Example HTML content with different Turnstile implementations
    test_cases = [
        {
            'name': 'Standard Turnstile with Demo Sitekey',
            'content': '''
            <div class="cf-turnstile" data-sitekey="1x00000000000000000000AA" data-theme="light"></div>
            <script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
            '''
        },
        {
            'name': 'Invisible Turnstile',
            'content': '''
            <div class="cf-turnstile" data-sitekey="3x00000000000000000000FF" data-size="invisible"></div>
            '''
        },
        {
            'name': 'JavaScript Configuration',
            'content': '''
            <script>
            window.turnstile.render('#captcha', {
                sitekey: '1xABCDEF1234567890ABCDEF1234567890',
                callback: function(token) { console.log(token); }
            });
            </script>
            '''
        },
        {
            'name': 'Fake/Placeholder Sitekey',
            'content': '''
            <div class="cf-turnstile" data-sitekey="0x4AAAAAAA" data-theme="dark"></div>
            '''
        },
        {
            'name': 'No Turnstile Content',
            'content': '''
            <div class="regular-form">
                <input type="text" name="username">
                <input type="password" name="password">
                <button type="submit">Login</button>
            </div>
            '''
        }
    ]
    
    # Process each test case
    for i, test_case in enumerate(test_cases, 1):
        print(f" Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        content = test_case['content']
        
        # Full YARA scan
        result = scan_for_turnstile_yara(content)
        print(f"Detection: {' Found' if result['has_turnstile'] else ' Not found'}")
        
        if result['has_turnstile']:
            print(f"Confidence: {result['confidence_score']}%")
            print(f"Total Matches: {result['total_matches']}")
            print(f"Categories: {', '.join(result['categories'])}")
            
            # Extract sitekeys
            sitekeys = extract_sitekeys_yara(content)
            if sitekeys:
                print(f"Sitekeys Found: {sitekeys}")
                
                # Validate first sitekey
                for sitekey in sitekeys:
                    validation = validate_sitekey_yara(sitekey)
                    validity = " Valid" if validation['valid'] else " Invalid" if validation['valid'] is False else " Unknown"
                    print(f"Sitekey '{sitekey}': {validity}")
                    print(f"  Reason: {validation['reason']}")
            else:
                print("Sitekeys Found: None")
            
            # Get detailed summary
            summary = get_yara_detection_summary(content)
            print(f"Summary:\n{summary}")
        
        print()
    
    print(" Example completed!")
    print("\n Usage Tips:")
    print("- Use scan_for_turnstile_yara() for comprehensive detection")
    print("- Use extract_sitekeys_yara() for quick sitekey extraction")
    print("- Use validate_sitekey_yara() to check if sitekeys are fake/demo")
    print("- Check confidence scores to assess detection reliability")
    print("- Multiple categories indicate different aspects detected")

if __name__ == "__main__":
    main()