# coding=utf-8
import sys
import requests
import json
import time
from datetime import datetime
import os
import multiprocessing

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from spyder.config import DBSession, JD_max_iter, JD_url, logger, HEADER, get_proxy
from spyder.config import return_none_when_exception, repeat_while_return_none
from spyder.model import JDWare as Ware


def get(param):
    time.sleep(1)
    page, keyword = param
    param = {'_format_': 'json', 'stock': 1, 'page': page, 'keyword': keyword}
    proxy = get_proxy()
    req = requests.post(JD_url, data=param, proxies=proxy, headers=HEADER, timeout=5)
    if req.status_code != 200: raise Exception('error return code')
    info = json.loads(json.loads(req.content).get('value'))
    print 'get ware {} in page {} by {} done'.format(keyword, page, proxy.get('http'))
    time.sleep(4)
    return [Ware(key_word=keyword, json=json.dumps(ware, ensure_ascii=False), create_date=datetime.date(datetime.now()))
            for ware in info.get('wareList').get('wareList') or []]


def check_ware_count(keyword):
    param = {'_format_': 'json', 'stock': 1, 'page': 1, 'keyword': keyword}
    return json.loads(
        json.loads(
            requests.post(JD_url, data=param, headers=HEADER, timeout=5).content
        ).get('value')
    ).get('wareList').get('wareCount')


if __name__ == '__main__':
    keyword = sys.argv[1]
    batch_size = 25
    ware_list = []
    ware_count = check_ware_count(keyword)
    print 'start to get {} wares from JD'.format(ware_count)
    for batch in range(JD_max_iter / batch_size):
        pool = multiprocessing.Pool(processes=batch_size)
        ware_list += reduce(
            lambda x, y: x + y,
            pool.map(
                repeat_while_return_none(return_none_when_exception(get)),
                zip(range(batch * batch_size, (batch + 1) * batch_size), [keyword] * batch_size)
            )
        )
        pool.close()
        pool.join()
        print 'batch {} finish, acc ware count:{}'.format(batch, len(ware_list))
        if len(ware_list) > ware_count: break
    print 'get ware from JD finish'

    print 'start to dump ware to mysql'
    session = DBSession()
    session.add_all(ware_list)
    session.commit()
    session.close()
    print 'dump ware to mysql finish'

    print 'all done'
