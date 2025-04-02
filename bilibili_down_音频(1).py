import csv
import json
import time
import requests
import re
import os
import subprocess
from pprint import pprint
import pandas as pd
import re

from urllib.parse import urlparse

def is_valid_url(url):
    """检查 URL 是否有效"""
    parsed_url = urlparse(url)
    return parsed_url.scheme in ['http', 'https'] and parsed_url.netloc != ''

def sanitize_filename(filename):
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n']
    for char in illegal_chars:
        filename = filename.replace(char, '')
    filename = filename.replace('\n', ' ')  # 将换行符替换为空格或者直接删除
    return filename

# 输出路径
output_path = r"D:\音效视频"  # 指定输出目录

# 确保输出目录存在
if not os.path.exists(output_path):
    os.makedirs(output_path)

# Excel 文件路径
excel_file = r"C:\Users\DELL\Desktop\电台音频.xlsx"

# 读取 Excel 文件
df = pd.read_excel(excel_file)

# 检查“链接”列是否存在
if '链接' in df.columns:
    try:
        # 遍历“链接”列的每一行
        for url in df['链接']:
            if not is_valid_url(url):
                print(f"无效的 URL：{url}，跳过此链接。")
                continue  # 跳过当前循环，继续下一个链接
            # 这里可以添加你对有效 URL 的处理逻辑，比如下载视频等
            print(f"有效 URL：{url}")
            if "p=" in url:
                start_index = url.index("p=") + 2
                end_index = start_index
                while end_index < len(url) and url[end_index].isdigit():
                    end_index += 1
                a_value = url[start_index:end_index]
                print(f"提取的 p 值为: {a_value}")
            else:
                a_value="0"
            # 请求头
            headers = {
                "Cookie": "_ga=GA1.1.1910727854.1743402173; Hm_lvt_b97569d26a525941d8d163729d284198=1743402173; HMACCOUNT=CB00A0C3201B1143; JSESSIONID=D7D65EBDF1FEE17F963CEABE0BC06A33; Hm_lvt_e8002ef3d9e0d8274b5b74cc4a027d08=1743402173; Hm_lvt_a748d15030989c341737dce02fbfa9a3=1743402173; Hm_lpvt_e8002ef3d9e0d8274b5b74cc4a027d08=1743402573; _ga_852H6NENR0=GS1.1.1743402172.1.1.1743402828.0.0.0; Hm_lpvt_a748d15030989c341737dce02fbfa9a3=1743402829; Hm_lpvt_b97569d26a525941d8d163729d284198=1743402829",
                "referer": "https://www.bilibili.com/video/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
            }

            video_header = {
                "referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
            }

            try:
                response = requests.get(url=url, headers=headers)
                response.raise_for_status()  # 检查请求是否成功
            except requests.RequestException as e:
                print(f"请求失败：{e}，跳过此链接。")
                continue  # 跳过当前循环，继续下一个链接

            time.sleep(15)

            # 解析数据
            title_match = re.findall('"title":"(.*?)","pubdate"', response.text)
            if not title_match:
                print(f"无法从URL {url} 中提取标题，跳过此链接。")
                continue  # 跳过当前循环，继续下一个链接
            title = title_match[0]
            title = sanitize_filename(title)
            # 设置文件路径
            audio_path = os.path.join(output_path, f'{title}.mp3')
            # video_path = os.path.join(output_path, f'{title}.mp4')
            # output_file = os.path.join(output_path, f'{title}-out.mp4')
            if os.path.exists(audio_path):
                print(f"{audio_path} 已存在，跳过")
                continue  # 跳过当前循环，继续下一个链接

            html_data_match = re.findall('<script>window.__playinfo__=(.*?)</script>', response.text)
            if not html_data_match:
                print(f"无法从URL {url} 中提取播放信息，跳过此链接。")
                continue  # 跳过当前循环，继续下一个链接
            html_data = html_data_match[0]
            json_data = json.loads(html_data)


            audio_url_matchs = json_data["data"]["dash"].get("audio", [])
            if audio_url_matchs:
                audio_url_match = audio_url_matchs[0].get("baseUrl")
                if audio_url_match and is_valid_url(audio_url_match):
                    print("音频地址为：", audio_url_match)
                    time.sleep(10)
                    try:
                        audio_content = requests.get(url=audio_url_match, headers=video_header)
                        audio_content.raise_for_status()
                        with open(audio_path, mode="wb") as f:
                            f.write(audio_content.content)
                            print(f"下载{audio_path}成功")
                    except requests.RequestException as e:
                        print(f"下载音频失败：{e}，跳过此链接。")
                        continue  # 跳过当前循环，继续下一个链接

                else:
                    print(f"无法从播放信息中提取音频URL或音频URL无效，跳过此链接。")

    except Exception as e:
        print(f"程序运行异常：{e}")