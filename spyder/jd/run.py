# coding=utf-8
import sys
import requests
import json
import time
from datetime import datetime
from config import url, max_iter
from model import DBSession, Ware

reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == '__main__':
    keyword = sys.argv[1]
    page = 0 if len(sys.argv) == 2 else sys.argv[2]
    param = {'_format_': 'json', 'stock': 1, 'page': page, 'keyword': keyword}
    log = "[{}]\t抓取 {} 第 {} 页完毕, 当前页商品个数{}, 总商品个数{}, 累计已抓{}"
    ware_count = 0
    for i in range(max_iter):
        session = DBSession()
        param['page'] += 1
        req = requests.post(url, data=param)
        info = json.loads(json.loads(req.content)['value'])
        ware_list = info['wareList']['wareList']
        total_count = info['wareList']['wareCount']
        ware_count += len(ware_list)
        print log.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), keyword, param['page'],
                         len(ware_list), total_count, ware_count)
        for ware in ware_list:
            w = Ware(
                key_word=keyword,
                ware_id=str(ware['wareId']),
                name=str(ware['wname']),
                price=str(ware['jdPrice']),
                diff_mobile_price=str(ware['diffMobilePrice']),
                is_self=str(ware['self']),
                shop_name=str(ware['shopName']),
                stock_state=str(ware['stockState']),
                available_in_store=str(ware['availableInStore']),
                pre_sale=str(ware['preSale']),
                total_count=str(ware['totalCount']),
                good=str(ware['good']),
                sams_tag=None,
                sams_price=None,
                eBook_flag=str(ware['eBookFlag']),
                can_free_read=str(ware['canFreeRead']),
                promotion_flag=None,
                m_promotion_id=str(ware['mPromotionId']),
                is_booking=str(ware['isBooking']),
                dis_price=None,
                cid1=None,
                cid2=None,
                cat_id=None,
                up_to_saving=str(ware['upToSaving']),
                eche=str(ware['eche']),
                author=str(ware['author']),
                priority=str(ware['priority']),
                international=str(ware['international']),
                stock_quantity=str(ware['stockQuantity']),
                adword=str(ware['adword']),
                lowest_buy=str(ware['lowestBuy']),
                create_time=datetime.now()
            )
            session.add(w)
        session.commit()
        session.close()
        if ware_count >= int(total_count): break
        time.sleep(3)
    print '抓取完毕'
