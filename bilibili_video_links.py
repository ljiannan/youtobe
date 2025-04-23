from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import json
import os
import traceback
import random
import pickle


# 添加保存和加载Cookie的功能
def save_cookies(driver, path):
    """保存浏览器Cookies到文件"""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(path, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)
    print(f"Cookies已保存到: {path}")


def load_cookies(driver, path):
    """从文件加载Cookies到浏览器"""
    if not os.path.exists(path):
        print(f"Cookie文件不存在: {path}")
        return False
    
    try:
        # 尝试使用pickle加载二进制cookie
        try:
            with open(path, 'rb') as file:
                cookies = pickle.load(file)
        except:
            # 如果失败，尝试作为文本文件读取
            cookies = []
            with open(path, 'r', encoding='utf-8') as file:
                try:
                    # 尝试作为JSON解析
                    cookies = json.loads(file.read())
                except:
                    # 尝试按行解析cookie
                    lines = file.readlines()
                    for line in lines:
                        if '=' in line:
                            name, value = line.strip().split('=', 1)
                            cookies.append({'name': name, 'value': value})
        
        # 添加cookie到浏览器
        for cookie in cookies:
            # 某些站点可能需要处理domain
            if isinstance(cookie, dict):  # 确保cookie是字典
                if 'domain' in cookie:
                    if cookie['domain'].startswith('.'):
                        cookie['domain'] = cookie['domain']
                    else:
                        cookie['domain'] = '.' + cookie['domain']
                
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"添加Cookie时出错: {e}")
            
        print(f"成功加载Cookies")
        return True
    except Exception as e:
        print(f"加载Cookies时出错: {e}")
        return False


def manual_login(driver):
    """手动登录B站账号"""
    print("=" * 50)
    print("请在浏览器中手动登录B站账号")
    print("登录成功后，请在此输入任意键继续...")
    print("=" * 50)
    input("等待登录完成，按Enter继续...")
    
    # 检查登录状态
    try:
        # 检查是否有头像元素，这通常表示已登录
        avatar = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".header-avatar, .user-con .avatar"))
        )
        print("检测到登录成功")
        return True
    except:
        print("未检测到登录状态，可能登录失败")
        return False


def get_video_count(driver):
    """获取UP主视频总数"""
    try:
        # 尝试多种可能的选择器
        count_selectors = [
            ".n-statistics .n-data:first-child .n-data-v",  # 2024年新版个人空间
            ".n-statistics__first .n-data__value",          # 新版备选
            ".video-count",                                 # 旧版视频计数
            ".sub-item .count",                            # 可能的数量显示
            ".channel-item .count",                        # 频道数量
            ".channel-item .num",                          # 频道视频数
            ".sub-title .count"                            # 子标题中的数量
        ]

        for selector in count_selectors:
            try:
                count_elem = driver.find_element(By.CSS_SELECTOR, selector)
                count_text = count_elem.text.strip()
                # 处理中文"万"
                if "万" in count_text:
                    count = float(count_text.replace("万", "")) * 10000
                else:
                    count = int(re.sub(r'\D', '', count_text))
                print(f"获取到视频计数: {count_text} -> {count}")
                return count
            except:
                continue
                
        # 尝试从页面源码中提取视频数量
        page_source = driver.page_source
        count_patterns = [
            r'"videoCount":(\d+)',             # JSON格式可能包含的计数
            r'"video_count":(\d+)',            # 另一种JSON格式
            r'视频[^\d]*(\d+)[^\d]*个',         # 中文文本格式
            r'(\d+)[^\d]*投稿',                # 另一种中文表述
            r'(\d+)[^\d]*视频'                 # 简单中文表述
        ]
        
        for pattern in count_patterns:
            match = re.search(pattern, page_source)
            if match:
                count = int(match.group(1))
                print(f"从源码提取到视频计数: {count}")
                return count
                
        print("未能获取视频计数，默认为30")
        return 30
    except Exception as e:
        print(f"获取视频计数出错: {e}")
        return 30


