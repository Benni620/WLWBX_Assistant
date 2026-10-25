"""Sensors for WLWBX."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WlwbxEntity
from .const import DOMAIN

STATE_ICONS = {
    "Charging": "mdi:ev-station",
    "VehicleConnected": "mdi:car-electric",
    "Unplugged": "mdi:power-plug-off",
    "Error": "mdi:alert-circle",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data["wlwbx"][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = [
        WlwbxSensor(coordinator, entry, "state", "Ladezustand", icon="mdi:ev-station"),
        WlwbxSensor(
            coordinator, entry, "session_charging_rate", "Ladeleistung",
            device_class=SensorDeviceClass.POWER, unit=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        WlwbxSensor(
            coordinator, entry, "session_energy", "Energie aktuelle Session",
            device_class=SensorDeviceClass.ENERGY, unit=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        WlwbxSensor(
            coordinator, entry, "session_soc", "SOC",
            device_class=SensorDeviceClass.BATTERY, unit="%",
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:battery",
        ),
        WlwbxSensor(
            coordinator, entry, "session_target_soc", "Ziel SOC",
            device_class=SensorDeviceClass.BATTERY, unit="%",
            icon="mdi:battery-charging",
        ),
        WlwbxSensor(coordinator, entry, "session_remaining", "Restzeit Ladevorgang"),
        WlwbxSensor(
            coordinator, entry, "lifetime_energy", "Gesamtenergie",
            device_class=SensorDeviceClass.ENERGY, unit=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        WlwbxSensor(
            coordinator, entry, "lifetime_charging_time", "Gesamte Ladezeit",
            device_class=SensorDeviceClass.DURATION, unit=UnitOfTime.HOURS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            icon="mdi:clock-outline",
        ),
        WlwbxSensor(
            coordinator, entry, "curve_power_total", "Ladeleistung (Kurve)",
            device_class=SensorDeviceClass.POWER, unit=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:speedometer",
        ),
        WlwbxSensor(
            coordinator, entry, "curve_power_l1", "Ladeleistung L1",
            device_class=SensorDeviceClass.POWER, unit=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:speedometer",
        ),
        WlwbxSensor(
            coordinator, entry, "curve_power_l2", "Ladeleistung L2",
            device_class=SensorDeviceClass.POWER, unit=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:speedometer",
        ),
        WlwbxSensor(
            coordinator, entry, "curve_power_l3", "Ladeleistung L3",
            device_class=SensorDeviceClass.POWER, unit=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:speedometer",
        ),
        WlwbxSensor(
            coordinator, entry, "meter_energy", "Energiezähler",
            device_class=SensorDeviceClass.ENERGY, unit=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        WlwbxSensor(coordinator, entry, "system_state", "Systemzustand"),
        WlwbxSensor(coordinator, entry, "error_count", "Aktive Fehler",
                    icon="mdi:alert-circle"),
    ]
    async_add_entities(entities)


class WlwbxSensor(WlwbxEntity, SensorEntity):
    def __init__(
        self, coordinator, entry, kind: str, name: str,
        device_class=None, unit=None, state_class=None, icon=None,
    ) -> None:
        super().__init__(coordinator, entry, kind)
        self._attr_translation_key = None
        self._attr_name = f"Wallbox {name}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        if kind == "state" and icon is None:
            icon = "mdi:ev-station"
        self._attr_icon = icon

    def _value(self, kind: str) -> Any:
        data = self.coordinator.data
        if kind == "state":
            return (data.get("state") or {}).get("value")
        if kind.startswith("session_"):
            session = data.get("session") or {}
            if not session:
                return None
            if kind == "session_charging_rate":
                return session.get("chargingRate")
            if kind == "session_energy":
                wh = session.get("energyConsumption")
                return round(wh / 1000, 2) if wh is not None else None
            if kind == "session_soc":
                return session.get("latestSOC")
            if kind == "session_target_soc":
                return session.get("targetSOC")
            if kind == "session_remaining":
                return session.get("remainingTime")
        if kind == "lifetime_energy":
            wh = (data.get("lifetime") or {}).get("totalEnergy")
            return round(wh / 1000, 2) if wh is not None else None
        if kind == "lifetime_charging_time":
            secs = (data.get("lifetime") or {}).get("totalChargingTime")
            return round(secs / 3600, 1) if secs is not None else None
        if kind.startswith("curve_"):
            # Letzten Datenpunkt der Ladekurve auswerten.
            # Achtung: Leistungswerte der Kurve sind in kW!
            points = (data.get("charging_curve") or {}).get("curvePoints") or []
            if not points:
                return None
            last = points[-1]

            def _kw_to_w(kw: Any) -> float | None:
                return round(kw * 1000, 1) if kw is not None else None

            if kind == "curve_power_total":
                total = (
                    (last.get("powerL1") or 0)
                    + (last.get("powerL2") or 0)
                    + (last.get("powerL3") or 0)
                )
                return round(total * 1000, 1)
            if kind == "curve_power_l1":
                return _kw_to_w(last.get("powerL1"))
            if kind == "curve_power_l2":
                return _kw_to_w(last.get("powerL2"))
            if kind == "curve_power_l3":
                return _kw_to_w(last.get("powerL3"))
        if kind == "meter_energy":
            wh = (data.get("energy_meter") or {}).get("energyAmount")
            return round(wh / 1000, 2) if wh is not None else None
        if kind == "system_state":
            return (data.get("device_state") or {}).get("systemState")
        if kind == "error_count":
            errors = data.get("errors")
            if not isinstance(errors, list):
                return 0
            return len(
                [e for e in errors if (e or {}).get("status") == "active"]
            )
        return None

    @property
    def extra_state_attributes(self) -> dict | None:
        # Aktive Fehler als DTC-Liste, z.B. {"error_1": "DTCHIGHTEMP"}
        if self._kind != "error_count":
            return None
        errors = self.coordinator.data.get("errors")
        if not isinstance(errors, list):
            return None
        active = [e for e in errors if (e or {}).get("status") == "active"]
        return {f"error_{i + 1}": e.get("dtc") for i, e in enumerate(active)}

    @property
    def native_value(self) -> Any:
        return self._value(self._kind)

    @property
    def icon(self):
        if self._kind == "state":
            return STATE_ICONS.get(self.native_value, "mdi:ev-station")
        return self._attr_icon