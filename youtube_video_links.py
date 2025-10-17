from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import time
import traceback
import os
import random
import argparse
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta


def get_youtube_videos(channel_url: str, max_scrolls: int = 500, headless: bool = True, 
                      show_progress: bool = True) -> List[Dict[str, str]]:
    """
    从 YouTube 频道的视频页面提取视频链接。
    
    参数:
        channel_url (str): YouTube 频道的视频页面 URL。
        max_scrolls (int): 进行滚动加载操作的最大次数。
        headless (bool): 是否使用无头模式。
        show_progress (bool): 是否显示进度信息。
    
    返回:
        List[Dict[str, str]]: 包含视频 ID、标题和链接的字典列表。
    """
    # 使用 undetected-chromedriver 的简化配置
    driver = None
    try:
        # 方法1：使用最简单的配置
        driver = uc.Chrome(headless=headless)
    except Exception as e:
        if show_progress:
            print(f"使用默认配置失败，尝试备用配置: {e}")
        try:
            # 方法2：使用基本选项
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            if headless:
                options.add_argument('--headless')
            driver = uc.Chrome(options=options, headless=headless)
        except Exception as e2:
            if show_progress:
                print(f"所有配置都失败: {e2}")
            raise e2
    
    videos = []
    start_time = datetime.now()
    
    try:
        if show_progress:
            print(f"正在访问: {channel_url}")
            print(f"⏰ 开始时间: {start_time.strftime('%H:%M:%S')}")
        driver.get(channel_url)
        time.sleep(5)  # 等待页面加载
        
        # 智能滚动策略 - 针对大量视频优化
        scrolls = 0
        no_change_count = 0  # 连续无变化次数
        max_no_change = 5    # 连续5次无变化则停止
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        
        if show_progress:
            print(f"开始智能滚动加载视频 (最多 {max_scrolls} 次)...")
            print("💡 提示: 对于大量视频的频道，滚动可能需要较长时间")
        
        while scrolls < max_scrolls and no_change_count < max_no_change:
            # 滚动到页面底部
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            
            # 动态等待时间 - 根据滚动次数调整
            if scrolls < 50:
                wait_time = random.uniform(1, 2)  # 前50次快速滚动
            elif scrolls < 200:
                wait_time = random.uniform(2, 3)  # 中间阶段中等速度
            else:
                wait_time = random.uniform(3, 5)  # 后期慢速滚动，确保加载完成
            
            time.sleep(wait_time)
            
            # 检查页面高度变化
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            
            if show_progress and (scrolls + 1) % 10 == 0:
                print(f"滚动进度: {scrolls + 1}/{max_scrolls} - 页面高度: {new_height} - 等待时间: {wait_time:.1f}s")
            
            if new_height == last_height:
                no_change_count += 1
                if show_progress and no_change_count == 1:
                    print("⚠️ 页面高度未变化，继续尝试...")
            else:
                no_change_count = 0  # 重置无变化计数
                last_height = new_height
            
            scrolls += 1
            
            # 每100次滚动后暂停一下，让页面完全加载
            if scrolls % 100 == 0:
                if show_progress:
                    print(f"🔄 已滚动 {scrolls} 次，暂停3秒让页面完全加载...")
                time.sleep(3)
        
        if no_change_count >= max_no_change:
            if show_progress:
                print(f"✅ 连续 {max_no_change} 次无变化，停止滚动")
        elif scrolls >= max_scrolls:
            if show_progress:
                print(f"✅ 已达到最大滚动次数 {max_scrolls}")
        
        if show_progress:
            scroll_end_time = datetime.now()
            scroll_duration = scroll_end_time - start_time
            print(f"📊 滚动统计: 总共滚动 {scrolls} 次，最终页面高度: {last_height}")
            print(f"⏱️ 滚动耗时: {scroll_duration.total_seconds():.1f} 秒")
        
        # 等待视频链接元素出现
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/watch?v=']")))
        except Exception as e:
            if show_progress:
                print("等待视频链接超时，继续提取...")
        
        if show_progress:
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
                if show_progress:
                    print(f"使用选择器找到视频元素: {selector}")
                break
        
        if not video_elements:
            if show_progress:
                print("未找到视频元素")
            return videos

        seen_video_ids = set()
        processed_count = 0
        total_elements = len(video_elements)
        
        if show_progress:
            print(f"开始处理 {total_elements} 个视频元素...")
        
        for idx, elem in enumerate(video_elements):
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
                    
                    if video_id and video_id not in seen_video_ids:
                        seen_video_ids.add(video_id)
                        videos.append({
                            "video_id": video_id,
                            "title": title.strip() if title else "无标题",
                            "link": link
                        })
                        processed_count += 1
                        
                        # 根据视频数量调整进度显示频率
                        if show_progress:
                            if total_elements < 100:
                                if processed_count % 5 == 0:
                                    print(f"已处理 {processed_count} 个视频...")
                            elif total_elements < 1000:
                                if processed_count % 20 == 0:
                                    print(f"已处理 {processed_count} 个视频...")
                            else:
                                if processed_count % 50 == 0:
                                    print(f"已处理 {processed_count} 个视频...")
                            
                            # 显示处理进度百分比
                            if (idx + 1) % 100 == 0:
                                progress = ((idx + 1) / total_elements) * 100
                                print(f"📊 处理进度: {progress:.1f}% ({idx + 1}/{total_elements})")
                            
            except Exception as e:
                if show_progress:
                    print(f"处理第 {idx + 1} 个元素时出错: {e}")
                traceback.print_exc()
        
        if show_progress:
            end_time = datetime.now()
            total_duration = end_time - start_time
            print(f"总共提取到 {len(videos)} 个视频")
            print(f"⏱️ 总耗时: {total_duration.total_seconds():.1f} 秒")
            if len(videos) > 0:
                avg_time_per_video = total_duration.total_seconds() / len(videos)
                print(f"📈 平均每个视频耗时: {avg_time_per_video:.2f} 秒")
        return videos
    except Exception as e:
        if show_progress:
            print(f"获取视频时发生错误: {e}")
        traceback.print_exc()
        return videos
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                if show_progress:
                    print(f"关闭浏览器时出错: {e}")


