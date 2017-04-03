# coding=utf-8
import re

import requests
import json
import time

from bs4 import BeautifulSoup


class Source:
    def __init__(self):
        self._headers = requests.utils.default_headers()
        self._headers.update({
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8',
        })
        self._pool_url = None

    def get(self):
        pass

    def request(self, url):
        # proxy = requests.get(self._pool_url)
        # proxy = json.loads(proxy) if proxy != 'None' else None
        proxy = None
        try:
            req = requests.get(url, headers=self._headers, proxies=proxy, timeout=5)
        except Exception:
            req = None
        time.sleep(3)
        return None if req is None or req.status_code != 200 else req.content


class XiCi(Source):
    def __init__(self):
        Source.__init__(self)
        self.url = 'http://www.xicidaili.com/{}/{}'

    def get(self):
        url = []
        for style in ['nn', 'nt', 'wt']:
            for page in range(1, 11):
                content = self.request(self.url.format(style, page))
                while content is None:
                    content = self.request(self.url.format(style, page))
                html = BeautifulSoup(content, 'html.parser')
                for tr in html.find_all('tr'):
                    td = tr.find_all('td')
                    if not td or td[5].text != 'HTTP': continue
                    url.append("http://{}:{}".format(td[1].text, td[2].text))
            return url


class SixSix(Source):
    def __init__(self):
        Source.__init__(self)
        self.url = "http://www.66ip.cn/{}.html"

    def get(self):
        url = []
        for page in range(2, 12):
            content = self.request(self.url.format(page))
            while content is None:
                content = self.request(self.url.format(page))
            html = BeautifulSoup(content, 'html.parser')
            table = html.find_all('table')[2]
            for tr in table.find_all('tr'):
                td = tr.find_all('td')
                if not td or td[0].text == 'ip': continue
                url.append("http://{}:{}".format(td[0].text, td[1].text))
        return url


class QuanMin(Source):
    def __init__(self):
        Source.__init__(self)
        self.url = "http://www.goubanjia.com/index{}.shtml"

    def _decrypt(self, src):
        if src is None: return None
        s = 'ABCDEFGHIZ'
        dst = ''
        for c in src:
            dst += str(s.find(c))
        dst = int(dst) >> 3
        return dst

    def get(self):
        url = []
        for i in range(1, 11):
            content = self.request(self.url.format(i))
            while content is None:
                content = self.request(self.url.format(i))
            html = BeautifulSoup(content, 'html.parser')
            # print html.prettify()
            for tr in html.find_all('tr'):
                td = tr.find_all('td')
                if not td or td == []: continue
                ip = ''
                for i in td[0].find_all(True, style=re.compile("^display")):
                    ip += i.text
                port = self._decrypt(td[0].find_all(True, class_=re.compile("^port"))[0]['class'][1])
                if port is None or port == 80: continue
                url.append("http://{}:{}".format(ip, port))
        return url


# 需要图像识别
# class MiPu(Source):
#     def __init__(self):
#         Source.__init__(self)
#         self.url = "http://proxy.mimvp.com/free.php?proxy={}"
#
#     def get(self):
#         url = []
#         for i in ['in_tp']:
#             content = self.request(self.url.format(i))
#             while content is None:
#                 content = self.request(self.url.format(i))
#             html = BeautifulSoup(content, 'html.parser')
#             print html.prettify()
#             table = html.find_all('tbody')[0]
#             for i in html.find_all('td'):
#                 print i.text
#             for tr in table.find_all('tr'):
#                 td = tr.find_all('td')
#                 if not td or td[0].text == 'ip': continue
#                 url.append("http://{}:{}".format(td[0].text, td[1].text))
#         return url

# 需要抓取网页
# class YouDaiLi(Source):
#     def __init__(self):
#         Source.__init__(self)
#         self.url = "http://www.youdaili.net/Daili/guonei/36714.html"
#
#     def get(self):
#         pass


class CooBoBo(Source):
    def __init__(self):
        Source.__init__(self)
        self.url = "http://www.coobobo.com/free-http-proxy/{}"

    def get(self):
        url = []
        for page in range(1, 11):
            content = self.request(self.url.format(page))
            while content is None:
                content = self.request(self.url.format(page))
            html = BeautifulSoup(content, 'html.parser')
            table = html.find_all('tbody')[0]
            for tr in table.find_all('tr'):
                td = tr.find_all('td')
                if not td or td[1].text == '80': continue
                url.append("http://{}:{}".format(td[0].text, td[1].text))
        return url


class YunDaiLi(Source):
    def __init__(self):
        Source.__init__(self)
        self.url = "http://www.ip3366.net/?stype={}&page={}"

    def get(self):
        url = []
        for style in range(1, 5):
            for page in range(1, 8):
                content = self.request(self.url.format(style, page))
                while content is None:
                    content = self.request(self.url.format(style, page))
                html = BeautifulSoup(content, 'html.parser')
                table = html.find_all('tbody')[0]
                for tr in table.find_all('tr'):
                    td = tr.find_all('td')
                    if not td or td[1].text == '80' or td[3] == 'HTTPS': continue
                    url.append("http://{}:{}".format(td[0].text, td[1].text))
        return url


class YunHai(Source):
    def __init__(self):
        Source.__init__(self)
        self.url = "http://www.kxdaili.com/dailiip/{}/{}.html"

    def get(self):
        url = []
        for style in range(1, 5):
            for page in range(1, 11):
                content = self.request(self.url.format(style, page))
                while content is None:
                    content = self.request(self.url.format(style, page))
                html = BeautifulSoup(content, 'html.parser')
                table = html.find_all('tbody')[0]
                for tr in table.find_all('tr'):
                    td = tr.find_all('td')
                    if not td or td[1].text == '80': continue
                    url.append("http://{}:{}".format(td[0].text, td[1].text))
        return url


class Data5U(Source):
    def __init__(self):
        Source.__init__(self)
        self.url = "http://www.data5u.com/free/{}/index.shtml"

    def _decrypt(self, src):
        if src is None: return None
        s = 'ABCDEFGHIZ'
        dst = ''
        for c in src:
            dst += str(s.find(c))
        dst = int(dst) >> 3
        return dst

    def get(self):
        url = []
        for style in ['gngn', 'gnpt', 'gwgn', 'gwpt']:
            content = self.request(self.url.format(style))
            while content is None:
                content = self.request(self.url.format(style))
            html = BeautifulSoup(content, 'html.parser')
            table = html.find_all('ul', class_='l2')
            for row in table:
                cell = row.find_all('li')
                if not cell: continue
                port = self._decrypt(cell[1]['class'][1])
                if port is None or port == 80: continue
                url.append("http://{}:{}".format(cell[0].text, port))
        return url
