from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional

from .models import Product, Precheck


VAT_RATE = Decimal("0.19")

PRECHECK_DEFAULTS: Dict[str, Decimal] = {
    # Gebäude & Netz
    "building_efh": Decimal("0.00"),
    "building_mfh": Decimal("100.00"),
    "building_commercial": Decimal("50.00"),
    "grid_1p": Decimal("100.00"),
    "grid_3p": Decimal("0.00"),
    # Wechselrichter
    "inverter_tier_3": Decimal("700.00"),
    "inverter_tier_5": Decimal("1000.00"),
    "inverter_tier_10": Decimal("1500.00"),
    "inverter_tier_20": Decimal("2000.00"),
    "inverter_tier_30": Decimal("2200.00"),
    # Speicher
    "storage_tier_3": Decimal("1000.00"),
    "storage_tier_5": Decimal("1300.00"),
    "storage_tier_10": Decimal("2000.00"),
    # Kabelpreise
    "wr_cable_pm_lt10": Decimal("5.00"),
    "wr_cable_pm_lt20": Decimal("15.00"),
    "wr_cable_pm_lt30": Decimal("22.00"),
    "wallbox_cable_pm_lt11": Decimal("7.00"),
    "wallbox_cable_pm_lt20": Decimal("14.00"),
    # Wallbox-Basiskosten & Extras
    "wallbox_base_4kw": Decimal("300.00"),
    "wallbox_base_11kw": Decimal("500.00"),
    "wallbox_base_22kw": Decimal("800.00"),
    "wallbox_mount_stand": Decimal("200.00"),
    "wallbox_pv_surplus": Decimal("200.00"),
    # Pakete
    "package_basis": Decimal("890.00"),
    "package_plus": Decimal("1490.00"),
    "package_pro": Decimal("2290.00"),
}

INVERTER_TIERS = [
    (Decimal("3"), "inverter_tier_3"),
    (Decimal("5"), "inverter_tier_5"),
    (Decimal("10"), "inverter_tier_10"),
    (Decimal("20"), "inverter_tier_20"),
    (Decimal("30"), "inverter_tier_30"),
]

STORAGE_TIERS = [
    (Decimal("3"), "storage_tier_3"),
    (Decimal("5"), "storage_tier_5"),
    (Decimal("10"), "storage_tier_10"),
]

WR_CABLE_TIERS = [
    (Decimal("10"), "wr_cable_pm_lt10"),
    (Decimal("20"), "wr_cable_pm_lt20"),
    (Decimal("30"), "wr_cable_pm_lt30"),
]


@dataclass
class PricingInput:
    building_type: str = ""
    site_address: str = ""
    main_fuse_ampere: int = 0
    grid_type: str = ""
    distance_meter: Decimal = Decimal("0")
    desired_power_kw: Decimal = Decimal("0")
    storage_kwh: Decimal = Decimal("0")
    own_components: bool = False
    has_wallbox: bool = False
    wallbox_power: str = ""
    wallbox_mount: str = ""
    wallbox_cable_installed: bool = False
    wallbox_cable_length: Decimal = Decimal("0")
    wallbox_pv_surplus: bool = False


def _precheck_sku(key: str) -> str:
    return f"PCHK-{key.upper().replace('_', '-')}"


class PrecheckCatalog:
    """Lädt alle Precheck-Preisbausteine aus dem Produktkatalog."""

    def __init__(self) -> None:
        sku_map = {key: _precheck_sku(key) for key in PRECHECK_DEFAULTS}
        products = Product.objects.filter(
            sku__in=sku_map.values(),
            is_active=True,
        )
        self._products: Dict[str, Product] = {}
        reverse_lookup = {sku: key for key, sku in sku_map.items()}
        for product in products:
            key = reverse_lookup.get(product.sku)
            if key:
                self._products[key] = product

    def value(self, key: str) -> Decimal:
        product = self._products.get(key)
        if product:
            return product.sales_price_net
        return PRECHECK_DEFAULTS[key]

    def product(self, key: str) -> Optional[Product]:
        return self._products.get(key)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "on", "yes"}


