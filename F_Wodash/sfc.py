import bs4
import datetime
import json
import logging
import urllib
import urllib2
import urlparse
import workOrder
import xlwt

class SortKeyFinder:
    pass
    def __init__(self, path):
        self.selectors = {}
        with open(path) as ol:
            # text = ol.read()
            # print(text)
            obj = json.load(ol)
            for i, e in enumerate(obj['data']):
                self.selectors[i] = e
    
    def get_key(self, station):
        key = len(self.selectors)
        for i in sorted(self.selectors.keys()):
            if station.upper() in self.selectors[i]:
                key = i
                break
        return key


class StationMerger:
    pass
    def __init__(self, path):
        self.mappings = []
        with open(path) as ol:
            # text = ol.read()
            # print(text)
            obj = json.load(ol)
            for e in obj['data']:
                self.mappings.append(e)

    def merger(self, stations):
        c_stations = []
        for station in stations:
            for mapping in self.mappings:
                if station in mapping['stations']:
                    if len(c_stations) > 0 and c_stations[-1][0] == mapping['cname']:
                        c_stations[-1][1].append(station)
                    else:
                        c_stations.append((mapping['cname'] , [station]))
                    break
            else:
                c_stations.append((station, [station]))
        return c_stations


def plant_string(plant):
    value = 'GHUS-JV'
    if plant == 'GHUB':
        value = 'GHUB-HP'
    elif plant == 'GHUO':
        value = 'GHUO-Microsoft'
    elif plant == 'GHUD':
        value = 'GHUD-HPDB'
    elif plant == 'GHUX':
        value = 'GHUX-JV'
    elif plant == 'GHUC':
        value = 'GHUC-Dothill'
    elif plant == 'GHGG':
        value = 'GHGG-MU3'
    return value

def url_switch(plant):
    url = 'http://10.67.70.66:8080'
    if plant == 'GHGG':
        url = 'http://10.67.70.65:808'
    return url

def get_assemblyed(plant, csns, url='http://10.67.70.212:8091/SSNINFO/'): # http://10.67.70.212:8091/SSNINFO/,http://10.67.70.213:8091/SSNINFO/
    assys = []
    # uri = '%s/%s' % (url.rstrip('/'), 'GetSSNByCSN')
    uri = urlparse.urljoin(url, 'GetSSNByCSN')
    headers = {'Content-type': 'application/json'}
    param = {'data':[]}
    for csn in csns:
        param['data'].append({'csn': csn})
    data = json.dumps(param)
    req = urllib2.Request(uri, data, headers)
    res = urllib2.urlopen(req)
    text = res.read()
    
    try:
        obj = json.loads(text)
        for dic in obj['data']:
            if 'csn' in dic:
                csn = str(dic['csn'])
                if csn in csns:
                    assys.append(csn)
    except ValueError as e:
        logger = logging.getLogger()
        logger.warn('%s==%s==%s' % (plant, text, e ))
        logger.warn(csns)
        print(plant)
        print(csns)
        print(text)

    return assys

def get_components(plant, sns, url='http://10.67.70.212:8091/SSNINFO/'): # http://10.67.70.212:8091/SSNINFO/,http://10.67.70.213:8091/SSNINFO/
    assys = {}
    # uri = '%s/%s' % (url.rstrip('/'), 'GetSSNByCSN')
    uri = urlparse.urljoin(url, 'GetCsnBySsn')
    headers = {'Content-type': 'application/json'}
    param = {'data':[]}
    for sn in sns:
        param['data'].append({'ssn': sn})
    data = json.dumps(param)
    req = urllib2.Request(uri, data, headers)
    res = urllib2.urlopen(req)
    text = res.read()
    try:
        obj = json.loads(text)
        for dic in obj['data']:
            if 'ssn' in dic:
                ssn = str(dic['ssn'])
                coms = []
                if 'details' in dic:
                    for record in dic['details']:
                        com = { 'csn':record['csn'], 'pn':record['hhpn'], 'desc':record['desc'], 'mg':record['categoryname'] }
                        coms.append(com)
                    assys[ssn] = coms
    except ValueError as e:
        logger = logging.getLogger()
        logger.warn('%s==%s==%s' % (plant, text, e ))
        logger.warn(sns)
        print(plant)
        print(sns)
        print(text)
        
    return assys

