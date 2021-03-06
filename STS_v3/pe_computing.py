
#  -*- coding: utf-8 -*-

"""
compute_pe：计算市盈率
"""

from pymongo import ASCENDING, DESCENDING, UpdateOne

from database import DB_CONN
#from stock_util import get_all_codes
import tushare as ts

finance_report_collection = DB_CONN['finance_report']
daily_collection = DB_CONN['daily']


def compute_pe():
    """
    计算股票在某只的市盈率
    """

    # 获取所有股票
    codes = ts.get_stock_basics().index.tolist() # get_all_codes()
    total = len(codes)
    err_code = []
    for i,code in enumerate(codes):
        print('计算市盈率, %s' % code)
        daily_cursor = daily_collection.find(
            {'code': code},
            projection={'close': True, 'date': True})

        update_requests = []
        for daily in daily_cursor:
            try:
                _date = daily['date']
            except:
                print('code: %s has no data' % code)
                err_code.append(code)
                continue

            finance_report = finance_report_collection.find_one(
                {'code': code, 'report_date': {'$regex': '\d{4}-12-31'}, 'announced_date': {'$lte': _date}},
                sort=[('announced_date', DESCENDING)]
            )

            if finance_report is None:
                continue

            # 计算滚动市盈率并保存到daily_k中
            eps = 0
            if finance_report['eps'] != '-':
                eps = finance_report['eps']

            # 计算PE
            if eps != 0:
                update_requests.append(UpdateOne(
                    {'code': code, 'date': _date},
                    {'$set': {'pe': round(daily['close'] / eps, 4)}}))

        if len(update_requests) > 0:
            update_result = daily_collection.bulk_write(update_requests, ordered=False)
            print('pe计算进度: (%s/%s)%s, 更新：%d' % (i+1, total, code, update_result.modified_count))
    print(err_code)

if __name__ == "__main__":
#    col_list = DB_CONN.list_collection_names()
#    if 'finance_report' not in col_list:
    finance_report_col = DB_CONN['finance_report']
    if 'code_1_report_date_1_announced_date_1' not in finance_report_col.index_information().keys():
        DB_CONN['finance_report'].create_index(
            [('code',ASCENDING), ('report_date',ASCENDING), ('announced_date',ASCENDING)])    

    compute_pe()
