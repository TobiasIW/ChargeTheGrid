import json

class configClass:
    def __init__(self):
        self.baseFolder = "/home/pi/ChargeOS_v2/ChargeTheGrid/"
        self.dataFolder = self.baseFolder + "data/"
        self.configFolder = self.baseFolder + "config/"
        self._configPath = self.configFolder + "configuration.json"
        self.openFile()

        # Battery configuration
        self.homeBattModel = self.jConfig["battery"]["model"]
        self.homeBattIP = self.jConfig["battery"]["IP"]
        self.homeBattProtocol = self.jConfig["battery"]["protocol"]

        # Combos configuration
        self.combo = []  # Initialize an empty array for combos
        for combo in self.jConfig["combos"]:
            self.combo.append({
                "carName": combo["car"]["name"],
                "carProtocol": combo["car"]["protocol"],
                "carUser": combo["car"]["user"],
                "carPassword": combo["car"]["password"],
                "carCapacity": combo["car"]["capacity"],  # in kWh
                "wbIP": combo["wb"]["IP"],
                "wbName": combo["wb"]["name"],
                "wbProtocol": combo["wb"]["protocol"],
                "nPhases": combo["car"]["nPhases"]
            })

    def openFile(self):
        with open(self._configPath, 'r') as f:
            data = f.read()
        self.jConfig = json.loads(data)