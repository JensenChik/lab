# coding=utf-8
import sys
import requests
import json
import time
from datetime import datetime
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from spyder.config import DBSession, logger, ip_pool, User_Agent
from spyder.config import lagou_company_url, lagou_max_iter, lagou_city_json, lagou_stage_json, lagou_domain_json
from spyder.model import LagouCompany as Company

cookie = requests.utils.dict_from_cookiejar(requests.get('http://m.lagou.com/').cookies)
cookie.update({'LGUID': 'NULL'})
cookie = ';'.join(['{}={}'.format(k, v) for k, v in cookie.items()])
headers = requests.utils.default_headers()
headers.update({'User-Agent': User_Agent, 'Cookie': cookie})


def get(page, city=0, stage=0, domain=0):
    param = {'first': 'false', 'pn': page, 'sortField': 0, 'havemark': 0}
    try:
        r = requests.post(lagou_company_url.format(city_code=city, stage_code=stage, domain_code=domain),
                          proxies=ip_pool.gen_proxies(), data=param, headers=headers, timeout=5)
        respond = json.loads(r.content) if r.status_code == 200 else None
    except Exception:
        respond = None
    time.sleep(1)
    return respond


def is_small_city(city):
    respond = get(page=0, city=city)
    while respond is None:
        respond = get(page=0, city=city)
    company_count = int(respond['totalCount'])
    if company_count < 900:
        logger.warning('{} 公司数为 {} < 900, 执行全批抓取'.format(lagou_city_json[city_code], company_count))
        return True
    else:
        logger.warning('{} 公司数为 {} > 900, 执行分批抓取'.format(lagou_city_json[city_code], company_count))
        return False


def dump(city, stage=0, domain=0):
    if stage == 0 or domain == 0:
        logger.warning('开始抓取 {} 的公司'.format(lagou_city_json[city]))
    else:
        logger.warning('开始抓取 {} {} 的 {} 公司'.format(
            lagou_city_json[city],
            lagou_stage_json[stage],
            lagou_domain_json[domain]
        ))
    log = "抓取第 {} 页完毕, 当前页公司个数{}, 累计已抓{}, 该类别总计{}"
    count = 0
    page = 0
    for i in range(lagou_max_iter):
        page += 1
        info = get(page=page, city=city, stage=stage, domain=domain)
        while info is None:
            info = get(page=page, city=city, stage=stage, domain=domain)
        total_count = int(info['totalCount'])
        company_list = info['result']
        count += len(company_list)
        logger.warning(log.format(page, len(company_list), count, total_count))
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
        if len(company_list) == 0:
            break
    return count


if __name__ == '__main__':
    current_count = 0
    logger.warning('开始抓取')
    for city_code, city_name in lagou_city_json.items():
        if is_small_city(city_code):
            current_count += dump(city_code)
            logger.warning('抓取 {} 的公司完毕, 累计抓取{}'.format(lagou_city_json[city_code], current_count))
            continue

        for stage_code, stage_name in lagou_stage_json.items():
            for domain_code, domain_name in lagou_domain_json.items():
                current_count += dump(city=city_code, stage=stage_code, domain=domain_code)
                logger.warning('抓取 {} {} 的 {} 公司完毕, 累计抓取 {}'.format(
                    lagou_city_json[city_code],
                    lagou_stage_json[stage_code],
                    lagou_domain_json[domain_code],
                    current_count
                ))

    logger.warning('抓取完毕')
