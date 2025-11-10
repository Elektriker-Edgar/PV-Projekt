from decimal import Decimal

from django.test import TestCase

from apps.quotes.models import Product
from apps.quotes.pricing import PricingInput, calculate_pricing


class PricingCatalogTests(TestCase):
    def setUp(self):
        self.package_basis = Product.objects.get(sku="PCHK-PACKAGE-BASIS")
        self.travel_zone_0 = Product.objects.get(sku="PCHK-TRAVEL-ZONE-0")
        self.discount = Product.objects.get(sku="PCHK-DISCOUNT-COMPLETE-KIT")

    def test_pricing_uses_catalog_values_and_percent_discount(self):
        self.package_basis.sales_price_net = Decimal("1234.00")
        self.package_basis.save(update_fields=["sales_price_net"])
        self.travel_zone_0.sales_price_net = Decimal("10.00")
        self.travel_zone_0.save(update_fields=["sales_price_net"])
        self.discount.unit = "percent"
        self.discount.sales_price_net = Decimal("10.00")
        self.discount.save(update_fields=["unit", "sales_price_net"])

        pricing_input = PricingInput(
            site_address="Hamburg",
            desired_power_kw=Decimal("2"),
            own_components=False,
        )
        pricing = calculate_pricing(pricing_input)

        self.assertEqual(pricing["base_price"], Decimal("1234.00"))
        self.assertEqual(pricing["travel_cost"], Decimal("10.00"))
        self.assertEqual(pricing["discount"], Decimal("123.40"))

    def test_pricing_supports_absolute_discount_value(self):
        self.discount.unit = "lump_sum"
        self.discount.sales_price_net = Decimal("250.00")
        self.discount.save(update_fields=["unit", "sales_price_net"])

        pricing_input = PricingInput(
            site_address="Hamburg",
            desired_power_kw=Decimal("2"),
            own_components=False,
        )
        pricing = calculate_pricing(pricing_input)

        self.assertEqual(pricing["discount"], Decimal("250.00"))
