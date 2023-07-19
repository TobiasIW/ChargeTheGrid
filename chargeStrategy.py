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

    def toTimestamp(self, d):
        return d.timestamp()

    def calcStrategy(self, homeData, csvname, charger, myCar, pred, config):

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


        if charger.power > 0:
            self.tiLastCharge = datetime.datetime.now()


        flgAllow1P = True
        if self.stChargeMode == OFF:
            pwrAvl = 0
        if self.stChargeMode == ON:
            pwrAvl = 11000
        if self.stChargeMode >= AUTO_CUTOFF:
            if len(pred.date_a) > 0:
                timeNow_ts = pred.toTimestamp(datetime.datetime.now())
                dateDay_a_ts = [pred.toTimestamp(pred.date_a[n]) for n in range(0, len(pred.date_a))]
                minSOCVeh = interpolate.interp1d(dateDay_a_ts, pred.minSOCVeh_a)(timeNow_ts)
                maxSOCVehProdChrg = interpolate.interp1d(dateDay_a_ts, pred.maxSOCVehProdChrg_a)(timeNow_ts)

                maxSOCVehExcessChrg = interpolate.interp1d(dateDay_a_ts, pred.maxSOCVehExcessChrg_a)(timeNow_ts)
                minSOCHomeExcessChargeMin = interpolate.interp1d(dateDay_a_ts, pred.minSOCHome_a)(timeNow_ts)
                minSOCHomeExcessChargeMax = interpolate.interp1d(dateDay_a_ts, pred.minSOCHomeLowProd_a)(timeNow_ts)
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


                if abs(homeData.SOC-self.ratSOCTar)>=3:
                        self.ratSOCTar = homeData.SOC
                print("hold5 " + str(self.ratSOCTar))
                self.ratSOCTar = min(max(self.ratSOCTar, minSOCHomeExcessCharge), 97)

                print("ratSOCTar:" + str(self.ratSOCTar))
                print("minSOC:" + str(minSOCVeh))
                if homeData.SOC > 97:
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
            else:
                pwrAvl = 0

        try:
            if self.stChargeMode != MANUAL:
                # asyncio.run(plug.update())
                charger.setPower(pwrAvl, flgAllow1P)

        except:
            pass
        # print("ChargeStratEnd")
        return 0