def get_last_time(plant, sns, url='http://10.67.70.212:8091/SSNINFO/'):
    last_times = {}
    # uri = '%s/%s' % (url.rstrip('/'), 'GeteventBySSN')
    uri = urlparse.urljoin(url, 'GeteventBySSN')
    headers = {'Content-type': 'application/json'}
    param = {'data':[]}
    for sn in sns:
        param['data'].append({'ssn': sn})
    data = json.dumps(param)
    req = urllib2.Request(uri, data, headers)
    res = urllib2.urlopen(req)
    text = res.read()
    try:
        obj = json.loads(text)
        for dic in obj['data']:
            if 'ssn' in dic:
                last = datetime.datetime.min
                if 'details' in dic:
                    for event in dic['details']:
                        try:
                            dt = datetime.datetime.strptime(event['scandatetime'], '%Y-%m-%d %H:%M:%S.%f')
                            if dt > last:
                                last = dt
                        except ValueError:
                            continue
                    last_times[dic['ssn']] = last
    except ValueError as e:
        logger = logging.getLogger()
        logger.warn('%s==%s==%s' % (plant, text, e ))
        logger.warn(sns)
        print(plant)
        print(sns)
        print(text)
    return last_times

def get_desc_pn(plant, pn, url='http://10.67.70.66:8080'):
    factory = 'MSDIITJ'
    if plant == 'GHUC':
        factory = 'DothillTJ'
    elif plant == 'GHGG':
        factory = 'GHGG-MU3'
    desc = ''
    
    url = urllib.basejoin(url, '/MM/mmprodmasteredit.asp')
    url += '?pAdd=1&pEdit=1&pDelete=1&pCopy=1&pModule=MM&pSection=Product&pFunction=Product+Master&pFunctionname=MM_FUN_PRODUCT_PROFILE&Plant=%s&mode=Edit&ppartno=%s' % (factory, pn)
    resp = urllib.urlopen(url)
    try:
        bs = bs4.BeautifulSoup(resp)
        ta = filter(lambda e:e['name'] == 'lDescription' , bs.find_all('textarea'))[0]
        desc = ta.string
        # print(desc)
    except KeyError:
        logging.getLogger().error('No desc found for %s, %s' % (plant, pn) )
    return desc

def get_wo_info2(plant, wo_no, url='http://10.67.70.66:8080'):
    info = { 'pn':'' ,'desc':''}
    
    data = {"mode": "Edit", "pAdd": "1", "pCopy": "1", "pDelete": "1", "pEdit": "1",
     "pFunction": "WO+Serial", "pFunctionName": "PM_RPT_WO_SSN", "pModule": "PM", "pSection": "Report"}
    data["Plant"] = plant_string(plant)
    data["workorderno"] = wo_no
    query_string = ''
    for key in data:
        query_string = '%s&%s=%s' % (query_string, key, data[key])
    uri = '%s/PM/mfworkorderssn.asp?%s' % (url, query_string.strip('&'))
    response = urllib2.urlopen(uri)
    if response.code == 200:
        content = response.read().strip()
        bs = bs4.BeautifulSoup(content)
        try:
            info['pn'] = bs.findAll('table')[1].findAll('tr')[2].findAll('td')[1].findAll('small')[1].string
            info['desc'] = get_desc_pn(plant, info['pn'], url)
        except IndexError:
            pass
    return info

