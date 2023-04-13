import json
import requests
import time
from datetime import datetime

import datetime
import pytz
from scipy import interpolate
import numpy as np
import math
from astral.location import Location, LocationInfo


class PredictionClass:
    latitude = 48.9805
    longitude = 8.98356
    qBatt = 8000  # Batteriekapazität Hausbattereie 8kWh
    qVeh = 34000
    maxBattPowDischa = -3300
    maxBattPowChrg = 3300
    maxPowInv_C = 7000
    maxFeedIn = 4200  # maximale Einspeiseleistung W

    def __init__(self):
        self.berlin = pytz.timezone("Europe/Berlin")
        self.azimuthPV = np.array([118, 208, 298])
        self.zenithPV = np.array([35, 35, 35])
        self.pwrPeak = np.array([900, 7800, 900])
        self.qConsPerDay = 4000  # 5000Wh: 15kWh/100km * 33km
        self.hDailyCons = 8  # assume daily consumption at 12pm
        self.minSOCVehTar = 50
        self.maxSOCVehTarProdChrg = 70
        self.maxSOCVehTarExcessChrg = 95

        self.consPer100km = 15000.0  # Wh/100km
        self.anglZenithPwrDiff_a = [90, 60, 30, 0]
        self.pwrDiff_a = [0, 0.04, 0.06, 0.07]
        self.dailyConsPath = "/home/pi/Entwicklung/dailyCons.json"
        self.powProd_a = []
        self.powProdLow_a = []
        self.powCons_a = []
        self.date_a = []
        self.minSOCHome_a = []
        self.minSOCHomeLowProd_a = []
        self.minSOCHome_C = 4
        self.maxSOCHome_a = []
        self.minSOCVeh_a = []
        self.maxSOCVehProdChrg_a = []
        self.maxSOCVehExcessChrg_a = []
        self.city = LocationInfo("Vaihingen", "Germany", "Europe/Berlin", self.latitude, self.longitude)
        self.date_predHomeSOC_a = []
        self.predHomeSOC_a = []
        self.jDailyCons=[]

    def getPower(self, date, rClouds):
        azimuth = Location(self.city).solar_azimuth(date)
        zenith = 90 - Location(self.city).solar_elevation(date)
        # print("azimuth: " + str(azimuth) + " / zenith: " + str(zenith))
        if zenith < 90:
            alpha = (azimuth - self.azimuthPV) * 2 * math.pi / 360
            beta = (zenith - self.zenithPV) * 2 * math.pi / 360
            rArea = np.maximum(0.0, np.cos(alpha)) * np.maximum(0.0, np.cos(beta))
            # print("rArea:" + str(rArea))
            c0 = 0.208
            E0 = 1368.0
            E_peak = 1061
            c = c0 + rClouds * 0.63
            # print("c=" + str(c))
            E = E0 * math.exp(-c / (math.cos(zenith * 2 * math.pi / 360)))
            #print("E: " + str(E))
            #print("zenith:" + str(zenith))
            try:
                pwrDiff = np.sum(interpolate.interp1d(self.anglZenithPwrDiff_a, self.pwrDiff_a)(zenith) * self.pwrPeak) # diffuse power
            except Exception as e:
                print(e)
            power = np.sum(self.pwrPeak * rArea * E / E_peak) + pwrDiff
            power = np.clip(power, 0, self.maxPowInv_C)
            # print("power: " + str(power))
        else:
            power = 0
        return power



    def updateSOCLims(self, home):
        minSOC_Start = 100
        maxSOC_Start = 100
        i = 0
        self.loadDailyCons()
        self.date_predHomeSOC_a = []
        self.predHomeSOC_a = []
        self.date_predHomeSOC_a.append(self.berlin.localize(datetime.datetime.now()))
        self.predHomeSOC_a.append(home.SOC)
        if len(self.date_a) > 0:

            date_a_ts = [self.toTimestamp(self.date_a[n]) for n in range(0, len(self.date_a))]
            while self.date_predHomeSOC_a[i].day == datetime.datetime.now().day:
                i = i + 1
                self.date_predHomeSOC_a.append(self.date_predHomeSOC_a[-1] + datetime.timedelta(minutes=1))

                _dt_in_h = 1 / 60
                _excess = _dt_in_h * (interpolate.interp1d(date_a_ts, self.powProd_a)(
                    self.toTimestamp(self.date_predHomeSOC_a[-1])) - interpolate.interp1d(date_a_ts, self.powCons_a)(
                    self.toTimestamp(self.date_predHomeSOC_a[-1])))
                _excess = max(self.maxBattPowDischa * _dt_in_h, min(self.maxBattPowChrg * _dt_in_h, _excess))
                self.predHomeSOC_a.append(self.predHomeSOC_a[-1] + _excess / self.qBatt * 100)
                self.predHomeSOC_a[-1] = min(100, max(0, self.predHomeSOC_a[-1]))

        n = len(self.powProd_a) - 1
        n_1 = n + 1
        self.minSOCHome_a = [0] * n_1
        self.minSOCHomeLowProd_a = [0] * n_1
        self.maxSOCHome_a = [0] * n_1

        self.minSOCVeh_a = [0] * n_1
        self.maxSOCVehProdChrg_a = [0] * n_1
        self.maxSOCVehExcessChrg_a = [0] * n_1
        date_predHomeSOC_a_ts = [self.toTimestamp(self.date_predHomeSOC_a[n]) for n in
                                 range(0, len(self.date_predHomeSOC_a))]
        for i in range(n, -1, -1):
            if i == n:  # or self.date_a[i].hour == 0:
                self.minSOCHome_a[i] = minSOC_Start
                self.minSOCHomeLowProd_a[i] = minSOC_Start

                self.maxSOCHome_a[i] = maxSOC_Start

                self.minSOCVeh_a[i] = self.minSOCVehTar
                self.maxSOCVehProdChrg_a[i] = self.maxSOCVehTarProdChrg
                self.maxSOCVehExcessChrg_a[i] = self.maxSOCVehTarExcessChrg

            else:
                __timediff = self.date_a[i + 1] - self.date_a[i]
                __dt_in_h = __timediff.total_seconds() / 3600
                # print("timediff in h: "+str(__timediff_in_h))
                _prod = (self.powProd_a[i] + self.powProd_a[i + 1]) / 2 * __dt_in_h
                _prodLow = (self.powProdLow_a[i] + self.powProdLow_a[i + 1]) / 2 * __dt_in_h
                _cons = (self.powCons_a[i] + self.powCons_a[i + 1]) / 2 * __dt_in_h
                _qExcess = _prod - _cons
                _qExcessLow = _prodLow - _cons
                _qExcessLim = max(self.maxBattPowDischa * __dt_in_h,
                                  min(self.maxBattPowChrg * __dt_in_h, _qExcess) * 0.9)
                _qExcessLimLow = max(self.maxBattPowDischa * __dt_in_h,
                                  min(self.maxBattPowChrg * __dt_in_h, _qExcessLow) * 0.9)
                _qExcessOvrBattLim = max(0, _qExcess - _qExcessLim)

                self.minSOCHome_a[i] = self.minSOCHome_a[i + 1] - _qExcessLim / self.qBatt * 100
                self.minSOCHomeLowProd_a[i] = self.minSOCHomeLowProd_a[i + 1] - _qExcessLimLow / self.qBatt * 100

                _qExcessBatt = -min(0, (self.minSOCHome_a[i] - self.minSOCHome_C) * self.qBatt / 100) + _qExcessOvrBattLim
                if (Location(self.city).solar_elevation(self.date_a[i]) > 0) and (Location(self.city).solar_elevation(
                        self.date_a[i + 1]) <= 0):
                    self.minSOCHome_a[i] = 100 # reset SOC to max at sunset
                    self.minSOCHomeLowProd_a[i] = 100 # reset SOC to max at sunset

                self.minSOCHome_a[i] = min(97, max(self.minSOCHome_C, self.minSOCHome_a[i]))
                self.minSOCHomeLowProd_a[i] = min(97, max(self.minSOCHome_C, self.minSOCHomeLowProd_a[i]))

                self.maxSOCHome_a[i] = self.maxSOCHome_a[i + 1] - (
                        _qExcess - self.maxFeedIn * __dt_in_h) / self.qBatt * 100
                _qCutOff = max(0, (_prod - _cons - self.maxFeedIn * __dt_in_h))
                self.maxSOCHome_a[i] = min(100, max(0, self.maxSOCHome_a[i]))
                if self.date_predHomeSOC_a[-1] > self.date_a[i] > self.date_predHomeSOC_a[0]:
                    _homeSOCPred = interpolate.interp1d(date_predHomeSOC_a_ts, self.predHomeSOC_a)(
                        self.toTimestamp(self.date_a[i]))
                    if _homeSOCPred.mean() < 99:
                        _qCutOff = 0
                    else:
                        _qCutOff = _qCutOff
                deltaSOC, __flgPlannedTrip, __flgVehAway = self.getDailyCons(self.date_a[i], self.date_a[i + 1])
                if not __flgVehAway:
                    self.minSOCVeh_a[i] = self.minSOCVeh_a[i + 1] - max(0, _qExcess) / self.qVeh * 100
                    self.maxSOCVehProdChrg_a[i] = self.maxSOCVehProdChrg_a[i + 1] - _qExcessBatt / self.qVeh * 100
                    self.maxSOCVehExcessChrg_a[i] = self.maxSOCVehExcessChrg_a[i + 1] - _qCutOff / self.qVeh * 100
                else:
                    self.minSOCVeh_a[i] = self.minSOCVeh_a[i+1]
                    self.maxSOCVehProdChrg_a[i] = self.maxSOCVehProdChrg_a[i+1]
                    self.maxSOCVehExcessChrg_a[i] = self.maxSOCVehExcessChrg_a[i+1]


                #if self.date_a[i].hour == self.hDailyCons and self.date_a[i + 1].hour > self.hDailyCons:  # first time hour matches configured time (if hDailyCons= 13, then 13:55

                self.minSOCVeh_a[i] += deltaSOC
                self.maxSOCVehProdChrg_a[i] += deltaSOC
                self.maxSOCVehExcessChrg_a[i] += deltaSOC

                if __flgPlannedTrip:
                    self.minSOCVeh_a[i] = self.lim(self.minSOCVeh_a[i], 50, max(80, min(100, 15 + deltaSOC)))
                    self.maxSOCVehProdChrg_a[i] = self.lim(self.maxSOCVehProdChrg_a[i], 15, max(80, min(100, 15 + deltaSOC)))
                    self.maxSOCVehExcessChrg_a[i] = self.lim(self.maxSOCVehExcessChrg_a[i], 45, 100)
                else:
                    self.minSOCVeh_a[i] = self.lim(self.minSOCVeh_a[i], 50, max(80, self.minSOCVeh_a[i+1]))
                    self.maxSOCVehProdChrg_a[i] = self.lim(self.maxSOCVehProdChrg_a[i], 15, max(85, self.maxSOCVehProdChrg_a[i+1]))
                    self.maxSOCVehExcessChrg_a[i] = self.lim(self.maxSOCVehExcessChrg_a[i], 45, max(100, self.maxSOCVehExcessChrg_a[i+1]))


            # print(self.date_a[i])
            # print("min: " + str(self.minSOC_a[i]) + " / max:" + str(self.maxSOC_a[i]))

    def loadDailyCons(self):
        with open(self.dailyConsPath, 'r') as f:
            data = f.read()
        self.jDailyCons = json.loads(data)

    def getDailyCons(self, arg_date, arg_dateOld):
        cons = 0
        __foundTripOnDate = False
        __flgPlannedTrip = False
        __flgVehAway = False
        for day in self.jDailyCons['consumption']:
            try:
                jsonStrtDate = datetime.datetime.strptime(day["date"] + " " + day["StartTime"], '%Y-%m-%d %H:%M')
                jsonEndDate = datetime.datetime.strptime(day["date"] + " " + day["EndTime"], '%Y-%m-%d %H:%M')
            except Exception as e:
                print(e)
            jsonStrtDateLoc = self.berlin.localize(jsonStrtDate)
            jsonEndDateLoc = self.berlin.localize(jsonEndDate)
            if jsonStrtDateLoc.day == arg_date.day:
                __foundTripOnDate = True
            if arg_date <= jsonStrtDateLoc < arg_dateOld:
                cons = float(day["km"]) * self.consPer100km / 100
                __flgPlannedTrip = True
            if jsonStrtDateLoc < arg_date < jsonEndDateLoc:
                __flgVehAway = True
        if (not __foundTripOnDate) and arg_date.hour == self.hDailyCons and arg_dateOld.hour > self.hDailyCons:
            cons = 0.12 * self.consPer100km
        # print("Day: "+str(date)+", Cons: "+str(cons))
        return (cons / self.qVeh * 100, __flgPlannedTrip, __flgVehAway)

    def isPluggedIn(self, date):
        a=1

    def lim(self, val, lowLim, upLim):
        return min(upLim, max(lowLim, val))

    def updatePrediction(self):
        self.powProd_a = []
        self.powProdLow_a = []
        self.powCons_a = []
        self.date_a = []
        __Date_a = []
        __TEnv_a = []
        __RClouds_a = []

        # s = sun(city.observer, date=datetime.date.today())
        response = requests.get(
            "http://api.openweathermap.org/data/2.5/onecall?lat=48.9805&lon=8.98356&exclude=minutely&appid=d2d5732789261d036171254607f31898")

        for myhour in response.json()['hourly']:
            date_simpl = datetime.datetime.fromtimestamp(myhour["dt"])

            date = self.berlin.localize(date_simpl)
            __Date_a.append(date)

            __tEnv = myhour["temp"] - 273.15
            # print('temp: ' + str(tEnv))
            __rClouds = myhour["clouds"] / 100
            # print('wolken: ' + str(rClouds))
            __RClouds_a.append(__rClouds)
            __TEnv_a.append(__tEnv)

        for days in response.json()['daily']:
            date_simpl = datetime.datetime.fromtimestamp(days["dt"])
            date = self.berlin.localize(date_simpl)
            dateTmp = date - datetime.timedelta(hours=6)
            if dateTmp > __Date_a[-1]:
                __Date_a.append(dateTmp)
                __TEnv_a.append(days["temp"]["morn"] - 273.15)
                __RClouds_a.append(days["clouds"] / 100)
            dateTmp = date
            if dateTmp > __Date_a[-1]:
                __Date_a.append(dateTmp)
                __TEnv_a.append(days["temp"]["day"] - 273.15)
                __RClouds_a.append(days["clouds"] / 100)
            dateTmp = date + datetime.timedelta(hours=6)
            if dateTmp > __Date_a[-1]:
                __Date_a.append(dateTmp)
                __TEnv_a.append(days["temp"]["eve"] - 273.15)
                __RClouds_a.append(days["clouds"] / 100)
            dateTmp = date + datetime.timedelta(hours=12)
            if dateTmp > __Date_a[-1]:
                __Date_a.append(dateTmp)
                __TEnv_a.append(days["temp"]["night"] - 273.15)
                __RClouds_a.append(days["clouds"] / 100)#

        print(__Date_a)
        timeExtrpDays = __Date_a[0]

        dateDay_a_ts = [self.toTimestamp(__Date_a[n]) for n in range(0, len(__Date_a))]
        while timeExtrpDays <= __Date_a[-1]:
            timeExtrpDays_ts = self.toTimestamp(timeExtrpDays)
            # print("test0")
            tempRClouds = interpolate.interp1d(dateDay_a_ts, __RClouds_a)(timeExtrpDays_ts)
            # print("test1")
            temptEnv = interpolate.interp1d(dateDay_a_ts, __TEnv_a)(timeExtrpDays_ts)
            # print("test2")
            powProd = self.getPower(timeExtrpDays, tempRClouds)
            # print("test3")
            powCons = self.getPowCons(temptEnv, tempRClouds, timeExtrpDays)
            # print("test4")
            self.powProd_a.append(powProd)
            self.powProdLow_a.append(powProd/2)

            self.powCons_a.append(powCons)

            self.date_a.append(timeExtrpDays)
            timeExtrpDays = timeExtrpDays + datetime.timedelta(minutes=5)
            # print(timeExtrpDays)
            # print(timeExtrpDays_ts)
        # print(self.date_a)
        # print(__Date_a)

    def toTimestamp(self, d):
        return d.timestamp()

    def getPowCons(self, tEnv, rClouds, date):

        if tEnv < 20:
            power = max(300, min(1000, (tEnv - 7) * -166 + 1500))  # ramp from 1500 to 500 between 7 and 13 deg
        else:
            power = max(300, min(1200, (tEnv - 25) * 200 + 500))  # ramp from 500 to 1500 between 25 and 30 deg

        if 6 < date.hour < 22:
            power = power + 300

        return power
