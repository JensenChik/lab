# coding=utf-8
import ConfigParser
import json

cf = ConfigParser.ConfigParser()
cf.read('/home/suit/lab/spyder/config.ini')
DATABASE_URI = cf.get('lagou', 'sql_conn')
company_url = cf.get('lagou', 'company_url')
max_iter = int(cf.get('lagou', 'max_iter'))
city_json = json.loads(cf.get('lagou', 'city_json'))
stage_json = json.loads(cf.get('lagou', 'stage_json'))
domain_json = json.loads(cf.get('lagou', 'domain_json'))
