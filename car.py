import logging
from weconnect import weconnect
import asyncio
from aiohttp import ClientSession
from audiconnect.audi_connect_account import AudiConnectAccount
import datetime
class carClass:
    SOC = 0.0
    consumption = 15 # kWh/100km
    newValue = 0
    _oldState = 2
    # initialize lastChange to minimum value
    # This will be updated when the SOC is fetched
    lastChange = datetime.datetime.min
    def __init__(self, carConfig):
        self.capacityWs =carConfig["carCapacity"]* 1000 * 3600  # Convert kWh to Ws
        self.capacityWh = carConfig["carCapacity"] *1000  # Convert kWh to Wh
        self.minSOCVeh_a = []
        self.maxSOCVehProdChrg_a = []
        self.maxSOCVehExcessChrg_a = []
        self.name = carConfig["carName"]
    def initSOC(self, vis):
        """Initialize the SOC from the visualization."""
        self.SOC = vis.readVal("SOC_Car_"+self.name)
        self._oldState = vis.readVal("ChargerStatus_"+self.name)



    def modelUpdateSOC(self, dT_s, charger):
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
    def range(self):
        """Calculate the range based on the current SOC and consumption."""
        return (self.SOC / 100) *self.capacityWs/1000/3600 *(100 / self.consumption)
    def getInfo(self, carConfig):
        if carConfig["carProtocol"] == "VW":
            self._handleVWProtocol(carConfig)
        elif carConfig["carProtocol"] == "Audi":
            self._handleAudiProtocol(carConfig)
            
        else:
            print(f"Error: Protocol '{carConfig['carProtocol']}' is not supported.")
            logging.error(f"Unsupported protocol: {carConfig['carProtocol']}")
            raise ValueError(f"Unsupported protocol: {carConfig['carProtocol']}")

    def _handleVWProtocol(self, carConfig):
        weConnect = weconnect.WeConnect(username=carConfig["carUser"], password=carConfig["carPassword"], updateAfterLogin=False, loginOnInit=False)
        print("Fetch the State of Charge (SOC) for the VW.")
        print('#  Login')
        weConnect.login()
        print('#  update')
        weConnect.update()
        print('#  print results')
        for vin, vehicle in weConnect.vehicles.items():
            del vin
            if "charging" in vehicle.domains \
                    and "batteryStatus" in vehicle.domains["charging"] \
                    and vehicle.domains["charging"]["batteryStatus"].enabled:
                if vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.enabled:
                    print('#  battery status')
                    print(vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.value)
                    
                    
                    #if vehicle.domains["charging"]["batteryStatus"]["currentSOC_pct"].lastUpdatefromServer is not None:
                        #print('#  last update from server')
                        #if vehicle.domains["charging"]["batteryStatus"]["currentSOC_pct"].lastUpdatefromServer > self.lastChange:
                            #self.lastChange = vehicle.domains["charging"]["batteryStatus"]["currentSOC_pct"].lastUpdatefromServer
                    self.SOC = float(vehicle.domains["charging"]["batteryStatus"].currentSOC_pct.value)
                            #self.lastChange = vehicle.domains["charging"]["batteryStatus"].lastUpdatefromServer
                    if self.newValue == 0:
                        self.newValue = 1
                    else:
                        self.newValue = 0

    def _handleAudiProtocol(self, carConfig)    :
        """Handle the Audi protocol to fetch vehicle information."""
        print("Audi protocol selected.")    
        # Use asyncio to run the Audi_get_vehicle_soc method
        asyncio.run(self.Audi_get_vehicle_soc(carConfig))


    async def Audi_get_vehicle_soc(self, carConfig):
        print("Fetch the State of Charge (SOC) for the Audi.")
        # Hardcoded credentials (replace with your own)
        username = carConfig["carUser"]
        password = carConfig["carPassword"]

        country = "DE"  # Example country code
        spin = ""  # Optional, if required by the API
        api_level = 1  # Example API level
        print ("start async session")
        async with ClientSession() as session:
            # Initialize the AudiConnectAccount
            account = AudiConnectAccount(session, username, password, country, spin, api_level)

            # Log in to the Audi service
            print("Logging in to Audi Connect...")
            await account.login()

            # Update vehicle information
            print("Updating vehicle information...")
            await account.update(None)

            # Fetch and print the State of Charge (SOC) for each vehicle
            print("Fetching vehicle information...")
            for vehicle in account._vehicles:
                # Check Car 
                print("Checking vehicle:", vehicle.vin)

                soc = vehicle.state_of_charge
                self.SOC = float(soc)
                if self.newValue == 0:
                    self.newValue = 1
                else:
                    self.newValue = 0
                print("Audi charging power:", vehicle.charging_power)

                print(f"Audi Vehicle VIN: {vehicle.vin}, State of Charge: {soc}%")

