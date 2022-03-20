import csv
import matplotlib.pyplot as plt
import pandas as pd
import asyncio
from kasa import SmartPlug
import os.path
import time
import datetime
import pytz



class visualizationClass:
    csvname = "/home/pi/Entwicklung/bat_stats.csv"
    exec_delta = 1 / 60  # time between scheduled execution in h
    x = []

    SOC_a = []
    Prod_a = []
    Cons_a = []
    ConsHome_a = []
    Batt_pow_a = []
    GridFeedIn_pow_a = []
    OperatingMode_a = []
    SystemStatus_a = []
    Time_a = []
    Consumption = []
    Production = []
    FeedIn = []
    Grid_Consumption = []
    Charge = []
    Discharge = []
    SwitchActive_a = []
    stChargeMode_a = []
    flgAuto_a = []
    Car_SOC_a = []



    def readVal(self, Attr):

        with open(self.csvname, mode='r') as csvfile:
            csv_reader = csv.DictReader(csvfile)

            i = 0
            retVal = 0
            for row in csv_reader:
                i += 1
                if i > 1:  # first line has header
                    retVal = float(row[Attr])  # use last one only
        return retVal

    def writeCSV(self, homeData, charger, myCar):
        with open(self.csvname, 'a', newline='') as csvfile:
            fieldnames = ['SOC', 'Prod', 'Cons', 'Batt_pow', 'GridFeedIn_pow', 'OperatingMode', 'CarStatus',
                          'TimeStamp', 'newValueSOCCar', 'Mode', 'flgAuto', 'Cons_Home', 'SOC_Car']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(
                {'SOC': homeData.SOC, 'Prod': homeData.Prod, 'Cons': homeData.Cons, 'Batt_pow': homeData.Batt_pow,
                 'GridFeedIn_pow': homeData.GridFeedIn_pow, 'OperatingMode': homeData.OperatingMode,
                 'flgAuto': homeData.flgAuto, 'CarStatus': charger.state, 'TimeStamp': homeData.TimeStamp,
                 'newValueSOCCar': myCar.newValue, 'Mode': homeData.stChargeMode, 'Cons_Home': homeData.Cons_home,
                 'SOC_Car': myCar.SOC})
            data = csv.reader(open(self.csvname, 'r'))

            i = len(self.x) - 1#

            self.SOC_a.append(homeData.SOC)
            self.Prod_a.append(homeData.Prod)
            self.Cons_a.append(homeData.Cons)
            self.Batt_pow_a.append(homeData.Batt_pow)
            self.GridFeedIn_pow_a.append(homeData.GridFeedIn_pow)
            self.OperatingMode_a.append(homeData.OperatingMode)
            self.SystemStatus_a.append(charger.state)

            self.Time_a.append(self.berlin.localize(pd.to_datetime(homeData.TimeStamp)))
            if self.GridFeedIn_pow_a[i] > 0:
                self.FeedIn_pow = self.GridFeedIn_pow_a[i]
                self.Grid_Consumption_pow = 0
            else:
                self.FeedIn_pow = 0
                self.Grid_Consumption_pow = -self.GridFeedIn_pow_a[i]

            if i > 2:
                time_delta = self.Time_a[-1] - self.Time_a[-2]
                self.exec_delta = (time_delta.total_seconds() / 3600)
                self.Consumption.append(self.Consumption[- 1] + self.Cons_a[-1]  * self.exec_delta / 1000)
                self.Production.append(self.Production[- 1] + self.Prod_a[-1] * self.exec_delta / 1000)
                self.FeedIn.append(self.FeedIn[- 1] + self.FeedIn_pow * self.exec_delta / 1000)
                self.Grid_Consumption.append(self.Grid_Consumption[-1] + self.Grid_Consumption_pow * self.exec_delta / 1000)

            else:
                self.Consumption.append(homeData.Cons * self.exec_delta / 1000)
                self.Production.append(homeData.Prod * self.exec_delta / 1000)
                self.FeedIn.append(self.FeedIn_pow * self.exec_delta / 1000)
                self.Grid_Consumption.append(self.Grid_Consumption_pow * self.exec_delta / 1000)
            self.newValueSOCCar_a.append(myCar.newValue)
            self.stChargeMode_a.append(homeData.stChargeMode)
            self.flgAuto_a.append(homeData.flgAuto)
            self.ConsHome_a.append(homeData.Cons_home)  # int(row[10]))
            self.Car_SOC_a.append(myCar.SOC)

            self.x.append(i)

    def clear(self):
        self.x = []
        self.SOC_a = []
        self.Prod_a = []
        self.Cons_a = []
        self.ConsHome_a = []
        self.Batt_pow_a = []
        self.GridFeedIn_pow_a = []
        self.OperatingMode_a = []
        self.SystemStatus_a = []
        self.Time_a = []
        self.Consumption = []
        self.Production = []
        self.FeedIn = []
        self.Grid_Consumption = []
        self.Charge = []
        self.Discharge = []
        self.newValueSOCCar_a = []
        self.stChargeMode_a = []
        self.flgAuto_a = []
        self.Car_SOC_a = []
        self.FeedIn_pow = []

    def __init__(self):
        self.clear()
        self.berlin = pytz.timezone("Europe/Berlin")
        data = csv.reader(open(self.csvname, 'r'))
        i = 0
        for row in data:
            i = i + 1
            if i > 1:

                self.SOC_a.append(int(row[0]))
                self.Prod_a.append(int(row[1]))
                self.Cons_a.append(int(row[2]))
                self.Batt_pow_a.append(int(row[3]))
                self.GridFeedIn_pow_a.append(int(row[4]))
                self.OperatingMode_a.append(int(row[5]))
                self.SystemStatus_a.append(row[6])
                self.Time_a.append(self.berlin.localize(pd.to_datetime(row[7])))
                if self.GridFeedIn_pow_a[i - 2] > 0:
                    self.FeedIn_pow = self.GridFeedIn_pow_a[i - 2]
                    self.Grid_Consumption_pow = 0
                else:
                    self.FeedIn_pow = 0
                    self.Grid_Consumption_pow = -self.GridFeedIn_pow_a[i - 2]

                if i > 2:
                    time_delta = self.Time_a[i - 2] - self.Time_a[i - 3]
                    self.exec_delta = (time_delta.total_seconds() / 3600)
                    self.Consumption.append(self.Consumption[i - 3] + (
                            self.Cons_a[i - 2] + self.Cons_a[i - 3]) / 2 * self.exec_delta / 1000)
                    self.Production.append(
                        self.Production[i - 3] + (self.Prod_a[i - 2] + self.Prod_a[i - 2]) / 2 * self.exec_delta / 1000)
                    self.FeedIn.append(self.FeedIn[i - 3] + self.FeedIn_pow * self.exec_delta / 1000)
                    self.Grid_Consumption.append(
                        self.Grid_Consumption[i - 3] + self.Grid_Consumption_pow * self.exec_delta / 1000)

                else:
                    self.Consumption.append(int(row[2]) * self.exec_delta / 1000)
                    self.Production.append(int(row[1]) * self.exec_delta / 1000)
                    self.FeedIn.append(self.FeedIn_pow * self.exec_delta / 1000)
                    self.Grid_Consumption.append(self.Grid_Consumption_pow * self.exec_delta / 1000)
                self.newValueSOCCar_a.append(int(row[8]))
                self.stChargeMode_a.append(int(row[9]))
                self.flgAuto_a.append(int(row[10]))
                self.ConsHome_a.append(int(row[11]))  # int(row[10]))
                self.Car_SOC_a.append(float(row[12]))

                self.x.append(i)

    def plotData(self, pred):
        i = len(self.x)
        ti = [pd.to_datetime(d) for d in self.Time_a]
        # print(ti)
        # defining subplots and their positions
        #fig = plt.figure(figsize=(18, 15))
        plt1 = plt.subplot2grid((34, 4), (0, 0), rowspan=8, colspan=2)
        plt2 = plt.subplot2grid((34, 4), (10, 0), rowspan=5, colspan=2)
        plt3 = plt.subplot2grid((34, 4), (17, 0), rowspan=6, colspan=2)
        plt4 = plt.subplot2grid((34, 4), (25, 0), rowspan=1, colspan=2)
        plt5 = plt.subplot2grid((34, 4), (28, 0), rowspan=2, colspan=2)
        plt6 = plt.subplot2grid((34, 4), (32, 0), rowspan=2, colspan=2)
        plt1_2 = plt.subplot2grid((34, 4), (0, 2), rowspan=8, colspan=2)
        plt2_2 = plt.subplot2grid((34, 4), (10, 2), rowspan=5, colspan=2)
        plt.subplots_adjust(hspace=2, wspace=0)


        # plotting the points
        __endofday = datetime.datetime.now().replace(hour=23, minute=59, second=59)
        if len(pred.date_a) > 0:
            __endpred = pred.date_a[-1]
        else:
            __endpred = __endofday
        plt1.set_ylim(-5000, 10000)
        plt1.set_xlim(ti[0], __endofday)

        plt1_2.set_ylim(-5000, 10000)
        plt1_2.set_xlim(__endofday, __endpred)
        # plt1_2.yticks([-5000, -2500, 0, 2500, 5000, 7500, 10000], "")

        plt2.set_ylim(0, 101)
        plt2.set_xlim(ti[0], __endofday)

        plt2_2.set_ylim(0, 101)
        plt2_2.set_xlim(__endofday, __endpred)
        # plt2_2.yticks([0, 50, 100], "")

        plt3.set_xlim(ti[0], __endofday)

        plt4.set_ylim(-0.1, 3.1)
        plt4.set_xlim(ti[0], __endofday)

        plt5.set_ylim(-0.1, 5.1)
        plt5.set_xlim(ti[0], __endofday)

        plt6.set_xlim(ti[0], __endofday)

        plt1.plot(ti, self.Cons_a, label="Verbrauch", linewidth="0.5")
        plt1.plot(ti, self.Prod_a, label="Produktion", linewidth="0.5")
        plt1.plot(ti, self.Batt_pow_a, label="Laden(-)/Entladen(+)", linewidth="0.5")
        plt1.plot(ti, self.GridFeedIn_pow_a, label="Einspeisung(+)/Bezug(-)", linewidth="0.5")
        plt1.plot(ti, self.ConsHome_a, label="Verbr. o. WB", linewidth="0.5")
        plt1.plot(pred.date_a, pred.powProd_a, 'tab:brown', label="präd. Produktion", linewidth="0.5")
        plt1.plot(pred.date_a, pred.powCons_a, 'm', label="präd. Verbrauch", linewidth="0.5")
        plt1_2.plot(pred.date_a, pred.powProd_a, 'tab:brown', label="präd. Produktion", linewidth="0.5")
        plt1_2.plot(pred.date_a, pred.powCons_a, 'm', label="präd. Verbrauch", linewidth="0.5")

        plt2.plot(ti, self.SOC_a, label="SOC", linewidth="0.5")
        plt2.plot(ti, self.Car_SOC_a, label="SOC_Auto", linewidth="0.5")
        plt2.plot(pred.date_a, pred.minSOCHome_a, '--', label="min. SOC Haus", linewidth="0.5")
        plt2.plot(pred.date_a, pred.maxSOCHome_a, '--', label="max. SOC Haus", linewidth="0.5")
        plt2.plot(pred.date_a, pred.minSOCVeh_a, '--', label="Min SOC Veh High Prio", linewidth="0.5")
        plt2.plot(pred.date_a, pred.maxSOCVehProdChrg_a, '--', label="Min SOC Veh Überschuss", linewidth="0.5")
        plt2.plot(pred.date_a, pred.maxSOCVehExcessChrg_a, '--', label="Min SOC Veh Abriegeln", linewidth="0.5")

        plt2.annotate("{:10.0f}".format(self.SOC_a[i - 2]) + "%", xy=(ti[i - 2], self.SOC_a[i - 2]),
                      horizontalalignment="right")
        plt2.annotate("{:10.0f}".format(self.Car_SOC_a[i - 2]) + "%", xy=(ti[i - 2], self.Car_SOC_a[i - 2]),
                      horizontalalignment="right")

        plt2_2.plot(pred.date_a, pred.minSOCHome_a, '--', label="min. SOC Haus")
        plt2_2.plot(pred.date_a, pred.maxSOCHome_a, '--', label="max. SOC Haus")
        plt2_2.plot(pred.date_a, pred.minSOCVeh_a, '--', label="Min SOC Veh High Prio")
        plt2_2.plot(pred.date_a, pred.maxSOCVehProdChrg_a, '--', label="Min SOC Veh Überschuss")
        plt2_2.plot(pred.date_a, pred.maxSOCVehExcessChrg_a, '--', label="Min SOC Veh Abriegeln")

        plt3.plot(ti, self.Consumption, label="Verbrauch")
        plt3.plot(ti, self.Production, label="Produktion")
        plt3.plot(ti, self.FeedIn, label="Einspeisung")
        plt3.plot(ti, self.Grid_Consumption, label="Bezug")
        plt3.annotate("{:10.1f}".format(self.Consumption[i - 2]) + " kWh", xy=(ti[i - 2], self.Consumption[i - 2]),
                      horizontalalignment="right")
        plt3.annotate("{:10.1f}".format(self.Production[i - 2]) + " kWh", xy=(ti[i - 2], self.Production[i - 2]),
                      horizontalalignment="right")
        plt3.annotate("{:10.1f}".format(self.FeedIn[i - 2]) + " kWh", xy=(ti[i - 2], self.FeedIn[i - 2]),
                      horizontalalignment="right")
        plt3.annotate("{:10.1f}".format(self.Grid_Consumption[i - 2]) + " kWh",
                      xy=(ti[i - 2], self.Grid_Consumption[i - 2]), horizontalalignment="right")

        plt4.plot(ti, self.newValueSOCCar_a, label="Neuer API-Wert SOC Auto (toggle 0/1)")

        plt5.plot(ti, self.stChargeMode_a, label="Modus")
        plt5.plot(ti, self.flgAuto_a, label="Automatik")
        plt5.annotate("{:10.0f}".format(self.stChargeMode_a[i - 2]) + "", xy=(ti[i - 2], self.stChargeMode_a[i - 2]),
                      horizontalalignment="right")

        plt6.plot(ti, [int(i) for i in self.SystemStatus_a],
                  label="Fahrzeugstatus (Unknown/Error=0, Idle=1, Charging=2, WaitCar=3, Complete=4, Error=5)")
        # plt6.annotate("{:10.0f}".format(SystemStatus_a[i-2]) + "", xy=(ti[i-2], SystemStatus_a,[i-2]), horizontalalignment="right")

        plt1.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=4)
        plt2.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3)
        plt3.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=4)
        plt4.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=1)
        plt5.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2)
        plt6.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2)

        # function to show the plot
        figure = plt.gcf()  # get current figure
        figure.set_size_inches(18, 15)
        plt1.grid()
        plt1_2.grid()

        plt2.grid()
        plt2_2.grid()

        plt3.grid()

        plt4.grid()
        plt5.grid()

        # plt3.grid()
        # plt.tight_layout()
        plt.savefig("/home/pi/Entwicklung/graph.png")
        plt.savefig("/home/pi/Entwicklung/graph.svg", format = "svg")

        # plt.savefig("/var/www/html/graph.png")
        #plt.show()
        # html_str = mpld3.fig_to_html(fig)
        # Html_file = open("index.html", "w")
        # Html_file.write(html_str)
        # Html_file.close()