def _price_for_tier(value: Decimal, tiers, catalog: PrecheckCatalog) -> Decimal:
    for limit, key in tiers:
        if value <= limit:
            return catalog.value(key)
    # Fallback auf letzte Stufe
    return catalog.value(tiers[-1][1])


def _building_surcharge(building_type: str, catalog: PrecheckCatalog) -> Decimal:
    mapping = {
        "mfh": "building_mfh",
        "commercial": "building_commercial",
        "efh": "building_efh",
    }
    key = mapping.get(building_type or "efh", "building_efh")
    return catalog.value(key)


def _grid_surcharge(grid_type: str, catalog: PrecheckCatalog) -> Decimal:
    if (grid_type or "").lower() == "1p":
        return catalog.value("grid_1p")
    return catalog.value("grid_3p")


def _inverter_price(desired_power: Decimal, catalog: PrecheckCatalog) -> Decimal:
    if desired_power <= 0:
        return Decimal("0.00")
    return _price_for_tier(desired_power, INVERTER_TIERS, catalog)


def _storage_price(storage_kwh: Decimal, catalog: PrecheckCatalog) -> Decimal:
    if storage_kwh <= 0:
        return Decimal("0.00")
    return _price_for_tier(storage_kwh, STORAGE_TIERS, catalog)


def _wr_cable_price(desired_power: Decimal, distance: Decimal, catalog: PrecheckCatalog) -> Decimal:
    if distance <= 0:
        return Decimal("0.00")
    price_per_meter = _price_for_tier(desired_power if desired_power > 0 else Decimal("0"), WR_CABLE_TIERS, catalog)
    return distance * price_per_meter


def _wallbox_prices(data: PricingInput, catalog: PrecheckCatalog) -> Dict[str, Decimal]:
    if not data.has_wallbox:
        return {
            "wallbox_base_price": Decimal("0.00"),
            "wallbox_cable_cost": Decimal("0.00"),
            "wallbox_extra_cost": Decimal("0.00"),
        }

    base = Decimal("0.00")
    if data.wallbox_power == "4kw":
        base = catalog.value("wallbox_base_4kw")
    elif data.wallbox_power == "11kw":
        base = catalog.value("wallbox_base_11kw")
    elif data.wallbox_power == "22kw":
        base = catalog.value("wallbox_base_22kw")

    cable_cost = Decimal("0.00")
    cable_length = Decimal(str(data.wallbox_cable_length or 0))
    if not data.wallbox_cable_installed and cable_length > 0:
        if data.wallbox_power == "4kw":
            price_per_meter = catalog.value("wallbox_cable_pm_lt11")
        else:
            price_per_meter = catalog.value("wallbox_cable_pm_lt20")
        cable_cost = cable_length * price_per_meter

    extras = Decimal("0.00")
    if data.wallbox_mount == "stand":
        extras += catalog.value("wallbox_mount_stand")
    if data.wallbox_pv_surplus:
        extras += catalog.value("wallbox_pv_surplus")

    return {
        "wallbox_base_price": base,
        "wallbox_cable_cost": cable_cost,
        "wallbox_extra_cost": extras,
    }


def calculate_pricing(data: PricingInput) -> Dict[str, Decimal]:
    catalog = PrecheckCatalog()
    desired_power = Decimal(str(data.desired_power_kw or 0))
    storage_kwh = Decimal(str(data.storage_kwh or 0))
    distance = Decimal(str(data.distance_meter or 0))

    building_surcharge = _building_surcharge(data.building_type, catalog)
    grid_surcharge = _grid_surcharge(data.grid_type, catalog)
    inverter_price = _inverter_price(desired_power, catalog)
    storage_price = _storage_price(storage_kwh, catalog)
    wr_cable_cost = _wr_cable_price(desired_power, distance, catalog)
    wallbox_prices = _wallbox_prices(data, catalog)

    components = {
        "building_surcharge": _quantize(building_surcharge),
        "grid_surcharge": _quantize(grid_surcharge),
        "inverter_price": _quantize(inverter_price),
        "storage_price": _quantize(storage_price),
        "wr_cable_cost": _quantize(wr_cable_cost),
        "wallbox_base_price": _quantize(wallbox_prices["wallbox_base_price"]),
        "wallbox_cable_cost": _quantize(wallbox_prices["wallbox_cable_cost"]),
        "wallbox_extra_cost": _quantize(wallbox_prices["wallbox_extra_cost"]),
    }

    net_total = _quantize(sum(components.values()))
    vat_amount = _quantize(net_total * VAT_RATE)
    gross_total = _quantize(net_total + vat_amount)

    result = {
        **components,
        "net_total": net_total,
        "vat_amount": vat_amount,
        "gross_total": gross_total,
    }
    return result


