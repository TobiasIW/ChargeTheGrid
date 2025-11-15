#!/usr/bin/python3
import json
import requests
import csv
import matplotlib.pyplot as plt
# import pandas as pd
import asyncio
from scipy import interpolate
import os.path
import time
import datetime
from astral.sun import sun
from astral.location import Location
# import pytz
import goecharger
# from django.utils import timezone
from dataclasses import dataclass


class chargeStrategy:
    def __init__(self, home):
        self.tiLastCharge = datetime.datetime.now()
        self.ratSOCTar = home.SOC
        self.flgSOCHoldActv = False
        self.stChargeMode=0
        self.filterTime = 5*60 # 5 minutes
        self.pwrAvlFltd = 0
        self.iMinSOC = 0
    def toTimestamp(self, d):
        return d.timestamp()

    def calcStrategy(self, homeData,  chargers, myCars, pred, config, dt):

        powDes = 0
        try:
            with open(config.dataFolder + 'input.txt', 'r') as status:
                self.stChargeMode = int(status.read())
        except Exception as e:
            print("Error reading stChargeMode from input.txt:", e)


        OFF = 0
        ON = 1
        AUTO_CUTOFF = 2
        AUTO_LOW = 3
        AUTO_HIGH = 4
        MANUAL = 5
        AUTO = 6

        homeData.stChargeMode = self.stChargeMode

        for charger in chargers:
            if charger.power > 0:
                self.tiLastCharge = datetime.datetime.now()
        

        flgAllow1P = True
        if self.stChargeMode == OFF:
            pwrAvl = 0
            for charger in chargers:
                charger.setPower(pwrAvl, flgAllow1P, 0, 11000)
        if self.stChargeMode == ON:
            pwrAvl = 11000
            for charger in chargers:
                charger.setPower(pwrAvl, flgAllow1P, 0, 11000)
        if self.stChargeMode!= MANUAL and self.stChargeMode >= AUTO_CUTOFF:
            if len(pred.date_a) > 0:
                timeNow_ts = pred.toTimestamp(datetime.datetime.now())
                dateDay_a_ts = [pred.toTimestamp(pred.date_a[n]) for n in range(0, len(pred.date_a))]

                maxSOCVehProdChrg_a=[]
                maxSOCVehExcessChrg_a=[]
                minSOCVeh_a = []
                for car in myCars:
                    minSOCVeh_a.append(interpolate.interp1d(dateDay_a_ts, car.minSOCVeh_a)(timeNow_ts))
                    maxSOCVehProdChrg_a.append(interpolate.interp1d(dateDay_a_ts, car.maxSOCVehProdChrg_a)(timeNow_ts))
                    maxSOCVehExcessChrg_a.append (interpolate.interp1d(dateDay_a_ts, car.maxSOCVehExcessChrg_a)(timeNow_ts))

                minSOCHomeExcessChargeMin = interpolate.interp1d(dateDay_a_ts, pred.minSOCHome_a)(timeNow_ts)
                minSOCHomeExcessChargeMax = interpolate.interp1d(dateDay_a_ts, pred.minSOCHomeLowProd_a)(timeNow_ts)
                _nPluggedIn = 0
                hysteresisSOC = 5
                minSOC = 100+hysteresisSOC
                
                iMinSOCOld = self.iMinSOC
                self.iMinSOC = 0
                iMinSOC = -1
                for i in range(0, len(chargers), 1):
                    if chargers[i].flgPluggedIn :
                        _nPluggedIn += 1

                        if (myCars[i].SOC < minSOC and myCars[i].SOC < maxSOCVehExcessChrg_a[i]) or myCars[i].SOC < min(minSOCVeh_a[i], maxSOCVehProdChrg_a[i]):
                            if myCars[i].SOC < min(minSOCVeh_a[i], maxSOCVehProdChrg_a[i]):
                                minSOC = 0
                            else:
                                if i == iMinSOCOld:
                                    minSOC = myCars[i].SOC-5
                                else:
                                
                                    minSOC = myCars[i].SOC
                            iMinSOC=i
                for i in range(len(chargers)):
                    if i != iMinSOC:
                        chargers[i].setPower(0, flgAllow1P, 0, 11000)
                if iMinSOC >= 0:
                    myCar = myCars[iMinSOC]
                    charger = chargers[iMinSOC]
                    minSOCVeh = minSOCVeh_a[iMinSOC]
                    maxSOCVehProdChrg = maxSOCVehProdChrg_a[iMinSOC]
                    maxSOCVehExcessChrg = maxSOCVehExcessChrg_a[iMinSOC]
                
        
                    if  (self.stChargeMode == AUTO and myCar.SOC < maxSOCVehProdChrg) or self.stChargeMode == AUTO_HIGH:
                        minSOCHomeExcessCharge = minSOCHomeExcessChargeMin
                    else:
                        if self.stChargeMode == AUTO_LOW:
                            minSOCHomeExcessCharge = minSOCHomeExcessChargeMax
                        else:
                            minSOCHomeExcessCharge = minSOCHomeExcessChargeMin + (minSOCHomeExcessChargeMax - minSOCHomeExcessChargeMin) * (myCar.SOC - maxSOCVehProdChrg)/(maxSOCVehExcessChrg - maxSOCVehProdChrg)

                    print("minSOCHomeExcessChargeMin: " + str(minSOCHomeExcessChargeMin))
                    print("minSOCHomeExcessChargeMax: " + str(minSOCHomeExcessChargeMax))
                    print("minSOCHomeExcessCharge: " + str(minSOCHomeExcessCharge))

                    # SOC Hold State machine
                    print("hold0 " + str(self.tiLastCharge))
                    if not self.flgSOCHoldActv and charger.power > 0:
                        self.flgSOCHoldActv = True
                        self.ratSOCTar = homeData.SOC
                        print("hold1 " + str(self.ratSOCTar))

                    if not charger.flgPluggedIn:
                        self.flgSOCHoldActv = False
                        print("hold2 " + str(self.ratSOCTar))

                    if self.tiLastCharge + datetime.timedelta(hours=1) < datetime.datetime.now():
                        self.flgSOCHoldActv = False
                        print("hold3 ")


                    if abs(homeData.SOC-self.ratSOCTar)>=homeData.ratSOCMinOper:
                            self.ratSOCTar = homeData.SOC
                    print("hold5 " + str(self.ratSOCTar))
                    self.ratSOCTar = min(max(self.ratSOCTar, minSOCHomeExcessCharge), homeData.ratSOCMaxOper)

                    print("ratSOCTar:" + str(self.ratSOCTar))
                    print("minSOC:" + str(minSOCVeh))
                    if homeData.SOC > homeData.ratSOCMaxOper:
                        if int(homeData.Prod) - int(homeData.Cons_home) + int(homeData.Batt_pow) - pred.maxFeedIn > 0:
                            pwrAvlCutOff = max(int(homeData.Prod) - int(homeData.Cons_home) - pred.maxFeedIn, 6 * 230 + 1)
                        else:
                            pwrAvlCutOff = 0
                    else:
                        pwrAvlCutOff = 0

                    pwrAvlExcChrg_HomeSuff = 0
                    pwrAvlExcChrg_BattOff = 0
                    pwrAvlExcChrg_Min = 0
                    if (self.stChargeMode == AUTO and myCar.SOC > maxSOCVehExcessChrg) or self.stChargeMode == AUTO_CUTOFF:  # above upper limit for prediction based smart charging. only charge if otherwise, power would be cut
                        pwrAvl = pwrAvlCutOff
                        # pwrAvl = int(homeData.Prod) - int(homeData.Cons_home) - pred.maxFeedIn
                        flgAllow1P = True

                    else:
                        if (int(homeData.Prod) > int(homeData.Cons_home)) and (abs(int(homeData.Batt_pow)) < 10):
                            pwrAvlExcChrg_BattOff = int(homeData.Prod) - int(homeData.Cons_home) - 100
                        if self.flgSOCHoldActv:
                            pwrAvlExcChrg = int(homeData.Prod) - int(homeData.Cons_home) + min(-pred.maxBattPowDischa,
                                max((homeData.SOC - self.ratSOCTar) * 500, - pred.maxBattPowChrg))
                        else:
                            pwrAvlExcChrg = int(homeData.Prod) - int(homeData.Cons_home) + min(-pred.maxBattPowDischa,
                                max((homeData.SOC - minSOCHomeExcessCharge) * 500, - pred.maxBattPowChrg))
                        if self.stChargeMode == AUTO:
                            __maxChrg = (maxSOCVehExcessChrg - myCar.SOC) * 5000
                            pwrAvlExcChrg_HomeSuff = min(pwrAvlExcChrg, __maxChrg)
                        else:
                            pwrAvlExcChrg_HomeSuff = pwrAvlExcChrg

                        if homeData.SOC < minSOCHomeExcessCharge:
                            pwrAvlExcChrg_Min = max(0, int(homeData.Prod) - int(homeData.Cons_home) - pred.maxBattPowChrg - 100)

                        if myCar.SOC > maxSOCVehProdChrg or self.stChargeMode == AUTO_LOW or self.stChargeMode == AUTO_HIGH:  # above upper limit for normal smart charging. charge when above minimum house SOC
                            flgAllow1P = True
                            _sun = sun(pred.city.observer, tzinfo=pred.berlin)
                            _sunset=(_sun["sunset"])
                            if (datetime.datetime.now().hour >= 6) and (pred.berlin.localize(datetime.datetime.now()) < _sunset):
                                pwrAvl = max(pwrAvlExcChrg_HomeSuff, pwrAvlExcChrg_BattOff, pwrAvlExcChrg_Min, pwrAvlCutOff)
                            else:
                                pwrAvl = 0
                        else:
                            if myCar.SOC > minSOCVeh:  # above minimum SOC: charge when production is greater than consumption
                                pwrAvl = int(homeData.Prod) - int(homeData.Cons_home)  # + max(0, min(3300, (homeData.SOC - 5) * 330))
                                pwrAvl = max(pwrAvl, pwrAvlExcChrg)

                            else:  # below min SOC: charge with full power
                                pwrAvl = 11000

                    __powerMin= max (0, int(homeData.Prod) - int(homeData.Cons_home) - max(0, min(pred.maxBattPowChrg + (homeData.ratSOCMaxOper - homeData.SOC) * 1000,pred.maxBattPowChrg)))
                    __powerMax= int(homeData.Prod) - int(homeData.Cons_home) - max(min(pred.maxBattPowDischa - (homeData.SOC - homeData.ratSOCMinOper ) * 1000, 0), pred.maxBattPowDischa)
                    __powerMin = min(__powerMin, pwrAvl)  # never reduce power below pwrAvl
                    __powerMax = max(__powerMax, pwrAvl)  # never increase power above pwrAvl
                    #filter pwrAvl with a filter time of 5 minutes
                    self.pwrAvlFltd = self.pwrAvlFltd + (pwrAvl - self.pwrAvlFltd) * dt/ self.filterTime
                    self.pwrAvlFltd = max(self.pwrAvlFltd, __powerMin)
                    self.pwrAvlFltd = min(self.pwrAvlFltd, __powerMax)
                    print ("Prod: " + str(homeData.Prod))
                    print ("Cons: " + str(homeData.Cons_home))
                    print("pwrAvlFltd: " + str(self.pwrAvlFltd))
                    print("pwrAvl: " + str(pwrAvl))
                    print("pwrAvlMin: " + str(__powerMin))
                    print("pwrAvlMax: " + str(__powerMax))
                    charger.setPower(self.pwrAvlFltd, flgAllow1P, __powerMin, __powerMax)
            else: # manual mode, no actuation
                pwrAvl = 0

        # print("ChargeStratEnd")
        return 0
