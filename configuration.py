import json
class configurationClass:
    def __init__(self):
        self._configPath = "configuration.json"
        self.openFile()
        self.wbModel = self.jConfig["wb"]["model"]
        self.wbIP = self.jConfig["wb"]["IP"]
        self.wbProtocol = self.jConfig["wb"]["protocol"]



    def openFile(self):
        with open(self._configPath, 'r') as f:
            data = f.read()
        self.jConfig = json.loads(data)