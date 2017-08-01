from spyder.config import DBSession, HEADER, get_proxy, wow_url
from spyder.config import return_none_when_exception, repeat_while_return_none
from spyder.model import AuctionWare

import requests
from bs4 import BeautifulSoup
import json
from collections import OrderedDict
import time


def get(location):
    city, realm = location.split('.')
    for pn in range(100):
        time.sleep(1)
        url = "https://{city}.lianjia.com/zufang/{realm}/pg{pn}/".format(city=city, realm=realm, pn=pn)
        proxy = get_proxy()
        req = requests.get(url, proxies=proxy, headers=HEADER, timeout=5)
        if req.status_code != 200: raise Exception('error return code')

        html = BeautifulSoup(req.content, 'html.parser')
        house_list = html.find_all(id='house-lst')[0].find_all('li')
        for house in house_list:
            title = house.find_all('a', title=True)[0].text.strip()
            region = house.find_all('span', class_="region")[0].text.strip()
            zone = house.find_all('span', class_="zone")[0].text.strip()
            meters = house.find_all('span', class_="meters")[0].text.strip()
            area, floor, build = house.find_all('div', class_="other")[0].text.split('/')

            tags = house.find_all('div', class_="chanquan")[0].find_all('span')
            tag_list = ','.join(set(tag.text for tag in tags if tag.text.strip() != ''))
            price = house.find_all('div', class_="price")[0].text.strip()
            update = house.find_all('div', class_="price-pre")[0].text.strip()
            square = house.find_all('div', class_="square")[0].text.strip()

            info = json.dumps(OrderedDict([
                ('area', area),
                ('region', region),
                ('title', title),
                ('zone', zone),
                ('meters', meters),
                ('floor', floor),
                ('build', build),
                ('price', price),
                ('view', square),
                ('tags', tag_list),
                ('last_modify', update)
            ]), ensure_ascii=False)

        auctions = json.loads(req.content).get('auctions') or []
        print 'get {} data by {} done'.format(realm, proxy.get('http'))
    time.sleep(4)
    fp = open('/tmp/{}_wow_auction_house/{}'.format(date.today(), realm), 'w')
    map(lambda ware: fp.writelines('{}\n'.format(json.dumps(ware, ensure_ascii=False))), auctions)
    fp.close()
    return len(auctions)

