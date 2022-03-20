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
    def update(self, charger):
        response = requests.get(f"http://192.168.178.100:8080/api/v1/status")
        self.SOC=response.json()["USOC"]
        self.Prod=response.json()["Production_W"]
        self.Cons=response.json()["Consumption_W"]
        self.Batt_pow=response.json()["Pac_total_W"]
        self.GridFeedIn_pow=response.json()["GridFeedIn_W"]
        self.TimeStamp=response.json()["Timestamp"]
        self.OperatingMode=response.json()["OperatingMode"]
        self.SystemStatus=response.json()["SystemStatus"]

        self.Cons_home=self.Cons-charger.power
