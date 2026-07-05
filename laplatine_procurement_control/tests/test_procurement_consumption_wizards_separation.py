# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.laplatine_procurement_control.models.procurement_stock_ops import (
    CONSUMPTION_MOVE_REFERENCE,
)


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementConsumptionWizardsSeparation(TransactionCase):
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
        cls.cockpit_group = cls.env.ref(
            "laplatine_procurement_control.group_procurement_control_user"
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Wizards Separation Operator",
                "login": "wizards_separation_operator",
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
        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "Wizards Separation Internal",
                "login": "wizards_separation_internal",
                "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
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

    def test_t23_consumption_menu_opens_consumption_wizard(self):
        menu = self.env.ref(
            "laplatine_procurement_control.menu_raw_material_consumption"
        )
        self.assertEqual(
            menu.action.res_model, "laplatine.raw.material.consumption.wizard"
        )

    def test_t24_stock_update_menu_opens_stock_update_wizard(self):
        menu = self.env.ref(
            "laplatine_procurement_control.menu_raw_material_stock_update"
        )
        self.assertEqual(
            menu.action.res_model, "laplatine.raw.material.stock.update.wizard"
        )

    def test_t25_consumption_wizard_has_no_adjustment_mode(self):
        view = self.env.ref(
            "laplatine_procurement_control.raw_material_consumption_wizard_view_form"
        )
        arch = view.arch
        self.assertNotIn('name="mode"', arch)
        self.assertNotIn("qty_counted_kg", arch)
        self.assertNotIn("adjustment_reason", arch)
        self.assertNotIn("action_open_adjustment_mode", arch)
        self.assertNotIn("Mettre à jour la quantité disponible", arch)

    def test_t26_stock_update_wizard_has_no_consumption_fields(self):
        view = self.env.ref(
            "laplatine_procurement_control.raw_material_stock_update_wizard_view_form"
        )
        arch = view.arch
        self.assertNotIn("qty_consumed_kg", arch)
        self.assertNotIn("action_register_consumption", arch)
        self.assertIn("qty_counted_kg", arch)
        self.assertIn("qty_diff_kg", arch)
        self.assertIn("adjustment_reason", arch)

    def test_t27_operator_can_access_both_wizards(self):
        cons_env = self.env["laplatine.raw.material.consumption.wizard"].with_user(
            self.operator
        )
        stock_env = self.env["laplatine.raw.material.stock.update.wizard"].with_user(
            self.operator
        )
        self.assertTrue(cons_env.create({}))
        self.assertTrue(stock_env.create({}))

    def test_t28_user_without_group_cannot_access_menus(self):
        menu_env = self.env["ir.ui.menu"].with_user(self.internal_user)
        for xml_id in (
            "laplatine_procurement_control.menu_laplatine_root",
            "laplatine_procurement_control.menu_raw_material_consumption",
            "laplatine_procurement_control.menu_raw_material_stock_update",
        ):
            menu = self.env.ref(xml_id)
            visible = menu_env.search([("id", "=", menu.id)])
            self.assertFalse(
                visible,
                f"Menu {menu.display_name!r} visible sans groupe opérateur",
            )

    def test_t29_nominal_consumption_not_regressed(self):
        product = self._create_tracked_product("Separation Consumption Product")
        location = self._create_internal_location("Separation Consumption Bin")
        self._set_stock(product, location, 500.0)

        action = self.env["laplatine.raw.material.consumption.wizard"].create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "qty_consumed_kg": 75.0,
            }
        ).action_register_consumption()

        move = self.env["stock.move"].search(
            [
                ("product_id", "=", product.id),
                ("reference", "=", CONSUMPTION_MOVE_REFERENCE),
            ],
            order="id desc",
            limit=1,
        )
        self.assertEqual(move.state, "done")
        self.assertEqual(action["params"]["title"], "Consommation enregistrée")
        self.assertAlmostEqual(
            self.stock_ops.get_qty_kg_at_location(product, location), 425.0
        )

    def test_t30_consumption_controls_not_regressed(self):
        product = self._create_tracked_product("Separation Consumption Controls")
        location = self._create_internal_location("Separation Controls Bin")
        self._set_stock(product, location, 50.0)
        wizard = self.env["laplatine.raw.material.consumption.wizard"].create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "qty_consumed_kg": 100.0,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_register_consumption()

    def test_t31_nominal_stock_update_not_regressed(self):
        product = self._create_tracked_product("Separation Stock Update Product")
        location = self._create_internal_location("Separation Stock Update Bin")
        self._set_stock(product, location, 200.0)

        action = self.env["laplatine.raw.material.stock.update.wizard"].create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "qty_counted_kg": 175.0,
                "adjustment_reason": "Comptage séparation wizards",
            }
        ).action_update_stock()

        self.assertAlmostEqual(
            self.stock_ops.get_qty_kg_at_location(product, location), 175.0
        )
        self.assertEqual(action["params"]["title"], "Stock mis à jour")
        self.assertIn("Écart enregistré : -25 kg", action["params"]["message"])

    def test_t32_stock_update_rejects_missing_reason_and_negative_qty(self):
        product = self._create_tracked_product("Separation Stock Controls")
        location = self._create_internal_location("Separation Stock Controls Bin")
        self._set_stock(product, location, 100.0)

        wizard_missing_reason = self.env[
            "laplatine.raw.material.stock.update.wizard"
        ].create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "qty_counted_kg": 90.0,
                "adjustment_reason": "  ",
            }
        )
        with self.assertRaises(UserError):
            wizard_missing_reason.action_update_stock()

        wizard_negative = self.env["laplatine.raw.material.stock.update.wizard"].create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "qty_counted_kg": -1.0,
                "adjustment_reason": "Quantité négative test",
            }
        )
        with self.assertRaises(UserError):
            wizard_negative.action_update_stock()

    def test_t33_zero_stock_location_only_in_stock_update_wizard(self):
        product = self._create_tracked_product("Separation Zero Stock Product")
        empty_loc = self._create_internal_location("Separation Empty Bin")
        stocked_loc = self._create_internal_location("Separation Stocked Bin")
        self._set_stock(product, stocked_loc, 40.0)

        cons_allowed = self.stock_ops.get_allowed_source_locations(
            product, self.company, "consumption"
        )
        update_allowed = self.stock_ops.get_allowed_source_locations(
            product, self.company, "adjustment"
        )
        self.assertNotIn(empty_loc, cons_allowed)
        self.assertIn(stocked_loc, cons_allowed)
        self.assertIn(empty_loc, update_allowed)

        with Form(self.env["laplatine.raw.material.stock.update.wizard"]) as wizard:
            wizard.product_id = product
            wizard.location_id = empty_loc
            self.assertAlmostEqual(wizard.qty_available_kg, 0.0)

    def test_t34_cockpit_still_accessible_for_consultation_user(self):
        user = self.env["res.users"].create(
            {
                "name": "Cockpit Consult Separation",
                "login": "cockpit_consult_separation",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.cockpit_group.id,
                        ],
                    )
                ],
            }
        )
        menu_env = self.env["ir.ui.menu"].with_user(user)
        cockpit_menu = self.env.ref(
            "laplatine_procurement_control.menu_procurement_control_cockpit"
        )
        self.assertTrue(menu_env.search([("id", "=", cockpit_menu.id)]))

    def test_operator_cannot_create_wizards_without_acl(self):
        cons_env = self.env["laplatine.raw.material.consumption.wizard"].with_user(
            self.internal_user
        )
        stock_env = self.env["laplatine.raw.material.stock.update.wizard"].with_user(
            self.internal_user
        )
        with self.assertRaises(AccessError):
            cons_env.create({})
        with self.assertRaises(AccessError):
            stock_env.create({})

    def test_consumption_wizard_model_has_no_mode_field(self):
        wizard_model = self.env["laplatine.raw.material.consumption.wizard"]
        self.assertNotIn("mode", wizard_model._fields)
        self.assertNotIn("qty_counted_kg", wizard_model._fields)
        self.assertNotIn("adjustment_reason", wizard_model._fields)

    def test_stock_update_wizard_model_has_no_consumption_field(self):
        wizard_model = self.env["laplatine.raw.material.stock.update.wizard"]
        self.assertNotIn("qty_consumed_kg", wizard_model._fields)
        self.assertNotIn("mode", wizard_model._fields)
