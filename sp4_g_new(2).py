# _*_ coding: utf-8 _*_
"""
Time:     2025/1/22 17:36
Author:   ZhaoQi Cao(czq)
Version:  V 0.1
File:     sp4_g_new.py
Describe: Write during the python at zgxmt, Github link: https://github.com/caozhaoqi

整体流程

0.扫描已处理log(scan_logs_csv) 生成csv 移动csv中文件至指定路径(move_csv_video)
1.移动文件区分中英文(move_file_ch_en)
2.运行sp4_g_new切割片头片尾
3.获取切割完成数据

"""


import os
import subprocess
import logging
import json
import time
import csv
import shutil
import re
import concurrent.futures
import cv2
from pathlib import Path
from typing import Optional, Tuple, Union
import threading
from tqdm import tqdm

# 日志配置
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'skip_head_tail.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# 路径配置
root_path = r"G:\航拍特写原始数据分辨率筛选1600#85#2.11\已处理\1080\分辨率合格\【4K超清欧美国家街景视频】\下方 特殊"
output_root = r"H:\0415（106盘处理）\下方特殊"
# RTX 4060专用配置
ffmpeg_path = Path(r"D:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe")
ffprobe_path = Path(r"D:\ffmpeg-7.0.2-essentials_build\bin\ffprobe.exe")
# 配置参数b
batch_size = 15  # 每批处理的视频文件数量
head_cut_time = 60*2  # 片头时间（单位：秒）
tail_cut_time = 60*2  # 片尾时间（单位：秒）
TIMEOUT = 300  # 处理超时时间（秒）
MAX_RETRIES = 3  # 最大重试次数

# CSV 文件路径
csv_file_path = Path(log_dir) / 'processed_videos.csv'


def sanitize_filename(filename: str) -> str:
    """清理文件名中的不可见字符和非法字符"""
    # 移除不可见字符
    filename = ''.join(c for c in filename if ord(c) >= 32)
    # 替换Windows文件系统不允许的字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def is_valid_file(file_path: Union[str, Path]) -> bool:
    """判断文件是否为有效的视频文件"""
    file_path = Path(file_path)
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.m4v', '.wmv', '.rmvb', '.dat', '.vob'}
    exclude_dirs = {'$RECYCLE.BIN', 'System Volume Information', 'Windows', 'Program Files', 'Program Files (x86)'}
    
    try:
        # 检查文件大小（小于1MB的可能是损坏的）
        if file_path.stat().st_size < 1024 * 1024:
            return False
            
        return (
            file_path.is_file() and
            file_path.suffix.lower() in valid_extensions and
            not any(excluded in str(file_path) for excluded in exclude_dirs)
        )
    except (OSError, PermissionError):
        return False


def has_chinese_characters(text):
    """判断字符串是否包含中文"""
    return bool(re.search('[\u4e00-\u9fff]', text))


def get_video_info_ffmpeg(video_file):
    """使用 ffprobe 获取视频文件信息：帧率、帧数和时长"""
    try:
        # 确保路径使用正确的编码
        video_file = str(video_file)
        if isinstance(video_file, bytes):
            video_file = video_file.decode('utf-8')

        command = [
            str(ffprobe_path),
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            video_file
        ]
        
        # 使用UTF-8编码运行命令
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            encoding='utf-8'
        )

        if result.returncode != 0:
            logging.error(f"ffprobe 执行错误，文件：{video_file}，错误码：{result.returncode}，stderr：{result.stderr}")
            return None

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logging.error(f"JSON 解析错误，文件：{video_file}，错误：{e}，ffprobe 输出：{result.stdout}")
            return None

        for stream in output.get('streams', []):
            if stream['codec_type'] == 'video':
                fps = eval(stream.get('avg_frame_rate', '0'))
                duration = float(stream.get('duration', 0))

                if 'nb_frames' in stream:
                    frames = int(stream['nb_frames'])
                    return fps, frames, duration
                elif duration > 0 and fps > 0:
                    frames = int(duration * fps)
                    logging.warning(f"文件: {video_file} 缺少 nb_frames, 使用 duration 和 avg_frame_rate 计算的帧数：{frames}")
                    return fps, frames, duration
                else:
                    logging.error(f"文件: {video_file} 缺少 nb_frames 或 duration 或 avg_frame_rate。")
                    return None

        logging.error(f"无法获取视频流信息：{video_file}")
        return None
        
    except Exception as e:
        logging.error(f"获取视频信息时出错，文件：{video_file}，错误：{e}")
        return None


def get_video_info_opencv(video_file):
    """使用 OpenCV 获取视频文件信息：帧率、帧数和时长"""
    try:
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            logging.error(f"无法打开视频文件 {video_file}。")
            print(f"无法打开视频文件 {video_file}。")
            return None
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frames / fps
        cap.release()  # 关闭视频捕获对象
        return fps, frames, duration
    except Exception as e:
        logging.error(f"获取视频信息时出错，文件：{video_file}，错误：{e}")
        print(f"获取视频信息时出错，文件：{video_file}，错误：{e}")
        return None


