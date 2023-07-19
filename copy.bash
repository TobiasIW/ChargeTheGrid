#!/bin/bash
n=0
SECONDS=0
# /usr/bin/python3.7 /home/pi/chargeOS_v2/chargeOS.py >> /home/pi/my.log 2>&1
cp /home/pi/chargeOS_v2/data/bat_stats.csv /home/pi/chargeOS_v2/data/archive/bat_stats_$(date --date="1 day ago" +\%F).csv
cp /home/pi/chargeOS_v2/data/graph.svg /home/pi/chargeOS_v2/data/archive/graph_$(date --date="1 day ago" +\%F).svg

while [ $SECONDS -le 60 ]
do
  sudo cp /home/pi/chargeOS_v2/data/plotly_plot.html /var/www/html/
  sudo cp /home/pi/chargeOS_v2/data/graph.svg /var/www/html/
  sudo cp /var/www/html/input.txt /home/pi/chargeOS_v2/data/
  sudo cp /home/pi/chargeOS_v2/_templates/index_neu.html /var/www/html/
  echo $SECONDS >> /home/pi/my.log
  sleep 10
done