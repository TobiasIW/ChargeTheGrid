import asyncio
import logging
from aiohttp import ClientSession

from .audi_connect_account import AudiConnectAccount, AudiConnectObserver
from .audi_models import VehicleData

_LOGGER = logging.getLogger(__name__)

class AudiAccount(AudiConnectObserver):
    def __init__(self, username, password, country, spin, api_level):
        """Initialize the component state."""
        self.username = username
        self.password = password
        self.country = country
        self.spin = spin
        self.api_level = api_level
        self.config_vehicles = set()
        self.vehicles = set()
        self.connection = None

    async def init_connection(self):
        async with ClientSession() as session:
            self.connection = AudiConnectAccount(
                session=session,
                username=self.username,
                password=self.password,
                country=self.country,
                spin=self.spin,
                api_level=self.api_level,
            )
            self.connection.add_observer(self)

    async def discover_vehicles(self, vehicles):
        if len(vehicles) > 0:
            for vehicle in vehicles:
                vin = vehicle.vin.lower()

                self.vehicles.add(vin)

                cfg_vehicle = VehicleData()
                cfg_vehicle.vehicle = vehicle
                self.config_vehicles.add(cfg_vehicle)

                # Log discovered vehicle data
                _LOGGER.info(f"Discovered vehicle: VIN={vin}, Model={vehicle.model}")

    async def update(self):
        """Update status from the cloud."""
        _LOGGER.debug("Starting refresh cloud data...")
        if not await self.connection.update(None):
            _LOGGER.warning("Failed refresh cloud data")
            return False

        # Discover new vehicles that have not been added yet
        new_vehicles = [
            x for x in self.connection._vehicles if x.vin not in self.vehicles
        ]
        if new_vehicles:
            _LOGGER.debug("Retrieved %d vehicle(s)", len(new_vehicles))
        await self.discover_vehicles(new_vehicles)

        _LOGGER.debug("Successfully refreshed cloud data")
        return True

    async def execute_vehicle_action(self, vin, action):
        if action == "lock":
            await self.connection.set_vehicle_lock(vin, True)
        if action == "unlock":
            await self.connection.set_vehicle_lock(vin, False)
        if action == "start_climatisation":
            await self.connection.set_vehicle_climatisation(vin, True)
        if action == "stop_climatisation":
            await self.connection.set_vehicle_climatisation(vin, False)
        if action == "start_charger":
            await self.connection.set_battery_charger(vin, True, False)
        if action == "start_timed_charger":
            await self.connection.set_battery_charger(vin, True, True)
        if action == "stop_charger":
            await self.connection.set_battery_charger(vin, False, False)
        if action == "start_preheater":
            await self.connection.set_vehicle_pre_heater(vin, True)
        if action == "stop_preheater":
            await self.connection.set_vehicle_pre_heater(vin, False)
        if action == "start_window_heating":
            await self.connection.set_vehicle_window_heating(vin, True)
        if action == "stop_window_heating":
            await self.connection.set_vehicle_window_heating(vin, False)

    async def handle_notification(self, vin: str, action: str) -> None:
        await self._refresh_vehicle_data(vin)

    async def refresh_vehicle_data(self, vin):
        await self._refresh_vehicle_data(vin)

    async def _refresh_vehicle_data(self, vin):
        redacted_vin = "*" * (len(vin) - 4) + vin[-4:]
        res = await self.connection.refresh_vehicle_data(vin)

        if res is True:
            _LOGGER.debug("Refresh vehicle data successful for VIN: %s", redacted_vin)
        elif res == "disabled":
            _LOGGER.debug("Refresh vehicle data is disabled for VIN: %s", redacted_vin)
        else:
            _LOGGER.debug("Refresh vehicle data failed for VIN: %s", redacted_vin)

        _LOGGER.debug("Requesting to refresh cloud data in 10 seconds...")
        await asyncio.sleep(10)

        try:
            _LOGGER.debug("Requesting to refresh cloud data now...")
            await self.update()
        except Exception as e:
            _LOGGER.exception("Refresh cloud data failed: %s", str(e))
