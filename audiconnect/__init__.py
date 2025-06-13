"""Standalone Audi Connect Integration."""

import logging
from datetime import timedelta

from .audi_account import AudiAccount

_LOGGER = logging.getLogger(__name__)

DEFAULT_UPDATE_INTERVAL = 15  # Default update interval in minutes
MIN_UPDATE_INTERVAL = 15  # Minimum update interval in minutes


class AudiConnectIntegration:
    def __init__(self, username, password, region="DE", api_level=0):
        """Initialize the Audi Connect Integration."""
        self.username = username
        self.password = password
        self.region = region
        self.api_level = api_level
        self.account = None

    async def setup(self):
        """Set up the Audi Connect Integration."""
        _LOGGER.debug("Setting up Audi Connect Integration...")
        self.account = AudiAccount(self.username, self.password, self.region, self.api_level)
        await self.account.init_connection()

    async def update(self):
        """Update the data from Audi Connect."""
        _LOGGER.debug("Updating data from Audi Connect...")
        if self.account:
            await self.account.update()
        else:
            _LOGGER.warning("Audi Account is not initialized.")

    async def unload(self):
        """Unload the Audi Connect Integration."""
        _LOGGER.debug("Unloading Audi Connect Integration...")
        self.account = None
