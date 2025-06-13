import asyncio
from aiohttp import ClientSession
from audiconnect.audi_connect_account import AudiConnectAccount

async def get_vehicle_soc():
    """Fetch the State of Charge (SOC) for all vehicles associated with the Audi account."""
    # Hardcoded credentials (replace with your own)
    username = "t.weiberle@gmail.com"
    password = "Linux1234Audi!"
    country = "DE"  # Example country code
    spin = ""  # Optional, if required by the API
    api_level = 1  # Example API level

    async with ClientSession() as session:
        # Initialize the AudiConnectAccount
        account = AudiConnectAccount(session, username, password, country, spin, api_level)

        # Log in to the Audi service
        await account.login()

        # Update vehicle information
        await account.update(None)

        # Fetch and print the State of Charge (SOC) for each vehicle
        for vehicle in account._vehicles:
            soc = vehicle.state_of_charge
            print("charging power:", vehicle.charging_power)

            print(f"Vehicle VIN: {vehicle.vin}, State of Charge: {soc}%")

# Entry point for testing
if __name__ == "__main__":
    asyncio.run(get_vehicle_soc())