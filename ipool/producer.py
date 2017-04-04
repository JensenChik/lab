# coding=utf-8
from source import XiCi, SixSix, QuanMin, CooBoBo, YunDaiLi, YunHai, Data5U
from model import IP
from config import DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import multiprocessing
import time
import requests
import json


def get(source):
    return source.get()


def ping(url):
    ip = IP(url=url, update_time=datetime.now())
    begin_time = time.time()
    try:
        respond = requests.post(
            url='https://so.m.jd.com/ware/searchList.action',
            data={'_format_': 'json', 'stock': 1, 'page': 1, 'keyword': '手机'},
            proxies=ip.to_proxy(),
            timeout=5
        ).content
        json.loads(respond)
        ip.speed = int(100 * (time.time() - begin_time))
    except Exception:
        ip = None
    return ip


class Producer:
    def __init__(self):
        self._source = [
            SixSix(), QuanMin(), CooBoBo(), Data5U(),
            XiCi(style='nt'), XiCi(style='nn'), XiCi(style='wt'),
            YunDaiLi(style=1), YunDaiLi(style=2), YunDaiLi(style=3), YunDaiLi(style=4),
            YunHai(style=1), YunHai(style=2), YunHai(style=3), YunHai(style=4),
        ]
        self._heart_beat = 600

    def _dump(self):
        print 'start to get ip from source'
        thread_pool = multiprocessing.Pool(15)
        proxy_url = reduce(lambda x, y: x + y, thread_pool.map(get, self._source))
        thread_pool.close()
        thread_pool.join()
        print 'get ip from source finish, ip count:', len(proxy_url)

        print 'start to ping JD'
        thread_pool = multiprocessing.Pool(200)
        ip_list = thread_pool.map(ping, proxy_url)
        thread_pool.close()
        thread_pool.join()
        print 'ping JD finish, valid ip count:', len(filter(lambda x: x is not None, ip_list))

        print 'start to dump ip to mysql'

        engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
        DBSession = sessionmaker(engine)
        session = DBSession()
        session.query(IP).delete()
        for ip in filter(lambda x: x is not None, ip_list):
            ip_in_db = session.query(IP).filter_by(url=ip.url).first()
            if not ip_in_db:
                session.add(ip)
        session.commit()
        session.close()
        print 'dump ip to mysql finish'

    def serve(self):
        while True:
            self._dump()
            time.sleep(self._heart_beat)


if __name__ == '__main__':
    producer = Producer()
    producer.serve()
