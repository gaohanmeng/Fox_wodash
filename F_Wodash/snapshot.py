# coding: UTF-8
__author__ = 'H7112589'


import json
import redis
from datetime import datetime, timedelta

import repository
import workOrder


HOST = 'localhost'
PORT = 6379
get_DB = 6
store_DB = 7

max_time = 7*24*60*60


def get_redis_from_six():
    wos = {}
    values = repository.get_all_keys(host=HOST, port=PORT, db=get_DB)
    # time_key = str(datetime.now().strftime('%Y%m%d%H'))
    s_time = str(datetime.now().strftime('%Y%m%d%H'))
    # s_time = str((datetime.now() + timedelta(hours=1)).strftime('%Y%m%d%H'))
    wo = workOrder.Workorder()

    ser = redis.Redis(host=HOST, port=PORT, db=store_DB)
    sers = redis.Redis(host=HOST, port=PORT, db=get_DB)
    pipe = ser.pipeline()
    for value in values:
        wo.plant = value.split(':')[0]
        wo.wo_no = value.split(':')[1]
        # keys = sers.keys('%s:*' % wo.plant)
        keys = sers.keys('%s' % value)
        for key in keys:
            res = sers.hmget(key, ['status', 'pn', 'desc', 'remark', 'rev', 'qty'])
            wo.status = json.loads(res[0])
            # wo.status = res[0]
            wo.pn = res[1]
            wo.desc = res[2]
            wo.remark = res[3].strip()
            wo.rev = res[4]
            wo.qty = res[5]
            wos['plant'] = wo.plant
            wos['wo'] = wo.wo_no
            wos['pn'] = wo.pn
            wos['desc'] = wo.desc
            wos['rev'] = wo.rev
            wos['qty'] = wo.qty
            wos['remark'] = wo.remark
            wos['status'] = wo.status
            pipe.sadd(s_time, wos)
            # pipe.zadd(s_time, wos)
            # pipe.hset(s_time, wo.wo_no, wos)
            pipe.expire(s_time, max_time)
            pipe.execute()
            # print ser.smembers(s_time)
            # print ser.hget(s_time, wo.wo_no)


if __name__ == '__main__':
    get_redis_from_six()
