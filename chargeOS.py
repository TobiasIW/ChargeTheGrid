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
import configuration
from sysCtrl import sysCtrlClass
import pandas as pd
sysCtrl = sysCtrlClass()
# logger=logging.getLogger("chargeOS")
# logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', filename='aaPyLog.log', level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)
logging.error("started")

config = configuration.configClass()

sysCtrl.checkRunning(config)

#charger = goecharger.chargerClass(config)
homeData = home.homeData(config)
strategy = chargeStrategy.chargeStrategy(homeData)
vis = visualization.visualizationClass(config)
# create a myCar array the same size as the combo array
myCar = []
charger=[]
for i in range(len(config.combo)):
    # create a car object for each combo
    myCar.append(car.carClass(vis, config.combo[i]))
    charger.append(goecharger.chargerClass(config.combo[i]))
#myCar = car.carClass(vis, config.combo[0])
pred = powerPrediction.PredictionClass(config)

cycleCounter = 0  # neuer Wert erst nach 2h
while True:#
    #try:
    cycleCounter = cycleCounter + 1
    flgExe, dT = sysCtrl.executeTask(60*5, 30)#60*60)
    if flgExe:
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### start 5min task###")

        
        for i in range(len(config.combo)):
            # get the car info for each car in the combo array
            try:
                myCar[i].getInfo(config.combo[i])

            except Exception as e:
                print(e)
                logging.error("Exception SOC: ")
                logging.error(e)

        for i in range(len(config.combo)):
            print("SOC: " + str(myCar[i].SOC))
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### end 5min task###")

################### 60 min Task ############
    flgExe, dT = sysCtrl.executeTask(60*60, 1)
    if flgExe:
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### start 60min task###")
        try:
            pred.updatePrediction()
        except Exception as e:
            
            print("Exception prediction:")
            print(e)
            logging.error("Exception prediction: ")
            logging.error(e)
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### end 60min task###")
    flgExe, dT = sysCtrl.executeTask(20, 0)
    if flgExe:
        print ("dT = " + str(dT))
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### start 20s task###")
        currData = {}
        for i in range(len(config.combo)):
            # update the charger values for each charger in the combo array
            charger[i].updateVals()
            myCar[i].modelUpdateSOC(dT, charger[i])
        homeData.update(charger[1], dT)
        pred.updateSOCLims(homeData)
        
        homeData.SwitchActive = strategy.calcStrategy(homeData, vis.csvname, charger[1], myCar[1], pred, config, dT)
        vis.writeCSV(homeData, charger[1], myCar[1], config)
        print("cycle finished: {0}".format(str(cycleCounter)))
        logging.error("cycle finished: " + str(cycleCounter))
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### end 20s task###")

    flgExe, dT = sysCtrl.executeTask(60, 20)
    if flgExe:
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### start 60s task###")
        vis.plotData(pred, config)
        #sysCtrl.checkRunning(config)
        #except Exception as e:
        #    print(e)
         #   logging.error('Exception outer: ')
          #  logging.error(e)
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ": ### end 60s task###")
    time.sleep(1)
# except:
#    print("abbruch chargeOS")
# finally:
# print("abschluss chargeOS")
# os.unlink(pidfile)

##########################
