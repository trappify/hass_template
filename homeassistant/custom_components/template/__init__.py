"""Template development integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the template integration."""
    hass.data.setdefault(DOMAIN, {})
    return True
