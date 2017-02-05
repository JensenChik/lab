# coding=utf-8
from model import IP
import requests
from random import choice
from config import PAGE_NUM, POOL_SIZE, HEART_BEAT, DBSession
import time
from datetime import datetime
from bs4 import BeautifulSoup
import json
from multiprocessing.dummy import Pool as ThreadPool
import logging


class Producer:
    # 更新ip池
    def __init__(self):
        self.begin_time = datetime.now()
        logging.basicConfig(
            level=logging.WARNING,
            format='[%(levelname)s]\t%(asctime)s\t%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger()

    def _update_ip_pool(self, session):
        # 抓取第i页的IP
        def get(i):
            valid_ip = session.query(IP).filter(IP.rank != None).order_by(IP.rank).limit(PAGE_NUM * 3).all()
            proxies = None if valid_ip == [] else choice(valid_ip).to_proxy()
            try:
                headers = requests.utils.default_headers()
                headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'})
                req = requests.get('http://www.xicidaili.com/nn/{}'.format(i), proxies=proxies, timeout=5,
                                   headers=headers)
            except Exception:
                req = None
            time.sleep(3)
            return None if req is None or req.status_code != 200 else req.content

        run_count = 0
        self.logger.warning('ip池供应不足，开始更新ip池')
        for page in range(1, PAGE_NUM):
            run_count += 1
            content = get(page)
            while content is None:
                content = get(page)
            html = BeautifulSoup(content, 'html.parser')
            for tr in html.find_all('tr'):
                td = tr.find_all('td')
                if not td or td[5].text != 'HTTP': continue
                url = "http://{}:{}".format(td[1].text, td[2].text)
                ip = IP(url=url, create_time=datetime.now())
                if session.query(IP).filter_by(url=url).first() is None:
                    session.add(ip)
            session.commit()
            if run_count > 100:
                break

    # 将ip按响应时间排序，并返回当前可用的ip数量
    def _check_and_rank_ip(self, session):
        def ping_jd(ip):
            t = time.time()
            try:
                respond = requests.post('http://so.m.jd.com/ware/searchList.action',
                                        data={'_format_': 'json', 'stock': 1, 'page': 1, 'keyword': '手机'},
                                        proxies=ip.to_proxy(), timeout=5).content
                json.loads(respond)
                ip.rank = int(100 * (time.time() - t))
            except Exception:
                ip.rank = None
            return ip

        self.logger.warning('开始判断ip活性')
        all_ip = session.query(IP).all()
        pool = ThreadPool(100)
        ips = pool.map(ping_jd, all_ip)
        for ip in ips:
            session.add(ip)
        session.query(IP).filter(IP.rank == None).delete()
        session.commit()
        pool.close()
        pool.join()
        return session.query(IP).count()

    def serve(self):
        self.logger.warning('开始服务')
        while (datetime.now() - self.begin_time).days == 0:
            session = DBSession()
            valid_ip_count = self._check_and_rank_ip(session)
            self.logger.warning('当前可用ip数量为: {}'.format(valid_ip_count))
            if valid_ip_count < POOL_SIZE:
                self._update_ip_pool(session)
            session.close()
            time.sleep(HEART_BEAT)
        self.logger.warning('服务完毕')


if __name__ == '__main__':
    producer = Producer()
    producer.serve()
