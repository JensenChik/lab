# coding=utf-8
import requests
from bs4 import BeautifulSoup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ConfigParser
import sys
import os
from datetime import datetime
import time
import json
from random import choice
import datetime

cf = ConfigParser.ConfigParser()
cf.read(os.path.join(sys.path[0], 'config.ini'))
DATABASE_URI = cf.get('param', 'sql_conn')
HEART_BEAT = int(cf.get('param', 'heart_beat'))
POOL_SIZE = int(cf.get('param', 'pool_size'))
PAGE_NUM = int(cf.get('param', 'page_num'))
BaseModel = declarative_base()
engine = create_engine(DATABASE_URI, pool_recycle=3600, encoding='utf-8')
DBSession = sessionmaker(engine)


class IP(BaseModel):
    __tablename__ = 'ip'
    id = Column(Integer, primary_key=True)
    url = Column(String(35), unique=True)
    create_time = Column(DateTime)
    rank = Column(Integer)

    def to_proxy(self):
        return {'http': self.url}


# 更新ip池
def update_ip_pool(session):
    # 抓取第i页的IP
    def get(i):
        valid_ip = session.query(IP).filter(IP.rank != None).order_by(IP.rank).limit(PAGE_NUM*3).all()
        proxies = None if valid_ip == [] else choice(valid_ip).to_proxy()
        # print '使用代理{}抓取第{}页'.format(proxies, i)
        try:
            headers = requests.utils.default_headers()
            headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'})
            req = requests.get('http://www.xicidaili.com/nn/{}'.format(i), proxies=proxies, timeout=5, headers=headers)
        except Exception:
            req = None
        time.sleep(3)
        return None if req is None or req.status_code != 200 or req.content == 'block' else req.content

    run_count = 0
    print datetime.datetime.now(), 'ip池供应不足，开始更新ip池'
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
        if run_count > 100: break


# 将ip按响应时间排序，并返回当前可用的ip数量
def check_and_rank_ip(session):
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

    print datetime.datetime.now(), '开始判断ip活性'
    from multiprocessing.dummy import Pool as ThreadPool
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


def serve():
    current_time = datetime.datetime.now()
    while current_time.hour != 23 and current_time.minute != 59:
        session = DBSession()
        valid_ip_count = check_and_rank_ip(session)
        print datetime.datetime.now(), '当前可用ip数量为:', valid_ip_count
        if valid_ip_count < POOL_SIZE:
            update_ip_pool(session)
        session.close()
        time.sleep(HEART_BEAT)
        current_time = datetime.datetime.now()


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'initdb':
        BaseModel.metadata.create_all(engine)
    elif action == 'serve':
        try:
            serve()
        except Exception, e:
            print e
