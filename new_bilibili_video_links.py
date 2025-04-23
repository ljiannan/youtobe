from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import json
import os
import traceback
import random
import datetime
import colorama
from colorama import Fore, Back, Style

# ====================== 用户配置区 ======================
# 在此处修改您的设置

# B站UP主的URL
UP_MAIN_URL = "https://space.bilibili.com/30222835/upload/video"

# B站Cookie文件路径
COOKIE_FILE_PATH = r"C:\Users\DELL\Desktop\bilibili.txt"

# ChromeDriver路径
CHROME_DRIVER_PATH = r"D:\chrom driver\chrom driver\chromedriver.exe"

# 输出文件设置
OUTPUT_FILENAME = "video_links.txt"

# 调试截图
SAVE_DEBUG_SCREENSHOTS = True
DEBUG_SCREENSHOTS_FOLDER = "debug_screenshots"

# 滚动设置
MAX_SCROLLS = 20  # 最大滚动次数
SCROLL_PAUSE_TIME = 2  # 每次滚动后暂停时间(秒)

# 浏览器设置
HEADLESS_MODE = False  # 是否启用无头模式 (True=隐藏浏览器界面运行, False=显示浏览器界面)
BROWSER_WIDTH = 1920   # 浏览器窗口宽度
BROWSER_HEIGHT = 1080  # 浏览器窗口高度

# ====================== 程序设置区 ======================
# 初始化colorama
colorama.init(autoreset=True)

# 运行时间跟踪
START_TIME = time.time()


def print_header():
    """打印程序头部信息"""
    header = f"""
{Fore.CYAN}{'='*70}
{Fore.CYAN}║{Fore.YELLOW}                 B站UP主视频链接批量获取工具                  {Fore.CYAN}║
{Fore.CYAN}{'='*70}
{Fore.GREEN}► 开始时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{Fore.GREEN}► UP主链接: {UP_MAIN_URL}
{Fore.GREEN}► Cookie文件: {COOKIE_FILE_PATH}
{Fore.CYAN}{'='*70}
    """
    print(header)


def print_section(title):
    """打印带有美化格式的分节标题"""
    print(f"\n{Fore.BLUE}{'='*20} {Fore.YELLOW}{title} {Fore.BLUE}{'='*20}{Style.RESET_ALL}")


def print_success(message):
    """打印成功信息"""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_warning(message):
    """打印警告信息"""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_error(message):
    """打印错误信息"""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_info(message):
    """打印一般信息"""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def print_progress(current, total, message="进度"):
    """打印进度条"""
    percent = current / total
    bar_length = 40
    filled_length = int(bar_length * percent)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\r{Fore.CYAN}{message}: [{bar}] {int(percent*100)}% ({current}/{total})", end='')
    if current == total:
        print()  # 换行


def log_debug(message):
    """记录调试信息"""
    if not hasattr(log_debug, "debug_file"):
        log_debug.debug_file = open("debug.log", "w", encoding="utf-8")
        log_debug.debug_file.write(f"===== 调试日志 {datetime.datetime.now()} =====\n")
    
    log_debug.debug_file.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
    log_debug.debug_file.flush()


def save_debug_screenshot(driver, filename, folder=DEBUG_SCREENSHOTS_FOLDER):
    """保存调试截图"""
    if not SAVE_DEBUG_SCREENSHOTS:
        return
        
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = os.path.join(folder, filename)
        driver.save_screenshot(path)
        print_info(f"已保存调试截图: {path}")
    except Exception as e:
        print_warning(f"保存截图时出错: {e}")


