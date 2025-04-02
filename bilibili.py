import csv
import json
import time
import requests
import re
import os
import subprocess
from pprint import pprint
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor


def download_video(url, headers, file_path):
    try:
        if os.path.exists(file_path):
            print(f"{file_path}已存在跳过下载")
        else:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        file.write(chunk)
            print(f"视频下载完成: {file_path}")
    except requests.RequestException as e:
        print(f"下载视频失败：{e}")


def is_valid_url(url):
    """检查 URL 是否有效"""
    parsed_url = urlparse(url)
    return parsed_url.scheme in ['http', 'https'] and parsed_url.netloc!= ''


def sanitize_filename(filename):
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n']
    for char in illegal_chars:
        filename = filename.replace(char, '')
    filename = filename.replace('\n', ' ')  # 将换行符替换为空格或者直接删除
    return filename


# 输出路径
output_path = r"D:\bilibili视频\邓园长"  # 指定输出目录

# 确保输出目录存在
if not os.path.exists(output_path):
    os.makedirs(output_path)

# 读取 CSV 文件中的 base_url
csv_file = r"C:\Users\DELL\Desktop\cam-prcess-data-1\src\spider\bilibili.csv"  # CSV 文件路径

# 记录当前处理的链接序号
link_count = 1

with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
    try:
        reader = csv.reader(file)
        for row in reader:
            url = row[0]  # 获取每一行的 base_url

            if not is_valid_url(url):
                print(f"无效的 URL：{url}，跳过此链接。")
                continue  # 跳过当前循环，继续下一个链接

            # 请求头
            headers = {
                "cookie":
                    "buvid3=BCFB2D7C-2FBB-69D0-649E-EA1E7453D8DC81458infoc; b_nut=1736403881; _uuid=965BBABA-F3103-77FC-2461-D4F5146638EF05043infoc; rpdid=|(kl)lkR|JJ)0J'u~JYR|J)mR; header_theme_version=CLOSE; enable_web_push=DISABLE; enable_feed_channel=ENABLE; buvid_fp_plain=undefined; bsource=search_bing; home_feed_column=4; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDM2NDI3NTEsImlhdCI6MTc0MzM4MzQ5MSwicGx0IjotMX0.lYEaQXR6bJvIWVpBDhgtPJcjDoSkDdY2RkXy8eg2gEU; bili_ticket_expires=1743642691; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; buvid4=07249AD2-4FEA-D53D-EA0A-CA3E523117A490681-025010906-Tlxm0x%2BFH9wmlSxeRduQRg%3D%3D; fingerprint=cb745620388008990781bc0e2142add9; buvid_fp=cb745620388008990781bc0e2142add9; bp_t_offset_1976684408=1050436365084262400; b_lsid=58113610F_195F42A1503; SESSDATA=53cd535b%2C1759110233%2C42fd0%2A41CjA-qL17EiU78rbA3NSHQXhrQ2QytlB8Uos6gqektR8KH45C5ODAe9PoGJDMDFYUNyYSVkJDNWVRZmhYR1pQcUZNcEl1OTg0YlJYUVluTVcxMWRjS1BUd1ZkMThpd2lEcFVzZ2xGaWpwSUIySnZldzVSSFhHd3lJSEh5eWRIc3hIeV9XdEpFeDNBIIEC; bili_jct=0cb71345efe287078501dfccd08ef140; DedeUserID=476990344; DedeUserID__ckMd5=afa6a27510b63e3e; CURRENT_QUALITY=112; bp_t_offset_476990344=1051066720254427136; browser_resolution=1257-677; CURRENT_FNVAL=4048; sid=dq48sv4p",

                             # "buvid3=615FE795-139B-FC67-42CD-7EBD3C3CECC251454infoc; b_nut=1735522351; b_lsid=D82C6ED7_1942487862E; bsource=search_baidu; _uuid=54DDD5CC-D1F2-16109-B2F10-AB829BDE15D554744infoc; buvid_fp=f5d90131d3e24371a0cef1b2b0fd5476; enable_web_push=DISABLE; home_feed_column=5; browser_resolution=1536-703; CURRENT_FNVAL=4048; buvid4=2D6AC6F7-EC11-056B-21D8-E0E254C1D31166978-024123001-eemYTBp1RvMgE1liZuW4Tw%3D%3D; sid=6rqpn50c; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzU3ODc2MjYsImlhdCI6MTczNTUyODM2NiwicGx0IjotMX0.cbJ2n5yIekVC8DwpDxxETwPoItxOf2cJCKT8O6nMBFo; bili_ticket_expires=1735787566; rpdid=|(YR|YRYkkm0J'u~JllkkRRm; header_theme_version=CLOSE; bp_t_offset_701485130=1016914007900028928; is-2022-channel=1; SESSDATA=e6bdeb3f%2C1751161973%2Ca47ba%2Ac1CjCNwcL1mzHm_KHQ3g13KMBkdCNc4OmQbGbZq5PpRG1g7_zPqLenoY1KWc5weuNXsKcSVkN0STl1cU9xWWhndDNuTlhrWHprNWpROGZNN0xqQS1DMVdwM0dqMjVkOE1US21xV3pBS1phZTQ3bnhkTzNVczhyMUZ1UWk3ZHloNDVQMThxWHBjOXJBIIEC; bili_jct=10d75ee53078a2bf7269dabfbe4cabc8; DedeUserID=518717379; DedeUserID__ckMd5=8d9bd4cb88a9db25; fingerprint=f5d90131d3e24371a0cef1b2b0fd5476; buvid_fp_plain=undefined; bp_t_offset_518717379=1017030861075251200",
                    # "buvid3=615FE795-139B-FC67-42CD-7EBD3C3CECC251454infoc; b_nut=1735522351; b_lsid=9682737A_1941A8D126F; bsource=search_baidu; _uuid=54DDD5CC-D1F2-16109-B2F10-AB829BDE15D554744infoc; buvid_fp=f5d90131d3e24371a0cef1b2b0fd5476; enable_web_push=DISABLE; home_feed_column=5; browser_resolution=1536-703; CURRENT_FNVAL=4048; buvid4=2D6AC6F7-EC11-056B-21D8-E0E254C1D31166978-024123001-eemYTBp1RvMgE1liZuW4Tw%3D%3D; sid=6rqpn50c; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzU3ODc2MjYsImlhdCI6MTczNTUyODM2NiwicGx0IjotMX0.cbJ2n5yIekVC8DwpDxxETwPoItxOf2cJCKT8O6nMBFo; bili_ticket_expires=1735787566; rpdid=|(YR|YRYkkm0J'u~JllkkRRm; header_theme_version=CLOSE; bp_t_offset_701485130=1016914007900028928; is-2022-channel=1; SESSDATA=e6bdeb3f%2C1751161973%2Ca47ba%2Ac1CjCNwcL1mzHm_KHQ3g13KMBkdCNc4OmQbGbZq5PpRG1g7_zPqLenoY1KWc5weuNXsKcSVkN0STl1cU9xWWhndDNuTlhrWHprNWpROGZNN0xqQS1DMVdwM0dqMjVkOE1US21xV3pBS1phZTQ3bnhkTzNVczhyMUZ1UWk3ZHloNDVQMThxWHBjOXJBIIEC; bili_jct=10d75ee53078a2bf7269dabfbe4cabc8; DedeUserID=518717379; DedeUserID__ckMd5=8d9bd4cb88a9db25; fingerprint=f5d90131d3e24371a0cef1b2b0fd5476; buvid_fp_plain=undefined",
                "referer": "https://www.bilibili.com/?spm_id_from=333.1387.0.0",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
            }

            video_header = {
                "referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
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
            original_title = title_match[0]
            original_title = sanitize_filename(original_title)

            # 使用链接序号作为主要标题，原始标题作为备注添加到文件名中
            title_with_seq = f"{link_count}_{original_title}"

            # 设置文件路径
            audio_path = os.path.join(output_path, f'{title_with_seq}.mp3')
            video_path = os.path.join(output_path, f'{title_with_seq}.mp4')
            output_file = os.path.join(output_path, f'{title_with_seq}-out.mp4')
            if os.path.exists(output_file):
                print(f"{output_file} 已存在，跳过")
                continue  # 跳过当前循环，继续下一个链接

            html_data_match = re.findall('<script>window.__playinfo__=(.*?)</script>', response.text)
            if not html_data_match:
                print(f"无法从URL {url} 中提取播放信息，跳过此链接。")
                continue  # 跳过当前循环，继续下一个链接
            html_data = html_data_match[0]
            json_data = json.loads(html_data)

            max_bandwidth_video = ''
            max_bandwidth = 0
            if "data" in json_data and "dash" in json_data["data"]:
                if "video" in json_data["data"]["dash"]:
                    num = len(json_data["data"]["dash"]["video"])
                    for i in range(num):
                        bandwidth = json_data["data"]["dash"]["video"][i]["bandwidth"]
                        if bandwidth > max_bandwidth:
                            max_bandwidth = bandwidth
                            if "baseUrl" in json_data["data"]["dash"]["video"][i]:
                                video_url = json_data["data"]["dash"]["video"][i]["baseUrl"]
                                if is_valid_url(video_url):
                                    max_bandwidth_video = video_url

                    print("最大码率视频地址为：", max_bandwidth_video)
                    print("最大码率为：", max_bandwidth)

                    if not max_bandwidth_video:
                        print(f"无效的视频 URL，跳过此链接。")
                        continue


                    download_video(max_bandwidth_video, video_header, video_path)

                    # try:
                    #     video_content = requests.get(url=max_bandwidth_video, headers=video_header, timeout=10)
                    #     video_content.raise_for_status()
                    #     with open(video_path, mode="wb") as f:
                    #         f.write(video_content.content)
                    # except requests.RequestException as e:
                    #     print(f"下载视频失败：{e}，跳过此链接。")
                    #     continue  # 跳过当前循环，继续下一个链接

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
                            except requests.RequestException as e:
                                print(f"下载音频失败：{e}，跳过此链接。")
                                continue  # 跳过当前循环，继续下一个链接

                            # 合并音频和视频
                            ffmpeg_command = f'ffmpeg -i "{video_path}" -i "{audio_path}" -acodec copy -vcodec copy "{output_file}"'
                            subprocess.run(ffmpeg_command, shell=True)
                            # 删除临时文件
                            os.remove(video_path)
                            os.remove(audio_path)
                            print(f'Processed {url}')
                        else:
                            print(f"无法从播放信息中提取音频URL或音频URL无效，跳过此链接。")
                    else:
                        print(f"无法从播放信息中提取音频URL，跳过此链接。")
            else:
                print(f"无法从播放信息中提取视频数据，跳过此链接。")

            # 处理完一个链接后，序号加1
            link_count += 1

    except Exception as e:
        print(f"程序运行异常：{e}")
