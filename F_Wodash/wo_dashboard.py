# coding: UTF-8
from flask import Flask, g, render_template, request, session, url_for, jsonify, send_file, send_from_directory
from ViewModel import IndexVM, MaintainVM, DetailVM
import datetime
import flask_login
import json
import logging
import redis
import xlrd
import xlwt
import middleware
import repository
import sfc
import sys,os
import workOrder

reload(sys)
sys.setdefaultencoding('utf-8')


HOST = 'localhost'  # '172.21.35.53'
PORT = 6379
DB = 6
store_DB = 7

app = Flask(__name__)
static_dir = os.path.join(os.path.dirname(__file__), 'static')
# app.wsgi_app = middleware.PrefixMiddleware(app.wsgi_app, prefix='/wo_dashboard')
app.wsgi_app = middleware.PrefixMiddleware(app.wsgi_app, prefix='/test_dashboard')  # 修改prefix参数
logging.basicConfig(level=logging.DEBUG, filename=r'web.log')
logger = logging.getLogger('flask.app')


@app.route('/', methods=['GET', 'POST'])
def index():
    vm = IndexVM()
    vm.plant = 'GHUO'
    if 'plant' in request.form:
        vm.plant = request.form['plant']

    wos =  repository.get_all_wo_status(vm.plant,host=HOST, port=PORT, db=DB)
    # vm.wos = wos
    # vm.wo_nos = sorted(wos.keys())
    vm.wos = wos
    vm.wo_nos = sorted(wos.keys())
    stations = set([])
    for wo_no in vm.wo_nos:
        stations = stations.union(vm.wos[wo_no].status.keys())
        # print vm.wos[wo_no].status.keys()
    kf = sfc.SortKeyFinder(r'.\static\station.json')
    vm.stations = sorted(stations,key= lambda s: kf.get_key(s))
    merger = sfc.StationMerger(r'.\static\merge.json')
    vm.c_stations = merger.merger(vm.stations)
    return render_template('index.html', vm=vm)


@app.route('/maintain', methods=['GET', 'POST'])
def maintain():
    vm = MaintainVM()
    vm.plant = 'GHUO'
    if 'plant' in request.form:
        vm.plant = request.form['plant']

    wos = repository.get_all_wo_status(vm.plant, host=HOST, port=PORT, db=DB)
    vm.wos = wos
    vm.wo_nos = sorted(wos.keys())

    return render_template('maintain.html', vm=vm)
    # return render_template('test.html', vm=vm)
    # return render_template('maintaincopy.html', vm=vm)


@app.route('/detail/<string:plant>/<string:wo>/<station>', methods=['GET'])
def detail(plant, wo, station='0'):
    vm = DetailVM()
    vm.plant = plant
    vm.wo_no = wo
    vm.station = station
    if station == 'VIGCT':
        station = 'VI/CT'
    vm.wo = repository.get_wo(plant, wo, HOST, PORT, DB)
    if not station == '0':
        filtered = {}
        for sn in vm.wo.units:
            if vm.wo.units[sn][0] == station:
                filtered[sn] = vm.wo.units[sn]
        vm.wo.units = filtered

    filter(lambda sn: vm.wo.units[sn][0] == station, vm.wo.units)

    return render_template('detail.html', vm=vm)


@app.route('/api/woinfo/<string:plant>/<string:wo>', methods=['GET'])
def api_wo_info(plant, wo):
    info = sfc.get_wo_info(plant, wo, sfc.url_switch(plant))
    return jsonify(info)


@app.route('/api/woadd', methods=['POST'])
def api_add_wo():
    logger.debug('api_add_wo')
    plant = ''
    wo = ''
    remark= ''
    result = 0
    if 'plant' in request.form:
        plant = request.form['plant']
    if 'wo' in request.form:
        wo = request.form['wo']
    if 'remark' in request.form:
        remark = request.form['remark']
    # logger.debug('%s==%s==%s' % (plant, wo, remark))

    order = workOrder.Workorder()
    order.plant = str(plant)
    order.wo_no = str(wo)
    order.remark = str(remark)
    # logger.debug('key:%s' % order.key)
    info = sfc.get_wo_info(plant, wo, sfc.url_switch(plant))
    order.pn = info['pn']
    order.desc = info['desc']
    order.rev = info['rev']
    order.qty = info['qty']
    (order.status, order.units) = sfc.get_workOrder_status_units(plant, wo, sfc.url_switch(plant))
    repository.set_wo(order, host=HOST, port=PORT, db=DB)
    result = 1
    return str(result)


@app.route('/maintain/wosadd')  # 新增
def index_add_wos():
    vm = MaintainVM()
    vm.plant = 'GHUO'
    if 'plant' in request.form:
        vm.plant = request.form['plant']
    wos = repository.get_all_wo_status(vm.plant, host=HOST, port=PORT, db=DB)
    vm.wos = wos
    return render_template('addwos.html', vm=vm)


