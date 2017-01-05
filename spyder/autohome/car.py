# coding=utf-8
import sys
import requests
import json
import time
from datetime import datetime
from config import car_url, max_iter, brand_json
from model import DBSession, Car

reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == '__main__':
    current_count = 0
    
    for brand_code, brand_name in brand_json.items():
        info = json.loads(requests.get(url, params={'b': brand_code}).content)
        all_sell_series = info['result']['allSellSeries']
        for series in all_sell_series:
            series_name = series['name']
            for item in series['SeriesItems']:
                card_name = item['name']
                min_price = item['minprice']
                max_price = item['maxprice']
                row = record.format(brand=brand_name, series=series_name, name=card_name, min_price=min_price,
                                    max_price=max_price)
                print row.strip()
        time.sleep(3)
