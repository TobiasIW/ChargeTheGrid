import os
import sys
import datetime
import time
# import evaluate_sb
import chargeStrategy
import goecharger
import home
import visualization
import car
import logging
import powerPrediction
from sysCtrl import sysCtrlClass
sysCtrl = sysCtrlClass()
# logger=logging.getLogger("chargeOS")
# logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', filename='aaPyLog.log', level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)
logging.error("started")

sysCtrl.checkRunning()

charger = goecharger.chargerClass("192.168.178.201")

# print("test4")
homeData = home.homeData()
strategy = chargeStrategy.chargeStrategy()
vis = visualization.visualizationClass()
myCar = car.carClass(vis)
pred = powerPrediction.PredictionClass()

cycleCounter = 0  # neuer Wert erst nach 2h
while True:#
    #try:
    cycleCounter = cycleCounter + 1
    flgExe, dT = sysCtrl.executeTask(60*120, 60*120)
    if flgExe:
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### start 120min task###")
        #print("### start 120min Task ###")
        try:
            myCar.getInfo()
        except Exception as e:
            print(e)
            logging.error("Exception SOC: ")
            logging.error(e)
            if myCar.newValue == 3:
                myCar.newValue = 2
            else:
                myCar.newValue = 3
        print("SOC: " + str(myCar.SOC))
    flgExe, dT = sysCtrl.executeTask(60*60, 1)
    if flgExe:
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### start 60min task###")
        try:
            pred.updatePrediction()
        except Exception as e:
            print(e)
            logging.error("Exception prediction: ")
            logging.error(e)
    flgExe, dT = sysCtrl.executeTask(20, 0)
    if flgExe:
        print ("dT = " + str(dT))
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### start 20s task###")
        charger.updateVals()
        homeData.update(charger)
        pred.updateSOCLims(homeData)
        myCar.model(dT, charger)
        homeData.SwitchActive = strategy.calcStrategy(homeData, vis.csvname, charger, myCar, pred)
        vis.writeCSV(homeData, charger, myCar)
        print("cycle finished: {0}".format(str(cycleCounter)))
        logging.error("cycle finished: " + str(cycleCounter))
    flgExe, dT = sysCtrl.executeTask(60, 0)
    if flgExe:
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### start 60s task###")
        vis.plotData(pred)
        #except Exception as e:
        #    print(e)
         #   logging.error('Exception outer: ')
          #  logging.error(e)

    time.sleep(1)
# except:
#    print("abbruch chargeOS")
# finally:
# print("abschluss chargeOS")
# os.unlink(pidfile)

##########################
