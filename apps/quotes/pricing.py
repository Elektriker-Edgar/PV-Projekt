from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

from .models import Product, Precheck
from .helpers import infer_inverter_class_key


VAT_RATE = Decimal("0.19")

PRECHECK_DEFAULTS: Dict[str, Decimal] = {
    "package_basis": Decimal("890.00"),
    "package_plus": Decimal("1490.00"),
    "package_pro": Decimal("2290.00"),
    "travel_zone_0": Decimal("0.00"),
    "travel_zone_30": Decimal("50.00"),
    "travel_zone_60": Decimal("95.00"),
    "surcharge_tt_grid": Decimal("150.00"),
    "surcharge_selective_fuse": Decimal("220.00"),
    "material_ac_wiring": Decimal("180.00"),
    "material_spd": Decimal("320.00"),
    "material_meter_upgrade": Decimal("450.00"),
    "material_storage_kwh": Decimal("800.00"),
    "wallbox_base_4kw": Decimal("890.00"),
    "wallbox_base_11kw": Decimal("1290.00"),
    "wallbox_base_22kw": Decimal("1690.00"),
    "wallbox_stand_mount": Decimal("350.00"),
    "wallbox_pv_surplus": Decimal("0.00"),
    "cable_wr_up_to_5kw": Decimal("15.00"),
    "cable_wr_5_to_10kw": Decimal("25.00"),
    "cable_wr_above_10kw": Decimal("35.00"),
    "cable_wb_4kw": Decimal("12.00"),
    "cable_wb_11kw": Decimal("20.00"),
    "cable_wb_22kw": Decimal("30.00"),
    "discount_complete_kit": Decimal("15.00"),
}


@dataclass
class PricingInput:
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
    """Hilfsklasse f\u00fcr alle Precheck-Preisbausteine aus dem Produktkatalog."""

    def __init__(self) -> None:
        sku_map = {key: _precheck_sku(key) for key in PRECHECK_DEFAULTS.keys()}
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


def _infer_travel_cost(address: str, catalog: PrecheckCatalog) -> Decimal:
    text = (address or "").lower()
    if "hamburg" in text:
        return catalog.value("travel_zone_0")
    if any(city in text for city in ["norderstedt", "ahrensburg", "pinneberg"]):
        return catalog.value("travel_zone_30")
    return catalog.value("travel_zone_60")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "on", "yes"}


