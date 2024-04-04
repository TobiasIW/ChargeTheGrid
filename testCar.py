import argparse
import credentials

from weconnect import weconnect


def main():
    
    print('#  Initialize WeConnect')
    weConnect = weconnect.WeConnect(username=credentials.username, password=credentials.password, updateAfterLogin=False, loginOnInit=False)
    print('#  Login')
    weConnect.login()
    print('#  update')
    weConnect.update()
    print('#  print results')
    for vin, vehicle in weConnect.vehicles.items():
        del vin
        print(vehicle)
        if "climatisation" in vehicle.domains \
                    and "climatisationStatus" in vehicle.domains["climatisation"] \
                    and vehicle.domains["climatisation"]["climatisationStatus"].enabled:
                if vehicle.domains["climatisation"]["climatisationStatus"].climatisationState.enabled:
                    print('#  climatization status')
                    print(vehicle.domains["climatisation"]["climatisationStatus"].climatisationState.value)
        if "charging" in vehicle.domains \
                    and "batteryStatus" in vehicle.domains["charging"] \
                    and vehicle.domains["charging"]["batteryStatus"].enabled:
                if vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.enabled:
                    print('#  battery status')
                    print(vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.value)
            
    print('#  done')


if __name__ == '__main__':
    main()