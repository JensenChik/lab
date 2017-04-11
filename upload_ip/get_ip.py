# coding=utf-8
import requests
from bs4 import BeautifulSoup
import re
import commands
import datetime
import time

while True:
    try:
        req = requests.get('http://m.baidu.com/s?word=ip')
        html = BeautifulSoup(req.content, 'html.parser')
        ip = html.find_all(text=re.compile(u'本机IP:'))[0].split(':')[-1]
        print datetime.datetime.now(), ip
        status, info = commands.getstatusoutput("ssh root@conj.space 'cd /home/env; python update_ip.py %s'" % ip)
        if status != 0: raise Exception("更新远程IP信息失败")
    except Exception, e:
        print e
    time.sleep(3600)
