# coding=utf-8
import sys
import requests
import json
import time
from datetime import datetime
from config import company_url, max_iter
from model import DBSession, Company

reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == '__main__':
    page = 0 if len(sys.argv) == 1 else sys.argv[1]
    param = {'first': 'false', 'pn': page, 'sortField': 0, 'havemark': 0}
    log = "[{}]\t抓取第 {} 页完毕, 当前页公司个数{}, 累计已抓{}"
    current_count = 0
    for i in range(max_iter):
        param['pn'] += 1
        req = requests.post(company_url, data=param)
        info = json.loads(req.content)
        company_list = info['result']
        current_count += len(company_list)

        print log.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), param['pn'],
                         len(company_list), current_count)
        session = DBSession()

        for company in company_list:
            c = Company(
                company_id=company["companyId"],
                company_full_name=company["companyFullName"],
                company_short_name=company["companyShortName"],
                city=company["city"],
                position_num=company["positionNum"],
                city_score=company["cityScore"],
                finance_stage=company["financeStage"],
                industry_field=company["industryField"],
                country_score=company["countryScore"],
                company_features=company["companyFeatures"],
                process_rate=company["processRate"],
                interview_remark_num=company["interviewRemarkNum"],
                approve=company["approve"],
                create_time=datetime.now()
            )
            session.add(c)
        session.commit()
        session.close()
        if len(company_list) == 0: break
        time.sleep(3)
    print '抓取完毕'