def calculate_pricing(data: PricingInput) -> Dict[str, Decimal]:
    desired_power = Decimal(str(data.desired_power_kw or 0))
    storage_kwh = Decimal(str(data.storage_kwh or 0))
    distance = Decimal(str(data.distance_meter or 0))
    main_fuse = int(data.main_fuse_ampere or 0)
    grid_type = (data.grid_type or "").lower()

    inverter_class_key = infer_inverter_class_key(desired_power)

    catalog = PrecheckCatalog()

    if storage_kwh > 0:
        package = "pro"
    elif desired_power > 3 or inverter_class_key in {"5kva", "10kva"} or grid_type == "1p":
        package = "plus"
    else:
        package = "basis"

    base_price = {
        "basis": catalog.value("package_basis"),
        "plus": catalog.value("package_plus"),
        "pro": catalog.value("package_pro"),
    }[package]

    travel_cost = _infer_travel_cost(data.site_address, catalog)

    surcharges = Decimal("0.00")
    if grid_type == "1p":
        surcharges += catalog.value("surcharge_tt_grid")
    if main_fuse > 35:
        surcharges += catalog.value("surcharge_selective_fuse")
    if distance > 15:
        extra = distance - Decimal("15")
        if desired_power <= 5:
            price_per_meter = catalog.value("cable_wr_up_to_5kw")
        elif desired_power <= 10:
            price_per_meter = catalog.value("cable_wr_5_to_10kw")
        else:
            price_per_meter = catalog.value("cable_wr_above_10kw")
        surcharges += extra * price_per_meter

    inverter_cost = Decimal("0.00")
    storage_cost = Decimal("0.00")
    wallbox_cost = Decimal("0.00")

    if not data.own_components:
        inv_price_map = {
            "1kva": Decimal("800.00"),
            "3kva": Decimal("1200.00"),
            "5kva": Decimal("1800.00"),
            "10kva": Decimal("2800.00"),
        }
        inverter_cost = inv_price_map.get(inverter_class_key, Decimal("0.00"))
        inverter_cost += catalog.value("material_ac_wiring")
        if package in {"plus", "pro"}:
            inverter_cost += catalog.value("material_spd")
            inverter_cost += catalog.value("material_meter_upgrade")
        if package == "pro" and storage_kwh > 0:
            storage_cost = storage_kwh * catalog.value("material_storage_kwh")

    if data.has_wallbox:
        power = data.wallbox_power
        if power == "4kw":
            wallbox_cost += catalog.value("wallbox_base_4kw")
        elif power == "11kw":
            wallbox_cost += catalog.value("wallbox_base_11kw")
        elif power == "22kw":
            wallbox_cost += catalog.value("wallbox_base_22kw")

        if data.wallbox_mount == "stand":
            wallbox_cost += catalog.value("wallbox_stand_mount")

        if data.wallbox_pv_surplus:
            wallbox_cost += catalog.value("wallbox_pv_surplus")

        if not data.wallbox_cable_installed and data.wallbox_cable_length > 0:
            length = Decimal(str(data.wallbox_cable_length))
            if power == "4kw":
                price = catalog.value("cable_wb_4kw")
            elif power == "11kw":
                price = catalog.value("cable_wb_11kw")
            elif power == "22kw":
                price = catalog.value("cable_wb_22kw")
            else:
                price = Decimal("0.00")
            wallbox_cost += length * price

    material_cost = inverter_cost + storage_cost + wallbox_cost

    discount = Decimal("0.00")
    if not data.own_components:
        discount_value = catalog.value("discount_complete_kit")
        discount_product = catalog.product("discount_complete_kit")
        if discount_product and discount_product.unit == "percent":
            discount = (base_price * discount_value) / Decimal("100")
        else:
            discount = discount_value

    net_total = base_price + travel_cost + surcharges + material_cost - discount
    net_total = _quantize(net_total)
    vat_amount = _quantize(net_total * VAT_RATE)
    gross_total = _quantize(net_total + vat_amount)

    return {
        "package": package,
        "base_price": _quantize(base_price),
        "travel_cost": _quantize(travel_cost),
        "surcharges": _quantize(surcharges),
        "inverter_cost": _quantize(inverter_cost),
        "storage_cost": _quantize(storage_cost),
        "wallbox_cost": _quantize(wallbox_cost),
        "material_cost": _quantize(material_cost),
        "discount": _quantize(discount),
        "net_total": net_total,
        "vat_amount": vat_amount,
        "gross_total": gross_total,
    }


def pricing_input_from_request(data: Dict[str, Any]) -> PricingInput:
    def dec(key: str, fallback: str = None) -> Decimal:
        value = data.get(key)
        if value in (None, '') and fallback:
            value = data.get(fallback)
        if value in (None, ''):
            value = "0"
        return Decimal(str(value))

    return PricingInput(
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
        wallbox_pv_surplus=False,  # Placeholder bis Feature unterstützt wird
    )


def pricing_to_response(pricing: Dict[str, Decimal]) -> Dict[str, Any]:
    def f(value: Decimal) -> float:
        return float(value)

    return {
        "package": pricing["package"],
        "basePrice": f(pricing["base_price"]),
        "travelCost": f(pricing["travel_cost"]),
        "surcharges": f(pricing["surcharges"]),
        "inverterCost": f(pricing["inverter_cost"]),
        "storageCost": f(pricing["storage_cost"]),
        "wallboxCost": f(pricing["wallbox_cost"]),
        "materialCost": f(pricing["material_cost"]),
        "discount": f(pricing["discount"]),
        "totalNet": f(pricing["net_total"]),
        "vatAmount": f(pricing["vat_amount"]),
        "total": f(pricing["gross_total"]),
    }
