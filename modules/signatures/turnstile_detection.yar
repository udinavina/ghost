/*
 * Cloudflare Turnstile Detection Rules
 * Navina Inc (c) 2025. All rights reserved.
 * 
 * Comprehensive YARA rules for detecting Turnstile implementations
 * Replaces regex-based detection for better accuracy and extensibility
 */

rule CloudflareTurnstile_Standard {
    meta:
        description = "Detects standard Cloudflare Turnstile implementation"
        category = "captcha"
        confidence = "high"
        
    strings:
        $cf_class = "cf-turnstile" nocase
        $sitekey_attr = "data-sitekey" nocase
        $turnstile_script = "challenges.cloudflare.com/turnstile" nocase
        $turnstile_api = "turnstile/v0/api.js" nocase
        $response_field = "cf-turnstile-response" nocase
        
    condition:
        ($cf_class and $sitekey_attr) or
        ($turnstile_script and $sitekey_attr) or
        ($turnstile_api and $cf_class) or
        $response_field
}

rule CloudflareTurnstile_Sitekey {
    meta:
        description = "Detects Turnstile sitekeys in various formats"
        category = "captcha_sitekey"
        confidence = "high"
        
    strings:
        // Standard sitekey patterns (1x or 0x followed by 30 hex chars)
        $sitekey_1x = /data-sitekey=['"]1x[0-9A-Fa-f]{30}['"]/ nocase
        $sitekey_0x = /data-sitekey=['"]0x[0-9A-Fa-f]{30}['"]/ nocase
        $sitekey_3x = /data-sitekey=['"]3x[0-9A-Fa-f]{30}['"]/ nocase
        
        // JavaScript sitekey assignments
        $js_sitekey_1x = /sitekey['":\s]*['"]1x[0-9A-Fa-f]{30}['"]/ nocase
        $js_sitekey_0x = /sitekey['":\s]*['"]0x[0-9A-Fa-f]{30}['"]/ nocase
        $js_sitekey_3x = /sitekey['":\s]*['"]3x[0-9A-Fa-f]{30}['"]/ nocase
        
        // Demo/test sitekeys
        $demo_visible = "1x00000000000000000000AA" nocase
        $demo_block = "2x00000000000000000000AB" nocase  
        $demo_invisible = "3x00000000000000000000FF" nocase
        
    condition:
        any of ($sitekey_*, $js_sitekey_*, $demo_*)
}

rule CloudflareTurnstile_Advanced {
    meta:
        description = "Detects advanced/obfuscated Turnstile implementations"
        category = "captcha_advanced"
        confidence = "medium"
        
    strings:
        // Obfuscated class names
        $obf_class1 = /class=['"][^'"]*turnstile[^'"]*['"]/ nocase
        $obf_class2 = /class=['"][^'"]*cf-[^'"]*['"]/ nocase
        
        // JavaScript API calls
        $js_render = "turnstile.render" nocase
        $js_reset = "turnstile.reset" nocase
        $js_response = "turnstile.getResponse" nocase
        $js_remove = "turnstile.remove" nocase
        
        // Callback functions
        $callback = "data-callback" nocase
        $error_callback = "data-error-callback" nocase
        $expired_callback = "data-expired-callback" nocase
        
        // Widget configuration
        $theme_attr = "data-theme" nocase
        $size_attr = "data-size" nocase
        $action_attr = "data-action" nocase
        $cdata_attr = "data-cdata" nocase
        
    condition:
        ($obf_class1 or $obf_class2) or
        ($js_render or $js_reset or $js_response or $js_remove) or
        ($callback or $error_callback or $expired_callback) or
        ($theme_attr or $size_attr or $action_attr or $cdata_attr)
}

rule CloudflareTurnstile_FakeSitekeys {
    meta:
        description = "Detects fake/placeholder Turnstile sitekeys"
        category = "captcha_fake"
        confidence = "high"
        
    strings:
        // Common placeholder patterns
        $fake_4a = /['"]0x4[Aa]{6,}/ nocase
        $fake_placeholder = "YOUR_SITE_KEY" nocase
        $fake_example = "EXAMPLE_SITEKEY" nocase
        $fake_test = "TEST_SITEKEY" nocase
        
        // Repeating patterns
        $repeat_zeros = /['"]1x0{20,}/ nocase
        $repeat_a = /['"]1x[Aa]{20,}/ nocase
        $repeat_f = /['"]1x[Ff]{20,}/ nocase
        
        // Sequential patterns
        $sequential = /['"]1x123456789ABCDEF/ nocase
        
        // Common hex words
        $hex_words = /['"]1x.*(DEAD|BEEF|CAFE|FACE|BABE){4,}/ nocase
        
    condition:
        any of them
}

rule CloudflareTurnstile_IframeChallenge {
    meta:
        description = "Detects Turnstile iframe-based challenges"
        category = "captcha_iframe"
        confidence = "medium"
        
    strings:
        $iframe_src = "challenges.cloudflare.com" nocase
        $iframe_turnstile = /iframe[^>]*turnstile/ nocase
        $iframe_chl = "cf-chl-widget" nocase
        $chl_script = "cf-chl-" nocase
        
    condition:
        ($iframe_src and ($iframe_turnstile or $iframe_chl)) or
        $chl_script
}

rule CloudflareTurnstile_NetworkRequests {
    meta:
        description = "Detects Turnstile-related network patterns"
        category = "captcha_network"
        confidence = "low"
        
    strings:
        // API endpoints
        $api_endpoint = "challenges.cloudflare.com/turnstile/v0" nocase
        $cdn_endpoint = "challenges.cloudflare.com/cdn-cgi" nocase
        
        // Response validation
        $validation_url = "/turnstile/v0/siteverify" nocase
        
        // Resource loading
        $resource_js = "turnstile/v0/api.js" nocase
        $resource_css = "turnstile/v0/api.css" nocase
        
    condition:
        any of them
}

rule CloudflareTurnstile_ResponseFields {
    meta:
        description = "Detects Turnstile response/token fields"
        category = "captcha_response"
        confidence = "high"
        
    strings:
        // Response field patterns
        $response_input = /input[^>]*name=['"]cf-turnstile-response['"]/ nocase
        $response_field = "cf-turnstile-response" nocase
        $token_field = /input[^>]*turnstile[^>]*token/ nocase
        
        // Token validation patterns
        $token_pattern = /[0-9A-Za-z_-]{100,}/ // Typical token length
        
    condition:
        any of ($response_*, $token_*)
}

rule CloudflareTurnstile_ConfigPatterns {
    meta:
        description = "Detects Turnstile configuration patterns"
        category = "captcha_config"
        confidence = "medium"
        
    strings:
        // Configuration objects
        $config_obj = /turnstile['":\s]*{[^}]*sitekey/ nocase
        $window_turnstile = "window.turnstile" nocase
        
        // Common config properties
        $sitekey_prop = /"sitekey"['":\s]*['"][0-9A-Fa-f]{20,}['"]/ nocase
        $action_prop = /"action"['":\s]*['"][^'"]+['"]/ nocase
        $theme_light = /"theme"['":\s]*['"]light['"]/ nocase
        $theme_dark = /"theme"['":\s]*['"]dark['"]/ nocase
        $theme_auto = /"theme"['":\s]*['"]auto['"]/ nocase
        $size_normal = /"size"['":\s]*['"]normal['"]/ nocase
        $size_compact = /"size"['":\s]*['"]compact['"]/ nocase
        $size_invisible = /"size"['":\s]*['"]invisible['"]/ nocase
        
    condition:
        ($config_obj or $window_turnstile) or
        ($sitekey_prop or $action_prop) or
        ($theme_light or $theme_dark or $theme_auto) or
        ($size_normal or $size_compact or $size_invisible)
}

rule CloudflareTurnstile_LegacyPatterns {
    meta:
        description = "Detects legacy or uncommon Turnstile patterns"
        category = "captcha_legacy"
        confidence = "low"
        
    strings:
        // Old CF challenge patterns
        $cf_challenge = "cf-challenge" nocase
        $cf_chl = "cf-chl-" nocase
        
        // Alternative implementations
        $cloudflare_challenge = "cloudflare-challenge" nocase
        $challenge_form = /form[^>]*challenge/ nocase
        
    condition:
        any of them
}