@app.route('/maintain/getwos', methods=['post', 'GET'])  # 新增
def get_wos_status():
    i = 0
    result = []
    vm = MaintainVM()
    vm.plant = 'GHUO'
    if 'plant' in request.form:
        vm.plant = request.form['plant']
    wos = repository.get_all_wo_status(vm.plant, host=HOST, port=PORT, db=DB)
    vm.wos = wos

    try:
        f = request.files.get('excelFile').read()
        data = xlrd.open_workbook(file_contents=f)
        table = data.sheet_by_index(i)
        keys = table.row_values(0)
        if keys:
            row_num = table.nrows  # 行数
            col_num = table.ncols  # 列数
            for i in range(1, row_num):
                sheet_data = {}
                for j in range(0, col_num):
                    sheet_data['DESC'] = table.row_values(i)[0]
                    sheet_data['PN'] = table.row_values(i)[1]
                    # sheet_data['WO'] = table.row_values(i)[2]
                    if str(int(table.row_values(i)[2])).startswith('6'):
                        sheet_data['WO'] = '0000' + str(int(table.row_values(i)[2]))
                    elif str(int(table.row_values(i)[2])).startswith('1') \
                            or str(int(table.row_values(i)[2])).startswith('4'):
                        sheet_data['WO'] = '000' + str(int(table.row_values(i)[2]))
                    sheet_data['Qty'] = table.row_values(i)[5]
                    sheet_data['Remark'] = table.row_values(i)[6]
                    if sheet_data not in result:
                        result.append(sheet_data)
        return render_template('addwoss.html', results=result, vm=vm)
    except Exception:
        return render_template('error.html')


@app.route('/maintain/uploadwos', methods=['post', ])  # 新增
def wos_upload_redis():
    order = workOrder.Workorder()
    i = 0
    result = []
    vm = MaintainVM()
    vm.plant = 'GHUO'
    if 'plant' in request.form:
        vm.plant = request.form['plant']
    wos = repository.get_all_wo_status(vm.plant, host=HOST, port=PORT, db=DB)
    vm.wos = wos

    try:
        f = request.files.get('excelFile').read()
        data = xlrd.open_workbook(file_contents=f)
        table = data.sheet_by_index(i)
        keys = table.row_values(0)
        if keys:
            row_num = table.nrows
            col_num = table.ncols
            for i in range(1, row_num):
                sheet_data = {}
                for j in range(0, col_num):
                    sheet_data['DESC'] = table.row_values(i)[0]
                    sheet_data['PN'] = table.row_values(i)[1]
                    sheet_data['WO'] = table.row_values(i)[2]
                    sheet_data['Qty'] = table.row_values(i)[5]
                    sheet_data['Remark'] = table.row_values(i)[6]
                    if sheet_data not in result:
                        result.append(sheet_data)
        for info in result:
            order._plant = vm.plant
            order.desc = info['DESC']
            order.pn = info['PN']
            if str(int(info['WO'])).startswith('6'):
                order.wo_no = '0000' + str(int(info['WO']))
            elif str(int(info['WO'])).startswith('1') or str(int(info['WO'])).startswith('4'):
                order.wo_no = '000' + str(int(info['WO']))
            order.qty = info['Qty']
            order.remark = info['Remark']
            (order.status, order.units) = sfc.get_workOrder_status_units(vm.plant, order.wo_no, sfc.url_switch(vm.plant))
            # print(order._plant, order.desc, order.pn, order.wo_no, order.qty, order.remark)
            repository.set_wos(order, host=HOST, port=PORT, db=DB)
        return render_template('addwos.html', vm=vm)
    except Exception:
        return render_template('error.html')


@app.route('/maintain/download', methods=['post', ])  # 新增
def download_templates():
    if request.form.get('Download'):
        files = os.path.join(os.path.dirname(__file__), 'static/input.xlsx')
        return send_file(filename_or_fp=files, as_attachment=True, attachment_filename='input.xls')


@app.route('/maintain/downloaddetail', methods=['post', ])  # 新增
def download_detail():
    if request.form.get('DownloadDetail'):
        x = 1
        details_file = os.path.join(os.path.dirname(__file__), 'static/detail.xlsx')
        wb = xlwt.Workbook()
        ws = wb.add_sheet('details', cell_overwrite_ok=True)
        detail_key = request.form.getlist('CheckDetail')
        for key in detail_key:
            details = repository.get_wo(key.split('/')[0], key.split('/')[1], HOST, PORT, DB)
            # print(sorted(details.wo_no))
            wo_no = details.wo_no
            pn = details.pn
            desc = details.desc
            qty = details.total
            remark = details.remark.decode(encoding='utf-8')
            plant = details.plant
            last_update = str(details.last_update).split('.')[0]
            sns = details.units.keys()
            for sn in sns:
                station = details.units[sn][0]
                if station == 'VIGCT':
                    station = 'VI/CT'
                row = ['PLANT', 'WO', 'PN', 'SN', 'STATION', 'DESC', u'已出货', 'Remark', 'LastTime']
                column = [plant, wo_no, pn, sn, station, desc, qty, remark, last_update]
                for i in range(0, len(row)):
                    ws.write(0, i, row[i])
                    i += 1
                for j in range(0, len(column)):
                    ws.write(x, j, column[j])
                    j += 1
                x += 1
        wb.save(details_file)
        return send_file(filename_or_fp=details_file, as_attachment=True, attachment_filename='details.xls')


