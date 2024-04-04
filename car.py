import logging
import credentials
from weconnect import weconnect

class carClass:
    SOC = 0.0
    capacityWs = 34 * 1000 * 3600
    newValue = 0
    _oldState = 2

    def __init__(self, vis, config):
        self.SOC = vis.readVal("SOC_Car")
        self._oldState = vis.readVal("CarStatus")

    def model(self, dT_s, charger):
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

    def getInfo(self):
        weConnect = weconnect.WeConnect(username=credentials.username, password=credentials.password, updateAfterLogin=False, loginOnInit=False)
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
                        if (self.newValue == 0):
                            self.newValue = 1
                        else:
                            self.newValue = 0
               

