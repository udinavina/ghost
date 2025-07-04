#!/usr/bin/python3

"""
YARA-based Turnstile Detection Module
Navina Inc (c) 2025. All rights reserved.

Uses YARA rules to detect Cloudflare Turnstile implementations
More robust and extensible than regex-based detection
"""

import os
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False


class YaraTurnstileDetector:
    """YARA-based Turnstile detection engine"""
    
    def __init__(self):
        self.rules = None
        self.rules_loaded = False
        self.rules_source = None
        
        if not YARA_AVAILABLE:
            print("  YARA not available. Install with: pip install yara-python")
            return
        
        try:
            self._load_rules()
        except Exception as e:
            print(f"  Failed to load YARA rules: {e}")
    
    def _get_rules_file_path(self) -> Optional[str]:
        """Get path to the external YARA rules file"""
        # Look for rules file in signatures directory (preferred location)
        current_dir = Path(__file__).parent
        signatures_dir = current_dir / "signatures"
        rules_file = signatures_dir / "turnstile_detection.yar"
        
        if rules_file.exists():
            return str(rules_file)
        
        # Fallback: look in parent directory (old location)
        parent_rules = current_dir.parent / "turnstile_detection.yar"
        if parent_rules.exists():
            return str(parent_rules)
        
        # Fallback: look in current working directory
        cwd_rules = Path.cwd() / "turnstile_detection.yar"
        if cwd_rules.exists():
            return str(cwd_rules)
        
        # If no external file found, return None to use embedded fallback
        return None
    
    def _get_fallback_rules(self) -> str:
        """Fallback embedded YARA rules if external file not found"""
        return """
rule CloudflareTurnstile_Basic {
    meta:
        description = "Basic Cloudflare Turnstile detection (fallback)"
        category = "captcha"
        confidence = "medium"
        
    strings:
        $cf_class = "cf-turnstile" nocase
        $sitekey_attr = "data-sitekey" nocase
        $turnstile_script = "challenges.cloudflare.com/turnstile" nocase
        
    condition:
        ($cf_class and $sitekey_attr) or $turnstile_script
}

rule CloudflareTurnstile_Sitekey_Basic {
    meta:
        description = "Basic sitekey detection (fallback)"
        category = "captcha_sitekey"
        confidence = "medium"
        
    strings:
        $sitekey_1x = /data-sitekey=['"]1x[0-9A-Fa-f]{30}['"]/ nocase
        $sitekey_0x = /data-sitekey=['"]0x[0-9A-Fa-f]{30}['"]/ nocase
        $demo_visible = "1x00000000000000000000AA" nocase
        $demo_invisible = "3x00000000000000000000FF" nocase
        
    condition:
        any of them
}
"""
    
    def _load_rules(self):
        """Load YARA rules for Turnstile detection"""
        if not YARA_AVAILABLE:
            return
            
        try:
            # First try to load from external file
            rules_file_path = self._get_rules_file_path()
            
            if rules_file_path:
                print(f"  Loading YARA rules from: {rules_file_path}")
                # Load directly from external file
                self.rules = yara.compile(filepath=rules_file_path)
                self.rules_loaded = True
                self.rules_source = "external_file"
                print(f"  Successfully loaded YARA rules from external file")
            else:
                print("  External YARA rules file not found, using embedded fallback rules")
                # Use embedded fallback rules
                rules_string = self._get_fallback_rules()
                
                # Create temporary file for fallback rules
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yar', delete=False) as f:
                    f.write(rules_string)
                    temp_rules_path = f.name
                
                # Compile rules
                self.rules = yara.compile(filepath=temp_rules_path)
                self.rules_loaded = True
                self.rules_source = "embedded_fallback"
                
                # Clean up temp file
                os.unlink(temp_rules_path)
                print(f"  Successfully loaded fallback YARA rules")
            
        except Exception as e:
            print(f"  Failed to compile YARA rules: {e}")
            self.rules_loaded = False
    
    def scan_content(self, content: str) -> Dict[str, Any]:
        """
        Scan content for Turnstile patterns using YARA rules
        
        Args:
            content: HTML/JavaScript content to scan
            
        Returns:
            Detection results dictionary
        """
        if not self.rules_loaded or not self.rules:
            return {
                'yara_available': False,
                'error': 'YARA rules not loaded',
                'detections': []
            }
        
        try:
            # Scan content with YARA rules
            matches = self.rules.match(data=content.encode('utf-8', errors='ignore'))
            
            detections = []
            sitekeys = set()
            confidence_total = 0
            
            for match in matches:
                detection = {
                    'rule': match.rule,
                    'category': match.meta.get('category', 'unknown'),
                    'description': match.meta.get('description', ''),
                    'confidence': match.meta.get('confidence', 'unknown'),
                    'strings': []
                }
                
                # Extract matched strings and their positions
                for string_match in match.strings:
                    matched_data = {
                        'identifier': string_match.identifier,
                        'offset': string_match.instances[0].offset if string_match.instances else 0,
                        'matched_data': string_match.instances[0].matched_data.decode('utf-8', errors='ignore') if string_match.instances else '',
                        'length': string_match.instances[0].matched_length if string_match.instances else 0
                    }
                    detection['strings'].append(matched_data)
                    
                    # Extract sitekeys from matches
                    matched_text = matched_data['matched_data']
                    
                    # Check if this is a direct sitekey match
                    if any(x in string_match.identifier.lower() for x in ['sitekey', 'demo_', 'js_sitekey']):
                        # Direct sitekey pattern matches
                        import re
                        
                        # If it's a demo key match, use the matched text directly
                        if 'demo_' in string_match.identifier.lower():
                            if re.match(r'^[0-3]x[0-9A-Fa-f]{20,30}$', matched_text, re.IGNORECASE):
                                sitekeys.add(matched_text)
                        else:
                            # Extract from attribute patterns
                            sitekey_patterns = [
                                r'data-sitekey=[\'"]([01x3][x0-9A-Fa-f]{20,})[\'"]',
                                r'sitekey[\'"\s:=]+[\'"]([01x3][x0-9A-Fa-f]{20,})[\'"]',
                                r'[\'"]([01x3][x0-9A-Fa-f]{30,})[\'"]'
                            ]
                            
                            for pattern in sitekey_patterns:
                                found_keys = re.findall(pattern, matched_text, re.IGNORECASE)
                                for key in found_keys:
                                    if len(key) >= 20:  # Minimum sitekey length
                                        sitekeys.add(key)
                
                detections.append(detection)
                
                # Calculate confidence score
                conf_map = {'high': 3, 'medium': 2, 'low': 1}
                confidence_total += conf_map.get(detection['confidence'], 1)
            
            # Determine overall confidence
            overall_confidence = min(confidence_total * 10, 100) if detections else 0
            
            return {
                'yara_available': True,
                'detections': detections,
                'sitekeys_found': list(sitekeys),
                'total_matches': len(matches),
                'confidence_score': overall_confidence,
                'has_turnstile': len(detections) > 0,
                'categories': list(set(d['category'] for d in detections)),
                'rules_source': self.rules_source
            }
            
        except Exception as e:
            return {
                'yara_available': True,
                'error': f'YARA scan failed: {str(e)}',
                'detections': []
            }
    
    def extract_sitekeys_advanced(self, content: str) -> List[str]:
        """Extract sitekeys using YARA rules (more comprehensive than regex)"""
        if not self.rules_loaded:
            return []
        
        result = self.scan_content(content)
        return result.get('sitekeys_found', [])
    
    def is_turnstile_present(self, content: str) -> bool:
        """Check if Turnstile is present in content"""
        if not self.rules_loaded:
            return False
        
        result = self.scan_content(content)
        return result.get('has_turnstile', False)
    
    def get_detection_summary(self, content: str) -> str:
        """Get human-readable detection summary"""
        if not self.rules_loaded:
            return "  YARA not available for advanced detection"
        
        result = self.scan_content(content)
        
        if result.get('error'):
            return f"  YARA scan error: {result['error']}"
        
        if not result.get('has_turnstile'):
            return "  No Turnstile patterns detected by YARA"
        
        summary_lines = [
            f"  YARA detected {result['total_matches']} Turnstile pattern(s)",
            f"  Confidence: {result['confidence_score']}%",
            f"  Categories: {', '.join(result['categories'])}"
        ]
        
        if result.get('rules_source'):
            source_desc = "external file" if result['rules_source'] == "external_file" else "fallback rules"
            summary_lines.append(f"  Rules source: {source_desc}")
        
        if result.get('sitekeys_found'):
            summary_lines.append(f"  Sitekeys: {', '.join(result['sitekeys_found'][:3])}{'...' if len(result['sitekeys_found']) > 3 else ''}")
        
        return '\n   '.join(summary_lines)
    
    def validate_sitekey_with_yara(self, sitekey: str, content: str = None) -> Dict[str, Any]:
        """
        Validate a sitekey using YARA rules to detect if it's fake/demo
        
        Args:
            sitekey: The sitekey to validate
            content: Optional content context for validation
            
        Returns:
            Validation results dictionary
        """
        if not self.rules_loaded:
            return {'valid': None, 'reason': 'YARA not available'}
        
        # Create test content with the sitekey
        test_content = f'<div class="cf-turnstile" data-sitekey="{sitekey}"></div>'
        if content:
            test_content = content
        
        result = self.scan_content(test_content)
        
        # Check if fake sitekey rules matched
        fake_categories = [d['category'] for d in result.get('detections', []) if d['category'] == 'captcha_fake']
        
        if fake_categories:
            return {
                'valid': False,
                'reason': 'YARA detected fake/placeholder sitekey pattern',
                'yara_categories': result.get('categories', [])
            }
        elif result.get('has_turnstile'):
            return {
                'valid': True,
                'reason': 'YARA detected valid Turnstile pattern',
                'yara_categories': result.get('categories', [])
            }
        else:
            return {
                'valid': None,
                'reason': 'No Turnstile patterns detected',
                'yara_categories': []
            }