def skip_head_tail(video_file):
    """跳过视频的片头和片尾"""
    try:
        logging.info(f"开始处理：{repr(video_file)}")
        print(f"\n开始处理：{repr(video_file)}")
        start_time = time.time()

        # 确保路径使用正确的编码
        video_file = str(video_file)
        if isinstance(video_file, bytes):
            video_file = video_file.decode('utf-8')

        # 检查文件是否存在和可访问
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"文件不存在：{video_file}")
        if not os.access(video_file, os.R_OK):
            raise PermissionError(f"无法读取文件：{video_file}")

        # 检查输入文件大小
        file_size = os.path.getsize(video_file)
        if file_size < 1024:  # 小于1KB
            raise ValueError(f"文件过小（{file_size}字节），可能已损坏")

        # 获取视频信息
        print("正在获取视频信息...")
        video_info = get_video_info_ffmpeg(video_file)
        if video_info is None:
            video_info = get_video_info_opencv(video_file)
        if video_info is None:
            raise ValueError("无法获取视频信息")

        fps, frames, duration = video_info
        print(f"视频信息：帧率={fps}, 帧数={frames}, 时长={duration:.2f}秒")

        # 检查视频时长
        if duration <= (head_cut_time + tail_cut_time):
            raise ValueError(f"视频时长（{duration}秒）小于需要切除的总时长（{head_cut_time + tail_cut_time}秒）")

        # 构造输出路径
        base_filename = os.path.splitext(os.path.basename(video_file))[0]
        relative_path = os.path.relpath(os.path.dirname(video_file), root_path)
        output_dir = os.path.join(output_root, relative_path)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{base_filename}_processed.mp4")

        # 确保输出路径使用正确的编码
        output_file = str(Path(output_file))

        # 计算时间点
        start_time_cut = head_cut_time
        duration_cut = duration - head_cut_time - tail_cut_time

        # 构建FFmpeg命令
        print("正在准备FFmpeg命令...")
        command = [
            str(ffmpeg_path),
            '-y',
            '-i', video_file,
            '-ss', str(start_time_cut),
            '-t', str(duration_cut),
            '-c:v', 'h264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-avoid_negative_ts', 'make_zero',
            output_file
        ]

        # 执行FFmpeg命令
        print(f"正在处理视频...")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8'  # 指定编码为UTF-8
        )

        # 实时获取处理进度
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                if "time=" in output:
                    # 提取处理进度
                    time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})", output)
                    if time_match:
                        hours, minutes, seconds = map(int, time_match.groups())
                        processed_time = hours * 3600 + minutes * 60 + seconds
                        progress = (processed_time / duration_cut) * 100
                        print(f"\r处理进度: {progress:.1f}%", end='')

        # 检查处理结果
        if process.returncode != 0:
            stderr_output = process.stderr.read()
            raise subprocess.CalledProcessError(process.returncode, command, stderr_output)

        # 验证输出文件
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"输出文件未生成：{output_file}")

        output_size = os.path.getsize(output_file)
        if output_size < 1024:
            os.remove(output_file)
            raise ValueError(f"输出文件过小（{output_size}字节）")

        # 验证输出视频
        print("\n正在验证输出视频...")
        output_info = get_video_info_ffmpeg(output_file)
        if output_info is None:
            raise ValueError("无法获取输出视频信息")

        _, _, output_duration = output_info
        expected_duration = duration_cut
        if abs(output_duration - expected_duration) > 5:
            raise ValueError(f"输出视频时长异常：预期={expected_duration:.2f}秒，实际={output_duration:.2f}秒")

        end_time = time.time()
        print(f"\n成功处理 {video_file}")
        print(f"处理时间：{end_time - start_time:.2f}秒")
        return True

    except Exception as e:
        logging.error(f"处理失败：{str(e)}")
        print(f"\n处理失败：{str(e)}")
        if 'output_file' in locals() and os.path.exists(output_file):
            try:
                os.remove(output_file)
                print(f"已删除失败的输出文件：{output_file}")
            except:
                pass
        return False


def load_processed_videos():
    """加载已处理的视频路径"""
    processed_videos = set()
    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:
                    processed_videos.add(row[0])
    return processed_videos


def save_processed_videos(processed_videos):
    """保存已处理的视频路径"""
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for video_path in processed_videos:
            writer.writerow([video_path])


def verify_video_integrity(video_path: Union[str, Path]) -> bool:
    """验证视频文件的完整性"""
    try:
        command = [
            str(ffmpeg_path),
            '-v', 'error',
            '-i', str(video_path),
            '-f', 'null',
            '-'
        ]
        result = subprocess.run(command, capture_output=True, timeout=30)
        return result.returncode == 0 and not result.stderr
    except Exception as e:
        logging.error(f"验证视频完整性失败：{video_path}，错误：{e}")
        return False


def get_video_info(video_file: Union[str, Path]) -> Optional[Tuple[float, int, float]]:
    """获取视频信息，使用多种方法尝试"""
    methods = [get_video_info_ffmpeg, get_video_info_opencv]
    
    for method in methods:
        try:
            info = method(video_file)
            if info and all(x > 0 for x in info):
                return info
        except Exception as e:
            logging.warning(f"使用 {method.__name__} 获取视频信息失败：{e}")
            continue
    
    return None


