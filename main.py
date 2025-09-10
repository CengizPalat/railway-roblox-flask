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
import re

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

class RobloxVerificationSolver:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('TWOCAPTCHA_API_KEY')
        self.solver = None
        
        if self.api_key:
            try:
                from python2captcha import TwoCaptcha
                self.solver = TwoCaptcha(self.api_key)
                logger.info("2Captcha solver initialized successfully")
            except ImportError:
                logger.warning("python2captcha not installed - verification solving disabled")
            except Exception as e:
                logger.warning(f"Failed to initialize 2Captcha: {str(e)}")
        else:
            logger.info("No 2Captcha API key provided - using manual verification handling")
    
    def solve_roblox_verification(self, sb):
        """Handle Roblox verification puzzles"""
        try:
            logger.info("Detected Roblox verification challenge, attempting to solve...")
            
            # Wait for puzzle to fully load
            sb.sleep(5)
            
            # Take screenshot of the puzzle
            screenshot_data = sb.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            page_source = sb.get_page_source()
            page_text = sb.get_text("body").lower()
            
            # Method 1: Try automated solving if 2Captcha is available
            if self.solver:
                auto_result = self.try_automated_solving(sb, page_source, screenshot_b64)
                if auto_result.get("success"):
                    return auto_result
            
            # Method 2: Try clicking Start Puzzle and waiting
            click_result = self.try_start_puzzle_approach(sb)
            if click_result.get("success"):
                return click_result
            
            # Method 3: Wait and retry approach
            retry_result = self.wait_and_retry_approach(sb)
            return retry_result
                
        except Exception as e:
            logger.error(f"Verification solving error: {str(e)}")
            return {
                "success": False, 
                "error": str(e),
                "screenshot": screenshot_b64 if 'screenshot_b64' in locals() else None
            }
    
    def try_automated_solving(self, sb, page_source, screenshot_b64):
        """Try automated solving with 2Captcha"""
        try:
            # Check for FunCaptcha (Arkose Labs)
            if self.is_funcaptcha(page_source):
                return self.solve_funcaptcha(sb, page_source)
            
            # Try image-based solving
            return self.solve_image_puzzle(sb, screenshot_b64)
            
        except Exception as e:
            logger.error(f"Automated solving failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def is_funcaptcha(self, page_source):
        """Check if this is a FunCaptcha challenge"""
        indicators = ["funcaptcha", "arkose", "enforcement.arkoselabs.com", "data-pkey"]
        return any(indicator in page_source.lower() for indicator in indicators)
    
    def solve_funcaptcha(self, sb, page_source):
        """Solve FunCaptcha using 2Captcha"""
        try:
            public_key_match = re.search(r'data-pkey="([^"]+)"', page_source)
            if not public_key_match:
                public_key_match = re.search(r'"publicKey":"([^"]+)"', page_source)
            
            if public_key_match:
                public_key = public_key_match.group(1)
                current_url = sb.get_current_url()
                
                logger.info(f"Solving FunCaptcha with public key: {public_key}")
                
                result = self.solver.funcaptcha(sitekey=public_key, url=current_url)
                token = result['code']
                
                # Input solution
                sb.execute_script(f'document.querySelector("[name=\'fc-token\']").value = "{token}";')
                sb.click("button[type='submit']")
                sb.sleep(5)
                
                return {"success": True, "method": "funcaptcha_2captcha", "token": token}
                
        except Exception as e:
            logger.error(f"FunCaptcha solving failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def solve_image_puzzle(self, sb, screenshot_b64):
        """Solve image puzzle using 2Captcha"""
        try:
            logger.info("Attempting image puzzle solving...")
            
            # Click Start Puzzle
            if sb.is_element_present("button:contains('Start Puzzle')", timeout=3):
                sb.click("button:contains('Start Puzzle')")
                sb.sleep(3)
            
            # Get puzzle image after clicking
            puzzle_screenshot = sb.get_screenshot_as_png()
            puzzle_b64 = base64.b64encode(puzzle_screenshot).decode()
            
            # Analyze puzzle type
            page_text = sb.get_text("body").lower()
            instructions = self.get_puzzle_instructions(page_text)
            
            # Submit to 2Captcha
            result = self.solver.normal(puzzle_b64, lang='en', hintText=instructions)
            answer = result['code']
            
            # Input answer
            success = self.input_puzzle_answer(sb, answer, page_text)
            
            return {"success": success, "method": "image_puzzle_2captcha", "answer": answer}
            
        except Exception as e:
            logger.error(f"Image puzzle solving failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_puzzle_instructions(self, page_text):
        """Generate instructions for puzzle workers"""
        if "dice" in page_text:
            return "Calculate sum of all dice numbers"
        elif "cube" in page_text or "match" in page_text:
            return "Find matching images/cubes"
        elif "card" in page_text:
            return "Find matching cards"
        elif "animal" in page_text:
            return "Rotate animals to stand on 4 legs"
        else:
            return "Solve the puzzle as shown"
    
    def input_puzzle_answer(self, sb, answer, page_text):
        """Input puzzle answer"""
        try:
            if "dice" in page_text and answer.isdigit():
                selectors = ["input[type='text']", "input[type='number']", ".puzzle-input"]
                for selector in selectors:
                    if sb.is_element_present(selector, timeout=2):
                        sb.type(selector, answer)
                        break
            
            # Submit
            submit_selectors = [
                "button:contains('Submit')", "button:contains('Continue')", 
                "button[type='submit']", ".submit-btn"
            ]
            
            for selector in submit_selectors:
                if sb.is_element_present(selector, timeout=2):
                    sb.click(selector)
                    sb.sleep(3)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to input answer: {str(e)}")
            return False
    
    def try_start_puzzle_approach(self, sb):
        """Try simply clicking Start Puzzle and waiting"""
        try:
            logger.info("Trying Start Puzzle approach...")
            
            # Click Start Puzzle button
            start_selectors = [
                "button:contains('Start Puzzle')",
                "button[class*='start']",
                ".start-button",
                "#start-puzzle"
            ]
            
            clicked = False
            for selector in start_selectors:
                if sb.is_element_present(selector, timeout=3):
                    sb.click(selector)
                    clicked = True
                    break
            
            if not clicked:
                return {"success": False, "message": "Start Puzzle button not found"}
            
            sb.sleep(10)  # Wait for puzzle to load
            
            # Check if verification passed
            current_url = sb.get_current_url()
            page_text = sb.get_text("body").lower()
            
            if "verification" not in page_text or "home" in current_url or "dashboard" in current_url:
                return {"success": True, "method": "start_puzzle_wait"}
            
            # Try waiting longer for auto-solve
            logger.info("Puzzle still present, waiting longer...")
            sb.sleep(30)
            
            page_text = sb.get_text("body").lower()
            if "verification" not in page_text:
                return {"success": True, "method": "start_puzzle_extended_wait"}
            
            return {"success": False, "message": "Puzzle still showing after wait"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def wait_and_retry_approach(self, sb):
        """Wait and retry verification"""
        try:
            logger.info("Using wait and retry approach...")
            
            # Sometimes just waiting helps
            sb.sleep(15)
            
            # Try refreshing
            sb.refresh()
            sb.sleep(5)
            
            page_text = sb.get_text("body").lower()
            if "verification" not in page_text:
                return {"success": True, "method": "refresh_retry"}
            
            # Try different approach - go back to login
            sb.get("https://www.roblox.com/login")
            sb.sleep(5)
            
            return {"success": False, "method": "wait_retry", "message": "Manual intervention may be needed"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class RobloxAnalytics:
    def __init__(self):
        self.username = "ByddyY8rPao2124"
        self.password = "VHAHnfR9GNuX4aABZWtD"
        self.last_login = None
        self.login_valid_hours = 2
        self.session_data = {}
        self.last_results = {}
        self.verification_solver = RobloxVerificationSolver()
        
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
            
            # Anti-detection options
            "--disable-blink-features=AutomationControlled",
            "--disable-automation",
            "--disable-infobars",
            "--disable-extensions-file-access-check",
            
            # Additional stealth options
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--accept-lang=en-US,en;q=0.9",
            "--disable-logging",
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
                "--disable-images"
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
            
            sb = SB(
                uc=True,  # Undetected Chrome mode for Cloudflare bypass
                headless=True if (os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT')) else False,
                browser="chrome",
                chromium_arg=" ".join(chrome_options),
                page_load_strategy="eager",
                timeout_multiplier=2.0,
                incognito=True,
                guest_mode=True
            )
            
            sb.open_new_window()
            logger.info("SeleniumBase session started successfully")
            yield sb
            
        except Exception as e:
            logger.error(f"Failed to create SeleniumBase session: {str(e)}")
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
            
            sb.get("https://www.roblox.com")
            sb.sleep(8)
            
            current_url = sb.get_current_url()
            page_title = sb.get_title()
            page_source = sb.get_page_source()
            
            screenshot_data = sb.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            cloudflare_indicators = [
                "checking your browser", "cloudflare", "please wait",
                "verifying you are human", "browser verification"
            ]
            
            page_lower = page_source.lower()
            detected_indicators = [indicator for indicator in cloudflare_indicators if indicator in page_lower]
            
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
                "timestamp": datetime.now().isoformat()
            }

    def handle_initial_page_load(self, sb, url: str) -> bool:
        """Handle initial page load with Cloudflare detection and waiting"""
        try:
            logger.info(f"Loading page: {url}")
            sb.get(url)
            sb.sleep(5)
            
            page_source = sb.get_page_source().lower()
            if any(indicator in page_source for indicator in ["checking your browser", "cloudflare", "please wait"]):
                logger.info("Cloudflare challenge detected, waiting for bypass...")
                
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
        """Enhanced Roblox login with verification handling"""
        try:
            logger.info("Starting Roblox login process...")
            
            if not self.handle_initial_page_load(sb, "https://www.roblox.com/login"):
                return {"success": False, "error": "Failed to load login page"}
            
            # Handle cookie consent
            try:
                if sb.is_element_present("button[aria-label='Accept All']", timeout=3):
                    logger.info("Accepting cookie consent...")
                    sb.click("button[aria-label='Accept All']")
                    sb.sleep(2)
            except:
                pass
            
            # Fill login form
            username_selectors = ["#login-username", "input[placeholder*='Username']", "input[name='username']"]
            username_field = None
            
            for selector in username_selectors:
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
                    "screenshot": screenshot_b64
                }
            
            logger.info("Filling login credentials...")
            sb.type(username_field, self.username)
            
            # Fill password
            password_selectors = ["#login-password", "input[type='password']"]
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
            login_button_selectors = ["#login-button", "button[type='submit']", ".btn-primary-md"]
            
            for selector in login_button_selectors:
                try:
                    if sb.is_element_present(selector, timeout=3):
                        logger.info(f"Clicking login button: {selector}")
                        sb.click(selector)
                        break
                except:
                    continue
            
            sb.sleep(8)
            
            # Check for verification challenge
            current_url = sb.get_current_url()
            page_text = sb.get_text("body").lower()
            
            if any(indicator in page_text for indicator in ["verification", "start puzzle", "captcha"]):
                logger.info("🧩 VERIFICATION CHALLENGE DETECTED - Attempting to solve...")
                
                verification_result = self.verification_solver.solve_roblox_verification(sb)
                
                if verification_result.get("success"):
                    logger.info(f"✅ Verification solved using method: {verification_result.get('method')}")
                    # Continue with login flow after verification
                    sb.sleep(5)
                    current_url = sb.get_current_url()
                else:
                    logger.warning(f"❌ Verification solving failed: {verification_result.get('error', 'Unknown error')}")
                    screenshot_data = sb.get_screenshot_as_png()
                    screenshot_b64 = base64.b64encode(screenshot_data).decode()
                    return {
                        "success": False,
                        "error": "Verification challenge could not be solved",
                        "verification_result": verification_result,
                        "screenshot": screenshot_b64
                    }
            
            # Check for 2FA
            if "challenge" in current_url or "verification" in current_url or "two-step" in current_url:
                logger.info("2FA/Additional verification detected, waiting...")
                sb.sleep(45)
                current_url = sb.get_current_url()
            
            # Check success
            success_indicators = [
                "home" in current_url, "dashboard" in current_url,
                "/users/" in current_url, "create.roblox.com" in current_url
            ]
            
            if any(success_indicators):
                logger.info("✅ Login successful!")
                self.last_login = datetime.now()
                return {
                    "success": True,
                    "login_time": self.last_login.isoformat(),
                    "final_url": current_url
                }
            
            # Try navigating to creator dashboard
            logger.info("Attempting to navigate to creator dashboard...")
            sb.get("https://create.roblox.com/")
            sb.sleep(8)
            
            if "create.roblox.com" in sb.get_current_url():
                logger.info("✅ Successfully reached creator dashboard")
                self.last_login = datetime.now()
                return {
                    "success": True,
                    "login_time": self.last_login.isoformat(),
                    "final_url": sb.get_current_url()
                }
            
            # Login failed
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
        """Capture QPTR data from creator dashboard"""
        try:
            if game_id:
                analytics_url = f"https://create.roblox.com/dashboard/creations/experiences/{game_id}/analytics"
                logger.info(f"Navigating to specific game analytics: {game_id}")
            else:
                analytics_url = "https://create.roblox.com/dashboard/creations"
                logger.info("Navigating to general creations dashboard")
                
            if not self.handle_initial_page_load(sb, analytics_url):
                return {"success": False, "error": "Failed to load analytics page"}
            
            sb.sleep(10)
            
            screenshot_data = sb.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            # Extract QPTR and analytics data
            qptr_data = {}
            analytics_data = {}
            
            qptr_selectors = [
                "[data-testid*='qptr']", "[data-testid*='playthrough']", 
                "[data-testid*='retention']", ".metric-card", ".analytics-metric",
                "[class*='metric']", "[class*='stat']", ".dashboard-stat"
            ]
            
            for selector in qptr_selectors:
                try:
                    if sb.is_element_present(selector, timeout=3):
                        elements = sb.find_elements(selector)
                        for i, elem in enumerate(elements[:10]):
                            try:
                                text = elem.text.strip()
                                if text and "%" in text:
                                    text_lower = text.lower()
                                    if any(keyword in text_lower for keyword in [
                                        'play', 'through', 'retention', 'rate', 'qualified'
                                    ]):
                                        qptr_data[f"{selector}_{i}"] = text
                                    elif text and len(text) < 50:
                                        analytics_data[f"{selector}_{i}"] = text
                            except:
                                continue
                except:
                    continue
            
            # Extract from page source using regex
            page_source = sb.get_page_source()
            percentage_patterns = [
                r'(?:qptr|playthrough|retention).*?(\d+\.?\d*%)',
                r'(\d+\.?\d*%)',
                r'"value":\s*"(\d+\.?\d*%)"'
            ]
            
            source_extracted = {}
            for i, pattern in enumerate(percentage_patterns):
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    source_extracted[f"pattern_{i}"] = matches[:5]
            
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
        """Main method to run complete analytics collection with verification handling"""
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
                
                # Step 2: Login to Roblox (now with verification handling)
                logger.info("Step 2: Logging into Roblox with verification handling...")
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
                
                results["overall_success"] = (
                    cloudflare_result.get("success", False) and
                    login_result.get("success", False) and
                    qptr_result.get("success", False)
                )
                
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
        "status": "Roblox Analytics API - With Verification Solving",
        "version": "4.0.0",
        "python_version": "3.12 Compatible",
        "cloudflare_bypass": "SeleniumBase UC Mode ✅",
        "verification_solving": "2Captcha + Manual Methods ✅",
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'local'),
        "features": [
            "✅ Cloudflare bypass",
            "✅ Roblox verification puzzle solving", 
            "✅ 2Captcha integration",
            "✅ FunCaptcha (Arkose Labs) support",
            "✅ Image puzzle solving",
            "✅ Manual verification handling",
            "✅ QPTR data extraction",
            "✅ Screenshot diagnostics"
        ],
        "endpoints": [
            "GET /status - System status",
            "POST /test-cloudflare - Test Cloudflare bypass",
            "POST /trigger-diagnostic - Full analytics with verification",
            "GET /results - Latest results",
            "POST /login-test - Test login with verification",
            "POST /test-verification - Test verification solving only"
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
        "verification_solver": {
            "enabled": analytics.verification_solver.solver is not None,
            "api_key_configured": bool(analytics.verification_solver.api_key),
            "methods_available": ["2captcha_auto", "manual_clicking", "wait_retry"]
        },
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
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test-verification', methods=['POST'])
def test_verification_endpoint():
    """Test verification solving only"""
    try:
        logger.info("Testing verification solving...")
        
        with analytics.get_selenium_session() as sb:
            # Navigate to login to trigger verification
            sb.get("https://www.roblox.com/login")
            sb.sleep(3)
            
            # Fill credentials to trigger verification
            if sb.is_element_present("#login-username", timeout=5):
                sb.type("#login-username", analytics.username)
                sb.type("#login-password", analytics.password)
                sb.click("#login-button")
                sb.sleep(5)
                
                # Check if verification appears
                page_text = sb.get_text("body").lower()
                if any(indicator in page_text for indicator in ["verification", "start puzzle", "captcha"]):
                    result = analytics.verification_solver.solve_roblox_verification(sb)
                    return jsonify(result)
                else:
                    return jsonify({
                        "success": True,
                        "message": "No verification challenge appeared",
                        "timestamp": datetime.now().isoformat()
                    })
            
            return jsonify({
                "success": False,
                "error": "Could not find login form",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Verification test error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/login-test', methods=['POST'])
def login_test_endpoint():
    """Test Roblox login with verification handling"""
    try:
        logger.info("Testing Roblox login with verification handling...")
        
        with analytics.get_selenium_session() as sb:
            result = analytics.login_to_roblox(sb)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Login test endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/trigger-diagnostic', methods=['POST'])
def trigger_diagnostic():
    """Trigger complete analytics collection with verification handling"""
    try:
        data = request.get_json() or {}
        game_id = data.get('game_id')
        
        logger.info(f"🚀 Starting complete diagnostic with verification solving for game_id: {game_id}")
        result = analytics.run_complete_analytics_collection(game_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Diagnostic trigger error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/results')
def results():
    """Get latest results and system information"""
    return jsonify({
        "system_info": {
            "system": "SeleniumBase UC Mode + Verification Solving",
            "python_version": "3.12",
            "cloudflare_status": "Bypass Enabled ✅",
            "verification_status": "Solving Enabled ✅",
            "environment": os.getenv('RAILWAY_ENVIRONMENT', 'local')
        },
        "session_info": {
            "last_login": analytics.last_login.isoformat() if analytics.last_login else None,
            "credentials": "Configured" if analytics.username else "Missing",
            "session_valid": analytics.last_login and 
                           (datetime.now() - analytics.last_login) < timedelta(hours=analytics.login_valid_hours)
        },
        "verification_info": {
            "solver_enabled": analytics.verification_solver.solver is not None,
            "api_key_configured": bool(analytics.verification_solver.api_key),
            "supported_methods": [
                "FunCaptcha (Arkose Labs)",
                "Image puzzles (dice, cubes, cards)",
                "Manual clicking approaches",
                "Wait and retry strategies"
            ]
        },
        "last_results": analytics.last_results,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({
        "status": "healthy",
        "verification_ready": True,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = not (os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT'))
    
    logger.info(f"🚀 Starting Flask app with VERIFICATION SOLVING on port {port}")
    logger.info(f"Environment: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}")
    logger.info(f"Verification: {'Enabled' if analytics.verification_solver.api_key else 'Manual only'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
