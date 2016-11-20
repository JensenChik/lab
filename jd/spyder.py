# coding=utf-8
import requests
import json
import time
from datetime import datetime
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

url = 'http://so.m.jd.com/ware/searchList.action'

if __name__ == '__main__':
    keyword = sys.argv[1]
    page = 0 if len(sys.argv) == 2 else sys.argv[2]
    param = {'_format_': 'json', 'stock': 1, 'page': page, 'keyword': keyword}
    file_name = '{}_{}.json'.format(datetime.now().strftime('%Y%m%d'), keyword)
    ware_count = 0
    for i in range(1000):
        param['page'] += 1
        req = requests.post(url, data=param)
        info = json.loads(json.loads(req.content)['value'])
        ware_count += len(info['wareList'])
        print datetime.now(), '抓取', keyword, '第', param['page'], '页完毕, 当前页物品个数为', len(info['wareList']), \
            ', 总商品数', info['wareCount'], ', 累计已抓取', ware_count
        with open(file_name, 'a') as fp:
            json.dump(info, fp)
            fp.writelines('\n')
        if ware_count >= int(info['wareCount']):break
        time.sleep(3)



