import datetime

class Workorder:
    def __init__(self):
        self._wo_no = ''
        self._plant = ''
        self._key = ''
        self.last_update = datetime.datetime.now()
        self.units = {}
        self.status = {}
        self.pn = ''
        self.desc = ''
        self.rev = ''
        self.qty = 0
        self.remark = u''


    @property
    def key(self):
        return '%s:%s' % (self.plant, self.wo_no)


    @property
    def wo_no(self):
        return self._wo_no

    @wo_no.setter
    def wo_no(self, value):
        self._wo_no = value
        
    
    @property
    def plant(self):
        return self._plant

    @plant.setter
    def plant(self, value):
        self._plant = value
    
    def total(self):
        sum = 0
        for key in self.status:
            sum += self.status[key]
        return sum

class StationSorter:
    def __init__(self):
        self.key_selector = {}

def main():
    wo = Workorder()
    wo.plant = 'GHUB'
    wo.wo_no = '0000600000000'
    print(wo.plant, wo.wo_no, wo.key)


if __name__ == "__main__":
    main()
