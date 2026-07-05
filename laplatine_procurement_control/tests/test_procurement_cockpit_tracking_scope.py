# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementCockpitTrackingScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.company.laplatine_procurement_warehouse_id = cls.warehouse.id
        cls.production_location = cls.env["stock.location"].search(
            [
                ("usage", "=", "production"),
                "|",
                ("company_id", "=", cls.company.id),
                ("company_id", "=", False),
            ],
            limit=1,
        )
        cls.company.laplatine_consumption_destination_location_id = (
            cls.production_location
        )
        cls.vendor = cls.env["res.partner"].create({"name": "Vendor Tracking Scope"})
        cls.indicators = cls.env["laplatine.procurement.indicators"]
        cls.stock_ops = cls.env["laplatine.procurement.stock.ops"]
        cls.control_line = cls.env["laplatine.procurement.control.line"]
        cls.weight_uom = cls.env.ref("uom.product_uom_kgm")
        cls.manager_group = cls.env.ref(
            "laplatine_procurement_control.group_procurement_control_manager"
        )
        cls.consumption_group = cls.env.ref(
            "laplatine_procurement_control.group_raw_material_consumption_user"
        )
        cls.cockpit_group = cls.env.ref(
            "laplatine_procurement_control.group_procurement_control_user"
        )
        cls.manager_group.users = [(4, cls.env.uid)]
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Cockpit Scope Operator",
                "login": "cockpit_scope_operator",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.consumption_group.id,
                        ],
                    )
                ],
            }
        )

    def _create_product(self, name, tracking=False):
        product = self.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "purchase_ok": True,
                "standard_price": 1.0,
                "uom_id": self.weight_uom.id,
                "uom_po_id": self.weight_uom.id,
            }
        )
        product.product_tmpl_id.laplatine_consumption_tracking = tracking
        return product

    def _create_internal_location(self, name, parent=None):
        parent = parent or self.warehouse.lot_stock_id
        return self.env["stock.location"].create(
            {
                "name": name,
                "location_id": parent.id,
                "usage": "internal",
            }
        )

    def _set_stock(self, product, location, quantity):
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": product.id,
                "location_id": location.id,
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

    def _refresh(self):
        self.control_line.with_user(self.env.user).action_refresh()

    def _line_for(self, product):
        return self.control_line.search(
            [("product_id", "=", product.id), ("company_id", "=", self.company.id)]
        )

    def test_t35_tracked_product_present_in_cockpit(self):
        product = self._create_product("Article A Tracked", tracking=True)
        self._set_stock(product, self.warehouse.lot_stock_id, 100.0)
        self._create_orderpoint(product)
        self._create_supplierinfo(product)

        self._refresh()
        line = self._line_for(product)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.qty_available, 100.0)
        self.assertEqual(line.min_qty, 50.0)

    def test_t36_untracked_product_absent_from_cockpit(self):
        product = self._create_product("Article B Untracked", tracking=False)
        self._set_stock(product, self.warehouse.lot_stock_id, 100.0)
        self._create_orderpoint(product)
        self._create_supplierinfo(product)

        self._refresh()
        self.assertFalse(self._line_for(product))

    def test_t37_untracked_with_orderpoint_absent_from_cockpit(self):
        product = self._create_product("Untracked With OP", tracking=False)
        self._set_stock(product, self.warehouse.lot_stock_id, 50.0)
        self._create_orderpoint(product)

        self._refresh()
        self.assertFalse(self._line_for(product))

    def test_t38_untracked_with_supplier_absent_from_cockpit(self):
        product = self._create_product("Untracked With Supplier", tracking=False)
        self._set_stock(product, self.warehouse.lot_stock_id, 50.0)
        self._create_supplierinfo(product)

        self._refresh()
        self.assertFalse(self._line_for(product))

    def test_t39_untracking_then_refresh_removes_line(self):
        product = self._create_product("Toggle Off Product", tracking=True)
        self._set_stock(product, self.warehouse.lot_stock_id, 10.0)
        self._refresh()
        self.assertTrue(self._line_for(product))

        product.product_tmpl_id.laplatine_consumption_tracking = False
        self._refresh()
        self.assertFalse(self._line_for(product))

    def test_t40_tracking_then_refresh_creates_line(self):
        product = self._create_product("Toggle On Product", tracking=False)
        self._set_stock(product, self.warehouse.lot_stock_id, 10.0)
        self._refresh()
        self.assertFalse(self._line_for(product))

        product.product_tmpl_id.laplatine_consumption_tracking = True
        self._refresh()
        self.assertTrue(self._line_for(product))

    def test_t41_tracked_without_orderpoint_visible_with_alert(self):
        product = self._create_product("Article C Incomplete", tracking=True)
        self._set_stock(product, self.warehouse.lot_stock_id, 25.0)

        self._refresh()
        line = self._line_for(product)
        self.assertEqual(len(line), 1)
        alert_codes = set(line.alert_ids.mapped("code"))
        self.assertIn("orderpoint_incomplete", alert_codes)

    def test_t42_same_tracking_boolean_for_cockpit_and_wizards(self):
        tracked = self._create_product("Shared Tracked", tracking=True)
        untracked = self._create_product("Shared Untracked", tracking=False)

        cockpit_ids = set(
            self.indicators.get_eligible_products(self.company).ids
        )
        wizard_ids = set(
            self.stock_ops.get_eligible_consumption_products(self.company).ids
        )

        self.assertIn(tracked.id, cockpit_ids)
        self.assertIn(tracked.id, wizard_ids)
        self.assertNotIn(untracked.id, cockpit_ids)
        self.assertNotIn(untracked.id, wizard_ids)

    def test_t43_consumption_non_regression_after_cockpit_scope(self):
        product = self._create_product("Consumption Scope Product", tracking=True)
        location = self._create_internal_location("Consumption Scope Bin")
        self._set_stock(product, location, 100.0)
        wizard = (
            self.env["laplatine.raw.material.consumption.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "product_id": product.id,
                    "location_id": location.id,
                    "qty_consumed_kg": 5.0,
                }
            )
        )
        wizard.action_register_consumption()
        self.assertTrue(
            self.env["stock.move"].search(
                [("product_id", "=", product.id), ("state", "=", "done")], limit=1
            )
        )

    def test_t44_stock_update_non_regression_after_cockpit_scope(self):
        product = self._create_product("Stock Update Scope Product", tracking=True)
        location = self._create_internal_location("Stock Update Scope Bin")
        self._set_stock(product, location, 50.0)
        wizard = (
            self.env["laplatine.raw.material.stock.update.wizard"]
            .with_user(self.operator)
            .create(
                {
                    "product_id": product.id,
                    "location_id": location.id,
                    "qty_counted_kg": 60.0,
                    "adjustment_reason": "Comptage scope cockpit",
                }
            )
        )
        wizard.action_update_stock()
        self.assertAlmostEqual(
            self.stock_ops.get_qty_kg_at_location(product, location), 60.0
        )

    def test_t45_operator_cannot_refresh_cockpit(self):
        with self.assertRaises(AccessError):
            self.control_line.with_user(self.operator).action_refresh()

    def test_t46_eligible_products_filter_requires_tracking(self):
        tracked = self._create_product("Filter Tracked", tracking=True)
        untracked = self._create_product("Filter Untracked", tracking=False)
        eligible = self.indicators.get_eligible_products(self.company)
        self.assertIn(tracked, eligible)
        self.assertNotIn(untracked, eligible)