@app.route('/api/woclose', methods=['POST', ])
def api_close_wo():
    # logger.debug('api_close_wo')
    plant = ''
    wo = ''
    result = 0
    if 'plant' in request.form:
        plant = request.form['plant']
    if 'wo' in request.form:
        wo = request.form['wo']
    # logger.debug('%s==%s' % (plant, wo))
    repository.del_key('%s:%s' % (plant, wo))
    result = 1
    return str(result)


@app.route('/maintain/delallkeys', methods=['post', 'get'])  # 新增
def close_all_wos():
    # 1.删除所有
    if request.form.get('btnclose'):
        keys = request.form.getlist('hidcloseall')
        vm = MaintainVM()
        vm.plant = keys[0]
        if 'plant' in request.form:
            vm.plant = request.form['plant']
        wos = repository.get_all_wo_status(vm.plant, host=HOST, port=PORT, db=DB)
        vm.wos = wos
        vm.wo_nos = sorted(wos.keys())  # ['000060030987', '000060030988']
        for wo in vm.wo_nos:
            result = repository.del_key('%s:%s' % (vm.plant, wo), host=HOST, port=PORT, db=DB)
        return render_template('maintain.html', vm=vm)


@app.route('/maintain/delpartkeys', methods=['post', ])  # 新增
def close_part_wos():
    # 1.批量删除
    if request.form.get('clspart'):
        keys = request.form.getlist('hidclosepart')
        vm = MaintainVM()
        vm.plant = keys[0]
        wos = repository.get_all_wo_status(vm.plant, host=HOST, port=PORT, db=DB)
        vm.wos = wos
        vm.wo_nos = sorted(wos.keys())
        part_list = request.form.getlist('CheckPart')
        if 'plant' in request.form:
            vm.plant = request.form['plant']
        for wo in part_list:
            result = repository.del_key('%s:%s' % (vm.plant, wo), host=HOST, port=PORT, db=DB)

        return render_template('maintain.html', vm=vm)


@app.route('/maintain/index_query', methods=['post', 'get'])  # xinzeng
def index_query():
    vm = MaintainVM()
    vm.plant = 'GHUO'
    keys = []
    if 'plant' in request.form:
        vm.plant = request.form['plant']
    wos = repository.get_all_wo_status(vm.plant, host=HOST, port=PORT, db=store_DB)
    vm.wos = wos
    vm.wo_nos = sorted(wos.keys())
    stations = set([])
    for wo_no in vm.wo_nos:
        stations = stations.union(vm.wos[wo_no].status.keys())
    kf = sfc.SortKeyFinder(r'.\static\station.json')
    vm.stations = sorted(stations, key=lambda s: kf.get_key(s))
    merger = sfc.StationMerger(r'.\static\merge.json')
    vm.c_stations = merger.merger(vm.stations)
    if request.method == 'post':
        return render_template('query_redis.html', vm=vm, keys=keys)
    return render_template('query_redis.html', vm=vm, keys=keys)


@app.route('/maintain/query', methods=['post', 'get'])  # xinzeng
def query_redis():
    keys = []
    start_time = request.form.get('startTime')
    end_time = request.form.get('endTime')
    vm = MaintainVM()
    vm.plant = request.form.getlist('hidvalue')[0]
    if 'plant' in request.form:
        vm.plant = request.form['plant']

    if request.form.get('query_redis'):
        if start_time and end_time:
            start = str(datetime.datetime.strptime(start_time, '%Y/%m/%d').strftime('%Y%m%d'))
            end = str(datetime.datetime.strptime(end_time, '%Y/%m/%d').strftime('%Y%m%d'))
            keys, results_start = repository.snap_shot_status(start, end, vm.plant, host=HOST, port=PORT, db=store_DB)
            vm.wos = results_start
            # print vm.wos[0]['status'].values()  # [335, 5, 1, 1, 4, 1, 2, 79, 1, 2, 1]
            stations = set([])
            for ss in vm.wos:
                stations = stations.union(ss['status'].keys())
            kf = sfc.SortKeyFinder(r'.\static\station.json')
            vm.stations = sorted(stations, key=lambda s: kf.get_key(s))
            merger = sfc.StationMerger(r'.\static\merge.json')
            vm.c_stations = merger.merger(vm.stations)
            return render_template('query_redis.html', vm=vm, keys=keys)
        else:
            return render_template('error.html')
    return render_template('query_redis.html', vm=vm, keys=keys)


def main():
    app.run(debug=True, host='10.67.71.132', port=40020)

if __name__ == "__main__":
    main()
