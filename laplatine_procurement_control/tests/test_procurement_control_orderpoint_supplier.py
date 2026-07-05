# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementControlOrderpointSupplier(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.company.laplatine_procurement_warehouse_id = cls.warehouse.id
        cls.indicators = cls.env["laplatine.procurement.indicators"]
        cls.vendor = cls.env["res.partner"].create({"name": "Vendor Orderpoint Test"})

    def _create_product(self, name):
        return self.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "purchase_ok": True,
                "standard_price": 1.0,
            }
        )

    def _create_sublocation(self, name):
        return self.env["stock.location"].create(
            {
                "name": name,
                "location_id": self.warehouse.lot_stock_id.id,
                "usage": "internal",
            }
        )

    def _create_orderpoint(self, product, location, min_qty, max_qty):
        return self.env["stock.warehouse.orderpoint"].create(
            {
                "product_id": product.id,
                "warehouse_id": self.warehouse.id,
                "location_id": location.id,
                "product_min_qty": min_qty,
                "product_max_qty": max_qty,
            }
        )

    def _create_supplierinfo(self, product, min_qty, delay):
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "delay": delay,
                "price": 1.0,
                "min_qty": min_qty,
            }
        )

    def test_orderpoint_in_sublocation_is_resolved(self):
        product = self._create_product("Sublocation OP Product")
        sublocation = self._create_sublocation("Conteneur Test")
        orderpoint = self._create_orderpoint(
            product, sublocation, min_qty=5000.0, max_qty=18250.0
        )

        result = self.indicators._resolve_orderpoint(product, self.warehouse)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["orderpoint"], orderpoint)

    def test_multiple_orderpoints_in_warehouse_is_ambiguous(self):
        product = self._create_product("Ambiguous OP Product")
        sub_a = self._create_sublocation("Zone A")
        sub_b = self._create_sublocation("Zone B")
        self._create_orderpoint(product, sub_a, min_qty=100.0, max_qty=200.0)
        self._create_orderpoint(product, sub_b, min_qty=300.0, max_qty=400.0)

        result = self.indicators._resolve_orderpoint(product, self.warehouse)

        self.assertEqual(result["status"], "ambiguous")
        self.assertFalse(result["orderpoint"])

    def test_seller_selected_with_procurement_lot_qty(self):
        product = self._create_product("Lot Seller Product")
        sublocation = self._create_sublocation("Lot Test")
        self._create_orderpoint(
            product, sublocation, min_qty=5000.0, max_qty=18250.0
        )
        self._create_supplierinfo(product, min_qty=18250.0, delay=90)

        evaluation = self.indicators.evaluate_product(product, self.company)
        line_values = evaluation["line_values"]

        self.assertEqual(line_values["min_qty"], 5000.0)
        self.assertEqual(line_values["max_qty"], 18250.0)
        self.assertEqual(line_values["supplier_id"], self.vendor.id)
        self.assertEqual(line_values["supplier_delay"], 90)
        self.assertNotIn("supplier_missing", evaluation["alert_codes"])
        self.assertNotIn("orderpoint_incomplete", evaluation["alert_codes"])

    def test_history_insufficient_keeps_insufficient_data_status(self):
        product = self._create_product("History Insufficient Product")
        sublocation = self._create_sublocation("History Test")
        self._create_orderpoint(
            product, sublocation, min_qty=5000.0, max_qty=18250.0
        )
        self._create_supplierinfo(product, min_qty=18250.0, delay=90)

        evaluation = self.indicators.evaluate_product(product, self.company)

        self.assertEqual(evaluation["risk_status"], "insufficient_data")
        self.assertIn("history_insufficient", evaluation["alert_codes"])
        self.assertEqual(evaluation["line_values"]["supplier_id"], self.vendor.id)