def get_total_pages(driver):
    """获取总页数"""
    try:
        # 尝试多种可能的分页选择器
        pagination_selectors = [
            ".paginationjs-pages ul li",            # 常见的分页样式
            ".pagination .page-item",               # Bootstrap风格分页
            ".be-pager-item",                       # B站旧版分页
            ".n-pager__item",                       # B站新版分页
            ".pages li",                            # 简单分页
            "[class*='pagination'] [class*='item']" # 通用选择器
        ]
        
        for selector in pagination_selectors:
            try:
                page_items = driver.find_elements(By.CSS_SELECTOR, selector)
                if page_items:
                    numbers = []
                    for item in page_items:
                        try:
                            text = item.text.strip()
                            if text and text.isdigit():
                                numbers.append(int(text))
                        except:
                            pass
                    
                    if numbers:
                        max_page = max(numbers)
                        print(f"从分页元素检测到总页数: {max_page}")
                        return max_page
            except:
                continue
                
        # 尝试从页面源码中提取页数信息
        page_source = driver.page_source
        page_patterns = [
            r'"page":{"count":(\d+)',              # JSON格式中的页数信息
            r'"totalPage":(\d+)',                  # 另一种JSON格式
            r'"pageCount":(\d+)',                  # 另一种表示
            r'共\s*(\d+)\s*页'                      # 中文文本表示
        ]
        
        for pattern in page_patterns:
            match = re.search(pattern, page_source)
            if match:
                total_pages = int(match.group(1))
                print(f"从源码提取到总页数: {total_pages}")
                return total_pages
                
        print("未能检测到总页数，默认为1页")
        return 1
    except Exception as e:
        print(f"获取总页数出错: {e}")
        return 1


def scroll_page(driver):
    """逐步滚动页面以加载所有内容"""
    print("开始滚动页面以加载所有内容...")
    
    # 获取页面高度
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # 滚动次数
    scroll_attempts = 0
    max_attempts = 10
    
    while scroll_attempts < max_attempts:
        # 滚动到页面底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # 等待内容加载
        time.sleep(2)
        
        # 获取新的页面高度
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # 如果高度没有变化，可能已经到底或没有更多内容
        if new_height == last_height:
            scroll_attempts += 1
            if scroll_attempts >= 2:  # 连续两次高度不变，认为已加载完成
                break
        else:
            scroll_attempts = 0  # 重置计数器
            
        last_height = new_height
        print(f"页面滚动中... 当前高度: {new_height}px")
    
    # 滚动回页面顶部
    driver.execute_script("window.scrollTo(0, 0);")
    print("页面滚动完成")


def verify_page_number(driver, expected_page):
    """验证当前加载的是否为预期页面"""
    try:
        # 首先检查URL中的页码
        current_url = driver.current_url
        url_page_match = re.search(r'[?&]pn=(\d+)', current_url)
        if url_page_match:
            url_page = int(url_page_match.group(1))
            if url_page == expected_page:
                print(f"URL确认当前是第{expected_page}页")
                return True
        
        # 检查活动的分页按钮
        active_selectors = [
            ".paginationjs-page.active",
            ".page-item.active",
            ".be-pager-item.be-pager-item-active",
            ".n-pager__item.active",
            "[class*='pagination'] [class*='active']"
        ]
        
        for selector in active_selectors:
            try:
                active_page = driver.find_element(By.CSS_SELECTOR, selector)
                page_text = active_page.text.strip()
                if page_text.isdigit() and int(page_text) == expected_page:
                    print(f"分页按钮确认当前是第{expected_page}页")
                    return True
            except:
                continue
        
        print(f"无法确认当前是否为第{expected_page}页")
        return False
    except Exception as e:
        print(f"验证页码时出错: {e}")
        return False


