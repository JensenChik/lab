# coding=utf-8
import re
import requests
import time
from bs4 import BeautifulSoup
from config import DBSession, return_none_when_exception, repeat_while_return_none
from model import IP
from random import choice


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

    def get(self):
        pass

    @repeat_while_return_none
    @return_none_when_exception
    def request(self, url):
        session = DBSession()
        valid_ip = session.query(IP).all()
        proxy = None if valid_ip == [] else choice(valid_ip).to_proxy()
        session.close()
        req = requests.get(url, headers=self._headers, proxies=proxy, timeout=5)
        if req.status_code != 200: raise Exception('error return code')
        print 'request', url, 'by', proxy, 'success'
        time.sleep(3)
        return req.content


class XiCi(Source):
    def __init__(self, style, style_tips=['nt', 'nn', 'wt']):
        Source.__init__(self)
        self.url = 'http://www.xicidaili.com/{style}/{page}'.format(style=style, page='{page}')

    @return_none_when_exception
    def _extract(self, html):
        url = []
        for tr in html.find_all('tr'):
            td = tr.find_all('td')
            if not td or td[5].text != 'HTTP': continue
            url.append("http://{}:{}".format(td[1].text, td[2].text))
        return url

    def get(self):
        url = []
        for page in range(1, 11):
            content = self.request(self.url.format(page=page))
            html = BeautifulSoup(content, 'html.parser')
            url += self._extract(html) or []
        return url


class SixSix(Source):
    def __init__(self):
        Source.__init__(self)
        self.url = "http://www.66ip.cn/{}.html"

    @return_none_when_exception
    def _extract(self, html):
        url = []
        table = html.find_all('table')[2]
        for tr in table.find_all('tr'):
            td = tr.find_all('td')
            if not td or td[0].text == 'ip': continue
            url.append("http://{}:{}".format(td[0].text, td[1].text))
        return url

    def get(self):
        url = []
        for page in range(2, 12):
            content = self.request(self.url.format(page))
            html = BeautifulSoup(content, 'html.parser')
            url += self._extract(html) or []
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

    @return_none_when_exception
    def _extract(self, html):
        url = []
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

    def get(self):
        url = []
        for i in range(1, 11):
            content = self.request(self.url.format(i))
            html = BeautifulSoup(content, 'html.parser')
            url += self._extract(html) or []
        return url


# todo: 需要图像识别
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

# todo: 需要抓取网页
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

    @return_none_when_exception
    def _extract(self, html):
        url = []
        table = html.find_all('tbody')[0]
        for tr in table.find_all('tr'):
            td = tr.find_all('td')
            if not td: continue
            url.append("http://{}:{}".format(td[0].text, td[1].text))
        return url

    def get(self):
        url = []
        for page in range(1, 11):
            content = self.request(self.url.format(page))
            html = BeautifulSoup(content, 'html.parser')
            url += self._extract(html) or []
        return url


class YunDaiLi(Source):
    def __init__(self, style, style_tips=[1, 2, 3, 4]):
        Source.__init__(self)
        self.url = "http://www.ip3366.net/?stype={style}&page={page}".format(style=style, page="{page}")

    @return_none_when_exception
    def _extract(self, html):
        url = []
        table = html.find_all('tbody')[0]
        for tr in table.find_all('tr'):
            td = tr.find_all('td')
            if not td or td[3] == 'HTTPS': continue
            url.append("http://{}:{}".format(td[0].text, td[1].text))
        return url

    def get(self):
        url = []
        for page in range(1, 8):
            content = self.request(self.url.format(page=page))
            html = BeautifulSoup(content, 'html.parser')
            url += self._extract(html) or []
        return url


class YunHai(Source):
    def __init__(self, style, style_tips=[1, 2, 3, 4]):
        Source.__init__(self)
        self.url = "http://www.kxdaili.com/dailiip/{style}/{page}.html".format(style=style, page='{page}')

    @return_none_when_exception
    def _extract(self, html):
        url = []
        table = html.find_all('tbody')[0]
        for tr in table.find_all('tr'):
            td = tr.find_all('td')
            if not td: continue
            url.append("http://{}:{}".format(td[0].text, td[1].text))
        return url

    def get(self):
        url = []
        for page in range(1, 11):
            content = self.request(self.url.format(page=page))
            html = BeautifulSoup(content, 'html.parser')
            url += self._extract(html) or []
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

    @return_none_when_exception
    def _extract(self, html):
        url = []
        table = html.find_all('ul', class_='l2')
        for row in table:
            cell = row.find_all('li')
            if not cell: continue
            port = self._decrypt(cell[1]['class'][1])
            if port is None: continue
            url.append("http://{}:{}".format(cell[0].text, port))
        return url

    def get(self):
        url = []
        for style in ['gngn', 'gnpt', 'gwgn', 'gwpt']:
            content = self.request(self.url.format(style))
            html = BeautifulSoup(content, 'html.parser')
            url += self._extract(html) or []
        return url
