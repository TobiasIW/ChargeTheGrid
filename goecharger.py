#!/usr/bin/python3
import json
import requests
import csv
import matplotlib.pyplot as plt
import pandas as pd
import asyncio
import os.path
import time
import datetime
import math

import pytz


# from django.utils import timezone
class chargerClass:
    state = 0
    power = 0
    ip = ""
    nPhases = 2
    TARGET = 0
    MIN = 1
    MAX = 2

    def __init__(self, arg_ip):
        self.ip = arg_ip
        self.flg1P = False
    def updateVals(self):
        print("1")
        response = requests.get(f"http://" + self.ip + "/api/status?filter=car,nrg")
        # print("1")
        # print(self.ip)
        # print(response)
        self.state = response.json()["car"]
        # print("1")
        myList = response.json()["nrg"]
        self.power = myList[11]
        print(self.power)

    def getVal(self, attribute):
        response = requests.get(f"http://" + self.ip + "/api/status?filter=" + attribute)
        val = response.json()[attribute]
        return val

    def getPower(self):
        myList = (self.getVal(self.ip, "nrg"))

        return myList[11]

    def setVal(self, attribute, value):
        # print("setValCalled",attribute,value)
        # print(f"http://"+self.ip+"/api/set?"+attribute+"="+value)
        response = requests.get(f"http://" + self.ip + "/api/set?" + attribute + "=" + value)

    def stopCharge(self):
        print("stop")
        self.setVal("frc", "1")

    def startCharge(self):
        # print("startChargeCalled")
        self.setVal("frc", "0")

    def setPower(self, power, flgAllw1P):
        # print("setpowerCalled",power)

        if power > 230 * 16:
            Amp = power / 230 / self.nPhases
            self.flg1P = False
        else:
            if not self.flg1P and power >= 230 * 6 * self.nPhases:
                Amp = power / 230 / self.nPhases
            else:
                if flgAllw1P and power >= 230 * 6:
                    Amp = power / 230
                    self.flg1P = True
                else:
                    Amp = 0

        Amp = min(Amp, 16)
        print("Amp=", Amp)
        if Amp > 6:
            # print("start",Amp)
            iAmp = int(round(Amp - 0.5, 0))
            self.startCharge()
            # print("start",iAmp)
            self.setVal("amp", str(iAmp))
            print("1 Phase: "+str(self.flg1P))
            if self.flg1P:
                self.setVal("psm", "1")
            else:
                self.setVal("psm", "2")
            # print("started",Amp)
        else:
            # print("stop")
            self.stopCharge()

# print(getVal ("192.168.178.148","car"))
# print(getVal ("192.168.178.148","nrg"))
# print(getVal ("192.168.178.148","wh"))
# print(getPower("192.168.178.148"))
# stopCharge("192.168.178.148")