def get_wo_info(plant, wo_no, url='http://10.67.70.66:8080'):
    info = { 'pn':'' ,'desc':'', 'rev':'', 'qty':0}
    
    data = {"mode": "Edit", "pAdd": "1", "pCopy": "1", "pDelete": "1", "pEdit": "1",
     "pFunction": "Work+Order", "pFunctionName": "PM_FUN_WORK_ORDER", "pModule": "PM", 
     "pSection": "WO+Order", 'pCustPoNo=':''}
    data["Plant"] = plant_string(plant)
    data["workorderno"] = wo_no
    query_string = ''
    for key in data:
        query_string = '%s&%s=%s' % (query_string, key, data[key])
    uri = '%s/PM/mfworkordermain.asp?%s' % (url, query_string.strip('&'))
    response = urllib2.urlopen(uri)
    if response.code == 200:
        content = response.read().strip()
        bs = bs4.BeautifulSoup(content)
        try:
            info['pn'] = str(bs.select('input[name==skuno]')[0]['value'].strip())
            info['desc'] = str(bs.select('textarea[name==skudesc]')[0].string.strip())
            info['rev'] = str(bs.select('input[name==skuversion]')[0]['value'].strip())
            info['qty'] = int(bs.select('input[name==workorderqty]')[0]['value'])
        except IndexError:
            print('?')
        except AttributeError:
            print('?')
    return info

def get_workOrder_status_units(plant, wo_no, url='http://10.67.70.66:8080'):
    status = {}
    units = {}

    data = {"mode": "Edit", "pAdd": "1", "pCopy": "1", "pDelete": "1", "pEdit": "1",
     "pFunction": "WO+Serial", "pFunctionName": "PM_RPT_WO_SSN", "pModule": "PM", "pSection": "Report"}
    data["Plant"] = plant_string(plant)
    data["workorderno"] = wo_no
    query_string = ''
    for key in data:
        query_string = '%s&%s=%s' % (query_string, key, data[key])
    uri = '%s/PM/mfworkorderssn.asp?%s' % (url, query_string.strip('&'))
    response = urllib2.urlopen(uri)
    if response.code == 200:
        content = response.read().strip()
        bs = bs4.BeautifulSoup(content)
        try:
            for row in bs.findAll('table')[3].findAll('tr'):
                tds = row.find_all('td')
                if 'Serial' in tds[0].string:
                    continue
                sn = str(tds[0].string.replace('&nbsp','').replace('\r','').replace('\n','').replace('\t','').replace(u'\xa0', ''))
                event = str(tds[2].string.replace('&nbsp','').replace('\r','').replace('\n','').replace('\t','').replace(u'\xa0', '')).upper()
                
                if event == 'INREPAIR':
                    event = 'REPAIR'
                # elif event in ('074F', '073F'):
                #     event = 'SHIPOUT'
                units[sn] = [event, datetime.datetime.min]
        except IndexError:
            pass
        except KeyError:
            pass
        except IOError:
            pass
        asses = {}
        # if not(plant == 'GHGG') and not(plant == 'GHUC'):
        #     asses = get_assemblyed(plant, units.keys())

        for unit in units:
            if unit in asses:
                units[unit][0] = 'ASSEMBLYED'

        last_times = {}
        if not(plant == 'GHGG') and not(plant == 'GHUC'):
            last_times = get_last_time(plant, units.keys())

        for unit in units:
            if unit in last_times:
                units[unit][1] = last_times[unit]
        
        for key in units:
            if units[key][0] in status:
                status[units[key][0]] += 1
            else:
                status[units[key][0]] = 1


    return status, units

def main():
    # print(get_wo_info('GHUO', '000060059590'))
    # print(get_workOrder_status_units('GHUO', '000060059590')[0])
    # print(get_workOrder_status_units('GHUO', '000060063112'))
    print(get_wo_info2('GHUO', '000060062534'))
    # kf = SortKeyFinder(r'.\static\station.json')
    # print(kf.get_key('OOBA'))
    # print(get_assemblyed('GHUB', ['02012GJ00T0NDJ1J3', '7CE013P30D', '79HN487700453', '02012GJ00T0NDJ00Y']))
    # print(get_last_time('GHUX', ['7CE013P30D', '7CE013P32G']))
    # print(get_components('GHUX', ['02012GJ00T0NDJ1J3', '7CE013P30D', '7CE013P32G']))

if __name__ == "__main__":
    main()