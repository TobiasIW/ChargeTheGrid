import csv
import matplotlib.pyplot as plt
import pandas as pd
import asyncio
# from kasa import SmartPlug
import os.path
import time
import datetime
import pytz
import numpy as np
from scipy import integrate
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio


class visualizationClass:
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
    Car_Consumption = []
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

    def writeCSV(self, homeData, charger, myCar, config):
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

            i = len(self.x) - 1  #

            self.SOC_a.append(homeData.SOC)
            self.Prod_a.append(homeData.Prod)
            self.Cons_a.append(homeData.Cons)
            self.Batt_pow_a.append(homeData.Batt_pow)
            self.GridFeedIn_pow_a.append(homeData.GridFeedIn_pow)
            self.OperatingMode_a.append(homeData.OperatingMode)
            self.SystemStatus_a.append(charger.state)

            self.Time_a.append(self.berlin.localize(pd.to_datetime(homeData.TimeStamp)))


            self.newValueSOCCar_a.append(myCar.newValue)
            self.stChargeMode_a.append(homeData.stChargeMode)
            self.flgAuto_a.append(homeData.flgAuto)
            self.ConsHome_a.append(homeData.Cons_home)  # int(row[10]))
            self.Car_SOC_a.append(myCar.SOC)

            self.x.append(i)

        time_delta_a = [self.Time_a[n].timestamp() / 3600000 for n in range(0, len(self.Time_a))]
        __cons_car = [self.Cons_a[n] - self.ConsHome_a[n] for n in range(0, len(self.Time_a))]
        self.FeedIn_pow = [max(0, self.GridFeedIn_pow_a[n]) for n in range(0, len(self.Time_a))]
        self.Grid_Consumption_pow = [max(0, -self.GridFeedIn_pow_a[n]) for n in range(0, len(self.Time_a))]

        self.Consumption = integrate.cumtrapz(self.Cons_a, time_delta_a, initial = 0)
        self.Production = integrate.cumtrapz(self.Prod_a, time_delta_a, initial = 0)
        self.FeedIn = integrate.cumtrapz(self.FeedIn_pow, time_delta_a, initial = 0)
        self.Grid_Consumption = integrate.cumtrapz(self.Grid_Consumption_pow, time_delta_a, initial = 0)
        self.Car_Consumption = integrate.cumtrapz(__cons_car, time_delta_a, initial = 0)
        df = pd.DataFrame({'index': self.Time_a, 'consumption': self.Cons_a, 'production': self.Prod_a})
        pd.options.plotting.backend= "plotly"
        __current_date = datetime.datetime.now().date()
        __is_from_today = self.Time_a[0].date() == __current_date
        if __is_from_today:
            self.__init__(config)
        a=1
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

    def __init__(self, config):
        self.clear()
        self.csvname = config.dataFolder + "bat_stats.csv"
        self.dfCsvName = config.dataFolder + "df.csv"
        self.berlin = pytz.timezone("Europe/Berlin")
        try:
            data = csv.reader(open(self.csvname, 'r'))
            i = 0
            for row in data:
                i = i + 1
                if i > 1:

                    self.SOC_a.append(float(row[0]))
                    self.Prod_a.append(int(row[1]))
                    self.Cons_a.append(int(row[2]))
                    self.Batt_pow_a.append(int(row[3]))
                    self.GridFeedIn_pow_a.append(int(row[4]))
                    self.OperatingMode_a.append(int(row[5]))
                    self.SystemStatus_a.append(row[6])
                    self.Time_a.append(self.berlin.localize(pd.to_datetime(row[7])))



                    self.newValueSOCCar_a.append(int(row[8]))
                    self.stChargeMode_a.append(int(row[9]))
                    self.flgAuto_a.append(int(row[10]))
                    self.ConsHome_a.append(int(row[11]))  # int(row[10]))
                    self.Car_SOC_a.append(float(row[12]))

                    self.x.append(i)
            time_delta_a = [self.Time_a[n].timestamp() / 3600000 for n in range(0, len(self.Time_a))]
            self.FeedIn_pow = [max(0, self.GridFeedIn_pow_a[n]) for n in range(0, len(self.Time_a))]
            self.Grid_Consumption_pow = [max(0, -self.GridFeedIn_pow_a[n]) for n in range(0, len(self.Time_a))]

            self.Consumption = integrate.cumtrapz(self.Cons_a, time_delta_a, initial=0)
            self.Production = integrate.cumtrapz(self.Prod_a, time_delta_a, initial=0)
            self.FeedIn = integrate.cumtrapz(self.FeedIn_pow, time_delta_a, initial=0)
            self.Grid_Consumption = integrate.cumtrapz(self.Grid_Consumption_pow, time_delta_a, initial=0)
            __cons_car = [self.Cons_a[n] - self.ConsHome_a[n] for n in range(0, len(self.Time_a))]

            self.Car_Consumption = integrate.cumtrapz(__cons_car, time_delta_a, initial=0)

        except:
            print("Exception: could not load csv")
    def plotData(self, pred, config):
        i = len(self.x)
        ti = [pd.to_datetime(d) for d in self.Time_a]
        # print(ti)
        # defining subplots and their positions
        # fig = plt.figure(figsize=(18, 15))
        plt1 = plt.subplot2grid((43, 4), (0, 0), rowspan=8, colspan=2)
        plt1_2 = plt.subplot2grid((43, 4), (0, 2), rowspan=8, colspan=2)
        plt2 = plt.subplot2grid((43, 4), (10, 0), rowspan=5, colspan=2)
        plt2_2 = plt.subplot2grid((43, 4), (10, 2), rowspan=5, colspan=2)
        plt3 = plt.subplot2grid((43, 4), (17, 0), rowspan=5, colspan=2)
        plt3_2 = plt.subplot2grid((43, 4), (17, 2), rowspan=5, colspan=2)
        plt4 = plt.subplot2grid((43, 4), (25, 0), rowspan=6, colspan=2)

        plt5 = plt.subplot2grid((43, 4), (33, 0), rowspan=1, colspan=2)
        plt6 = plt.subplot2grid((43, 4), (37, 0), rowspan=2, colspan=2)
        plt7 = plt.subplot2grid((43, 4), (41, 0), rowspan=2, colspan=2)

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
        plt3.set_ylim(0, 101)
        plt3.set_xlim(ti[0], __endofday)

        plt3_2.set_ylim(0, 101)
        plt3_2.set_xlim(__endofday, __endpred)
        plt4.set_xlim(ti[0], __endofday)

        plt5.set_ylim(-0.1, 3.1)
        plt5.set_xlim(ti[0], __endofday)

        plt6.set_ylim(-0.1, 5.1)
        plt6.set_xlim(ti[0], __endofday)

        plt7.set_xlim(ti[0], __endofday)

        plt1.plot(ti, self.Cons_a, label="Verbrauch", linewidth="0.5")
        plt1.plot(ti, self.Prod_a, label="Produktion", linewidth="0.5")
        plt1.plot(ti, self.Batt_pow_a, label="Laden(-)/Entladen(+)", linewidth="0.5")
        plt1.plot(ti, self.GridFeedIn_pow_a, label="Einspeisung(+)/Bezug(-)", linewidth="0.5")
        plt1.plot(ti, self.ConsHome_a, label="Verbr. o. WB", linewidth="0.5")
        #plt1.plot(pred.date_a, pred.powProd_a, 'tab:brown', label="präd. Produktion", linewidth="0.5")
        #plt1.plot(pred.date_a, pred.powProdLow_a, 'tab:brown', label="präd. Produktion Min.", linewidth="0.5")
        plt1.plot(pred.date_a, pred.powCons_a, 'm', label="präd. Verbrauch", linewidth="0.5")
        plt1.fill_between(pred.date_a, pred.powProdLow_a, pred.powProd_a, color='C0', alpha=0.4, label='Präd. Produktion')
        #plt1_2.plot(pred.date_a, pred.powProd_a, 'tab:brown', label="präd. Produktion", linewidth="0.5")
        #plt1_2.plot(pred.date_a, pred.powProdLow_a, 'tab:brown', label="präd. Produktion Min.", linewidth="0.5")
        plt1_2.plot(pred.date_a, pred.powCons_a, 'm', label="präd. Verbrauch", linewidth="0.5")
        plt1_2.fill_between(pred.date_a, pred.powProdLow_a, pred.powProd_a, color='C0', alpha=0.4)

        n = len(pred.date_a)
        plt2.plot(ti, self.Car_SOC_a, label="SOC_Auto", linewidth="0.5")
        #plt2.plot(pred.date_a, pred.minSOCVeh_a, 'm--', label="Min SOC Veh High Prio", linewidth="0.5")
        #plt2.plot(pred.date_a, pred.maxSOCVehProdChrg_a, 'g--', label="Min SOC Veh Überschuss", linewidth="0.5")
        #plt2.plot(pred.date_a, pred.maxSOCVehExcessChrg_a, 'g', label="Min SOC Veh Abriegeln", linewidth="0.5")
        plt2.fill_between(pred.date_a, 0, np.minimum(pred.minSOCVeh_a, pred.maxSOCVehProdChrg_a), color='tomato', alpha=0.4, label='Fz SOC: max. Laden')
        plt2.fill_between(pred.date_a, pred.minSOCVeh_a, np.maximum(pred.maxSOCVehProdChrg_a,  pred.minSOCVeh_a), linewidth=0.0, color='orange', alpha=0.4, label='Fz SOC: vollst. Ertrag laden')
        plt2.fill_between(pred.date_a, pred.maxSOCVehProdChrg_a, pred.maxSOCVehExcessChrg_a, color='palegreen', alpha=0.4, label='Fz SOC: Smart charging')
        plt2.fill_between(pred.date_a, pred.maxSOCVehExcessChrg_a, 110, color='deepskyblue', alpha=0.4, label='Fz SOC: Laden bei Abriegelung')

        plt2.annotate("{:10.0f}".format(self.Car_SOC_a[i - 2]) + "%", xy=(ti[i - 2], self.Car_SOC_a[i - 2]), horizontalalignment="right")


        #plt2_2.plot(pred.date_a, pred.minSOCVeh_a, 'm--', label="Min SOC Veh High Prio")
        try:
            plt2_2.fill_between(pred.date_a, 0, np.minimum(pred.minSOCVeh_a, pred.maxSOCVehProdChrg_a),  color='tomato', alpha=0.4, label='Fz SOC: max. Laden')
        except ValueError as e:
            print("Exception: ValueError: ", e)
            with np.printoptions(threshold=np.inf):
                print("pred.minSOCVeh_a: ", pred.minSOCVeh_a)
                print("pred.maxSOCVehProdChrg_a: ", pred.maxSOCVehProdChrg_a)
                print("np.minimum(pred.minSOCVeh_a, pred.maxSOCVehProdChrg_a): ",
                      np.minimum(pred.minSOCVeh_a, pred.maxSOCVehProdChrg_a))
        except Exception as e:
            print("Exception: ",e)
            with np.printoptions(threshold=np.inf):
                print("pred.minSOCVeh_a: ", pred.minSOCVeh_a)
                print("pred.maxSOCVehProdChrg_a: ", pred.maxSOCVehProdChrg_a)
                print("np.minimum(pred.minSOCVeh_a, pred.maxSOCVehProdChrg_a): ", np.minimum(pred.minSOCVeh_a, pred.maxSOCVehProdChrg_a))

        plt2_2.fill_between(pred.date_a, pred.maxSOCVehProdChrg_a, pred.maxSOCVehExcessChrg_a, color='palegreen', alpha=0.4, label='Fz SOC: Smart charging')
        plt2_2.fill_between(pred.date_a, pred.maxSOCVehExcessChrg_a, 110,  color='deepskyblue', alpha=0.4, label='Fz SOC: Laden bei Abriegelung')
        #plt2_2.plot(pred.date_a, pred.maxSOCVehProdChrg_a, 'g--', label="Min SOC Veh Überschuss")
        #plt2_2.plot(pred.date_a, pred.maxSOCVehExcessChrg_a, 'g', label="Min SOC Veh Abriegeln")
        plt2_2.fill_between(pred.date_a, pred.maxSOCVehProdChrg_a, np.minimum(pred.maxSOCVehProdChrg_a, pred.minSOCVeh_a), linewidth=0.0, color='orange', alpha=0.4, label='Fz SOC: vollst. Ertrag laden')


        plt3.plot(ti, self.SOC_a, label="SOC", linewidth="0.5")
        #plt3.plot(pred.date_a, pred.maxSOCHome_a, 'c--', label="max. SOC Haus", linewidth="0.5")
        plt3.fill_between(pred.date_a, np.full(n, 0), pred.minSOCHome_a,  color='tomato', alpha=0.4, label='Haus SOC zu gering')
        plt3.fill_between(pred.date_a, pred.minSOCHome_a, pred.minSOCHomeLowProd_a, color='gold', alpha=0.4, label='Haus SOC Zielbereich ')
        plt3.fill_between(pred.date_a, pred.minSOCHomeLowProd_a, np.full(n, 110), color='palegreen', alpha=0.4, label='Haus SOC Überschuss ')


        plt3.annotate("{:10.0f}".format(self.SOC_a[i - 2]) + "%", xy=(ti[i - 2], self.SOC_a[i - 2]),
                      horizontalalignment="right")

        #plt3_2.plot(pred.date_a, pred.maxSOCHome_a, 'c--', label="max. SOC Haus")
        plt3_2.fill_between(pred.date_a, np.full(n, 0), pred.minSOCHome_a, color='tomato', alpha=0.4, label='Haus SOC zu gering')
        plt3_2.fill_between(pred.date_a, pred.minSOCHome_a, pred.minSOCHomeLowProd_a, color='gold', alpha=0.4, label='Haus SOC Zielbereich ')
        plt3_2.fill_between(pred.date_a, pred.minSOCHomeLowProd_a, np.full(n, 110), color='palegreen', alpha=0.4, label='Haus SOC Überschuss ')

        plt4.plot(ti, self.Consumption, label="Verbrauch")
        plt4.plot(ti, self.Production, label="Produktion")
        plt4.plot(ti, self.FeedIn, label="Einspeisung")
        plt4.plot(ti, self.Grid_Consumption, label="Bezug")
        plt4.annotate("{:10.1f}".format(self.Consumption[i - 2]) + " kWh", xy=(ti[i - 2], self.Consumption[i - 2]),
                      horizontalalignment="right")
        plt4.annotate("{:10.1f}".format(self.Production[i - 2]) + " kWh", xy=(ti[i - 2], self.Production[i - 2]),
                      horizontalalignment="right")
        plt4.annotate("{:10.1f}".format(self.FeedIn[i - 2]) + " kWh", xy=(ti[i - 2], self.FeedIn[i - 2]),
                      horizontalalignment="right")
        plt4.annotate("{:10.1f}".format(self.Grid_Consumption[i - 2]) + " kWh",
                      xy=(ti[i - 2], self.Grid_Consumption[i - 2]), horizontalalignment="right")

        plt5.plot(ti, self.newValueSOCCar_a, label="Neuer API-Wert SOC Auto (toggle 0/1)")

        plt6.plot(ti, self.stChargeMode_a, label="Modus")
        plt6.plot(ti, self.flgAuto_a, label="Automatik")
        plt6.annotate("{:10.0f}".format(self.stChargeMode_a[i - 2]) + "", xy=(ti[i - 2], self.stChargeMode_a[i - 2]),
                      horizontalalignment="right")

        plt7.plot(ti, [int(i) for i in self.SystemStatus_a],
                  label="Fahrzeugstatus (Unknown/Error=0, Idle=1, Charging=2, WaitCar=3, Complete=4, Error=5)")
        # plt7.annotate("{:10.0f}".format(SystemStatus_a[i-2]) + "", xy=(ti[i-2], SystemStatus_a,[i-2]), horizontalalignment="right")

        plt1.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=4)
        plt2.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3)
        plt3.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3)

        plt4.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=4)
        plt5.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=1)
        plt6.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2)
        plt7.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2)

        # function to show the plot
        figure = plt.gcf()  # get current figure
        figure.set_size_inches(18, 15)
        plt1.grid()
        plt1_2.grid()

        plt2.grid()
        plt2_2.grid()
        plt3.grid()
        plt3_2.grid()
        plt4.grid()

        plt5.grid()
        plt6.grid()

        # plt4.grid()
        # plt.tight_layout()
        plt.savefig(config.dataFolder + "graph.png")
        plt.savefig(config.dataFolder + "graph.svg", format="svg", bbox_inches='tight')

        # Create subplots with two rows and one column
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.015, row_heights=[0.3, 0.2, 0.2, 0.3])

        # Add consumption trace to the first subplot
        fig.add_trace(go.Scatter(x=ti, y=self.Cons_a, mode='lines',line=dict(color='blue', width=1), name='total consumption'), row=1, col=1)
        fig.add_trace(go.Scatter(x=ti, y=self.ConsHome_a, mode='lines', line=dict(color='purple', width=1), name='home consumption'), row=1, col=1)
        fig.add_trace(go.Scatter(x=ti, y=self.Prod_a, mode='lines', line=dict(color='orange', width=1), name='Production'), row=1, col=1)
        fig.add_trace(go.Scatter(x=ti, y=self.GridFeedIn_pow_a, line=dict(color='red', width=1), mode='lines', name='Einspeisung(+)/Bezug(-)'), row=1, col=1)
        fig.add_trace(go.Scatter(x=ti, y=self.Batt_pow_a, mode='lines', line=dict(color='green', width=1), name='Laden(-)/Entladen(+)'), row=1, col=1)

        __colTomato = 'rgba(255, 99, 71, 0.4)'
        __colBlue = 'rgba(0, 191, 255, 0.4)'
        __colGreen = 'rgba(152, 255, 152, 0.4)'
        __colOrange = 'rgba(255, 165, 0, 0.4)'
        __colYellow = 'rgba(255, 215, 0, 0.4)'

        fig.add_trace(go.Scatter(x=ti, y=self.Car_SOC_a, mode='lines', showlegend=True, name='Car SOC'), row=2, col=1)
        #invisible line for filling area between excess charge limit and 100%
        fig.add_trace(go.Scatter(x=pred.date_a, y=[100]*len(pred.date_a), mode='lines', showlegend=False, line=dict(color='green'), name='y=100'), row=2, col=1)
        # lines for car SOC limits
        fig.add_trace(go.Scatter(x=pred.date_a, y=pred.maxSOCVehExcessChrg_a, mode='lines', showlegend=True, fill='tonexty',fillcolor=__colBlue, line=dict(color='green', width=1),  name='Fz SOC: smart Laden'), row=2, col=1)
        fig.add_trace(go.Scatter(x=pred.date_a, y=pred.maxSOCVehProdChrg_a, mode='lines', showlegend=True, fill='tonexty', fillcolor=__colGreen,line=dict(color='orange', width=1), name='Fz SOC: smart Laden'), row=2, col=1)
        fig.add_trace(go.Scatter(x=pred.date_a, y=np.minimum(pred.minSOCVeh_a, pred.maxSOCVehProdChrg_a), mode='lines', fill='tonexty', fillcolor=__colOrange,line=dict(color='red', width=1), showlegend=True, name='Fz SOC: max. Laden'), row=2, col=1)
        fig.add_trace(go.Scatter(x=pred.date_a, y=[0]*len(pred.date_a), mode='lines', fill='tonexty', fillcolor=__colTomato,line=dict(color='red', width=1), showlegend=False, name='y=0'), row=2, col=1)



        fig.add_trace(go.Scatter(x=ti, y=self.SOC_a, mode='lines', name='Home SOC'), row=3, col=1)
        fig.add_trace(go.Scatter(x=pred.date_a, y=[100]*len(pred.date_a), mode='lines', showlegend=False, line = dict(color='green', width=1),name='y=100'), row=3, col=1)
        fig.add_trace(go.Scatter(x=pred.date_a, y=pred.minSOCHomeLowProd_a, mode='lines', fill='tonexty', fillcolor=__colGreen, line = dict(color='yellow', width=1), name='Max. Home SOC'), row=3, col=1)
        fig.add_trace(go.Scatter(x=pred.date_a, y=pred.minSOCHome_a, mode='lines', fill='tonexty', fillcolor=__colYellow, line=dict(color='red', width=1), name='Min. Home SOC'), row=3, col=1)
        fig.add_trace(go.Scatter(x=pred.date_a, y=[0]*len(pred.date_a), mode='lines', fill='tonexty',fillcolor=__colTomato, showlegend=False, name='y=0'), row=3, col=1)


        # Add production trace to the second subplot
        fig.add_trace(go.Scatter(x=ti, y=self.Consumption, mode='lines', name='Total Consumption'), row=4, col=1)
        fig.add_trace(go.Scatter(x=ti, y=self.Production, mode='lines', name='Total Production'), row=4, col=1)
        fig.add_trace(go.Scatter(x=ti, y=self.Car_Consumption, mode='lines', name='Charge energy'), row=4, col=1)
        fig.add_trace(go.Scatter(x=ti, y=self.Grid_Consumption, mode='lines', name='Bezug'), row=4, col=1)
        fig.add_trace(go.Scatter(x=ti, y=self.FeedIn, mode='lines', name='Einspeisung'), row=4, col=1)

        # Update the layout
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Power',
            yaxis2_title='Car SOC',
            yaxis3_title='Home SOC',
            yaxis4_title='Energy',
            height=800,
            width=1000,
            autosize=True
        )
        # Set x-axis range from 12:00 AM to 11:59 PM of the current day
        current_date = datetime.datetime.now().date()
        x_range = [datetime.datetime.combine(current_date, datetime.datetime.min.time()),
                   datetime.datetime.combine(current_date, datetime.datetime.max.time())]
        fig.update_xaxes(range=x_range)
        # Set y-axis range of the first subplot to 0 to 100
        fig.update_yaxes(range=[-5000, 10000], row=1, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1)
        fig.update_yaxes(range=[0, 100], row=3, col=1)

        # Display the plot
        #fig.write_html(config.dataFolder + 'plotly_plot.html')
        pio.write_html(fig, config.dataFolder + 'plotly_plot.html', full_html=False)






