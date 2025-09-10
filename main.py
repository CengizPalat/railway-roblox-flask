#!/usr/bin/env python3
"""
RAILWAY FLASK SERVER - COMPLETE WITH BROWSER VERIFICATION FIX
File: main.py
FIXED: Handles Cloudflare "Verifying browser..." challenge + Cookie consent
"""

import os
import time
import json
import base64
import threading
import asyncio
import random
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for zrdgames.com
CORS(app, origins=[
    "https://zrdgames.com",
    "https://www.zrdgames.com",
    "http://localhost:3000",
    "http://localhost:8080"
], methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type'])

# Configuration
PORT = int(os.getenv('PORT', 8080))
ALT_USERNAME = os.getenv('ALT_ROBLOX_USERNAME', 'ByddyY8rPao2124')
ALT_PASSWORD = os.getenv('ALT_ROBLOX_PASSWORD')
SPARKEDHOSTING_API = os.getenv('SPARKEDHOSTING_API_URL', 'https://roblox.sparked.network/api')

# Selenium Grid URLs with PORT 4444
SELENIUM_GRID_URLS = [
    # Option 1: Simple service name (Railway's preferred internal networking)
    'http://standalone-chrome:4444/wd/hub',
    
    # Option 2: External URL (guaranteed fallback)  
    'https://standalone-chrome-production-eb24.up.railway.app/wd/hub',
    
    # Option 3: Full internal format
    'http://standalone-chrome.railway.internal:4444/wd/hub',
    
    # Option 4: Alternative internal format
    'http://standalone-chrome-production-eb24.railway.internal:4444/wd/hub'
]

# Store the working URL once found
WORKING_SELENIUM_URL = None

# Store for diagnostic results
diagnostic_results = {}

def find_working_selenium_url():
    """Test multiple Selenium URLs to find the working one"""
    global WORKING_SELENIUM_URL
    
    if WORKING_SELENIUM_URL:
        return WORKING_SELENIUM_URL
    
    logger.info("Testing Selenium Grid URLs (port 4444)...")
    
    for i, url in enumerate(SELENIUM_GRID_URLS):
        try:
            logger.info(f"Testing URL {i+1}/{len(SELENIUM_GRID_URLS)}: {url}")
            
            # Test status endpoint first
            status_url = url.replace('/wd/hub', '/status')
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get('value', {}).get('ready'):
                    logger.info(f"Found working Selenium URL: {url}")
                    WORKING_SELENIUM_URL = url
                    return url
                else:
                    logger.warning(f"URL {url} responded but not ready")
            else:
                logger.warning(f"URL {url} returned HTTP {response.status_code}")
                
        except Exception as e:
            logger.warning(f"URL {url} failed: {str(e)[:100]}")
            continue
    
    # If no status endpoint works, try direct WebDriver connection
    logger.info("Status endpoints failed, trying direct WebDriver connections...")
    
    for i, url in enumerate(SELENIUM_GRID_URLS):
        try:
            logger.info(f"Direct test {i+1}/{len(SELENIUM_GRID_URLS)}: {url}")
            
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--headless")
            
            driver = webdriver.Remote(
                command_executor=url,
                options=options
            )
            
            # Simple test
            driver.get("https://httpbin.org/ip")
            driver.quit()
            
            logger.info(f"Found working Selenium URL via WebDriver: {url}")
            WORKING_SELENIUM_URL = url
            return url
            
        except Exception as e:
            logger.warning(f"Direct WebDriver test failed for {url}: {str(e)[:100]}")
            continue
    
    logger.error("No working Selenium Grid URL found!")
    return None

class RobloxLoginDiagnostics:
    """Advanced Roblox login diagnostics with Browser Verification + Cookie Consent Fix"""
    
    def __init__(self):
        self.report_id = None
        self.selenium_url = find_working_selenium_url()
        self.debug_data = {
            'test_timestamp': datetime.utcnow().isoformat(),
            'selenium_url': self.selenium_url,
            'username': ALT_USERNAME,
            'screenshots': [],
            'page_sources': [],
            'steps_completed': [],
            'errors_encountered': [],
            'success': False
        }
    
    def get_chrome_options(self):
        """Enhanced Chrome options for better stealth and browser verification bypass"""
        options = Options()
        
        # Core Railway compatibility options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--headless")
        
        # Enhanced stealth options for browser verification
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-automation")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-web-resources")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-first-run")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--disable-ipc-flooding-protection")
        
        # Window and display settings
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # Enhanced user agent (more realistic)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Experimental options for better stealth
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth preferences
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,  # Disable images for speed
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    def capture_screenshot(self, driver, step_name):
        """Enhanced screenshot capture with error handling"""
        try:
            screenshot_data = driver.get_screenshot_as_base64()
            screenshot_info = {
                'step': step_name,
                'timestamp': datetime.utcnow().isoformat(),
                'data': screenshot_data,
                'url': driver.current_url,
                'title': driver.title
            }
            self.debug_data['screenshots'].append(screenshot_info)
            logger.info(f"Screenshot captured: {step_name}")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed for {step_name}: {e}")
            return False
    
    def capture_page_source(self, driver, step_name):
        """Enhanced page source capture"""
        try:
            page_source = driver.page_source
            source_info = {
                'step': step_name,
                'timestamp': datetime.utcnow().isoformat(),
                'content': page_source[:5000],  # First 5000 chars
                'full_length': len(page_source),
                'url': driver.current_url
            }
            self.debug_data['page_sources'].append(source_info)
            logger.info(f"Page source captured: {step_name}")
            return True
        except Exception as e:
            logger.error(f"Page source capture failed for {step_name}: {e}")
            return False
    
    def log_step(self, step_name, status, details=None):
        """Enhanced step logging"""
        step_data = {
            'step': step_name,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        self.debug_data['steps_completed'].append(step_data)
        logger.info(f"Step: {step_name} - {status}")
    
    def log_error(self, error_type, error_message, details=None):
        """Enhanced error logging"""
        error_data = {
            'type': error_type,
            'timestamp': datetime.utcnow().isoformat(),
            'message': str(error_message),
            'details': details or {}
        }
        self.debug_data['errors_encountered'].append(error_data)
        logger.error(f"Error: {error_type} - {error_message}")
    
    def handle_browser_verification(self, driver, max_wait_time=60):
        """CRITICAL NEW FIX: Handle Cloudflare 'Verifying browser...' challenge"""
        try:
            self.log_step("browser_verification_check", "starting")
            
            # Detection strategies for browser verification
            verification_indicators = [
                # Text-based detection
                ("xpath", "//text()[contains(., 'Verifying browser')]"),
                ("xpath", "//*[contains(text(), 'Verifying browser')]"),
                ("xpath", "//*[contains(text(), 'Checking your browser')]"),
                ("xpath", "//*[contains(text(), 'Please wait')]"),
                
                # Common Cloudflare selectors
                ("css", ".cf-browser-verification"),
                ("css", ".cf-checking-browser"),
                ("css", "#cf-spinner"),
                ("css", ".cf-spinner"),
                
                # Generic loading/verification patterns
                ("css", "[class*='verification']"),
                ("css", "[class*='checking']"),
                ("css", "[id*='verification']"),
                ("css", "[id*='checking']"),
                
                # Look for modals or overlays
                ("css", "div[style*='position: fixed']"),
                ("css", ".modal[style*='display: block']"),
                ("css", ".overlay:not([style*='display: none'])")
            ]
            
            verification_detected = False
            verification_element = None
            
            # Check if verification challenge is present
            for strategy_type, selector in verification_indicators:
                try:
                    elements = []
                    
                    if strategy_type == "xpath":
                        elements = driver.find_elements(By.XPATH, selector)
                    else:  # css
                        if ":not(" in selector:
                            # Handle complex CSS selectors
                            elements = driver.find_elements(By.CSS_SELECTOR, selector.split(":not(")[0])
                            # Filter out hidden elements
                            elements = [el for el in elements if el.is_displayed()]
                        else:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            verification_detected = True
                            verification_element = element
                            self.log_step("browser_verification_detected", "found", {
                                "selector": selector,
                                "element_text": element.text[:100] if hasattr(element, 'text') else '',
                                "strategy": strategy_type
                            })
                            break
                    
                    if verification_detected:
                        break
                        
                except Exception as e:
                    continue
            
            if not verification_detected:
                self.log_step("browser_verification_check", "none_found")
                return True
            
            # Browser verification detected - wait for it to complete
            self.capture_screenshot(driver, "browser_verification_detected")
            
            self.log_step("browser_verification_wait", "starting", {
                "max_wait_time": max_wait_time,
                "check_interval": 2
            })
            
            start_time = time.time()
            check_interval = 2
            
            while time.time() - start_time < max_wait_time:
                try:
                    # Check if verification is still present
                    still_verifying = False
                    
                    # Re-check all indicators
                    for strategy_type, selector in verification_indicators:
                        try:
                            elements = []
                            
                            if strategy_type == "xpath":
                                elements = driver.find_elements(By.XPATH, selector)
                            else:
                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            if any(el.is_displayed() for el in elements):
                                still_verifying = True
                                break
                                
                        except:
                            continue
                    
                    if not still_verifying:
                        # Check if we're back to normal page
                        current_url = driver.current_url
                        page_source = driver.page_source.lower()
                        
                        # Look for signs verification completed
                        if ("login" in current_url.lower() and 
                            "verifying" not in page_source and 
                            "checking" not in page_source):
                            
                            elapsed_time = time.time() - start_time
                            self.log_step("browser_verification_wait", "completed", {
                                "time_elapsed": round(elapsed_time, 2),
                                "final_url": current_url
                            })
                            self.capture_screenshot(driver, "browser_verification_completed")
                            return True
                    
                    # Add random delay to appear more human
                    time.sleep(check_interval + random.uniform(0.5, 1.5))
                    
                    # Log progress every 10 seconds
                    elapsed = time.time() - start_time
                    if elapsed % 10 < check_interval:
                        self.log_step("browser_verification_progress", "waiting", {
                            "elapsed_seconds": round(elapsed, 1),
                            "remaining_seconds": round(max_wait_time - elapsed, 1)
                        })
                    
                except Exception as e:
                    logger.warning(f"Error during verification wait: {e}")
                    time.sleep(2)
                    continue
            
            # Timeout reached
            self.log_step("browser_verification_wait", "timeout", {
                "timeout_seconds": max_wait_time,
                "final_url": driver.current_url
            })
            self.capture_screenshot(driver, "browser_verification_timeout")
            
            # Try to proceed anyway - sometimes verification completes but indicators remain
            return False
            
        except Exception as e:
            self.log_error("browser_verification_handling", f"Error handling browser verification: {e}")
            self.capture_screenshot(driver, "browser_verification_error")
            return False
    
    def handle_cookie_consent(self, driver):
        """Handle Roblox cookie consent banner"""
        try:
            self.log_step("cookie_consent_check", "starting")
            
            # Wait a moment for the banner to appear
            time.sleep(2)
            
            # Look for cookie consent buttons with multiple strategies
            cookie_strategies = [
                # Strategy 1: Direct text search
                ("xpath", "//button[contains(text(), 'Accept All')]"),
                ("xpath", "//button[contains(text(), 'Decline All')]"),
                
                # Strategy 2: Common CSS selectors
                ("css", "button[data-testid='accept-all']"),
                ("css", "button[data-testid='decline-all']"),
                ("css", ".cookie-consent button"),
                ("css", "#cookie-consent button"),
                
                # Strategy 3: Aria labels
                ("css", "button[aria-label*='cookie']"),
                ("css", "button[aria-label*='Accept']"),
                ("css", "button[aria-label*='Decline']"),
            ]
            
            button_found = False
            
            for strategy_type, selector in cookie_strategies:
                try:
                    buttons = []
                    
                    if strategy_type == "xpath":
                        buttons = driver.find_elements(By.XPATH, selector)
                    else:  # css
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            try:
                                # Scroll to button first
                                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)
                                
                                # Get button info for logging
                                button_text = button.text or button.get_attribute('aria-label') or 'Cookie Button'
                                
                                # Try regular click first
                                try:
                                    button.click()
                                    self.log_step("cookie_consent_click", "success", {
                                        "button_text": button_text,
                                        "method": "regular_click",
                                        "selector": selector
                                    })
                                    button_found = True
                                    break
                                except Exception:
                                    # Try JavaScript click as fallback
                                    driver.execute_script("arguments[0].click();", button)
                                    self.log_step("cookie_consent_click", "success_js", {
                                        "button_text": button_text,
                                        "method": "javascript_click", 
                                        "selector": selector
                                    })
                                    button_found = True
                                    break
                                    
                            except Exception as click_error:
                                logger.warning(f"Failed to click button: {click_error}")
                                continue
                    
                    if button_found:
                        break
                        
                except Exception as e:
                    logger.warning(f"Strategy {strategy_type} with selector {selector} failed: {e}")
                    continue
            
            if button_found:
                # Wait for banner to disappear
                time.sleep(2)
                self.capture_screenshot(driver, "cookie_consent_handled")
                self.log_step("cookie_consent_check", "success", {"banner_dismissed": True})
                return True
            else:
                # No cookie banner found - that's also fine
                self.log_step("cookie_consent_check", "none_found", {"banner_present": False})
                return True
                
        except Exception as e:
            self.log_error("cookie_consent_handling", f"Error handling cookies: {e}")
            self.capture_screenshot(driver, "cookie_consent_error")
            return False
    
    def test_selenium_connection(self):
        """Test Selenium Grid connection with the working URL"""
        if not self.selenium_url:
            logger.error("No working Selenium URL available")
            return False
            
        logger.info(f"Testing Selenium connection to: {self.selenium_url}")
        
        try:
            options = self.get_chrome_options()
            
            driver = webdriver.Remote(
                command_executor=self.selenium_url,
                options=options
            )
            
            # Simple test
            driver.get("https://httpbin.org/ip")
            driver.quit()
            
            logger.info("Selenium connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Selenium connection test failed: {e}")
            return False
    
    def run_full_diagnostic(self):
        """COMPLETE login diagnostic workflow WITH browser verification + cookie consent fix"""
        self.report_id = f"diagnostic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        driver = None
        
        if not self.selenium_url:
            self.log_error("selenium_url", "No working Selenium Grid URL found", {
                "attempted_urls": SELENIUM_GRID_URLS,
                "recommendation": "Check Railway services and networking configuration"
            })
            return self.generate_diagnostic_report()
        
        try:
            # Step 1: Test Selenium connection
            self.log_step("selenium_connectivity_test", "starting", {"grid_url": self.selenium_url})
            
            if not self.test_selenium_connection():
                self.log_error("selenium_connection", "Failed to connect to Selenium Grid", {
                    "grid_url": self.selenium_url,
                    "recommendation": "Check Railway service status and networking"
                })
                return self.generate_diagnostic_report()
            
            self.log_step("selenium_connectivity_test", "success")
            
            # Step 2: Initialize Selenium WebDriver with enhanced stealth
            self.log_step("selenium_init", "starting", {"grid_url": self.selenium_url})
            
            options = self.get_chrome_options()
            driver = webdriver.Remote(
                command_executor=self.selenium_url,
                options=options
            )
            
            # Configure timeouts
            driver.set_page_load_timeout(60)  # Increased for verification challenges
            driver.implicitly_wait(10)
            
            # Execute stealth JavaScript to hide automation indicators
            stealth_js = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                window.chrome = {
                    runtime: {},
                };
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """
            driver.execute_script(stealth_js)
            
            self.log_step("selenium_init", "success", {"browser": "Chrome", "version": "120", "stealth": True})
            self.capture_screenshot(driver, "selenium_initialized")
            
            # Step 3: Navigate to Roblox with human-like behavior
            self.log_step("roblox_navigation", "starting")
            
            # Add random delay to appear more human
            time.sleep(random.uniform(1, 3))
            
            driver.get("https://www.roblox.com/login")
            
            # Wait for initial page load
            time.sleep(random.uniform(3, 5))
            
            self.log_step("roblox_navigation", "success", {"url": driver.current_url})
            self.capture_screenshot(driver, "roblox_login_page")
            self.capture_page_source(driver, "login_page_source")
            
            # Step 4: Handle cookie consent FIRST!
            self.handle_cookie_consent(driver)
            
            # Step 5: CRITICAL NEW - Handle browser verification challenge
            verification_handled = self.handle_browser_verification(driver, max_wait_time=90)
            
            if not verification_handled:
                self.log_error("browser_verification", "Browser verification challenge timed out", {
                    "recommendation": "Consider using residential proxy or different browser fingerprint"
                })
                # Continue anyway - sometimes verification completes but indicators remain
            
            # Step 6: Analyze login form (after all challenges handled)
            self.log_step("login_form_analysis", "starting")
            
            try:
                # Add delay to ensure page is fully loaded
                time.sleep(random.uniform(2, 4))
                
                # Use flexible selectors for form elements
                username_field = None
                password_field = None
                login_button = None
                
                # Find username field with multiple selectors
                username_selectors = [
                    "#login-username",
                    "input[placeholder*='Username']",
                    "input[name='username']", 
                    "input[type='text']"
                ]
                
                for selector in username_selectors:
                    try:
                        username_field = driver.find_element(By.CSS_SELECTOR, selector)
                        if username_field.is_displayed():
                            break
                    except:
                        continue
                
                # Find password field with multiple selectors  
                password_selectors = [
                    "#login-password",
                    "input[placeholder*='Password']",
                    "input[name='password']",
                    "input[type='password']"
                ]
                
                for selector in password_selectors:
                    try:
                        password_field = driver.find_element(By.CSS_SELECTOR, selector)
                        if password_field.is_displayed():
                            break
                    except:
                        continue
                
                # Find login button with multiple selectors
                login_selectors = [
                    "#login-button",
                    "button[type='submit']",
                    "input[type='submit']"
                ]
                
                for selector in login_selectors:
                    try:
                        login_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if login_button.is_displayed():
                            break
                    except:
                        continue
                
                # Also try XPath for "Log In" text
                if not login_button:
                    try:
                        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]")
                    except:
                        pass
                
                form_analysis = {
                    "username_field_found": username_field is not None,
                    "password_field_found": password_field is not None,
                    "login_button_found": login_button is not None,
                    "page_title": driver.title,
                    "current_url": driver.current_url
                }
                
                self.log_step("login_form_analysis", "success", form_analysis)
                self.capture_screenshot(driver, "login_form_analyzed")
                
            except Exception as e:
                self.log_error("form_analysis", f"Login form elements not found: {e}")
                self.capture_screenshot(driver, "login_form_error")
                
            # Step 7: Attempt login (with all challenges handled)
            self.log_step("login_attempt", "starting")
            
            try:
                if not ALT_PASSWORD:
                    raise ValueError("ALT_ROBLOX_PASSWORD not configured")
                
                if not username_field or not password_field or not login_button:
                    raise ValueError("Required form elements not found")
                
                # Human-like typing with realistic delays
                username_field.clear()
                time.sleep(random.uniform(0.5, 1.0))
                
                # Type username character by character with delays
                for char in ALT_USERNAME:
                    username_field.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                
                time.sleep(random.uniform(0.5, 1.5))
                
                # Type password character by character with delays
                password_field.clear()
                time.sleep(random.uniform(0.5, 1.0))
                
                for char in ALT_PASSWORD:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                
                time.sleep(random.uniform(1.0, 2.0))
                
                self.capture_screenshot(driver, "credentials_entered")
                
                # Scroll to login button and ensure it's visible
                driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                time.sleep(random.uniform(0.5, 1.0))
                
                # Attempt to click login button
                try:
                    login_button.click()
                    self.log_step("login_button_click", "success", {"method": "regular_click"})
                except Exception as click_error:
                    # Try JavaScript click as fallback
                    driver.execute_script("arguments[0].click();", login_button)
                    self.log_step("login_button_click", "success_js", {"method": "javascript_click"})
                
                self.capture_screenshot(driver, "login_button_clicked")
                
                # Wait for login processing with longer timeout
                time.sleep(random.uniform(5, 8))
                
                # Check result
                current_url = driver.current_url
                page_source = driver.page_source.lower()
                
                # Success indicators
                if any(indicator in current_url.lower() for indicator in ['home', 'dashboard', 'profile']):
                    self.log_step("login_attempt", "success", {"redirect_url": current_url})
                    self.debug_data['success'] = True
                elif "login" not in current_url.lower():
                    self.log_step("login_attempt", "success", {"redirect_url": current_url})
                    self.debug_data['success'] = True
                else:
                    # Analyze failure reason
                    failure_reason = "unknown"
                    if any(keyword in page_source for keyword in ['captcha', 'recaptcha', 'verify']):
                        failure_reason = "captcha_required"
                    elif any(keyword in page_source for keyword in ['two-factor', '2fa', 'verification']):
                        failure_reason = "2fa_required"
                    elif any(keyword in page_source for keyword in ['incorrect', 'invalid', 'wrong']):
                        failure_reason = "invalid_credentials"
                    elif any(keyword in page_source for keyword in ['locked', 'suspended', 'disabled']):
                        failure_reason = "account_locked"
                    elif any(keyword in page_source for keyword in ['verifying', 'checking']):
                        failure_reason = "browser_verification_persistent"
                    
                    self.log_step("login_attempt", "failed", {
                        "stayed_on_login": True,
                        "failure_reason": failure_reason
                    })
                
                self.capture_screenshot(driver, "login_attempt_result")
                
            except Exception as e:
                self.log_error("login_execution", f"Login attempt failed: {e}")
                self.capture_screenshot(driver, "login_execution_error")
            
            # Step 8: Final analysis
            self.log_step("final_analysis", "starting")
            
            try:
                final_state = {
                    "current_url": driver.current_url,
                    "page_title": driver.title,
                    "login_success": self.debug_data['success'],
                    "total_screenshots": len(self.debug_data['screenshots']),
                    "total_errors": len(self.debug_data['errors_encountered'])
                }
                
                self.log_step("final_analysis", "completed", final_state)
                self.capture_screenshot(driver, "final_state")
                
            except Exception as e:
                self.log_error("final_analysis", f"Final analysis failed: {e}")
                
        except Exception as e:
            self.log_error("diagnostic_workflow", f"Critical diagnostic failure: {e}")
            
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("WebDriver cleaned up")
                except:
                    pass
        
        return self.generate_diagnostic_report()
    
    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        total_steps = len(self.debug_data['steps_completed'])
        total_errors = len(self.debug_data['errors_encountered'])
        screenshots_captured = len(self.debug_data['screenshots'])
        
        # Enhanced diagnosis logic
        if self.debug_data['success']:
            diagnosis = "LOGIN_SUCCESS"
            recommended_actions = ["Monitor for consistency", "Account is functioning normally"]
        elif not self.selenium_url:
            diagnosis = "SELENIUM_URL_RESOLUTION_FAILURE"
            recommended_actions = [
                "Check Railway internal networking configuration",
                "Verify standalone-chrome service is running on port 4444"
            ]
        elif any(error['type'] == 'browser_verification' for error in self.debug_data['errors_encountered']):
            diagnosis = "BROWSER_VERIFICATION_TIMEOUT"
            recommended_actions = [
                "Cloudflare browser verification challenge timed out",
                "Consider using residential proxy with different IP",
                "Try non-headless browser for manual verification",
                "Implement CAPTCHA solving service integration",
                "Add more realistic browser fingerprinting"
            ]
        elif any('password' in str(error).lower() for error in self.debug_data['errors_encountered']):
            diagnosis = "AUTHENTICATION_FAILURE"
            recommended_actions = [
                "Verify ALT_ROBLOX_PASSWORD environment variable",
                "Check account status manually",
                "Try manual login to confirm account status"
            ]
        else:
            # Check if browser verification was detected in steps
            browser_verification_detected = any(
                'browser_verification' in step.get('step', '') 
                for step in self.debug_data['steps_completed']
            )
            
            if browser_verification_detected:
                diagnosis = "BROWSER_VERIFICATION_CHALLENGE"
                recommended_actions = [
                    "Cloudflare detected automated browser",
                    "Browser verification challenge appeared",
                    "System waited for challenge completion",
                    "Consider alternative automation approaches",
                    "Review browser fingerprinting techniques"
                ]
            else:
                diagnosis = "GENERAL_LOGIN_FAILURE"
                recommended_actions = [
                    "Check for account suspension",
                    "Verify credentials are correct",
                    "Check for 2FA requirements",
                    "Review screenshots for specific error messages"
                ]
        
        report = {
            'report_id': self.report_id,
            'diagnostic_summary': {
                'test_timestamp': self.debug_data['test_timestamp'],
                'final_diagnosis': diagnosis,
                'total_steps_completed': total_steps,
                'total_errors_encountered': total_errors,
                'screenshots_captured': screenshots_captured,
                'login_success': self.debug_data['success'],
                'recommended_actions': recommended_actions
            },
            'test_environment': {
                'selenium_grid_url': self.selenium_url,
                'attempted_urls': SELENIUM_GRID_URLS,
                'working_url_found': self.selenium_url is not None,
                'username_tested': ALT_USERNAME,
                'browser': "Chrome/120.0.0.0",
                'railway_environment': True,
                'cookie_consent_handling': True,
                'browser_verification_handling': True,
                'stealth_mode': True
            },
            'detailed_steps': self.debug_data['steps_completed'],
            'errors_log': self.debug_data['errors_encountered'],
            'screenshots': self.debug_data['screenshots'],
            'page_sources': self.debug_data['page_sources']
        }
        
        return report

# Flask Routes

@app.route('/status', methods=['GET'])
def health_check():
    """Health check with Selenium Grid testing"""
    
    # Test all Selenium URLs and return detailed status
    selenium_status = "failed"
    selenium_details = {
        "attempted_urls": [],
        "working_url": None,
        "error_details": {}
    }
    
    working_url = find_working_selenium_url()
    
    if working_url:
        selenium_status = "ok"
        selenium_details["working_url"] = working_url
        
        # Test the working URL
        try:
            status_url = working_url.replace('/wd/hub', '/status')
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                selenium_details["grid_ready"] = status_data.get('value', {}).get('ready', False)
                selenium_details["nodes"] = len(status_data.get('value', {}).get('nodes', []))
            
        except Exception as e:
            selenium_details["status_check_error"] = str(e)[:100]
    else:
        # Record details about failures
        for url in SELENIUM_GRID_URLS:
            try:
                status_url = url.replace('/wd/hub', '/status')
                response = requests.get(status_url, timeout=5)
                selenium_details["error_details"][url] = f"HTTP_{response.status_code}"
            except Exception as e:
                selenium_details["error_details"][url] = str(e)[:100]
    
    selenium_details["attempted_urls"] = SELENIUM_GRID_URLS
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'selenium_grid': selenium_status,
        'selenium_details': selenium_details,
        'selenium_url': working_url,
        'environment': 'railway',
        'version': '6.0-browser-verification-fix'
    })

@app.route('/trigger-diagnostic', methods=['POST'])
def trigger_diagnostic():
    """Trigger diagnostic with browser verification + cookie consent handling"""
    try:
        logger.info("Starting diagnostic trigger (with browser verification + cookie consent fix)")
        
        # Validate environment
        if not ALT_PASSWORD:
            return jsonify({
                'success': False,
                'error': 'ALT_ROBLOX_PASSWORD not configured',
                'required_env_vars': ['ALT_ROBLOX_PASSWORD']
            }), 400
        
        # Quick pre-check of Selenium connection
        working_url = find_working_selenium_url()
        if not working_url:
            return jsonify({
                'success': False,
                'error': 'No working Selenium Grid URL found',
                'attempted_urls': SELENIUM_GRID_URLS,
                'recommendation': 'Check Railway services and networking'
            }), 503
        
        # Run diagnostic in background thread
        def run_diagnostic():
            try:
                diagnostics = RobloxLoginDiagnostics()
                report = diagnostics.run_full_diagnostic()
                
                # Store result
                diagnostic_results[diagnostics.report_id] = report
                
                # Upload to SparkedHosting API
                try:
                    upload_response = requests.post(
                        f"{SPARKEDHOSTING_API}/diagnostic-report",
                        json=report,
                        timeout=30
                    )
                    if upload_response.status_code == 200:
                        logger.info("Report uploaded to SparkedHosting")
                    else:
                        logger.error(f"Upload failed: {upload_response.status_code}")
                except Exception as upload_error:
                    logger.error(f"Upload error: {upload_error}")
                
            except Exception as e:
                logger.error(f"Diagnostic error: {e}")
        
        # Start diagnostic in background
        diagnostic_thread = threading.Thread(target=run_diagnostic)
        diagnostic_thread.daemon = True
        diagnostic_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Diagnostic started (with browser verification + cookie consent handling)',
            'selenium_url': working_url,
            'estimated_duration': '90-180 seconds',
            'check_results_at': '/results',
            'features': [
                'cookie_consent_handling', 
                'browser_verification_handling',
                'cloudflare_challenge_support',
                'enhanced_stealth_mode',
                'human_like_typing',
                'multiple_selectors'
            ]
        })
        
    except Exception as e:
        logger.error(f"Trigger error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/results', methods=['GET'])
def get_results():
    """Get latest diagnostic results"""
    try:
        if not diagnostic_results:
            return jsonify({
                'success': False,
                'message': 'No diagnostic results available',
                'available_reports': 0
            })
        
        # Get most recent result
        latest_report_id = max(diagnostic_results.keys())
        latest_report = diagnostic_results[latest_report_id]
        
        return jsonify({
            'success': True,
            'report': latest_report,
            'total_reports': len(diagnostic_results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/results/<report_id>', methods=['GET'])
def get_specific_result(report_id):
    """Get specific diagnostic result by ID"""
    try:
        if report_id not in diagnostic_results:
            return jsonify({
                'success': False,
                'error': 'Report not found',
                'available_reports': list(diagnostic_results.keys())
            }), 404
        
        return jsonify({
            'success': True,
            'report': diagnostic_results[report_id]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def simple_health():
    """Simple health check for Railway"""
    return jsonify({
        'status': 'healthy',
        'service': 'roblox-analytics-flask',
        'timestamp': datetime.utcnow().isoformat()
    })

# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': ['/status', '/trigger-diagnostic', '/results', '/health']
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'Check logs for details'
    }), 500

# Main application
if __name__ == '__main__':
    logger.info("Starting Railway Flask Server (Browser Verification + Cookie Consent Fix)")
    logger.info(f"Testing Selenium URLs: {SELENIUM_GRID_URLS}")
    
    # Test Selenium connection on startup
    working_url = find_working_selenium_url()
    if working_url:
        logger.info(f"Found working Selenium URL: {working_url}")
    else:
        logger.error("No working Selenium URL found at startup")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
