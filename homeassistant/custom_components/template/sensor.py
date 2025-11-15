"""Simple sensor used for template development."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_platform(
    hass: HomeAssistant, config: dict, async_add_entities: AddEntitiesCallback, discovery_info=None
) -> None:
    """Set up the template sensor."""
    async_add_entities([TemplateHelloWorldSensor()])


class TemplateHelloWorldSensor(SensorEntity):
    """Sensor that mirrors current time every minute."""

    _attr_name = "Template Clock"
    _attr_native_unit_of_measurement = None
    _attr_unique_id = "template_clock"

    async def async_update(self) -> None:
        """Update the sensor state."""
        self._attr_native_value = datetime.utcnow().isoformat()
