# coding=utf-8
import ConfigParser
import json

cf = ConfigParser.ConfigParser()
cf.read('/home/suit/lab/spyder/config.ini')
DATABASE_URI = cf.get('autohome', 'sql_conn')
car_url = cf.get('autohome', 'car_url')
max_iter = int(cf.get('autohome', 'max_iter'))
brand_json = json.loads(cf.get('autohome', 'brand_json'))
