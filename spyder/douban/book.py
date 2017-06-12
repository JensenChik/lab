# coding=utf-8
import requests
from bs4 import BeautifulSoup
import random
import string
import sys
import os
import time
from datetime import date
import shutil
import multiprocessing

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from spyder.config import DBSession, HEADER, get_proxy
from spyder.config import book_tag_list as TAG_LIST
from spyder.config import return_none_when_exception, repeat_while_return_none
from spyder.model import DoubanBook


def get(tag):
    time.sleep(1)
    proxy = get_proxy()
    HEADER.update({"Cookie": "bid=%s" % "".join(random.sample(string.ascii_letters + string.digits, 11))})
    book_list = []
    for pos in range(0, 1000, 20):
        url = "https://book.douban.com/tag/{}?start={}&type=T".format(tag, pos)
        req = requests.get(url, proxies=proxy, headers=HEADER, timeout=5)
        if req.status_code != 200: raise Exception('error return code')
        html = BeautifulSoup(req.content, 'html.parser')
        book_list += html.find_all("li", class_='subject-item') or []
    print 'get {} by {} done'.format(tag, proxy.get('http'))
    time.sleep(4)
    fp = open('/tmp/{}_douban_book/{}'.format(date.today(), tag), 'w')
    map(lambda book: fp.writelines('{}\n'.format(book.prettify().replace('\n', ' '))), book_list)
    fp.close()
    return len(book_list)


if __name__ == '__main__':
    print 'start to clean env'
    path = '/tmp/{}_douban_book/'.format(date.today())
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)

    print 'start to get douban books data'
    pool = multiprocessing.Pool(processes=20)
    count = reduce(
        lambda x, y: x + y,
        pool.map(
            repeat_while_return_none(return_none_when_exception(get)),
            TAG_LIST
        )
    )
    pool.close()
    pool.join()
    print 'get douban books data finish, book count: {}'.format(count)

    print 'start to clean mysql dirty data'
    session = DBSession()
    session.query(DoubanBook).filter_by(create_date=date.today()).delete()
    session.commit()
    session.close()

    print 'start to dump douban book data to mysql'
    for tag in TAG_LIST:
        session = DBSession()
        fp = open('/tmp/{}_douban_book/{}'.format(date.today(), tag))
        data = [DoubanBook(tag=tag, html=line, create_date=date.today()) for line in fp]
        session.add_all(data)
        fp.close()
        print 'dump {} to mysql finish'.format(tag)
        session.commit()
        session.close()
    print 'dump douban book to mysql finish'
    
    print 'finally, clean env'
    shutil.rmtree(path)
    print 'all done'
