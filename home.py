import json
import requests

class homeData:
    SOC: float=0
    Prod: float=0
    Cons: float=0
    Cons_home: float=0
    Batt_pow: float=0
    GridFeedIn_pow: float=0
    OperatingMode: float=0
    SystemStatus: float=0
    SwitchActive: float = 0
    stChargeMode: float=0
    flgAuto:float=0
    qBattCap = 8000 # Wh
    flgIni = True
    IP = ""
    def __init__(self, config):
        self.IP = config.homeBattIP
    def update(self, charger, dT):
        try:
            response = requests.get(f"http://" + self.IP + ":8080/api/v1/status")

            self.Prod=response.json()["Production_W"]
            self.Cons=response.json()["Consumption_W"]
            self.Batt_pow=response.json()["Pac_total_W"]
            self.GridFeedIn_pow=response.json()["GridFeedIn_W"]
            self.TimeStamp=response.json()["Timestamp"]
            self.OperatingMode=response.json()["OperatingMode"]
            self.SystemStatus=response.json()["SystemStatus"]
            if self.flgIni:
                self.SOC = response.json()["USOC"]
                self.flgIni = False
            else:
                __SOCRecd=response.json()["USOC"]
                self.SOC = self.SOC - self.Batt_pow*dT/3600/self.qBattCap*100
                self.SOC = self.SOC + (__SOCRecd - self.SOC) * 0.05
            self.Cons_home=self.Cons-charger.power
        except Exception as e:
                print("Exception: couldn't read wallbox data: ", e)