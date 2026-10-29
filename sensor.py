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

# API-Wert -> Key in den WebUI-locales (common.chargingState*)
CHARGING_STATE_LOCALE_KEYS = {
    "Unplugged": "chargingStateUnplugged",
    "VehicleConnected": "chargingStateVehicleConnected",
    "Authorizing": "chargingStateAuthorizing",
    "Charging": "chargingStateCharging",
    "ISOCharging": "chargingStateISOCharging",
    "Paused": "chargingStatePaused",
    "ChargingComplete": "chargingStateComplete",
    "Error": "chargingStateError",
    "Disabled": "chargingStateDeactivated",
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
        WlwbxSensor(coordinator, entry, "error_count", "Aktive Fehler",
                    icon="mdi:alert-circle"),
        WlwbxSensor(coordinator, entry, "passive_error_count", "Passive Fehler",
                    icon="mdi:alert-circle-outline"),
        WlwbxSensor(
            coordinator, entry, "temp_relay", "Temperatur Relais",
            device_class=SensorDeviceClass.TEMPERATURE, unit="°C",
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer",
        ),
        WlwbxSensor(
            coordinator, entry, "temp_input", "Temperatur Eingangspfad",
            device_class=SensorDeviceClass.TEMPERATURE, unit="°C",
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer",
        ),
        WlwbxSensor(
            coordinator, entry, "temp_output", "Temperatur Ausgangspfad",
            device_class=SensorDeviceClass.TEMPERATURE, unit="°C",
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer",
        ),
        WlwbxSensor(
            coordinator, entry, "temp_power_controller", "Temperatur Power-Controller",
            device_class=SensorDeviceClass.TEMPERATURE, unit="°C",
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer",
        ),
        WlwbxSensor(
            coordinator, entry, "temp_comm_controller", "Temperatur Kommunikations-Controller",
            device_class=SensorDeviceClass.TEMPERATURE, unit="°C",
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer",
        ),
        WlwbxSensor(
            coordinator, entry, "temp_emmc", "Temperatur eMMC",
            device_class=SensorDeviceClass.TEMPERATURE, unit="°C",
            state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer",
        ),
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
            raw = (data.get("state") or {}).get("value")
            # Anzeige übersetzen (Sprache folgt HA-Sprache); roher API-Wert
            # bleibt als Attribut state_raw erhalten (für Automatisierungen).
            key = CHARGING_STATE_LOCALE_KEYS.get(raw)
            if key:
                localized = self._locale("common", key)
                if localized:
                    return localized
            return raw
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
        if kind.startswith("temp_"):
            # /system/device-temperatures, Werte in °Celsius
            temps = data.get("temperatures") or {}
            field = {
                "temp_relay": "relayTemperature",
                "temp_input": "inputPathTemperature",
                "temp_output": "outputPathTemperature",
                "temp_power_controller": "powerControllerTemperature",
                "temp_comm_controller": "communicationControllerTemperature",
                "temp_emmc": "eMmcTemperature",
            }.get(kind)
            return temps.get(field) if field else None
        if kind == "error_count":
            errors = data.get("errors")
            if not isinstance(errors, list):
                return 0
            return len(
                [e for e in errors if (e or {}).get("status") == "active"]
            )
        if kind == "passive_error_count":
            errors = data.get("errors")
            if not isinstance(errors, list):
                return 0
            return len(
                [e for e in errors if (e or {}).get("status") == "passive"]
            )
        return None

    def _errors_by_status(self, status: str) -> list[dict]:
        errors = self.coordinator.data.get("errors")
        if not isinstance(errors, list):
            return []
        return [e for e in errors if (e or {}).get("status") == status]

    def _locale(self, *path) -> Any:
        """Wert aus den WebUI-locales laden (Sprache folgt HA-Sprache)."""
        locales = self.coordinator.data.get("locales") or {}
        # genau eine Sprache ist geladen (de oder en)
        node: Any = next(iter(locales.values()), None) or {}
        for part in path:
            if not isinstance(node, dict):
                return None
            node = node.get(part)
            if node is None:
                return None
        return node

    def _dtc_text(self, table: str, dtc: str | None) -> str | None:
        """DTC über faultManagement.errorCause / .correctiveAction auflösen."""
        if not dtc:
            return None
        table_data = self._locale("faultManagement", table) or {}
        if dtc in table_data:
            return table_data[dtc]
        for key, value in table_data.items():
            if str(key).lower() == str(dtc).lower():
                return value
        return None

    @property
    def extra_state_attributes(self) -> dict | None:
        # Ladezustand: deutsche Bezeichnung aus den WebUI-locales
        if self._kind == "state":
            raw = (self.coordinator.data.get("state") or {}).get("value")
            attrs = {"state_raw": raw}
            key = CHARGING_STATE_LOCALE_KEYS.get(raw)
            if key:
                attrs["state_localized"] = self._locale("common", key)
            return attrs

        # Fehler-Details (DTC, Ursache, Abhilfemaßnahme, Kategorie, Zeitstempel)
        if self._kind == "error_count":
            status = "active"
        elif self._kind == "passive_error_count":
            status = "passive"
        else:
            return None
        attrs: dict = {}
        for i, err in enumerate(self._errors_by_status(status)):
            category = err.get("category")
            attrs[f"error_{i + 1}"] = {
                "dtc": err.get("dtc"),
                "description": self._dtc_text("errorCause", err.get("dtc")),
                "corrective_action": self._dtc_text(
                    "correctiveAction", err.get("dtc")
                ),
                "category": category,
                "category_localized": (
                    self._locale("faultManagement", category)
                    if category
                    else None
                ),
                "timestamp": err.get("timestamp"),
            }
        return attrs

    @property
    def native_value(self) -> Any:
        return self._value(self._kind)

    @property
    def icon(self):
        if self._kind == "state":
            # Icon nach rohem API-Wert (Sensor zeigt die Übersetzung)
            raw = (self.coordinator.data.get("state") or {}).get("value")
            return STATE_ICONS.get(raw, "mdi:ev-station")
        return self._attr_icon