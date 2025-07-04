# YARA Signatures Directory

This directory contains YARA rule files for detecting various patterns in web content.

## Files

### `turnstile_detection.yar`
Comprehensive YARA rules for detecting Cloudflare Turnstile CAPTCHA implementations.

**Features:**
- 10 comprehensive detection rules
- Multiple confidence levels (high, medium, low)
- Categorized patterns (captcha, sitekey, advanced, fake, iframe, network, response, config, legacy)
- Detects standard, obfuscated, and fake implementations
- Validates sitekey formats and identifies demo/test keys

**Rules:**
1. `CloudflareTurnstile_Standard` - Standard implementations
2. `CloudflareTurnstile_Sitekey` - Sitekey detection in various formats
3. `CloudflareTurnstile_Advanced` - Advanced/obfuscated implementations
4. `CloudflareTurnstile_FakeSitekeys` - Fake/placeholder sitekeys
5. `CloudflareTurnstile_IframeChallenge` - Iframe-based challenges
6. `CloudflareTurnstile_NetworkRequests` - Network patterns
7. `CloudflareTurnstile_ResponseFields` - Response/token fields
8. `CloudflareTurnstile_ConfigPatterns` - Configuration patterns
9. `CloudflareTurnstile_LegacyPatterns` - Legacy/uncommon patterns

## Usage

The YARA rules are automatically loaded by the `yara_turnstile_detector.py` module.

```python
from modules.yara_turnstile_detector import scan_for_turnstile_yara, extract_sitekeys_yara

# Detect Turnstile in content
result = scan_for_turnstile_yara(html_content)
print(f"Found Turnstile: {result['has_turnstile']}")
print(f"Confidence: {result['confidence_score']}%")

# Extract sitekeys
sitekeys = extract_sitekeys_yara(html_content)
print(f"Sitekeys: {sitekeys}")
```

## Manual Compilation

To test the rules manually:

```bash
python3 -c "import yara; rules = yara.compile(filepath='turnstile_detection.yar'); print('Rules compiled successfully')"
```

---
*Navina Inc (c) 2025. All rights reserved.*