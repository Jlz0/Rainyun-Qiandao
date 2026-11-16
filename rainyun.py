import logging
import os
import random
import time
import sys
import threading
import json
import hashlib
import re
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# ============== 全局配置 ==============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

selenium_modules = None
debug = False
timeout = 30
user = ""
pwd = ""
linux = False

# ============== Selenium 模块管理 ==============
def import_selenium_modules():
    global selenium_modules
    if selenium_modules is None:
        from selenium import webdriver
        from selenium.webdriver import ActionChains
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.webdriver import WebDriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.common import TimeoutException
        
        selenium_modules = {
            'webdriver': webdriver,
            'ActionChains': ActionChains,
            'Options': Options,
            'Service': Service,
            'WebDriver': WebDriver,
            'By': By,
            'EC': EC,
            'WebDriverWait': WebDriverWait,
            'TimeoutException': TimeoutException
        }
    return selenium_modules

def unload_selenium_modules():
    global selenium_modules
    if selenium_modules is not None:
        modules_to_remove = [
            'selenium', 'selenium.webdriver', 'selenium.webdriver.chrome',
            'selenium.webdriver.chrome.options', 'selenium.webdriver.chrome.service',
            'selenium.webdriver.chrome.webdriver', 'selenium.webdriver.common',
            'selenium.webdriver.common.by', 'selenium.webdriver.support',
            'selenium.webdriver.support.expected_conditions',
            'selenium.webdriver.support.wait', 'selenium.common'
        ]
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
        selenium_modules = None

# ============== 反检测增强 ==============
def get_stealth_options(account_id: str) -> Dict[str, Any]:
    """生成防检测的浏览器配置"""
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    
    # 随机窗口大小（模拟真实用户）
    width = random.choice([1920, 1366, 1440, 1536, 1600])
    height = random.choice([1080, 768, 900, 1024])
    options.add_argument(f"--window-size={width},{height}")
    
    # 随机 User-Agent
    user_agent = get_random_user_agent(account_id)
    options.add_argument(f"--user-agent={user_agent}")
    
    # 语言设置
    options.add_argument("--lang=zh-CN,zh")
    
    # 禁用自动化检测特征
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    return options

