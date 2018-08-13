"""
定时脚本，每隔一定时间访问find.update_hot
"""
import requests
import time,os

def update_hot():
    while True:
        requests.get('https://design.zhengsj.top/api/find/update_load')
        time.sleep(5*60)

if __name__=='__main__':
    update_hot()