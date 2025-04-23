#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Optimized version of yt_plus02.py

import yt_dlp
import os
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from urllib.parse import urlparse
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any
import random
import json
import pathlib
import re

# ===================== 配置区域 =====================
# 从文件读取URL列表
def load_url_list_from_file(file_path: str) -> Dict[str, str]:
    """从文本文件读取URL列表
    
    文件格式: 每行一个URL和标题，用制表符分隔
    例如: https://www.youtube.com/watch?v=abcdef123456\t视频标题
    """
    result = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和注释
                    parts = line.split('\t', 1)  # 使用制表符分割URL和标题
                    if len(parts) == 2:
                        url, title = parts
                        result[url.strip()] = title.strip()
                    else:
                        # 如果没有标题，使用URL作为标题的依据，但需要清理
                        url = parts[0].strip()
                        # 从URL中提取视频ID作为标题
                        if 'youtube' in url or 'youtu.be' in url:
                            video_id = url.split('v=')[-1].split('&')[0] if 'v=' in url else url.split('/')[-1]
                            result[url] = f"youtube_{video_id}"
                        elif 'bilibili' in url:
                            video_id = url.split('/')[-1]
                            result[url] = f"bilibili_{video_id}"
                        else:
                            # 为其他URL创建安全的标题
                            safe_title = re.sub(r'[\\/:*?"<>|]', '_', url)
                            result[url] = safe_title
        return result
    except Exception as e:
        # 由于logger在后面才定义，这里使用logging模块直接记录错误
        logging.error(f"读取URL列表失败: {str(e)}")
        return {}

# 配置信息
CONFIG = {
    "cookies": {
        "youtube": r"C:\Users\DELL\Desktop\youtube.txt",
        "bilibili": r"C:\Users\DELL\Desktop\bilibili.txt"
    },
    "output_base": r"H:\0421音效乐器采集",  # 下载根目录
    "log_path": r"C:\Users\DELL\Desktop\cam-prcess-data-1\logs",  # 日志目录
    "max_retries": 3,  # 单个视频最大重试次数
    "max_workers": 1,  # 并行下载数量
    "timeout": 600,  # 下载超时(秒)
    "downloaded_record": r"C:\Users\DELL\Desktop\cam-prcess-data-1\downloaded_videos.json",  # 已下载视频记录文件
    "url_list_file": r"C:\Users\DELL\Desktop\新建 文本文档 (3).txt",  # URL列表文件路径
}

# 加载URL列表
url_list = load_url_list_from_file(CONFIG["url_list_file"])

# ===================================================

# 日志配置
class LoggerSetup:
    _logger = None

    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            cls._logger = cls._setup_logger()
        return cls._logger

    @staticmethod
    def _setup_logger():
        os.makedirs(CONFIG["log_path"], exist_ok=True)
        log_file = os.path.join(CONFIG["log_path"], f"download_{datetime.now().strftime('%Y%m%d')}.log")

        logger = logging.getLogger("VideoDownloader")
        logger.setLevel(logging.INFO)

        # 避免重复添加处理器
        if not logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)

            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger


logger = LoggerSetup.get_logger()


# 平台检测
@lru_cache(maxsize=128)
def get_platform(url: str) -> str:
    """判断URL所属平台，使用缓存优化"""
    if 'youtube' in url:
        return 'youtube'
    elif 'bilibili' in url:
        return 'bilibili'
    else:
        raise ValueError(f"不支持的平台: {url}")


# 下载配置
def get_ydl_opts(platform: str, output_path: str, task_id: int) -> Dict[str, Any]:
    """获取平台专用配置"""

    # 创建进度钩子
    def progress_hook(d):
        """自定义进度回调"""
        if d['status'] == 'downloading':
            info = (
                f"任务 {task_id} | "
                f"进度: {d.get('_percent_str', 'N/A')} | "
                f"速度: {d.get('_speed_str', 'N/A')} | "
                f"剩余时间: {d.get('_eta_str', 'N/A')}"
            )
            logger.info(info)

    common_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'retries': 10,
        'fragment_retries': 10,
        'ignoreerrors': True,
        'noprogress': True,  # 禁用内置进度条
        'progress_hooks': [progress_hook],
        'logger': logger,
        'merge_output_format': 'mp4',
        'socket_timeout': CONFIG["timeout"],
        'postprocessors': [{
            'key': 'FFmpegMetadata',
            'add_metadata': True
        }]
    }

    # 平台特定配置
    if platform == 'youtube':
        return {
            **common_opts,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'cookiefile': CONFIG["cookies"]["youtube"],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        }
    elif platform == 'bilibili':
        return {
            **common_opts,
            'format': 'bestvideo+bestaudio',
            'cookiefile': CONFIG["cookies"]['bilibili'],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
        }


