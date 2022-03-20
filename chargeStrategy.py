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
from astral import LocationInfo
# import pytz
import goecharger
# from django.utils import timezone
from dataclasses import dataclass


class chargeStrategy:
    limAlwaysOn = 65
    limHigh = 95
    limNorm = 95
    limLow = 100

    def calcStrategy(self, homeData, csvname, charger, myCar, pred):

        powDes = 0

        with open('/home/pi/Entwicklung/input.txt', 'r') as status:
            stChargeMode = int(status.read())

        if os.path.isfile(csvname):
            data = csv.reader(open(csvname, 'r'))
            i = 0
            for row in data:
                i = i + 1
                if i > 1:
                    if len(row) > 8:
                        SwitchActive = int(row[8])

        OFF = 0
        ON = 1
        AUTO = 2

        MANUAL = 5

        homeData.stChargeMode = stChargeMode

        flgAllow1P = False
        if stChargeMode == OFF:
            pwrAvl = 0
        if stChargeMode == ON:
            pwrAvl = 11000
        if stChargeMode >= AUTO:
            if len(pred.date_a)>0:
                timeNow_ts = pred.toTimestamp(datetime.datetime.now())
                dateDay_a_ts = [pred.toTimestamp(pred.date_a[n]) for n in range(0, len(pred.date_a))]
                minSOCVeh = interpolate.interp1d(dateDay_a_ts, pred.minSOCVeh_a)(timeNow_ts)
                maxSOCVehProdChrg = interpolate.interp1d(dateDay_a_ts, pred.maxSOCVehProdChrg_a)(timeNow_ts)
                maxSOCVehExcessChrg = interpolate.interp1d(dateDay_a_ts, pred.maxSOCVehExcessChrg_a)(timeNow_ts)
                minSOCHomeExcessCharge = interpolate.interp1d(dateDay_a_ts, pred.minSOCHome_a)(timeNow_ts)
                print("minSOC:" + str(minSOCVeh))

                if myCar.SOC > maxSOCVehExcessChrg: # above upper limit for prediction based smart charging. only charge if otherwise, power would be cut
                    if homeData.SOC > 97:
                        if int(homeData.Prod) - int(homeData.Cons_home) - pred.maxFeedIn >0:
                            pwrAvl = max(int(homeData.Prod) - int(homeData.Cons_home) - pred.maxFeedIn, 6*230+1)
                        else:
                            pwrAvl=0
                        #pwrAvl = int(homeData.Prod) - int(homeData.Cons_home) - pred.maxFeedIn
                        flgAllow1P = True
                    else:
                        pwrAvl = 0
                else:
                    if homeData.SOC >= minSOCHomeExcessCharge:
                        pwrAvlExcChrg = int(homeData.Prod) - int(homeData.Cons_home) + min(-pred.maxBattPowDischa, max((
                                homeData.SOC - minSOCHomeExcessCharge) * 500, - pred.maxBattPowChrg))
                    else:
                        if int(homeData.Prod) > int(homeData.Cons_home) and int(homeData.Batt_pow) == 0:
                            pwrAvlExcChrg = int(homeData.Prod) - int(homeData.Cons_home) -100
                        else:
                            pwrAvlExcChrg = max(0, int(homeData.Prod) - int(homeData.Cons_home) - pred.maxBattPowChrg -100)

                    if myCar.SOC > maxSOCVehProdChrg: # above upper limit for normal smart charging. charge when above minimum house SOC
                        flgAllow1P = True
                        pwrAvl = pwrAvlExcChrg

                    else:
                        if myCar.SOC > minSOCVeh: # above minimum SOC: charge when production is greater than consumption
                            pwrAvl = int(homeData.Prod) - int(homeData.Cons_home) # + max(0, min(3300, (homeData.SOC - 5) * 330))
                            pwrAvl = max(pwrAvl, pwrAvlExcChrg)
                        else:  # below min SOC: charge with full power
                            pwrAvl = 11000
            else:
                pwrAvl = 0

        try:
            if stChargeMode != MANUAL:
                # asyncio.run(plug.update())
                charger.setPower(pwrAvl, flgAllow1P)

        except:
            pass
        # print("ChargeStratEnd")
        return 0
