import requests
import re
import json
import csv
import os
import time
import subprocess
from tqdm import tqdm

name_bozhu = 'MING-FPV'
#保存地址
addr = fr"D:\bilibili视频\邓园长"
path = os.path.join(addr,name_bozhu)

"""发送请求获取响应"""
def getResponse(url):
#     headers = {
#     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#     "accept-encoding": "gzip, deflate, br, zstd",
#     "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
#     "cache-control": "max-age=0",
#     "cookie": "buvid3=D1B24835-C4E2-16CD-8EA1-1D559968095317158infoc; b_nut=1737008817; _uuid=A761FF35-E845-15D7-CBBA-18B54D1CE31317861infoc; enable_web_push=DISABLE; buvid4=AE4883FC-09B2-3F98-E46F-879040E7A67017747-025011606-MWTjrWIXFNSc1MIHlwTez2Ce4YTKHIdTDanUq7KIP5naY4m8oSgsucoNyfyVX07S; buvid_fp=81203b833b5dd0f3bb5fb2024ce3676e; DedeUserID=1371768778; DedeUserID__ckMd5=319ab9c97919a0f0; header_theme_version=CLOSE; rpdid=0zbfVFMdPI|1Sba2Vgb|4Fn|3w1TA54z; CURRENT_QUALITY=127; enable_feed_channel=DISABLE; bsource=search_bing; bmg_af_switch=1; bmg_src_def_domain=i2.hdslb.com; SESSDATA=1bd159e7%2C1756804631%2C9d823%2A32CjBOUKKL5hOLzPeIGt-JtlRjqlye5u4gop2o8pDT_zgWDxO_C_SkpjdMiYWaHJn8v0sSVl83UHo2bmdKa0ZfRi1XcS1kZDUxZ0lQd2hGajFEa29zWjFEOWR3YTBXWjFLS3QwNWlENjNTTUtJeXZrMjQ2V3k2bm4wbUJyeVVKUGxyNE8ySnNTTnp3IIEC; bili_jct=2d306617f034cd518b3ed3640c28d2ca; sid=8ojsao83; b_lsid=CAA102D6E_1956F18D16A; bp_t_offset_1371768778=1041480778451517440; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDE1ODgwNTUsImlhdCI6MTc0MTMyODc5NSwicGx0IjotMX0.JIG2tUw_ALsFwfbO4RmaZFbf0mKigTAna_NBu8Rkqvg; bili_ticket_expires=1741587995; home_feed_column=4; browser_resolution=627-738; CURRENT_FNVAL=4048",
#     "priority": "u=0, i=1",
#     "referer": "https://www.bilibili.com/",
#     "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Microsoft Edge\";v=\"133\", \"Chromium\";v=\"133\"",
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": "\"Windows\"",
#     "sec-fetch-dest": "document",
#     "sec-fetch-mode": "navigate",
#     "sec-fetch-site": "same-origin",
#     "sec-fetch-user": "?1",
#     "upgrade-insecure-requests": "1",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"
# }
    headers= {
                "cookie":"bbuvid3=BCFB2D7C-2FBB-69D0-649E-EA1E7453D8DC81458infoc; b_nut=1736403881; _uuid=965BBABA-F3103-77FC-2461-D4F5146638EF05043infoc; rpdid=|(kl)lkR|JJ)0J'u~JYR|J)mR; header_theme_version=CLOSE; enable_web_push=DISABLE; enable_feed_channel=ENABLE; buvid_fp_plain=undefined; bsource=search_bing; home_feed_column=4; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDM2NDI3NTEsImlhdCI6MTc0MzM4MzQ5MSwicGx0IjotMX0.lYEaQXR6bJvIWVpBDhgtPJcjDoSkDdY2RkXy8eg2gEU; bili_ticket_expires=1743642691; buvid4=07249AD2-4FEA-D53D-EA0A-CA3E523117A490681-025010906-Tlxm0x%2BFH9wmlSxeRduQRg%3D%3D; fingerprint=cb745620388008990781bc0e2142add9; buvid_fp=cb745620388008990781bc0e2142add9; bp_t_offset_1976684408=1050436365084262400; b_lsid=58113610F_195F42A1503; SESSDATA=53cd535b%2C1759110233%2C42fd0%2A41CjA-qL17EiU78rbA3NSHQXhrQ2QytlB8Uos6gqektR8KH45C5ODAe9PoGJDMDFYUNyYSVkJDNWVRZmhYR1pQcUZNcEl1OTg0YlJYUVluTVcxMWRjS1BUd1ZkMThpd2lEcFVzZ2xGaWpwSUIySnZldzVSSFhHd3lJSEh5eWRIc3hIeV9XdEpFeDNBIIEC; bili_jct=0cb71345efe287078501dfccd08ef140; DedeUserID=476990344; DedeUserID__ckMd5=afa6a27510b63e3e; bp_t_offset_476990344=1051066720254427136; sid=6qaesq5x; CURRENT_QUALITY=127; CURRENT_FNVAL=4048; browser_resolution=407-677",
                             # "buvid3=615FE795-139B-FC67-42CD-7EBD3C3CECC251454infoc; b_nut=1735522351; b_lsid=D82C6ED7_1942487862E; bsource=search_baidu; _uuid=54DDD5CC-D1F2-16109-B2F10-AB829BDE15D554744infoc; buvid_fp=f5d90131d3e24371a0cef1b2b0fd5476; enable_web_push=DISABLE; home_feed_column=5; browser_resolution=1536-703; CURRENT_FNVAL=4048; buvid4=2D6AC6F7-EC11-056B-21D8-E0E254C1D31166978-024123001-eemYTBp1RvMgE1liZuW4Tw%3D%3D; sid=6rqpn50c; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzU3ODc2MjYsImlhdCI6MTczNTUyODM2NiwicGx0IjotMX0.cbJ2n5yIekVC8DwpDxxETwPoItxOf2cJCKT8O6nMBFo; bili_ticket_expires=1735787566; rpdid=|(YR|YRYkkm0J'u~JllkkRRm; header_theme_version=CLOSE; bp_t_offset_701485130=1016914007900028928; is-2022-channel=1; SESSDATA=e6bdeb3f%2C1751161973%2Ca47ba%2Ac1CjCNwcL1mzHm_KHQ3g13KMBkdCNc4OmQbGbZq5PpRG1g7_zPqLenoY1KWc5weuNXsKcSVkN0STl1cU9xWWhndDNuTlhrWHprNWpROGZNN0xqQS1DMVdwM0dqMjVkOE1US21xV3pBS1phZTQ3bnhkTzNVczhyMUZ1UWk3ZHloNDVQMThxWHBjOXJBIIEC; bili_jct=10d75ee53078a2bf7269dabfbe4cabc8; DedeUserID=518717379; DedeUserID__ckMd5=8d9bd4cb88a9db25; fingerprint=f5d90131d3e24371a0cef1b2b0fd5476; buvid_fp_plain=undefined; bp_t_offset_518717379=1017030861075251200",
                    # "buvid3=615FE795-139B-FC67-42CD-7EBD3C3CECC251454infoc; b_nut=1735522351; b_lsid=9682737A_1941A8D126F; bsource=search_baidu; _uuid=54DDD5CC-D1F2-16109-B2F10-AB829BDE15D554744infoc; buvid_fp=f5d90131d3e24371a0cef1b2b0fd5476; enable_web_push=DISABLE; home_feed_column=5; browser_resolution=1536-703; CURRENT_FNVAL=4048; buvid4=2D6AC6F7-EC11-056B-21D8-E0E254C1D31166978-024123001-eemYTBp1RvMgE1liZuW4Tw%3D%3D; sid=6rqpn50c; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzU3ODc2MjYsImlhdCI6MTczNTUyODM2NiwicGx0IjotMX0.cbJ2n5yIekVC8DwpDxxETwPoItxOf2cJCKT8O6nMBFo; bili_ticket_expires=1735787566; rpdid=|(YR|YRYkkm0J'u~JllkkRRm; header_theme_version=CLOSE; bp_t_offset_701485130=1016914007900028928; is-2022-channel=1; SESSDATA=e6bdeb3f%2C1751161973%2Ca47ba%2Ac1CjCNwcL1mzHm_KHQ3g13KMBkdCNc4OmQbGbZq5PpRG1g7_zPqLenoY1KWc5weuNXsKcSVkN0STl1cU9xWWhndDNuTlhrWHprNWpROGZNN0xqQS1DMVdwM0dqMjVkOE1US21xV3pBS1phZTQ3bnhkTzNVczhyMUZ1UWk3ZHloNDVQMThxWHBjOXJBIIEC; bili_jct=10d75ee53078a2bf7269dabfbe4cabc8; DedeUserID=518717379; DedeUserID__ckMd5=8d9bd4cb88a9db25; fingerprint=f5d90131d3e24371a0cef1b2b0fd5476; buvid_fp_plain=undefined",
                "referer": "https://www.bilibili.com/video/BV1sUkXYuEDd?spm_id_from=333.788.player.player_end_recommend_autoplay&vd_source=d488bea544986800952a2093f9d37a4d",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
            }

    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError异常
        # time.sleep(10)
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
    return response