def load_cookies(driver, cookie_file):
    """从文件加载cookies并应用到浏览器"""
    try:
        # 首先确保访问bilibili.com根域名，这对cookie设置很重要
        print_info("访问B站首页以确保正确设置cookie...")
        driver.get("https://www.bilibili.com")
        time.sleep(5)  # 增加等待时间确保页面完全加载
        
        # 检查cookies文件是否存在
        if not os.path.exists(cookie_file):
            print_error(f"Cookie文件不存在: {cookie_file}")
            return False
            
        print_info(f"正在从 {cookie_file} 加载cookies...")
        
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_content = f.read().strip()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(cookie_file, 'r', encoding='gbk') as f:
                cookie_content = f.read().strip()
        
        # 检查文件是否为空
        if not cookie_content:
            print_error("Cookie文件为空")
            return False
            
        print_info(f"读取到cookie内容长度: {len(cookie_content)}")
        
        # 清除所有现有cookies
        driver.delete_all_cookies()
        print_info("已清除现有cookies")
        
        # 首先尝试解析为JSON格式
        cookies_added = 0
        try:
            # 检查是否为JSON数组格式
            if cookie_content.startswith('[') and cookie_content.endswith(']'):
                cookies = json.loads(cookie_content)
                for cookie in cookies:
                    # 确保cookie格式正确
                    if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                        # 处理domain字段
                        if 'domain' not in cookie or not cookie['domain']:
                            cookie['domain'] = '.bilibili.com'
                        elif cookie['domain'].startswith('.'):
                            # 保持原样
                            pass
                        elif cookie['domain'].startswith('bilibili.com'):
                            cookie['domain'] = '.bilibili.com' 
                        elif cookie['domain'].startswith('www.bilibili.com'):
                            cookie['domain'] = '.bilibili.com'
                            
                        # 确保path字段
                        if 'path' not in cookie:
                            cookie['path'] = '/'
                            
                        try:
                            # 移除可能导致问题的字段
                            for key in ['sameSite', 'storeId', 'id', 'hostOnly', 'expirationDate']:
                                if key in cookie:
                                    del cookie[key]
                            
                            log_debug(f"尝试添加cookie: {cookie['name']} = {cookie['value'][:5]}... (domain:{cookie['domain']})")
                            
                            driver.add_cookie(cookie)
                            cookies_added += 1
                        except Exception as e:
                            print_warning(f"添加cookie [{cookie['name']}] 时出错: {e}")
            # 检查是否为单个JSON对象
            elif cookie_content.startswith('{') and cookie_content.endswith('}'):
                cookie = json.loads(cookie_content)
                if 'cookies' in cookie:  # 某些导出格式可能包含cookies键
                    for c in cookie['cookies']:
                        try:
                            if 'domain' not in c or not c['domain']:
                                c['domain'] = '.bilibili.com'
                            elif c['domain'].startswith('bilibili.com'):
                                c['domain'] = '.bilibili.com'
                            
                            # 确保path字段
                            if 'path' not in c:
                                c['path'] = '/'
                                
                            # 移除可能导致问题的字段
                            for key in ['sameSite', 'storeId', 'id', 'hostOnly', 'expirationDate']:
                                if key in c:
                                    del c[key]
                                    
                            log_debug(f"尝试添加cookie: {c['name']} = {c['value'][:5]}... (domain:{c['domain']})")
                            driver.add_cookie(c)
                            cookies_added += 1
                        except Exception as e:
                            print_warning(f"添加cookie时出错: {e}")
                else:
                    # 单个cookie对象
                    if 'domain' not in cookie or not cookie['domain']:
                        cookie['domain'] = '.bilibili.com'
                    elif cookie['domain'].startswith('bilibili.com'):
                        cookie['domain'] = '.bilibili.com'
                        
                    # 确保path字段
                    if 'path' not in cookie:
                        cookie['path'] = '/'
                        
                    # 移除可能导致问题的字段
                    for key in ['sameSite', 'storeId', 'id', 'hostOnly', 'expirationDate']:
                        if key in cookie:
                            del cookie[key]
                            
                    log_debug("尝试添加单个cookie对象")
                    driver.add_cookie(cookie)
                    cookies_added += 1
        except json.JSONDecodeError:
            print_info("不是JSON格式，尝试解析为Netscape或字符串格式...")
            
            # 尝试解析为Netscape格式的cookie (NetScape格式通常是.txt文件，每行一个cookie)
            # 示例: domain\tHTTP-ONLY\tpath\tSECURE\texpiry\tname\tvalue
            if '\t' in cookie_content:
                lines = cookie_content.split('\n')
                for line in lines:
                    if line.startswith('#') or not line.strip():  # 跳过注释行和空行
                        continue
                    
                    try:
                        parts = line.split('\t')
                        if len(parts) >= 7:  # Netscape格式至少有7个字段
                            domain, http_only, path, secure, expiry, name, value = parts[:7]
                            
                            # 修复domain，确保以.开头
                            if domain and not domain.startswith('.') and not domain.startswith('http'):
                                domain = '.' + domain
                                
                            cookie_dict = {
                                'name': name,
                                'value': value,
                                'domain': domain if domain else '.bilibili.com',
                                'path': path if path else '/',
                                'secure': secure.lower() == 'true',
                                'httpOnly': http_only.lower() == 'true'
                            }
                            if expiry and expiry != '0':
                                cookie_dict['expiry'] = int(expiry)
                                
                            log_debug(f"尝试添加Netscape格式cookie: {name}")
                            driver.add_cookie(cookie_dict)
                            cookies_added += 1
                    except Exception as e:
                        print_warning(f"解析Netscape格式cookie行时出错: {e}")
            else:
                # 尝试解析为简单的键值对字符串格式 (name=value; name=value)
                cookie_list = cookie_content.split(';')
                for cookie_pair in cookie_list:
                    if '=' in cookie_pair:
                        try:
                            name, value = cookie_pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            # 跳过空值
                            if not name or not value:
                                continue
                                
                            cookie_dict = {
                                'name': name,
                                'value': value,
                                'domain': '.bilibili.com',
                                'path': '/'
                            }
                            log_debug(f"尝试添加简单格式cookie: {name}")
                            driver.add_cookie(cookie_dict)
                            cookies_added += 1
                        except Exception as e:
                            print_warning(f"添加简单格式cookie时出错: {e}")
        
        print_success(f"成功添加 {cookies_added} 个cookies")
        
        # 验证cookie是否设置成功
        print_info("Cookies加载完成，刷新页面并验证...")
        driver.refresh()
        time.sleep(5)
        
        # 打印当前所有cookies用于调试
        current_cookies = driver.get_cookies()
        print_info(f"当前浏览器中的cookies数量: {len(current_cookies)}")
        for i, c in enumerate(current_cookies[:5]):  # 只显示前5个
            log_debug(f"Cookie {i+1}: {c['name']} = {c['value'][:5]}... (domain:{c.get('domain', 'N/A')})")
        
        # 检查关键cookie是否存在
        bili_jct = None
        sessdata = None
        
        for c in current_cookies:
            if c['name'].lower() == 'bili_jct':
                bili_jct = c['value']
            elif c['name'].lower() == 'sessdata':
                sessdata = c['value']
                
        if bili_jct and sessdata:
            print_success("找到关键登录cookie: bili_jct 和 SESSDATA")
            # 如果找到了关键cookie，就认为登录成功，简化检测逻辑
            return True
        else:
            print_warning("未找到关键登录cookie")
            if not bili_jct:
                print_warning("- 缺少 bili_jct cookie")
            if not sessdata: 
                print_warning("- 缺少 SESSDATA cookie")
        
        # 进行简单检查
        try:
            print_info("尝试查找登录状态元素...")
            # 保存页面截图以供调试
            save_debug_screenshot(driver, "login_check.png")
            
            # 尝试查找表示已登录的元素 - 使用更多选择器
            login_selectors = [
                ".user-name", ".username", ".nav-user-name", ".user-info-name",
                ".avatar-name", ".user-nickname", ".user-name-wrap", ".account-info",
                ".login-name", ".vip-name", "[data-v-logged='true']"
            ]
            
            for selector in login_selectors:
                try:
                    elems = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elems:
                        for elem in elems:
                            if elem.is_displayed():
                                print_success(f"找到登录状态元素: {selector} => {elem.text}")
                                return True
                except:
                    continue
                    
            # 检查是否有账号ID元素
            dedeuser_value = None
            for c in current_cookies:
                if c['name'] == 'DedeUserID':
                    dedeuser_value = c['value']
                    print_success(f"从cookie找到用户ID: {dedeuser_value}")
                    if dedeuser_value:  # 如果找到用户ID，也可以认为是登录状态
                        return True
                        
            # 查找头像元素也可以表示登录状态
            avatar_selectors = [
                ".avatar", ".user-avatar", ".bili-avatar", ".v-img", 
                "img.avatar", "[class*='avatar']"
            ]
            
            for selector in avatar_selectors:
                try:
                    avatars = driver.find_elements(By.CSS_SELECTOR, selector)
                    if avatars:
                        for avatar in avatars:
                            if avatar.is_displayed():
                                print_success(f"找到头像元素，可能已登录: {selector}")
                                return True
                except:
                    continue
                    
            print_info("未找到明确的登录状态元素，但如果有关键cookie，仍可继续运行")
            return bool(bili_jct and sessdata)  # 如果有关键cookie，返回True
        except Exception as e:
            print_warning(f"检查登录状态时出错: {e}")
            # 仍然继续，因为有关键cookie就可以了
            return bool(bili_jct and sessdata)
    except Exception as e:
        print_error(f"加载cookies时出错: {e}")
        traceback.print_exc()
        return False