def save_video_links(videos: List[Dict[str, str]], filename: str = "youtube_video_links.txt", 
                    save_json: bool = False) -> bool:
    """
    将视频链接保存到文件中。
    
    参数:
        videos (List[Dict[str, str]]): 视频字典列表。
        filename (str): 输出文件名。
        save_json (bool): 是否同时保存JSON格式。
    
    返回:
        bool: 保存成功返回 True，否则返回 False。
    """
    if not videos:
        print("没有视频需要保存")
        return False
    
    try:
        # 保存链接文件
        with open(filename, "w", encoding="utf-8") as f:
            for video in videos:
                f.write(f"{video['link']}\n")
        
        # 保存详细信息文件
        detail_filename = os.path.splitext(filename)[0] + "_details.txt"
        with open(detail_filename, "w", encoding="utf-8") as f:
            for idx, video in enumerate(videos, 1):
                f.write(f"视频 {idx}:\n")
                f.write(f"标题: {video['title']}\n")
                f.write(f"链接: {video['link']}\n")
                f.write(f"视频ID: {video['video_id']}\n")
                f.write("-"*50 + "\n")
        
        # 保存JSON文件（可选）
        if save_json:
            json_filename = os.path.splitext(filename)[0] + ".json"
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(videos, f, ensure_ascii=False, indent=2)
            print(f"JSON文件已保存到: {json_filename}")
        
        print(f"视频链接已保存到: {filename}")
        print(f"视频详情已保存到: {detail_filename}")
        return True
        
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="从YouTube频道提取视频链接")
    parser.add_argument("--url", "-u", 
                       help="YouTube频道的视频页面URL")
    parser.add_argument("--max-scrolls", "-s", type=int, default=10,
                       help="最大滚动次数 (默认: 10)")
    parser.add_argument("--output", "-o", default="youtube_video_links.txt",
                       help="输出文件名 (默认: youtube_video_links.txt)")
    parser.add_argument("--headless", action="store_true", default=True,
                       help="使用无头模式 (默认: True)")
    parser.add_argument("--no-headless", action="store_false", dest="headless",
                       help="不使用无头模式")
    parser.add_argument("--json", action="store_true",
                       help="同时保存JSON格式文件")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="静默模式，不显示进度信息")
    
    return parser.parse_args()


def detect_high_video_channel(channel_url: str) -> bool:
    """检测是否为高视频数量频道"""
    # 一些已知的高视频数量频道特征
    high_video_channels = [
        "@RelaxationChannel",
        "@Music",
        "@VEVO", 
        "@TED",
        "@BBC",
        "@CNN",
        "@NationalGeographic"
    ]
    
    for channel in high_video_channels:
        if channel in channel_url:
            return True
    return False

def main():
    """
    从 YouTube 频道中提取并保存视频链接的主函数。
    """
    # 直接使用指定的频道URL
    channel_url = "https://www.youtube.com/@dequitem/videos"
    
    # 检测是否为高视频数量频道
    is_high_video_channel = detect_high_video_channel(channel_url)
    
    print("=" * 60)
    print("YouTube 视频链接提取工具")
    print("=" * 60)
    print(f"频道URL: {channel_url}")
    
    if is_high_video_channel:
        print("🔍 检测到高视频数量频道，启用优化模式")
        max_scrolls = 500
        print(f"最大滚动次数: {max_scrolls}")
        print("💡 预计处理时间: 10-30分钟（取决于视频数量）")
    else:
        max_scrolls = 100
        print(f"最大滚动次数: {max_scrolls}")
    
    print("输出文件: youtube_video_links.txt")
    print("无头模式: True")
    print("=" * 60)
    
    try:
        videos = get_youtube_videos(
            channel_url=channel_url,
            max_scrolls=max_scrolls,
            headless=True,
            show_progress=True
        )
        
        if videos:
            success = save_video_links(
                videos=videos,
                filename="youtube_video_links.txt",
                save_json=False
            )
            
            if success:
                print(f"\n✅ 成功提取到 {len(videos)} 个视频链接")
                print(f"📁 文件已保存到: youtube_video_links.txt")
            else:
                print("\n❌ 保存文件失败")
        else:
            print("\n⚠️  未能提取到任何视频链接")
            print("可能的原因:")
            print("1. 频道URL不正确")
            print("2. 网络连接问题")
            print("3. YouTube页面结构发生变化")
            print("4. 需要增加滚动次数")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main() 