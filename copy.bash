#!/bin/bash
n=0
SECONDS=0

# /usr/bin/python3.7 /home/pi/ChargeOS_v2/ChargeTheGrid/chargeOS.py >> /home/pi/my.log 2>&1
# archive bat_stats.csv from yesterday if it does not exist yet
if [ ! -f /home/pi/ChargeOS_v2/ChargeTheGrid/data/archive/bat_stats_$(date --date="1 day ago" +\%F).csv ]; then
  cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/bat_stats.csv /home/pi/ChargeOS_v2/ChargeTheGrid/data/archive/bat_stats_$(date --date="1 day ago" +\%F).csv
  # replace bat_stats.csv with template
  cp /home/pi/ChargeOS_v2/ChargeTheGrid/_templates/bat_stats_templ.csv /home/pi/ChargeOS_v2/ChargeTheGrid/data/bat_stats.csv
fi
# archive graph.svg from yesterday if it does not exist yet
if [ ! -f /home/pi/ChargeOS_v2/ChargeTheGrid/data/archive/graph_$(date --date="1 day ago" +\%F).svg ]; then
  cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/graph.svg /home/pi/ChargeOS_v2/ChargeTheGrid/data/archive/graph_$(date --date="1 day ago" +\%F).svg
  cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/plotly_plot.html /home/pi/ChargeOS_v2/ChargeTheGrid/data/archive/graph_$(date --date="1 day ago" +\%F).svg
  # Create a variable for the subfolder name for yesterday's month (YYYY_MM)
  subfolder_name=$(date --date="1 day ago" +\%Y_\%m)
  if [ ! -d /var/www/html/graphs/$subfolder_name ]; then
      sudo mkdir -p /var/www/html/graphs/$subfolder_name
      echo "Created directory /var/www/html/graphs/$subfolder_name"
    fi

  # Copy graph.svg to the month folder
  sudo cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/graph.svg /var/www/html/graphs/$subfolder_name/graph_$(date --date="1 day ago" +\%F).svg
   cp /home/pi/ChargeOS_v2/ChargeTheGrid/data/plotly_plot.html /var/www/html/graphs/$subfolder_name/plotly_plot_$(date --date="1 day ago" +\%F).html
fi

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