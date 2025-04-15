#!/bin/bash
n=0
SECONDS=0
# /usr/bin/python3.7 /home/pi/ChargeOS_v2/ChargeTheGrid/chargeOS.py >> /home/pi/my.log 2>&1
cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/bat_stats.csv /home/pi/ChargeOS_v2/ChargeTheGrid/data/archive/bat_stats_$(date --date="1 day ago" +\%F).csv
cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/graph.svg /home/pi/ChargeOS_v2/ChargeTheGrid/data/archive/graph_$(date --date="1 day ago" +\%F).svg

while [ $SECONDS -le 60 ]
do
  sudo cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/plotly_plot.html /var/www/html/
  sudo cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/graph.svg /var/www/html/
  sudo cp /var/www/html/input.txt /home/pi/ChargeOS_v2/ChargeTheGrid/data/
  sudo cp /var/www/html/input.txt /home/pi/ChargeOS_v2/ChargeTheGrid/data/
  sudo cp cp /var/www/html/dailyCons.json /home/pi/ChargeOS_v2/ChargeTheGrid/config/
  

  echo $SECONDS >> /home/pi/my.log
  sleep 10
done