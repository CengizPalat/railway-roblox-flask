#!/usr/bin/env python3
"""
RAILWAY FLASK SERVER - UNDETECTED CHROMEDRIVER SOLUTION
File: main.py
PROVEN FIX: Uses undetected-chromedriver to bypass Cloudflare challenges
Based on 2024-2025 forum solutions that work against current Cloudflare
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

# CRITICAL: Import undetected_chromedriver instead of regular selenium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Store for diagnostic results
diagnostic_results = {}

class RobloxLoginDiagnostics:
    """Advanced Roblox login diagnostics with UNDETECTED CHROMEDRIVER"""
    
    def __init__(self):
        self.report_id = None
        self.debug_data = {
            'test_timestamp': datetime.utcnow().isoformat(),
            'username': ALT_USERNAME,
            'screenshots': [],
            'page_sources': [],
            'steps_completed': [],
            'errors_encountered': [],
            'success': False
        }
    
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
    
    def handle_cookie_consent(self, driver):
        """Handle Roblox cookie consent banner"""
        try:
            self.log_step("cookie_consent_check", "starting")
            time.sleep(2)
            
            cookie_strategies = [
                ("xpath", "//button[contains(text(), 'Accept All')]"),
                ("xpath", "//button[contains(text(), 'Decline All')]"),
                ("css", "button[data-testid='accept-all']"),
                ("css", "button[data-testid='decline-all']"),
            ]
            
            button_found = False
            
            for strategy_type, selector in cookie_strategies:
                try:
                    buttons = []
                    
                    if strategy_type == "xpath":
                        buttons = driver.find_elements(By.XPATH, selector)
                    else:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            try:
                                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)
                                
                                button_text = button.text or 'Cookie Button'
                                
                                try:
                                    button.click()
                                    self.log_step("cookie_consent_click", "success", {
                                        "button_text": button_text,
                                        "method": "regular_click"
                                    })
                                    button_found = True
                                    break
                                except Exception:
                                    driver.execute_script("arguments[0].click();", button)
                                    self.log_step("cookie_consent_click", "success_js", {
                                        "button_text": button_text,
                                        "method": "javascript_click"
                                    })
                                    button_found = True
                                    break
                                    
                            except Exception as click_error:
                                continue
                    
                    if button_found:
                        break
                        
                except Exception as e:
                    continue
            
            if button_found:
                time.sleep(2)
                self.capture_screenshot(driver, "cookie_consent_handled")
                self.log_step("cookie_consent_check", "success")
                return True
            else:
                self.log_step("cookie_consent_check", "none_found")
                return True
                
        except Exception as e:
            self.log_error("cookie_consent_handling", f"Error handling cookies: {e}")
            return False
    
    def wait_for_cloudflare_challenge(self, driver, max_wait_time=120):
        """ENHANCED: Wait for Cloudflare challenge with undetected chromedriver"""
        try:
            self.log_step("cloudflare_challenge_wait", "starting", {"max_wait_time": max_wait_time})
            
            # Cloudflare challenge indicators
            challenge_indicators = [
                "verifying browser",
                "checking your browser", 
                "please wait",
                "cloudflare",
                "security check"
            ]
            
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    current_url = driver.current_url.lower()
                    page_source = driver.page_source.lower()
                    page_title = driver.title.lower()
                    
                    # Check if challenge is present
                    challenge_detected = any(
                        indicator in page_source or 
                        indicator in page_title or
                        indicator in current_url
                        for indicator in challenge_indicators
                    )
                    
                    if not challenge_detected:
                        # Check if we're on the target page
                        if "login" in current_url and "roblox.com" in current_url:
                            elapsed_time = time.time() - start_time
                            self.log_step("cloudflare_challenge_wait", "completed", {
                                "time_elapsed": round(elapsed_time, 2),
                                "final_url": driver.current_url
                            })
                            self.capture_screenshot(driver, "cloudflare_challenge_passed")
                            return True
                    
                    # Add human-like delay
                    time.sleep(random.uniform(2, 4))
                    
                    # Log progress every 10 seconds
                    elapsed = time.time() - start_time
                    if elapsed % 10 < 3:
                        self.log_step("cloudflare_challenge_progress", "waiting", {
                            "elapsed_seconds": round(elapsed, 1),
                            "remaining_seconds": round(max_wait_time - elapsed, 1)
                        })
                        self.capture_screenshot(driver, f"cloudflare_wait_{int(elapsed//10)}")
                    
                except Exception as e:
                    logger.warning(f"Error during challenge wait: {e}")
                    time.sleep(2)
                    continue
            
            # Timeout reached
            self.log_step("cloudflare_challenge_wait", "timeout", {
                "timeout_seconds": max_wait_time
            })
            self.capture_screenshot(driver, "cloudflare_challenge_timeout")
            return False
            
        except Exception as e:
            self.log_error("cloudflare_challenge_handling", f"Error handling challenge: {e}")
            return False
    
    def run_full_diagnostic(self):
        """COMPLETE diagnostic with UNDETECTED CHROMEDRIVER"""
        self.report_id = f"diagnostic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        driver = None
        
        try:
            # Step 1: Initialize UNDETECTED ChromeDriver
            self.log_step("undetected_chrome_init", "starting")
            
            # CRITICAL: Use undetected_chromedriver instead of regular selenium
            options = uc.ChromeOptions()
            
            # Essential options for Railway/headless environment
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--headless")  # Required for Railway
            
            # Additional stealth options (undetected_chromedriver handles most automatically)
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            
            # Initialize undetected ChromeDriver
            driver = uc.Chrome(
                options=options,
                headless=True,
                use_subprocess=False,  # Important for Railway
                version_main=None  # Auto-detect Chrome version
            )
            
            # Configure timeouts
            driver.set_page_load_timeout(120)
            driver.implicitly_wait(10)
            
            self.log_step("undetected_chrome_init", "success", {
                "driver_type": "undetected_chromedriver",
                "headless": True,
                "version": "auto-detected"
            })
            self.capture_screenshot(driver, "undetected_chrome_initialized")
            
            # Step 2: Navigate to Roblox with human-like behavior
            self.log_step("roblox_navigation", "starting")
            
            # Add random delay
            time.sleep(random.uniform(2, 5))
            
            driver.get("https://www.roblox.com/login")
            
            # Wait for initial page load
            time.sleep(random.uniform(3, 6))
            
            self.log_step("roblox_navigation", "success", {"url": driver.current_url})
            self.capture_screenshot(driver, "roblox_login_page_reached")
            
            # Step 3: Handle cookie consent
            self.handle_cookie_consent(driver)
            
            # Step 4: CRITICAL - Wait for Cloudflare challenge to complete
            challenge_passed = self.wait_for_cloudflare_challenge(driver, max_wait_time=120)
            
            if not challenge_passed:
                self.log_error("cloudflare_challenge", "Challenge did not complete within timeout")
                # Continue anyway - undetected_chromedriver might have bypassed it
            
            # Step 5: Analyze login form
            self.log_step("login_form_analysis", "starting")
            
            try:
                # Add delay to ensure page is fully loaded
                time.sleep(random.uniform(3, 5))
                
                # Find form elements with flexible selectors
                username_field = None
                password_field = None
                login_button = None
                
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
                
            # Step 6: Attempt login with human-like typing
            self.log_step("login_attempt", "starting")
            
            try:
                if not ALT_PASSWORD:
                    raise ValueError("ALT_ROBLOX_PASSWORD not configured")
                
                if not username_field or not password_field or not login_button:
                    raise ValueError("Required form elements not found")
                
                # Human-like typing with realistic delays
                username_field.clear()
                time.sleep(random.uniform(0.5, 1.0))
                
                # Type username character by character
                for char in ALT_USERNAME:
                    username_field.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                
                time.sleep(random.uniform(1.0, 2.0))
                
                # Type password character by character
                password_field.clear()
                time.sleep(random.uniform(0.5, 1.0))
                
                for char in ALT_PASSWORD:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                
                time.sleep(random.uniform(1.0, 2.0))
                
                self.capture_screenshot(driver, "credentials_entered")
                
                # Click login button
                driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                time.sleep(random.uniform(0.5, 1.0))
                
                try:
                    login_button.click()
                    self.log_step("login_button_click", "success", {"method": "regular_click"})
                except Exception:
                    driver.execute_script("arguments[0].click();", login_button)
                    self.log_step("login_button_click", "success_js", {"method": "javascript_click"})
                
                self.capture_screenshot(driver, "login_button_clicked")
                
                # Wait for login processing
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
                    
                    self.log_step("login_attempt", "failed", {
                        "stayed_on_login": True,
                        "failure_reason": failure_reason
                    })
                
                self.capture_screenshot(driver, "login_attempt_result")
                
            except Exception as e:
                self.log_error("login_execution", f"Login attempt failed: {e}")
                self.capture_screenshot(driver, "login_execution_error")
            
            # Step 7: Final analysis
            self.log_step("final_analysis", "starting")
            
            try:
                final_state = {
                    "current_url": driver.current_url,
                    "page_title": driver.title,
                    "login_success": self.debug_data['success'],
                    "total_screenshots": len(self.debug_data['screenshots']),
                    "total_errors": len(self.debug_data['errors_encountered']),
                    "undetected_chromedriver": True
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
                    logger.info("Undetected ChromeDriver cleaned up")
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
            diagnosis = "LOGIN_SUCCESS_WITH_UNDETECTED_CHROMEDRIVER"
            recommended_actions = ["Monitor for consistency", "Undetected ChromeDriver working correctly"]
        elif any('cloudflare' in str(step.get('step', '')).lower() for step in self.debug_data['steps_completed']):
            cloudflare_passed = any(
                step.get('status') == 'completed' and 'cloudflare' in step.get('step', '') 
                for step in self.debug_data['steps_completed']
            )
            if cloudflare_passed:
                diagnosis = "CLOUDFLARE_BYPASSED_BUT_LOGIN_FAILED"
                recommended_actions = [
                    "Undetected ChromeDriver successfully bypassed Cloudflare",
                    "Check account credentials and status",
                    "Look for CAPTCHA or 2FA requirements in screenshots"
                ]
            else:
                diagnosis = "CLOUDFLARE_CHALLENGE_PERSISTENT"
                recommended_actions = [
                    "Cloudflare challenge detected by undetected ChromeDriver",
                    "Try increasing wait time or using different IP",
                    "Consider SeleniumBase as alternative",
                    "May need non-headless mode for advanced challenges"
                ]
        else:
            diagnosis = "GENERAL_LOGIN_FAILURE_WITH_UNDETECTED_CHROMEDRIVER"
            recommended_actions = [
                "Undetected ChromeDriver initialized successfully",
                "Check for specific error messages in screenshots",
                "Verify account credentials and status"
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
                'driver_type': 'undetected_chromedriver',
                'username_tested': ALT_USERNAME,
                'browser': "Undetected Chrome",
                'railway_environment': True,
                'cloudflare_bypass_attempted': True,
                'human_like_behavior': True
            },
            'detailed_steps': self.debug_data['steps_completed'],
            'errors_log': self.debug_data['errors_encountered'],
            'screenshots': self.debug_data['screenshots'],
            'page_sources': self.debug_data['page_sources']
        }
        
        return report

# Flask Routes (same as before, just updated version)

@app.route('/status', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'driver_type': 'undetected_chromedriver',
        'environment': 'railway',
        'version': '7.0-undetected-chromedriver'
    })

@app.route('/trigger-diagnostic', methods=['POST'])
def trigger_diagnostic():
    """Trigger diagnostic with UNDETECTED CHROMEDRIVER"""
    try:
        logger.info("Starting diagnostic with UNDETECTED CHROMEDRIVER")
        
        if not ALT_PASSWORD:
            return jsonify({
                'success': False,
                'error': 'ALT_ROBLOX_PASSWORD not configured'
            }), 400
        
        def run_diagnostic():
            try:
                diagnostics = RobloxLoginDiagnostics()
                report = diagnostics.run_full_diagnostic()
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
                except Exception as upload_error:
                    logger.error(f"Upload error: {upload_error}")
                
            except Exception as e:
                logger.error(f"Diagnostic error: {e}")
        
        diagnostic_thread = threading.Thread(target=run_diagnostic)
        diagnostic_thread.daemon = True
        diagnostic_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Diagnostic started with UNDETECTED CHROMEDRIVER',
            'estimated_duration': '120-240 seconds',
            'check_results_at': '/results',
            'features': [
                'undetected_chromedriver',
                'cloudflare_bypass',
                'human_like_typing',
                'enhanced_stealth'
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/results', methods=['GET'])
def get_results():
    """Get latest diagnostic results"""
    try:
        if not diagnostic_results:
            return jsonify({
                'success': False,
                'message': 'No diagnostic results available'
            })
        
        latest_report_id = max(diagnostic_results.keys())
        latest_report = diagnostic_results[latest_report_id]
        
        return jsonify({
            'success': True,
            'report': latest_report,
            'total_reports': len(diagnostic_results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def simple_health():
    return jsonify({
        'status': 'healthy',
        'service': 'roblox-analytics-flask-undetected',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    logger.info("Starting Railway Flask Server with UNDETECTED CHROMEDRIVER")
    app.run(host='0.0.0.0', port=PORT, debug=False)
