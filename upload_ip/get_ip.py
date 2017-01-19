# coding=utf-8
import requests
from bs4 import BeautifulSoup
import re
import commands
req = requests.get('http://m.baidu.com/s?word=ip')

html = BeautifulSoup(req.content, 'lxml')
ip = html.find_all(text=re.compile(u'本机IP:'))[0].split(':')[-1]
status, info = commands.getstatusoutput("ssh root@conj.space 'cd /home/env; python reload_nginx.py %s'" % ip)
print status, info
