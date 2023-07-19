from NativeAPI import WeConnect
import logging
import requests
import asyncio


class carClass:
    SOC = 0.0
    capacityWs = 34 * 1000 * 3600
    newValue = 0
    _oldState = 2

    def __init__(self, vis, config):
        self.SOC = vis.readVal("SOC_Car")
        self._oldState = vis.readVal("CarStatus")

    def model(self, dT_s, charger):
        _state = int(charger.state)
        if (_state == 2) or (_state == 4):
            _power = float(charger.power)
            if (self._oldState != 2) and (self._oldState != 4) and (self._oldState != 0):
                try:
                    self.getInfo()
                except Exception as e:
                    print(e)
                    logging.error("Exception SOC: ")
                    logging.error(e)
                    if self.newValue == 3:
                        self.newValue = 2
                    else:
                        self.newValue = 3
        else:
            _power = 0  # -0.2 * 15 * 1000 / 24

        print("Power: " + str(_power))
        self.SOC = float(self.SOC) + 100 * ((_power * dT_s) / self.capacityWs)
        self._oldState = _state

    def getInfo(self):
        # logging.getLogger().setLevel(logging.WARN)
        print('test1')
        vwc = WeConnect()
        print('test2')
        vwc.login()
        print('test3')
        cars = vwc.get_real_car_data()
        print('test4')
        profile = vwc.get_personal_data()

        print('Hi {} {} {} ({})!'.format(profile['salutation'], profile['firstName'], profile['lastName'],
                                         profile['nickname']))
        mbb = vwc.get_mbb_status()
        # print('Profile completed?', mbb['profileCompleted'])
        # print('S-PIN defined?', mbb['spinDefined'])
        print('CarNet enrollment country:',mbb['carnetEnrollmentCountry'])
        if (cars and len(cars)):
            # print('Enumerating cars...')
            for car in cars['realCars']:
                vin = car['vehicleIdentificationNumber']
                # print('\tNickname:', car['nickname'])
                # print('\tDealer:', car['allocatedDealerBrandCode'])
                # print('\tCarNet enrollment date:', car['carnetAllocationTimestamp'])
                # print('\tCarNet indicator:', car['carNetIndicator'])
                # print('\tDeactivated:', car['deactivated'])
                # if (car['deactivated'] == True):
                #    print('\tDeactivation reason:',car['deactivationReason'])

                # print('---\nFetching information of {} (vin {})...\n---\n'.format(car['nickname'], vin))
                details = vwc.get_vehicle_data(vin)
                cardata = details['vehicleDataDetail']['carportData']
                print('\tModel:' ,cardata['modelName'])
                # print('\tYear:', cardata['modelYear'])
                # print('\tModel code:', cardata['modelCode'])
                # print('\tEngine:', cardata['engine'])
                # print('\tMMI:', cardata['mmi'])
                # print('\tTransmission:', cardata['transmission'])
                users = vwc.get_users(vin)
                # print('\tFound {} user(s) with access: {}'.format(len(users['users']), ', '.join([user['nickname'] for user in users['users']])))
                r = vwc.request_status_update(vin)
                vsr = vwc.get_vsr(vin)
                pvsr = vwc.parse_vsr(vsr)
                # print('\tStatus:')
                status = pvsr['status']
                print (status)
                self.SOC = float(status['state_of_charge'].split()[0])
                if (self.newValue == 0):
                    self.newValue = 1
                else:
                    self.newValue = 0
                # print('\t\tDistance covered:', status['distance_covered'])
                # print('\t\tParking light:', status['parking_light'])
                # print('\t\tParking brake:', status['parking_brake'])
                # print('\t\tTemperature outside:', (int(status['temperature_outside'].split(' ')[0])-2731)/10)
                # print('\t\tBEM:', status['bem'])
                # print('\t\tSpeed:', status['speed'])
                # print('\t\tTotal range:', status['total_range'])
                # print('\t\tPrimary range:', status['primary_range'])
                # print('\t\tSecondary range:', status['secondary_range'])
                # print('\t\tFuel level:', status['fuel_level'])
                # print('\t\tCNG level:', status['cng_level'])

                # print('\tIntervals:')
                # intv = pvsr['intervals']
                # print('\t\tDistance to oil change:', intv['distance_to_oil_change'])
                # print('\t\tDays to oil change:', intv['time_to_oil_change'])
                # print('\t\tDistance to inspection:', intv['distance_to_inspection'])
                # print('\t\tDays to inspection:', intv['time_to_inspection'])
                # print('\t\tAdBlue range:', intv['ad_blue_range'])

                # print('\tOil level:')
                # oil = pvsr['oil_level']
                # print('\t\tLiters:', oil['liters'])
                # print('\t\tPercentage:', oil['dipstick_percentage'])

                # print('\tDoors:')
                # doors = pvsr['doors']
                # avdoors = {'left_front':'Left front', 'right_front':'Right front', 'left_rear':'Left rear', 'right_rear':'Right rear', 'trunk':'Trunk', 'hood':'Hood'}
                # for d in avdoors.items():
                #    print('\t\t{}: {}, {}'.format(d[1], doors['open_'+d[0]], doors['lock_'+d[0]]))

                # print('\tWindows:')
                # win = pvsr['windows']
                # avwin = {'left_front':'Left front', 'right_front':'Right front', 'left_rear':'Left rear', 'right_rear':'Right rear'}
                # for d in avwin.items():
                #    print('\t\t{}: {}, {}'.format(d[1], win['state_'+d[0]], win['position_'+d[0]]))
                # print('\t\tState roof:', win['state_roof'])
                # print('\t\tState roof rear:', win['state_roof_rear'])
                # print('\t\tState service flap:', win['state_service_flap'])
                # print('\t\tState spoiler:', win['state_spoiler'])
                # print('\t\tState convertible top:', win['state_convertible_top'])

                # print('\tTyre pressure:')
                # tyre = pvsr['tyre_pressure']
                # avtyre = {'left_front':'Left front', 'right_front':'Right front', 'left_rear':'Left rear', 'right_rear':'Right rear','spare':'Spare'}
                # for d in avtyre.items():
                #    print('\t\t{}: {} (desired {}, diff {})'.format(d[1], tyre['current_'+d[0]], tyre['desired_'+d[0]], tyre['difference_'+d[0]]))
                pos = vwc.get_position(vin)
                latlong = pos['storedPositionResponse']['position']['carCoordinate']
                data = requests.get(
                    'https://nominatim.openstreetmap.org/search.php?q=' + str(latlong['latitude'] / 1e6) + ',' + str(
                        latlong['longitude'] / 1e6) + '&polygon_geojson=1&format=jsonv2')
                j = data.json()
                if (len(j) > 0):
                    print('\tLocation: ' + j[0]['display_name'])