def navigate_to_page_by_url(driver, page_num, up_id):
    """通过直接修改URL导航到指定页面"""
    try:
        current_url = driver.current_url
        # 避免不必要的刷新：如果已经在正确的页面上，不执行跳转
        url_page_match = re.search(r'[?&]pn=(\d+)', current_url)
        if url_page_match and int(url_page_match.group(1)) == page_num:
            print(f"已经在第{page_num}页，无需跳转")
            return True
            
        # 使用多种可能的URL格式
        urls = [
            f"https://space.bilibili.com/{up_id}/video?pn={page_num}",
            f"https://space.bilibili.com/{up_id}/video?tid=0&pn={page_num}&keyword=&order=pubdate",
            f"https://space.bilibili.com/{up_id}/video?page={page_num}"
        ]
        
        for url in urls:
            try:
                print(f"尝试通过URL导航到第{page_num}页: {url}")
                driver.get(url)
                time.sleep(3)
                
                # 验证是否加载了正确的页面
                if verify_page_number(driver, page_num):
                    print(f"成功通过URL导航到第{page_num}页")
                    return True
            except:
                continue
        
        print(f"所有URL导航方式均失败")
        return False
    except Exception as e:
        print(f"URL导航到第{page_num}页失败: {e}")
        return False


def navigate_to_page_by_button(driver, page_num):
    """尝试通过点击分页按钮导航到指定页面"""
    try:
        # 首先滚动到页面底部，确保分页控件可见
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # 尝试多种可能的分页按钮选择器
        pagination_selectors = [
            ".paginationjs-pages ul li",
            ".pagination .page-item",
            ".be-pager-item",
            ".n-pager__item",
            ".pages li",
            ".page-wrap .page-item",
            "[class*='pagination'] [class*='item']"
        ]
        
        for selector in pagination_selectors:
            try:
                page_btns = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if not page_btns:
                    continue
                    
                print(f"找到{len(page_btns)}个分页按钮")
                
                # 截图查看分页区域
                try:
                    element = driver.find_element(By.CSS_SELECTOR, ".page-wrap, .pagination, .be-pager")
                    screenshot_path = f"pagination_screenshot_page{page_num}.png"
                    element.screenshot(screenshot_path)
                    print(f"已保存分页区域截图到 {screenshot_path}")
                except:
                    pass
                
                # 检查每个按钮
                for btn in page_btns:
                    try:
                        btn_text = btn.text.strip()
                        print(f"发现分页按钮: '{btn_text}'")
                        
                        # 检查是否是目标页码
                        if btn_text == str(page_num):
                            print(f"找到第{page_num}页按钮，尝试点击...")
                            
                            # 确保元素可见和可点击
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            
                            try:
                                # 尝试直接点击
                                btn.click()
                                time.sleep(2)
                            except:
                                # 如果直接点击失败，尝试JS点击
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(2)
                            
                            # 验证是否成功导航
                            if verify_page_number(driver, page_num):
                                print(f"成功通过按钮导航到第{page_num}页")
                                return True
                    except Exception as e:
                        print(f"点击按钮时出错: {e}")
                        continue
            except Exception as e:
                print(f"使用选择器'{selector}'查找按钮时出错: {e}")
                continue
        
        # 尝试通过"下一页"按钮导航
        if page_num > 1:  # 对于除第1页外的所有页面
            next_page_selectors = [
                ".paginationjs-next",
                ".pagination .next",
                ".be-pager-next",
                ".n-pager__next",
                ".page-wrap .next", 
                "[class*='pagination'] [class*='next']",
                "a:contains('下一页')"
            ]
            
            for selector in next_page_selectors:
                try:
                    next_btns = driver.find_elements(By.CSS_SELECTOR, selector)
                    if next_btns:
                        next_btn = next_btns[0]
                        current_page = 1
                        
                        # 获取当前页面
                        try:
                            active_page = driver.find_element(By.CSS_SELECTOR, ".active, .be-pager-item-active")
                            if active_page.text.isdigit():
                                current_page = int(active_page.text)
                        except:
                            pass
                            
                        print(f"当前在第{current_page}页，需要点击'下一页'按钮 {page_num - current_page} 次")
                        
                        # 点击适当次数的"下一页"
                        for i in range(page_num - current_page):
                            print(f"点击'下一页'按钮 ({i+1}/{page_num - current_page})...")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                            time.sleep(1)
                            
                            try:
                                next_btn.click()
                            except:
                                driver.execute_script("arguments[0].click();", next_btn)
                            
                            time.sleep(3)
                            
                            # 验证是否到达目标页
                            if verify_page_number(driver, current_page + i + 1):
                                if current_page + i + 1 == page_num:
                                    print(f"成功通过'下一页'按钮导航到第{page_num}页")
                                    return True
                            else:
                                print("导航失败，未到达预期页面")
                                break
                                
                            # 重新获取"下一页"按钮
                            try:
                                next_btns = driver.find_elements(By.CSS_SELECTOR, selector)
                                if next_btns:
                                    next_btn = next_btns[0]
                                else:
                                    print("未找到'下一页'按钮，可能已到达最后一页")
                                    break
                            except:
                                print("无法获取'下一页'按钮")
                                break
                except:
                    continue
        
        print("所有按钮导航方式均失败")
        return False
    except Exception as e:
        print(f"按钮导航到第{page_num}页失败: {e}")
        return False


