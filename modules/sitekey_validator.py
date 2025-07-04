#!/usr/bin/python3

"""
Sitekey Validation Module
Navina Inc (c) 2025. All rights reserved.

Comprehensive validation for Cloudflare Turnstile sitekeys
Detects demo keys, fake keys, and validates real sitekey formats
"""

import re
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Optional


class SitekeyValidator:
    """Comprehensive Turnstile sitekey validator"""
    
    # Known demo/test sitekeys from Cloudflare
    DEMO_SITEKEYS = {
        '1x00000000000000000000AA': 'Demo - Always passes (visible)',
        '2x00000000000000000000AB': 'Demo - Always blocks',  
        '3x00000000000000000000FF': 'Demo - Always passes (invisible)'
    }
    
    # Known invalid string patterns
    INVALID_PATTERNS = [
        '0x4AAAAAAA', 'YOUR_SITE_KEY', 'PLACEHOLDER', 'EXAMPLE', 'TEST_KEY',
        'DEMO', 'FAKE', 'NULL', 'UNDEFINED'
    ]
    
    # Regex patterns for obviously invalid sitekeys
    INVALID_REGEX_PATTERNS = [
        # All zeros or mostly zeros
        (r'^[01]x0{20,}[0-9A-Fa-f]*$', 'Contains too many zeros (likely placeholder)'),
        (r'^[01]x[0-9A-Fa-f]*0{20,}$', 'Ends with too many zeros (likely placeholder)'),
        
        # Repeating patterns
        (r'^[01]x([0-9A-Fa-f])\1{25,}$', 'Contains repeating single character (likely test key)'),
        (r'^[01]x([0-9A-Fa-f]{2})\1{12,}$', 'Contains repeating 2-char pattern (likely test key)'),
        (r'^[01]x([0-9A-Fa-f]{4})\1{6,}$', 'Contains repeating 4-char pattern (likely test key)'),
        
        # Sequential patterns
        (r'^[01]x(0123456789ABCDEF){2,}$', 'Contains sequential hex pattern (likely test key)'),
        (r'^[01]x(FEDCBA9876543210){2,}$', 'Contains reverse sequential pattern (likely test key)'),
        (r'^[01]x123456789ABCDEF.*$', 'Starts with sequential pattern (likely test key)'),
        
        # Common test patterns
        (r'^[01]x[Ff]{20,}$', 'Contains all F characters (likely placeholder)'),
        (r'^[01]x[Aa]{20,}$', 'Contains all A characters (likely placeholder)'),
        (r'^[01]x[0-9]{20,}$', 'Contains only numbers (invalid hex format)'),
        
        # Common hex test words
        (r'^[01]x.*(DEAD|BEEF|CAFE|FACE|BABE|FADE){4,}.*$', 'Contains common hex test words'),
        
        # Obviously fake patterns
        (r'^[01]x.*(TEST|FAKE|DEMO|EXAMPLE|PLACEHOLDER).*$', 'Contains test/fake keywords'),
        (r'^[01]x4[Aa]{6,}.*$', 'Starts with 4AAA... (common placeholder pattern)'),
        
        # Suspicious patterns
        (r'^[01]x([0-9A-Fa-f]{1,3})\1{8,}$', 'Contains short repeating pattern'),
        (r'^[01]x(12|AB|CD|EF){10,}$', 'Contains obvious test sequences'),
    ]
    
    @classmethod
    def validate_sitekey(cls, sitekey: str, url: str = None) -> Dict[str, any]:
        """
        Comprehensive sitekey validation
        
        Args:
            sitekey: The sitekey to validate
            url: Optional URL where sitekey was found (for context)
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': False,
            'is_demo': False,
            'is_fake': False,
            'type': 'unknown',
            'confidence': 0,
            'warnings': [],
            'notes': [],
            'domain': None
        }
        
        if url:
            parsed_url = urlparse(url)
            result['domain'] = parsed_url.netloc
        
        # 1. Check if it's a known demo key
        if sitekey in cls.DEMO_SITEKEYS:
            result.update({
                'is_demo': True,
                'type': 'demo',
                'confidence': 100,
                'description': cls.DEMO_SITEKEYS[sitekey],
                'warnings': ['Demo keys only work on specific domains', 
                            'Not suitable for real solving'],
                'notes': ['Use for testing Turnstile integration only']
            })
            return result
        
        # 2. Check for obvious fake/placeholder patterns
        sitekey_upper = sitekey.upper()
        for pattern in cls.INVALID_PATTERNS:
            if pattern in sitekey_upper:
                result.update({
                    'is_fake': True,
                    'type': 'fake',
                    'confidence': 95,
                    'reason': f'Contains placeholder text: {pattern}',
                    'warnings': ['This is clearly a placeholder/fake sitekey'],
                    'notes': ['Extract from a real Turnstile-protected website']
                })
                return result
        
        # 3. Check regex patterns for invalid sitekeys
        for pattern, reason in cls.INVALID_REGEX_PATTERNS:
            if re.match(pattern, sitekey, re.IGNORECASE):
                result.update({
                    'is_fake': True,
                    'type': 'fake',
                    'confidence': 90,
                    'reason': reason,
                    'warnings': ['Pattern suggests fake/test sitekey'],
                    'notes': ['Real sitekeys have random-looking hex characters']
                })
                return result
        
        # 4. Basic format validation
        if not (len(sitekey) >= 20 and sitekey.startswith(('1x', '0x'))):
            result.update({
                'is_fake': True,
                'type': 'invalid_format',
                'confidence': 100,
                'reason': 'Invalid format - must start with 1x/0x and be 20+ chars',
                'warnings': ['Does not match Turnstile sitekey format'],
                'notes': ['Real Turnstile sitekeys start with "1x" or "0x"']
            })
            return result
        
        # 5. Advanced format validation for real sitekeys
        if len(sitekey) == 32 and (sitekey.startswith('1x') or sitekey.startswith('0x')):
            hex_part = sitekey[2:]
            try:
                # Verify it's valid hex
                int(hex_part, 16)
                
                # Check for randomness (basic entropy check)
                entropy_score = cls._calculate_entropy(hex_part)
                
                result.update({
                    'is_valid': True,
                    'type': 'production' if sitekey.startswith('1x') else 'development',
                    'confidence': min(50 + int(entropy_score * 50), 95),
                    'entropy_score': entropy_score,
                    'notes': [
                        f'Valid {result["type"]} sitekey format',
                        'Sitekeys are domain-restricted by Cloudflare',
                        'Test by using with local server'
                    ]
                })
                
                if entropy_score < 0.5:
                    result['warnings'].append('Low entropy - may be a test pattern')
                    result['confidence'] -= 20
                
                return result
                
            except ValueError:
                result.update({
                    'is_fake': True,
                    'type': 'invalid_hex',
                    'confidence': 95,
                    'reason': 'Contains non-hex characters after prefix',
                    'warnings': ['Invalid hex encoding'],
                    'notes': ['Real sitekeys are hex-encoded after the prefix']
                })
                return result
        else:
            # Unusual length but valid prefix
            result.update({
                'is_valid': True,
                'type': 'unusual_format',
                'confidence': 30,
                'reason': f'Unusual length: {len(sitekey)} chars (expected 32)',
                'warnings': ['Non-standard length for Turnstile sitekey'],
                'notes': ['May be valid but unusual format']
            })
            return result
    
    @staticmethod
    def _calculate_entropy(hex_string: str) -> float:
        """Calculate basic entropy score for hex string (0.0 to 1.0)"""
        if not hex_string:
            return 0.0
        
        # Count character frequencies
        char_counts = {}
        for char in hex_string.upper():
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        length = len(hex_string)
        entropy = 0.0
        for count in char_counts.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)
        
        # Normalize to 0-1 scale (max entropy for hex is log2(16) = 4)
        max_entropy = 4.0
        return min(entropy / max_entropy, 1.0)
    
    @classmethod
    def print_validation_result(cls, sitekey: str, result: Dict[str, any]):
        """Print formatted validation results"""
        print(f"    Validating sitekey...")
        
        if result['is_demo']:
            print(f"     DEMO SITEKEY: {result['description']}")
            for warning in result['warnings']:
                print(f"    {warning}")
            for note in result['notes']:
                print(f"    {note}")
        
        elif result['is_fake']:
            print(f"    INVALID: {result['reason']}")
            for warning in result['warnings']:
                print(f"     {warning}")
            for note in result['notes']:
                print(f"    {note}")
        
        elif result['is_valid']:
            print(f"    VALID FORMAT: {result['type'].title()} sitekey")
            if 'confidence' in result:
                print(f"    Confidence: {result['confidence']}%")
            if 'entropy_score' in result:
                print(f"    Entropy: {result['entropy_score']:.2f}")
            if result.get('domain'):
                print(f"    Domain: {result['domain']}")
            
            for warning in result.get('warnings', []):
                print(f"     {warning}")
            for note in result.get('notes', []):
                print(f"    {note}")
        
        else:
            print(f"     UNKNOWN: Could not determine sitekey validity")


# Convenience function for direct usage
async def validate_sitekey(sitekey: str, url: str = None):
    """Async wrapper for sitekey validation (for compatibility)"""
    result = SitekeyValidator.validate_sitekey(sitekey, url)
    SitekeyValidator.print_validation_result(sitekey, result)
    
    # Generate local server URL for valid sitekeys
    if result['is_valid'] and not result['is_demo'] and url:
        print(f"    Local server URL: http://localhost:8888/solve?sitekey={sitekey}&url={url}")
    
    return result