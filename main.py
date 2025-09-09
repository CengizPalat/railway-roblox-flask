#!/usr/bin/env python3
"""
FIXED RAILWAY FLASK SERVER - Selenium Grid Connection Issue Resolved
File: main.py
CRITICAL FIX: Use Railway internal networking for Selenium Grid connection
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

# FIXED: Configuration with proper Railway internal networking
PORT = int(os.getenv('PORT', 8080))  # Railway default port

# CRITICAL FIX: Use Railway internal networking instead of localhost
SELENIUM_GRID_URL = os.getenv('SELENIUM_REMOTE_URL', 'http://standalone-chrome.railway.internal:4444/wd/hub')
logger.info(f"🔗 Selenium Grid URL: {SELENIUM_GRID_URL}")

ALT_USERNAME = os.getenv('ALT_ROBLOX_USERNAME', 'ByddyY8rPao2124')
ALT_PASSWORD = os.getenv('ALT_ROBLOX_PASSWORD')
SPARKEDHOSTING_API = os.getenv('SPARKEDHOSTING_API_URL', 'https://roblox.sparked.network/api')

# Store for diagnostic results
diagnostic_results = {}

class RobloxLoginDiagnostics:
    """Advanced Roblox login diagnostics with FIXED Railway integration"""
    
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
        """Railway-optimized Chrome options with enhanced stability"""
        options = Options()
        
        # ENHANCED: Core Railway compatibility options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--headless")  # Essential for Railway
        
        # ENHANCED: Performance and stability options
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # ENHANCED: Anti-detection measures
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
        """ENHANCED: Test Selenium Grid connection with multiple fallbacks"""
        logger.info("🔍 Testing Selenium Grid connection...")
        
        # Test 1: Status endpoint check
        try:
            test_url = SELENIUM_GRID_URL.replace('/wd/hub', '/status')
            logger.info(f"🔗 Testing Selenium status at: {test_url}")
            
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Selenium status endpoint responding")
                status_data = response.json()
                if status_data.get('value', {}).get('ready'):
                    logger.info("✅ Selenium Grid is ready")
                    return True
                else:
                    logger.warning("⚠️ Selenium Grid not ready")
            else:
                logger.warning(f"⚠️ Selenium status HTTP {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Selenium status check failed: {e}")
        
        # Test 2: Direct WebDriver connection
        try:
            logger.info("🔗 Testing direct WebDriver connection...")
            options = self.get_chrome_options()
            
            driver = webdriver.Remote(
                command_executor=SELENIUM_GRID_URL,
                options=options
            )
            
            # Simple test
            driver.get("https://httpbin.org/ip")
            driver.quit()
            
            logger.info("✅ Direct WebDriver connection successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Direct WebDriver connection failed: {e}")
            return False
    
    def run_full_diagnostic(self):
        """ENHANCED: Complete login diagnostic workflow with better error handling"""
        self.report_id = f"diagnostic_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        driver = None
        
        try:
            # Step 1: Test Selenium connection first
            self.log_step("selenium_connectivity_test", "starting", {"grid_url": SELENIUM_GRID_URL})
            
            if not self.test_selenium_connection():
                self.log_error("selenium_connection", "Failed to connect to Selenium Grid", {
                    "grid_url": SELENIUM_GRID_URL,
                    "recommendation": "Check Railway internal networking configuration"
                })
                return self.generate_diagnostic_report()
            
            self.log_step("selenium_connectivity_test", "success")
            
            # Step 2: Initialize Selenium WebDriver
            self.log_step("selenium_init", "starting", {"grid_url": SELENIUM_GRID_URL})
            
            options = self.get_chrome_options()
            driver = webdriver.Remote(
                command_executor=SELENIUM_GRID_URL,
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
        """ENHANCED: Generate comprehensive diagnostic report"""
        total_steps = len(self.debug_data['steps_completed'])
        total_errors = len(self.debug_data['errors_encountered'])
        screenshots_captured = len(self.debug_data['screenshots'])
        
        # Enhanced diagnosis logic
        if self.debug_data['success']:
            diagnosis = "LOGIN_SUCCESS"
            recommended_actions = ["Monitor for consistency", "Account is functioning normally"]
        elif any(error['type'] == 'selenium_connection' for error in self.debug_data['errors_encountered']):
            diagnosis = "SELENIUM_CONNECTION_FAILURE"
            recommended_actions = [
                "Fix Railway internal networking to Selenium Grid",
                "Verify standalone-chrome service is running",
                "Check environment variables: SELENIUM_REMOTE_URL",
                "Use: http://standalone-chrome.railway.internal:4444/wd/hub"
            ]
        elif any('password' in str(error).lower() for error in self.debug_data['errors_encountered']):
            diagnosis = "AUTHENTICATION_FAILURE"
            recommended_actions = [
                "Verify ALT_ROBLOX_PASSWORD environment variable",
                "Check account status manually",
                "Try manual login to confirm account status"
            ]
        elif any(error['type'] == 'form_analysis' for error in self.debug_data['errors_encountered']):
            diagnosis = "LOGIN_FORM_CHANGED"
            recommended_actions = [
                "Update login form selectors",
                "Check for Roblox UI changes",
                "Implement more robust element detection"
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
                'selenium_grid_url': self.debug_data.get('selenium_url', 'Connection failed'),
                'selenium_urls_tested': SELENIUM_GRID_URLS,
                'username_tested': ALT_USERNAME,
                'browser': "Chrome/120.0.0.0",
                'browser_settings': "Headless, No-sandbox, Anti-detection",
                'railway_environment': True
            },
            'detailed_steps': self.debug_data['steps_completed'],
            'errors_log': self.debug_data['errors_encountered'],
            'screenshots': self.debug_data['screenshots'],
            'page_sources': self.debug_data['page_sources']
        }
        
        return report

# ENHANCED Flask Routes

@app.route('/status', methods=['GET'])
def health_check():
    """ENHANCED: Health check with detailed Selenium Grid testing"""
    try:
        # Test Selenium Grid connection with multiple methods
        selenium_status = "failed"
        selenium_details = {}
        
        try:
            # Method 1: Status endpoint
            status_url = SELENIUM_GRID_URL.replace('/wd/hub', '/status')
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get('value', {}).get('ready'):
                    selenium_status = "ok"
                    selenium_details = {
                        "status_endpoint": "ok",
                        "grid_ready": True,
                        "nodes": len(status_data.get('value', {}).get('nodes', []))
                    }
                else:
                    selenium_details = {"status_endpoint": "ok", "grid_ready": False}
            else:
                selenium_details = {"status_endpoint": f"http_{response.status_code}"}
                
        except Exception as status_error:
            selenium_details = {"status_endpoint": f"error_{str(status_error)[:50]}"}
            
            # Method 2: Direct connection test if status fails
            try:
                logger.info("🔗 Testing direct WebDriver connection as fallback...")
                options = Options()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--headless")
                
                driver = webdriver.Remote(
                    command_executor=SELENIUM_GRID_URL,
                    options=options
                )
                driver.quit()
                
                selenium_status = "ok"
                selenium_details["direct_connection"] = "ok"
                
            except Exception as direct_error:
                selenium_details["direct_connection"] = f"error_{str(direct_error)[:50]}"
    
    except Exception as e:
        selenium_status = "failed"
        selenium_details = {"error": str(e)[:100]}
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'selenium_grid': selenium_status,
        'selenium_details': selenium_details,
        'selenium_url': SELENIUM_GRID_URL,
        'environment': 'railway',
        'version': '2.0-fixed'
    })

@app.route('/trigger-diagnostic', methods=['POST'])
def trigger_diagnostic():
    """ENHANCED: Trigger Roblox login diagnostic with better error handling"""
    try:
        logger.info("🚀 Starting enhanced diagnostic trigger")
        
        # Validate environment
        if not ALT_PASSWORD:
            return jsonify({
                'success': False,
                'error': 'ALT_ROBLOX_PASSWORD not configured',
                'required_env_vars': ['ALT_ROBLOX_PASSWORD']
            }), 400
        
        # Quick pre-check of Selenium connection
        try:
            diagnostics_test = RobloxLoginDiagnostics()
            if not diagnostics_test.test_selenium_connection():
                return jsonify({
                    'success': False,
                    'error': 'Selenium Grid connection failed',
                    'selenium_url': SELENIUM_GRID_URL,
                    'recommendation': 'Check Railway internal networking configuration'
                }), 503
        except Exception as pre_check_error:
            logger.error(f"❌ Pre-check failed: {pre_check_error}")
        
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
            'selenium_url': SELENIUM_GRID_URL,
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

# ENHANCED: Error handling
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
    logger.info("🚀 Starting FIXED Railway Flask Server")
    logger.info(f"🔗 Selenium Grid URL: {SELENIUM_GRID_URL}")
    logger.info(f"👤 Alt Username: {ALT_USERNAME}")
    logger.info(f"🌐 API URL: {SPARKEDHOSTING_API}")
    
    # Test Selenium connection on startup
    try:
        test_diagnostics = RobloxLoginDiagnostics()
        connection_ok = test_diagnostics.test_selenium_connection()
        logger.info(f"🔌 Selenium connection test: {'✅ OK' if connection_ok else '❌ FAILED'}")
    except Exception as e:
        logger.error(f"❌ Startup Selenium test failed: {e}")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