def get_bilibili_videos(up_id, use_cookies=True, cookies_path=r"C:\Users\DELL\Desktop\bilibili.txt"):
    """提取B站UP主所有视频链接"""
    # 配置浏览器选项
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    # options.add_argument('--headless=new')  # 注释掉无头模式，使浏览器可见
    options.add_argument('--disable-gpu')
    
    # 添加更多反检测措施
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    
    # 添加自定义User-Agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

    # 设置浏览器
    service = Service(r"D:\chrom driver\chrom driver\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    # 修改window.navigator.webdriver为false以绕过检测
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // 覆盖WebDriver属性
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """
    })

    # 设置窗口大小
    driver.set_window_size(1920, 1080)

    videos = []

    try:
        # 首先访问B站首页以设置Cookies
        print("先访问B站首页...")
        driver.get("https://www.bilibili.com/")
        time.sleep(3)
        
        login_success = False
        
        # 尝试加载Cookies
        if use_cookies and os.path.exists(cookies_path):
            print(f"尝试使用保存的Cookies: {cookies_path}")
            load_cookies(driver, cookies_path)
            
            # 刷新页面使Cookies生效
            driver.refresh()
            time.sleep(3)
            
            # 检查是否登录成功
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".header-avatar, .avatar"))
                )
                login_success = True
                print("Cookies登录成功!")
            except:
                print("Cookies无效或已过期")
                login_success = False
        
        # 如果Cookies无效或不存在，则进行手动登录
        if not login_success:
            print("需要手动登录...")
            if manual_login(driver):
                # 保存新的Cookies供下次使用
                save_cookies(driver, cookies_path)
                login_success = True
        
        # 即使没有登录成功，也尝试访问UP主页面(有些UP主不需要登录也能查看)
        
        # 直接访问视频列表页
        url = f"https://space.bilibili.com/{up_id}/video"
        print(f"正在访问: {url}")
        driver.get(url)

        # 等待页面加载
        wait_for_page_load(driver)

        # 检查是否有登录弹窗，如果有则需要手动登录
        if check_login_popup(driver):
            print("检测到登录弹窗，需要手动登录...")
            if manual_login(driver):
                # 保存新的Cookies供下次使用
                save_cookies(driver, cookies_path)
                # 重新访问页面
                driver.get(url)
                wait_for_page_load(driver)

        # 获取视频总数和总页数
        total_videos = get_video_count(driver)
        total_pages = get_total_pages(driver)
        
        print(f"检测到视频总数约: {total_videos}")
                    print(f"检测到总页数: {total_pages}")
        
        # 如果无法检测到页数，尝试使用视频数估算
        if total_pages <= 1 and total_videos > 30:
            estimated_pages = (total_videos + 29) // 30  # 每页约30个视频
            total_pages = max(estimated_pages, 1)
            print(f"根据视频数量估算页数: {total_pages}")

        # 处理当前页面视频
        current_page_videos = scrape_current_page(driver)
        videos.extend(current_page_videos)
        print(f"第1页找到 {len(current_page_videos)} 个视频")

        # 循环处理后续页面
        page = 2
        consecutive_failures = 0
        max_failures = 5  # 增加失败次数阈值
        
        while page <= total_pages and consecutive_failures < max_failures:
            print(f"\n===== 开始处理第 {page} 页 =====")
            
            # 优先尝试点击按钮导航 - 这样更自然，不会刷新整个页面
            success = navigate_to_page_by_button(driver, page)
            
            # 如果按钮导航失败，尝试URL导航
            if not success:
                success = navigate_to_page_by_url(driver, page, up_id)
            
            # 等待页面加载并滚动
            wait_for_page_load(driver)
            
            # 检查是否成功加载了正确的页面
            is_correct_page = verify_page_number(driver, page)
            
            if not success or not is_correct_page:
                consecutive_failures += 1
                print(f"导航到第{page}页失败 (失败次数: {consecutive_failures}/{max_failures})")
                
                if consecutive_failures < max_failures:
                    print("尝试重新加载页面...")
                    time.sleep(random.uniform(2, 5))
                    continue
                else:
                    print(f"连续{max_failures}次失败，停止翻页")
                break
            else:
                consecutive_failures = 0  # 重置失败计数

            # 提取当前页面视频
            page_videos = scrape_current_page(driver)

            # 添加新找到的视频
            new_count = 0
            existing_bvids = set(v['bvid'] for v in videos)

            for video in page_videos:
                if video['bvid'] not in existing_bvids:
                    videos.append(video)
                    new_count += 1

            print(f"第{page}页找到 {new_count} 个新视频")

            # 视频数量没有增加，可能是页面没有正确加载或者已到达末页
            if new_count == 0:
                # 尝试再次通过URL加载页面，使用不同的查询参数
                retry_url = f"https://space.bilibili.com/{up_id}/video?tid=0&pn={page}&keyword=&order=pubdate"
                print(f"未找到新视频，尝试使用不同参数: {retry_url}")
                driver.get(retry_url)
                wait_for_page_load(driver)

                # 再次尝试获取视频
                retry_videos = scrape_current_page(driver)
                retry_count = 0

                for video in retry_videos:
                    if video['bvid'] not in existing_bvids:
                        videos.append(video)
                        retry_count += 1

                print(f"重试后，第{page}页找到 {retry_count} 个新视频")

                # 如果仍然没有新视频
                if retry_count == 0:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print(f"多次尝试无法获取新视频，可能已到达末页，停止翻页")
                    break
                else:
                    consecutive_failures = 0  # 重置失败计数
            
            # 准备处理下一页
            page += 1

            # 随机延迟，避免请求过快
            time.sleep(random.uniform(3, 7))

        print(f"所有页面处理完成，总共找到 {len(videos)} 个视频")

        # 视频数量与预期差距较大时，尝试使用API方法
        expected_min = max(5, total_videos // 2)  # 至少应该找到一半的视频
        if len(videos) < expected_min:
            print(f"视频数量({len(videos)})远低于预期({total_videos})，尝试使用API方法提取...")
            backup_videos = get_videos_using_api(driver, up_id)

            # 添加备用方法找到的视频
            existing_bvids = set(v['bvid'] for v in videos)
            new_count = 0
            for video in backup_videos:
                if video['bvid'] not in existing_bvids:
                    videos.append(video)
                    new_count += 1

            print(f"API方法新增 {new_count} 个视频，总计 {len(videos)} 个视频")

        return videos

    except Exception as e:
        print(f"视频提取过程中出错: {e}")
        traceback.print_exc()
        return videos
    finally:
        driver.quit()


def check_login_popup(driver):
    """检查页面上是否有登录弹窗"""
    try:
        # 尝试查找常见的登录弹窗元素
        login_elements = driver.find_elements(By.CSS_SELECTOR, 
            ".bili-mini-login-panel, .login-panel, .unlogin-popover, .login-tip, .need-login")
        
        if login_elements:
            print("检测到登录弹窗")
            return True
            
        # 检查是否有包含"登录"字样的弹窗
        login_text_elements = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '登录') or contains(text(), '登陆')]")
            
        for elem in login_text_elements:
            # 检查元素是否可见且像是弹窗的一部分
            if elem.is_displayed() and elem.tag_name in ['div', 'p', 'h2', 'h3', 'span', 'button']:
                parent = driver.execute_script(
                    "return arguments[0].parentNode.parentNode.parentNode", elem)
                if 'popup' in parent.get_attribute('class') or 'modal' in parent.get_attribute('class'):
                    print("检测到登录文本弹窗")
                    return True
        
        return False
    except Exception as e:
        print(f"检查登录弹窗时出错: {e}")
        return False


def wait_for_page_load(driver, timeout=10):
    """等待页面加载完成并执行滚动以加载延迟内容"""
    try:
        # 等待页面加载指示器消失或关键元素出现
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".video-list, .cube-list, .bili-video-card"))
        )
        
        # 执行页面滚动，确保懒加载内容显示
        scroll_page(driver)
        
    except TimeoutException:
        print("页面加载超时")
    except Exception as e:
        print(f"等待页面加载时出错: {e}")


def scrape_current_page(driver):
    """从当前页面获取所有视频信息"""
    videos = []
    page_source = driver.page_source

    # 首先使用更精确的方式提取视频卡片
    try:
        # 2024年B站最新版视频卡片最常见的选择器
        print("尝试使用选择器提取视频卡片...")
        video_items = driver.find_elements(By.CSS_SELECTOR,
                                           '.bili-video-card, .small-item, .video-page-card, [data-v-code]')

        if video_items:
            print(f"找到 {len(video_items)} 个视频卡片元素")

            for item in video_items:
                try:
                    # 尝试在卡片内找到链接
                    link_elem = None
                    try:
                        link_elem = item.find_element(By.CSS_SELECTOR, "a[href*='/video/']")
                    except:
                        # 如果自身就是链接元素
                        if item.tag_name == 'a' and '/video/' in (item.get_attribute('href') or ''):
                            link_elem = item

                    if link_elem:
                        href = link_elem.get_attribute('href')
                        # 提取BV号
                        bvid_match = re.search(r'BV\w{10}', href)

                        if bvid_match:
                            bvid = bvid_match.group(0)

                            # 尝试获取标题
                            title = ''
                            try:
                                title_elem = item.find_element(By.CSS_SELECTOR,
                                                               '.bili-video-card__info--tit, .title, h3')
                                title = title_elem.text.strip() or title_elem.get_attribute('title')
                            except:
                                pass

                            # 添加视频信息
                            videos.append({
                                'bvid': bvid,
                                'title': title or '未知标题',
                                'link': f"https://www.bilibili.com/video/{bvid}"
                            })
                            print(f"找到视频: {bvid} - {title}")
                except Exception as e:
                    # 单个元素处理错误不影响整体
                    pass
    except Exception as e:
        print(f"选择器提取视频卡片时出错: {e}")

    # 备用方法：从页面源码直接提取所有BV号
    if not videos:
        print("使用正则表达式从页面源码提取BV号...")
        bv_pattern = r'BV\w{10}'
        bvids = re.findall(bv_pattern, page_source)

        for bvid in set(bvids):
            # 检查此BV号是否已经添加
            if not any(v['bvid'] == bvid for v in videos):
                videos.append({
                    'bvid': bvid,
                    'title': '标题未知',
                    'link': f"https://www.bilibili.com/video/{bvid}"
                })
                print(f"从源码中提取到视频: {bvid}")

    # 第三种方法：尝试从页面中的JSON数据提取
    if len(videos) < 2:
        print("尝试从页面JSON数据提取视频...")
        try:
            # 尝试提取__INITIAL_STATE__
            state_pattern = r'window\.__INITIAL_STATE__=({.*?});'
            state_match = re.search(state_pattern, page_source)

            if state_match:
                state_json = state_match.group(1)
                try:
                    state_data = json.loads(state_json)

                    # 尝试不同的数据路径
                    if 'videoList' in state_data and 'vlist' in state_data['videoList']:
                        vlist = state_data['videoList']['vlist']
                        for video in vlist:
                            bvid = video.get('bvid')
                            if bvid and not any(v['bvid'] == bvid for v in videos):
                                videos.append({
                                    'bvid': bvid,
                                    'title': video.get('title', '未知标题'),
                                    'link': f"https://www.bilibili.com/video/{bvid}"
                                })
                                print(f"从INITIAL_STATE中提取到视频: {bvid}")
                except:
                    print("解析INITIAL_STATE JSON失败")
        except Exception as e:
            print(f"从JSON数据提取视频时出错: {e}")

    return videos


def get_videos_using_api(driver, up_id):
    """使用B站API获取视频列表"""
    videos = []

    try:
        # 访问API URL
        for page in range(1, 5):  # 尝试获取前5页
            api_url = f"https://api.bilibili.com/x/space/arc/search?mid={up_id}&ps=30&tid=0&pn={page}&keyword=&order=pubdate"
            print(f"请求API: {api_url}")

            driver.get(api_url)
            time.sleep(3)

            # 尝试解析JSON响应
            try:
                pre_element = driver.find_element(By.TAG_NAME, "pre")
                json_text = pre_element.text
                data = json.loads(json_text)

                if data.get('code') == 0 and 'data' in data and 'list' in data['data'] and 'vlist' in data['data'][
                    'list']:
                    vlist = data['data']['list']['vlist']

                    if not vlist:
                        print(f"API第{page}页没有数据，停止请求")
                        break

                    for video in vlist:
                        bvid = video.get('bvid')
                        if bvid:
                            videos.append({
                                'bvid': bvid,
                                'title': video.get('title', '未知标题'),
                                'link': f"https://www.bilibili.com/video/{bvid}"
                            })
                            print(f"API获取视频: {bvid}")
                else:
                    print(f"API返回错误或无数据: {data.get('message')}")
                    break
            except Exception as e:
                print(f"解析API响应失败: {e}")
                break

            # 随机延迟
            time.sleep(random.uniform(1, 3))

    except Exception as e:
        print(f"API获取视频列表失败: {e}")

    print(f"API总共获取到 {len(videos)} 个视频")
    return videos


def save_video_links(videos, filename="video_links.txt"):
    """保存视频链接到文件"""
    if not videos:
        print("没有视频可保存")
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

        print(f"视频链接已保存到 {filename}")
        print(f"详细信息已保存到 {detail_filename}")
        return True
    except Exception as e:
        print(f"保存文件出错: {e}")
        return False


def extract_user_id(url):
    """从URL中提取用户ID"""
    match = re.search(r'space\.bilibili\.com/(\d+)', url)
    if match:
        return match.group(1)
    return None


def main():
    """程序入口点"""
    print("=" * 50)
    print("B站UP主视频链接提取工具")
    print("=" * 50)
    
    # 用户输入UP主ID或链接
    up_input = input("请输入UP主ID或主页链接: ").strip()
    
    # 判断输入是纯数字ID还是链接
    if up_input.isdigit():
        user_id = up_input
    else:
        # 从链接中提取ID
        user_id = extract_user_id(up_input)
        
    if not user_id:
        print("无效的B站UP主ID或链接")
        return

    print(f"开始提取UP主 {user_id} 的视频链接")
    
    # 询问是否使用保存的Cookies
    use_saved_cookies = True
    cookies_input = input("是否使用保存的Cookies尝试登录? (y/n, 默认y): ").lower()
    if cookies_input == 'n':
        use_saved_cookies = False

    # 获取视频
    cookies_path = r"C:\Users\DELL\Desktop\bilibili.txt"
    videos = get_bilibili_videos(user_id, use_cookies=use_saved_cookies, cookies_path=cookies_path)

    # 去重
    unique_videos = []
    seen_bvids = set()

    for video in videos:
        if video['bvid'] not in seen_bvids:
            seen_bvids.add(video['bvid'])
            unique_videos.append(video)

    if unique_videos:
        # 保存视频链接
        save_video_links(unique_videos, f"up_{user_id}_videos.txt")
        print(f"成功提取 {len(unique_videos)} 个不重复视频链接")
    else:
        print("未能提取到任何视频链接")


if __name__ == "__main__":
    main()
