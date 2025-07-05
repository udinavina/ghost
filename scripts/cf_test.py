#!/usr/bin/env python3
"""
Enhanced Cloudflare Turnstile Widget Detector with Error State Handling
Handles error states, retries, and different widget states
"""

import asyncio
import time
import random
from typing import Optional, Dict, List, Tuple
from playwright.async_api import Page, Browser, Playwright, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudflareTurnstileDetector:
    """
    Enhanced Cloudflare Turnstile widget detector with error state handling
    """
    
    def __init__(self, page: Page, debug: bool = False):
        self.page = page
        self.debug = debug
        
        # Enhanced Turnstile widget selectors including error states
        self.turnstile_selectors = [
            # Main Turnstile container selectors
            'div[data-sitekey]',
            '.cf-turnstile',
            '[class*="cf-turnstile"]',
            '[id*="turnstile"]',
            'div[data-theme]',
            
            # Checkbox selectors - the actual clickable element
            'input[type="checkbox"][id*="cf-chl"]',
            'input[type="checkbox"][name*="cf-turnstile"]',
            'label[for*="cf-chl"]',
            'label[for*="turnstile"]',
            
            # Error state containers
            '.cf-error-details',
            '.cf-turnstile-wrapper',
            'div:has-text("Verify you are human")',
            'div:has-text("Having trouble?")',
            
            # Iframe selectors for embedded widgets
            'iframe[src*="turnstile"]',
            'iframe[src*="challenges.cloudflare"]',
            'iframe[title*="challenge"]',
            'iframe[title*="verification"]',
            'iframe[title*="Widget containing"]',
            
            # Challenge container selectors
            'div[data-callback]',
            '.challenge-container',
            '.captcha-container',
            '[class*="challenge"]',
            
            # Generic Cloudflare selectors
            'div[class*="cloudflare"]',
            '[data-cf-beacon]',
            '.cf-browser-verification',
            
            # Button/checkbox patterns
            'input[type="checkbox"][data-sitekey]',
            'button[data-sitekey]',
            '.challenge-form',
        ]
        
        # Error state selectors
        self.error_selectors = [
            'div:has-text("Error")',
            'div:has-text("Having trouble?")',
            '.cf-error-details',
            '[class*="error"]',
            'div:has-text("Send Feedback")',
            '.cf-turnstile-error',
        ]
        
        # Success/completion indicators
        self.success_selectors = [
            '.cf-turnstile-success',
            '[data-cf-turnstile-success]',
            '.challenge-success',
            '.verification-success',
            'div[data-cf-turnstile="success"]',
            'input[type="checkbox"]:checked',
        ]
        
        # Loading/processing indicators
        self.loading_selectors = [
            '.cf-turnstile-loading',
            '.challenge-loading',
            '.verification-loading',
            'div[data-cf-turnstile="loading"]',
            '.cf-spinner',
        ]
    
    async def human_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Add human-like random delays"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)
    
    async def wait_for_page_load(self, timeout: int = 30000):
        """Wait for page to fully load including dynamic content"""
        try:
            # Wait for network to be idle
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            
            # Additional wait for dynamic content
            await self.human_delay(2000, 4000)
            
            # Check if page is still loading JavaScript
            await self.page.wait_for_function(
                "document.readyState === 'complete'",
                timeout=timeout
            )
            
        except PlaywrightTimeoutError:
            logger.warning("Page load timeout, continuing anyway...")
    
    async def detect_turnstile_widgets(self) -> List[Dict]:
        """
        Enhanced detection including error states and different widget types
        """
        widgets = []
        
        logger.info(" Scanning for Turnstile widgets (including error states)...")
        
        # Wait for page to stabilize
        await self.wait_for_page_load()
        
        # Check each selector pattern
        for selector in self.turnstile_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                
                for i, element in enumerate(elements):
                    try:
                        # Check if element is visible
                        is_visible = await element.is_visible()
                        if not is_visible:
                            continue
                        
                        # Get element properties
                        widget_info = await self.analyze_widget_element(element, selector, i)
                        if widget_info:
                            widgets.append(widget_info)
                            
                    except Exception as e:
                        if self.debug:
                            logger.debug(f"Error analyzing element {i} for {selector}: {e}")
                        continue
                        
            except Exception as e:
                if self.debug:
                    logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        # Enhanced detection for text-based elements
        text_based_widgets = await self.detect_text_based_widgets()
        widgets.extend(text_based_widgets)
        
        # Remove duplicates based on position
        unique_widgets = self.deduplicate_widgets(widgets)
        
        logger.info(f" Found {len(unique_widgets)} Turnstile widget(s)")
        
        if self.debug:
            for widget in unique_widgets:
                logger.debug(f"Widget: {widget['selector']} | State: {widget['state']} | Confidence: {widget['confidence']:.2f}")
        
        return unique_widgets
    
    async def detect_text_based_widgets(self) -> List[Dict]:
        """Detect widgets based on text content (for error states)"""
        widgets = []
        
        try:
            # Find elements containing "Verify you are human" text
            verify_elements = await self.page.query_selector_all('text="Verify you are human"')
            
            for element in verify_elements:
                try:
                    # Get the parent container
                    parent = await element.evaluate('el => el.closest("div, label, form")')
                    if parent:
                        widget_info = await self.analyze_text_widget(element, "text-based-verify")
                        if widget_info:
                            widgets.append(widget_info)
                except:
                    continue
            
            # Find error state elements
            error_elements = await self.page.query_selector_all('text="Having trouble?"')
            
            for element in error_elements:
                try:
                    # Get the container with the checkbox
                    container = await element.evaluate('''
                        el => {
                            let current = el;
                            while (current && current.parentElement) {
                                current = current.parentElement;
                                const checkbox = current.querySelector('input[type="checkbox"]');
                                if (checkbox) return current;
                            }
                            return null;
                        }
                    ''')
                    
                    if container:
                        widget_info = await self.analyze_text_widget(element, "error-state", container)
                        if widget_info:
                            widgets.append(widget_info)
                except:
                    continue
                    
        except Exception as e:
            if self.debug:
                logger.debug(f"Error in text-based detection: {e}")
        
        return widgets
    
    async def analyze_text_widget(self, element, selector_type: str, container=None) -> Optional[Dict]:
        """Analyze text-based widget elements"""
        try:
            target_element = container if container else element
            
            # Get bounding box
            bbox = await target_element.bounding_box()
            if not bbox:
                return None
            
            # Check for error state
            is_error_state = await self.check_error_state(target_element)
            
            # Look for checkbox within container
            checkbox = await target_element.query_selector('input[type="checkbox"]')
            
            widget_info = {
                'element': checkbox if checkbox else target_element,
                'container': target_element,
                'selector': selector_type,
                'index': 0,
                'tag_name': await target_element.evaluate("el => el.tagName.toLowerCase()"),
                'is_iframe': False,
                'bbox': bbox,
                'attributes': {},
                'iframe_info': None,
                'state': 'error' if is_error_state else 'normal',
                'has_checkbox': bool(checkbox),
                'confidence': 0.8 if checkbox else 0.6
            }
            
            return widget_info
            
        except Exception as e:
            if self.debug:
                logger.debug(f"Error analyzing text widget: {e}")
            return None
    
    async def check_error_state(self, element) -> bool:
        """Check if widget is in error state"""
        try:
            # Check for error text content
            text_content = await element.text_content()
            error_indicators = [
                "Error", "Having trouble?", "Send Feedback",
                "Try again", "Something went wrong"
            ]
            
            if any(indicator in text_content for indicator in error_indicators):
                return True
            
            # Check for error classes
            class_name = await element.get_attribute('class') or ''
            if 'error' in class_name.lower():
                return True
                
            return False
            
        except:
            return False
    
    async def analyze_widget_element(self, element, selector: str, index: int) -> Optional[Dict]:
        """Enhanced widget element analysis with state detection"""
        try:
            # Get bounding box
            bbox = await element.bounding_box()
            if not bbox:
                return None
            
            # Get element attributes
            attributes = {}
            for attr in ['data-sitekey', 'data-theme', 'data-callback', 'src', 'id', 'class', 'name', 'type']:
                try:
                    value = await element.get_attribute(attr)
                    if value:
                        attributes[attr] = value
                except:
                    pass
            
            # Get element tag name
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            
            # Check if it's an iframe
            is_iframe = tag_name == 'iframe'
            
            # Determine widget state
            widget_state = await self.determine_widget_state(element)
            
            # Get iframe content if applicable
            iframe_info = None
            if is_iframe:
                iframe_info = await self.analyze_iframe_content(element)
            
            # Look for associated checkbox if this is a label or container
            checkbox = None
            if tag_name in ['label', 'div']:
                checkbox = await element.query_selector('input[type="checkbox"]')
                if not checkbox:
                    # Look for checkbox by ID association
                    for_attr = attributes.get('for')
                    if for_attr:
                        checkbox = await self.page.query_selector(f'input[id="{for_attr}"]')
            
            widget_info = {
                'element': checkbox if checkbox else element,
                'container': element,
                'selector': selector,
                'index': index,
                'tag_name': tag_name,
                'is_iframe': is_iframe,
                'bbox': bbox,
                'attributes': attributes,
                'iframe_info': iframe_info,
                'state': widget_state,
                'has_checkbox': bool(checkbox),
                'confidence': self.calculate_confidence(selector, attributes, is_iframe, widget_state)
            }
            
            if self.debug:
                logger.debug(f"Widget found: {widget_info}")
            
            return widget_info
            
        except Exception as e:
            if self.debug:
                logger.debug(f"Error analyzing widget element: {e}")
            return None
    
    async def determine_widget_state(self, element) -> str:
        """Determine the current state of the widget"""
        try:
            # Check if element or its container has error indicators
            container = await element.evaluate('''
                el => {
                    let current = el;
                    for (let i = 0; i < 5; i++) {
                        if (!current.parentElement) break;
                        current = current.parentElement;
                        const text = current.textContent || '';
                        if (text.includes('Error') || text.includes('Having trouble?')) {
                            return current;
                        }
                    }
                    return el;
                }
            ''')
            
            if container:
                text_content = await container.text_content()
                if any(error in text_content for error in ["Error", "Having trouble?", "Send Feedback"]):
                    return "error"
                
                if any(loading in text_content for loading in ["Loading", "Verifying", "Please wait"]):
                    return "loading"
                
                if any(success in text_content for success in ["Success", "Verified", "Complete"]):
                    return "success"
            
            # Check for checkbox state if it's a checkbox
            if await element.evaluate("el => el.type === 'checkbox'"):
                is_checked = await element.is_checked()
                return "success" if is_checked else "normal"
            
            return "normal"
            
        except:
            return "unknown"
    
    async def analyze_iframe_content(self, iframe_element) -> Optional[Dict]:
        """Enhanced iframe analysis"""
        try:
            src = await iframe_element.get_attribute('src')
            title = await iframe_element.get_attribute('title')
            
            # Check if iframe source indicates Turnstile
            is_turnstile_iframe = bool(
                src and (
                    'turnstile' in src.lower() or
                    'challenges.cloudflare' in src.lower() or
                    'cf-' in src.lower()
                )
            )
            
            # Check title for challenge indicators
            is_challenge_title = bool(
                title and (
                    'challenge' in title.lower() or
                    'verification' in title.lower() or
                    'captcha' in title.lower() or
                    'widget containing' in title.lower()
                )
            )
            
            return {
                'src': src,
                'title': title,
                'is_turnstile_iframe': is_turnstile_iframe,
                'is_challenge_title': is_challenge_title
            }
            
        except Exception as e:
            if self.debug:
                logger.debug(f"Error analyzing iframe: {e}")
            return None
    
    def calculate_confidence(self, selector: str, attributes: Dict, is_iframe: bool, state: str) -> float:
        """Enhanced confidence calculation including state"""
        confidence = 0.0
        
        # High confidence indicators
        if 'data-sitekey' in attributes:
            confidence += 0.4
        
        if 'cf-turnstile' in selector or 'turnstile' in selector:
            confidence += 0.3
        
        if is_iframe and attributes.get('src', ''):
            src = attributes['src'].lower()
            if 'turnstile' in src or 'challenges.cloudflare' in src:
                confidence += 0.3
        
        # Checkbox-specific confidence
        if attributes.get('type') == 'checkbox':
            if 'cf-chl' in attributes.get('id', '') or 'turnstile' in attributes.get('name', ''):
                confidence += 0.4
            else:
                confidence += 0.2
        
        # Medium confidence indicators
        if 'data-theme' in attributes or 'data-callback' in attributes:
            confidence += 0.2
        
        if 'cloudflare' in selector.lower():
            confidence += 0.2
        
        # Text-based confidence
        if 'text-based' in selector:
            confidence += 0.2
        
        # State-based confidence adjustment
        if state == 'error':
            confidence += 0.1  # Error state widgets are still valid targets
        elif state == 'success':
            confidence -= 0.3  # Already completed
        elif state == 'loading':
            confidence -= 0.1  # Might need to wait
        
        # Lower confidence indicators
        if 'challenge' in selector.lower() or 'verification' in selector.lower():
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def deduplicate_widgets(self, widgets: List[Dict]) -> List[Dict]:
        """Enhanced deduplication considering states"""
        unique_widgets = []
        
        for widget in widgets:
            is_duplicate = False
            bbox = widget['bbox']
            
            for existing in unique_widgets:
                existing_bbox = existing['bbox']
                
                # Check if positions are very close (within 10 pixels)
                if (abs(bbox['x'] - existing_bbox['x']) < 10 and
                    abs(bbox['y'] - existing_bbox['y']) < 10):
                    
                    # Prefer widgets with checkboxes over containers
                    if widget['has_checkbox'] and not existing['has_checkbox']:
                        unique_widgets.remove(existing)
                        break
                    elif existing['has_checkbox'] and not widget['has_checkbox']:
                        is_duplicate = True
                        break
                    # Keep the one with higher confidence
                    elif widget['confidence'] > existing['confidence']:
                        unique_widgets.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_widgets.append(widget)
        
        # Sort by confidence (highest first)
        return sorted(unique_widgets, key=lambda w: w['confidence'], reverse=True)
    
    async def click_turnstile_widget(self, widget: Dict) -> bool:
        """Enhanced clicking with error state handling"""
        try:
            element = widget['element']
            state = widget['state']
            
            logger.info(f" Clicking Turnstile widget (state: {state}, confidence: {widget['confidence']:.2f})")
            
            # Handle different states
            if state == 'success':
                logger.info("Widget already in success state")
                return True
            
            if state == 'loading':
                logger.info("Widget is loading, waiting...")
                await self.human_delay(2000, 4000)
                # Re-detect state after waiting
                new_state = await self.determine_widget_state(element)
                if new_state == 'success':
                    return True
            
            # Handle error state with retry
            if state == 'error':
                logger.info("Widget in error state, attempting refresh/retry...")
                await self.handle_error_state(widget)
                await self.human_delay(1000, 2000)
            
            # Wait for element to be stable
            await element.wait_for_element_state("stable", timeout=5000)
            
            # Scroll element into view
            await element.scroll_into_view_if_needed()
            
            # Add human delay
            await self.human_delay(500, 1500)
            
            # Enhanced clicking strategies
            return await self.perform_enhanced_click(element, widget)
                
        except Exception as e:
            logger.error(f"Error clicking Turnstile widget: {e}")
            return False
    
    async def handle_error_state(self, widget: Dict):
        """Handle widgets in error state"""
        try:
            container = widget['container']
            
            # Look for refresh/retry buttons
            refresh_selectors = [
                'button:has-text("Try again")',
                'button:has-text("Retry")',
                'button:has-text("Refresh")',
                'a:has-text("Try again")',
                '.refresh-button',
                '.retry-button'
            ]
            
            for selector in refresh_selectors:
                try:
                    refresh_btn = await container.query_selector(selector)
                    if refresh_btn and await refresh_btn.is_visible():
                        logger.info(f"Found refresh button: {selector}")
                        await refresh_btn.click()
                        await self.human_delay(1000, 2000)
                        return
                except:
                    continue
            
            # If no refresh button, try clicking the error area itself
            error_element = await container.query_selector('div:has-text("Error"), div:has-text("Having trouble?")')
            if error_element:
                await error_element.click()
                await self.human_delay(500, 1000)
                
        except Exception as e:
            if self.debug:
                logger.debug(f"Error handling error state: {e}")
    
    async def perform_enhanced_click(self, element, widget: Dict) -> bool:
        """Enhanced clicking with multiple strategies"""
        try:
            # Check if element is still visible and enabled
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()
            
            if not is_visible:
                logger.warning("Widget is not visible")
                return False
            
            # Different strategies based on element type
            if widget['is_iframe']:
                return await self.click_iframe_widget(element, widget)
            
            # For checkboxes, use specific checkbox strategies
            if widget['has_checkbox'] or await element.evaluate("el => el.type === 'checkbox'"):
                return await self.click_checkbox_widget(element, widget)
            
            # General element clicking
            return await self.click_general_widget(element, widget)
                
        except Exception as e:
            logger.error(f"Error in enhanced click: {e}")
            return False
    
    async def click_checkbox_widget(self, element, widget: Dict) -> bool:
        """Specialized checkbox clicking"""
        try:
            logger.info("Clicking checkbox widget...")
            
            # Check if already checked
            is_checked = await element.is_checked()
            if is_checked:
                logger.info("Checkbox already checked")
                return True
            
            # Try different checkbox interaction methods
            strategies = [
                # Method 1: Direct click
                lambda: element.click(timeout=5000),
                
                # Method 2: Force click
                lambda: element.click(force=True, timeout=5000),
                
                # Method 3: Check method
                lambda: element.check(timeout=5000),
                
                # Method 4: Space key press
                lambda: self.checkbox_space_press(element),
                
                # Method 5: Human-like click
                lambda: self.simulate_human_click(element),
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    logger.info(f"Trying checkbox strategy {i + 1}")
                    await strategy()
                    
                    # Wait for response
                    await self.human_delay(1000, 2000)
                    
                    # Check if checkbox is now checked
                    if await element.is_checked():
                        logger.info(" Checkbox checked successfully!")
                        return True
                    
                    # Check for other success indicators
                    if await self.verify_click_success():
                        logger.info(" Widget interaction successful!")
                        return True
                    
                except Exception as e:
                    logger.warning(f"Checkbox strategy {i + 1} failed: {e}")
                    if i < len(strategies) - 1:
                        await self.human_delay(500, 1000)
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error clicking checkbox widget: {e}")
            return False
    
    async def checkbox_space_press(self, element):
        """Press space key on focused checkbox"""
        await element.focus()
        await self.human_delay(100, 300)
        await element.press("Space")
    
    async def click_general_widget(self, element, widget: Dict) -> bool:
        """Click general widget elements"""
        try:
            strategies = [
                lambda: element.click(timeout=5000),
                lambda: element.click(force=True, timeout=5000),
                lambda: self.simulate_human_click(element),
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    logger.info(f"Trying general click strategy {i + 1}")
                    await strategy()
                    
                    # Wait for response
                    await self.human_delay(1000, 2000)
                    
                    # Check if click was successful
                    if await self.verify_click_success():
                        logger.info(" Widget click successful!")
                        return True
                    
                except Exception as e:
                    logger.warning(f"General strategy {i + 1} failed: {e}")
                    if i < len(strategies) - 1:
                        await self.human_delay(500, 1000)
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error in general widget click: {e}")
            return False
    
    async def click_iframe_widget(self, iframe_element, widget: Dict) -> bool:
        """Enhanced iframe widget handling"""
        try:
            logger.info("Handling iframe widget...")
            
            # Get iframe content frame
            content_frame = await iframe_element.content_frame()
            if not content_frame:
                logger.warning("Could not access iframe content")
                # Try clicking the iframe itself
                await iframe_element.click(timeout=5000)
                await self.human_delay(1000, 2000)
                return await self.verify_click_success()
            
            # Wait for iframe content to load
            await content_frame.wait_for_load_state("networkidle", timeout=10000)
            
            # Look for clickable elements within iframe
            clickable_selectors = [
                'input[type="checkbox"]',
                'button',
                '.challenge-button',
                '.verify-button',
                '[role="button"]',
                'div[tabindex]',
                '.clickable',
                'label'
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = await content_frame.query_selector_all(selector)
                    
                    for element in elements:
                        if await element.is_visible():
                            logger.info(f"Clicking element in iframe: {selector}")
                            
                            # For checkboxes in iframe
                            if selector == 'input[type="checkbox"]':
                                if not await element.is_checked():
                                    await element.click(timeout=5000)
                            else:
                                await element.click(timeout=5000)
                            
                            # Wait and check for success
                            await self.human_delay(1000, 2000)
                            
                            if await self.verify_click_success():
                                logger.info(" Iframe widget click successful!")
                                return True
                            
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Iframe selector {selector} failed: {e}")
                    continue
            
            # If no specific elements found, try clicking the iframe itself
            logger.info("Trying to click iframe directly...")
            await iframe_element.click(timeout=5000)
            await self.human_delay(1000, 2000)
            
            return await self.verify_click_success()
            
        except Exception as e:
            logger.error(f"Error handling iframe widget: {e}")
            return False
    
    async def simulate_human_click(self, element):
        """Enhanced human-like clicking behavior"""
        try:
            # Get element center position
            bbox = await element.bounding_box()
            if not bbox:
                await element.click()
                return
            
            # Add slight randomness to click position
            offset_x = random.uniform(-bbox['width'] * 0.1, bbox['width'] * 0.1)
            offset_y = random.uniform(-bbox['height'] * 0.1, bbox['height'] * 0.1)
            
            click_x = bbox['x'] + bbox['width'] / 2 + offset_x
            click_y = bbox['y'] + bbox['height'] / 2 + offset_y
            
            # Hover first, then click
            await self.page.mouse.move(click_x, click_y)
            await self.human_delay(100, 300)
            await self.page.mouse.down()
            await self.human_delay(50, 150)
            await self.page.mouse.up()
            
        except Exception as e:
            logger.warning(f"Human click simulation failed, using regular click: {e}")
            await element.click()
    
    async def verify_click_success(self) -> bool:
        """Enhanced success verification"""
        try:
            # Wait for potential page changes
            await self.human_delay(1000, 2000)
            
            # Check for success indicators
            for selector in self.success_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        logger.info(f" Success indicator found: {selector}")
                        return True
                except:
                    continue
            
            # Check for checked checkboxes
            try:
                checked_boxes = await self.page.query_selector_all('input[type="checkbox"]:checked')
                for checkbox in checked_boxes:
                    # Check if it's a Turnstile checkbox
                    checkbox_id = await checkbox.get_attribute('id') or ''
                    checkbox_name = await checkbox.get_attribute('name') or ''
                    
                    if 'cf-chl' in checkbox_id or 'turnstile' in checkbox_name:
                        logger.info(" Turnstile checkbox is checked")
                        return True
            except:
                pass
            
            # Check if page has changed (redirect, new content, etc.)
            try:
                await self.page.wait_for_function(
                    """() => {
                        return document.readyState === 'complete' && 
                               !document.querySelector('.cf-turnstile-loading, .challenge-loading');
                    }""",
                    timeout=5000
                )
            except PlaywrightTimeoutError:
                pass
            
            # Check if error states are gone
            remaining_errors = 0
            for selector in self.error_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    remaining_errors += len([e for e in elements if await e.is_visible()])
                except:
                    continue
            
            if remaining_errors == 0:
                logger.info(" No error states remaining")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error verifying click success: {e}")
            return False
    
    async def handle_all_turnstile_widgets(self, max_attempts: int = 5) -> bool:
        """
        Enhanced handling with retry logic for error states
        """
        logger.info(" Starting enhanced Turnstile widget detection and handling...")
        
        success = False
        
        for attempt in range(max_attempts):
            logger.info(f"Attempt {attempt + 1}/{max_attempts}")
            
            # Detect widgets
            widgets = await self.detect_turnstile_widgets()
            
            if not widgets:
                logger.info("No Turnstile widgets detected")
                success = True
                break
            
            # Sort widgets by priority (error states first, then by confidence)
            widgets = self.prioritize_widgets(widgets)
            
            # Try to handle each widget
            for widget in widgets:
                logger.info(f"Processing widget: {widget['selector']} | State: {widget['state']} | Confidence: {widget['confidence']:.2f}")
                
                # Skip already successful widgets
                if widget['state'] == 'success':
                    logger.info("Widget already successful, skipping")
                    success = True
                    continue
                
                if await self.click_turnstile_widget(widget):
                    success = True
                    break
                else:
                    # If widget failed, wait and try refresh strategies
                    logger.info("Widget click failed, trying refresh strategies...")
                    await self.try_refresh_strategies(widget)
            
            if success:
                break
            
            # Wait before next attempt with exponential backoff
            if attempt < max_attempts - 1:
                wait_time = (attempt + 1) * 2  # 2, 4, 6, 8 seconds
                logger.info(f"Waiting {wait_time} seconds before next attempt...")
                await self.human_delay(wait_time * 1000, (wait_time + 2) * 1000)
                
                # Try page refresh if we're on the last few attempts
                if attempt >= max_attempts - 2:
                    logger.info("Trying page refresh...")
                    await self.page.reload(wait_until="networkidle")
                    await self.human_delay(3000, 5000)
        
        return success
    
    def prioritize_widgets(self, widgets: List[Dict]) -> List[Dict]:
        """Prioritize widgets for processing"""
        def priority_score(widget):
            score = widget['confidence']
            
            # Prioritize widgets with checkboxes
            if widget['has_checkbox']:
                score += 1.0
            
            # Prioritize error states (they need immediate attention)
            if widget['state'] == 'error':
                score += 0.5
            
            # Deprioritize already successful widgets
            if widget['state'] == 'success':
                score -= 2.0
            
            # Deprioritize loading widgets
            if widget['state'] == 'loading':
                score -= 0.5
            
            return score
        
        return sorted(widgets, key=priority_score, reverse=True)
    
    async def try_refresh_strategies(self, widget: Dict):
        """Try various refresh strategies for failed widgets"""
        try:
            container = widget['container']
            
            # Strategy 1: Look for and click refresh buttons
            refresh_patterns = [
                'button:has-text("Try again")',
                'button:has-text("Refresh")',
                'a:has-text("Try again")',
                '.refresh', '.retry', '.reload'
            ]
            
            for pattern in refresh_patterns:
                try:
                    refresh_element = await container.query_selector(pattern)
                    if refresh_element and await refresh_element.is_visible():
                        logger.info(f"Clicking refresh element: {pattern}")
                        await refresh_element.click()
                        await self.human_delay(2000, 3000)
                        return
                except:
                    continue
            
            # Strategy 2: Right-click on widget (sometimes triggers refresh menu)
            try:
                await widget['element'].click(button='right')
                await self.human_delay(500, 1000)
                
                # Look for refresh option in context menu
                refresh_option = await self.page.query_selector('text="Refresh"')
                if refresh_option:
                    await refresh_option.click()
                    await self.human_delay(2000, 3000)
                    return
            except:
                pass
            
            # Strategy 3: Try pressing F5 or Ctrl+R on the widget
            try:
                await widget['element'].focus()
                await self.page.keyboard.press('F5')
                await self.human_delay(2000, 3000)
            except:
                pass
                
        except Exception as e:
            if self.debug:
                logger.debug(f"Error in refresh strategies: {e}")


class TurnstileTester:
    """
    Enhanced testing class with better error handling
    """
    
    def __init__(self, headless: bool = False, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        
        # Enhanced browser launch with more stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-extensions',
                '--disable-default-apps',
                '--disable-dev-shm-usage',
                '--disable-gpu-sandbox',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
            ]
        )
        
        # Create context with enhanced stealth settings
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
        )
        
        self.page = await context.new_page()
        
        # Enhanced anti-detection scripts
        await self.page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            delete window.navigator.__proto__.webdriver;
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => ({
                    length: 4,
                    0: { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    1: { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    2: { name: 'Native Client', filename: 'internal-nacl-plugin' },
                    3: { name: 'WebKit built-in PDF', filename: 'webkit-pdf-plugin' }
                }),
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock hardware properties
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Add random mouse movements
            let moveCount = 0;
            const maxMoves = 3 + Math.floor(Math.random() * 5);
            
            const randomMove = () => {
                if (moveCount >= maxMoves) return;
                
                const x = Math.random() * window.innerWidth;
                const y = Math.random() * window.innerHeight;
                
                const event = new MouseEvent('mousemove', {
                    clientX: x,
                    clientY: y,
                    bubbles: true
                });
                document.dispatchEvent(event);
                moveCount++;
                
                setTimeout(randomMove, 500 + Math.random() * 1500);
            };
            
            setTimeout(randomMove, 1000 + Math.random() * 2000);
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def test_url(self, url: str, wait_time: int = 5) -> bool:
        """Enhanced URL testing with error state handling"""
        try:
            logger.info(f" Navigating to: {url}")
            
            # Navigate to the URL
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for any dynamic content to load
            await asyncio.sleep(wait_time)
            
            # Create enhanced detector
            detector = CloudflareTurnstileDetector(self.page, debug=self.debug)
            
            # Handle Turnstile widgets with enhanced retry logic
            success = await detector.handle_all_turnstile_widgets(max_attempts=5)
            
            if success:
                logger.info(" Successfully handled Turnstile widgets!")
                
                # Final verification
                final_widgets = await detector.detect_turnstile_widgets()
                error_widgets = [w for w in final_widgets if w['state'] == 'error']
                
                if error_widgets:
                    logger.warning(f" {len(error_widgets)} widgets still in error state")
                    return False
                else:
                    logger.info(" All widgets successfully processed!")
                    return True
            else:
                logger.warning(" Failed to handle Turnstile widgets")
                return False
            
        except Exception as e:
            logger.error(f"Error testing URL {url}: {e}")
            return False
    
    async def test_with_screenshot(self, url: str, screenshot_path: str = None) -> Tuple[bool, str]:
        """Test URL and take screenshots for debugging"""
        try:
            success = await self.test_url(url)
            
            # Take screenshot
            if not screenshot_path:
                timestamp = int(time.time())
                screenshot_path = f"turnstile_test_{timestamp}.png"
            
            await self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            return success, screenshot_path
            
        except Exception as e:
            logger.error(f"Error in test with screenshot: {e}")
            return False, ""


# Enhanced example usage and test functions
async def test_error_state_handling():
    """Test the enhanced error state handling"""
    
    test_urls = [
        "https://demo.turnstile.workers.dev/",
        "https://2captcha.com/demo/cloudflare-turnstile",
        # Add your URLs with error states here
    ]
    
    async with TurnstileTester(headless=False, debug=True) as tester:
        for url in test_urls:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing Enhanced Error Handling: {url}")
            logger.info(f"{'='*60}")
            
            success, screenshot = await tester.test_with_screenshot(url)
            
            if success:
                logger.info(f" {url} - SUCCESS")
            else:
                logger.warning(f" {url} - FAILED")
                logger.info(f"Screenshot saved for debugging: {screenshot}")
            
            # Wait between tests
            await asyncio.sleep(5)


async def test_specific_error_site(url: str, headless: bool = False):
    """Test a site specifically known to have error states"""
    async with TurnstileTester(headless=headless, debug=True) as tester:
        logger.info(f"Testing error state handling on: {url}")
        
        success, screenshot = await tester.test_with_screenshot(url)
        
        if success:
            print(f" Successfully handled error states on {url}")
        else:
            print(f" Failed to handle error states on {url}")
            print(f"Debug screenshot: {screenshot}")
        
        return success


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific URL
        url = sys.argv[1]
        headless = "--headless" in sys.argv
        
        result = asyncio.run(test_specific_error_site(url, headless=headless))
        
        if result:
            print(f" Successfully handled Turnstile error states on {url}")
            sys.exit(0)
        else:
            print(f" Failed to handle Turnstile error states on {url}")
            sys.exit(1)
    else:
        # Run enhanced error state tests
        asyncio.run(test_error_state_handling())#!/usr/bin/env python3
"""
Cloudflare Turnstile "I'm Human" Widget Detector and Auto-Clicker
For testing purposes - detects dynamically generated Cloudflare widgets
"""

import asyncio
import time
import random
from typing import Optional, Dict, List, Tuple
from playwright.async_api import Page, Browser, Playwright, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudflareTurnstileDetector:
    """
    Comprehensive Cloudflare Turnstile widget detector and interactor
    Handles various widget states and dynamic generation
    """
    
    def __init__(self, page: Page, debug: bool = False):
        self.page = page
        self.debug = debug
        
        # Turnstile widget selectors (multiple patterns for reliability)
        self.turnstile_selectors = [
            # Main Turnstile container selectors
            'div[data-sitekey]',
            '.cf-turnstile',
            '[class*="cf-turnstile"]',
            '[id*="turnstile"]',
            'div[data-theme]',
            
            # Iframe selectors for embedded widgets
            'iframe[src*="turnstile"]',
            'iframe[src*="challenges.cloudflare"]',
            'iframe[title*="challenge"]',
            'iframe[title*="verification"]',
            
            # Challenge container selectors
            'div[data-callback]',
            '.challenge-container',
            '.captcha-container',
            '[class*="challenge"]',
            
            # Generic Cloudflare selectors
            'div[class*="cloudflare"]',
            '[data-cf-beacon]',
            '.cf-browser-verification',
            
            # Button/checkbox patterns
            'input[type="checkbox"][data-sitekey]',
            'button[data-sitekey]',
            '.challenge-form',
        ]
        
        # Success/completion indicators
        self.success_selectors = [
            '.cf-turnstile-success',
            '[data-cf-turnstile-success]',
            '.challenge-success',
            '.verification-success',
            'div[data-cf-turnstile="success"]'
        ]
        
        # Loading/processing indicators
        self.loading_selectors = [
            '.cf-turnstile-loading',
            '.challenge-loading',
            '.verification-loading',
            'div[data-cf-turnstile="loading"]'
        ]
    
    async def human_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Add human-like random delays"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)
    
    async def wait_for_page_load(self, timeout: int = 30000):
        """Wait for page to fully load including dynamic content"""
        try:
            # Wait for network to be idle
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            
            # Additional wait for dynamic content
            await self.human_delay(1000, 3000)
            
            # Check if page is still loading JavaScript
            await self.page.wait_for_function(
                "document.readyState === 'complete'",
                timeout=timeout
            )
            
        except PlaywrightTimeoutError:
            logger.warning("Page load timeout, continuing anyway...")
    
    async def detect_turnstile_widgets(self) -> List[Dict]:
        """
        Detect all Turnstile widgets on the page
        Returns list of widget information dictionaries
        """
        widgets = []
        
        logger.info(" Scanning for Turnstile widgets...")
        
        # Wait for page to stabilize
        await self.wait_for_page_load()
        
        # Check each selector pattern
        for selector in self.turnstile_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                
                for i, element in enumerate(elements):
                    try:
                        # Check if element is visible
                        is_visible = await element.is_visible()
                        if not is_visible:
                            continue
                        
                        # Get element properties
                        widget_info = await self.analyze_widget_element(element, selector, i)
                        if widget_info:
                            widgets.append(widget_info)
                            
                    except Exception as e:
                        if self.debug:
                            logger.debug(f"Error analyzing element {i} for {selector}: {e}")
                        continue
                        
            except Exception as e:
                if self.debug:
                    logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        # Remove duplicates based on position
        unique_widgets = self.deduplicate_widgets(widgets)
        
        logger.info(f" Found {len(unique_widgets)} Turnstile widget(s)")
        
        return unique_widgets
    
    async def analyze_widget_element(self, element, selector: str, index: int) -> Optional[Dict]:
        """Analyze a potential Turnstile widget element"""
        try:
            # Get bounding box
            bbox = await element.bounding_box()
            if not bbox:
                return None
            
            # Get element attributes
            attributes = {}
            for attr in ['data-sitekey', 'data-theme', 'data-callback', 'src', 'id', 'class']:
                try:
                    value = await element.get_attribute(attr)
                    if value:
                        attributes[attr] = value
                except:
                    pass
            
            # Get element tag name
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            
            # Check if it's an iframe
            is_iframe = tag_name == 'iframe'
            
            # Get iframe content if applicable
            iframe_info = None
            if is_iframe:
                iframe_info = await self.analyze_iframe_content(element)
            
            widget_info = {
                'element': element,
                'selector': selector,
                'index': index,
                'tag_name': tag_name,
                'is_iframe': is_iframe,
                'bbox': bbox,
                'attributes': attributes,
                'iframe_info': iframe_info,
                'confidence': self.calculate_confidence(selector, attributes, is_iframe)
            }
            
            if self.debug:
                logger.debug(f"Widget found: {widget_info}")
            
            return widget_info
            
        except Exception as e:
            if self.debug:
                logger.debug(f"Error analyzing widget element: {e}")
            return None
    
    async def analyze_iframe_content(self, iframe_element) -> Optional[Dict]:
        """Analyze iframe content for Turnstile indicators"""
        try:
            src = await iframe_element.get_attribute('src')
            title = await iframe_element.get_attribute('title')
            
            # Check if iframe source indicates Turnstile
            is_turnstile_iframe = bool(
                src and (
                    'turnstile' in src.lower() or
                    'challenges.cloudflare' in src.lower() or
                    'cf-' in src.lower()
                )
            )
            
            # Check title for challenge indicators
            is_challenge_title = bool(
                title and (
                    'challenge' in title.lower() or
                    'verification' in title.lower() or
                    'captcha' in title.lower()
                )
            )
            
            return {
                'src': src,
                'title': title,
                'is_turnstile_iframe': is_turnstile_iframe,
                'is_challenge_title': is_challenge_title
            }
            
        except Exception as e:
            if self.debug:
                logger.debug(f"Error analyzing iframe: {e}")
            return None
    
    def calculate_confidence(self, selector: str, attributes: Dict, is_iframe: bool) -> float:
        """Calculate confidence score for Turnstile detection"""
        confidence = 0.0
        
        # High confidence indicators
        if 'data-sitekey' in attributes:
            confidence += 0.4
        
        if 'cf-turnstile' in selector or 'turnstile' in selector:
            confidence += 0.3
        
        if is_iframe and attributes.get('src', ''):
            src = attributes['src'].lower()
            if 'turnstile' in src or 'challenges.cloudflare' in src:
                confidence += 0.3
        
        # Medium confidence indicators
        if 'data-theme' in attributes or 'data-callback' in attributes:
            confidence += 0.2
        
        if 'cloudflare' in selector.lower():
            confidence += 0.2
        
        # Lower confidence indicators
        if 'challenge' in selector.lower() or 'verification' in selector.lower():
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def deduplicate_widgets(self, widgets: List[Dict]) -> List[Dict]:
        """Remove duplicate widgets based on position and attributes"""
        unique_widgets = []
        
        for widget in widgets:
            is_duplicate = False
            bbox = widget['bbox']
            
            for existing in unique_widgets:
                existing_bbox = existing['bbox']
                
                # Check if positions are very close (within 10 pixels)
                if (abs(bbox['x'] - existing_bbox['x']) < 10 and
                    abs(bbox['y'] - existing_bbox['y']) < 10):
                    
                    # Keep the one with higher confidence
                    if widget['confidence'] > existing['confidence']:
                        unique_widgets.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_widgets.append(widget)
        
        # Sort by confidence (highest first)
        return sorted(unique_widgets, key=lambda w: w['confidence'], reverse=True)
    
    async def click_turnstile_widget(self, widget: Dict) -> bool:
        """
        Click on a detected Turnstile widget with human-like behavior
        """
        try:
            element = widget['element']
            
            logger.info(f" Attempting to click Turnstile widget (confidence: {widget['confidence']:.2f})")
            
            # Wait for element to be stable
            await element.wait_for_element_state("stable", timeout=5000)
            
            # Scroll element into view
            await element.scroll_into_view_if_needed()
            
            # Add human delay
            await self.human_delay(500, 1500)
            
            # If it's an iframe, we need to handle it differently
            if widget['is_iframe']:
                return await self.click_iframe_widget(element, widget)
            else:
                return await self.click_direct_widget(element, widget)
                
        except Exception as e:
            logger.error(f"Error clicking Turnstile widget: {e}")
            return False
    
    async def click_direct_widget(self, element, widget: Dict) -> bool:
        """Click directly on a non-iframe widget"""
        try:
            # Check if element is still visible and enabled
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()
            
            if not is_visible:
                logger.warning("Widget is not visible")
                return False
            
            if not is_enabled:
                logger.warning("Widget is not enabled")
                return False
            
            # Try different click strategies
            strategies = [
                lambda: element.click(timeout=5000),
                lambda: element.click(force=True, timeout=5000),
                lambda: self.simulate_human_click(element),
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    logger.info(f"Trying click strategy {i + 1}")
                    await strategy()
                    
                    # Wait for response
                    await self.human_delay(1000, 2000)
                    
                    # Check if click was successful
                    if await self.verify_click_success():
                        logger.info(" Widget click successful!")
                        return True
                    
                except Exception as e:
                    logger.warning(f"Click strategy {i + 1} failed: {e}")
                    if i < len(strategies) - 1:
                        await self.human_delay(500, 1000)
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error in direct widget click: {e}")
            return False
    
    async def click_iframe_widget(self, iframe_element, widget: Dict) -> bool:
        """Handle clicking within an iframe widget"""
        try:
            logger.info("Handling iframe widget...")
            
            # Get iframe content frame
            content_frame = await iframe_element.content_frame()
            if not content_frame:
                logger.warning("Could not access iframe content")
                return False
            
            # Wait for iframe content to load
            await content_frame.wait_for_load_state("networkidle", timeout=10000)
            
            # Look for clickable elements within iframe
            clickable_selectors = [
                'input[type="checkbox"]',
                'button',
                '.challenge-button',
                '.verify-button',
                '[role="button"]',
                'div[tabindex]',
                '.clickable'
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = await content_frame.query_selector_all(selector)
                    
                    for element in elements:
                        if await element.is_visible():
                            logger.info(f"Clicking element in iframe: {selector}")
                            await element.click(timeout=5000)
                            
                            # Wait and check for success
                            await self.human_delay(1000, 2000)
                            
                            if await self.verify_click_success():
                                logger.info(" Iframe widget click successful!")
                                return True
                            
                except Exception as e:
                    if self.debug:
                        logger.debug(f"Iframe selector {selector} failed: {e}")
                    continue
            
            # If no specific elements found, try clicking the iframe itself
            logger.info("Trying to click iframe directly...")
            await iframe_element.click(timeout=5000)
            await self.human_delay(1000, 2000)
            
            return await self.verify_click_success()
            
        except Exception as e:
            logger.error(f"Error handling iframe widget: {e}")
            return False
    
    async def simulate_human_click(self, element):
        """Simulate more human-like clicking behavior"""
        try:
            # Get element center position
            bbox = await element.bounding_box()
            if not bbox:
                await element.click()
                return
            
            # Add slight randomness to click position
            offset_x = random.uniform(-bbox['width'] * 0.1, bbox['width'] * 0.1)
            offset_y = random.uniform(-bbox['height'] * 0.1, bbox['height'] * 0.1)
            
            click_x = bbox['x'] + bbox['width'] / 2 + offset_x
            click_y = bbox['y'] + bbox['height'] / 2 + offset_y
            
            # Hover first, then click
            await self.page.mouse.move(click_x, click_y)
            await self.human_delay(100, 300)
            await self.page.mouse.down()
            await self.human_delay(50, 150)
            await self.page.mouse.up()
            
        except Exception as e:
            logger.warning(f"Human click simulation failed, using regular click: {e}")
            await element.click()
    
    async def verify_click_success(self) -> bool:
        """Verify if the widget click was successful"""
        try:
            # Wait for potential page changes
            await self.human_delay(1000, 2000)
            
            # Check for success indicators
            for selector in self.success_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        logger.info(f" Success indicator found: {selector}")
                        return True
                except:
                    continue
            
            # Check if page has changed (redirect, new content, etc.)
            try:
                # Look for form submissions or page changes
                await self.page.wait_for_function(
                    """() => {
                        return document.readyState === 'complete' && 
                               !document.querySelector('.cf-turnstile-loading, .challenge-loading');
                    }""",
                    timeout=5000
                )
            except PlaywrightTimeoutError:
                pass
            
            # Check if Turnstile widgets are gone (indicating success)
            remaining_widgets = await self.detect_turnstile_widgets()
            if len(remaining_widgets) == 0:
                logger.info(" No Turnstile widgets remaining - likely successful")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error verifying click success: {e}")
            return False
    
    async def handle_all_turnstile_widgets(self, max_attempts: int = 3) -> bool:
        """
        Detect and handle all Turnstile widgets on the page
        """
        logger.info(" Starting Turnstile widget detection and handling...")
        
        success = False
        
        for attempt in range(max_attempts):
            logger.info(f"Attempt {attempt + 1}/{max_attempts}")
            
            # Detect widgets
            widgets = await self.detect_turnstile_widgets()
            
            if not widgets:
                logger.info("No Turnstile widgets detected")
                success = True
                break
            
            # Try to handle each widget
            for widget in widgets:
                logger.info(f"Processing widget: {widget['selector']} (confidence: {widget['confidence']:.2f})")
                
                if await self.click_turnstile_widget(widget):
                    success = True
                    break
            
            if success:
                break
            
            # Wait before next attempt
            if attempt < max_attempts - 1:
                logger.info("Waiting before next attempt...")
                await self.human_delay(2000, 4000)
        
        return success


class TurnstileTester:
    """
    Main class for testing Turnstile detection and interaction
    """
    
    def __init__(self, headless: bool = False, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-extensions',
                '--disable-default-apps',
            ]
        )
        
        # Create context with realistic settings
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        self.page = await context.new_page()
        
        # Add anti-detection scripts
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            delete window.navigator.__proto__.webdriver;
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def test_url(self, url: str) -> bool:
        """Test Turnstile detection and interaction on a specific URL"""
        try:
            logger.info(f" Navigating to: {url}")
            
            # Navigate to the URL
            await self.page.goto(url, wait_until="networkidle")
            
            # Create detector
            detector = CloudflareTurnstileDetector(self.page, debug=self.debug)
            
            # Handle Turnstile widgets
            success = await detector.handle_all_turnstile_widgets()
            
            if success:
                logger.info(" Successfully handled Turnstile widgets!")
            else:
                logger.warning(" Failed to handle Turnstile widgets")
            
            return success
            
        except Exception as e:
            logger.error(f"Error testing URL {url}: {e}")
            return False


# Example usage and test functions
async def test_turnstile_sites():
    """Test the detector on known Turnstile sites"""
    
    test_urls = [
        "https://demo.turnstile.workers.dev/",  # Official Turnstile demo
        "https://2captcha.com/demo/cloudflare-turnstile",  # Testing site
        # Add more test URLs as needed
    ]
    
    async with TurnstileTester(headless=False, debug=True) as tester:
        for url in test_urls:
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing: {url}")
            logger.info(f"{'='*50}")
            
            success = await tester.test_url(url)
            
            if success:
                logger.info(f" {url} - SUCCESS")
            else:
                logger.warning(f" {url} - FAILED")
            
            # Wait between tests
            await asyncio.sleep(3)


async def test_custom_site(url: str, headless: bool = False):
    """Test a custom site for Turnstile widgets"""
    async with TurnstileTester(headless=headless, debug=True) as tester:
        return await tester.test_url(url)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific URL
        url = sys.argv[1]
        headless = "--headless" in sys.argv
        
        result = asyncio.run(test_custom_site(url, headless=headless))
        
        if result:
            print(f" Successfully handled Turnstile on {url}")
            sys.exit(0)
        else:
            print(f" Failed to handle Turnstile on {url}")
            sys.exit(1)
    else:
        # Run demo tests
        asyncio.run(test_turnstile_sites())
