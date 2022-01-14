#!/usr/bin/python3
import json
import requests
import csv
import matplotlib.pyplot as plt
import pandas as pd
import asyncio
from kasa import SmartPlug
import os.path
import time
import socket
import datetime
from astral.sun import sun
from astral import LocationInfo
import pytz
import pytz
import chargeStrategy
import goecharger
import home
import visualization
import car
import time
from dataclasses import dataclass
from datetime import datetime

tiNow = datetime.now()
current_time = tiNow.strftime("%H:%M:%S")
print("Current Time =", current_time)
seconds = time.time()
print("Seconds since epoch =", seconds)
time.sleep(5)
tiNow2 = datetime.now()
current_time = tiNow2.strftime("%H:%M:%S")
print("Current Time =", current_time)
seconds = time.time()
print("Seconds since epoch =", seconds)


