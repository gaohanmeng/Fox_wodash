import repository
import sfc
import workOrder

HOST = 'localhost'
PORT = 6379
DB = 0


def main():
    wos =  {}
    ol = open(r'.\static\inputs.txt')
    lines = ol.readlines()
    ol.close()
    for line in lines:
        tokens = line.split(',')
        wo = workOrder.Workorder()
        wo.plant = tokens[0]
        wo.wo_no = tokens[1]
        info = sfc.get_wo_info(wo.plant, wo.wo_no, sfc.url_switch(wo.plant))
        print(info)
        wo.pn = info['pn']
        wo.rev = info['rev']
        wo.qty = info['qty']
        wo.rev = info['rev']
        wo.desc = info['desc']
        if(len(tokens) > 2):
            wo.remark = tokens[2].strip()
        if len(wo.pn) > 0:
            (wo.status, wo.units) =  sfc.get_workOrder_status_units(wo.plant, wo.wo_no, sfc.url_switch(wo.plant))
            wos[wo.wo_no] = wo
            print('%s==%s' % (wo.key, repository.set_wo(wo, HOST, PORT, DB)))
        else:
            print('%s Skiped' % wo.key)
    print('Done')


if __name__ == "__main__":
    main()