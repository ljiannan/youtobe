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

# ===================== 配置区域 =====================
url_list = {
"https://www.youtube.com/watch?v=w9OIvIeP3W4": "Omni Foundation",
"https://www.youtube.com/watch?v=d6vhqNyZZzo": "Omni Foundation",
"https://www.youtube.com/watch?v=9m2u2_WXn0A": "Omni Foundation",
"https://www.youtube.com/watch?v=OYtQzuYg7RU": "Omni Foundation",
"https://www.youtube.com/watch?v=v7iKy0Ly01M": "Omni Foundation",
"https://www.youtube.com/watch?v=RoXBU9Kh3fY&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=k4GPcXHrxUA": "Omni Foundation",
"https://www.youtube.com/watch?v=Q6VRB9xvimI": "Omni Foundation",
"https://www.youtube.com/watch?v=zgKYpLLlF7k&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=sOObHVOl6PY": "Omni Foundation",
"https://www.youtube.com/watch?v=jHlZUPqx0tE": "Omni Foundation",
"https://www.youtube.com/watch?v=ZeW3zW_cxGk": "Omni Foundation",
"https://www.youtube.com/watch?v=fkNsgMxwoqg": "Omni Foundation",
"https://www.youtube.com/watch?v=kGSkfgaNRcg": "Omni Foundation",
"https://www.youtube.com/watch?v=PpbqGWM9bnQ": "Omni Foundation",
"https://www.youtube.com/watch?v=pMiERPAhs-4": "Omni Foundation",
"https://www.youtube.com/watch?v=CSMu9ib_nls": "Omni Foundation",
"https://www.youtube.com/watch?v=hGVJzOhMKsw": "Omni Foundation",
"https://www.youtube.com/watch?v=Iz54GekE5Bw": "Omni Foundation",
"https://www.youtube.com/watch?v=5IneR3Dy_-E": "Omni Foundation",
"https://www.youtube.com/watch?v=fUlTpBciGr4": "Omni Foundation",
"https://www.youtube.com/watch?v=7ebjfSsiKwQ": "Omni Foundation",
"https://www.youtube.com/watch?v=UTQhqDKe1x4&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=T1S5AsBNkSs": "Omni Foundation",
"https://www.youtube.com/watch?v=T33_Ve63ccw&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=ESUr0BMPCOI": "Omni Foundation",
"https://www.youtube.com/watch?v=9gkLlwyiap4": "Omni Foundation",
"https://www.youtube.com/watch?v=tS4C3ykqY4M": "Omni Foundation",
"https://www.youtube.com/watch?v=YN_rFF0SGYE": "Omni Foundation",
"https://www.youtube.com/watch?v=eH-Tx90TVYY": "Omni Foundation",
"https://www.youtube.com/watch?v=yxI71ptAoMY": "Omni Foundation",
"https://www.youtube.com/watch?v=HvCWPhRYPgs": "Omni Foundation",
"https://www.youtube.com/watch?v=_F6HPttVazk": "Omni Foundation",
"https://www.youtube.com/watch?v=CftrHCiyfmg": "Omni Foundation",
"https://www.youtube.com/watch?v=B6lFH59I5Oc": "Omni Foundation",
"https://www.youtube.com/watch?v=YBTYDVBRjJs": "Omni Foundation",
"https://www.youtube.com/watch?v=SshnbfG8zBI": "Omni Foundation",
"https://www.youtube.com/watch?v=ksRzttaXwpc": "Omni Foundation",
"https://www.youtube.com/watch?v=KxxhLeVL5_Y": "Omni Foundation",
"https://www.youtube.com/watch?v=sc7WHRPfKdg": "Omni Foundation",
"https://www.youtube.com/watch?v=UXciBiD9Csg": "Omni Foundation",
"https://www.youtube.com/watch?v=ovofkQniwuQ&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=gQS5T-dl6-E&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=k7Ho5g3hGiM": "Omni Foundation",
"https://www.youtube.com/watch?v=pWStK9HBUOc": "Omni Foundation",
"https://www.youtube.com/watch?v=KnmdI_XUxAs": "Omni Foundation",
"https://www.youtube.com/watch?v=wSoSTVQ2oDo": "Omni Foundation",
"https://www.youtube.com/watch?v=3Dw17ofSFag&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=uOFFQXvHN4g": "Omni Foundation",
"https://www.youtube.com/watch?v=pql42pc__CI": "Omni Foundation",
"https://www.youtube.com/watch?v=ASQMFI6zjXQ": "Omni Foundation",
"https://www.youtube.com/watch?v=bm4hqUFDzYU": "Omni Foundation",
"https://www.youtube.com/watch?v=0ZdVdnbnwNs": "Omni Foundation",
"https://www.youtube.com/watch?v=tONvdf-mo2Y": "Omni Foundation",
"https://www.youtube.com/watch?v=_BgEbcSdFQE": "Omni Foundation",
"https://www.youtube.com/watch?v=R814Aa2ppjc": "Omni Foundation",
"https://www.youtube.com/watch?v=V4ww21JE_YU": "Omni Foundation",
"https://www.youtube.com/watch?v=b2gDCh-KTKE": "Omni Foundation",
"https://www.youtube.com/watch?v=DXddIB5v1nc": "Omni Foundation",
"https://www.youtube.com/watch?v=rNEOpGuFQGo": "Omni Foundation",
"https://www.youtube.com/watch?v=zwzjLeQIokE": "Omni Foundation",
"https://www.youtube.com/watch?v=ULaVA0kp1vQ": "Omni Foundation",
"https://www.youtube.com/watch?v=aFZr-pF7knk": "Omni Foundation",
"https://www.youtube.com/watch?v=OyV2hC1QhDA": "Omni Foundation",
"https://www.youtube.com/watch?v=muFcUtlLufQ": "Omni Foundation",
"https://www.youtube.com/watch?v=ZdqCMmncSVM": "Omni Foundation",
"https://www.youtube.com/watch?v=kYAiTtSmOkg": "Omni Foundation",
"https://www.youtube.com/watch?v=dJ8OL72w9Nc": "Omni Foundation",
"https://www.youtube.com/watch?v=CDWdcWpPcIY": "Omni Foundation",
"https://www.youtube.com/watch?v=-giDY77lxg4": "Omni Foundation",
"https://www.youtube.com/watch?v=50mZLkJHEKY": "Omni Foundation",
"https://www.youtube.com/watch?v=NVRMTgHKRRI": "Omni Foundation",
"https://www.youtube.com/watch?v=sXNDa1GdIm0": "Omni Foundation",
"https://www.youtube.com/watch?v=w2uQR_NmB2E": "Omni Foundation",
"https://www.youtube.com/watch?v=YpR1avMAX78": "Omni Foundation",
"https://www.youtube.com/watch?v=d1DgInHD99E": "Omni Foundation",
"https://www.youtube.com/watch?v=nXynRKiTijA": "Omni Foundation",
"https://www.youtube.com/watch?v=0uJns7Aa3Fs": "Omni Foundation",
"https://www.youtube.com/watch?v=Neb19_C6Gwk": "Omni Foundation",
"https://www.youtube.com/watch?v=uaproJS4yxE&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=qek9r-dqP68": "Omni Foundation",
"https://www.youtube.com/watch?v=W-YHFjDUvx4": "Omni Foundation",
"https://www.youtube.com/watch?v=JxexB-ZOylk": "Omni Foundation",
"https://www.youtube.com/watch?v=LgxVUui4_8c": "Omni Foundation",
"https://www.youtube.com/watch?v=cKp9ugv-_5I": "Omni Foundation",
"https://www.youtube.com/watch?v=Vgr7pHtIJx0": "Omni Foundation",
"https://www.youtube.com/watch?v=N4HFGfa6MtY": "Omni Foundation",
"https://www.youtube.com/watch?v=L6GBc7BEPIw&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=HCpGrLq4AjM": "Omni Foundation",
"https://www.youtube.com/watch?v=WxKCgidspgc": "Omni Foundation",
"https://www.youtube.com/watch?v=6lLDSXGPQDU": "Omni Foundation",
"https://www.youtube.com/watch?v=GRc_n5LnxJE": "Omni Foundation",
"https://www.youtube.com/watch?v=ZJUMnj1a6JM": "Omni Foundation",
"https://www.youtube.com/watch?v=Gnlo7yvycxs": "Omni Foundation",
"https://www.youtube.com/watch?v=r9IX6mZfnFk": "Omni Foundation",
"https://www.youtube.com/watch?v=NQ7TlVfDHVY": "Omni Foundation",
"https://www.youtube.com/watch?v=fu41tbQG6xI": "Omni Foundation",
"https://www.youtube.com/watch?v=XQF5E4vnldQ": "Omni Foundation",
"https://www.youtube.com/watch?v=vPG8BnvB6aM": "Omni Foundation",
"https://www.youtube.com/watch?v=g2Jn9BcwKRI": "Omni Foundation",
"https://www.youtube.com/watch?v=s0uUnd7jNFk&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=toxEX-CDZyY": "Omni Foundation",
"https://www.youtube.com/watch?v=cG5eD1o4wVA&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=Q4c9WEc6UBg": "Omni Foundation",
"https://www.youtube.com/watch?v=-q1MwWARzqw": "Omni Foundation",
"https://www.youtube.com/watch?v=m3aYFAZzjnw&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=-ku-_ibgPLo": "Omni Foundation",
"https://www.youtube.com/watch?v=dVgQglYmSsc": "Omni Foundation",
"https://www.youtube.com/watch?v=Mqc8HkHcMYw": "Omni Foundation",
"https://www.youtube.com/watch?v=l5j9Xgz0_JM": "Omni Foundation",
"https://www.youtube.com/watch?v=qiOmRs0ZuEE": "Omni Foundation",
"https://www.youtube.com/watch?v=3ExslFDv6Co": "Omni Foundation",
"https://www.youtube.com/watch?v=_J5aZIt_9-A": "Omni Foundation",
"https://www.youtube.com/watch?v=0iz-r6wP-Ww": "Omni Foundation",
"https://www.youtube.com/watch?v=aRmTn7_aXWU": "Omni Foundation",
"https://www.youtube.com/watch?v=n0o7TU3sFNQ": "Omni Foundation",
"https://www.youtube.com/watch?v=xqU-oiMsCcU": "Omni Foundation",
"https://www.youtube.com/watch?v=44fqqySSaS4": "Omni Foundation",
"https://www.youtube.com/watch?v=RxBHzAaVdCY": "Omni Foundation",
"https://www.youtube.com/watch?v=4SztAEtphlU": "Omni Foundation",
"https://www.youtube.com/watch?v=DZh8rcIkNEY&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=Sw6NK9MqqU4": "Omni Foundation",
"https://www.youtube.com/watch?v=yr_sGrqhdBg": "Omni Foundation",
"https://www.youtube.com/watch?v=FUnJBR5kR0I": "Omni Foundation",
"https://www.youtube.com/watch?v=_XxCU7mghj8": "Omni Foundation",
"https://www.youtube.com/watch?v=OosoIH6osS0": "Omni Foundation",
"https://www.youtube.com/watch?v=1JUfPhrX_S4": "Omni Foundation",
"https://www.youtube.com/watch?v=GmAdrrlfQdg": "Omni Foundation",
"https://www.youtube.com/watch?v=NTB0EABbMw8&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=5fG6gDStP14": "Omni Foundation",
"https://www.youtube.com/watch?v=QJ-vnR8T8mE": "Omni Foundation",
"https://www.youtube.com/watch?v=dO1vKl-SO9Y": "Omni Foundation",
"https://www.youtube.com/watch?v=bHmbPxr29wc": "Omni Foundation",
"https://www.youtube.com/watch?v=DtER8Q7Lic0": "Omni Foundation",
"https://www.youtube.com/watch?v=pMSqqs4cTNA&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=NAVkBARgigo": "Omni Foundation",
"https://www.youtube.com/watch?v=gEHv2mGWeVo": "Omni Foundation",
"https://www.youtube.com/watch?v=e26zZ83Oh6Y": "Omni Foundation",
"https://www.youtube.com/watch?v=ItZ6o3PgERc": "Omni Foundation",
"https://www.youtube.com/watch?v=JawqxFrdysY": "Omni Foundation",
"https://www.youtube.com/watch?v=xfzKoyJ25Xo": "Omni Foundation",
"https://www.youtube.com/watch?v=DpY2oNDuoFo": "Omni Foundation",
"https://www.youtube.com/watch?v=tpjek5pZcH8": "Omni Foundation",
"https://www.youtube.com/watch?v=D6wjD4ekJBg": "Omni Foundation",
"https://www.youtube.com/watch?v=tOMetQ68wPI": "Omni Foundation",
"https://www.youtube.com/watch?v=ZeJLGgxLeLQ": "Omni Foundation",
"https://www.youtube.com/watch?v=NMmD0nDQFgM": "Omni Foundation",
"https://www.youtube.com/watch?v=DdnixrsNgms": "Omni Foundation",
"https://www.youtube.com/watch?v=f6eTz5919Q0": "Omni Foundation",
"https://www.youtube.com/watch?v=Znc3DE81Tj4": "Omni Foundation",
"https://www.youtube.com/watch?v=rIjxgCH_pGw": "Omni Foundation",
"https://www.youtube.com/watch?v=1c4--1pvqNU": "Omni Foundation",
"https://www.youtube.com/watch?v=cBUnTfyxIoA": "Omni Foundation",
"https://www.youtube.com/watch?v=CfM6LSVTeNo&pp=0gcJCX4JAYcqIYzv": "Omni Foundation",
"https://www.youtube.com/watch?v=7ePAC2Rx36w": "Omni Foundation",
"https://www.youtube.com/watch?v=ZBX_MySIyWc": "Omni Foundation",
"https://www.youtube.com/watch?v=oBGKHwFANxs": "Omni Foundation",
"https://www.youtube.com/watch?v=UDxn0J_hhHE&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=2q645CQNwkU": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=7g90gEP9vuQ": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=nBVnzdca-EA": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=iIpVJi2qNy8": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=35I0xiIfp5k": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=5z-ZMx-WGGw": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=BnyVtP7YQi0": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=xpRgR-tZEpk": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=sS1WYIu_gA4": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=Pp1Vims_oTk": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=DyjPdNFEZC0": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=zkZnWFUMrlA": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=ZwhPhs5SapY": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=KPAozB2o0HE": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=DY9S84LGuls": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=Azzc5odj9V4": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=o0U3mVKLTOk": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=ejmv82QOqKw": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=cfzcrw7SvPY": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=x5oweOmARFQ": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=IhvXQfAND2M": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=AkPsnw7l3wM&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=knXeAYanK3w": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=Vmd5q1mwi-E": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=nvkMaIp6Bc0": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=Yu9rdOmGqVI&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=IoAxyyJkBbU": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=NOIxac4zDKI": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=S_IchSH3xks": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=BmS0JXlizH0": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=zqjyFfjHcdU": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=vkVL2je3nAk&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=OHkmmdCz8-w": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=q6rc-JO3F40": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=f31gDOHSGBY": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=abHAhKm4XdM": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=uZwEW_jCtr0": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=fSl2R8emBtE": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=sna803rDilU": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=V6YNEZ7sudM": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=TfXZ1n6HUeI&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=GX4QpPzEfSE&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=8G_rsnXh3vU&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=kmhV9KGsgoc": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=My_4AS_kxM8": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=53CciCfpwQI": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=aaSjv7Xo33c": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=G1I12v5Tcwc": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=B4FNlVA1piI": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=KN_8KnvWiAg": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=7ISCEZUkHBo": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=l5wecD_RL7I": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=rrmQdNL2V5o": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=MW7r1Nz6d2U&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=UPZrqnAoVxc": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=JZnogFQzROs": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=LCcGFjSWCO4": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=eNZYDD0NkgM": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=h7T4IhrUGu4": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=lf5Aupb-w8o": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=oSoreXUT0bs&pp=0gcJCX4JAYcqIYzv": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=EOa1lluacj0": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=dhFRA-9xXEs": "Lucas Imbiriba",
"https://www.youtube.com/watch?v=lrULMp_kh00": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=Lkv7ktXfzqE": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=D8-rO9pBED0&pp=0gcJCX4JAYcqIYzv": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=z-r4bMd1mZs": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=13_Nr6fWtEI&pp=0gcJCX4JAYcqIYzv": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=W_953NF3htU": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=HWmiTWs20NM": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=Ui7_8IH134w": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=e6reJVRUCFo": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=SD8BOb85GM0": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=iqnbdFlrPgc": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=UxCoB1fef78": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=z77o8iF3CD4": "Miyagawa Haruna Official",
"https://www.youtube.com/watch?v=Yo-rLqzgod0": "Miyagawa Haruna Official",

}

