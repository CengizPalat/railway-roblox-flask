from flask import Flask, jsonify, request
import os
import time
import json
from datetime import datetime, timedelta
import base64
from seleniumbase import SB
import logging
import traceback
import sys
from typing import Dict, Optional, Any
import threading
from contextlib import contextmanager

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class RobloxAnalytics:
    def __init__(self):
        self.username = "ByddyY8rPao2124"
        self.password = "VHAHnfR9GNuX4aABZWtD"
        self.last_login = None
        self.login_valid_hours = 2
        self.session_data = {}
        self.last_results = {}
        
    def get_comprehensive_chrome_options(self):
        """Get comprehensive Chrome options optimized for Railway deployment and Cloudflare bypass"""
        base_options = [
            # Core stability options
            "--no-sandbox",
            "--disable-dev-shm-usage", 
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            
            # Memory and performance optimization
            "--memory-pressure-off",
            "--max_old_space_size=4096",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-field-trial-config",
            "--disable-back-forward-cache",
            "--disable-background-networking",
            
            # Anti-detection options
            "--disable-blink-features=AutomationControlled",
            "--disable-automation",
            "--disable-infobars",
            "--disable-extensions-file-access-check",
            "--disable-extensions-http-throttling",
            "--disable-extensions-app-file-protocol",
            
            # Network and security
            "--disable-sync",
            "--disable-translate",
            "--disable-ipc-flooding-protection",
            "--disable-default-apps",
            "--disable-component-extensions-with-background-pages",
            "--disable-client-side-phishing-detection",
            "--disable-hang-monitor",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-domain-reliability",
            "--disable-component-update",
            "--disable-background-downloads",
            "--disable-add-to-shelf",
            "--disable-office-editing-component-extension",
            "--disable-file-system",
            
            # Rendering optimizations
            "--aggressive-cache-discard",
            "--force-color-profile=srgb",
            "--disable-threaded-animation",
            "--disable-threaded-scrolling",
            "--disable-partial-raster",
            "--disable-skia-runtime-opts",
            "--run-all-compositor-stages-before-draw",
            "--disable-new-content-rendering-timeout",
            "--disable-canvas-aa",
            "--disable-2d-canvas-clip-aa",
            "--disable-gl-drawing-for-tests",
            "--enable-low-res-tiling",
            "--disable-webgl",
            "--disable-webgl2",
            
            # Additional stealth options
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--accept-lang=en-US,en;q=0.9",
            "--disable-logging",
            "--disable-log-file",
            "--silent"
        ]
        
        # Railway-specific settings
        if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT'):
            logger.info("Applying Railway-specific Chrome options")
            base_options.extend([
                "--remote-debugging-port=9222",
                "--headless=new",
                "--window-size=1920,1080",
                "--disable-extensions",
                "--no-first-run",
                "--disable-plugins",
                "--disable-images",
                "--disable-javascript-harmony-shipping",
                "--disable-background-mode",
                "--disable-background-networking",
                "--disable-client-side-phishing-detection",
                "--disable-default-apps",
                "--disable-hang-monitor",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-sync",
                "--disable-translate",
                "--metrics-recording-only",
                "--no-first-run",
                "--safebrowsing-disable-auto-update",
                "--enable-automation",
                "--password-store=basic",
                "--use-mock-keychain"
            ])
        else:
            logger.info("Applying local development Chrome options")
            base_options.extend([
                "--window-size=1920,1080"
            ])
            
        return base_options

    @contextmanager
    def get_selenium_session(self):
        """Context manager for SeleniumBase session with comprehensive error handling"""
        sb = None
        try:
            chrome_options = self.get_comprehensive_chrome_options()
            logger.info(f"Starting SeleniumBase with {len(chrome_options)} Chrome options")
            
            # Initialize SeleniumBase with UC mode and comprehensive options
            sb = SB(
                uc=True,  # Undetected Chrome mode for Cloudflare bypass
                headless=True if (os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT')) else False,
                browser="chrome",
                chromium_arg=" ".join(chrome_options),
                page_load_strategy="eager",  # Faster page loading
                timeout_multiplier=2.0,  # More generous timeouts for Railway
                incognito=True,  # Fresh session each time
                guest_mode=True  # Additional stealth
            )
            
            sb.open_new_window()  # Fresh window
            logger.info("SeleniumBase session started successfully")
            yield sb
            
        except Exception as e:
            logger.error(f"Failed to create SeleniumBase session: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        finally:
            if sb:
                try:
                    sb.quit()
                    logger.info("SeleniumBase session closed")
                except:
                    logger.warning("Error closing SeleniumBase session")

    def test_cloudflare_bypass(self, sb) -> Dict[str, Any]:
        """Test Cloudflare bypass capability with detailed diagnostics"""
        try:
            logger.info("Testing Cloudflare bypass...")
            
            # Test with Roblox main page
            sb.get("https://www.roblox.com")
            sb.sleep(8)  # Allow time for any challenges
            
            # Capture current state
            current_url = sb.get_current_url()
            page_title = sb.get_title()
            page_source = sb.get_page_source()
            
            # Take diagnostic screenshot
            screenshot_data = sb.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            # Check for Cloudflare indicators
            cloudflare_indicators = [
                "checking your browser",
                "cloudflare",
                "please wait",
                "verifying you are human",
                "browser verification",
                "challenge-platform",
                "cf-browser-verification"
            ]
            
            page_lower = page_source.lower()
            detected_indicators = [indicator for indicator in cloudflare_indicators if indicator in page_lower]
            
            # Additional checks
            has_roblox_content = any(term in page_lower for term in ["roblox", "sign up", "log in", "games"])
            challenge_detected = len(detected_indicators) > 0
            
            return {
                "success": True,
                "cloudflare_bypass": not challenge_detected and has_roblox_content,
                "current_url": current_url,
                "page_title": page_title,
                "detected_indicators": detected_indicators,
                "has_roblox_content": has_roblox_content,
                "screenshot": screenshot_b64,
                "page_length": len(page_source),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cloudflare bypass test error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }

    def handle_initial_page_load(self, sb, url: str) -> bool:
        """Handle initial page load with Cloudflare detection and waiting"""
        try:
            logger.info(f"Loading page: {url}")
            sb.get(url)
            
            # Initial wait
            sb.sleep(5)
            
            # Check for Cloudflare challenge
            page_source = sb.get_page_source().lower()
            if any(indicator in page_source for indicator in ["checking your browser", "cloudflare", "please wait"]):
                logger.info("Cloudflare challenge detected, waiting for bypass...")
                
                # Wait for challenge to complete (UC mode should handle this)
                max_wait = 30
                wait_interval = 2
                waited = 0
                
                while waited < max_wait:
                    sb.sleep(wait_interval)
                    waited += wait_interval
                    
                    current_source = sb.get_page_source().lower()
                    if not any(indicator in current_source for indicator in ["checking your browser", "cloudflare", "please wait"]):
                        logger.info("Cloudflare challenge bypassed!")
                        break
                    
                    logger.info(f"Still waiting for Cloudflare bypass... ({waited}s)")
                
                if waited >= max_wait:
                    logger.warning("Cloudflare challenge may not have been bypassed within timeout")
            
            return True
            
        except Exception as e:
            logger.error(f"Page load error: {str(e)}")
            return False

    def login_to_roblox(self, sb) -> Dict[str, Any]:
        """Comprehensive Roblox login with detailed error handling"""
        try:
            logger.info("Starting Roblox login process...")
            
            # Navigate to login page
            if not self.handle_initial_page_load(sb, "https://www.roblox.com/login"):
                return {"success": False, "error": "Failed to load login page"}
            
            # Handle cookie consent if present
            try:
                if sb.is_element_present("button[aria-label='Accept All']", timeout=3):
                    logger.info("Accepting cookie consent...")
                    sb.click("button[aria-label='Accept All']")
                    sb.sleep(2)
            except Exception as e:
                logger.info("No cookie consent dialog found or failed to handle")
            
            # Wait for login form to be available
            login_form_selectors = [
                "#login-username",
                "input[placeholder*='Username']",
                "input[name='username']"
            ]
            
            username_field = None
            for selector in login_form_selectors:
                try:
                    if sb.is_element_present(selector, timeout=5):
                        username_field = selector
                        break
                except:
                    continue
            
            if not username_field:
                screenshot_data = sb.get_screenshot_as_png()
                screenshot_b64 = base64.b64encode(screenshot_data).decode()
                return {
                    "success": False, 
                    "error": "Username field not found",
                    "screenshot": screenshot_b64,
                    "current_url": sb.get_current_url(),
                    "page_source_snippet": sb.get_page_source()[:1000]
                }
            
            # Fill login credentials
            logger.info("Filling login credentials...")
            sb.type(username_field, self.username)
            
            # Find password field
            password_selectors = [
                "#login-password",
                "input[placeholder*='Password']", 
                "input[name='password']",
                "input[type='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    if sb.is_element_present(selector, timeout=3):
                        password_field = selector
                        break
                except:
                    continue
            
            if password_field:
                sb.type(password_field, self.password)
            else:
                return {"success": False, "error": "Password field not found"}
            
            # Submit login
            login_button_selectors = [
                "#login-button",
                "button[type='submit']",
                "button[data-testid='login-button']",
                ".btn-primary-md"
            ]
            
            for selector in login_button_selectors:
                try:
                    if sb.is_element_present(selector, timeout=3):
                        logger.info(f"Clicking login button: {selector}")
                        sb.click(selector)
                        break
                except:
                    continue
            
            # Wait for login processing
            sb.sleep(8)
            
            # Check login result
            current_url = sb.get_current_url()
            logger.info(f"After login attempt, current URL: {current_url}")
            
            # Handle 2FA or verification if present
            if "challenge" in current_url or "verification" in current_url or "two-step" in current_url:
                logger.info("2FA/Verification challenge detected, waiting...")
                
                # Wait for manual verification or automatic solving
                verification_wait = 45
                sb.sleep(verification_wait)
                current_url = sb.get_current_url()
                logger.info(f"After verification wait, current URL: {current_url}")
            
            # Check for successful login indicators
            success_indicators = [
                "home" in current_url,
                "dashboard" in current_url,
                "/users/" in current_url,
                "create.roblox.com" in current_url
            ]
            
            if any(success_indicators):
                logger.info("Login appears successful!")
                self.last_login = datetime.now()
                return {
                    "success": True,
                    "login_time": self.last_login.isoformat(),
                    "final_url": current_url
                }
            
            # Try navigating to creator dashboard to confirm access
            logger.info("Attempting to navigate to creator dashboard...")
            sb.get("https://create.roblox.com/")
            sb.sleep(8)
            
            if "create.roblox.com" in sb.get_current_url():
                logger.info("Successfully reached creator dashboard")
                self.last_login = datetime.now()
                return {
                    "success": True,
                    "login_time": self.last_login.isoformat(),
                    "final_url": sb.get_current_url()
                }
            
            # Login may have failed
            screenshot_data = sb.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            return {
                "success": False,
                "error": "Login verification failed - unexpected final URL",
                "final_url": current_url,
                "screenshot": screenshot_b64
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            screenshot_data = None
            try:
                screenshot_data = sb.get_screenshot_as_png()
                screenshot_b64 = base64.b64encode(screenshot_data).decode()
            except:
                screenshot_b64 = None
                
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "screenshot": screenshot_b64
            }

    def capture_qptr_data(self, sb, game_id: Optional[str] = None) -> Dict[str, Any]:
        """Capture QPTR data from creator dashboard with comprehensive extraction"""
        try:
            # Determine analytics URL
            if game_id:
                analytics_url = f"https://create.roblox.com/dashboard/creations/experiences/{game_id}/analytics"
                logger.info(f"Navigating to specific game analytics: {game_id}")
            else:
                analytics_url = "https://create.roblox.com/dashboard/creations"
                logger.info("Navigating to general creations dashboard")
                
            # Navigate to analytics
            if not self.handle_initial_page_load(sb, analytics_url):
                return {"success": False, "error": "Failed to load analytics page"}
            
            # Wait for page to fully load
            sb.sleep(10)
            
            # Take diagnostic screenshot
            screenshot_data = sb.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            # Extract QPTR and analytics data
            qptr_data = {}
            analytics_data = {}
            
            # Comprehensive selectors for different QPTR representations
            qptr_selectors = [
                # Direct QPTR selectors
                "[data-testid*='qptr']",
                "[data-testid*='playthrough']", 
                "[data-testid*='play-through']",
                "[data-testid*='retention']",
                
                # General metric selectors
                ".metric-card",
                ".analytics-metric",
                "[class*='metric']",
                "[class*='stat']",
                ".dashboard-stat",
                
                # Percentage value selectors
                "[class*='percentage']",
                ".percent-value",
                
                # Text content selectors
                "*:contains('%')",
                "span:contains('%')",
                "div:contains('%')"
            ]
            
            for selector in qptr_selectors:
                try:
                    if sb.is_element_present(selector, timeout=3):
                        elements = sb.find_elements(selector)
                        for i, elem in enumerate(elements[:10]):  # Limit to first 10 matches
                            try:
                                text = elem.text.strip()
                                if text and "%" in text:
                                    # Check if this looks like QPTR data
                                    text_lower = text.lower()
                                    if any(keyword in text_lower for keyword in [
                                        'play', 'through', 'retention', 'rate', 'qualified'
                                    ]):
                                        qptr_data[f"{selector}_{i}"] = text
                                    elif text and len(text) < 50:  # Any percentage under 50 chars
                                        analytics_data[f"{selector}_{i}"] = text
                            except Exception as elem_error:
                                logger.debug(f"Error extracting from element: {elem_error}")
                                continue
                except Exception as selector_error:
                    logger.debug(f"Selector {selector} failed: {selector_error}")
                    continue
            
            # Try to extract data from page source using regex
            page_source = sb.get_page_source()
            import re
            
            # Look for percentage patterns in source
            percentage_patterns = [
                r'(?:qptr|playthrough|retention).*?(\d+\.?\d*%)',
                r'(\d+\.?\d*%)',  # Any percentage
                r'"value":\s*"(\d+\.?\d*%)"',  # JSON value patterns
                r'data-value="(\d+\.?\d*%)"'  # Data attribute patterns
            ]
            
            source_extracted = {}
            for i, pattern in enumerate(percentage_patterns):
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    source_extracted[f"pattern_{i}"] = matches[:5]  # First 5 matches
            
            # Get current page info
            current_url = sb.get_current_url()
            page_title = sb.get_title()
            
            return {
                "success": True,
                "qptr_data": qptr_data,
                "analytics_data": analytics_data,
                "source_extracted": source_extracted,
                "screenshot": screenshot_b64,
                "current_url": current_url,
                "page_title": page_title,
                "page_length": len(page_source),
                "game_id": game_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"QPTR capture error: {str(e)}")
            screenshot_data = None
            try:
                screenshot_data = sb.get_screenshot_as_png()
                screenshot_b64 = base64.b64encode(screenshot_data).decode()
            except:
                screenshot_b64 = None
                
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "screenshot": screenshot_b64,
                "timestamp": datetime.now().isoformat()
            }

    def run_complete_analytics_collection(self, game_id: Optional[str] = None) -> Dict[str, Any]:
        """Main method to run complete analytics collection with full error handling"""
        start_time = datetime.now()
        results = {
            "start_time": start_time.isoformat(),
            "game_id": game_id,
            "steps": {}
        }
        
        try:
            with self.get_selenium_session() as sb:
                # Step 1: Test Cloudflare bypass
                logger.info("Step 1: Testing Cloudflare bypass...")
                cloudflare_result = self.test_cloudflare_bypass(sb)
                results["steps"]["cloudflare_test"] = cloudflare_result
                
                if not cloudflare_result.get("cloudflare_bypass", False):
                    logger.warning("Cloudflare bypass may have failed, proceeding anyway...")
                
                # Step 2: Login to Roblox
                logger.info("Step 2: Logging into Roblox...")
                login_result = self.login_to_roblox(sb)
                results["steps"]["login"] = login_result
                
                if not login_result.get("success", False):
                    results["overall_success"] = False
                    results["error"] = "Login failed"
                    return results
                
                # Step 3: Capture QPTR data
                logger.info("Step 3: Capturing QPTR data...")
                qptr_result = self.capture_qptr_data(sb, game_id)
                results["steps"]["qptr_capture"] = qptr_result
                
                # Overall success assessment
                results["overall_success"] = (
                    cloudflare_result.get("success", False) and
                    login_result.get("success", False) and
                    qptr_result.get("success", False)
                )
                
                # Store results for later retrieval
                self.last_results = results
                
                return results
                
        except Exception as e:
            logger.error(f"Complete analytics collection error: {str(e)}")
            results["overall_success"] = False
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()
            return results
        
        finally:
            end_time = datetime.now()
            results["end_time"] = end_time.isoformat()
            results["duration_seconds"] = (end_time - start_time).total_seconds()

# Initialize analytics instance
analytics = RobloxAnalytics()

@app.route('/')
def home():
    """Root endpoint with system information"""
    return jsonify({
        "status": "Roblox Analytics API - Production Ready",
        "version": "3.0.0",
        "python_version": "3.12 Compatible",
        "cloudflare_bypass": "SeleniumBase UC Mode",
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'local'),
        "features": [
            "Cloudflare bypass testing",
            "Roblox login automation", 
            "QPTR data extraction",
            "Screenshot diagnostics",
            "Comprehensive error handling"
        ],
        "endpoints": [
            "GET /status - System status",
            "POST /test-cloudflare - Test Cloudflare bypass",
            "POST /trigger-diagnostic - Full analytics collection",
            "GET /results - Latest results",
            "POST /login-test - Test login only"
        ],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/status')
def status():
    """System status endpoint"""
    return jsonify({
        "status": "running",
        "last_login": analytics.last_login.isoformat() if analytics.last_login else None,
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'local'),
        "port": os.getenv('PORT', '5000'),
        "credentials_configured": bool(analytics.username and analytics.password),
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test-cloudflare', methods=['POST'])
def test_cloudflare_endpoint():
    """Test Cloudflare bypass capability"""
    try:
        logger.info("Testing Cloudflare bypass via endpoint...")
        
        with analytics.get_selenium_session() as sb:
            result = analytics.test_cloudflare_bypass(sb)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Cloudflare test endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/login-test', methods=['POST'])
def login_test_endpoint():
    """Test Roblox login only"""
    try:
        logger.info("Testing Roblox login via endpoint...")
        
        with analytics.get_selenium_session() as sb:
            result = analytics.login_to_roblox(sb)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Login test endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/trigger-diagnostic', methods=['POST'])
def trigger_diagnostic():
    """Trigger complete analytics collection with comprehensive diagnostics"""
    try:
        data = request.get_json() or {}
        game_id = data.get('game_id')
        
        logger.info(f"Starting complete diagnostic collection for game_id: {game_id}")
        result = analytics.run_complete_analytics_collection(game_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Diagnostic trigger error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/results')
def results():
    """Get latest results and system information"""
    return jsonify({
        "system_info": {
            "system": "SeleniumBase UC Mode",
            "python_version": "3.12",
            "cloudflare_status": "Bypass Enabled",
            "environment": os.getenv('RAILWAY_ENVIRONMENT', 'local')
        },
        "session_info": {
            "last_login": analytics.last_login.isoformat() if analytics.last_login else None,
            "credentials": "Configured" if analytics.username else "Missing",
            "session_valid": analytics.last_login and 
                           (datetime.now() - analytics.last_login) < timedelta(hours=analytics.login_valid_hours)
        },
        "last_results": analytics.last_results,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /",
            "GET /status", 
            "POST /test-cloudflare",
            "POST /login-test",
            "POST /trigger-diagnostic",
            "GET /results",
            "GET /health"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": str(error),
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = not (os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT'))
    
    logger.info(f"Starting Flask app on port {port}, debug={debug_mode}")
    logger.info(f"Environment: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
