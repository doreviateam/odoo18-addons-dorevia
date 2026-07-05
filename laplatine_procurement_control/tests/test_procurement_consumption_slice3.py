# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.laplatine_procurement_control.models.procurement_stock_ops import (
    CONSUMPTION_MOVE_REFERENCE,
)


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementConsumptionSlice3(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.stock_ops = cls.env["laplatine.procurement.stock.ops"]
        cls.weight_uom = cls.env.ref("uom.product_uom_kgm")
        cls.gram_uom = cls.env.ref("uom.product_uom_gram")
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
                "name": "Consumption Operator Slice3",
                "login": "consumption_operator_slice3",
                "groups_id": [(6, 0, [cls.consumption_group.id])],
            }
        )

    def _create_tracked_product(self, name, uom=None):
        uom = uom or self.weight_uom
        product = self.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "purchase_ok": True,
                "standard_price": 1.0,
                "uom_id": uom.id,
                "uom_po_id": uom.id,
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

    def _create_wizard(self, product, location, qty_kg, user=None):
        env = self.env["laplatine.raw.material.consumption.wizard"]
        if user:
            env = env.with_user(user)
        return env.create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "qty_consumed_kg": qty_kg,
            }
        )

    def test_t07_nominal_consumption_creates_done_move(self):
        product = self._create_tracked_product("Slice3 Nominal Product")
        location = self._create_internal_location("Slice3 Nominal Bin")
        self._set_stock(product, location, 13250.0)

        wizard = self._create_wizard(product, location, 75.0, user=self.operator)
        action = wizard.action_register_consumption()

        move = self.env["stock.move"].search(
            [
                ("product_id", "=", product.id),
                ("location_id", "=", location.id),
                ("reference", "=", CONSUMPTION_MOVE_REFERENCE),
            ],
            order="id desc",
            limit=1,
        )
        self.assertEqual(move.state, "done")
        self.assertEqual(move.location_dest_id, self.production_location)
        self.assertAlmostEqual(move.product_uom_qty, 75.0)
        self.assertEqual(move.create_uid, self.operator)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["title"], "Consommation enregistrée")
        self.assertIn("75 kg", action["params"]["message"])
        self.assertIn("13 175 kg", action["params"]["message"])

    def test_t08_consumption_decreases_stock(self):
        product = self._create_tracked_product("Slice3 Stock Decrease")
        location = self._create_internal_location("Slice3 Stock Bin")
        self._set_stock(product, location, 500.0)

        self._create_wizard(product, location, 120.0).action_register_consumption()

        remaining = self.stock_ops.get_qty_at_location(product, location)
        self.assertAlmostEqual(remaining, 380.0)

    def test_t09_move_uses_company_production_destination(self):
        product = self._create_tracked_product("Slice3 Destination Product")
        location = self._create_internal_location("Slice3 Destination Bin")
        self._set_stock(product, location, 200.0)
        custom_production = self.env["stock.location"].create(
            {
                "name": "Slice3 Custom Production",
                "usage": "production",
                "company_id": self.company.id,
            }
        )
        self.company.laplatine_consumption_destination_location_id = custom_production

        self._create_wizard(product, location, 10.0).action_register_consumption()

        move = self.env["stock.move"].search(
            [("product_id", "=", product.id)], order="id desc", limit=1
        )
        self.assertEqual(move.location_dest_id, custom_production)

    def test_t10_rejects_zero_quantity(self):
        product = self._create_tracked_product("Slice3 Zero Qty Product")
        location = self._create_internal_location("Slice3 Zero Qty Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_wizard(product, location, 0.0)

        with self.assertRaises(UserError):
            wizard.action_register_consumption()

    def test_t11_rejects_negative_quantity(self):
        product = self._create_tracked_product("Slice3 Negative Qty Product")
        location = self._create_internal_location("Slice3 Negative Qty Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_wizard(product, location, -5.0)

        with self.assertRaises(UserError):
            wizard.action_register_consumption()

    def test_t12_rejects_quantity_above_available(self):
        product = self._create_tracked_product("Slice3 Over Qty Product")
        location = self._create_internal_location("Slice3 Over Qty Bin")
        self._set_stock(product, location, 50.0)
        wizard = self._create_wizard(product, location, 50.01)

        with self.assertRaises(UserError):
            wizard.action_register_consumption()

    def test_t13_converts_kilograms_to_stock_uom(self):
        product = self._create_tracked_product("Slice3 Gram Product", uom=self.gram_uom)
        location = self._create_internal_location("Slice3 Gram Bin")
        self._set_stock(product, location, 2000.0)

        self._create_wizard(product, location, 0.75).action_register_consumption()

        move = self.env["stock.move"].search(
            [("product_id", "=", product.id)], order="id desc", limit=1
        )
        self.assertAlmostEqual(move.product_uom_qty, 750.0)
        self.assertEqual(move.product_uom, self.gram_uom)

    def test_consumption_rereads_stock_at_validation(self):
        product = self._create_tracked_product("Slice3 Reread Stock Product")
        location = self._create_internal_location("Slice3 Reread Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_wizard(product, location, 60.0)
        self._set_stock(product, location, 40.0)

        with self.assertRaises(UserError):
            wizard.action_register_consumption()

    def test_consumption_rejects_missing_product(self):
        product = self._create_tracked_product("Slice3 Missing Product")
        location = self._create_internal_location("Slice3 Missing Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_wizard(product, location, 10.0)
        wizard.product_id = False

        with self.assertRaises(UserError):
            wizard.action_register_consumption()

    def test_consumption_rejects_missing_location(self):
        product = self._create_tracked_product("Slice3 Missing Location Product")
        location = self._create_internal_location("Slice3 Missing Location Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_wizard(product, location, 10.0)
        wizard.location_id = False

        with self.assertRaises(UserError):
            wizard.action_register_consumption()

    def test_consumption_rejects_ineligible_product_at_validation(self):
        product = self._create_tracked_product("Slice3 Ineligible Product")
        location = self._create_internal_location("Slice3 Ineligible Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_wizard(product, location, 10.0)
        product.product_tmpl_id.laplatine_consumption_tracking = False

        with self.assertRaises(UserError):
            wizard.action_register_consumption()

    def test_destination_rejects_other_company_location_on_consumption(self):
        other_company = self.env["res.company"].create({"name": "Other Co Slice3"})
        other_location = self.env["stock.location"].create(
            {
                "name": "Other Co Production Slice3",
                "usage": "production",
                "company_id": other_company.id,
            }
        )
        self.company.laplatine_consumption_destination_location_id = other_location
        product = self._create_tracked_product("Slice3 Other Co Product")
        location = self._create_internal_location("Slice3 Other Co Bin")
        self._set_stock(product, location, 100.0)
        wizard = self._create_wizard(product, location, 10.0)

        with self.assertRaises(UserError):
            wizard.action_register_consumption()
