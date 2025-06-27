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
    pwrHysNeg = 1000
    pwrHysPos = 1000

    def __init__(self, config):
        self.ip = config["wbIP"]
        self.flg1P = False
        self.flgPluggedIn = False
        self.nPhases = config["nPhases"]
    def updateVals(self):
        print("1")
        try:
            response = requests.get(f"http://" + self.ip + "/api/status?filter=car,nrg")
        
            # print("1")
            # print(self.ip)
            # print(response)
            self.state = response.json()["car"]
            if self.state == 1:
                self.flgPluggedIn = False
            else:
                self.flgPluggedIn = True
            # print("1")
            myList = response.json()["nrg"]
            self.power = myList[11]
            print(self.power)
        except Exception as e:
            print(e)



    def getVal(self, attribute):
        try:
            response = requests.get(f"http://" + self.ip + "/api/status?filter=" + attribute)
        except Exception as e:
            print(e)
        val = response.json()[attribute]
        return val

    def getPower(self):
        myList = (self.getVal(self.ip, "nrg"))

        return myList[11]

    def setVal(self, attribute, value):
        # print("setValCalled",attribute,value)
        # print(f"http://"+self.ip+"/api/set?"+attribute+"="+value)
        try:
            response = requests.get(f"http://" + self.ip + "/api/set?" + attribute + "=" + value)
        except Exception as e:
            print(e)

    def stopCharge(self):
        print("stop")
        self.setVal("frc", "1")

    def startCharge(self):
        # print("startChargeCalled")
        self.setVal("frc", "0")

    def setPower(self, power, flgAllw1P, pwrMin, pwrMax):
        # print("setpowerCalled",power)
        if self.flg1P:
            if power > 230 * 6 - self.pwrHysNeg and pwrMax > 230 * 6 and power < 230 * 16 + self.pwrHysPos and pwrMin < 230 * 16:
                Amp = power / 230
                Amp = max(6, Amp)
                Amp = min(Amp, 16)
                self.flg1P = True
                print("1 phase")
            elif power < 230 * 6 + self.pwrHysPos or pwrMax < 230 * 6:
                Amp = 0
                self.flg1P = True
                print("chargin switched off")
            else: # power > 230 * 16 + self.pwrHysPos or pwrMin > 230 * 16:
                Amp = power / (230 * self.nPhases)
                Amp = max(6, Amp)
                Amp = min(Amp, 16)
                self.flg1P = False
                print("switch from 1 phase to multi phase")
        else: # multi phase charging
            if power > 230 * 6 *self.nPhases - self.pwrHysNeg :
                Amp = power / (230 * self.nPhases)
                Amp = max(6, Amp)
                Amp = min(Amp, 16)
                self.flg1P = False
                print("multi phase charging")
            else:
                if power > 230 * 6 - self.pwrHysNeg and pwrMax > 230 * 6:

                    Amp = power / 230
                    Amp = max(6, Amp)
                    Amp = min(Amp, 16)
                    self.flg1P = True
                    print("switched from multi phase to 1 phase")
                else:
                    Amp = 0
                    self.flg1P = False
                    print("charging switched off from multi phase")

                

        print("Amp=", Amp)
        print("1 phase=", self.flg1P)
        if Amp >= 6:
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