"""解析响应体"""
def parseResponse(response,count):
    try:
        html_data = re.findall('<script>window.__playinfo__=(.*?)</script>', response.text)[0]
        jsonData = json.loads(html_data)
        videoTitle = re.findall('<title data-vue-meta="true">(.*?)</title>', response.text)[0]
        # print(response.text)
        # print(html_data)
        # print(videoTitle)
        audioUrl = jsonData['data']['dash']['audio'][0]['baseUrl']
        videoUrl = jsonData['data']['dash']['video'][0]['baseUrl']
        # print(audioUrl)
        # print(videoUrl)
        videoInfo = {
            'videoTitle': videoTitle,
            'audioUrl': audioUrl,
            'videoUrl': videoUrl,
        }
        print(f"第{count}个视频获取Response信息成功！")
        return videoInfo
    except (IndexError, KeyError, json.JSONDecodeError) as e:
        print(f"解析响应失败: {e}")
        return None

"""保存视频和音频"""
def saveMedia(fileName, content, mediaType):
    os.makedirs(name=path, exist_ok=True)
    with open(path+fr'\\{fileName}.{mediaType}', mode='wb') as f:
        f.write(content)
    print(f"保存{mediaType}成功！")

def AvMerge(Mp3Name, Mp4Name, savePath,count):
    print(f"开始合并第{count}个音频和视频...")
    print(f"音频文件: {Mp3Name}")
    print(f"视频文件: {Mp4Name}")
    print(f"合并后文件保存路径: {savePath}")
    with open(os.devnull, 'w') as devnull:
        ffmpeg_path = r"D:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe"
        result = subprocess.run(
            [ffmpeg_path, '-i', Mp4Name, '-i', Mp3Name, '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', savePath],
            stdout=devnull,stderr=devnull
        )
    from datetime import datetime
    # 记录程序开始时间
    start_time = datetime.now()
    print(f"第{count}个视频合并成功！")
    print(f"完成时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print('---------------------------------')
    os.remove(Mp3Name)
    os.remove(Mp4Name)

def processUrlFromFile(csvFilePath):
    processed_count = 0  # 初始化计数器
    with open(csvFilePath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) > 0:
                url = row[0]
                mainProcessing(url, processed_count + 1)
                processed_count += 1  # 每处理一个URL，计数器加1

def mainProcessing(url,count):
    try:
        response = getResponse(url)
        if response is None:
            return
        videoInfo = parseResponse(response,count)
        if videoInfo is None:
            return
        fileName = videoInfo['videoTitle']

        audioContent = getResponse(videoInfo['audioUrl']).content
        saveMedia(fileName, audioContent, 'mp3')
        videoContent = getResponse(videoInfo['videoUrl']).content
        saveMedia(fileName, videoContent, 'mp4')


        Mp3Name = path+f'\\{fileName}.mp3'
        Mp4Name = path+f'\\{fileName}.mp4'
        savePath = path+f'\\merge{count}_{fileName}.mp4'
        AvMerge(Mp3Name, Mp4Name, savePath,count)
    except Exception as e:
        print(f"处理URL {url} 时出错: {str(e)}")

# if __name__ == '__main__':
#     path_file=r'D:/python/杨玉鲲/中广/哔哩哔哩/bilibili.csv'
#
#     csvFilePath = input("请输入包含B站视频url地址的CSV文件路径:").strip()
#     # csvFilePath = input("请输入包含B站视频url地址的CSV文件路径:").strip()
#     if not csvFilePath:
#         print("文件路径不能为空，请重新运行程序并输入有效的文件路径。")
#         exit(1)
#     processUrlFromFile(csvFilePath)

if __name__ == '__main__':
    # 使用固定的文件路径
    csvFilePath = r"C:\Users\DELL\Desktop\cam-prcess-data-1\src\spider\bilibili.csv"
    processUrlFromFile(csvFilePath)