def get_random_user_agent(account_id: str) -> str:
    """生成随机 User-Agent"""
    base_date = datetime.date(2022, 3, 29)
    base_version = 100
    days_diff = (datetime.date.today() - base_date).days
    current_ver = base_version + (days_diff // 32)
    
    user_agents = [
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{current_ver}.0.0.0 Safari/537.36",
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{current_ver-1}.0.0.0 Safari/537.36",
        f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{current_ver}.0.0.0 Safari/537.36",
        f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{current_ver}.0.0.0 Safari/537.36",
    ]
    
    account_hash = hashlib.md5(account_id.encode()).hexdigest()
    seed = int(account_hash[:8], 16)
    rng = random.Random(seed)
    return rng.choice(user_agents)

def generate_fingerprint_script(account_id: str) -> str:
    """生成浏览器指纹伪装脚本"""
    account_hash = hashlib.md5(account_id.encode()).hexdigest()
    seed = int(account_hash[:8], 16)
    rng = random.Random(seed)
    
    webgl_vendors = [
        ("Intel Inc.", "Intel Iris Xe Graphics"),
        ("Intel Inc.", "Intel UHD Graphics 770"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4070/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3060/PCIe/SSE2"),
        ("AMD", "AMD Radeon RX 7800 XT"),
    ]
    vendor, renderer = rng.choice(webgl_vendors)
    
    hardware_concurrency = rng.choice([4, 6, 8, 12, 16])
    device_memory = rng.choice([4, 8, 16])
    languages = [["zh-CN", "zh"], ["zh-CN", "en-US"], ["en-US", "en"]]
    language = rng.choice(languages)
    canvas_noise_seed = rng.randint(1, 1000000)
    audio_noise = rng.uniform(0.00001, 0.0001)
    
    return f"""
    (function() {{
        'use strict';
        
        // 隐藏 webdriver 属性
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
        
        // 伪装 plugins
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [
                {{ name: 'Chrome PDF Plugin', description: 'Portable Document Format' }},
                {{ name: 'Chrome PDF Viewer', description: 'Internal PDF Viewer' }}
            ]
        }});
        
        // 伪装 languages
        Object.defineProperty(navigator, 'languages', {{ get: () => {json.dumps(language)} }});
        Object.defineProperty(navigator, 'language', {{ get: () => '{language[0]}' }});
        
        // 伪装 hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hardware_concurrency} }});
        
        // 伪装 deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {device_memory} }});
        
        // 伪装 WebGL
        const getParameterProxyHandler = {{
            apply: function(target, thisArg, args) {{
                const param = args[0];
                if (param === 37445) return '{vendor}';
                if (param === 37446) return '{renderer}';
                return Reflect.apply(target, thisArg, args);
            }}
        }};
        
        try {{
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = new Proxy(originalGetParameter, getParameterProxyHandler);
        }} catch(e) {{}}
        
        try {{
            const originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = new Proxy(originalGetParameter2, getParameterProxyHandler);
        }} catch(e) {{}}
        
        // 伪装 canvas 指纹
        const noiseSeed = {canvas_noise_seed};
        function seededRandom(seed) {{
            const x = Math.sin(seed) * 10000;
            return x - Math.floor(x);
        }}
        
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
            const canvas = this;
            const ctx = canvas.getContext('2d');
            if (ctx) {{
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {{
                    if (seededRandom(noiseSeed + i) < 0.01) {{
                        data[i] = data[i] ^ 1;
                        data[i+1] = data[i+1] ^ 1;
                    }}
                }}
                ctx.putImageData(imageData, 0, 0);
            }}
            return originalToDataURL.apply(this, arguments);
        }};
        
        // 伪装 chrome 对象
        window.chrome = {{
            runtime: {{}},
            loadTimes: function() {{}},
            csi: function() {{}},
            app: {{}}
        }};
        
        // 隐藏 $cdc_ 变量
        Object.defineProperty(window, '$cdc_asdjflasutopfhvcZLmcfl', {{ configurable: false, writable: false }});
    }})();
    """

# ============== 初始化 Selenium ==============
def init_selenium(account_id: str, proxy: str = None):
    modules = import_selenium_modules()
    webdriver = modules['webdriver']
    Options = modules['Options']
    Service = modules['Service']
    
    ops = get_stealth_options(account_id)
    
    if proxy:
        ops.add_argument(f"--proxy-server=http://{proxy}")
        logger.info(f"浏览器已配置代理：{proxy}")
    
    if linux:
        ops.add_argument("--headless=new")
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        
        if os.path.exists(chromedriver_path):
            logger.info(f"使用 ChromeDriver: {chromedriver_path}")
            service = Service(chromedriver_path)
        else:
            logger.info("使用 Selenium Manager 自动管理 ChromeDriver")
            service = Service()
        
        return webdriver.Chrome(service=service, options=ops)
    else:
        service = Service()
        return webdriver.Chrome(service=service, options=ops)

# ============== 弹窗处理 ==============
def dismiss_modal(driver, timeout: int = 10):
    """关闭各种弹窗"""
    modules = import_selenium_modules()
    WebDriverWait = modules['WebDriverWait']
    EC = modules['EC']
    By = modules['By']
    TimeoutException = modules['TimeoutException']
    
    wait = WebDriverWait(driver, timeout)
    
    modal_selectors = [
        "//button[contains(normalize-space(.), '确认')]",
        "//button[contains(normalize-space(.), '确定')]",
        "//button[contains(normalize-space(.), '关闭')]",
        "//button[contains(@class, 'btn-confirm')]",
        "//div[contains(@class, 'modal')]//button",
    ]
    
    for selector in modal_selectors:
        try:
            buttons = driver.find_elements(By.XPATH, selector)
            for btn in buttons:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.2)
                        btn.click()
                        logger.info("已关闭弹窗")
                        time.sleep(0.5)
                        return True
                except Exception:
                    continue
        except Exception:
            continue
    
    return False

# ============== Cookie 管理 ==============
def save_cookies(driver, account_id: str):
    if not account_id:
        return
    os.makedirs("temp/cookies", exist_ok=True)
    account_hash = hashlib.md5(account_id.encode()).hexdigest()[:16]
    cookie_path = os.path.join("temp", "cookies", f"{account_hash}.json")
    
    try:
        cookies = driver.get_cookies()
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"Cookie 已保存到：{cookie_path}")
    except Exception as e:
        logger.warning(f"保存 Cookie 失败：{e}")