def process_video_with_timeout(video_file: Union[str, Path]) -> bool:
    """使用超时机制处理视频"""
    result = {"success": False}
    
    def _process():
        try:
            result["success"] = skip_head_tail(video_file)
        except Exception as e:
            result["error"] = str(e)
            logging.error(f"处理视频时出错：{e}")
            result["success"] = False
    
    try:
        print(f"\n开始处理文件: {video_file}")
        print(f"检查ffmpeg路径: {ffmpeg_path}")
        print(f"检查ffprobe路径: {ffprobe_path}")
        
        # 验证ffmpeg和ffprobe是否存在且可执行
        if not os.path.exists(ffmpeg_path):
            raise FileNotFoundError(f"找不到ffmpeg: {ffmpeg_path}")
        if not os.path.exists(ffprobe_path):
            raise FileNotFoundError(f"找不到ffprobe: {ffprobe_path}")
            
        # 检查文件权限
        if not os.access(str(ffmpeg_path), os.X_OK):
            raise PermissionError(f"ffmpeg没有执行权限: {ffmpeg_path}")
        if not os.access(str(ffprobe_path), os.X_OK):
            raise PermissionError(f"ffprobe没有执行权限: {ffprobe_path}")
            
        thread = threading.Thread(target=_process)
        thread.start()
        thread.join(timeout=TIMEOUT)
        
        if thread.is_alive():
            logging.error(f"处理视频超时：{video_file}")
            print(f"处理超时，超过{TIMEOUT}秒")
            return False
            
        if not result["success"] and "error" in result:
            print(f"处理失败原因: {result['error']}")
            
        return result["success"]
        
    except Exception as e:
        logging.error(f"处理视频时发生错误：{e}")
        print(f"发生错误: {str(e)}")
        return False


def verify_environment():
    """验证运行环境"""
    print("\n正在验证运行环境...")
    
    # 检查必要的目录
    print(f"检查输入目录: {root_path}")
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"输入目录不存在: {root_path}")
        
    print(f"检查输出目录: {output_root}")
    if not os.path.exists(output_root):
        try:
            os.makedirs(output_root)
            print(f"已创建输出目录: {output_root}")
        except Exception as e:
            raise Exception(f"无法创建输出目录: {e}")
            
    # 检查ffmpeg和ffprobe
    print(f"检查ffmpeg: {ffmpeg_path}")
    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError(f"找不到ffmpeg: {ffmpeg_path}")
        
    print(f"检查ffprobe: {ffprobe_path}")
    if not os.path.exists(ffprobe_path):
        raise FileNotFoundError(f"找不到ffprobe: {ffprobe_path}")
        
    # 测试ffmpeg和ffprobe是否可执行
    try:
        subprocess.run([str(ffmpeg_path), "-version"], capture_output=True, check=True)
        print("ffmpeg 测试成功")
    except Exception as e:
        raise Exception(f"ffmpeg 测试失败: {e}")
        
    try:
        subprocess.run([str(ffprobe_path), "-version"], capture_output=True, check=True)
        print("ffprobe 测试成功")
    except Exception as e:
        raise Exception(f"ffprobe 测试失败: {e}")
        
    print("环境验证完成\n")


def main():
    """主程序"""
    try:
        # 验证环境
        verify_environment()
        
        video_files = []
        root_path_obj = Path(root_path)
        
        print("正在扫描视频文件...")
        for path in root_path_obj.rglob('*'):
            if is_valid_file(path):
                video_files.append(path)

        if not video_files:
            print(f"在目录 {root_path} 中未找到任何视频文件。")
            return

        total_files = len(video_files)
        print(f"\n找到 {total_files} 个视频文件")
        
        # 使用tqdm创建进度条
        with tqdm(total=total_files, desc="处理视频") as pbar:
            success_count = 0
            fail_count = 0
            
            for video_file in video_files:
                try:
                    success = process_video_with_timeout(video_file)
                    if success:
                        success_count += 1
                        pbar.set_postfix({"状态": "成功", "成功": success_count, "失败": fail_count})
                    else:
                        fail_count += 1
                        pbar.set_postfix({"状态": "失败", "成功": success_count, "失败": fail_count})
                except Exception as e:
                    fail_count += 1
                    pbar.set_postfix({"状态": "错误", "成功": success_count, "失败": fail_count})
                    logging.error(f"处理视频时发生错误：{e}")
                    print(f"\n处理出错: {str(e)}")
                finally:
                    pbar.update(1)
            
            # 显示最终统计
            print(f"\n处理完成！总计：{total_files}个文件")
            print(f"成功：{success_count}个")
            print(f"失败：{fail_count}个")
            
            if fail_count > 0:
                print("\n请检查日志文件获取详细错误信息：")
                print(f"日志文件路径: {os.path.join(log_dir, 'skip_head_tail.log')}")
                
    except Exception as e:
        print(f"\n程序运行出错: {str(e)}")
        logging.error(f"程序运行出错: {str(e)}")


if __name__ == "__main__":
    main()