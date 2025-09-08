#!/usr/bin/env python3
"""
RAILWAY FLASK SERVER - Complete Solution
File: main.py
Production-ready Flask server for Railway with Selenium integration
"""

import os
import time
import json
import base64
import threading
import asyncio
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
PORT = int(os.getenv('PORT', 8080))  # Railway default port
SELENIUM_GRID_URL = 'http://localhost:4444/wd/hub'  # Internal Selenium grid
ALT_USERNAME = os.getenv('ALT_ROBLOX_USERNAME', 'ByddyY8rPao2124')
ALT_PASSWORD = os.getenv('ALT_ROBLOX_PASSWORD')
SPARKEDHOSTING_API = os.getenv('SPARKEDHOSTING_API_URL', 'https://roblox.sparked.network/api')

# Store for diagnostic results
diagnostic_results = {}

class RobloxLoginDiagnostics:
    """Advanced Roblox login diagnostics with Railway integration"""
    
    def __init__(self):
        self.report_id = None
        self.debug_data = {
            'test_timestamp': datetime.utcnow().isoformat(),
            'selenium_url': SELENIUM_GRID_URL,
            'username': ALT_USERNAME,
            'screenshots': [],
            'page_sources': [],
            'steps_completed': [],
            'errors_encountered': [],
            'success': False
        }
    
    def get_chrome_options(self):
        """Railway-optimized Chrome options"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        return options
    
    def capture_screenshot(self, driver, step_name):
        """Capture and store screenshot"""
        try:
            screenshot = driver.get_screenshot_as_base64()
            screenshot_data = {
                'step': step_name,
                'timestamp': datetime.utcnow().isoformat(),
                'image_base64': screenshot
            }
            self.debug_data['screenshots'].append(screenshot_data)
            logger.info(f"📸 Screenshot captured: {step_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Screenshot failed: {e}")
            return False
    
    def capture_page_source(self, driver, step_name):
        """Capture page source for analysis"""
        try:
            source = driver.page_source
            source_data = {
                'step': step_name,
                'timestamp': datetime.utcnow().isoformat(),
                'html_content': source[:10000]  # Limit size
            }
            self.debug_data['page_sources'].append(source_data)
            logger.info(f"📄 Page source captured: {step_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Page source capture failed: {e}")
            return False
    
    def log_step(self, step_name, status, details=None):
        """Log diagnostic step"""
        step_data = {
            'step': step_name,
            'timestamp': datetime.utcnow().isoformat(),
            'status': status,
            'details': details or {}
        }
        self.debug_data['steps_completed'].append(step_data)
        logger.info(f"🔍 Step: {step_name} - {status}")
    
    def log_error(self, error_type, error_message, details=None):
        """Log diagnostic error"""
        error_data = {
            'type': error_type,
            'timestamp': datetime.utcnow().isoformat(),
            'message': str(error_message),
            'details': details or {}
        }
        self.debug_data['errors_encountered'].append(error_data)
        logger.error(f"❌ Error: {error_type} - {error_message}")
    
    def run_full_diagnostic(self):
        """Complete login diagnostic workflow"""
        self.report_id = f"diagnostic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        driver = None
        
        try:
            # Step 1: Initialize Selenium
            self.log_step("selenium_init", "starting", {"grid_url": SELENIUM_GRID_URL})
            
            options = self.get_chrome_options()
            driver = webdriver.Remote(
                command_executor=SELENIUM_GRID_URL,
                options=options
            )
            
            self.log_step("selenium_init", "success", {"browser": "Chrome", "version": "120"})
            self.capture_screenshot(driver, "selenium_initialized")
            
            # Step 2: Navigate to Roblox
            self.log_step("roblox_navigation", "starting")
            driver.get("https://www.roblox.com/login")
            time.sleep(3)
            
            self.log_step("roblox_navigation", "success", {"url": driver.current_url})
            self.capture_screenshot(driver, "roblox_login_page")
            self.capture_page_source(driver, "login_page_source")
            
            # Step 3: Analyze login form
            self.log_step("login_form_analysis", "starting")
            
            username_field = driver.find_element(By.ID, "login-username")
            password_field = driver.find_element(By.ID, "login-password")
            login_button = driver.find_element(By.ID, "login-button")
            
            form_analysis = {
                "username_field_found": username_field is not None,
                "password_field_found": password_field is not None,
                "login_button_found": login_button is not None,
                "page_title": driver.title
            }
            
            self.log_step("login_form_analysis", "success", form_analysis)
            
            # Step 4: Attempt login
            self.log_step("login_attempt", "starting")
            
            username_field.clear()
            username_field.send_keys(ALT_USERNAME)
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(ALT_PASSWORD)
            time.sleep(1)
            
            self.capture_screenshot(driver, "credentials_entered")
            
            login_button.click()
            time.sleep(5)
            
            # Step 5: Check login result
            current_url = driver.current_url
            page_title = driver.title
            
            login_success = False
            error_message = None
            
            # Check for various login outcomes
            if "login" not in current_url.lower():
                login_success = True
                self.log_step("login_attempt", "success", {
                    "final_url": current_url,
                    "page_title": page_title
                })
            else:
                # Check for specific error messages
                try:
                    error_element = driver.find_element(By.CLASS_NAME, "alert-warning")
                    error_message = error_element.text
                except:
                    try:
                        error_element = driver.find_element(By.CLASS_NAME, "form-has-error")
                        error_message = "Form validation error"
                    except:
                        error_message = "Unknown login failure"
                
                self.log_error("login_failure", error_message, {
                    "final_url": current_url,
                    "page_title": page_title
                })
            
            self.capture_screenshot(driver, "login_result")
            self.capture_page_source(driver, "login_result_source")
            
            # Step 6: Additional checks
            self.log_step("additional_checks", "starting")
            
            # Check for CAPTCHA
            captcha_present = False
            try:
                driver.find_element(By.CLASS_NAME, "captcha")
                captcha_present = True
            except:
                pass
            
            # Check for 2FA
            twofa_present = False
            try:
                driver.find_element(By.ID, "two-step-verification")
                twofa_present = True
            except:
                pass
            
            additional_data = {
                "captcha_detected": captcha_present,
                "two_factor_detected": twofa_present,
                "login_success": login_success,
                "error_message": error_message
            }
            
            self.log_step("additional_checks", "complete", additional_data)
            self.debug_data['success'] = login_success
            
        except WebDriverException as e:
            self.log_error("selenium_error", str(e), {"type": "WebDriverException"})
        except TimeoutException as e:
            self.log_error("timeout_error", str(e), {"type": "TimeoutException"})
        except Exception as e:
            self.log_error("unexpected_error", str(e), {"type": type(e).__name__})
        
        finally:
            if driver:
                try:
                    driver.quit()
                    self.log_step("cleanup", "success", {"driver_closed": True})
                except:
                    self.log_step("cleanup", "failed", {"driver_close_error": True})
        
        # Generate final report
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive diagnostic report"""
        total_steps = len(self.debug_data['steps_completed'])
        total_errors = len(self.debug_data['errors_encountered'])
        screenshots_captured = len(self.debug_data['screenshots'])
        
        # Determine diagnosis
        if self.debug_data['success']:
            diagnosis = "LOGIN_SUCCESS"
            recommended_actions = ["Login working correctly", "No action required"]
        elif total_errors == 0:
            diagnosis = "LOGIN_FAILED_NO_ERRORS"
            recommended_actions = [
                "Check credentials are correct",
                "Verify account is not suspended",
                "Try manual login to confirm account status"
            ]
        elif any(error['type'] == 'selenium_error' for error in self.debug_data['errors_encountered']):
            diagnosis = "SELENIUM_CONNECTION_ISSUE"
            recommended_actions = [
                "Check Selenium Grid is running",
                "Verify Railway container has proper Chrome setup",
                "Check network connectivity to Selenium hub"
            ]
        elif any('captcha' in str(error).lower() for error in self.debug_data['errors_encountered']):
            diagnosis = "CAPTCHA_DETECTED"
            recommended_actions = [
                "Implement CAPTCHA solving service",
                "Use residential proxy IP",
                "Add random delays between requests"
            ]
        else:
            diagnosis = "GENERAL_LOGIN_FAILURE"
            recommended_actions = [
                "Check for account suspension",
                "Verify credentials are correct",
                "Check for 2FA requirements",
                "Monitor for IP blocks"
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
                'selenium_grid_url': SELENIUM_GRID_URL,
                'username_tested': ALT_USERNAME,
                'browser': "Chrome/120.0.0.0",
                'browser_settings': "Headless, No-sandbox, Anti-detection"
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
    """Health check endpoint"""
    try:
        # Test Selenium Grid connection
        response = requests.get(f"http://localhost:4444/status", timeout=5)
        selenium_status = "ok" if response.status_code == 200 else "failed"
    except:
        selenium_status = "failed"
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'selenium_grid': selenium_status,
        'environment': 'railway',
        'version': '1.0'
    })

