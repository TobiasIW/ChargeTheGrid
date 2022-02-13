import os
import sys
import sysCtrl
import time
# import evaluate_sb
import chargeStrategy
import goecharger
import home
import visualization
import car
import logging
import powerPrediction

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
    if cycleCounter >= 120:
        print("### start 120min Task ###")
        cycleCounter = 0
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
    if cycleCounter % 60 == 2:
        print("### start 60min Task ###")
        try:
            pred.updatePrediction()
        except Exception as e:
            print(e)
            logging.error("Exception prediction: ")
            logging.error(e)
    print("### start 1min Task ###")
    pred.updateSOCLims()
    charger.updateVals()
    homeData.update(charger)
    myCar.model(60, charger)
    # print ("test7")
    homeData.SwitchActive = strategy.calcStrategy(homeData, vis.csvname, charger, myCar, pred)
    # print ("test8")
    vis.writeCSV(homeData, charger, myCar)
    # print ("test9")
    vis.readCSV()
    # print ("test10")
    vis.plotData(pred)
    # print ("test11")
    #except Exception as e:
    #    print(e)
     #   logging.error('Exception outer: ')
      #  logging.error(e)
    print("cycle finished: {0}".format(str(cycleCounter)))
    logging.error("cycle finished: " + str(cycleCounter))
    time.sleep(55)
# except:
#    print("abbruch chargeOS")
# finally:
# print("abschluss chargeOS")
# os.unlink(pidfile)

##########################
