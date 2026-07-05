# -*- coding: utf-8 -*-
from datetime import timedelta

from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementControlCockpit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.other_warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id), ("id", "!=", cls.warehouse.id)],
            limit=1,
        )
        cls.vendor = cls.env["res.partner"].create({"name": "Vendor Cockpit Test"})
        cls.indicators = cls.env["laplatine.procurement.indicators"]
        cls.control_line = cls.env["laplatine.procurement.control.line"]
        cls.company.write(
            {
                "laplatine_procurement_warehouse_id": cls.warehouse.id,
                "laplatine_procurement_consumption_days": 10,
                "laplatine_procurement_min_history_days": 3,
                "laplatine_procurement_stale_warning_hours": 12,
            }
        )
        cls.manager_user = cls.env.ref(
            "laplatine_procurement_control.group_procurement_control_manager"
        ).users[:1]
        if not cls.manager_user:
            cls.manager_user = cls.env["res.users"].create(
                {
                    "name": "Procurement Manager Test",
                    "login": "procurement_manager_test",
                    "groups_id": [
                        (
                            6,
                            0,
                            [
                                cls.env.ref("base.group_user").id,
                                cls.env.ref(
                                    "laplatine_procurement_control.group_procurement_control_manager"
                                ).id,
                                cls.env.ref("stock.group_stock_user").id,
                                cls.env.ref("purchase.group_purchase_user").id,
                            ],
                        )
                    ],
                }
            )
        cls.consult_user = cls.env["res.users"].create(
            {
                "name": "Procurement Consult Test",
                "login": "procurement_consult_test",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref(
                                "laplatine_procurement_control.group_procurement_control_user"
                            ).id,
                            cls.env.ref("stock.group_stock_user").id,
                        ],
                    )
                ],
            }
        )

    def _create_product(self, name):
        return self.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "purchase_ok": True,
                "standard_price": 1.0,
            }
        )

    def _set_stock(self, product, quantity, warehouse=None):
        warehouse = warehouse or self.warehouse
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": product.id,
                "location_id": warehouse.lot_stock_id.id,
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

    def _create_confirmed_po(self, product, qty, uom=None):
        uom = uom or product.uom_po_id
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": qty,
                            "product_uom": uom.id,
                            "price_unit": 1.0,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        po.button_confirm()
        return po

    def test_double_refresh_does_not_duplicate_lines(self):
        product = self._create_product("Duplicate Refresh Product")
        self._set_stock(product, 10.0)
        self.control_line.with_user(self.manager_user).action_refresh()
        self.control_line.with_user(self.manager_user).action_refresh()
        lines = self.control_line.search([("product_id", "=", product.id)])
        self.assertEqual(len(lines), 1)

    def test_refresh_removes_out_of_scope_line(self):
        product = self._create_product("Out Of Scope Product")
        line = self.control_line.create(
            {
                "product_id": product.id,
                "company_id": self.company.id,
                "risk_status": "normal",
            }
        )
        product.purchase_ok = False
        self.control_line.with_user(self.manager_user).action_refresh()
        self.assertFalse(line.exists())

    def test_refresh_respects_configured_warehouse(self):
        product = self._create_product("Warehouse Scope Product")
        self._set_stock(product, 100.0, warehouse=self.warehouse)
        if self.other_warehouse:
            self._set_stock(product, 500.0, warehouse=self.other_warehouse)
        self.control_line.with_user(self.manager_user).action_refresh()
        line = self.control_line.search([("product_id", "=", product.id)], limit=1)
        self.assertEqual(line.warehouse_id, self.warehouse)
        self.assertEqual(line.qty_available, 100.0)

    def test_uom_conversion_for_po_remaining_qty(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        unit = self.env.ref("uom.product_uom_unit")
        product = self._create_product("UOM Product")
        product.write({"uom_po_id": dozen.id, "uom_id": unit.id})
        self._create_confirmed_po(product, 2.0, uom=dozen)
        po_line = self.env["purchase.order.line"].search(
            [("product_id", "=", product.id)], limit=1
        )
        po_line.write({"qty_received": 1.0})
        remaining = self.indicators._get_line_remaining_qty(product, po_line)
        self.assertEqual(remaining, 12.0)

    def test_ambiguous_orderpoints_raise_alert_not_arbitrary_selection(self):
        product = self._create_product("Ambiguous OP Product")
        with patch.object(
            type(self.indicators),
            "_resolve_orderpoint",
            return_value={"orderpoint": False, "status": "ambiguous"},
        ):
            evaluation = self.indicators.evaluate_product(product, self.company)
        self.assertIn("orderpoint_incomplete", evaluation["alert_codes"])

    def test_draft_and_sent_po_excluded_from_confirmed_qty(self):
        product = self._create_product("PO State Product")
        self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": 50.0,
                            "product_uom": product.uom_po_id.id,
                            "price_unit": 1.0,
                        },
                    )
                ],
            }
        )
        sent_po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": 30.0,
                            "product_uom": product.uom_po_id.id,
                            "price_unit": 1.0,
                        },
                    )
                ],
            }
        )
        sent_po.write({"state": "sent"})
        confirmed_po = self._create_confirmed_po(product, 10.0)
        self.assertEqual(confirmed_po.state, "purchase")
        qty = self.indicators._get_confirmed_po_qty(product, self.company)
        self.assertEqual(qty, 10.0)

    def test_partial_reception_counts_remaining_only(self):
        product = self._create_product("Partial PO Product")
        po = self._create_confirmed_po(product, 100.0)
        line = po.order_line[0]
        line.write({"qty_received": 40.0})
        qty = self.indicators._get_confirmed_po_qty(product, self.company)
        self.assertEqual(qty, 60.0)

    def test_consult_user_cannot_refresh(self):
        with self.assertRaises(AccessError):
            self.control_line.with_user(self.consult_user).action_refresh()

    def test_manager_user_can_refresh(self):
        product = self._create_product("Manager Refresh Product")
        self._set_stock(product, 5.0)
        self.control_line.with_user(self.manager_user).action_refresh()
        self.assertTrue(
            self.control_line.search([("product_id", "=", product.id)], limit=1)
        )

    def test_stale_warning_uses_company_hours(self):
        product = self._create_product("Stale Product")
        line = self.control_line.create(
            {
                "product_id": product.id,
                "company_id": self.company.id,
                "risk_status": "normal",
                "last_refresh": fields.Datetime.now() - timedelta(hours=13),
            }
        )
        self.assertTrue(line.is_data_stale)
        self.assertIn("12 h", line.stale_warning_message)

    def test_company_separation_on_refresh(self):
        other_company = self.env["res.company"].create({"name": "Other Co Test"})
        other_wh = self.env["stock.warehouse"].search(
            [("company_id", "=", other_company.id)], limit=1
        )
        if not other_wh:
            return
        other_company.laplatine_procurement_warehouse_id = other_wh.id
        product = self._create_product("Company Split Product")
        self._set_stock(product, 15.0)
        self.control_line.with_user(self.manager_user).action_refresh()
        line_main = self.control_line.search(
            [("product_id", "=", product.id), ("company_id", "=", self.company.id)]
        )
        line_other = self.control_line.search(
            [("product_id", "=", product.id), ("company_id", "=", other_company.id)]
        )
        self.assertEqual(len(line_main), 1)
        self.assertFalse(line_other)
