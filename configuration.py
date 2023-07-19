import json
class configClass:
    def __init__(self):
        self.baseFolder = "/home/pi/chargeOS_v2/"

        self.dataFolder =  self.baseFolder + "data/"
        self.configFolder = self.baseFolder + "config/"

        self._configPath = self.configFolder + "configuration.json"
        self.openFile()
        self.wbModel = self.jConfig["wb"]["model"]
        self.wbIP = self.jConfig["wb"]["IP"]
        self.wbProtocol = self.jConfig["wb"]["protocol"]
        self.homeBattModel = self.jConfig["battery"]["model"]
        self.homeBattIP = self.jConfig["battery"]["IP"]
        self.homeBattProtocol = self.jConfig["battery"]["protocol"]



    def openFile(self):
        with open(self._configPath, 'r') as f:
            data = f.read()
        self.jConfig = json.loads(data)