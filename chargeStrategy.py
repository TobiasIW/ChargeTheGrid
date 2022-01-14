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
        HIGH_PRIO = 2
        NORMAL = 3
        LOW_PRIO = 4
        MANUAL = 5
        AUTO = 6

        homeData.stChargeMode = stChargeMode

        print("ChargeMode:" + str(stChargeMode))
        # if stChargeMode == AUTO:
        #     homeData.flgAuto = 1
        #     city = LocationInfo("Vaihingen", "Germany", "Europe/Berlin", 48.5, 8.5)
        #
        #     s = sun(city.observer, date=datetime.date.today())
        #
        #     if datetime.datetime.now(utc) < (s["sunrise"]) + datetime.timedelta(hours=2):
        #         stChargeMode = LOW_PRIO
        #         print(" before sunrise +2")
        #     else:
        #         if (datetime.datetime.now(utc) <= (s["noon"] + datetime.timedelta(hours=1))):
        #             stChargeMode = HIGH_PRIO
        #             print(" before noon+1")
        #         else:
        #             if (datetime.datetime.now(utc) < s["sunset"]):
        #                 stChargeMode = NORMAL
        #                 print("after noon")
        #
        #             else:
        #                 stChargeMode = LOW_PRIO
        #                 print("after sunset")
        # else:
        #     flgAuto = 0
        flgAllow1P = False
        if stChargeMode == OFF:
            pwrAvl = 0
        if stChargeMode == ON:
            pwrAvl = 11000
        if stChargeMode >= HIGH_PRIO:
            timeNow_ts = pred.toTimestamp(datetime.datetime.now())
            dateDay_a_ts = [pred.toTimestamp(pred.date_a[n]) for n in range(0, len(pred.date_a))]
            minSOCVeh = interpolate.interp1d(dateDay_a_ts, pred.minSOCVeh_a)(timeNow_ts)
            maxSOCVehProdChrg = interpolate.interp1d(dateDay_a_ts, pred.maxSOCVehProdChrg_a)(timeNow_ts)
            maxSOCVehExcessChrg = interpolate.interp1d(dateDay_a_ts, pred.maxSOCVehExcessChrg_a)(timeNow_ts)
            minSOCHomeExcessCharge = interpolate.interp1d(dateDay_a_ts, pred.minSOCHome_a)(timeNow_ts)
            print("minSOC:" + str(minSOCVeh))

            if myCar.SOC > maxSOCVehExcessChrg:
                if homeData.SOC > 97:
                    pwrAvl = int(homeData.Prod) - int(homeData.Cons_home) - pred.maxFeedIn
                    flgAllow1P = True
                else:
                    pwrAvl = 0
            else:
                if myCar.SOC > maxSOCVehProdChrg:
                    flgAllow1P = True
                    pwrAvl = int(homeData.Prod) - int(homeData.Cons_home) + min(3300, (
                            homeData.SOC - minSOCHomeExcessCharge - 1) * 500)
                    if homeData.SOC == 0:
                        flgAllow1P = True
                else:
                    if myCar.SOC > minSOCVeh:
                        pwrAvl = int(homeData.Prod) - int(homeData.Cons_home) # + max(0, min(3300, (homeData.SOC - 5) * 330))
                    else:  # below min SOC: charge with full power
                        pwrAvl = 11000

        try:
            if stChargeMode != MANUAL:
                # asyncio.run(plug.update())
                charger.setPower(pwrAvl, flgAllow1P)

        except:
            pass
        print("ChargeStratEnd")
        return 0
