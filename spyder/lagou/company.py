# coding=utf-8
import sys
import requests
import json
import time
from datetime import datetime
from config import company_url, max_iter, city_json, stage_json, domain_json
from model import DBSession, Company

reload(sys)
sys.setdefaultencoding('utf-8')


def crawling(city_code_, stage_code_=0, domain_code_=0, page=0):
    if stage_code_ == 0 or domain_code_ == 0:
        print '[{}]\t开始抓取 {} 的公司'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), city_json[city_code_])
    else:
        print '[{}]\t开始抓取 {} {} 的 {} 公司'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), city_json[city_code_], stage_json[stage_code_], domain_json[domain_code_])
    param = {'first': 'false', 'pn': page, 'sortField': 0, 'havemark': 0}
    log = "[{}]\t抓取第 {} 页完毕, 当前页公司个数{}, 累计已抓{}, 该类别总计{}"
    count = 0
    for i in range(max_iter):
        param['pn'] += 1
        req = requests.post(
                company_url.format(
                        city_code=city_code_,
                        stage_code=stage_code_,
                        domain_code=domain_code_
                ),
                data=param
        )
        info = json.loads(req.content)
        total_count = int(info['totalCount'])
        company_list = info['result']
        count += len(company_list)
        print log.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), param['pn'],
                         len(company_list), count, total_count)
        session = DBSession()
        for company in company_list:
            c = Company(
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
        if len(company_list) == 0: break
    return count


def is_small_city(city_code_):
    param = {'first': 'false', 'pn': 0, 'sortField': 0, 'havemark': 0}
    req = requests.post(company_url.format(city_code=city_code_, stage_code=0, domain_code=0), data=param)
    total_count = int(json.loads(req.content)['totalCount'])
    time.sleep(3)
    if total_count < 900:
        print "[{}]\t{} 公司数为 {} < 900, 执行全批抓取".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), city_json[city_code_], total_count)
        return True
    else:
        print "[{}]\t{} 公司数为 {} >= 900, 执行分批抓取".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), city_json[city_code_], total_count)
        return False



if __name__ == '__main__':
    current_count = 0

    for city_code, city_name in city_json.items():
        if is_small_city(city_code):
            try:
                current_count += crawling(city_code)
            except requests.exceptions.ConnectionError:
                print 'lagou网拒绝连接，中场休息十分钟'
                time.sleep(600)
            print '[{}]\t抓取 {} 的公司完毕, 累计抓取{}'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), city_json[city_code], current_count)
            continue

        for stage_code, stage_name in stage_json.items():
            for domain_code, domain_name in domain_json.items():
                try:
                    current_count += crawling(city_code, stage_code, domain_code)
                except requests.exceptions.ConnectionError:
                    print 'lagou网拒绝连接，中场休息十分钟'
                    time.sleep(600)
                print '[{}]\t抓取 {} {} 的 {} 公司完毕, 累计抓取 {}'.format(
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        city_json[city_code],
                        stage_json[stage_code],
                        domain_json[domain_code],
                        current_count
                )

    print '抓取完毕'