@app.route('/trigger-diagnostic', methods=['POST'])
def trigger_diagnostic():
    """Trigger Roblox login diagnostic"""
    try:
        logger.info("🚀 Starting diagnostic trigger")
        
        # Validate environment
        if not ALT_PASSWORD:
            return jsonify({
                'success': False,
                'error': 'ALT_ROBLOX_PASSWORD not configured'
            }), 400
        
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
                        logger.info("✅ Report uploaded to SparkedHosting")
                    else:
                        logger.error(f"❌ Upload failed: {upload_response.status_code}")
                except Exception as upload_error:
                    logger.error(f"❌ Upload error: {upload_error}")
                
            except Exception as e:
                logger.error(f"❌ Diagnostic error: {e}")
        
        # Start diagnostic in background
        diagnostic_thread = threading.Thread(target=run_diagnostic)
        diagnostic_thread.daemon = True
        diagnostic_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Diagnostic started',
            'status': 'running',
            'check_url': '/status'
        })
        
    except Exception as e:
        logger.error(f"❌ Trigger error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/results/<report_id>', methods=['GET'])
def get_diagnostic_result(report_id):
    """Get diagnostic results by ID"""
    if report_id in diagnostic_results:
        return jsonify({
            'success': True,
            'report': diagnostic_results[report_id]
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Report not found',
            'available_reports': list(diagnostic_results.keys())
        }), 404

@app.route('/results', methods=['GET'])
def list_diagnostic_results():
    """List all available diagnostic results"""
    return jsonify({
        'success': True,
        'available_reports': list(diagnostic_results.keys()),
        'total_count': len(diagnostic_results)
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint info"""
    return jsonify({
        'service': 'Railway Roblox Analytics',
        'version': '1.0',
        'endpoints': [
            '/status',
            '/trigger-diagnostic',
            '/results/<report_id>',
            '/results'
        ],
        'documentation': 'POST to /trigger-diagnostic to start login diagnostic'
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 RAILWAY FLASK SERVER - ROBLOX ANALYTICS")
    print("=" * 60)
    print(f"🌐 Port: {PORT}")
    print(f"🔧 Selenium Grid: {SELENIUM_GRID_URL}")
    print(f"👤 Alt Account: {ALT_USERNAME}")
    print(f"📊 SparkedHosting API: {SPARKEDHOSTING_API}")
    print(f"🔗 Health Check: /status")
    print(f"🎯 Trigger Diagnostic: /trigger-diagnostic")
    print(f"📊 View Results: /results/<report_id>")
    print("=" * 60)
    
    try:
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        exit(1)