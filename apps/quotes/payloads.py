from decimal import Decimal
from typing import Any, Dict, Mapping

from .models import Precheck


PRICING_FIELD_ALIASES = {
    "building_type": ["building_type", "site_building_type"],
    "site_address": ["site_address", "customer_address", "address"],
    "main_fuse_ampere": ["main_fuse_ampere"],
    "grid_type": ["grid_type", "site_grid_type"],
    "distance_meter": ["distance_meter", "distance_meter_to_inverter", "distance_meter_to_hak"],
    "desired_power_kw": ["desired_power_kw"],
    "storage_kwh": ["storage_kwh"],
    "own_components": ["own_components"],
    "has_wallbox": ["has_wallbox", "wallbox"],
    "wallbox_power": ["wallbox_power", "wallbox_class"],
    "wallbox_mount": ["wallbox_mount"],
    "wallbox_cable_installed": ["wallbox_cable_installed", "wallbox_cable_prepared"],
    "wallbox_cable_length": ["wallbox_cable_length", "wallbox_cable_length_m"],
    "wallbox_pv_surplus": ["wallbox_pv_surplus"],
}


def normalize_pricing_payload(data: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Vereinheitlicht eingegebene Daten (Wizard, API, Tests) auf den
    gemeinsamen Pricing-Namensraum. Füllt nur Felder, die einen Wert haben.
    """
    normalized: Dict[str, Any] = {}
    for field, aliases in PRICING_FIELD_ALIASES.items():
        for alias in aliases:
            if alias not in data:
                continue
            value = data[alias]
            if value in ("", None):
                continue
            normalized[field] = value
            break
    return normalized


def payload_from_precheck(precheck: Precheck) -> Dict[str, Any]:
    """
    Erstellt denselben Pricing-Payload aus einem Precheck-Objekt.
    Dadurch nutzen API/Wizard und Precheck denselben Namensraum.
    """
    site = precheck.site
    distance_value = (
        precheck.distance_meter_to_inverter
        or getattr(site, "distance_meter_to_hak", None)
        or Decimal("0")
    )
    wallbox_length = precheck.wallbox_cable_length_m or Decimal("0")
    return {
        "building_type": getattr(site, "building_type", "") or (precheck.building_type or ""),
        "site_address": getattr(site, "address", ""),
        "main_fuse_ampere": getattr(site, "main_fuse_ampere", 0) or 0,
        "grid_type": (getattr(site, "grid_type", "") or "").lower(),
        "distance_meter": distance_value,
        "desired_power_kw": precheck.desired_power_kw or Decimal("0"),
        "storage_kwh": precheck.storage_kwh or Decimal("0"),
        "own_components": precheck.own_components,
        "has_wallbox": precheck.wallbox,
        "wallbox_power": precheck.wallbox_class or "",
        "wallbox_mount": precheck.wallbox_mount or "",
        "wallbox_cable_installed": precheck.wallbox_cable_prepared,
        "wallbox_cable_length": wallbox_length,
        "wallbox_pv_surplus": precheck.wallbox_pv_surplus,
    }
