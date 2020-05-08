import repository
import sfc
import workOrder
import snapshot

HOST = 'localhost'
PORT = 6379
DB = 0


def update_all():
     keys = repository.get_all_keys(HOST, PORT, DB)
     groups = {}
     for key in keys:
          tokens = key.split(':')
          if tokens[0] in groups:
               groups[tokens[0]].append(key)
          else:
               groups[tokens[0]] = []
               groups[tokens[0]].append(key)
     for gp in groups:
          if len(groups[gp]) > 0:
               update_plant(gp)

def update_plant(plant):
     wos = repository.get_all_wo_status(plant, HOST, PORT, DB)
     for wo in wos:
          (wos[wo].status, wos[wo].units) = sfc.get_workOrder_status_units(plant, wo, sfc.url_switch(plant))
          repository.set_wo(wos[wo], HOST, PORT, DB)
     

def main():
    update_all()
    snapshot.get_redis_from_six()
    print('Done')

if __name__ == "__main__":
     main()
