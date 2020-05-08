import datetime
import json
import logging
import re
import redis
import workOrder


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


def get_all_wo_status(plant, host='localhost', port=6379, db=0):
    wos = {}
    regex = re.compile(r'\w{4}:\d{12}')
    ser = redis.Redis(host=host, port=port, db=db)
    keys = ser.keys('%s:*' % plant)
    for key in keys:
        if not regex.match(key):
            continue
        try:
            wo = workOrder.Workorder()
            wo.plant = key.split(':')[0]
            wo.wo_no = key.split(':')[1]
            # res = ser.hmget(key, {'status':'', 'pn':'', 'desc':'', 'remark':'' })
            res = ser.hmget(key, ['status', 'pn', 'desc', 'remark', 'rev', 'qty'])
            wo.status = json.loads(res[0])
            wo.pn = res[1]
            wo.desc = res[2]
            wo.remark = res[3].strip()
            wo.rev = res[4]
            wo.qty = res[5]
            # wo.status = json.loads(ser.hget(key, 'status'))
            # wo.pn = ser.hget(key, 'pn')
            # wo.desc = ser.hget(key, 'desc')
            # wo.remark = ser.hget(key, 'remark')
            wos[wo.wo_no] = wo
        except KeyError:
            continue
    return wos


def get_all_wo(plant, host='localhost', port=6379, db=0):
    wos = {}
    ser = redis.Redis(host=host, port=port, db=db)
    keys = ser.keys('%s:*' % plant)
    for key in keys:
        try:
            value = ser.hgetall(key)
            wo = workOrder.Workorder()
            wo.plant = key.split(':')[0]
            wo.wo_no = key.split(':')[1]
            wo.rev = value['rev']
            wo.pn = value['pn']
            wo.desc = value['desc']
            wo.qty = value['qty']
            wo.status = json.loads(value['status'])
            wo.units = json.loads(value['units'])
            wo.last_update = value['last_update']
            wos[wo.wo_no] = wo
        except KeyError:
            continue
    return wos


def get_wo(plant, wo, host='localhost', port=6379, db=0):
    logger = logging.getLogger('flask.app')
    key = '%s:%s' % (plant, wo)
    logger.debug(key)
    ser = redis.Redis(host=host, port=port, db=db)
    try:
        value = ser.hgetall(key)
        # print(value)
        wo = workOrder.Workorder()
        wo.plant = key.split(':')[0]
        wo.wo_no = key.split(':')[1]
        wo.status = json.loads(value['status'])
        # pn total
        wo.pn = value['pn']
        wo.total = wo.total()
        # print(wo.total)
        wo.rev = value['rev']
        wo.qty = value['qty']
        wo.desc = value['desc']
        wo.remark = value['remark'].strip()
        wo.units = json.loads(value['units'])
        wo.last_update = value['last_update']
    except KeyError:
        pass

    return wo


def get_wo_date(key, host='localhost', port=6379, db=0):
    ser = redis.Redis(host=host, port=port, db=db)
    results = ser.get(key)
    return results


def get_all_keys(host='localhost', port=6379, db=0):
    ser = redis.Redis(host=host, port=port, db=db)
    keys = filter(lambda k: k.find(':') > 3, ser.keys('*'))
    return keys


def del_key(key, host='localhost', port=6379, db=0):
    result = False
    try:
        ser = redis.Redis(host=host, port=port, db=db)
        ser.delete(key)
        # print(ser.delete(key))
        result = True
    except Exception:
        logging.getLogger().error('Fail to delete key')
    return result


def set_wo(wo, host='localhost', port=6379, db=0):
    ser = redis.Redis(host=host, port=port, db=db)
    key = wo.key
    pipe = ser.pipeline()
    pipe.hset(key, 'status', json.dumps(wo.status))
    pipe.hset(key, 'units', json.dumps(wo.units, cls=DateTimeEncoder))
    # pipe.hset(key, 'units', DateTimeEncoder.encode(wo.units))
    pipe.hset(key, 'pn', wo.pn)
    pipe.hset(key, 'desc', wo.desc)
    pipe.hset(key, 'rev', wo.rev)
    pipe.hset(key, 'qty', wo.qty)
    pipe.hset(key, 'remark', wo.remark)
    pipe.hset(key, 'last_update', datetime.datetime.now())
    pipe.execute()


def set_wos(wos, host='localhost', port=6379, db=0):
    ser = redis.Redis(host=host, port=port, db=db)
    key = wos.key
    # print(key, wos.pn, wos.desc, wos.qty, wos.remark)
    pipe = ser.pipeline()
    pipe.hset(key, 'status', json.dumps(wos.status))
    pipe.hset(key, 'units', json.dumps(wos.units, cls=DateTimeEncoder))
    pipe.hset(key, 'pn', wos.pn)
    pipe.hset(key, 'desc', wos.desc)
    pipe.hset(key, 'rev', wos.rev)
    pipe.hset(key, 'qty', wos.qty)
    pipe.hset(key, 'remark', wos.remark)
    pipe.hset(key, 'last_update', datetime.datetime.now())
    pipe.execute()


def snap_shot_status(start, end, plant, host='localhost', port=6379, db=0):
    s_key = int(start + '00')
    f_key = int(end + '24')
    dict_s = {}
    key_list = []
    results_start = []
    ser = redis.Redis(host=host, port=port, db=db)
    keys = ser.keys()
    for key in sorted(keys):
        if int(key) in range(s_key, f_key):
            key_list.append(key)
            data_start_s = ser.smembers(key)
            for i in range(0, len(list(data_start_s))):
                # data_start = eval(list(ser.sunion(key))[0], dict_s)
                data_start = eval(list(data_start_s)[i], dict_s)
                if data_start not in results_start and data_start['plant'] == plant:
                    results_start.append(data_start)
                else:
                    continue
    return key_list, results_start


def test():
    # wos = get_all_wo('GHUB')
    wos = get_all_wo_status('GHUB')
    print(wos['000060062991'].status)
    # wo = workOrder.Workorder()
    # wo.plant = 'GHUB'
    # wo.wo_no = '000060062991';
    # wo.status = {'PT': 10, 'VI/CT':20}
    # wo.units = {'LXAHU0AD4DH04Z':'VI/CT','LXAHU0AD4DH04I':'PT'}
    # print(set_wo(wo))


if __name__ == "__main__":
    # test()
    pass
