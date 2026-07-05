# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementControlRefresh(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.production_location = cls.env["stock.location"].search(
            [("usage", "=", "production")], limit=1
        )
        cls.vendor = cls.env["res.partner"].create({"name": "Vendor Refresh Test"})
        cls.indicators = cls.env["laplatine.procurement.indicators"]
        cls.control_line = cls.env["laplatine.procurement.control.line"]
        cls.env.ref(
            "laplatine_procurement_control.group_procurement_control_manager"
        ).users = [(4, cls.env.uid)]

    def _create_product(self, name):
        return self.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "purchase_ok": True,
                "standard_price": 1.0,
            }
        )

    def _set_stock(self, product, quantity):
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "inventory_quantity": quantity,
            }
        ).action_apply_inventory()

    def _create_orderpoint(self, product, min_qty=50.0, max_qty=200.0):
        return self.env["stock.warehouse.orderpoint"].create(
            {
                "product_id": product.id,
                "warehouse_id": self.warehouse.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "product_min_qty": min_qty,
                "product_max_qty": max_qty,
            }
        )

    def _create_supplierinfo(self, product, delay=5):
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "delay": delay,
                "price": 1.0,
                "min_qty": 1.0,
            }
        )

    def _create_done_move(self, product, qty, move_date):
        move = self.env["stock.move"].create(
            {
                "name": "Consumption test",
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.production_location.id,
                "date": fields.Datetime.to_datetime(move_date),
            }
        )
        move._action_confirm()
        move._action_assign()
        move.quantity = qty
        move.picked = True
        move._action_done()
        move.write({"date": fields.Datetime.to_datetime(move_date)})
        move.move_line_ids.write({"date": fields.Datetime.to_datetime(move_date)})
        return move

    def test_build_risk_input_without_warehouse(self):
        self.company.laplatine_procurement_warehouse_id = False
        product = self._create_product("No Warehouse Product")
        risk_input = self.indicators.build_risk_input(product, self.company)
        self.assertFalse(risk_input.warehouse_configured)

        result = self.indicators.evaluate_product(product, self.company)
        self.assertEqual(result["risk_status"], "insufficient_data")

    def test_action_refresh_creates_line_with_matrix_result(self):
        self.company.write(
            {
                "laplatine_procurement_warehouse_id": self.warehouse.id,
                "laplatine_procurement_consumption_days": 10,
                "laplatine_procurement_min_history_days": 3,
                "laplatine_procurement_watch_lead_days": 7,
            }
        )
        product = self._create_product("Refresh Product")
        self._set_stock(product, 200.0)
        self._create_orderpoint(product, min_qty=50.0)
        self._create_supplierinfo(product, delay=5)
        move_date = fields.Date.today() - timedelta(days=5)
        self._create_done_move(product, 100.0, move_date)

        self.control_line.action_refresh()
        line = self.control_line.search(
            [("product_id", "=", product.id), ("company_id", "=", self.company.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.qty_available, 100.0)
        self.assertAlmostEqual(line.daily_consumption, 10.0)
        self.assertEqual(line.min_qty, 50.0)
        self.assertTrue(line.risk_status)
        self.assertTrue(line.risk_reason)
        self.assertTrue(line.last_refresh)
        self.assertEqual(line.refreshed_by_id, self.env.user)

    def test_refresh_uses_company_watch_lead_days(self):
        self.company.write(
            {
                "laplatine_procurement_warehouse_id": self.warehouse.id,
                "laplatine_procurement_consumption_days": 10,
                "laplatine_procurement_min_history_days": 3,
                "laplatine_procurement_watch_lead_days": 10,
            }
        )
        product = self._create_product("Watch Lead Product")
        self._set_stock(product, 200.0)
        self._create_orderpoint(product, min_qty=50.0)
        self._create_supplierinfo(product, delay=1)
        move_date = fields.Date.today() - timedelta(days=5)
        self._create_done_move(product, 100.0, move_date)

        risk_input = self.indicators.build_risk_input(product, self.company)
        self.assertEqual(risk_input.watch_lead_days, 10)

    def test_refresh_removes_obsolete_lines(self):
        self.company.laplatine_procurement_warehouse_id = self.warehouse.id
        obsolete_product = self._create_product("Obsolete Product")
        obsolete_product.purchase_ok = False
        obsolete_line = self.control_line.create(
            {
                "product_id": obsolete_product.id,
                "company_id": self.company.id,
                "risk_status": "normal",
            }
        )
        eligible_product = self._create_product("Eligible Product")
        self._set_stock(eligible_product, 10.0)

        self.control_line.action_refresh()
        self.assertFalse(obsolete_line.exists())