def scroll_page(driver, scroll_pause_time=2):
    """滚动页面以加载更多内容"""
    print_info("开始滚动页面以加载更多内容...")
    
    # 获取初始页面高度
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # 记录滚动前的视频数
    videos_before = len(driver.find_elements(By.CSS_SELECTOR, 
                                           '.bili-video-card, .small-item, .video-page-card, [data-v-code]'))
    print_info(f"滚动前视频数: {videos_before}")
    
    # 已滚动次数和最大滚动次数
    scroll_count = 0
    max_scrolls = 20  # 可以根据需要调整
    no_new_content_count = 0
    
    while scroll_count < max_scrolls:
        # 向下滚动
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # 等待页面加载
        time.sleep(scroll_pause_time)
        scroll_count += 1
        
        # 输出进度
        print_progress(scroll_count, max_scrolls)
        
        # 获取新的页面高度
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # 获取当前视频数
        videos_now = len(driver.find_elements(By.CSS_SELECTOR, 
                                            '.bili-video-card, .small-item, .video-page-card, [data-v-code]'))
        
        print_info(f"当前视频数: {videos_now}")
        
        # 检查是否有新内容加载
        if videos_now > videos_before:
            videos_before = videos_now
            no_new_content_count = 0
            print_info(f"加载了新视频，继续滚动...")
        else:
            no_new_content_count += 1
            print_info(f"没有加载新视频 ({no_new_content_count}次)")
            
            # 如果连续3次没有新内容，尝试点击"加载更多"按钮
            if no_new_content_count == 3:
                try:
                    load_more_button = driver.find_element(By.CSS_SELECTOR, 
                                                         '.load-more, .more-btn, [class*="more"]')
                    print_info("找到'加载更多'按钮，点击中...")
                    driver.execute_script("arguments[0].click();", load_more_button)
                    time.sleep(3)
                    no_new_content_count = 0  # 重置计数器
                except:
                    print_info("未找到'加载更多'按钮")
            
            # 如果连续5次没有新内容，可能已到底部
            if no_new_content_count >= 5:
                print_info("连续5次未加载新内容，可能已到达页面底部")
                break
        
        # 如果页面高度没变，可能已经加载完所有内容
        if new_height == last_height:
            # 执行一些额外的滚动尝试
            for i in range(3):
                # 尝试一些小幅度的上下滚动，以触发可能的懒加载
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 500);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 再次检查高度
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height > last_height:
                    print_info("通过额外滚动触发了新内容加载")
                    break
                    
            if new_height == last_height:
                print_info(f"页面高度未变化，可能已加载所有内容")
                break
                
        last_height = new_height
    
    # 最终统计
    total_videos = len(driver.find_elements(By.CSS_SELECTOR, 
                                          '.bili-video-card, .small-item, .video-page-card, [data-v-code]'))
    print_info(f"滚动完成，共找到 {total_videos} 个视频元素")
    
    return total_videos


