from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import traceback
import os
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_youtube_videos(channel_url, max_scrolls=10):
    """
    从 YouTube 频道的视频页面提取视频链接。
    
    参数:
        channel_url (str): YouTube 频道的视频页面 URL。
        max_scrolls (int): 进行滚动加载操作的最大次数。
    
    返回:
        list: 包含视频 ID、标题和链接的字典列表。
    """
    # 设置 Chrome 选项
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_argument('--headless=new')
    options.add_argument('--disable-software-rasterizer')
    
    # chromedriver 可执行文件的路径
    service = Service(r"D:\chrom driver\chrom driver\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    
    videos = []
    
    try:
        print(f"正在访问: {channel_url}")
        driver.get(channel_url)
        time.sleep(5)  # 等待页面加载
        
        # 向下滚动以加载更多视频
        scrolls = 0
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        while scrolls < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scrolls += 1
        
        # 等待视频链接元素出现
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/watch?v=']")))
        except Exception as e:
            print("Timeout waiting for video links, proceeding with extraction.")
        
        print("正在提取视频链接...")
        # 尝试多种选择器以适应不同的 YouTube 布局
        selectors = [
            "ytd-grid-video-renderer a#video-title",
            "ytd-rich-grid-media a#video-title",
            "ytd-rich-grid-media a",
            "a[href*='/watch?v=']"
        ]
        video_elements = []
        for selector in selectors:
            video_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if video_elements:
                print(f"Found video elements using selector: {selector}")
                break
        if not video_elements:
            print("No video elements found using the specified selectors.")

        seen_video_ids = set()
        for elem in video_elements:
            try:
                link = elem.get_attribute("href")
                title = elem.get_attribute("title") or elem.text
                if not link:
                    continue
                # 仅处理有效的观看链接
                if "/watch" in link:
                    video_id = None
                    if "v=" in link:
                        video_id = link.split("v=")[-1].split("&")[0]
                    if video_id and video_id in seen_video_ids:
                        continue
                    seen_video_ids.add(video_id)
                    videos.append({
                        "video_id": video_id,
                        "title": title,
                        "link": link
                    })
                    print(f"Found video: {video_id} - {title}")
            except Exception as e:
                print(f"Error processing an element: {e}")
                traceback.print_exc()
        print(f"Total videos extracted: {len(videos)}")
        return videos
    except Exception as e:
        print(f"Error occurred while fetching videos: {e}")
        traceback.print_exc()
        return videos
    finally:
        driver.quit()


def save_video_links(videos, filename="youtube_video_links.txt"):
    """
    将视频链接保存到文件中。
    
    参数:
        videos (list): 视频字典列表。
        filename (str): 输出文件名。
    
    返回:
        bool: 保存成功返回 True，否则返回 False。
    """
    if not videos:
        print("No videos to save.")
        return False
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for video in videos:
                f.write(f"{video['link']}\n")
        
        detail_filename = os.path.splitext(filename)[0] + "_details.txt"
        with open(detail_filename, "w", encoding="utf-8") as f:
            for idx, video in enumerate(videos, 1):
                f.write(f"Video {idx}:\n")
                f.write(f"Title: {video['title']}\n")
                f.write(f"Link: {video['link']}\n")
                f.write(f"Video ID: {video['video_id']}\n")
                f.write("-"*50 + "\n")
        print(f"Video links saved to {filename}")
        print(f"Video details saved to {detail_filename}")
        return True
    except Exception as e:
        print(f"Error saving files: {e}")
        return False


def main():
    """
    从 YouTube 频道中提取并保存视频链接的主函数。
    """
    # 替换为实际的 YouTube 频道视频页面 URL
    channel_url = "https://www.youtube.com/@miyagawaharunaofficial/videos"
    print(f"开始为频道提取视频链接: {channel_url}")
    
    videos = get_youtube_videos(channel_url)
    if videos:
        save_video_links(videos)
        print(f"成功提取到 {len(videos)} 个视频链接。")
    else:
        print("未能提取到任何视频链接。")


if __name__ == "__main__":
    main() 