async def download_video(url: str, title: str, task_id: int) -> bool:
    """异步下载单个视频"""
    try:
        platform = get_platform(url)

        # 创建日期目录结构
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = os.path.join(CONFIG["output_base"], platform, date_str, title)
        os.makedirs(output_path, exist_ok=True)

        logger.info(f"\n▶ 开始处理任务 {task_id}/{len(url_list)}")
        logger.info(f"标题: {title}")
        logger.info(f"URL: {url}")
        logger.info(f"保存路径: {output_path}")

        # 获取下载配置
        ydl_opts = get_ydl_opts(platform, output_path, task_id)
        if platform == 'youtube':
            await asyncio.sleep(random.uniform(2, 5))

        # 在线程池中运行实际下载（避免阻塞事件循环）
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            for attempt in range(CONFIG["max_retries"]):
                try:
                    # 在线程池中运行下载
                    def download():
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            return ydl.download([url])

                    await loop.run_in_executor(pool, download)
                    
                    # 检查是否实际下载了视频文件
                    files = os.listdir(output_path)
                    video_files = [f for f in files if f.endswith(('.mp4', '.webm', '.mkv'))]
                    
                    if not video_files:
                        # 如果目录为空或只有非视频文件，可能是碰到了人机验证
                        logger.error(f"⚠️ 可能碰到人机验证，目录中没有找到视频文件: {output_path}")
                        return False
                    
                    # 检查视频文件大小是否为0
                    for video_file in video_files:
                        file_path = os.path.join(output_path, video_file)
                        if os.path.getsize(file_path) < 10240:  # 小于10KB的视频文件视为异常
                            logger.error(f"⚠️ 视频文件大小异常，可能是人机验证: {file_path}")
                            return False
                    
                    logger.info(f"✅ 下载成功: {url}")
                    # 保存已下载视频记录
                    save_downloaded_video(url)
                    return True

                except Exception as e:
                    error_message = str(e)
                    logger.error(f"❌ 下载失败 (尝试 {attempt + 1}/{CONFIG['max_retries']}): {error_message}")
                    
                    # 检测是否是人机验证错误
                    if "429" in error_message or "bot" in error_message.lower() or "sign in" in error_message.lower():
                        logger.error(f"⚠️ 检测到人机验证限制，下次运行时将重试此视频: {url}")
                        # 如果遇到人机验证，直接返回失败，以便下次重试
                        return False
                        
                    if attempt < CONFIG["max_retries"] - 1:
                        delay = 2 ** (attempt + 1)
                        logger.info(f"等待 {delay} 秒后重试...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"⚠️ 放弃下载: {url}")
                        return False

    except Exception as e:
        logger.error(f"⚠️ 任务处理异常: {str(e)}")
        return False


# 已下载视频记录
def load_downloaded_videos() -> set:
    """加载已下载视频记录"""
    record_file = CONFIG["downloaded_record"]
    if os.path.exists(record_file):
        try:
            with open(record_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"读取下载记录失败: {str(e)}")
    return set()

def save_downloaded_video(url: str):
    """保存已下载视频记录"""
    record_file = CONFIG["downloaded_record"]
    downloaded = load_downloaded_videos()
    downloaded.add(url)
    try:
        # 确保目录存在
        pathlib.Path(record_file).parent.mkdir(parents=True, exist_ok=True)
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(list(downloaded), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存下载记录失败: {str(e)}")


async def download_manager():
    """管理并发下载"""
    # 加载已下载视频记录
    downloaded_videos = load_downloaded_videos()
    
    logger.info("=" * 50)
    logger.info("视频下载任务启动")
    logger.info(f"总任务数: {len(url_list)}")
    logger.info(f"并行下载数: {CONFIG['max_workers']}")
    logger.info(f"已下载视频数: {len(downloaded_videos)}")
    logger.info("=" * 50)

    # 创建任务列表
    tasks = []
    for idx, (url, title) in enumerate(url_list.items(), 1):
        # 跳过已下载的视频
        if url in downloaded_videos:
            logger.info(f"跳过已下载视频: {url} - {title}")
            continue
            
        task = download_video(url, title, idx)
        tasks.append(task)

    # 如果没有任务需要执行，直接返回
    if not tasks:
        logger.info("没有新视频需要下载")
        return

    # 分批执行下载任务
    results = []
    for i in range(0, len(tasks), CONFIG["max_workers"]):
        batch = tasks[i:i + CONFIG["max_workers"]]
        batch_results = await asyncio.gather(*batch)
        results.extend(batch_results)

    # 统计任务结果
    success_count = results.count(True)
    fail_count = results.count(False)

    logger.info("=" * 50)
    logger.info(f"下载完成统计: 成功 {success_count}, 失败 {fail_count}")
    logger.info("=" * 50)


def main():
    """程序入口点"""
    try:
        # 打印加载的URL信息
        logger.info(f"已从 {CONFIG['url_list_file']} 加载 {len(url_list)} 个URL")
        
        # 运行异步下载管理器
        asyncio.run(download_manager())
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
    except Exception as e:
        logger.exception(f"程序异常: {str(e)}")
    finally:
        logger.info("程序已退出")


if __name__ == "__main__":
    main()
