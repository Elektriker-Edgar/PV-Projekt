from decimal import Decimal

from django.test import TestCase

from apps.quotes.models import Product
from apps.quotes.pricing import PricingInput, calculate_pricing


class PricingCatalogTests(TestCase):
    def _set_price(self, sku: str, value: Decimal):
        Product.objects.filter(sku=sku).update(sales_price_net=value)

    def test_pricing_sums_expected_components(self):
        # Ensure predictable catalog values
        self._set_price("PCHK-BUILDING-MFH", Decimal("100.00"))
        self._set_price("PCHK-GRID-1P", Decimal("100.00"))
        self._set_price("PCHK-INVERTER-TIER-10", Decimal("1500.00"))
        self._set_price("PCHK-STORAGE-TIER-5", Decimal("1300.00"))
        self._set_price("PCHK-WR-CABLE-PM-LT10", Decimal("5.00"))

        pricing_input = PricingInput(
            building_type='mfh',
            grid_type='1p',
            desired_power_kw=Decimal("6"),
            storage_kwh=Decimal("4"),
            distance_meter=Decimal("12"),
        )
        pricing = calculate_pricing(pricing_input)

        self.assertEqual(pricing["building_surcharge"], Decimal("100.00"))
        self.assertEqual(pricing["grid_surcharge"], Decimal("100.00"))
        self.assertEqual(pricing["inverter_price"], Decimal("1500.00"))
        self.assertEqual(pricing["storage_price"], Decimal("1300.00"))
        self.assertEqual(pricing["wr_cable_cost"], Decimal("60.00"))
        self.assertEqual(pricing["net_total"], Decimal("3060.00"))
        self.assertEqual(pricing["vat_amount"], Decimal("581.40"))
        self.assertEqual(pricing["gross_total"], Decimal("3641.40"))

    def test_pricing_includes_wallbox_components(self):
        self._set_price("PCHK-INVERTER-TIER-20", Decimal("2000.00"))
        self._set_price("PCHK-WR-CABLE-PM-LT20", Decimal("15.00"))
        self._set_price("PCHK-WALLBOX-BASE-11KW", Decimal("500.00"))
        self._set_price("PCHK-WALLBOX-CABLE-PM-LT20", Decimal("14.00"))
        self._set_price("PCHK-WALLBOX-MOUNT-STAND", Decimal("200.00"))
        self._set_price("PCHK-WALLBOX-PV-SURPLUS", Decimal("200.00"))

        pricing_input = PricingInput(
            building_type='efh',
            grid_type='3p',
            desired_power_kw=Decimal("12"),
            distance_meter=Decimal("20"),
            has_wallbox=True,
            wallbox_power="11kw",
            wallbox_mount="stand",
            wallbox_cable_installed=False,
            wallbox_cable_length=Decimal("10"),
            wallbox_pv_surplus=True,
        )
        pricing = calculate_pricing(pricing_input)

        self.assertEqual(pricing["inverter_price"], Decimal("2000.00"))
        self.assertEqual(pricing["wr_cable_cost"], Decimal("300.00"))
        self.assertEqual(pricing["wallbox_base_price"], Decimal("500.00"))
        self.assertEqual(pricing["wallbox_cable_cost"], Decimal("140.00"))
        self.assertEqual(pricing["wallbox_extra_cost"], Decimal("400.00"))
        self.assertEqual(pricing["net_total"], Decimal("3340.00"))
        self.assertEqual(pricing["gross_total"], Decimal("3974.60"))
