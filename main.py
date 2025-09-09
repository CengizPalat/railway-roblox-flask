#!/usr/bin/env python3
"""
RAILWAY FLASK SERVER - FINAL VERSION
File: main.py
FIXED: Uses port 4444 for Selenium Grid with multi-URL fallback
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
PORT = int(os.getenv('PORT', 8080))
ALT_USERNAME = os.getenv('ALT_ROBLOX_USERNAME', 'ByddyY8rPao2124')
ALT_PASSWORD = os.getenv('ALT_ROBLOX_PASSWORD')
SPARKEDHOSTING_API = os.getenv('SPARKEDHOSTING_API_URL', 'https://roblox.sparked.network/api')

# FINAL: Selenium Grid URLs with PORT 4444 (your new configuration)
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
    
    logger.info("🔍 Testing Selenium Grid URLs (port 4444)...")
    
    for i, url in enumerate(SELENIUM_GRID_URLS):
        try:
            logger.info(f"🔗 Testing URL {i+1}/{len(SELENIUM_GRID_URLS)}: {url}")
            
            # Test status endpoint first
            status_url = url.replace('/wd/hub', '/status')
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get('value', {}).get('ready'):
                    logger.info(f"✅ Found working Selenium URL: {url}")
                    WORKING_SELENIUM_URL = url
                    return url
                else:
                    logger.warning(f"⚠️ URL {url} responded but not ready")
            else:
                logger.warning(f"⚠️ URL {url} returned HTTP {response.status_code}")
                
        except Exception as e:
            logger.warning(f"❌ URL {url} failed: {str(e)[:100]}")
            continue
    
    # If no status endpoint works, try direct WebDriver connection
    logger.info("🔄 Status endpoints failed, trying direct WebDriver connections...")
    
    for i, url in enumerate(SELENIUM_GRID_URLS):
        try:
            logger.info(f"🔗 Direct test {i+1}/{len(SELENIUM_GRID_URLS)}: {url}")
            
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
            
            logger.info(f"✅ Found working Selenium URL via WebDriver: {url}")
            WORKING_SELENIUM_URL = url
            return url
            
        except Exception as e:
            logger.warning(f"❌ Direct WebDriver test failed for {url}: {str(e)[:100]}")
            continue
    
    logger.error("❌ No working Selenium Grid URL found!")
    return None

class RobloxLoginDiagnostics:
    """Advanced Roblox login diagnostics with Railway integration"""
    
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
        """Railway-optimized Chrome options"""
        options = Options()
        
        # Core Railway compatibility options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--headless")
        
        # Performance and stability options
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent for better compatibility
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
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
            logger.info(f"📸 Screenshot captured: {step_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Screenshot failed for {step_name}: {e}")
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
            logger.info(f"📄 Page source captured: {step_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Page source capture failed for {step_name}: {e}")
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
        logger.info(f"🔵 Step: {step_name} - {status}")
    
    def log_error(self, error_type, error_message, details=None):
        """Enhanced error logging"""
        error_data = {
            'type': error_type,
            'timestamp': datetime.utcnow().isoformat(),
            'message': str(error_message),
            'details': details or {}
        }
        self.debug_data['errors_encountered'].append(error_data)
        logger.error(f"❌ Error: {error_type} - {error_message}")
    
    def test_selenium_connection(self):
        """Test Selenium Grid connection with the working URL"""
        if not self.selenium_url:
            logger.error("❌ No working Selenium URL available")
            return False
            
        logger.info(f"🔍 Testing Selenium connection to: {self.selenium_url}")
        
        try:
            options = self.get_chrome_options()
            
            driver = webdriver.Remote(
                command_executor=self.selenium_url,
                options=options
            )
            
            # Simple test
            driver.get("https://httpbin.org/ip")
            driver.quit()
            
            logger.info("✅ Selenium connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Selenium connection test failed: {e}")
            return False
    
    def run_full_diagnostic(self):
        """Complete login diagnostic workflow"""
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
            
            # Step 2: Initialize Selenium WebDriver
            self.log_step("selenium_init", "starting", {"grid_url": self.selenium_url})
            
            options = self.get_chrome_options()
            driver = webdriver.Remote(
                command_executor=self.selenium_url,
                options=options
            )
            
            # Configure timeouts
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            self.log_step("selenium_init", "success", {"browser": "Chrome", "version": "120"})
            self.capture_screenshot(driver, "selenium_initialized")
            
            # Step 3: Navigate to Roblox
            self.log_step("roblox_navigation", "starting")
            driver.get("https://www.roblox.com/login")
            time.sleep(3)
            
            self.log_step("roblox_navigation", "success", {"url": driver.current_url})
            self.capture_screenshot(driver, "roblox_login_page")
            self.capture_page_source(driver, "login_page_source")
            
            # Step 4: Analyze login form
            self.log_step("login_form_analysis", "starting")
            
            try:
                username_field = driver.find_element(By.ID, "login-username")
                password_field = driver.find_element(By.ID, "login-password")
                login_button = driver.find_element(By.ID, "login-button")
                
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
                
            # Step 5: Attempt login
            self.log_step("login_attempt", "starting")
            
            try:
                if not ALT_PASSWORD:
                    raise ValueError("ALT_ROBLOX_PASSWORD not configured")
                
                username_field.clear()
                username_field.send_keys(ALT_USERNAME)
                time.sleep(1)
                
                password_field.clear()
                password_field.send_keys(ALT_PASSWORD)
                time.sleep(1)
                
                self.capture_screenshot(driver, "credentials_entered")
                
                login_button.click()
                time.sleep(5)
                
                # Check result
                current_url = driver.current_url
                if "login" not in current_url.lower():
                    self.log_step("login_attempt", "success", {"redirect_url": current_url})
                    self.debug_data['success'] = True
                else:
                    self.log_step("login_attempt", "failed", {"stayed_on_login": True})
                
                self.capture_screenshot(driver, "login_attempt_result")
                
            except Exception as e:
                self.log_error("login_execution", f"Login attempt failed: {e}")
                self.capture_screenshot(driver, "login_execution_error")
            
            # Step 6: Final analysis
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
                    logger.info("🔄 WebDriver cleaned up")
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
                "Verify standalone-chrome service is running on port 4444",
                "Test external URL as fallback",
                f"Attempted URLs: {', '.join(SELENIUM_GRID_URLS)}"
            ]
        elif any(error['type'] == 'selenium_connection' for error in self.debug_data['errors_encountered']):
            diagnosis = "SELENIUM_CONNECTION_FAILURE"
            recommended_actions = [
                "Verify Railway service connectivity",
                "Check standalone-chrome service status",
                "Review Railway internal networking settings"
            ]
        elif any('password' in str(error).lower() for error in self.debug_data['errors_encountered']):
            diagnosis = "AUTHENTICATION_FAILURE"
            recommended_actions = [
                "Verify ALT_ROBLOX_PASSWORD environment variable",
                "Check account status manually",
                "Try manual login to confirm account status"
            ]
        else:
            diagnosis = "GENERAL_LOGIN_FAILURE"
            recommended_actions = [
                "Check for account suspension",
                "Verify credentials are correct",
                "Check for 2FA requirements"
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
                'railway_environment': True
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
    """Health check with Selenium Grid testing (port 4444)"""
    
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
        'version': '4.0-port-4444-final'
    })

@app.route('/trigger-diagnostic', methods=['POST'])
def trigger_diagnostic():
    """Trigger diagnostic with URL resolution check"""
    try:
        logger.info("🚀 Starting diagnostic trigger (port 4444)")
        
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
            'selenium_url': working_url,
            'estimated_duration': '60-120 seconds',
            'check_results_at': '/results'
        })
        
    except Exception as e:
        logger.error(f"❌ Trigger error: {e}")
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
    logger.info("🚀 Starting Railway Flask Server (Port 4444 Final)")
    logger.info(f"🔗 Testing Selenium URLs: {SELENIUM_GRID_URLS}")
    
    # Test Selenium connection on startup
    working_url = find_working_selenium_url()
    if working_url:
        logger.info(f"🎉 Found working Selenium URL: {working_url}")
    else:
        logger.error("❌ No working Selenium URL found at startup")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
