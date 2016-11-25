# coding=utf-8
import ConfigParser

cf = ConfigParser.ConfigParser()
cf.read('/home/suit/lab/spyder/config.ini')
DATABASE_URI = cf.get('lagou', 'sql_conn')
company_url = cf.get('lagou', 'company_url')
max_iter = int(cf.get('lagou', 'max_iter'))