def get_bilibili_videos(up_id):
    """提取B站UP主所有视频链接"""
    # 配置浏览器选项
    options = Options()
    
    # 增强反自动化检测规避
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 设置UA
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
    
    # 语言设置
    options.add_argument('--lang=zh-CN')
    
    # 禁用各种自动化检测标志
    options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置无头模式 (根据配置)
    if HEADLESS_MODE:
        print_info("启用无头模式，浏览器将在后台运行")
        options.add_argument('--headless=new')
    else:
        print_info("使用有头模式，将显示浏览器界面")
    
    # 设置浏览器
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    # 设置浏览器窗口大小
    driver.set_window_size(BROWSER_WIDTH, BROWSER_HEIGHT)
    
    # 修改window.navigator.webdriver为false以绕过检测
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // 覆盖检测webdriver的方法
        if (window.navigator.plugins) {
            Object.setPrototypeOf(navigator, Object.prototype);
        }
        
        // 伪造完整的navigator属性
        const orgProto = navigator.__proto__;
        delete navigator.__proto__;
        
        // 伪造一些独特的指纹特征
        navigator.platform = 'Win32';
        navigator.language = 'zh-CN';
        """
    })
    
    # 伪造更多的浏览器特征
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "platform": "Windows",
        "acceptLanguage": "zh-CN,zh;q=0.9"
    })
    
    # 创建截图目录
    if not os.path.exists(DEBUG_SCREENSHOTS_FOLDER):
        os.makedirs(DEBUG_SCREENSHOTS_FOLDER)
    
    # 从文件加载cookies
    cookie_file = COOKIE_FILE_PATH
    cookie_loaded = load_cookies(driver, cookie_file)
    
    videos = []

    try:
        # 再次检查登录状态
        if not cookie_loaded:
            print_warning("警告: Cookie未成功加载，可能影响视频获取")
            
        # 确保已登录到B站主页
        print_info("再次访问B站主页并检查登录状态...")
        driver.get("https://www.bilibili.com")
        time.sleep(5)
        
        # 尝试关闭登录弹窗 (如果出现)
        close_login_popup(driver)
            
        # 直接访问视频列表页
        url = f"https://space.bilibili.com/{up_id}/video"
        print_info(f"正在访问UP主页面: {url}")
        driver.get(url)

        # 等待页面加载
        time.sleep(5)
        
        # 再次尝试关闭登录弹窗
        close_login_popup(driver)
        
        # 保存页面截图
        save_debug_screenshot(driver, f"up_page_{up_id}.png")
        
        # 使用滚动加载更多视频
        scroll_page(driver)

        # 获取当前页面上的所有视频
        current_page_videos = scrape_current_page(driver)
        videos.extend(current_page_videos)
        print_info(f"第1页找到 {len(current_page_videos)} 个视频")

        # 保存翻页前截图
        save_debug_screenshot(driver, "before_pagination.png")
        
        # 尝试获取页码信息 - 增强翻页检测
        total_pages = get_total_pages(driver)
        
        # 如果检测到多页，尝试翻页
        if total_pages > 1:
            print_info(f"检测到总共有 {total_pages} 页，开始翻页处理...")
            current_page = 1
            
            # 循环处理所有页面，采用点击翻页方式
            while current_page < total_pages:
                next_page = current_page + 1
                print_info(f"\n{'='*30} 尝试翻到第 {next_page} 页 {'='*30}")
                
                # 点击翻页 - 优先使用点击方式
                if navigate_to_page(driver, next_page, up_id):
                    current_page = next_page
                    print_info(f"成功导航到第 {current_page} 页")
                    
                    # 保存每个页面的截图
                    save_debug_screenshot(driver, f"page_{current_page}.png")
                    
                    # 再次尝试关闭登录弹窗
                    close_login_popup(driver)
                    
                    # 在新页面上滚动加载更多视频
                    scroll_page(driver)
                    
                    # 抓取当前页面视频
                    page_videos = scrape_current_page(driver)
                    
                    # 添加新找到的视频
                    new_count = 0
                    existing_bvids = set(v['bvid'] for v in videos)
                    
                    for video in page_videos:
                        if video['bvid'] not in existing_bvids:
                            videos.append(video)
                            new_count += 1
                            
                    print_info(f"第{current_page}页找到 {new_count} 个新视频")
                else:
                    print_info(f"导航到第 {next_page} 页失败，尝试下一页或结束")
                    # 导航失败可能是已到达最后一页，或者页面结构不支持正常翻页
                    # 尝试直接跳转到下一页
                    try:
                        direct_url = f"https://space.bilibili.com/{up_id}/video?page={next_page}"
                        print_info(f"尝试直接访问URL: {direct_url}")
                        driver.get(direct_url)
                        time.sleep(5)
                        current_page = next_page
                        
                        # 检查是否真的加载了新页面
                        if len(scrape_current_page(driver)) > 0:
                            continue  # 成功加载，继续处理下一页
                    except:
                        pass
                        
                    # 如果直接访问也失败，可能是真的没有更多页了
                    print_info(f"无法继续翻页，结束于第 {current_page} 页")
                    break
                
                # 随机延迟，避免请求过快
                delay = random.uniform(2, 5)
                print_info(f"翻页延迟 {delay:.1f} 秒...")
                time.sleep(delay)
        else:
            print_info("未检测到翻页，只处理当前页面")
        
        print_info(f"\n{'='*30} 抓取完成 {'='*30}")
        print_info(f"共找到 {len(videos)} 个视频")
        
        return videos
        
    except Exception as e:
        print_error(f"视频提取过程中出错: {e}")
        traceback.print_exc()
        # 发生错误时保存截图
        save_debug_screenshot(driver, "error.png")
        return videos
    finally:
        print_info("浏览器会话结束，即将关闭浏览器...")
        driver.quit()


def scrape_current_page(driver):
    """从当前页面获取所有视频信息，使用选择器方法"""
    videos = []
    print_info("使用CSS选择器提取当前页面视频...")
    
    # B站视频卡片的常见选择器集合
    video_card_selectors = [
        '.bili-video-card',  # 最新版本的视频卡片
        '.small-item',       # 旧版的视频卡片
        '.video-page-card',  # 页面视频卡片
        '.video-item',       # 视频列表项
        '.audio-card',       # 音频卡片(也可能包含视频)
        '.card-list .card',  # 卡片列表中的卡片
        '.section-item',     # 分区项目
        '.info-box',         # 带信息的盒子
        '[class*="video"][class*="card"]', # 包含video和card的类
        '[class*="videocard"]'  # 包含videocard的类
    ]
    
    # 合并所有选择器为一个大查询
    combined_selector = ', '.join(video_card_selectors)
    
    # 获取所有匹配的视频卡片元素
    try:
        video_items = driver.find_elements(By.CSS_SELECTOR, combined_selector)
        print_info(f"找到 {len(video_items)} 个潜在的视频卡片元素")
        
        if not video_items:
            print_info("未找到视频卡片，尝试使用更通用的选择器...")
            # 退回到更通用的选择器
            video_items = driver.find_elements(By.CSS_SELECTOR, "a[href*='/video/']")
            print_info(f"使用通用选择器找到 {len(video_items)} 个视频链接")
        
        # 处理找到的每个视频卡片
        for item in video_items:
            try:
                # 尝试不同的方式获取视频链接和信息
                video_info = extract_video_info_from_element(driver, item)
                if video_info and video_info['bvid'] and not any(v['bvid'] == video_info['bvid'] for v in videos):
                    videos.append(video_info)
                    print_info(f"提取到视频: {video_info['bvid']} - {video_info['title']}")
            except Exception as e:
                print_warning(f"提取单个视频信息时出错: {e}")
                continue
    except Exception as e:
        print_warning(f"使用选择器查找视频卡片时出错: {e}")
    
    # 如果使用选择器方法未找到视频，尝试直接从页面源码查找所有视频链接
    if not videos:
        print_info("选择器方法未找到视频，尝试从页面源码提取...")
        videos = extract_videos_from_page_source(driver)
    
    print_info(f"当前页面共提取到 {len(videos)} 个视频")
    return videos


def extract_video_info_from_element(driver, element):
    """从元素中提取视频信息"""
    try:
        # 默认视频信息
        video_info = {
            'bvid': '',
            'title': '未知标题',
            'link': ''
        }
        
        # 方法1: 如果元素本身是链接并包含视频地址
        href = element.get_attribute('href') or ''
        if '/video/' in href:
            link = href
            bvid_match = re.search(r'BV\w{10}', href)
            if bvid_match:
                video_info['bvid'] = bvid_match.group(0)
                video_info['link'] = f"https://www.bilibili.com/video/{video_info['bvid']}"
                
                # 尝试获取标题从元素的title属性或文本内容
                title = element.get_attribute('title') or element.text.strip()
                if title:
                    video_info['title'] = title
                    
                return video_info
        
        # 方法2: 查找元素内部的链接
        link_selectors = [
            "a[href*='/video/']",
            ".title a", 
            ".info a", 
            ".name a",
            "a.title", 
            "[title] a"
        ]
        
        for selector in link_selectors:
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, selector)
                href = link_elem.get_attribute('href')
                if href and '/video/' in href:
                    bvid_match = re.search(r'BV\w{10}', href)
                    if bvid_match:
                        video_info['bvid'] = bvid_match.group(0)
                        video_info['link'] = f"https://www.bilibili.com/video/{video_info['bvid']}"
                        
                        # 尝试获取标题
                        title_selectors = [".title", ".info-title", ".video-title", "[title]"]
                        for ts in title_selectors:
                            try:
                                title_elem = element.find_element(By.CSS_SELECTOR, ts)
                                title = title_elem.get_attribute('title') or title_elem.text.strip()
                                if title:
                                    video_info['title'] = title
                                    break
                            except:
                                pass
                                
                        # 如果还没有标题，尝试从链接元素获取
                        if video_info['title'] == '未知标题':
                            title = link_elem.get_attribute('title') or link_elem.text.strip()
                            if title:
                                video_info['title'] = title
                                
                        return video_info
            except:
                continue
        
        # 如果上述方法都失败，尝试JavaScript提取
        try:
            # 使用JavaScript查找视频链接
            links = driver.execute_script("""
                var element = arguments[0];
                var links = element.querySelectorAll('a[href*="/video/"]');
                var results = [];
                for(var i=0; i<links.length; i++) {
                    results.push({
                        href: links[i].href,
                        text: links[i].textContent.trim(),
                        title: links[i].getAttribute('title') || ''
                    });
                }
                return results;
            """, element)
            
            for link in links:
                href = link.get('href', '')
                if href and '/video/' in href:
                    bvid_match = re.search(r'BV\w{10}', href)
                    if bvid_match:
                        video_info['bvid'] = bvid_match.group(0)
                        video_info['link'] = f"https://www.bilibili.com/video/{video_info['bvid']}"
                        
                        # 获取标题
                        text = link.get('text', '').strip()
                        title = link.get('title', '').strip()
                        video_info['title'] = title or text or '未知标题'
                        
                        return video_info
        except:
            pass
        
        # 如果有BV号但没有完整链接
        if video_info['bvid'] and not video_info['link']:
            video_info['link'] = f"https://www.bilibili.com/video/{video_info['bvid']}"
            
        return video_info if video_info['bvid'] else None
            
    except Exception as e:
        print_warning(f"提取视频元素信息时出错: {e}")
        return None


def extract_videos_from_page_source(driver):
    """从页面源码中提取视频信息（作为选择器方法的备选）"""
    videos = []
    page_source = driver.page_source
    
    # 从源码中提取所有BV号
    bv_pattern = r'BV\w{10}'
    bvids = re.findall(bv_pattern, page_source)
    
    # 提取视频标题
    title_pattern = r'title="([^"]+)"[^>]*href="[^"]*?/video/(BV\w{10})'
    title_matches = re.findall(title_pattern, page_source)
    
    # 创建bvid到标题的映射
    title_map = {}
    for title, bvid in title_matches:
        title_map[bvid] = title
    
    # 添加找到的所有BV视频
    for bvid in set(bvids):
        videos.append({
            'bvid': bvid,
            'title': title_map.get(bvid, '未知标题'),
            'link': f"https://www.bilibili.com/video/{bvid}"
        })
    
    return videos


def get_total_pages(driver):
    """获取总页数"""
    print_info("检测页面数量...")
    try:
        # 保存页面源码以便于调试
        page_source = driver.page_source
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print_info("已保存页面源码以便调试")
        
        # 尝试获取所有页码元素，确定总页数
        total_pages = 1
        
        # 尝试更多可能的分页选择器
        pagination_selectors = [
            ".paginationjs-pages .paginationjs-page", 
            ".pagination .page-item", 
            ".be-pager-item", 
            ".pages .page-item",
            ".page-wrap .page-item",
            ".page-box .page",
            ".page-wrap",
            ".pager",
            "[class*='pagination']",
            "[class*='pager']",
            "[class*='page']"
        ]
        
        # 先查找页面元素
        for selector in pagination_selectors:
            try:
                print_info(f"尝试页码选择器: {selector}")
                page_items = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if page_items:
                    print_info(f"通过选择器 '{selector}' 找到 {len(page_items)} 个页码元素")
                    
                    numbers = []
                    for item in page_items:
                        try:
                            text = item.text.strip()
                            print_info(f"  页码文本: '{text}'")
                            # 处理可能有的"尾页"或其他非数字页码
                            if text.isdigit():
                                numbers.append(int(text))
                        except:
                            pass
                    
                    if numbers:
                        total_pages = max(numbers)
                        print_info(f"检测到总页数: {total_pages}")
                        # 保存分页元素截图
                        try:
                            if page_items[0].is_displayed():
                                driver.execute_script("arguments[0].scrollIntoView();", page_items[0])
                                save_debug_screenshot(driver, "pagination_element.png")
                        except:
                            pass
                        return total_pages
            except Exception as e:
                print_warning(f"使用选择器 '{selector}' 时出错: {e}")
        
        # 尝试从URL参数中获取信息
        try:
            current_url = driver.current_url
            print_info(f"当前URL: {current_url}")
            
            # 尝试执行JavaScript获取总页数
            js_page_count = driver.execute_script("""
                // 尝试从各种可能的页面数据中获取总页数
                if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.videoList) {
                    const state = window.__INITIAL_STATE__;
                    if (state.videoList.page && state.videoList.pagesize && state.videoList.count) {
                        return Math.ceil(state.videoList.count / state.videoList.pagesize) || 1;
                    }
                }
                
                // 尝试从页面上获取带页码的链接
                const pageLinks = document.querySelectorAll('a[href*="?page="], a[href*="&page="]');
                let maxPage = 1;
                
                for (let i = 0; i < pageLinks.length; i++) {
                    const href = pageLinks[i].getAttribute('href');
                    const match = href.match(/[?&]page=(\d+)/);
                    if (match && match[1]) {
                        const pageNum = parseInt(match[1], 10);
                        if (pageNum > maxPage) {
                            maxPage = pageNum;
                        }
                    }
                }
                
                return maxPage;
            """)
            
            if js_page_count and isinstance(js_page_count, (int, float)) and js_page_count > 1:
                print_info(f"通过JavaScript检测到总页数: {js_page_count}")
                return int(js_page_count)
                
        except Exception as e:
            print_warning(f"通过JavaScript获取页数时出错: {e}")
        
        print_info("未通过常规方法找到页码，尝试通过正则表达式从页面源码分析")
        
        # 尝试从页面源代码中查找页数信息
        try:
            # 查找常见的页数模式
            page_patterns = [
                r'\"page\":(\d+),\"pagesize\":(\d+),\"count\":(\d+)',  # INITIAL_STATE格式
                r'data-page="(\d+)"',  # 页码标记
                r'共(\d+)页',  # 中文表述
                r'totalPage\":(\d+)',  # JSON格式
                r'page=(\d+)',  # URL参数
            ]
            
            for pattern in page_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    print_info(f"通过模式 '{pattern}' 找到匹配: {matches}")
                    
                    if pattern == r'\"page\":(\d+),\"pagesize\":(\d+),\"count\":(\d+)' and len(matches[0]) == 3:
                        # 特殊处理API响应格式
                        page, pagesize, count = map(int, matches[0])
                        total_pages = (count + pagesize - 1) // pagesize
                        print_info(f"根据API参数计算得出总页数: {total_pages}")
                        return total_pages
                    else:
                        # 找出最大页码
                        nums = []
                        for m in matches:
                            if isinstance(m, tuple):
                                nums.extend([int(x) for x in m if x.isdigit()])
                            elif isinstance(m, str) and m.isdigit():
                                nums.append(int(m))
                        
                        if nums:
                            max_page = max(nums)
                            if max_page > 1:
                                print_info(f"找到可能的最大页码: {max_page}")
                                return max_page
        except Exception as e:
            print_warning(f"通过正则表达式分析页数时出错: {e}")
            
        # 如果以上方法都失败，返回默认值
        print_info(f"所有检测方法都未找到明确的页码，使用默认值: {total_pages}页")
        return total_pages
    except Exception as e:
        print_warning(f"获取页码时出错: {e}")
        traceback.print_exc()
        return 1


def navigate_to_page(driver, page_num, up_id):
    """通过点击翻页按钮导航到指定页码"""
    print_info(f"尝试点击翻页按钮导航到第{page_num}页...")
    
    # 尝试查找并点击页码按钮
    try:
        # 先保存当前页面URL，用于判断导航是否成功
        current_url = driver.current_url
        current_content_hash = hash(driver.page_source[:1000])  # 使用页面内容哈希值帮助判断页面是否变化
        
        # 保存导航前的截图
        save_debug_screenshot(driver, f"before_navigate_to_page_{page_num}.png")
        
        # 尝试点击指定页码按钮
        navigation_successful = False
        
        # 更多的分页按钮选择器
        pagination_selectors = [
            ".paginationjs-pages .paginationjs-page",
            ".pagination .page-item", 
            ".be-pager-item", 
            ".pages .page-item",
            ".page-wrap .page-item",
            ".page-box .page",
            "[class*='pagination'] [class*='page']",
            "[class*='pager'] [class*='item']",
            ".page-num",
            "li[data-page]"
        ]
        
        # 组合选择器为一个大查询
        combined_selector = ', '.join(pagination_selectors)
        
        print_info(f"查找页码按钮，选择器: {combined_selector}")
        page_btns = driver.find_elements(By.CSS_SELECTOR, combined_selector)
        print_info(f"找到 {len(page_btns)} 个潜在页码按钮")
        
        # 查看所有按钮的文本以便调试
        for i, btn in enumerate(page_btns):
            try:
                btn_text = btn.text.strip()
                print_info(f"按钮 {i+1}: 文本='{btn_text}'")
            except:
                print_info(f"按钮 {i+1}: 无法获取文本")
        
        # 点击指定页码
        found = False
        for btn in page_btns:
            try:
                btn_text = btn.text.strip()
                if btn_text == str(page_num):
                    print_info(f"找到第{page_num}页按钮，尝试点击...")
                    
                    # 尝试滚动到按钮位置
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                    time.sleep(1)
                    
                    # 尝试多种点击方法
                    try:
                        # 方法1: 直接点击
                        print_info("尝试直接点击...")
                        btn.click()
                    except:
                        try:
                            # 方法2: JavaScript点击
                            print_info("直接点击失败，尝试JavaScript点击...")
                            driver.execute_script("arguments[0].click();", btn)
                        except:
                            # 方法3: 模拟点击事件
                            print_info("JavaScript点击失败，尝试模拟点击事件...")
                            driver.execute_script("""
                                var event = new MouseEvent('click', {
                                    'view': window,
                                    'bubbles': true,
                                    'cancelable': true
                                });
                                arguments[0].dispatchEvent(event);
                            """, btn)
                    
                    found = True
                    print_info(f"已尝试点击第{page_num}页按钮，等待页面加载...")
                    time.sleep(5)  # 等待页面加载
                    break
            except Exception as e:
                print_warning(f"处理按钮时出错: {e}")
                continue
        
        # 如果没找到指定页码按钮，尝试点击"下一页"按钮
        if not found and page_num == 2:  # 只在第2页时尝试"下一页"按钮
            print_info("未找到指定页码按钮，尝试点击'下一页'按钮...")
            next_selectors = [
                ".next", ".next-page", ".paginationjs-next", 
                "[class*='next']", ".pagination-next",
                "button.nav-btn.iconfont.icon-arrowdown2", 
                "a.nav-btn.iconfont.icon-arrowdown2"
            ]
            combined_next = ', '.join(next_selectors)
            
            next_btns = driver.find_elements(By.CSS_SELECTOR, combined_next)
            for btn in next_btns:
                try:
                    if btn.is_displayed():
                        print_info(f"找到'下一页'按钮: {btn.get_attribute('class')}")
                        # 尝试滚动到按钮位置
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                        time.sleep(1)
                        
                        # 尝试点击
                        driver.execute_script("arguments[0].click();", btn)
                        found = True
                        print_info("已点击'下一页'按钮，等待页面加载...")
                        time.sleep(5)
                        break
                except Exception as e:
                    print_warning(f"点击'下一页'按钮时出错: {e}")
                    continue
        
        # 验证导航是否成功
        new_url = driver.current_url
        new_content_hash = hash(driver.page_source[:1000])
        
        # 保存导航后的截图
        save_debug_screenshot(driver, f"after_navigate_to_page_{page_num}.png")
        
        # 检查URL是否改变或包含页码参数
        url_changed = (new_url != current_url)
        has_page_param = (f"page={page_num}" in new_url)
        content_changed = (new_content_hash != current_content_hash)
        
        print_info(f"验证导航结果: URL改变={url_changed}, 包含页码参数={has_page_param}, 内容改变={content_changed}")
        
        # 如果页面内容变化，或URL变化且有页码参数，认为导航成功
        navigation_successful = content_changed or (url_changed and has_page_param)
        
        # 尝试通过页面内容进一步验证
        if navigation_successful or found:
            # 查找当前页码指示器
            try:
                current_page_indicators = driver.find_elements(By.CSS_SELECTOR, 
                                                            ".paginationjs-page.active, .page-item.active, .be-pager-item.active, [class*='page'][class*='active'], .page-current")
                for indicator in current_page_indicators:
                    if indicator.is_displayed() and indicator.text.strip() == str(page_num):
                        print_info(f"找到当前页码指示器，确认已在第{page_num}页")
                        return True
            except:
                pass
                
            # 如果导航看起来成功但找不到页码指示器，仍然返回True
            if navigation_successful:
                print_info(f"页面已变化，认为导航到第{page_num}页成功")
                return True
                
            # 如果点击成功但没有明确证据表明页面变化，也返回True
            if found:
                print_info(f"已点击按钮，但无法确认是否成功导航到第{page_num}页")
                return True
                
        # 最后一次尝试：查找页面上是否有明确显示当前是第几页
        try:
            # 查找页面上显示"第X页"或"共Y页"等文本
            page_texts = driver.find_elements(By.XPATH, "//*[contains(text(), '页') or contains(text(), 'page')]")
            for elem in page_texts:
                text = elem.text
                if str(page_num) in text and ('页' in text or 'page' in text):
                    print_info(f"从页面文本'{text}'确认已在第{page_num}页")
                    return True
        except:
            pass
        
        print_info(f"无法确认是否成功导航到第{page_num}页")
        return False
            
    except Exception as e:
        print_warning(f"点击分页按钮导航失败: {e}")
        traceback.print_exc()
        return False


def close_login_popup(driver):
    """尝试关闭登录弹窗"""
    try:
        # 多种可能的关闭按钮选择器
        close_selectors = [
            ".login-panel-close", 
            ".close", 
            ".login-close", 
            "[class*='close']",
            ".btn-close",
            ".dialog-close",
            ".popup-close-btn",
            "[title='关闭']",
            "button.close"
        ]
        
        for selector in close_selectors:
            try:
                close_btns = driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in close_btns:
                    if btn.is_displayed():
                        print_info(f"发现登录弹窗，尝试关闭... ({selector})")
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1)
                        return True
            except:
                continue
                
        # 如果没找到明确的关闭按钮，尝试按Escape键关闭
        try:
            # 检查是否有遮罩层或模态框
            overlays = driver.find_elements(By.CSS_SELECTOR, 
                                          ".mask, .modal, .overlay, .dialog, [class*='mask'], [class*='modal']")
            if any(overlay.is_displayed() for overlay in overlays):
                print_info("检测到遮罩层或弹窗，尝试按Escape键关闭...")
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                
                actions = ActionChains(driver)
                actions.send_keys(Keys.ESCAPE)
                actions.perform()
                time.sleep(1)
                return True
        except:
            pass
            
        return False
    except Exception as e:
        print_warning(f"尝试关闭登录弹窗时出错: {e}")
        return False


def save_video_links(videos, filename=OUTPUT_FILENAME):
    """保存视频链接到文件"""
    if not videos:
        print_warning("没有视频可保存")
        return False

    try:
        # 保存简单链接
        with open(filename, 'w', encoding='utf-8') as f:
            for video in videos:
                f.write(f"{video['link']}\n")

        # 保存详细信息
        detail_filename = f"{os.path.splitext(filename)[0]}_details.txt"
        with open(detail_filename, 'w', encoding='utf-8') as f:
            for i, video in enumerate(videos, 1):
                f.write(f"视频 {i}:\n")
                f.write(f"标题: {video.get('title', '未知标题')}\n")
                f.write(f"链接: {video['link']}\n")
                f.write(f"BV号: {video['bvid']}\n")
                f.write("-" * 50 + "\n")

        print_info(f"视频链接已保存到 {filename}")
        print_info(f"详细信息已保存到 {detail_filename}")
        return True
    except Exception as e:
        print_warning(f"保存文件出错: {e}")
        return False


def extract_user_id(url):
    """从URL中提取用户ID"""
    match = re.search(r'space\.bilibili\.com/(\d+)', url)
    if match:
        return match.group(1)
    return None


def main():
    # 打印程序头部
    print_header()
    
    # 从URL提取UP主ID
    user_id = extract_user_id(UP_MAIN_URL)
    if not user_id:
        print_error("无效的B站UP主链接")
        return

    print_section(f"提取UP主 {user_id} 的视频链接")

    # 获取视频
    videos = get_bilibili_videos(user_id)

    # 去重
    unique_videos = []
    seen_bvids = set()

    for video in videos:
        if video['bvid'] not in seen_bvids:
            seen_bvids.add(video['bvid'])
            unique_videos.append(video)

    if unique_videos:
        # 保存视频链接
        save_video_links(unique_videos)
        print_success(f"成功提取 {len(unique_videos)} 个不重复视频链接")
    else:
        print_warning("未能提取到任何视频链接")

    # 打印运行时间
    elapsed_time = time.time() - START_TIME
    print_section(f"任务完成，总耗时 {elapsed_time:.2f} 秒")


if __name__ == "__main__":
    main()
