#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/3/31 18:05
# @Author  : CUI liuliu
# @File    : yt_plus02.py


import yt_dlp
import os
import logging
from datetime import datetime
from urllib.parse import urlparse

# ===================== 配置区域 =====================
url_list = {
     # "https://www.bilibili.com/video/BV1SNXnYyEkU":"延时摄影",
     # "https://www.bilibili.com/video/BV1MEXLYhEiW/?spm_id_from=333.1387.upload.video_card.click&vd_source=d488bea544986800952a2093f9d37a4d":"醉清风影视传媒",
     #    "https://www.bilibili.com/video/BV1jE411D7Xy/?spm_id_from=333.1387.search.video_card.click&vd_source=d488bea544986800952a2093f9d37a4d":"醉清风影视传媒",
     #    "https://www.bilibili.com/video/BV1SE411Q78a/?spm_id_from=333.1387.search.video_card.click":"醉清风影视传媒",
     #    "https://www.bilibili.com/video/BV1eb4y1274z?spm_id_from=333.788.recommend_more_video.0&vd_source=d488bea544986800952a2093f9d37a4d":"_Sunsumday_",
     #    "https://www.bilibili.com/video/BV1eb4y1274z?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=2":"_Sunsumday_",
     #    "https://www.bilibili.com/video/BV1eb4y1274z?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=4":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1eb4y1274z?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=5":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1eb4y1274z?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=3":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1M44y1h7HD/?spm_id_from=333.1387.search.video_card.click&vd_source=d488bea544986800952a2093f9d37a4d":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1M44y1h7HD?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=2":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1M44y1h7HD?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=3":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1M44y1h7HD?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=4":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1M44y1h7HD/?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=5":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1N44y1h7sL/?spm_id_from=333.1387.search.video_card.click":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1N44y1h7sL?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=2":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1N44y1h7sL?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=3":"_Sunsumday_",
        "https://www.bilibili.com/video/BV1yL411t74p/?spm_id_from=333.1387.search.video_card.click": "_Sunsumday_",
        "https://www.bilibili.com/video/BV1yL411t74p?spm_id_from=333.788.videopod.episodes&vd_source=d488bea544986800952a2093f9d37a4d&p=2": "_Sunsumday_",
        "https://www.bilibili.com/video/BV1DP4y1h7Pj/?spm_id_from=333.1387.search.video_card.click&vd_source=d488bea544986800952a2093f9d37a4d": "_Sunsumday_",


# https://www.youtube.com/watch?v=B5unCXpegAw
# https://www.youtube.com/watch?v=T75IKSXVXlc
# https://www.youtube.com/watch?v=kMnpcMnguC4
# https://www.youtube.com/watch?v=pcyLksm78BI
# https://www.youtube.com/watch?v=XTK0n_pR7ZU
# https://www.youtube.com/watch?v=XRGyCY-RILQ
# https://www.youtube.com/watch?v=NuZVXOnqDJ4
# https://www.youtube.com/watch?v=Zj-AnS-4V6s
# https://www.youtube.com/watch?v=s37_-eVX4tE
# https://www.youtube.com/watch?v=_cw8S0XJGKc
# https://www.youtube.com/watch?v=Geu22rPdN4Q

}

cookies_config = {
    "youtube": r"C:\Users\DELL\Desktop\youtube.txt",
    "bilibili": r"C:\Users\DELL\Desktop\bilibili.txt"
}

output_base = r"D:\bilibili视频\延时摄影"  # 下载根目录
log_path = r"C:\Users\DELL\Desktop\cam-prcess-data-1\logs"  # 日志目录
max_retries = 3  # 单个视频最大重试次数


# ===================================================

# 初始化日志系统
def setup_logger():
    os.makedirs(log_path, exist_ok=True)
    log_file = os.path.join(log_path, f"download_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger("VideoDownloader")
    logger.setLevel(logging.INFO)

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


logger = setup_logger()


def get_platform(url):
    """判断URL所属平台"""
    # domain = urlparse(url).netloc.lower()
    if 'youtube' in url:
        return 'youtube'
    elif 'bilibili' in url:
        return 'bilibili'
    else:
        raise ValueError(f"不支持的平台: {url}")


def get_ydl_opts(platform, output_path):
    """获取平台专用配置"""
    common_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'retries': 10,
        'fragment_retries': 10,
        'ignoreerrors': True,
        'noprogress': True,  # 禁用内置进度条
        'progress_hooks': [progress_hook],
        'logger': logger,
        'merge_output_format': 'mp4',
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
            'cookiefile': cookies_config['youtube'],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        }
    elif platform == 'bilibili':
        return {
            **common_opts,
            'format': 'bestvideo+bestaudio',
            'cookiefile': cookies_config['bilibili'],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
        }


def progress_hook(d):
    """自定义进度回调"""
    if d['status'] == 'downloading':
        info = (
            f"进度: {d.get('_percent_str', 'N/A')} | "
            f"速度: {d.get('_speed_str', 'N/A')} | "
            f"剩余时间: {d.get('_eta_str', 'N/A')}"
        )
        logger.info(info)


def safe_download(url, output_path):
    """带重试机制的下载函数"""
    platform = get_platform(url)
    ydl_opts = get_ydl_opts(platform, output_path)

    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"✅ 下载成功: {url}")
            return True
        except yt_dlp.DownloadError as e:
            logger.error(f"❌ 下载失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"⚠️ 放弃下载: {url}")
                return False
        except Exception as e:
            logger.exception(f"⚠️ 未处理的异常: {str(e)}")
            return False

def main():
    logger.info("=" * 50)
    logger.info("视频下载任务启动")
    logger.info(f"总任务数: {len(url_list)}")
    logger.info("=" * 50)

    for idx, (url, title) in enumerate(url_list.items(), 1):
        try:
            logger.info(f"\n▶ 开始处理任务 {idx}/{len(url_list)}")
            logger.info(f"标题: {title}")
            logger.info(f"URL: {url}")

            # 创建平台专用目录
            platform = get_platform(url)
            output_path = os.path.join(output_base, platform, datetime.now().strftime("%Y%m%d"), title)
            os.makedirs(output_path, exist_ok=True)

            logger.info(f"保存路径: {output_path}")

            if safe_download(url, output_path):
                logger.info(f"▌ 任务 {idx} 完成")
            else:
                logger.warning(f"▌ 任务 {idx} 失败")

        except Exception as e:
            logger.error(f"⚠️ 任务处理异常: {str(e)}")
            continue

    logger.info("=" * 50)
    logger.info("所有任务处理完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()