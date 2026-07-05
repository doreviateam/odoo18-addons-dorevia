# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.laplatine_procurement_control.models.procurement_stock_ops import (
    ADJUSTMENT_MOVE_REFERENCE_PREFIX,
)


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementConsumptionSlice4(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.stock_ops = cls.env["laplatine.procurement.stock.ops"]
        cls.weight_uom = cls.env.ref("uom.product_uom_kgm")
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.company.write({"laplatine_procurement_warehouse_id": cls.warehouse.id})
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
        cls.consumption_group = cls.env.ref(
            "laplatine_procurement_control.group_raw_material_consumption_user"
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Consumption Operator Slice4",
                "login": "consumption_operator_slice4",
                "groups_id": [(6, 0, [cls.consumption_group.id])],
            }
        )

    def _create_tracked_product(self, name):
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
        product.product_tmpl_id.laplatine_consumption_tracking = True
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

    def _create_orderpoint(self, product, min_qty, max_qty=None):
        return self.env["stock.warehouse.orderpoint"].create(
            {
                "product_id": product.id,
                "warehouse_id": self.warehouse.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "product_min_qty": min_qty,
                "product_max_qty": max_qty or min_qty * 2,
            }
        )

    def _create_adjustment_wizard(self, product, location, counted_kg, reason, user=None):
        env = self.env["laplatine.raw.material.consumption.wizard"]
        if user:
            env = env.with_user(user)
        return env.create(
            {
                "mode": "adjustment",
                "product_id": product.id,
                "location_id": location.id,
                "qty_counted_kg": counted_kg,
                "adjustment_reason": reason,
            }
        )

    def test_t14_positive_inventory_adjustment(self):
        product = self._create_tracked_product("Slice4 Positive Product")
        location = self._create_internal_location("Slice4 Positive Bin")
        self._set_stock(product, location, 100.0)

        self._create_adjustment_wizard(
            product, location, 120.0, "Correction positive Slice4"
        ).action_apply_adjustment()

        self.assertAlmostEqual(
            self.stock_ops.get_qty_kg_at_location(product, location), 120.0
        )

    def test_t15_negative_inventory_adjustment(self):
        product = self._create_tracked_product("Slice4 Negative Product")
        location = self._create_internal_location("Slice4 Negative Bin")
        self._set_stock(product, location, 13175.0)

        action = self._create_adjustment_wizard(
            product,
            location,
            13150.0,
            "Ancienne consommation non enregistrée",
        ).action_apply_adjustment()

        self.assertAlmostEqual(
            self.stock_ops.get_qty_kg_at_location(product, location), 13150.0
        )
        self.assertIn("Stock après : 13 150 kg", action["params"]["message"])
        self.assertIn("Écart : -25 kg", action["params"]["message"])

    def test_t16_adjustment_to_zero(self):
        product = self._create_tracked_product("Slice4 Zero Product")
        location = self._create_internal_location("Slice4 Zero Bin")
        self._set_stock(product, location, 50.0)

        self._create_adjustment_wizard(
            product, location, 0.0, "Inventaire vide Slice4"
        ).action_apply_adjustment()

        self.assertAlmostEqual(
            self.stock_ops.get_qty_kg_at_location(product, location), 0.0
        )

    def test_t17_rejects_missing_reason(self):
        product = self._create_tracked_product("Slice4 Reason Product")
        location = self._create_internal_location("Slice4 Reason Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_adjustment_wizard(product, location, 90.0, "   ")

        with self.assertRaises(UserError):
            wizard.action_apply_adjustment()

    def test_t18_reorder_threshold_after_adjustment(self):
        product = self._create_tracked_product("Slice4 Threshold Product")
        location = self._create_internal_location("Slice4 Threshold Bin")
        self._set_stock(product, location, 5010.0)
        self._create_orderpoint(product, min_qty=5000.0)

        action = self._create_adjustment_wizard(
            product, location, 4950.0, "Ajustement sous seuil Slice4"
        ).action_apply_adjustment()

        self.assertEqual(action["params"]["type"], "warning")
        self.assertIn("Seuil de réapprovisionnement atteint", action["params"]["message"])
        self.assertIn("4 950 kg", action["params"]["message"])
        self.assertIn("5 000 kg", action["params"]["message"])

    def test_adjustment_confirmation_on_button(self):
        view = self.env.ref(
            "laplatine_procurement_control.raw_material_consumption_wizard_view_form"
        )
        self.assertIn(
            "confirm=",
            view.arch,
        )
        self.assertIn("Confirmer l'application de la correction", view.arch)

    def test_adjustment_reason_and_author_on_inventory_move(self):
        product = self._create_tracked_product("Slice4 Traceability Product")
        location = self._create_internal_location("Slice4 Traceability Bin")
        self._set_stock(product, location, 200.0)
        reason = "Motif traçabilité Slice4"

        self._create_adjustment_wizard(
            product, location, 180.0, reason, user=self.operator
        ).action_apply_adjustment()

        move = self.env["stock.move"].search(
            [
                ("product_id", "=", product.id),
                ("is_inventory", "=", True),
            ],
            order="id desc",
            limit=1,
        )
        self.assertTrue(move)
        self.assertEqual(move.name, reason)
        self.assertEqual(move.reference, reason)
        self.assertEqual(move.origin, ADJUSTMENT_MOVE_REFERENCE_PREFIX)
        self.assertEqual(move.create_uid, self.operator)

    def test_adjustment_rereads_odoo_qty_at_validation(self):
        product = self._create_tracked_product("Slice4 Reread Product")
        location = self._create_internal_location("Slice4 Reread Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_adjustment_wizard(product, location, 90.0, "Reread Slice4")
        self._set_stock(product, location, 90.0)

        with self.assertRaises(UserError):
            wizard.action_apply_adjustment()

    def test_consumption_threshold_warning_after_slice3_operation(self):
        product = self._create_tracked_product("Slice4 Consumption Threshold")
        location = self._create_internal_location("Slice4 Consumption Threshold Bin")
        self._set_stock(product, location, 5050.0)
        self._create_orderpoint(product, min_qty=5000.0)

        action = self.env["laplatine.raw.material.consumption.wizard"].create(
            {
                "mode": "consumption",
                "product_id": product.id,
                "location_id": location.id,
                "qty_consumed_kg": 100.0,
            }
        ).action_register_consumption()

        self.assertEqual(action["params"]["type"], "warning")
        self.assertIn("Seuil de réapprovisionnement atteint", action["params"]["message"])

    def test_slice3_consumption_still_works_after_slice4(self):
        product = self._create_tracked_product("Slice4 Regression Consumption")
        location = self._create_internal_location("Slice4 Regression Bin")
        self._set_stock(product, location, 300.0)

        action = self.env["laplatine.raw.material.consumption.wizard"].create(
            {
                "mode": "consumption",
                "product_id": product.id,
                "location_id": location.id,
                "qty_consumed_kg": 25.0,
            }
        ).action_register_consumption()

        self.assertEqual(action["params"]["title"], "Consommation enregistrée")
        self.assertAlmostEqual(
            self.stock_ops.get_qty_kg_at_location(product, location), 275.0
        )
