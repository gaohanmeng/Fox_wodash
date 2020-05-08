import workOrder

class IndexVM:
    def __init__(self):
        self.plants = [(u'MSFT', 'GHUO'), (u'ALI', 'GHUX'), (u'TC/BD', 'GHUD'), (u'HPE', 'GHUB'), (u'SG RSS', 'GHUC'), (u'SG OSS', 'GHGG')]
        self.plant = ''
        self.wo_nos = []
        self.wos = {}
        self.stations = []
        self.c_stations = []

class MaintainVM:
    def __init__(self):
        self.plants = [(u'MSFT', 'GHUO'), (u'ALI', 'GHUX'), (u'TC/BD', 'GHUD'), (u'HPE', 'GHUB'), (u'SG RSS', 'GHUC'), (u'SG OSS', 'GHGG')]
        self.plant = ''
        self.wo_nos = []
        self.wos = {}

class DetailVM:
    def __init__(self):
        self.plants = [(u'MSFT', 'GHUO'), (u'ALI', 'GHUX'), (u'TC/BD', 'GHUD'), (u'HPE', 'GHUB'), (u'SG RSS', 'GHUC'), (u'SG OSS', 'GHGG')]
        self.plant = ''
        self.wo_no = ''
        self.station = ''
        self.wo = workOrder.Workorder()