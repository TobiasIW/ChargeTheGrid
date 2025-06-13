import logging
from weconnect import weconnect

class carClass:
    SOC = 0.0
    newValue = 0
    _oldState = 2

    def __init__(self, vis, carConfig):
        self.SOC = vis.readVal("SOC_Car")
        self._oldState = vis.readVal("CarStatus")
        self.capacityWs =carConfig["carCapacity"]* 1000 * 3600  # Convert kWh to Ws
        
    def modelUpdateSOC(self, dT_s, charger):
        _state = int(charger.state)
        if (_state == 2) or (_state == 4):
            _power = float(charger.power)
            if (self._oldState != 2) and (self._oldState != 4) and (self._oldState != 0):
                try:
                    self.getInfo()
                except Exception as e:
                    print(e)
                    logging.error("Exception SOC: ")
                    logging.error(e)
                    if self.newValue == 3:
                        self.newValue = 2
                    else:
                        self.newValue = 3
        else:
            _power = 0  # -0.2 * 15 * 1000 / 24

        print("Power: " + str(_power))
        self.SOC = float(self.SOC) + 100 * ((_power * dT_s) / self.capacityWs)
        self._oldState = _state

    def getInfo(self, carConfig):
        if carConfig["carProtocol"] == "VW":
            self._handleVWProtocol(carConfig)
        elif carConfig["carProtocol"] == "Audi":
            self._handleAudiProtocol(carConfig)
            
        else:
            print(f"Error: Protocol '{carConfig['carProtocol']}' is not supported.")
            logging.error(f"Unsupported protocol: {carConfig['carProtocol']}")
            raise ValueError(f"Unsupported protocol: {carConfig['carProtocol']}")

    def _handleVWProtocol(self, carConfig):
        weConnect = weconnect.WeConnect(username=carConfig["carUser"], password=carConfig["carPassword"], updateAfterLogin=False, loginOnInit=False)
        print('#  Login')
        weConnect.login()
        print('#  update')
        weConnect.update()
        print('#  print results')
        for vin, vehicle in weConnect.vehicles.items():
            del vin
            if "charging" in vehicle.domains \
                    and "batteryStatus" in vehicle.domains["charging"] \
                    and vehicle.domains["charging"]["batteryStatus"].enabled:
                if vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.enabled:
                    print('#  battery status')
                    print(vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.value)
                    self.SOC = float(vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.value)
                    if self.newValue == 0:
                        self.newValue = 1
                    else:
                        self.newValue = 0

    def _handleAudiProtocol(self, carConfig):
        print("Audi protocol is not yet implemented.")
        self.SOC = 0  # Placeholder value for SOC