# Global detector instance
_detector = None

def get_yara_detector() -> YaraTurnstileDetector:
    """Get or create global YARA detector instance"""
    global _detector
    if _detector is None:
        _detector = YaraTurnstileDetector()
    return _detector

def scan_for_turnstile_yara(content: str) -> Dict[str, Any]:
    """Convenience function for YARA-based Turnstile detection"""
    detector = get_yara_detector()
    return detector.scan_content(content)

def extract_sitekeys_yara(content: str) -> List[str]:
    """Extract sitekeys using YARA rules"""
    detector = get_yara_detector()
    return detector.extract_sitekeys_advanced(content)

def is_turnstile_present_yara(content: str) -> bool:
    """Check if Turnstile is present using YARA rules"""
    detector = get_yara_detector()
    return detector.is_turnstile_present(content)

def validate_sitekey_yara(sitekey: str, content: str = None) -> Dict[str, Any]:
    """Validate sitekey using YARA rules"""
    detector = get_yara_detector()
    return detector.validate_sitekey_with_yara(sitekey, content)

def get_yara_detection_summary(content: str) -> str:
    """Get human-readable YARA detection summary"""
    detector = get_yara_detector()
    return detector.get_detection_summary(content)


# Module information and testing
def get_module_info() -> Dict[str, Any]:
    """Get information about this YARA detection module"""
    detector = get_yara_detector()
    return {
        'name': 'YARA Turnstile Detector',
        'version': '2.0.0',
        'yara_available': YARA_AVAILABLE,
        'rules_loaded': detector.rules_loaded if detector else False,
        'rules_source': detector.rules_source if detector else None,
        'description': 'Advanced Turnstile detection using YARA pattern matching'
    }

def test_yara_detection():
    """Test function to verify YARA detection is working"""
    test_content = '''
    <div class="cf-turnstile" data-sitekey="1x00000000000000000000AA" data-theme="light"></div>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
    '''
    
    print(" Testing YARA Turnstile Detection...")
    
    # Test detection
    result = scan_for_turnstile_yara(test_content)
    print(f" Detection result: {result['has_turnstile']}")
    print(f"   Confidence: {result['confidence_score']}%")
    print(f"   Matches: {result['total_matches']}")
    
    # Test sitekey extraction
    sitekeys = extract_sitekeys_yara(test_content)
    print(f" Extracted sitekeys: {sitekeys}")
    
    # Test validation
    if sitekeys:
        validation = validate_sitekey_yara(sitekeys[0])
        print(f" Sitekey validation: {validation}")
    
    return result


if __name__ == "__main__":
    # Run tests if module is executed directly
    info = get_module_info()
    print(" YARA Turnstile Detector Info:")
    for key, value in info.items():
        print(f"   {key}: {value}")
    print()
    
    if info['yara_available']:
        test_yara_detection()
    else:
        print(" YARA not available. Install with: pip install yara-python")