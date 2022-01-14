import json
import requests
import time
from datetime import datetime
from astral.sun import sun
from astral import LocationInfo
import astral
from pysolar.solar import *
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
    maxFeedIn = 4200  # maximale Einspeiseleistung W

    def __init__(self):
        self.berlin = pytz.timezone("Europe/Berlin")
        self.azimuthPV = np.array([110, 200, 290])
        self.zenithPV = np.array([35, 35, 35])
        self.pwrPeak = np.array([900, 7800, 900])
        self.qConsPerDay = 4000  # 5000Wh: 15kWh/100km * 33km
        self.hDailyCons = 13  # assume daily consumption at 12pm
        self.minSOCVehTar = 50
        self.maxSOCVehTarProdChrg = 70
        self.maxSOCVehTarExcessChrg = 90

        self.consPer100km = 15000.0  # Wh/100km
        self.anglZenithPwrDiff_a = [90, 60, 30]
        self.pwrDiff_a = [0, 0.04, 0.06]
        self.dailyConsPath = "/home/pi/Entwicklung/dailyCons.json"
        self.powProd_a = []
        self.powCons_a = []
        self.date_a = []
        self.minSOCHome_a = []
        self.maxSOCHome_a = []
        self.minSOCVeh_a = []
        self.maxSOCVehProdChrg_a = []
        self.maxSOCVehExcessChrg_a = []
        self.city = LocationInfo("Vaihingen", "Germany", "Europe/Berlin", self.latitude, self.longitude)

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
            c = c0 + rClouds * 0.5
            # print("c=" + str(c))
            E = E0 * math.exp(-c / (math.cos(zenith * 2 * math.pi / 360)))
            # print("E: " + str(E))
            pwrDiff = np.sum(interpolate.interp1d(self.anglZenithPwrDiff_a, self.pwrDiff_a)(zenith) * self.pwrPeak)
            power = np.sum(self.pwrPeak * rArea * E / E_peak) + pwrDiff

            print("power: " + str(power))
        else:
            power = 0
        return power

    def getDailyCons(self, arg_date):
        with open(self.dailyConsPath, 'r') as f:
            data = f.read()

        jDailyCons = json.loads(data)
        cons = 30 * self.consPer100km / 100
        for day in jDailyCons['consumption']:

            if arg_date.strftime("%Y-%m-%d") == day["date"]:
                date = day["date"]
                cons = float(day["km"]) * self.consPer100km / 100

        print("Day: "+str(date)+", Cons: "+str(cons))
        return cons / self.qVeh * 100

    def updateSOCLims(self):
        minSOC_Start = 100
        maxSOC_Start = 100

        n = len(self.powProd_a) - 1
        n_1 = n + 1
        self.minSOCHome_a = [0] * n_1
        self.maxSOCHome_a = [0] * n_1

        self.minSOCVeh_a = [0] * n_1
        self.maxSOCVehProdChrg_a = [0] * n_1
        self.maxSOCVehExcessChrg_a = [0] * n_1
        for i in range(n, -1, -1):
            if i == n:  # or self.date_a[i].hour == 0:
                self.minSOCHome_a[i] = minSOC_Start
                self.maxSOCHome_a[i] = maxSOC_Start

                self.minSOCVeh_a[i] = self.minSOCVehTar
                self.maxSOCVehProdChrg_a[i] = self.maxSOCVehTarProdChrg
                self.maxSOCVehExcessChrg_a[i] = self.maxSOCVehTarExcessChrg

            else:
                _prod = (self.powProd_a[i] + self.powProd_a[i + 1]) / 2
                _cons = (self.powCons_a[i] + self.powCons_a[i + 1]) / 2
                _excess = _prod - _cons

                self.minSOCHome_a[i] = self.minSOCHome_a[i + 1] - _excess / self.qBatt * 100
                _qExcess = -min(0, self.minSOCHome_a[i] * self.qBatt / 100)
                self.minSOCHome_a[i] = min(100, max(0, self.minSOCHome_a[i]))

                self.maxSOCHome_a[i] = self.maxSOCHome_a[i + 1] - (_excess - self.maxFeedIn) / self.qBatt * 100
                _qCutOff = -min(0, self.maxSOCHome_a[i] * self.qBatt / 100)
                self.maxSOCHome_a[i] = min(100, max(0, self.maxSOCHome_a[i]))

                self.minSOCVeh_a[i] = self.minSOCVeh_a[i + 1] - max(0, _excess) / self.qVeh * 100
                self.maxSOCVehProdChrg_a[i] = self.maxSOCVehProdChrg_a[i + 1] - _qExcess / self.qVeh * 100
                self.maxSOCVehExcessChrg_a[i] = self.maxSOCVehExcessChrg_a[i + 1] - _qCutOff / self.qVeh * 100

                if self.date_a[i].hour == self.hDailyCons:
                    deltaSOC = self.getDailyCons(self.date_a[i])
                    print("deltaSOC: "+str(deltaSOC))
                    self.minSOCVeh_a[i] += deltaSOC
                    self.maxSOCVehProdChrg_a[i] += deltaSOC
                    self.maxSOCVehExcessChrg_a[i] += deltaSOC

                self.minSOCVeh_a[i] = min(80, self.minSOCVeh_a[i])
                self.maxSOCVehProdChrg_a[i] = min(90, self.maxSOCVehProdChrg_a[i])
                self.maxSOCVehExcessChrg_a[i] = min(100, self.maxSOCVehExcessChrg_a[i])

                self.minSOCVeh_a[i] = max(50, self.minSOCVeh_a[i])
                self.maxSOCVehProdChrg_a[i] = max(40, self.maxSOCVehProdChrg_a[i])
                self.maxSOCVehExcessChrg_a[i] = max(30, self.maxSOCVehExcessChrg_a[i])

            # print(self.date_a[i])
            # print("min: " + str(self.minSOC_a[i]) + " / max:" + str(self.maxSOC_a[i]))

    def updatePrediction(self):
        self.powProd_a = []
        self.powCons_a = []
        self.date_a = []
        # s = sun(city.observer, date=datetime.date.today())
        response = requests.get(
            "http://api.openweathermap.org/data/2.5/onecall?lat=48.9805&lon=8.98356&exclude=minutely&appid=d2d5732789261d036171254607f31898")

        for myhour in response.json()['hourly']:
            date_simpl = datetime.datetime.fromtimestamp(myhour["dt"])

            date = self.berlin.localize(date_simpl)
            self.date_a.append(date_simpl)

            # print(get_altitude(latitude, longitude, date))
            # print(get_azimuth(latitude, longitude, date))
            # print('Zeit: ' + str(datetime.datetime.fromtimestamp(myhour["dt"])))

            tEnv = myhour["temp"] - 273.15
            # print('temp: ' + str(tEnv))
            rClouds = myhour["clouds"] / 100
            # print('wolken: ' + str(rClouds))
            powProd = self.getPower(date, rClouds)
            powCons = self.getPowCons(tEnv, rClouds, date)
            self.powProd_a.append(powProd)
            print("Power produced: " + str(powProd))
            print("Power consumed: " + str(powCons))
            self.powCons_a.append(powCons)
            print("------------------------------------------")
        # self.updateSOCLims()
        dateDay_a = []
        rCloudsDay_a = []
        tDay_a = []
        for days in response.json()['daily']:
            date_simpl = datetime.datetime.fromtimestamp(days["dt"])
            date = self.berlin.localize(date_simpl)
            dateDay_a.append(date - datetime.timedelta(hours=6))
            dateDay_a.append(date)
            dateDay_a.append(date + datetime.timedelta(hours=6))
            dateDay_a.append(date + datetime.timedelta(hours=12))
            print(days["temp"]["eve"])
            tDay_a.append(days["temp"]["morn"] - 273.15)
            tDay_a.append(days["temp"]["day"] - 273.15)
            tDay_a.append(days["temp"]["eve"] - 273.15)
            tDay_a.append(days["temp"]["night"] - 273.15)
            rClouds = days["clouds"] / 100
            for i in range(0, 4):
                rCloudsDay_a.append(rClouds)

        timeExtrpDays = self.berlin.localize(self.date_a[-1]) + datetime.timedelta(hours=1)
        # endDate = dateDay_a[-1] + datetime.timedelta(hours=11)
        # ti = [pd.to_datetime(d) for d in self.Time_a]
        dateDay_a_ts = [self.toTimestamp(dateDay_a[n]) for n in range(0, len(dateDay_a))]
        while timeExtrpDays < dateDay_a[-1]:
            timeExtrpDays = timeExtrpDays + datetime.timedelta(hours=1)
            timeExtrpDays_ts = self.toTimestamp(timeExtrpDays)
            self.date_a.append(timeExtrpDays)
            tempRClouds = interpolate.interp1d(dateDay_a_ts, rCloudsDay_a)(timeExtrpDays_ts)
            temptEnv = interpolate.interp1d(dateDay_a_ts, tDay_a)(timeExtrpDays_ts)
            powProd = self.getPower(timeExtrpDays, tempRClouds)
            powCons = self.getPowCons(temptEnv, tempRClouds, timeExtrpDays)
            self.powProd_a.append(powProd)
            self.powCons_a.append(powCons)

        #self.updateSOCLims()

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