# 配置信息
CONFIG = {
    "cookies": {
        "youtube": r"C:\Users\DELL\Desktop\youtube.txt",
        "bilibili": r"C:\Users\DELL\Desktop\bilibili.txt"
    },
    "output_base": r"E:\0418\音效下载",  # 下载根目录
    "log_path": r"C:\Users\DELL\Desktop\cam-prcess-data-1\logs",  # 日志目录
    "max_retries": 3,  # 单个视频最大重试次数
    "max_workers": 3,  # 并行下载数量
    "timeout": 600,  # 下载超时(秒)
}


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
            'cookiefile': CONFIG["cookies"]['youtube'],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
                    logger.info(f"✅ 下载成功: {url}")
                    return True

                except Exception as e:
                    logger.error(f"❌ 下载失败 (尝试 {attempt + 1}/{CONFIG['max_retries']}): {str(e)}")
                    if attempt == CONFIG["max_retries"] - 1:
                        logger.error(f"⚠️ 放弃下载: {url}")
                        return False

    except Exception as e:
        logger.error(f"⚠️ 任务处理异常: {str(e)}")
        return False


async def download_manager():
    """管理并发下载"""
    logger.info("=" * 50)
    logger.info("视频下载任务启动")
    logger.info(f"总任务数: {len(url_list)}")
    logger.info(f"并行下载数: {CONFIG['max_workers']}")
    logger.info("=" * 50)

    # 创建任务列表
    tasks = []
    for idx, (url, title) in enumerate(url_list.items(), 1):
        task = download_video(url, title, idx)
        tasks.append(task)

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