def pricing_input_from_request(data: Dict[str, Any]) -> PricingInput:
    def dec(key: str, fallback: str = None) -> Decimal:
        value = data.get(key)
        if value in (None, "") and fallback:
            value = data.get(fallback)
        if value in (None, ""):
            value = "0"
        return Decimal(str(value))

    return PricingInput(
        building_type=(data.get("building_type") or "efh").lower(),
        site_address=data.get("site_address") or "",
        main_fuse_ampere=int(data.get("main_fuse_ampere") or 0),
        grid_type=(data.get("grid_type") or "").lower(),
        distance_meter=dec("distance_meter_to_inverter", fallback="distance_meter_to_hak"),
        desired_power_kw=dec("desired_power_kw"),
        storage_kwh=dec("storage_kwh"),
        own_components=_as_bool(data.get("own_components")),
        has_wallbox=_as_bool(data.get("has_wallbox")),
        wallbox_power=data.get("wallbox_power") or "",
        wallbox_mount=data.get("wallbox_mount") or "",
        wallbox_cable_installed=_as_bool(data.get("wallbox_cable_installed")),
        wallbox_cable_length=dec("wallbox_cable_length"),
        wallbox_pv_surplus=_as_bool(data.get("wallbox_pv_surplus")),
    )


def pricing_input_from_precheck(precheck: Precheck) -> PricingInput:
    site = precheck.site
    return PricingInput(
        building_type=getattr(site, "building_type", "efh"),
        site_address=getattr(site, "address", ""),
        main_fuse_ampere=site.main_fuse_ampere,
        grid_type=(site.grid_type or "").lower(),
        distance_meter=site.distance_meter_to_hak,
        desired_power_kw=precheck.desired_power_kw,
        storage_kwh=precheck.storage_kwh or Decimal("0"),
        own_components=precheck.own_components,
        has_wallbox=getattr(precheck, "wallbox", False),
        wallbox_power=getattr(precheck, "wallbox_class", "") or "",
        wallbox_mount=getattr(precheck, "wallbox_mount", "") or "",
        wallbox_cable_installed=getattr(precheck, "wallbox_cable_prepared", False),
        wallbox_cable_length=getattr(precheck, "wallbox_cable_length_m", Decimal("0")) or Decimal("0"),
        wallbox_pv_surplus=getattr(precheck, "wallbox_pv_surplus", False),
    )


def pricing_to_response(pricing: Dict[str, Decimal]) -> Dict[str, Any]:
    def f(value: Decimal) -> float:
        return float(value)

    return {
        "buildingSurcharge": f(pricing["building_surcharge"]),
        "gridSurcharge": f(pricing["grid_surcharge"]),
        "inverterPrice": f(pricing["inverter_price"]),
        "storagePrice": f(pricing["storage_price"]),
        "wrCableCost": f(pricing["wr_cable_cost"]),
        "wallboxBasePrice": f(pricing["wallbox_base_price"]),
        "wallboxCableCost": f(pricing["wallbox_cable_cost"]),
        "wallboxExtraCost": f(pricing["wallbox_extra_cost"]),
        "totalNet": f(pricing["net_total"]),
        "vatAmount": f(pricing["vat_amount"]),
        "total": f(pricing["gross_total"]),
    }
