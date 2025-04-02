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


def get_bilibili_videos(up_id):
    """提取B站UP主所有视频链接"""
    # 配置浏览器选项
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    # 设置浏览器
    service = Service(r"D:\chrom driver\chrom driver\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    # 修改window.navigator.webdriver为false以绕过检测
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        })
        """
    })

    # 设置窗口大小
    driver.set_window_size(1920, 1080)

    videos = []

    try:
        # 直接访问视频列表页 - 使用标准路径"video"而非"upload/video"
        url = f"https://space.bilibili.com/{up_id}/video"
        print(f"正在访问: {url}")
        driver.get(url)

        # 等待页面加载
        time.sleep(5)

        # 获取页面上展示的视频总数
        try:
            # 尝试获取视频计数信息（可能的位置有多个）
            count_selectors = [
                ".cur-count", ".count", ".all-videos-count",
                ".sub-title .count", ".video-count"
            ]

            for selector in count_selectors:
                try:
                    count_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    count_text = count_elem.text
                    print(f"UP主视频计数: {count_text}")
                    break
                except:
                    continue
        except:
            print("未找到视频计数信息")

        # 尝试获取所有页码元素，确定总页数
        total_pages = 1
        try:
            page_items = driver.find_elements(By.CSS_SELECTOR,
                                              ".paginationjs-pages .paginationjs-page, .pagination .page-item, .be-pager-item")
            if page_items:
                numbers = []
                for item in page_items:
                    try:
                        num = int(item.text.strip())
                        numbers.append(num)
                    except:
                        pass

                if numbers:
                    total_pages = max(numbers)
                    print(f"检测到总页数: {total_pages}")
        except:
            print("无法确定总页数，默认为1页")

        # 处理当前页面视频
        current_page_videos = scrape_current_page(driver)
        videos.extend(current_page_videos)
        print(f"第1页找到 {len(current_page_videos)} 个视频")

        # 循环处理后续页面
        for page in range(2, total_pages + 1):
            if not navigate_to_page(driver, page, up_id):
                print(f"导航到第{page}页失败，停止翻页")
                break

            time.sleep(5)  # 等待新页面加载
            page_videos = scrape_current_page(driver)

            # 添加新找到的视频
            new_count = 0
            existing_bvids = set(v['bvid'] for v in videos)

            for video in page_videos:
                if video['bvid'] not in existing_bvids:
                    videos.append(video)
                    new_count += 1

            print(f"第{page}页找到 {new_count} 个新视频")

            # 视频数量没有增加，可能是页面没有正确加载
            if new_count == 0:
                # 尝试再次通过URL加载页面
                retry_url = f"https://space.bilibili.com/{up_id}/video?page={page}"
                driver.get(retry_url)
                time.sleep(5)

                # 再次尝试获取视频
                retry_videos = scrape_current_page(driver)
                retry_count = 0

                for video in retry_videos:
                    if video['bvid'] not in existing_bvids:
                        videos.append(video)
                        retry_count += 1

                print(f"重试后，第{page}页找到 {retry_count} 个新视频")

                # 如果仍然没有新视频，停止翻页
                if retry_count == 0:
                    print(f"重试后仍未找到新视频，停止翻页")
                    break

            # 随机延迟，避免请求过快
            time.sleep(random.uniform(2, 5))

        print(f"所有页面处理完成，总共找到 {len(videos)} 个视频")

        # 如果视频数量较少，尝试使用备用方法
        if len(videos) < 5:
            print("视频数量较少，尝试使用备用方法提取...")
            backup_videos = get_videos_using_api(driver, up_id)

            # 添加备用方法找到的视频
            existing_bvids = set(v['bvid'] for v in videos)
            for video in backup_videos:
                if video['bvid'] not in existing_bvids:
                    videos.append(video)

            print(f"备用方法后，总计 {len(videos)} 个视频")

        return videos

    except Exception as e:
        print(f"视频提取过程中出错: {e}")
        traceback.print_exc()
        return videos
    finally:
        driver.quit()


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


def navigate_to_page(driver, page_num, up_id):
    """导航到指定页码"""
    print(f"尝试导航到第{page_num}页...")

    # 方法1: 尝试点击分页按钮
    try:
        # 查找并点击指定页码的按钮
        page_btns = driver.find_elements(By.CSS_SELECTOR,
                                         ".paginationjs-pages .paginationjs-page, .pagination .page-item, .be-pager-item")

        found = False
        for btn in page_btns:
            try:
                if btn.text.strip() == str(page_num):
                    print(f"找到第{page_num}页按钮，点击中...")
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(3)
                    found = True
                    break
            except:
                pass

        if found:
            return True
    except Exception as e:
        print(f"点击分页按钮失败: {e}")

    # 方法2: 直接修改URL导航
    try:
        url = f"https://space.bilibili.com/{up_id}/video?page={page_num}"
        print(f"通过URL导航: {url}")
        driver.get(url)
        time.sleep(3)
        return True
    except Exception as e:
        print(f"通过URL导航失败: {e}")
        return False


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
    # 请替换为实际的UP主主页链接
    up_main_url = "https://space.bilibili.com/27901809/search?keyword=%E5%BB%B6%E6%97%B6%E6%91%84%E5%BD%B1"

    # 提取UP主ID - 注意修正路径为标准的/video而非/upload/video
    user_id = extract_user_id(up_main_url)
    if not user_id:
        print("无效的B站UP主链接")
        return

    print(f"开始提取UP主 {user_id} 的视频链接")

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
        print(f"成功提取 {len(unique_videos)} 个不重复视频链接")
    else:
        print("未能提取到任何视频链接")


if __name__ == "__main__":
    main()