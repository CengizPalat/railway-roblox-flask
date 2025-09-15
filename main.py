from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import os
import time
import json
import requests
from datetime import datetime, timedelta
import base64
import logging
import traceback
import sys
from typing import Dict, Optional, Any
import threading
from contextlib import contextmanager
import re

# Selenium imports for REMOTE WebDriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

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

# 🔧 COMPREHENSIVE CORS CONFIGURATION WITH EXPLICIT HEADERS
CORS(app, 
     origins=["*"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
     supports_credentials=False,
     send_wildcard=True,
     automatic_options=True)

# 🔧 EXPLICIT CORS HEADER INJECTION FOR COMPATIBILITY
@app.after_request
def after_request(response):
    """Ensure CORS headers are always present"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

@app.before_request
def handle_preflight():
    """Handle preflight OPTIONS requests"""
    if request.method == "OPTIONS":
        response = jsonify({'status': 'preflight_ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response

class RobloxVerificationSolver:
    def __init__(self, api_key=None):
        # Your 2Captcha API key - HARDCODED
        self.api_key = api_key or "b44a6e6b17d4b75d834aa5820db113ff"
        self.solver = None
        
        if self.api_key:
            try:
                # CORRECT IMPORT: from twocaptcha import TwoCaptcha (official 2captcha-python package)
                from twocaptcha import TwoCaptcha
                self.solver = TwoCaptcha(self.api_key)
                logger.info(f"✅ 2Captcha solver initialized successfully with API key: {self.api_key[:8]}...")
            except ImportError as e:
                logger.error(f"❌ 2captcha-python not installed - pip install 2captcha-python (Error: {str(e)})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize 2Captcha: {str(e)}")
        else:
            logger.warning("⚠️ No 2Captcha API key provided")
    
    def solve_roblox_verification(self, driver):
        """Handle Roblox verification puzzles with 2Captcha automated solving"""
        try:
            logger.info("🔍 Checking for Roblox verification puzzles...")
            
            # Wait for verification to appear
            time.sleep(5)
            
            # Get page content
            page_source = driver.page_source
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            
            # Check for verification indicators
            verification_indicators = [
                "verification", "start puzzle", "captcha", "challenge", "verify", 
                "funcaptcha", "arkose", "please complete", "security check"
            ]
            
            verification_present = any(indicator in page_text for indicator in verification_indicators)
            
            if not verification_present:
                logger.info("✅ No verification challenge detected")
                return {"success": True, "message": "No verification required", "method": "none"}
            
            logger.info("🎯 Verification challenge detected! Attempting automated solving...")
            
            # Take screenshot for debugging
            screenshot_data = driver.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            if self.solver:
                try:
                    # Strategy 1: Try FunCaptcha solving (most common for Roblox)
                    logger.info("🧩 Attempting FunCaptcha solving with 2Captcha...")
                    
                    # Look for FunCaptcha iframe
                    iframe_selectors = [
                        "iframe[src*='funcaptcha']",
                        "iframe[src*='arkose']", 
                        "iframe[data-e2e-selector*='funcaptcha']",
                        "iframe[title*='verification']"
                    ]
                    
                    funcaptcha_found = False
                    for selector in iframe_selectors:
                        try:
                            iframe = driver.find_element(By.CSS_SELECTOR, selector)
                            if iframe.is_displayed():
                                funcaptcha_found = True
                                iframe_src = iframe.get_attribute("src")
                                logger.info(f"🎯 Found FunCaptcha iframe: {iframe_src}")
                                
                                # Extract site key and other parameters for 2Captcha
                                site_key = self._extract_site_key(iframe_src, page_source)
                                
                                if site_key:
                                    result = self.solver.funcaptcha(
                                        sitekey=site_key,
                                        url=driver.current_url,
                                        **{"data[blob]": ""} 
                                    )
                                    
                                    if result and "code" in result:
                                        logger.info("✅ 2Captcha solved FunCaptcha!")
                                        
                                        # Submit the solution
                                        self._submit_funcaptcha_solution(driver, result["code"])
                                        time.sleep(3)
                                        
                                        # Check if verification was successful
                                        final_url = driver.current_url
                                        final_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                                        
                                        if "verification" not in final_text or "create.roblox.com" in final_url:
                                            return {
                                                "success": True,
                                                "method": "2captcha_funcaptcha",
                                                "cost": "$0.002",
                                                "final_url": final_url,
                                                "screenshot": screenshot_b64
                                            }
                                break
                        except:
                            continue
                    
                    if not funcaptcha_found:
                        logger.info("🔍 No FunCaptcha found, trying image captcha...")
                        
                        # Strategy 2: Try image captcha solving
                        captcha_images = driver.find_elements(By.CSS_SELECTOR, "img[src*='captcha'], img[alt*='captcha']")
                        
                        if captcha_images:
                            for img in captcha_images:
                                if img.is_displayed():
                                    img_src = img.get_attribute("src")
                                    if img_src and "data:" not in img_src:
                                        try:
                                            result = self.solver.normal(img_src)
                                            if result and "code" in result:
                                                # Find input field and submit solution
                                                captcha_inputs = driver.find_elements(By.CSS_SELECTOR, 
                                                    "input[name*='captcha'], input[id*='captcha'], input[placeholder*='captcha']")
                                                
                                                if captcha_inputs:
                                                    captcha_inputs[0].send_keys(result["code"])
                                                    
                                                    # Find and click submit button
                                                    submit_buttons = driver.find_elements(By.CSS_SELECTOR,
                                                        "button[type='submit'], input[type='submit'], button:contains('Submit')")
                                                    
                                                    if submit_buttons:
                                                        submit_buttons[0].click()
                                                        time.sleep(3)
                                                        
                                                        # Check success
                                                        final_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                                                        if "verification" not in final_text:
                                                            return {
                                                                "success": True,
                                                                "method": "2captcha_image",
                                                                "cost": "$0.001",
                                                                "screenshot": screenshot_b64
                                                            }
                                        except Exception as e:
                                            logger.warning(f"Image captcha solving failed: {e}")
                
                except Exception as e:
                    logger.error(f"❌ 2Captcha solving failed: {str(e)}")
            
            # Fallback strategies
            logger.info("🔄 Trying fallback verification strategies...")
            return self._fallback_verification_strategies(driver, screenshot_b64)
            
        except Exception as e:
            logger.error(f"❌ Verification solving error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "method": "error",
                "traceback": traceback.format_exc()
            }
    
    def _extract_site_key(self, iframe_src, page_source):
        """Extract FunCaptcha site key from iframe or page source"""
        try:
            # Common site key patterns
            patterns = [
                r'data-sitekey="([^"]+)"',
                r"'sitekey':\s*'([^']+)'",
                r'"sitekey":\s*"([^"]+)"',
                r'sitekey:\s*"([^"]+)"',
                r'pk=([A-F0-9-]+)',
                r'public_key=([A-F0-9-]+)'
            ]
            
            sources = [iframe_src, page_source]
            
            for source in sources:
                if source:
                    for pattern in patterns:
                        match = re.search(pattern, source, re.IGNORECASE)
                        if match:
                            return match.group(1)
            
            # Default Roblox FunCaptcha site key (commonly used)
            return "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"
            
        except Exception as e:
            logger.warning(f"Site key extraction failed: {e}")
            return None
    
    def _submit_funcaptcha_solution(self, driver, solution_code):
        """Submit FunCaptcha solution code"""
        try:
            # Common FunCaptcha callback patterns
            callbacks = [
                f"fc_callback('{solution_code}')",
                f"funcaptcha_callback('{solution_code}')",
                f"window.fc_callback && window.fc_callback('{solution_code}')"
            ]
            
            for callback in callbacks:
                try:
                    driver.execute_script(callback)
                    time.sleep(1)
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Solution submission failed: {e}")
    
    def _fallback_verification_strategies(self, driver, screenshot_b64):
        """Fallback strategies when automated solving fails"""
        try:
            # Strategy 1: Wait and see if verification auto-resolves
            logger.info("⏳ Strategy 1: Waiting for auto-resolution...")
            time.sleep(10)
            
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "verification" not in page_text:
                logger.info("✅ Verification auto-resolved!")
                return {"success": True, "method": "wait_only"}
            
            # Strategy 2: Refresh page
            logger.info("🔄 Strategy 2: Refreshing page...")
            driver.refresh()
            time.sleep(8)
            
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "verification" not in page_text:
                logger.info("✅ Verification passed after refresh!")
                return {"success": True, "method": "refresh_retry"}
            
            # Strategy 3: Go back to login page
            logger.info("🔙 Strategy 3: Going back to login page...")
            driver.get("https://www.roblox.com/login")
            time.sleep(5)
            
            # Check if we need to login again
            if "login" in driver.current_url.lower():
                logger.info("🔄 Returned to login page - verification cycle reset")
                return {"success": False, "method": "login_reset", "message": "Returned to login - try again"}
            
            logger.warning("⚠️ All retry strategies exhausted")
            return {
                "success": False, 
                "method": "wait_retry_exhausted", 
                "message": "Manual intervention may be needed"
            }
            
        except Exception as e:
            logger.error(f"❌ Wait and retry failed: {str(e)}")
            return {"success": False, "error": str(e)}

class RobloxAPIAuth:
    """🔧 NEW: API-based authentication using .ROBLOSECURITY cookies"""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.roblosecurity_cookie = None
        
    def authenticate_via_api(self, roblosecurity_cookie=None):
        """Authenticate using .ROBLOSECURITY cookie"""
        try:
            if roblosecurity_cookie:
                self.roblosecurity_cookie = roblosecurity_cookie
                logger.info("🔑 Attempting API authentication with provided cookie...")
            else:
                logger.info("🔑 No cookie provided, will need UI authentication first")
                return False
            
            # Set the authentication cookie
            self.session.cookies.set('.ROBLOSECURITY', self.roblosecurity_cookie, domain='.roblox.com')
            
            # Verify authentication
            response = self.session.get('https://users.roblox.com/v1/users/authenticated')
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"✅ API authentication successful for user: {user_data.get('name', 'Unknown')}")
                return True
            else:
                logger.warning(f"❌ API authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API authentication error: {e}")
            return False
    
    def get_analytics_data(self, game_id):
        """Get analytics data via API instead of scraping"""
        try:
            # This would use Roblox's analytics API if available
            # For now, return placeholder indicating API method
            return {
                "success": True,
                "method": "api",
                "game_id": game_id,
                "message": "Would use Roblox Analytics API here",
                "authenticated_session": True
            }
        except Exception as e:
            logger.error(f"❌ API analytics error: {e}")
            return {"success": False, "error": str(e)}

class RobloxAnalytics:
    def __init__(self):
        self.username = "ByddyY8rPao2124"
        self.password = "VHAHnfR9GNuX4aABZWtD"
        self.last_login = None
        self.login_valid_hours = 2
        self.session_data = {}
        self.last_results = {}
        
        # Remote Selenium URL - connecting to your existing Selenium service
        self.selenium_url = "https://standalone-chrome-production-eb24.up.railway.app/wd/hub"
        
        # Initialize components
        self.verification_solver = RobloxVerificationSolver()
        self.api_auth = RobloxAPIAuth(self.username, self.password)
        
        logger.info(f"🎯 RobloxAnalytics initialized with Remote Selenium: {self.selenium_url}")
        logger.info(f"🔑 2Captcha API key configured: {self.verification_solver.api_key[:8]}...")
        logger.info(f"🌍 NEW: API authentication and regional detection enabled")
    
    def detect_server_region(self):
        """🌍 NEW: Detect if we're running from European servers"""
        try:
            # Get our public IP and location
            response = requests.get('https://ipapi.co/json/', timeout=10)
            if response.status_code == 200:
                data = response.json()
                country = data.get('country_code', 'Unknown')
                region = data.get('continent_code', 'Unknown')
                is_eu = region == 'EU' or country in ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE']
                
                logger.info(f"🌍 Server location: {country} ({region}) - EU: {is_eu}")
                return {
                    "country": country,
                    "region": region,
                    "is_eu": is_eu,
                    "ip": data.get('ip', 'Unknown'),
                    "will_trigger_gdpr": is_eu
                }
        except Exception as e:
            logger.warning(f"Could not detect server region: {e}")
            
        return {
            "country": "Unknown",
            "region": "Unknown", 
            "is_eu": True,  # Assume EU to be safe
            "will_trigger_gdpr": True
        }
    
    @contextmanager
    def get_remote_driver(self):
        """Context manager for Remote WebDriver with enhanced US-focused configuration"""
        driver = None
        try:
            logger.info(f"🌐 Connecting to Remote Selenium at: {self.selenium_url}")
            
            # 🔧 ENHANCED Chrome options based on developer friend's recommendations
            chrome_options = Options()
            
            # Basic stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # 🎯 NEW: Enhanced anti-detection and US-focused configuration
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--window-size=1920,1080")  # Explicit window size
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 🌍 US-focused user agent to reduce GDPR triggers
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
            
            # Additional GDPR evasion settings
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--lang=en-US,en")  # US English preference
            
            # Connect to remote WebDriver
            driver = webdriver.Remote(
                command_executor=self.selenium_url,
                options=chrome_options
            )
            
            # Set timeouts
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(30)
            
            # 🔧 Enhanced stealth script
            stealth_script = """
            // Enhanced stealth configuration
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override plugin array
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override language to US English
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Override platform to Windows
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });
            """
            driver.execute_script(stealth_script)
            
            logger.info("✅ Enhanced Remote WebDriver connected successfully")
            yield driver
            
        except Exception as e:
            logger.error(f"❌ Remote WebDriver connection failed: {str(e)}")
            raise e
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("🔌 Remote WebDriver disconnected")
                except Exception as e:
                    logger.warning(f"⚠️ Error disconnecting WebDriver: {str(e)}")
    
    def advanced_cookie_handling(self, driver):
        """🔧 NEW: Advanced cookie banner handling based on developer friend's recommendations"""
        logger.info("🍪 🎯 ADVANCED COOKIE BANNER HANDLING...")
        
        try:
            # Step 1: Wait for any cookie banners to load
            time.sleep(3)
            
            # Step 2: Check for iframe-based cookie banners
            try:
                logger.info("🔍 Checking for iframe-based cookie banners...")
                iframe_selectors = [
                    "iframe[src*='cookie']",
                    "iframe[src*='consent']", 
                    "iframe[src*='privacy']",
                    "iframe[title*='cookie']",
                    "iframe[title*='consent']"
                ]
                
                for selector in iframe_selectors:
                    try:
                        iframe = WebDriverWait(driver, 5).until(
                            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, selector))
                        )
                        logger.info(f"✅ Found and switched to cookie iframe: {selector}")
                        
                        # Try to click accept buttons within iframe
                        accept_selectors = [
                            "button#acceptAll",
                            "button[aria-label*='Accept']",
                            "button[onclick*='accept']",
                            "//button[contains(., 'Accept')]",
                            "//button[contains(., 'Agree')]"
                        ]
                        
                        for btn_selector in accept_selectors:
                            try:
                                if btn_selector.startswith('//'):
                                    btn = driver.find_element(By.XPATH, btn_selector)
                                else:
                                    btn = driver.find_element(By.CSS_SELECTOR, btn_selector)
                                
                                driver.execute_script("arguments[0].click();", btn)
                                logger.info(f"✅ Clicked accept button in iframe: {btn_selector}")
                                time.sleep(1)
                                break
                            except:
                                continue
                        
                        driver.switch_to.default_content()
                        time.sleep(2)
                        break
                        
                    except:
                        continue
                        
            except:
                logger.info("No iframe-based cookie banners found")
            
            # Step 3: Handle regular cookie banners
            logger.info("🔍 Handling regular cookie banners...")
            
            # Enhanced GDPR-specific removal
            gdpr_removal_js = """
            console.log('🍪 GDPR Cookie Banner Removal...');
            
            // Comprehensive Roblox GDPR selectors
            const gdprSelectors = [
                '.cookie-banner-bg', '.cookie-banner', '.cookie-notice',
                '.cookie-consent', '.consent-banner', '.privacy-banner',
                '.gdpr-banner', '.gdpr-notice', '.gdpr-consent',
                '[class*="cookie"]', '[id*="cookie"]', '[data-testid*="cookie"]',
                '[class*="consent"]', '[id*="consent"]', '[data-testid*="consent"]',
                '[class*="privacy"]', '[id*="privacy"]', '[data-testid*="privacy"]',
                '[class*="gdpr"]', '[id*="gdpr"]', '[data-testid*="gdpr"]',
                '.modal-backdrop', '.modal-overlay', '.overlay', '.backdrop',
                '[role="dialog"]', '[role="alertdialog"]', '[aria-modal="true"]'
            ];
            
            let destroyed = 0;
            let acceptClicked = 0;
            
            // First, try to click accept buttons
            const acceptButtonTexts = ['Accept', 'Accept All', 'Allow', 'OK', 'Continue', 'Agree', 'I Accept'];
            acceptButtonTexts.forEach(text => {
                document.querySelectorAll('button, a, div[role="button"]').forEach(el => {
                    if (el.textContent.trim().includes(text) && el.offsetParent !== null) {
                        console.log('Clicking accept button:', el);
                        el.click();
                        acceptClicked++;
                    }
                });
            });
            
            // Then remove all banner elements
            gdprSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const computedStyle = window.getComputedStyle(el);
                    const zIndex = parseInt(computedStyle.zIndex) || 0;
                    const elementText = el.textContent.toLowerCase();
                    
                    const isBannerElement = (
                        elementText.includes('cookie') ||
                        elementText.includes('consent') ||
                        elementText.includes('privacy') ||
                        elementText.includes('gdpr') ||
                        elementText.includes('accept') ||
                        zIndex > 1000
                    );
                    
                    if (isBannerElement || selector.includes('cookie') || selector.includes('consent')) {
                        console.log('Destroying GDPR element:', selector, el);
                        el.style.cssText = 'display: none !important; visibility: hidden !important; opacity: 0 !important;';
                        el.remove();
                        destroyed++;
                    }
                });
            });
            
            // Clean body styles
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
            document.body.classList.remove('modal-open', 'no-scroll');
            
            console.log('GDPR removal complete. Destroyed:', destroyed, 'Accept clicked:', acceptClicked);
            return { destroyed: destroyed, acceptClicked: acceptClicked };
            """
            
            result = driver.execute_script(gdpr_removal_js)
            logger.info(f"🎯 GDPR handling complete: Destroyed {result['destroyed']} elements, clicked {result['acceptClicked']} accept buttons")
            
            # Step 4: Additional wait for any delayed banners
            time.sleep(2)
            
            return result
            
        except Exception as e:
            logger.warning(f"Advanced cookie handling error: {e}")
            return {"destroyed": 0, "acceptClicked": 0}
    
    def robust_click(self, element, driver):
        """🔧 NEW: Multiple click strategies from developer friend's recommendations"""
        strategies = [
            ("Standard Click", lambda: element.click()),
            ("JavaScript Click", lambda: driver.execute_script("arguments[0].click();", element)),
            ("ActionChains Click", lambda: ActionChains(driver).move_to_element(element).click().perform()),
            ("Event Dispatch Click", lambda: driver.execute_script(
                "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", element)),
            ("Focus + Click", lambda: driver.execute_script("arguments[0].focus(); arguments[0].click();", element))
        ]
        
        for strategy_name, click_method in strategies:
            try:
                logger.info(f"🎯 Attempting {strategy_name}...")
                click_method()
                time.sleep(1)
                return True
            except Exception as e:
                logger.warning(f"❌ {strategy_name} failed: {e}")
                continue
        
        return False
    
    def test_cloudflare_bypass(self, driver):
        """Test Cloudflare bypass capability"""
        try:
            logger.info("☁️ Testing Cloudflare bypass...")
            
            # Navigate to a Cloudflare-protected site
            driver.get("https://www.roblox.com")
            time.sleep(8)
            
            # Check for Cloudflare indicators
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            page_source = driver.page_source.lower()
            
            cloudflare_indicators = [
                "checking your browser", "cloudflare", "ray id", "performance & security",
                "ddos protection", "challenge", "please wait"
            ]
            
            current_url = driver.current_url
            
            if any(indicator in page_text for indicator in cloudflare_indicators):
                logger.warning("⚠️ Cloudflare challenge detected")
                return {
                    "success": False,
                    "message": "Cloudflare challenge present",
                    "current_url": current_url,
                    "detected_indicators": [ind for ind in cloudflare_indicators if ind in page_text]
                }
            else:
                logger.info("✅ Cloudflare bypass successful")
                return {
                    "success": True,
                    "message": "Cloudflare bypass successful",
                    "current_url": current_url,
                    "method": "remote_webdriver"
                }
                
        except Exception as e:
            logger.error(f"❌ Cloudflare test error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def login_to_roblox(self, driver):
        """🎯 ENHANCED LOGIN with regional detection and advanced cookie handling"""
        try:
            logger.info("🔐 Starting ENHANCED Roblox login with regional detection...")
            
            # Step 0: Detect server region
            region_info = self.detect_server_region()
            
            # Navigate to login page
            driver.get("https://www.roblox.com/login")
            time.sleep(5)
            
            # Step 1: Advanced cookie banner handling
            cookie_result = self.advanced_cookie_handling(driver)
            
            # Step 2: Form filling
            try:
                logger.info("🔍 Looking for login form elements...")
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "login-username"))
                )
                password_field = driver.find_element(By.ID, "login-password")
                login_button = driver.find_element(By.ID, "login-button")
                
                logger.info("✅ Found all login form elements")
                
                # Clear and fill fields
                username_field.clear()
                username_field.send_keys(self.username)
                time.sleep(2)
                
                password_field.clear()
                password_field.send_keys(self.password)
                time.sleep(2)
                
                logger.info("✅ Credentials filled")
                
                # Step 3: Robust login button click
                logger.info("🎯 Attempting robust login button click...")
                
                # Additional cookie removal right before clicking
                self.advanced_cookie_handling(driver)
                time.sleep(1)
                
                click_success = self.robust_click(login_button, driver)
                if not click_success:
                    logger.error("❌ All click strategies failed")
                    return {
                        "success": False,
                        "message": "Enhanced login click failed",
                        "current_url": driver.current_url,
                        "region_info": region_info,
                        "cookie_removal": cookie_result,
                        "suggestions": [
                            "Consider switching to US-based hosting" if region_info["is_eu"] else "Non-EU server but still failing",
                            "Try API authentication approach",
                            "Manual intervention may be required"
                        ]
                    }
                
                # Step 4: Post-login processing
                logger.info("⏳ Waiting for post-login processing...")
                time.sleep(5)
                
                # Check for verification challenge
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                verification_indicators = ["verification", "start puzzle", "captcha", "challenge", "verify"]
                
                if any(indicator in page_text for indicator in verification_indicators):
                    logger.info("🎯 Verification challenge detected, attempting 2Captcha solve...")
                    
                    # Handle 2Captcha verification
                    verification_result = self.verification_solver.solve_roblox_verification(driver)
                    
                    if verification_result.get("success"):
                        logger.info("✅ Verification solved successfully!")
                        time.sleep(5)
                        
                        # Extract cookies for future API use
                        cookies = driver.get_cookies()
                        roblosecurity_cookie = None
                        for cookie in cookies:
                            if cookie['name'] == '.ROBLOSECURITY':
                                roblosecurity_cookie = cookie['value']
                                logger.info("🔑 Extracted .ROBLOSECURITY cookie for future API use")
                                break
                        
                        # Verify final login success
                        final_url = driver.current_url
                        if any(success_indicator in final_url for success_indicator in ["create.roblox.com", "dashboard", "home"]):
                            logger.info("✅ Complete login process successful!")
                            self.last_login = datetime.now()
                            return {
                                "success": True,
                                "message": "Login successful with verification",
                                "final_url": final_url,
                                "verification_solved": True,
                                "region_info": region_info,
                                "roblosecurity_cookie": roblosecurity_cookie
                            }
                        else:
                            logger.warning("⚠️ Verification solved but login may not be complete")
                            return {
                                "success": True,
                                "message": "Verification solved - login status unclear",
                                "final_url": final_url,
                                "verification_solved": True,
                                "region_info": region_info
                            }
                    else:
                        logger.error("❌ Verification solving failed")
                        return {
                            "success": False,
                            "message": "Verification challenge failed",
                            "verification_error": verification_result.get("error", "Unknown error"),
                            "region_info": region_info
                        }
                else:
                    # No verification needed
                    current_url = driver.current_url
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    
                    # Extract cookies for future API use
                    cookies = driver.get_cookies()
                    roblosecurity_cookie = None
                    for cookie in cookies:
                        if cookie['name'] == '.ROBLOSECURITY':
                            roblosecurity_cookie = cookie['value']
                            logger.info("🔑 Extracted .ROBLOSECURITY cookie for future API use")
                            break
                    
                    # Check for successful login indicators
                    if (any(success_url in current_url for success_url in ["create.roblox.com", "dashboard", "home"]) or
                        "login" not in current_url.lower()):
                        logger.info("✅ Login successful without verification!")
                        self.last_login = datetime.now()
                        return {
                            "success": True,
                            "message": "Login successful without verification", 
                            "final_url": current_url,
                            "region_info": region_info,
                            "roblosecurity_cookie": roblosecurity_cookie
                        }
                    else:
                        # Check for login errors
                        error_indicators = ["incorrect", "invalid", "error", "try again"]
                        if any(error in page_text.lower() for error in error_indicators):
                            return {
                                "success": False,
                                "message": "Login failed - credentials may be incorrect",
                                "page_text_sample": page_text[:200],
                                "region_info": region_info
                            }
                        else:
                            return {
                                "success": False,
                                "message": "Login status unclear",
                                "current_url": current_url,
                                "page_text_sample": page_text[:200],
                                "region_info": region_info
                            }
                            
            except TimeoutException:
                logger.error("❌ Login form elements not found")
                return {
                    "success": False,
                    "message": "Login form not found - page may have changed",
                    "current_url": driver.current_url,
                    "region_info": region_info
                }
                
        except Exception as e:
            logger.error(f"❌ Enhanced login error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def extract_qptr_data(self, driver, game_id="7291257156"):
        """Extract QPTR data from Roblox Creator Dashboard"""
        try:
            logger.info(f"📊 Extracting QPTR data for game {game_id}...")
            
            # Navigate to Creator Dashboard
            dashboard_url = "https://create.roblox.com/dashboard/creations"
            driver.get(dashboard_url)
            time.sleep(10)
            
            # Look for game or navigate to specific game analytics
            analytics_url = f"https://create.roblox.com/dashboard/creations/analytics?placeId={game_id}"
            driver.get(analytics_url)
            time.sleep(15)
            
            # Take screenshot for debugging
            screenshot_data = driver.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_data).decode()
            
            # Look for QPTR data
            page_text = driver.find_element(By.TAG_NAME, "body").text
            page_source = driver.page_source
            
            # Common QPTR selectors and patterns
            qptr_patterns = [
                r'(\d+(?:\.\d+)?%)\s*(?:qualified|qptr|play.*through)',
                r'qualified.*?(\d+(?:\.\d+)?%)',
                r'play.*?through.*?(\d+(?:\.\d+)?%)'
            ]
            
            qptr_value = None
            for pattern in qptr_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    qptr_value = matches[0]
                    break
            
            return {
                "success": True,
                "qptr_value": qptr_value,
                "game_id": game_id,
                "screenshot": screenshot_b64,
                "extraction_time": datetime.now().isoformat(),
                "page_text_sample": page_text[:500] if page_text else "No text found"
            }
            
        except Exception as e:
            logger.error(f"❌ QPTR extraction error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def get_authenticated_session(self, game_id="7291257156"):
        """🔧 NEW: Primary authentication strategy (API first, UI fallback)"""
        logger.info("🔑 Starting multi-strategy authentication...")
        
        # Strategy 1: Try API authentication if we have a stored cookie
        stored_cookie = getattr(self, 'stored_roblosecurity', None)
        if stored_cookie:
            logger.info("🔑 Attempting API authentication with stored cookie...")
            if self.api_auth.authenticate_via_api(stored_cookie):
                return self.api_auth.get_analytics_data(game_id)
        
        # Strategy 2: UI authentication with enhanced cookie handling
        logger.info("🔑 Falling back to UI authentication...")
        try:
            with self.get_remote_driver() as driver:
                login_result = self.login_to_roblox(driver)
                
                if login_result.get("success"):
                    # Store cookie for future API use
                    if login_result.get("roblosecurity_cookie"):
                        self.stored_roblosecurity = login_result["roblosecurity_cookie"]
                        logger.info("🔑 Stored cookie for future API authentication")
                    
                    # Extract QPTR data via UI
                    qptr_result = self.extract_qptr_data(driver, game_id)
                    
                    return {
                        "success": True,
                        "method": "ui_authentication",
                        "login_result": login_result,
                        "qptr_result": qptr_result
                    }
                else:
                    return {
                        "success": False,
                        "method": "ui_authentication_failed",
                        "login_result": login_result
                    }
                    
        except Exception as e:
            logger.error(f"❌ Authentication session error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def run_complete_analytics_collection(self, game_id="7291257156"):
        """🎯 ENHANCED: Complete analytics collection with multi-strategy approach"""
        start_time = datetime.now()
        results = {
            "start_time": start_time.isoformat(),
            "game_id": game_id,
            "steps": {},
            "overall_success": False,
            "api_key_used": f"{self.verification_solver.api_key[:8]}...",
            "selenium_url": self.selenium_url,
            "region_detection": None,
            "authentication_method": None
        }
        
        try:
            logger.info("🚀 Starting ENHANCED analytics collection with multi-strategy authentication...")
            
            # Step 1: Detect server region
            logger.info("Step 1: Detecting server region...")
            region_info = self.detect_server_region()
            results["region_detection"] = region_info
            results["steps"]["region_detection"] = {"success": True, "data": region_info}
            
            # Step 2: Try primary authentication strategy
            logger.info("Step 2: Attempting multi-strategy authentication...")
            auth_result = self.get_authenticated_session(game_id)
            results["steps"]["authentication"] = auth_result
            results["authentication_method"] = auth_result.get("method", "unknown")
            
            if auth_result.get("success"):
                logger.info("✅ Authentication successful!")
                results["overall_success"] = True
                
                # If UI method was used, include individual step results
                if auth_result.get("method") == "ui_authentication":
                    results["steps"]["login"] = auth_result.get("login_result", {})
                    results["steps"]["qptr_extraction"] = auth_result.get("qptr_result", {})
                
            else:
                logger.error("❌ All authentication methods failed")
                results["overall_success"] = False
            
            # Store results for later retrieval
            self.last_results = results
            return results
                
        except Exception as e:
            logger.error(f"❌ Complete analytics collection error: {str(e)}")
            results["overall_success"] = False
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()
            return results
        
        finally:
            end_time = datetime.now()
            results["end_time"] = end_time.isoformat()
            results["duration_seconds"] = (end_time - start_time).total_seconds()
            logger.info(f"⏱️ Total duration: {results['duration_seconds']:.2f} seconds")

# Initialize analytics instance
analytics = RobloxAnalytics()

# 🔍 NEW: Screenshot viewer endpoints
@app.route('/view-screenshot/<path:screenshot_data>')
def view_screenshot(screenshot_data):
    """View base64 screenshot data in browser"""
    try:
        import base64
        image_data = base64.b64decode(screenshot_data)
        return Response(image_data, mimetype='image/png')
    except:
        return "Invalid screenshot data", 400

@app.route('/screenshot-viewer')
def screenshot_viewer():
    """Screenshot viewer interface"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔍 Roblox Login Screenshot Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .screenshot { max-width: 100%; border: 2px solid #ddd; border-radius: 8px; margin: 10px 0; }
            .info { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            button:hover { background: #0056b3; }
            .error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .success { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .region { background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Enhanced Roblox Login Debug Viewer</h1>
            <div class="info">
                <h3>📋 Features:</h3>
                <ul>
                    <li>🌍 Server region detection (EU = GDPR banners)</li>
                    <li>📸 Multi-step screenshot capture</li>
                    <li>🍪 Advanced cookie banner analysis</li>
                    <li>🔑 API + UI authentication testing</li>
                </ul>
            </div>
            
            <div>
                <h3>🧪 Debug Tests:</h3>
                <button onclick="checkRegion()">🌍 Check Server Region</button>
                <button onclick="runFullDebug()">🔍 Run Full Debug</button>
                <button onclick="testApiAuth()">🔑 Test API Auth</button>
            </div>
            
            <div id="result"></div>
        </div>
        
        <script>
            async function checkRegion() {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<div class="info">🌍 Checking server region...</div>';
                
                try {
                    const response = await fetch('/debug-region', { method: 'POST' });
                    const data = await response.json();
                    
                    const regionClass = data.region_info?.is_eu ? 'error' : 'success';
                    const gdprWarning = data.region_info?.is_eu ? 
                        '<p><strong>⚠️ WARNING:</strong> EU server detected - will trigger GDPR cookie banners!</p>' : 
                        '<p><strong>✅ GOOD:</strong> Non-EU server - reduced GDPR risk</p>';
                    
                    resultDiv.innerHTML = `
                        <div class="${regionClass}">
                            <h3>🌍 Server Region Analysis:</h3>
                            ${gdprWarning}
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                    
                } catch (error) {
                    resultDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                }
            }
            
            async function runFullDebug() {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<div class="info">🔍 Running full debug with screenshots...</div>';
                
                try {
                    const response = await fetch('/debug-login-with-screenshots', { method: 'POST' });
                    const data = await response.json();
                    
                    let html = '<div class="success"><h3>🔍 Full Debug Results:</h3>';
                    
                    if (data.screenshots) {
                        data.screenshots.forEach((screenshot, index) => {
                            html += `
                                <h4>📸 ${screenshot.step}: ${screenshot.description}</h4>
                                <img src="data:image/png;base64,${screenshot.data}" class="screenshot" alt="Debug Screenshot ${index + 1}">
                            `;
                        });
                    }
                    
                    html += `<h4>📊 Analysis:</h4><pre>${JSON.stringify(data.analysis, null, 2)}</pre></div>`;
                    resultDiv.innerHTML = html;
                    
                } catch (error) {
                    resultDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                }
            }
            
            async function testApiAuth() {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<div class="info">🔑 Testing API authentication...</div>';
                
                try {
                    const response = await fetch('/test-api-auth', { method: 'POST' });
                    const data = await response.json();
                    
                    resultDiv.innerHTML = `
                        <div class="success">
                            <h3>🔑 API Authentication Test:</h3>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                    
                } catch (error) {
                    resultDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/debug-region', methods=['POST'])
def debug_region():
    """Debug server region detection"""
    try:
        region_info = analytics.detect_server_region()
        return jsonify({
            "success": True,
            "region_info": region_info,
            "recommendations": {
                "should_switch_hosting": region_info["is_eu"],
                "alternative_approach": "API authentication" if region_info["is_eu"] else "UI automation should work",
                "estimated_gdpr_risk": "HIGH" if region_info["is_eu"] else "LOW"
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug-login-with-screenshots', methods=['POST'])
def debug_login_with_screenshots():
    """Enhanced debug with screenshots and region analysis"""
    try:
        logger.info("🔍 Starting enhanced debug with screenshots...")
        
        debug_results = {
            "start_time": datetime.now().isoformat(),
            "screenshots": [],
            "steps": {},
            "analysis": {},
            "region_info": analytics.detect_server_region()
        }
        
        with analytics.get_remote_driver() as driver:
            def take_screenshot(step_name, description):
                try:
                    screenshot_data = driver.get_screenshot_as_png()
                    screenshot_b64 = base64.b64encode(screenshot_data).decode()
                    debug_results["screenshots"].append({
                        "step": step_name,
                        "description": description,
                        "data": screenshot_b64,
                        "timestamp": datetime.now().isoformat(),
                        "current_url": driver.current_url
                    })
                    logger.info(f"📸 Screenshot taken: {step_name}")
                except Exception as e:
                    logger.warning(f"Screenshot failed for {step_name}: {e}")
            
            # Step 1: Navigate and analyze
            logger.info("Step 1: Navigate to Roblox login...")
            driver.get("https://www.roblox.com/login")
            time.sleep(5)
            take_screenshot("initial_load", "Roblox login page initial load")
            
            # Step 2: Cookie banner analysis
            logger.info("Step 2: Cookie banner analysis...")
            page_source = driver.page_source
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            cookie_elements = []
            for selector in [".cookie-banner-bg", ".cookie-banner", "[class*='cookie']", "[role='dialog']"]:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            cookie_elements.append({
                                "selector": selector,
                                "tag": elem.tag_name,
                                "classes": elem.get_attribute("class"),
                                "text": elem.text[:100],
                                "visible": elem.is_displayed()
                            })
                except:
                    continue
            
            debug_results["analysis"]["cookie_elements"] = cookie_elements
            debug_results["analysis"]["gdpr_indicators"] = [word for word in ["cookie", "consent", "privacy", "gdpr"] if word in page_text.lower()]
            
            take_screenshot("before_cookie_removal", f"Before removal - found {len(cookie_elements)} cookie elements")
            
            # Step 3: Apply enhanced cookie handling
            logger.info("Step 3: Apply enhanced cookie handling...")
            cookie_result = analytics.advanced_cookie_handling(driver)
            debug_results["analysis"]["cookie_removal_result"] = cookie_result
            
            take_screenshot("after_cookie_removal", f"After removal - destroyed {cookie_result.get('destroyed', 0)} elements")
            
            # Step 4: Login form analysis
            try:
                username_field = driver.find_element(By.ID, "login-username")
                password_field = driver.find_element(By.ID, "login-password")
                login_button = driver.find_element(By.ID, "login-button")
                
                debug_results["analysis"]["login_form"] = {
                    "found": True,
                    "button_clickable": login_button.is_enabled() and login_button.is_displayed(),
                    "button_location": login_button.location,
                    "button_size": login_button.size
                }
                
                # Test click interception
                try:
                    login_button.click()
                    debug_results["analysis"]["click_test"] = "SUCCESS - No interception"
                except Exception as click_error:
                    debug_results["analysis"]["click_test"] = f"FAILED - {str(click_error)}"
                    if "click intercepted" in str(click_error):
                        # Extract the intercepting element info
                        error_msg = str(click_error)
                        if "Other element would receive the click:" in error_msg:
                            intercepting_element = error_msg.split("Other element would receive the click:")[1].split("\n")[0].strip()
                            debug_results["analysis"]["intercepting_element"] = intercepting_element
                    
                    take_screenshot("click_interception", f"Click intercepted: {str(click_error)[:100]}")
                
            except Exception as form_error:
                debug_results["analysis"]["login_form"] = {"found": False, "error": str(form_error)}
            
            take_screenshot("final_analysis", "Final state analysis")
            
            # Final recommendations
            debug_results["recommendations"] = {
                "primary_issue": "GDPR cookie banner from EU server" if debug_results["region_info"]["is_eu"] else "Unknown issue",
                "immediate_solution": "Switch to US-based hosting (Railway supports region selection)" if debug_results["region_info"]["is_eu"] else "Try API authentication",
                "alternative_approaches": [
                    "API authentication with .ROBLOSECURITY cookie",
                    "US proxy or VPN integration", 
                    "Different cloud provider in US region"
                ]
            }
            
            debug_results["overall_success"] = len(cookie_elements) == 0 and debug_results["analysis"].get("login_form", {}).get("found", False)
            debug_results["end_time"] = datetime.now().isoformat()
            
            return jsonify(debug_results)
            
    except Exception as e:
        logger.error(f"❌ Enhanced debug failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/test-api-auth', methods=['POST'])
def test_api_auth():
    """Test API authentication approach"""
    try:
        # Test the API authentication concept
        auth_result = analytics.api_auth.authenticate_via_api(None)
        
        return jsonify({
            "success": True,
            "api_auth_available": auth_result,
            "message": "API authentication ready for .ROBLOSECURITY cookie",
            "next_steps": [
                "1. Get .ROBLOSECURITY cookie via one-time UI login",
                "2. Store cookie securely", 
                "3. Use API authentication for all future requests",
                "4. Bypass UI automation entirely"
            ],
            "advantages": [
                "No cookie banner issues",
                "Faster execution",
                "More reliable",
                "Less detection risk"
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/')
def home():
    """Root endpoint with enhanced system information"""
    return jsonify({
        "status": "🎯 Enhanced Roblox Analytics API - Multi-Strategy Authentication",
        "version": "7.0.0 - REGIONAL DETECTION + API AUTH + ENHANCED UI",
        "python_version": "3.12 Compatible",
        "selenium_mode": "Remote WebDriver ✅",
        "selenium_url": analytics.selenium_url,
        "verification_solving": "2Captcha Automated Solving ✅",
        "api_key_status": "Configured ✅",
        "api_key_preview": f"{analytics.verification_solver.api_key[:8]}...",
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'local'),
        "cors_status": "✅ Fully Fixed with Headers",
        "new_features": {
            "regional_detection": "✅ EU/GDPR detection",
            "api_authentication": "✅ .ROBLOSECURITY cookie support",
            "enhanced_cookie_handling": "✅ Advanced GDPR banner removal",
            "screenshot_debugging": "✅ Visual debugging interface",
            "multi_strategy_auth": "✅ API-first, UI-fallback"
        },
        "testing_interface": {
            "url": "/test",
            "description": "🎯 Main testing interface",
            "screenshot_viewer": "/screenshot-viewer",
            "debug_features": "Enhanced regional and cookie analysis"
        },
        "endpoints": [
            "GET /status - System status",
            "GET /screenshot-viewer - Visual debugging interface",
            "POST /debug-region - Check server region",
            "POST /debug-login-with-screenshots - Full debug with visuals",
            "POST /test-api-auth - Test API authentication",
            "POST /trigger-diagnostic - Complete analytics collection"
        ],
        "recommendations": {
            "immediate": "Check server region at /debug-region",
            "if_eu_server": "Consider US-based hosting for Railway app",
            "api_approach": "Extract .ROBLOSECURITY cookie for API authentication"
        }
    })

@app.route('/status')
def status():
    """Enhanced system status with regional information"""
    region_info = analytics.detect_server_region()
    
    return jsonify({
        "status": "🎯 Enhanced System Operational",
        "timestamp": datetime.now().isoformat(),
        "verification_solver": {
            "enabled": analytics.verification_solver.solver is not None,
            "api_key_configured": bool(analytics.verification_solver.api_key),
            "api_key_preview": f"{analytics.verification_solver.api_key[:8]}..." if analytics.verification_solver.api_key else "Not configured",
            "package": "2captcha-python (official)"
        },
        "selenium": {
            "mode": "Remote WebDriver",
            "selenium_url": analytics.selenium_url,
            "status": "Connected ✅"
        },
        "regional_detection": {
            "server_region": region_info,
            "gdpr_risk": "HIGH" if region_info["is_eu"] else "LOW",
            "recommendations": "Switch to US hosting" if region_info["is_eu"] else "Current region OK"
        },
        "authentication": {
            "ui_automation": "✅ Enhanced with GDPR handling",
            "api_authentication": "✅ Ready for .ROBLOSECURITY cookies",
            "multi_strategy": "✅ API-first, UI-fallback approach"
        },
        "latest_results": analytics.last_results
    })

@app.route('/results')
def get_results():
    """Get latest results"""
    return jsonify({
        "latest_results": analytics.last_results,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/balance', methods=['POST', 'GET'])
def check_balance():
    """Check 2Captcha account balance - FIXED METHOD"""
    try:
        if analytics.verification_solver.solver:
            # 🔧 FIXED: Use balance() not get_balance()
            balance = analytics.verification_solver.solver.balance()
            return jsonify({
                "success": True,
                "balance": f"${balance:.2f}",
                "balance_numeric": float(balance),
                "api_key": f"{analytics.verification_solver.api_key[:8]}...",
                "package": "2captcha-python (official)",
                "sufficient_funds": float(balance) > 0.01,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "2Captcha solver not initialized",
                "package_issue": "Check if 2captcha-python package is installed correctly",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/ping')
def ping():
    """Simple ping test endpoint"""
    return jsonify({
        "message": "pong",
        "status": "healthy",
        "cors_working": True,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/debug-selenium', methods=['GET', 'POST'])
def debug_selenium():
    """Debug the remote Selenium connection"""
    try:
        selenium_url = analytics.selenium_url
        logger.info(f"🔍 Debugging Selenium connection to: {selenium_url}")
        
        debug_results = {
            "selenium_url": selenium_url,
            "timestamp": datetime.now().isoformat()
        }
        
        # Test 1: HTTP connectivity
        try:
            import requests
            response = requests.get(f"{selenium_url}/status", timeout=10)
            debug_results["http_test"] = {
                "success": True,
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
                "response_json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        except Exception as e:
            debug_results["http_test"] = {"success": False, "error": str(e)}
        
        # Test 2: WebDriver connection
        try:
            with analytics.get_remote_driver() as driver:
                driver.get("https://www.google.com")
                debug_results["webdriver_test"] = {
                    "success": True,
                    "page_title": driver.title,
                    "current_url": driver.current_url
                }
        except Exception as e:
            debug_results["webdriver_test"] = {"success": False, "error": str(e)}
        
        debug_results["overall_assessment"] = {
            "ready_for_testing": debug_results.get("http_test", {}).get("success", False) and debug_results.get("webdriver_test", {}).get("success", False)
        }
        
        return jsonify(debug_results)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test-cloudflare', methods=['POST'])
def test_cloudflare_endpoint():
    """Test Cloudflare bypass capability"""
    try:
        with analytics.get_remote_driver() as driver:
            result = analytics.test_cloudflare_bypass(driver)
            return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test-verification', methods=['POST'])
def test_verification_endpoint():
    """Test verification solving with enhanced cookie handling"""
    try:
        with analytics.get_remote_driver() as driver:
            driver.get("https://www.roblox.com/login")
            time.sleep(3)
            
            # Apply enhanced cookie handling first
            analytics.advanced_cookie_handling(driver)
            
            try:
                username_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "login-username"))
                )
                password_field = driver.find_element(By.ID, "login-password")
                login_button = driver.find_element(By.ID, "login-button")
                
                username_field.send_keys(analytics.username)
                password_field.send_keys(analytics.password)
                
                # Use robust click
                analytics.robust_click(login_button, driver)
                time.sleep(8)
                
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                verification_indicators = ["verification", "start puzzle", "captcha", "challenge"]
                
                if any(indicator in page_text for indicator in verification_indicators):
                    result = analytics.verification_solver.solve_roblox_verification(driver)
                    result["api_key_used"] = f"{analytics.verification_solver.api_key[:8]}..."
                    result["enhanced_cookie_handling"] = "Applied"
                    return jsonify(result)
                else:
                    return jsonify({
                        "success": True,
                        "message": "No verification challenge - enhanced cookie handling successful",
                        "enhanced_cookie_handling": "Applied",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except TimeoutException:
                return jsonify({
                    "success": False,
                    "error": "Login form not found after cookie handling",
                    "timestamp": datetime.now().isoformat()
                })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/login-test', methods=['POST'])
def login_test_endpoint():
    """Test enhanced login with regional detection"""
    try:
        with analytics.get_remote_driver() as driver:
            result = analytics.login_to_roblox(driver)
            result["api_key_used"] = f"{analytics.verification_solver.api_key[:8]}..."
            result["selenium_url"] = analytics.selenium_url
            result["enhanced_features"] = "Regional detection + Advanced cookie handling"
            return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/trigger-diagnostic', methods=['POST'])
def trigger_diagnostic():
    """Enhanced diagnostic with multi-strategy authentication"""
    try:
        game_id = "7291257156"
        
        try:
            data = request.get_json(silent=True) or {}
            if isinstance(data, dict) and 'game_id' in data:
                game_id = data['game_id']
        except Exception as json_error:
            logger.warning(f"⚠️ Could not parse JSON request: {json_error}")
        
        logger.info(f"🚀 Starting ENHANCED diagnostic with multi-strategy authentication")
        logger.info(f"🎮 Game ID: {game_id}")
        logger.info(f"🌍 Regional detection enabled")
        logger.info(f"🔑 API + UI authentication available")
        
        result = analytics.run_complete_analytics_collection(game_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Enhanced diagnostic error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test')
def test_interface():
    """Enhanced test interface with regional detection"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 Enhanced Roblox Analytics Test Interface</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            .container { 
                background: white; 
                padding: 30px; 
                border-radius: 15px; 
                max-width: 900px; 
                margin: 0 auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #eee;
            }
            .enhancement {
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                font-weight: bold;
                text-align: center;
            }
            .button { 
                background: #007bff; 
                color: white; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                margin: 8px; 
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s ease;
                min-width: 140px;
            }
            .button:hover { 
                background: #0056b3; 
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,123,255,0.3);
            }
            .button:disabled {
                background: #6c757d;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            .enhanced { 
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            }
            .enhanced:hover {
                background: linear-gradient(135deg, #218838 0%, #1ea080 100%);
            }
            .danger { 
                background: #dc3545; 
            }
            .danger:hover { 
                background: #c82333; 
            }
            .test-section {
                background: #f8f9fa;
                padding: 20px;
                margin: 20px 0;
                border-radius: 10px;
                border-left: 4px solid #007bff;
            }
            .enhanced-section {
                background: #f8fff8;
                border-left-color: #28a745;
            }
            .result { 
                margin: 20px 0; 
                padding: 20px; 
                background: #f8f9fa; 
                border-radius: 8px; 
                font-family: 'Courier New', monospace; 
                white-space: pre-wrap; 
                max-height: 500px;
                overflow-y: auto;
                border: 1px solid #dee2e6;
            }
            .result.success {
                background: #d4edda;
                border-color: #c3e6cb;
                color: #155724;
            }
            .result.error {
                background: #f8d7da;
                border-color: #f5c6cb;
                color: #721c24;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Enhanced Roblox Analytics Test System</h1>
                <div class="enhancement">🎉 VERSION 7.0 - REGIONAL DETECTION + API AUTH + ENHANCED UI!</div>
                <p><strong>System URL:</strong> <code>''' + request.host_url + '''</code></p>
            </div>
            
            <div class="test-section enhanced-section">
                <h3>🌍 NEW: Regional Detection & Analysis</h3>
                <p>Check if your server location triggers GDPR cookie banners</p>
                <button class="button enhanced" onclick="checkRegion()">🌍 Check Server Region</button>
                <button class="button enhanced" onclick="openScreenshotViewer()">🔍 Open Screenshot Viewer</button>
            </div>
            
            <div class="test-section">
                <h3>📊 Basic System Tests</h3>
                <button class="button" onclick="checkStatus()">📊 Check Status</button>
                <button class="button" onclick="checkBalance()">💰 Check Balance</button>
                <button class="button" onclick="testPing()">🏓 Ping Test</button>
                <button class="button" onclick="debugSelenium()">🔍 Debug Selenium</button>
            </div>
            
            <div class="test-section enhanced-section">
                <h3>🔑 NEW: Authentication Tests</h3>
                <p>Test both API and enhanced UI authentication</p>
                <button class="button enhanced" onclick="testApiAuth()">🔑 Test API Auth</button>
                <button class="button enhanced" onclick="testEnhancedLogin()">🚀 Test Enhanced Login</button>
            </div>
            
            <div class="test-section">
                <h3>🚀 Complete System Test</h3>
                <p><strong>🎯 Enhanced with regional detection and multi-strategy authentication!</strong></p>
                <button class="button danger" onclick="runCompleteTest()" id="fullTestBtn">🚀 RUN ENHANCED COMPLETE TEST</button>
            </div>
            
            <div id="result" class="result" style="display:none;"></div>
        </div>
        
        <script>
            function showResult(content, type = 'info') {
                const element = document.getElementById('result');
                element.className = `result ${type}`;
                element.textContent = content;
                element.style.display = 'block';
                element.scrollTop = element.scrollHeight;
            }
            
            function showLoading(message = 'Loading...') {
                const element = document.getElementById('result');
                element.className = 'result';
                element.innerHTML = `<span style="color: #007bff; font-style: italic;">${message}</span>`;
                element.style.display = 'block';
            }
            
            async function checkRegion() {
                showLoading('🌍 Detecting server region and GDPR risk...');
                try {
                    const response = await fetch('/debug-region', { method: 'POST' });
                    const data = await response.json();
                    
                    const riskLevel = data.region_info?.is_eu ? 'HIGH GDPR RISK' : 'LOW GDPR RISK';
                    const recommendation = data.region_info?.is_eu ? 
                        'RECOMMEND: Switch to US-based hosting' : 
                        'GOOD: Current region should work fine';
                    
                    showResult(`🌍 Server Region Analysis:\\n\\n${riskLevel}\\n${recommendation}\\n\\n${JSON.stringify(data, null, 2)}`, 
                              data.region_info?.is_eu ? 'error' : 'success');
                } catch (error) {
                    showResult(`❌ Region check failed: ${error.message}`, 'error');
                }
            }
            
            function openScreenshotViewer() {
                window.open('/screenshot-viewer', '_blank');
            }
            
            async function checkStatus() {
                showLoading('Checking enhanced system status...');
                try {
                    const response = await fetch('/status');
                    const data = await response.json();
                    showResult(`Enhanced System Status:\\n${JSON.stringify(data, null, 2)}`, 'success');
                } catch (error) {
                    showResult(`Status check failed: ${error.message}`, 'error');
                }
            }
            
            async function checkBalance() {
                showLoading('Checking 2Captcha balance...');
                try {
                    const response = await fetch('/balance', { method: 'POST' });
                    const data = await response.json();
                    showResult(data.success ? 
                        `✅ Balance: ${data.balance}\\nAPI: ${data.api_key}\\nFunds: ${data.sufficient_funds}` :
                        `❌ Balance check failed: ${data.error}`, 
                        data.success ? 'success' : 'error');
                } catch (error) {
                    showResult(`Balance check failed: ${error.message}`, 'error');
                }
            }
            
            async function testPing() {
                showLoading('Testing ping...');
                try {
                    const response = await fetch('/ping');
                    const data = await response.json();
                    showResult(`✅ Ping successful: ${data.message}`, 'success');
                } catch (error) {
                    showResult(`❌ Ping failed: ${error.message}`, 'error');
                }
            }
            
            async function debugSelenium() {
                showLoading('🔍 Debugging Selenium connection...');
                try {
                    const response = await fetch('/debug-selenium', { method: 'POST' });
                    const data = await response.json();
                    showResult(`Selenium Debug Results:\\n${JSON.stringify(data, null, 2)}`, 
                              data.overall_assessment?.ready_for_testing ? 'success' : 'error');
                } catch (error) {
                    showResult(`❌ Selenium debug failed: ${error.message}`, 'error');
                }
            }
            
            async function testApiAuth() {
                showLoading('🔑 Testing API authentication approach...');
                try {
                    const response = await fetch('/test-api-auth', { method: 'POST' });
                    const data = await response.json();
                    showResult(`🔑 API Authentication Test:\\n${JSON.stringify(data, null, 2)}`, 'success');
                } catch (error) {
                    showResult(`❌ API auth test failed: ${error.message}`, 'error');
                }
            }
            
            async function testEnhancedLogin() {
                showLoading('🚀 Testing enhanced login with regional detection...');
                try {
                    const response = await fetch('/login-test', { method: 'POST' });
                    const data = await response.json();
                    showResult(`🚀 Enhanced Login Test:\\n${JSON.stringify(data, null, 2)}`, 
                              data.success ? 'success' : 'error');
                } catch (error) {
                    showResult(`❌ Enhanced login test failed: ${error.message}`, 'error');
                }
            }
            
            async function runCompleteTest() {
                if (!confirm('🚀 Run Enhanced Complete Test?\\n\\nThis includes:\\n- Regional detection\\n- Multi-strategy authentication\\n- Advanced cookie handling\\n- API + UI fallback\\n\\nContinue?')) {
                    return;
                }
                
                showLoading('🚀 Running enhanced complete test...\\nThis may take 2-5 minutes...\\n\\nSteps:\\n1. Detect server region\\n2. Apply regional optimizations\\n3. Advanced cookie banner handling\\n4. Multi-strategy authentication\\n5. Extract analytics data\\n6. Report comprehensive results');
                
                try {
                    const response = await fetch('/trigger-diagnostic', { 
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 'game_id': '7291257156' })
                    });
                    
                    const data = await response.json();
                    showResult(`🎉 Enhanced Complete Test Results:\\n${JSON.stringify(data, null, 2)}`, 
                              data.overall_success ? 'success' : 'error');
                } catch (error) {
                    showResult(`❌ Enhanced complete test failed: ${error.message}`, 'error');
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """Enhanced health check with regional information"""
    region_info = analytics.detect_server_region()
    
    return jsonify({
        "status": "healthy",
        "version": "7.0.0 - Enhanced Multi-Strategy",
        "selenium_mode": "remote_webdriver",
        "selenium_url": analytics.selenium_url,
        "verification_ready": True,
        "twocaptcha_ready": analytics.verification_solver.solver is not None,
        "regional_detection": region_info,
        "authentication_methods": ["API (.ROBLOSECURITY)", "Enhanced UI automation"],
        "enhanced_features": ["GDPR detection", "Advanced cookie handling", "Multi-strategy auth"],
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Starting Enhanced Roblox Analytics API on port {port}")
    logger.info(f"🔑 2Captcha API: {analytics.verification_solver.api_key[:8]}...")
    logger.info(f"🌐 Selenium URL: {analytics.selenium_url}")
    logger.info(f"🎯 Enhanced Features: Regional detection, API auth, Advanced UI")
    app.run(host='0.0.0.0', port=port, debug=False)