def load_cookies(driver, account_id: str) -> bool:
    if not account_id:
        return False
    account_hash = hashlib.md5(account_id.encode()).hexdigest()[:16]
    cookie_path = os.path.join("temp", "cookies", f"{account_hash}.json")
    
    if not os.path.exists(cookie_path):
        logger.info("未找到本地 Cookie，将使用账号密码登录")
        return False
    
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        driver.get("https://app.rainyun.com/")
        time.sleep(1)
        
        for cookie in cookies:
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
        
        # 刷新页面使 Cookie 生效
        driver.refresh()
        time.sleep(2)
        
        logger.info("已加载本地 Cookie")
        return True
    except Exception as e:
        logger.warning(f"加载 Cookie 失败：{e}")
        return False

# ============== 验证码处理 ==============
def process_captcha(driver, wait):
    """处理 TCaptcha 验证码（简化版）"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.common.exceptions import TimeoutException
    
    # 尝试查找验证码 iframe
    captcha_selectors = [
        "iframe[id^='tcaptcha']",
        "iframe[id^='captcha']",
        "iframe[contains(@src, 'captcha')]",
    ]
    
    captcha_frame = None
    for selector in captcha_selectors:
        try:
            captcha_frame = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            if captcha_frame.is_displayed():
                break
        except Exception:
            continue
    
    if not captcha_frame:
        logger.info("未检测到验证码 iframe")
        return False
    
    try:
        driver.switch_to.frame(captcha_frame)
        
        # 查找滑动验证码元素
        slide_selectors = [
            "//*[@id='slideBg']",
            "//*[@id='tcSlide']",
            "//div[contains(@class, 'tc-slider')]",
        ]
        
        slide_bg = None
        for selector in slide_selectors:
            try:
                slide_bg = wait.until(EC.visibility_of_element_located((By.XPATH, selector)))
                if slide_bg.is_displayed():
                    break
            except Exception:
                continue
        
        if slide_bg:
            logger.info("检测到滑动验证码，尝试自动处理...")
            # 注意：实际滑动需要更复杂的逻辑，这里仅做占位
            # 建议接入 ddddocr 或第三方打码平台
            time.sleep(2)
            
            # 尝试点击确认按钮
            confirm_selectors = [
                "//*[@id='tcStatus']/div[2]/div[2]/div/div",
                "//button[contains(@class, 'tc-confirm')]",
            ]
            for selector in confirm_selectors:
                try:
                    confirm = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    confirm.click()
                    logger.info("已点击验证码确认")
                    time.sleep(3)
                    break
                except Exception:
                    continue
        else:
            logger.info("未检测到滑动验证码元素")
        
        driver.switch_to.default_content()
        return True
        
    except Exception as e:
        logger.warning(f"验证码处理异常：{e}")
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return False

# ============== 登录逻辑（优化版） ==============
def login_with_retry(driver, username: str, password: str, wait) -> bool:
    """带重试的登录逻辑"""
    modules = import_selenium_modules()
    By = modules['By']
    EC = modules['EC']
    TimeoutException = modules['TimeoutException']
    
    # 尝试多种登录表单选择器
    login_form_selectors = [
        "//form[@id='loginForm']",
        "//form[contains(@class, 'login-form')]",
        "//div[contains(@class, 'auth-login')]//form",
    ]
    
    # 尝试多种输入框选择器
    username_selectors = [
        (By.NAME, 'username'),
        (By.NAME, 'login-field'),
        (By.NAME, 'account'),
        (By.ID, 'username'),
        (By.CSS_SELECTOR, 'input[type="text"][name*="user"]'),
    ]
    
    password_selectors = [
        (By.NAME, 'password'),
        (By.NAME, 'login-password'),
        (By.NAME, 'pwd'),
        (By.ID, 'password'),
        (By.CSS_SELECTOR, 'input[type="password"][name*="pass"]'),
    ]
    
    button_selectors = [
        (By.XPATH, '//*[@id="app"]/div[1]/div[1]/div/div[2]/fade/div/div/span/form/button'),
        (By.CSS_SELECTOR, 'button[type="submit"]'),
        (By.XPATH, '//button[contains(@class, "btn-primary")]'),
        (By.XPATH, '//button[contains(normalize-space(.), "登录")]'),
    ]
    
    # 尝试定位登录表单
    login_form = None
    for selector in login_form_selectors:
        try:
            login_form = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            if login_form.is_displayed():
                break
        except Exception:
            continue
    
    if not login_form:
        logger.warning("未找到登录表单，尝试直接定位输入框")
    
    # 定位用户名输入框
    username_input = None
    for selector in username_selectors:
        try:
            username_input = wait.until(EC.visibility_of_element_located(selector))
            break
        except Exception:
            continue
    
    if not username_input:
        logger.error("无法定位用户名输入框")
        return False
    
    # 定位密码输入框
    password_input = None
    for selector in password_selectors:
        try:
            password_input = wait.until(EC.visibility_of_element_located(selector))
            break
        except Exception:
            continue
    
    if not password_input:
        logger.error("无法定位密码输入框")
        return False
    
    # 定位登录按钮
    login_button = None
    for selector in button_selectors:
        try:
            login_button = wait.until(EC.element_to_be_clickable(selector))
            break
        except Exception:
            continue
    
    if not login_button:
        logger.error("无法定位登录按钮")
        return False
    
    # 模拟真实输入（带随机延迟）
    logger.info("开始输入账号密码...")
    for char in username:
        username_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    
    for char in password:
        password_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    
    # 模拟真实点击（带随机延迟）
    time.sleep(random.uniform(0.5, 1.5))
    login_button.click()
    logger.info("已点击登录按钮")
    
    # 等待登录结果
    time.sleep(3)
    
    # 检查是否触发验证码
    if "tcaptcha" in driver.page_source.lower() or "captcha" in driver.page_source.lower():
        logger.info("检测到验证码，尝试处理...")
        process_captcha(driver, wait)
        time.sleep(2)
    
    # 检查登录是否成功
    success_indicators = [
        "/dashboard",
        "/account",
        "/reward",
        "user-info",
        "username",
    ]
    
    for indicator in success_indicators:
        if indicator in driver.current_url.lower() or indicator in driver.page_source.lower():
            logger.info("登录成功检测通过")
            return True
    
    # 检查是否仍停留在登录页
    if "/auth/login" in driver.current_url:
        logger.warning("仍停留在登录页，可能登录失败")
        return False
    
    return True

# ============== 签到主逻辑 ==============
def run_checkin(account_user: str = None, account_pwd: str = None) -> Dict[str, Any]:
    current_user = account_user or user
    current_pwd = account_pwd or pwd
    driver = None
    retry_stats = {'count': 0}
    
    masked_user = f"{current_user[:3]}***{current_user[-3:] if len(current_user) > 6 else current_user}"
    
    class PrefixAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            return '[%s] %s' % (self.extra['prefix'], msg), kwargs
    
    logger_adapter = PrefixAdapter(logger, {'prefix': masked_user})
    
    try:
        logger_adapter.info("开始执行签到任务...")
        
        logger_adapter.info("初始化 Selenium（账号专属配置）")
        driver = init_selenium(current_user)
        
        # 注入防检测脚本
        with open("stealth.min.js", mode="r") as f:
            js = f.read()
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js})
        
        fingerprint_js = generate_fingerprint_script(current_user)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": fingerprint_js})
        logger_adapter.info("已注入浏览器指纹脚本（账号专属指纹）")
        
        wait = WebDriverWait(driver, timeout)
        
        # 尝试加载 Cookie
        if not load_cookies(driver, current_user):
            logger_adapter.info("Cookie 无效或不存在，准备登录...")
        
        # 跳转积分页
        logger_adapter.info("正在跳转积分页...")
        driver.get("https://app.rainyun.com/account/reward/earn")
        time.sleep(3)
        
        # 检查是否需要登录
        if "/auth/login" in driver.current_url:
            logger_adapter.info("Cookie 已失效，使用账号密码登录")
            
            if not login_with_retry(driver, current_user, current_pwd, wait):
                logger_adapter.error("登录失败，当前页面：{0}".format(driver.current_url))
                return {
                    'status': False, 'msg': '登录失败', 'points': 0,
                    'username': masked_user, 'retries': retry_stats['count']
                }
            
            # 等待登录完成
            time.sleep(3)
            
            # 检查登录是否成功
            if "/dashboard" in driver.current_url or "/account" in driver.current_url:
                logger_adapter.info("登录成功！")
                save_cookies(driver, current_user)
                driver.get("https://app.rainyun.com/account/reward/earn")
                time.sleep(2)
            else:
                logger_adapter.error("登录失败，当前页面：{0}".format(driver.current_url))
                return {
                    'status': False, 'msg': '登录失败', 'points': 0,
                    'username': masked_user, 'retries': retry_stats['count']
                }
        else:
            logger_adapter.info("Cookie 有效，免密登录成功！")
        
        # 确保在积分页
        if "/account/reward/earn" not in driver.current_url:
            driver.get("https://app.rainyun.com/account/reward/earn")
        
        driver.implicitly_wait(5)
        time.sleep(1)
        dismiss_modal(driver, timeout)
        
        # 查找签到按钮
        earn_selectors = [
            '//*[@id="app"]/div[1]/div[3]/div[2]/div/div/div[2]/div[2]/div/div/div/div[1]/div/div[1]/div/div[1]/div/span[2]/a',
            "//button[contains(normalize-space(.), '签到')]",
            "//button[contains(normalize-space(.), '领取奖励')]",
            "//a[contains(normalize-space(.), '签到')]",
        ]
        
        earn_button = None
        for selector in earn_selectors:
            try:
                earn_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                if earn_button.is_displayed():
                    break
            except Exception:
                continue
        
        if earn_button:
            btn_text = earn_button.text.strip()
            logger_adapter.info(f"签到按钮文字：[{btn_text}]")
            
            if btn_text in ["领取奖励", "签到", "去签到"]:
                logger_adapter.info("点击领取奖励")
                earn_button.click()
                
                # 检查是否触发验证码
                state = "none"
                try:
                    if "tcaptcha" in driver.page_source.lower():
                        state = "captcha"
                        logger_adapter.info("处理验证码")
                        try:
                            captcha_iframe = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "iframe[id^='tcaptcha_iframe']")))
                            driver.switch_to.frame(captcha_iframe)
                            process_captcha(driver, wait)
                        finally:
                            driver.switch_to.default_content()
                        driver.implicitly_wait(5)
                except Exception:
                    logger_adapter.info("未触发验证码")
            else:
                logger_adapter.info(f"今日已签到（按钮显示：{btn_text}）")
        else:
            logger_adapter.warning("未找到签到按钮")
        
        # 获取积分
        points_selectors = [
            '//*[@id="app"]/div[1]/div[3]/div[2]/div/div/div[2]/div[1]/div[1]/div/p/div/h3',
            "//div[contains(@class, 'points')]//h3",
            "//span[contains(@class, 'points-value')]",
        ]
        
        points_raw = ""
        for selector in points_selectors:
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                points_raw = element.get_attribute("textContent")
                break
            except Exception:
                continue
        
        if points_raw:
            current_points = int(''.join(re.findall(r'\d+', points_raw)))
            logger_adapter.info(f"当前剩余积分：{current_points} | 约为 {current_points / 2000:.2f} 元")
        else:
            current_points = 0
            logger_adapter.warning("无法获取积分信息")
        
        logger_adapter.info("签到任务执行成功！")
        return {
            'status': True, 'msg': '签到成功', 'points': current_points,
            'username': masked_user, 'retries': retry_stats['count']
        }
        
    except Exception as e:
        logger_adapter.error(f"签到任务执行失败：{e}")
        import traceback
        logger_adapter.error(f"详细错误信息：{traceback.format_exc()}")
        return {
            'status': False, 'msg': f'执行异常：{str(e)[:50]}...',
            'points': 0, 'username': masked_user, 'retries': retry_stats['count']
        }
    finally:
        if driver is not None:
            try:
                logger_adapter.info("正在关闭 WebDriver...")
                driver.quit()
                logger_adapter.info("WebDriver 已安全关闭")
            except Exception as e:
                logger_adapter.error(f"关闭 WebDriver 时出错：{e}")
        
        try:
            unload_selenium_modules()
        except:
            pass

# ============== 账号解析与执行 ==============
def parse_accounts():
    usernames_raw = os.getenv("RAINYUN_USER", "").replace("\r\n", "\n").replace("\r", "\n")
    passwords_raw = os.getenv("RAINYUN_PASS", "").replace("\r\n", "\n").replace("\r", "\n")
    
    usernames = [u for u in usernames_raw.split("\n") if u.strip()]
    passwords = [p for p in passwords_raw.split("\n") if p.strip()]
    
    if len(usernames) != len(passwords):
        logger.warning("用户名和密码数量不匹配，只使用匹配的部分")
        min_len = min(len(usernames), len(passwords))
        usernames = usernames[:min_len]
        passwords = passwords[:min_len]
    
    accounts = [(u.strip(), p.strip()) for u, p in zip(usernames, passwords) if u.strip() and p.strip()]
    
    if not accounts:
        single_user = os.getenv("RAINYUN_USER", "username")
        single_pwd = os.getenv("RAINYUN_PASS", "password")
        accounts = [(single_user, single_pwd)]
    
    logger.info(f"检测到 {len(accounts)} 个账号")
    for i, (username, _) in enumerate(accounts, 1):
        masked_user = f"{username[:3]}***{username[-3:] if len(username) > 6 else username}"
        logger.info(f"账号 {i}: {masked_user}")
    
    return accounts

def run_all_accounts():
    import concurrent.futures
    
    max_retries = int(os.getenv("CHECKIN_MAX_RETRIES", "2"))
    max_workers = int(os.getenv("MAX_WORKERS", "3"))
    stagger_delay = int(os.getenv("MAX_DELAY", "15"))
    
    accounts = parse_accounts()
    results = {}
    
    for i, (username, password) in enumerate(accounts, 1):
        results[username] = {
            'password': password, 'result': None,
            'retry_count': 0, 'index': i
        }
    
    pending_accounts = list(accounts)
    current_attempt = 0
    
    while pending_accounts and current_attempt <= max_retries:
        if current_attempt == 0:
            logger.info(f"========== 开始执行签到任务（共 {len(pending_accounts)} 个账号，并发数：{max_workers}） ==========")
        else:
            logger.info(f"========== 第 {current_attempt} 次重试（共 {len(pending_accounts)} 个失败账号） ==========")
        
        failed_accounts = []
        future_to_account = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i, (username, password) in enumerate(pending_accounts):
                if i > 0 and stagger_delay > 0:
                    lower_bound = 5
                    upper_bound = max(5, stagger_delay)
                    actual_delay = random.randint(lower_bound, upper_bound)
                    logger.info(f"随机等待 {actual_delay} 秒后启动下一个账号任务...")
                    time.sleep(actual_delay)
                
                account_idx = results[username]['index']
                retry_info = f"（第 {results[username]['retry_count'] + 1} 次尝试）" if results[username]['retry_count'] > 0 else ""
                logger.info(f"========== 启动账号 {account_idx}/{len(accounts)} {retry_info} ==========")
                
                future = executor.submit(run_checkin, username, password)
                future_to_account[future] = username
            
            for future in concurrent.futures.as_completed(future_to_account):
                username = future_to_account[future]
                account_idx = results[username]['index']
                
                try:
                    result = future.result()
                    results[username]['result'] = result
                    
                    if result['status']:
                        logger.info(f"✅ 账号 {account_idx} 签到成功")
                    else:
                        logger.error(f"❌ 账号 {account_idx} 签到失败：{result['msg']}")
                        results[username]['retry_count'] += 1
                        if results[username]['retry_count'] <= max_retries:
                            failed_accounts.append((username, results[username]['password']))
                except Exception as e:
                    logger.error(f"❌ 账号 {account_idx} 执行异常：{e}")
                    results[username]['retry_count'] += 1
                    if results[username]['retry_count'] <= max_retries:
                        failed_accounts.append((username, results[username]['password']))
        
        pending_accounts = failed_accounts
        current_attempt += 1
        
        if pending_accounts:
            retry_wait = 60
            logger.info(f"等待 {retry_wait} 秒后开始重试 {len(pending_accounts)} 个失败账号...")
            time.sleep(retry_wait)
    
    final_results = [results[username]['result'] for username, _ in accounts]
    success_count = len([r for r in final_results if r and r['status']])
    
    failed_count = len(accounts) - success_count
    logger.info(f"任务完成：{success_count}/{len(accounts)} 成功")
    
    return success_count > 0

# ============== 主入口 ==============
if __name__ == "__main__":
    timeout = int(os.getenv("TIMEOUT", "30000")) // 1000
    max_delay = int(os.getenv("MAX_DELAY", "5"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    linux = os.getenv("LINUX_MODE", "true").lower() == "true" or os.path.exists("/.dockerenv")
    
    user = os.getenv("RAINYUN_USER", "username").split("|")[0]
    pwd = os.getenv("RAINYUN_PASS", "password").split("|")[0]
    
    ver = "2.7 (优化版)"
    logger.info("------------------------------------------------------------------")
    logger.info(f"雨云自动签到工作流 v{ver}")
    logger.info("------------------------------------------------------------------")
    
    run_all_accounts()
