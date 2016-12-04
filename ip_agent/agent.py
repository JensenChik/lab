# coding=utf-8
import requests
from bs4 import BeautifulSoup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ConfigParser
import sys
from datetime import datetime
import time
import json

cf = ConfigParser.ConfigParser()
cf.read('config.ini')
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
        return {self.url.split(':')[0]: self.url}


def update_ip_pool(session):
    print 'ip池供应不足，开始更新ip池'
    for page in range(PAGE_NUM):
        print '抓取第{}页'.format(page)
        content = requests.get('http://ip84.com/dlgn/{}'.format(page + 1)).content
        html = BeautifulSoup(content, 'lxml')
        for tr in html.find_all('tr'):
            td = tr.find_all('td')
            if not td: continue
            url = "{}://{}:{}".format(td[4].text.lower(), td[0].text, td[1].text)
            ip = IP(url=url, create_time=datetime.now())
            if session.query(IP).filter_by(url=ip).first() is None:
                session.add(ip)
        session.commit()
        time.sleep(3)


def check_and_rank_ip(session):
    valid_ip = []
    all_ip = session.query(IP).all()
    for ip in all_ip:
        t = time.time()
        try:
            print ip.to_proxy(),
            respond = requests.post('http://so.m.jd.com/ware/searchList.action',
                                    data={'_format_': 'json', 'stock': 1, 'page': 1, 'keyword': '手机'},
                                    proxies=ip.to_proxy(), timeout=5).content
            json.loads(respond)
            print respond[:50]
            ip.rank = int(100 * (time.time() - t))
            valid_ip.append(ip)
        except Exception, e:
            print type(e)
            session.delete(ip)
        session.commit()
    return len(valid_ip)


def serve():
    while True:
        session = DBSession()
        valid_ip_count = check_and_rank_ip(session)
        if valid_ip_count < POOL_SIZE:
            update_ip_pool(session)
        session.close()
        time.sleep(HEART_BEAT)


if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'initdb':
        BaseModel.metadata.create_all(engine)
    elif action == 'serve':
        serve()
