#!/usr/bin/python3

"""
Enhanced Stealth Module for Browser Automation
Navina Inc (c) 2025. All rights reserved.

Implements advanced anti-detection techniques to bypass bot detection systems.
Based on analysis of CloudFlyer and current detection failures.
"""

import json
import random
from typing import Dict, List, Optional, Any
from pathlib import Path

class EnhancedStealth:
    """Advanced stealth techniques for browser automation"""
    
    @staticmethod
    def get_enhanced_chrome_args() -> List[str]:
        """Get enhanced Chrome arguments for better stealth"""
        return [
            # Core stealth arguments
            '--disable-blink-features=AutomationControlled',
            '--exclude-switches=enable-automation',
            '--disable-dev-shm-usage',
            
            # Additional stealth arguments
            '--disable-automation',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=BlockInsecurePrivateNetworkRequests',
            '--disable-features=ImprovedCookieControls',
            
            # Performance and detection bypass  
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-dev-shm-usage',
            '--disable-gpu-sandbox',
            # Note: removed --disable-gpu to enable WebGL context
            # Note: removed --disable-accelerated-2d-canvas to enable WebGL context  
            # Note: removed --disable-software-rasterizer to enable WebGL context
            
            # Network and tracking prevention
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-features=ImprovedCookieControls,LazyFrameLoading,GlobalMediaControls,DestroyProfileOnBrowserClose',
            
            # Chrome specific
            '--allow-running-insecure-content',
            '--disable-features=ChromeWhatsNewUI',
            '--disable-features=OptimizationHints',
            '--disable-features=CalculateNativeWinOcclusion',
            '--disable-features=InterestCohortAPI',
            '--disable-features=FlocIdComputedEventLogging',
            '--disable-features=UserAgentClientHint',
            
            # Memory and resource optimization
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            '--disable-logging',
            '--disable-permissions-api',
            '--disable-notifications',
            '--disable-push-api-background-mode',
            '--disable-background-networking',
            
            # Additional detection bypass
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--disable-features=Translate',
            '--disable-features=OptimizationHints',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',
            '--disable-sync',
            '--disable-domain-reliability',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--metrics-recording-only',
            '--no-first-run',
            '--safebrowsing-disable-auto-update',
            '--password-store=basic',
            '--use-mock-keychain',
        ]
    
    @staticmethod
    def get_enhanced_firefox_prefs() -> Dict[str, Any]:
        """Get enhanced Firefox preferences for better stealth"""
        return {
            # Core stealth preferences
            'dom.webdriver.enabled': False,
            'useAutomationExtension': False,
            
            # Additional stealth preferences
            'general.useragent.override': None,  # Will be set dynamically
            'permissions.default.image': 1,
            'permissions.default.stylesheet': 1,
            'dom.ipc.plugins.enabled.libflashplayer.so': False,
            'network.http.use-cache': True,
            'webgl.disabled': False,
            'dom.webnotifications.enabled': False,
            'media.peerconnection.enabled': False,
            
            # Privacy and tracking
            'privacy.trackingprotection.enabled': False,
            'privacy.resistFingerprinting': False,  # Ironically, this can be detected
            'privacy.donottrackheader.enabled': False,
            'geo.enabled': False,
            'geo.wifi.uri': '',
            'browser.cache.disk.enable': True,
            'browser.cache.memory.enable': True,
            'browser.cache.offline.enable': True,
            'network.cookie.cookieBehavior': 0,
            'network.cookie.lifetimePolicy': 0,
            
            # Performance
            'browser.tabs.remote.autostart': True,
            'browser.tabs.remote.autostart.2': True,
            'dom.ipc.processCount': 8,
            'browser.download.folderList': 2,
            'browser.helperApps.deleteTempFileOnExit': True,
            'browser.download.manager.showWhenStarting': False,
            'browser.download.useDownloadDir': True,
            'browser.download.dir': '/tmp',
            
            # WebRTC leak prevention
            'media.navigator.enabled': False,
            'media.navigator.video.enabled': False,
            'media.peerconnection.ice.default_address_only': True,
            'media.peerconnection.ice.no_host': True,
        }
    
    @staticmethod
    def get_stealth_js() -> str:
        """Get comprehensive JavaScript for stealth injection"""
        return """
        (() => {
            'use strict';
            
            // === Phase 1: Complete webdriver property removal ===
            try {
                // Save original property descriptor functions
                const origGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
                const origGetOwnPropertyNames = Object.getOwnPropertyNames;
                const origGetOwnPropertySymbols = Object.getOwnPropertySymbols;
                const origKeys = Object.keys;
                const origHasOwnProperty = Object.prototype.hasOwnProperty;
                const origGetPrototypeOf = Object.getPrototypeOf;
                
                // Override property detection functions to hide webdriver completely
                Object.getOwnPropertyDescriptor = function(obj, prop) {
                    if (prop === 'webdriver') return undefined;
                    return origGetOwnPropertyDescriptor.apply(this, arguments);
                };
                
                Object.getOwnPropertyNames = function(obj) {
                    const names = origGetOwnPropertyNames.apply(this, arguments);
                    return names.filter(name => name !== 'webdriver');
                };
                
                Object.keys = function(obj) {
                    const keys = origKeys.apply(this, arguments);
                    return keys.filter(key => key !== 'webdriver');
                };
                
                Object.prototype.hasOwnProperty = function(prop) {
                    if (prop === 'webdriver') return false;
                    return origHasOwnProperty.apply(this, arguments);
                };
                
                // Override 'in' operator for webdriver
                const originalHas = Reflect.has;
                Reflect.has = function(target, prop) {
                    if (prop === 'webdriver' && target === navigator) return false;
                    return originalHas.apply(this, arguments);
                };
                
                // Override property enumeration
                const originalOwnKeys = Reflect.ownKeys;
                Reflect.ownKeys = function(target) {
                    const keys = originalOwnKeys.apply(this, arguments);
                    if (target === navigator) {
                        return keys.filter(key => key !== 'webdriver');
                    }
                    return keys;
                };
                
                // Delete webdriver from navigator and its prototype
                delete navigator.webdriver;
                delete Object.getPrototypeOf(navigator).webdriver;
                
                // Prevent webdriver property from being added back
                const navProto = Object.getPrototypeOf(navigator);
                const origDefineProperty = Object.defineProperty;
                
                Object.defineProperty = function(obj, prop, descriptor) {
                    if ((obj === navigator || obj === navProto) && prop === 'webdriver') {
                        return obj;
                    }
                    return origDefineProperty.apply(this, arguments);
                };
                
            } catch (e) {}
            
            // === Phase 2: Chrome runtime detection bypass ===
            try {
                // Remove Chrome automation indicators
                const newProto = navigator.__proto__;
                delete newProto.webdriver;
                
                // Remove CDP traces
                const removeCdpTraces = () => {
                    try {
                        // Remove common CDP properties
                        delete window.$cdc_asdjflasutopfhvcZLmcfl_;
                        delete document.$cdc_asdjflasutopfhvcZLmcfl_;
                        delete window.document.$cdc_asdjflasutopfhvcZLmcfl_;
                        
                        // Remove CDP runtime
                        if (window.chrome) {
                            delete window.chrome.runtime;
                            delete window.chrome._CDP;
                        }
                        
                        // Clean document attributes
                        const docAttrs = document.documentElement.attributes;
                        [...docAttrs].forEach(attr => {
                            if (attr.name.includes('webdriver') || attr.name.includes('selenium')) {
                                document.documentElement.removeAttribute(attr.name);
                            }
                        });
                    } catch (e) {}
                };
                
                removeCdpTraces();
                
                // Re-run on document ready
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', removeCdpTraces);
                }
                
                // Monitor for CDP property additions
                const observer = new MutationObserver(() => {
                    removeCdpTraces();
                });
                
                observer.observe(document.documentElement, {
                    attributes: true,
                    attributeOldValue: true,
                    childList: false,
                    subtree: false
                });
                
            } catch (e) {}
            
            // === Phase 3: Permission API override ===
            try {
                if (navigator.permissions && navigator.permissions.query) {
                    const originalQuery = navigator.permissions.query.bind(navigator.permissions);
                    
                    navigator.permissions.query = async function(parameters) {
                        // Return realistic permission states
                        const permissionStates = {
                            'notifications': 'default',      // More natural than 'denied'
                            'geolocation': 'default',
                            'camera': 'default',
                            'microphone': 'default',
                            'persistent-storage': 'default',
                            'push': 'default',
                            'midi': 'default'
                        };
                        
                        const state = permissionStates[parameters.name] || 'default';
                        
                        return Promise.resolve({
                            state: state,
                            onchange: null
                        });
                    };
                }
                
                // Override Notification permission to be more natural
                if (window.Notification) {
                    const originalNotification = window.Notification;
                    
                    Object.defineProperty(window.Notification, 'permission', {
                        get: () => 'default',  // More natural than 'denied'
                        enumerable: true,
                        configurable: true
                    });
                    
                    // Override requestPermission to return a realistic response
                    if (window.Notification.requestPermission) {
                        window.Notification.requestPermission = async function() {
                            return Promise.resolve('default');
                        };
                    }
                }
            } catch (e) {}
            
            // === Phase 4: Plugin and mime type spoofing ===
            try {
                // Spoof plugins
                const pluginData = [
                    {
                        name: 'Chrome PDF Plugin',
                        filename: 'internal-pdf-viewer',
                        description: 'Portable Document Format',
                        mimeTypes: [{
                            type: 'application/pdf',
                            suffixes: 'pdf',
                            description: 'Portable Document Format'
                        }]
                    },
                    {
                        name: 'Chrome PDF Viewer',
                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                        description: '',
                        mimeTypes: [{
                            type: 'application/pdf',
                            suffixes: 'pdf',
                            description: ''
                        }]
                    },
                    {
                        name: 'Native Client',
                        filename: 'internal-nacl-plugin',
                        description: '',
                        mimeTypes: [
                            {
                                type: 'application/x-nacl',
                                suffixes: '',
                                description: 'Native Client Executable'
                            },
                            {
                                type: 'application/x-pnacl',
                                suffixes: '',
                                description: 'Portable Native Client Executable'
                            }
                        ]
                    }
                ];
                
                // Create fake plugins
                const fakePlugins = pluginData.map(p => {
                    const plugin = Object.create(Plugin.prototype);
                    plugin.name = p.name;
                    plugin.filename = p.filename;
                    plugin.description = p.description;
                    plugin.length = p.mimeTypes.length;
                    
                    p.mimeTypes.forEach((mt, i) => {
                        plugin[i] = mt;
                        Object.defineProperty(plugin, mt.type, {
                            value: mt,
                            enumerable: false
                        });
                    });
                    
                    return plugin;
                });
                
                // Override navigator.plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => fakePlugins,
                    enumerable: true,
                    configurable: true
                });
            } catch (e) {}
            
            // === Phase 5: Canvas fingerprinting protection ===
            try {
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                const originalToBlob = HTMLCanvasElement.prototype.toBlob;
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                
                // Add slight noise to canvas operations
                const addNoise = (data) => {
                    for (let i = 0; i < data.length; i += 4) {
                        data[i] = data[i] + (Math.random() * 2 - 1); // R
                        data[i + 1] = data[i + 1] + (Math.random() * 2 - 1); // G
                        data[i + 2] = data[i + 2] + (Math.random() * 2 - 1); // B
                    }
                    return data;
                };
                
                HTMLCanvasElement.prototype.toDataURL = function(...args) {
                    const context = this.getContext('2d');
                    if (context) {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        addNoise(imageData.data);
                        context.putImageData(imageData, 0, 0);
                    }
                    return originalToDataURL.apply(this, args);
                };
                
                HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {
                    const context = this.getContext('2d');
                    if (context) {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        addNoise(imageData.data);
                        context.putImageData(imageData, 0, 0);
                    }
                    return originalToBlob.call(this, callback, ...args);
                };
            } catch (e) {}
            
            // === Phase 6: WebGL fingerprinting protection ===
            try {
                // Only override if WebGL contexts exist
                if (window.WebGLRenderingContext) {
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.'; // UNMASKED_VENDOR_WEBGL
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER_WEBGL
                        }
                        return getParameter.apply(this, arguments);
                    };
                }
                
                if (window.WebGL2RenderingContext) {
                    const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                    WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter2.apply(this, arguments);
                    };
                }
            } catch (e) {}
            
            // === Phase 7: Audio fingerprinting protection ===
            try {
                const context = {
                    createAnalyser: AudioContext.prototype.createAnalyser,
                    createOscillator: AudioContext.prototype.createOscillator,
                    createGain: AudioContext.prototype.createGain,
                    createScriptProcessor: AudioContext.prototype.createScriptProcessor
                };
                
                // Add noise to audio context operations
                AudioContext.prototype.createAnalyser = function() {
                    const analyser = context.createAnalyser.apply(this, arguments);
                    const getFloatFrequencyData = analyser.getFloatFrequencyData;
                    analyser.getFloatFrequencyData = function(array) {
                        getFloatFrequencyData.apply(this, arguments);
                        for (let i = 0; i < array.length; i++) {
                            array[i] = array[i] + Math.random() * 0.01;
                        }
                    };
                    return analyser;
                };
            } catch (e) {}
            
            // === Phase 8: Remove automation-related properties ===
            try {
                const deleteProps = [
                    // Webdriver properties
                    '__webdriver_evaluate', '__selenium_evaluate', '__webdriver_script_function',
                    '__webdriver_script_func', '__webdriver_script_fn', '__fxdriver_evaluate',
                    '__driver_unwrapped', '__webdriver_unwrapped', '__driver_evaluate',
                    '__selenium_unwrapped', '__fxdriver_unwrapped',
                    
                    // Phantom properties
                    '_phantom', 'phantom', 'callPhantom',
                    
                    // Selenium properties
                    '_Selenium_IDE_Recorder', '_selenium', 'calledSelenium',
                    
                    // Other automation tools
                    '__nightmare', 'nightmare',
                    '__puppeteer_evaluation_script__', '__puppeteer__',
                    '__playwright__', '__pw_manual', '__playwright_target__',
                    
                    // Chrome specific
                    '$chrome_asyncScriptInfo', '$cdc_asdjflasutopfhvcZLmcfl_',
                    
                    // Additional suspects
                    'webdriver', 'driver', 'selenium', 'webdriverEnabled'
                ];
                
                deleteProps.forEach(prop => {
                    try {
                        delete window[prop];
                        delete document[prop];
                        delete navigator[prop];
                    } catch (e) {}
                });
                
                // Monitor for property additions
                const checkProps = () => {
                    deleteProps.forEach(prop => {
                        try {
                            if (window[prop]) delete window[prop];
                            if (document[prop]) delete document[prop];
                            if (navigator[prop]) delete navigator[prop];
                        } catch (e) {}
                    });
                };
                
                // Periodic cleanup
                setInterval(checkProps, 100);
                
            } catch (e) {}
            
            // === Phase 9: Timezone and locale consistency ===
            try {
                // Override timezone detection completely
                const origDate = Date;
                const origGetTimezoneOffset = Date.prototype.getTimezoneOffset;
                
                // Override getTimezoneOffset for all Date instances
                Date.prototype.getTimezoneOffset = function() {
                    return 420; // PST timezone offset (UTC-7)
                };
                
                // Override Date constructor for new Date() calls
                window.Date = new Proxy(origDate, {
                    construct(target, args) {
                        const instance = new target(...args);
                        return instance;
                    },
                    get(target, prop) {
                        if (prop === 'prototype') {
                            return target.prototype;
                        }
                        return target[prop];
                    }
                });
                
                // Ensure consistent Intl timezone
                if (window.Intl && window.Intl.DateTimeFormat) {
                    const origDateTimeFormat = Intl.DateTimeFormat;
                    const origResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
                    
                    // Override resolvedOptions to return consistent timezone
                    Intl.DateTimeFormat.prototype.resolvedOptions = function() {
                        const options = origResolvedOptions.apply(this, arguments);
                        options.timeZone = 'America/Los_Angeles';
                        return options;
                    };
                    
                    // Override DateTimeFormat constructor
                    window.Intl.DateTimeFormat = function(...args) {
                        if (args.length === 0) {
                            args = ['en-US', { timeZone: 'America/Los_Angeles' }];
                        } else if (args.length === 1 && typeof args[0] === 'string') {
                            args.push({ timeZone: 'America/Los_Angeles' });
                        } else if (args.length === 2 && typeof args[1] === 'object') {
                            args[1].timeZone = 'America/Los_Angeles';
                        }
                        return new origDateTimeFormat(...args);
                    };
                    
                    // Copy static methods
                    Object.setPrototypeOf(window.Intl.DateTimeFormat, origDateTimeFormat);
                    window.Intl.DateTimeFormat.prototype = origDateTimeFormat.prototype;
                }
                
                // Override any potential timezone leak through toLocaleString
                const origToLocaleString = Date.prototype.toLocaleString;
                Date.prototype.toLocaleString = function(...args) {
                    if (args.length === 0) {
                        args = ['en-US', { timeZone: 'America/Los_Angeles' }];
                    } else if (args.length === 1) {
                        args.push({ timeZone: 'America/Los_Angeles' });
                    } else if (args.length === 2 && typeof args[1] === 'object') {
                        args[1].timeZone = 'America/Los_Angeles';
                    }
                    return origToLocaleString.apply(this, args);
                };
                
            } catch (e) {}
            
            // === Phase 10: Console protection ===
            try {
                // Prevent console timing attacks
                const originalLog = console.log;
                const originalWarn = console.warn;
                const originalError = console.error;
                
                console.log = function(...args) {
                    // Filter out potential detection strings
                    const str = args.join(' ');
                    if (!str.includes('webdriver') && !str.includes('selenium')) {
                        return originalLog.apply(this, args);
                    }
                };
                
                console.warn = function(...args) {
                    const str = args.join(' ');
                    if (!str.includes('webdriver') && !str.includes('selenium')) {
                        return originalWarn.apply(this, args);
                    }
                };
                
                console.error = function(...args) {
                    const str = args.join(' ');
                    if (!str.includes('webdriver') && !str.includes('selenium')) {
                        return originalError.apply(this, args);
                    }
                };
            } catch (e) {}
            
        })();
        """
    
    @staticmethod
    def get_random_user_agent(browser_type: str = 'chrome') -> str:
        """Get a random realistic user agent"""
        user_agents = {
            'chrome': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            ],
            'firefox': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) Gecko/20100101 Firefox/133.0',
                'Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) Gecko/20100101 Firefox/132.0',
            ]
        }
        
        agents = user_agents.get(browser_type, user_agents['chrome'])
        return random.choice(agents)
    
    @staticmethod
    def get_realistic_viewport() -> Dict[str, int]:
        """Get realistic viewport dimensions"""
        viewports = [
            {'width': 1920, 'height': 1080},  # Full HD
            {'width': 1366, 'height': 768},   # Popular laptop
            {'width': 1440, 'height': 900},   # MacBook
            {'width': 1536, 'height': 864},   # Surface
            {'width': 1600, 'height': 900},   # HD+
            {'width': 1680, 'height': 1050},  # WSXGA+
            {'width': 2560, 'height': 1440},  # QHD
        ]
        return random.choice(viewports)
    
    @staticmethod
    def get_realistic_screen() -> Dict[str, int]:
        """Get realistic screen dimensions"""
        screens = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1600, 'height': 900},
            {'width': 1680, 'height': 1050},
            {'width': 2560, 'height': 1440},
            {'width': 3840, 'height': 2160},  # 4K
        ]
        return random.choice(screens)
    
    @staticmethod
    def get_enhanced_headers(browser_type: str = 'chrome') -> Dict[str, str]:
        """Get enhanced HTTP headers for better stealth"""
        base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        if browser_type == 'chrome':
            base_headers.update({
                'Sec-Ch-Ua': '"Chromium";v="131", "Google Chrome";v="131", "Not.A/Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
            })
        
        return base_headers
    
    @staticmethod
    def get_webgl_vendor_override() -> str:
        """Get WebGL vendor override script"""
        return """
        // WebGL vendor override
        const vendors = ['Intel Inc.', 'NVIDIA Corporation', 'AMD', 'Apple Inc.'];
        const renderers = [
            'Intel Iris OpenGL Engine',
            'Intel HD Graphics 630',
            'NVIDIA GeForce GTX 1050 Ti/PCIe/SSE2',
            'AMD Radeon Pro 560 OpenGL Engine',
            'Apple M1',
            'Mesa DRI Intel(R) HD Graphics'
        ];
        
        const vendor = vendors[Math.floor(Math.random() * vendors.length)];
        const renderer = renderers[Math.floor(Math.random() * renderers.length)];
        
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return vendor;
            if (parameter === 37446) return renderer;
            return getParameter.apply(this, arguments);
        };
        
        if (window.WebGL2RenderingContext) {
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return vendor;
                if (parameter === 37446) return renderer;
                return getParameter2.apply(this, arguments);
            };
        }
        """
    
    @staticmethod
    def get_battery_api_override() -> str:
        """Get Battery API override script"""
        return """
        // Battery API override for consistency
        if ('getBattery' in navigator) {
            const getBattery = navigator.getBattery;
            navigator.getBattery = async function() {
                const battery = await getBattery.call(navigator);
                
                // Override battery properties
                Object.defineProperties(battery, {
                    charging: { value: true },
                    chargingTime: { value: 0 },
                    dischargingTime: { value: Infinity },
                    level: { value: 0.99 }
                });
                
                return battery;
            };
        }
        """
    
    @staticmethod
    def get_profile_chrome_args(profile_path: str = None) -> List[str]:
        """Get Chrome arguments for loading a specific user profile"""
        args = EnhancedStealth.get_enhanced_chrome_args()
        
        if profile_path:
            # Add profile-specific arguments
            args.extend([
                f'--user-data-dir={profile_path}',
                '--profile-directory=Default',  # Use default profile
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-sync',  # Prevent Google account sync in automation
                '--disable-background-networking',  # Reduce background activity
            ])
        
        return args
    
    @staticmethod 
    def get_crawler_profile_path() -> str:
        """Get the path to the crawler's internal Chrome profile"""
        import os
        from pathlib import Path
        
        # Create a dedicated profile directory in modules folder
        modules_dir = Path(__file__).parent
        profile_dir = modules_dir / "crawler_profile"
        
        # Create the profile directory if it doesn't exist
        profile_dir.mkdir(exist_ok=True)
        
        return str(profile_dir)
    
    @staticmethod
    def create_realistic_profile(profile_path: str) -> None:
        """Create a realistic Chrome profile with fake but normal-looking data"""
        import os
        import json
        from pathlib import Path
        
        profile_dir = Path(profile_path)
        profile_dir.mkdir(exist_ok=True)
        
        # Create Preferences file with realistic settings
        preferences = {
            "profile": {
                "name": "Person",
                "default_content_setting_values": {
                    "notifications": 1,
                    "geolocation": 1,
                    "media_stream": 1
                },
                "content_settings": {
                    "pattern_pairs": {}
                }
            },
            "browser": {
                "show_home_button": True,
                "check_default_browser": False
            },
            "bookmark_bar": {
                "show_on_all_tabs": True
            },
            "distribution": {
                "do_not_create_any_shortcuts": True,
                "do_not_create_desktop_shortcut": True,
                "do_not_create_quick_launch_shortcut": True,
                "do_not_create_taskbar_shortcut": True,
                "do_not_launch_chrome": True,
                "do_not_register_for_update_launch": True,
                "make_chrome_default": False,
                "make_chrome_default_for_user": False,
                "suppress_first_run_default_browser_prompt": True,
                "system_level": False,
                "verbose_logging": False
            },
            "first_run_tabs": [],
            "homepage": "https://www.google.com/",
            "homepage_is_newtabpage": False,
            "session": {
                "restore_on_startup": 1
            }
        }
        
        prefs_file = profile_dir / "Preferences"
        with open(prefs_file, 'w') as f:
            json.dump(preferences, f, indent=2)
        
        # Create Local State file
        local_state = {
            "browser": {
                "enabled_labs_experiments": []
            },
            "profile": {
                "info_cache": {
                    "Default": {
                        "name": "Person",
                        "is_using_default_name": True,
                        "avatar_icon": "chrome://theme/IDR_PROFILE_AVATAR_0"
                    }
                }
            },
            "user_experience_metrics": {
                "stability": {
                    "stats_version": 5
                }
            }
        }
        
        local_state_file = profile_dir / "Local State"
        with open(local_state_file, 'w') as f:
            json.dump(local_state, f, indent=2)
        
        # Create First Run file to prevent first run dialogs
        first_run_file = profile_dir / "First Run"
        first_run_file.touch()
        
        print(f"Created realistic Chrome profile at: {profile_path}")
    
    @staticmethod
    def apply_to_page(page: Any, browser_type: str = 'chrome') -> None:
        """Apply all stealth measures to a page object"""
        # This would be called from the browser setup
        # The actual implementation depends on the browser automation framework
        pass