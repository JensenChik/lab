# coding=utf-8
import sys
import requests
import json
import time
from datetime import datetime
from config import job_url, max_iter 
from model import DBSession, Job

reload(sys)
sys.setdefaultencoding('utf-8')



def crawling(company_short_name):
    param = {'first': 'false', 'pn': 0, 'kd': ''}
    param = {'first': 'false', 'pn': page, 'sortField': 0, 'havemark': 0}
    log = "[{}]\t抓取第 {} 页完毕, 当前页职位个数{}, 累计已抓{}, 该公司总计{}"
    count = 0
    for i in range(max_iter):
        param['pn'] += 1
        req = requests.post(job_url, data=param)
        info = json.loads(req.content)
        total_count = int(info['content']['positionResult']['totalCount'])
        job_list = info['content']['positionResult']['result']
        count += len(job_list)
        print log.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), param['pn'],
                         len(job_list), count, total_count)
        session = DBSession()
        for job in job_list:
            c = Job(
                    company_id=company.get("companyId"),
                    company_full_name=company.get("companyFullName"),
                    company_short_name=company.get("companyShortName"),
                    city=company.get("city"),
                    position_num=company.get("positionNum"),
                    city_score=company.get("cityScore"),
                    finance_stage=company.get("financeStage"),
                    industry_field=company.get("industryField"),
                    country_score=company.get("countryScore"),
                    company_features=company.get("companyFeatures"),
                    process_rate=company.get("processRate"),
                    interview_remark_num=company.get("interviewRemarkNum"),
                    approve=company.get("approve"),
                    create_time=datetime.now()
            )
            session.add(c)
        session.commit()
        session.close()
        time.sleep(3)
        if len(job_list) == 0: break
    return count


if __name__ == '__main__':
    current_count = 0
    company_list = []
    for company in company_list:
        try:
            current_count += crawling(city_code, stage_code, domain_code)
        except requests.exceptions.ConnectionError:
            print 'lagou网拒绝连接，中场休息十分钟'
            time.sleep(600)
        print '[{}]\t抓取 {} 公司完毕, 累计抓取 {}'.format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            city_json[city_code],
            stage_json[stage_code],
            domain_json[domain_code],
            current_count
        )

    print '抓取完毕'
