# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementConsumptionSlice2(TransactionCase):
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
        cls.consult_group = cls.env.ref(
            "laplatine_procurement_control.group_procurement_control_user"
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

    def test_t05_auto_select_single_location_with_stock(self):
        product = self._create_tracked_product("Slice2 Single Loc Product")
        location = self._create_internal_location("Slice2 Single Bin")
        self._set_stock(product, location, 13250.0)

        with Form(self.env["laplatine.raw.material.consumption.wizard"]) as wizard:
            wizard.product_id = product
            self.assertEqual(wizard.location_id, location)
            self.assertTrue(wizard.location_is_auto)
            self.assertAlmostEqual(wizard.qty_available_kg, 13250.0)

    def test_t06_multiple_locations_user_choice(self):
        product = self._create_tracked_product("Slice2 Multi Loc Product")
        loc_a = self._create_internal_location("Slice2 Zone A")
        loc_b = self._create_internal_location("Slice2 Zone B")
        self._set_stock(product, loc_a, 100.0)
        self._set_stock(product, loc_b, 250.0)

        with Form(self.env["laplatine.raw.material.consumption.wizard"]) as wizard:
            wizard.product_id = product
            self.assertFalse(wizard.location_is_auto)
            wizard.location_id = loc_b
            self.assertAlmostEqual(wizard.qty_available_kg, 250.0)

    def test_t05_consumption_excludes_zero_stock_locations(self):
        product = self._create_tracked_product("Slice2 Zero Stock Product")
        empty_loc = self._create_internal_location("Slice2 Empty Bin")
        stocked_loc = self._create_internal_location("Slice2 Stocked Bin")
        self._set_stock(product, stocked_loc, 50.0)

        allowed = self.stock_ops.get_allowed_source_locations(
            product, self.company, "consumption"
        )
        self.assertIn(stocked_loc, allowed)
        self.assertNotIn(empty_loc, allowed)

    def test_adjustment_allows_zero_stock_location(self):
        product = self._create_tracked_product("Slice2 Adjustment Product")
        empty_loc = self._create_internal_location("Slice2 Adjustment Empty")

        allowed = self.stock_ops.get_allowed_source_locations(
            product, self.company, "adjustment"
        )
        self.assertIn(empty_loc, allowed)

        with Form(
            self.env["laplatine.raw.material.consumption.wizard"].with_context(
                default_mode="adjustment"
            )
        ) as wizard:
            wizard.product_id = product
            wizard.location_id = empty_loc
            self.assertAlmostEqual(wizard.qty_available_kg, 0.0)

    def test_t13_qty_conversion_to_kg(self):
        product = self._create_tracked_product("Slice2 Gram Product", uom=self.gram_uom)
        location = self._create_internal_location("Slice2 Gram Bin")
        self._set_stock(product, location, 1000.0)

        qty_kg = self.stock_ops.get_qty_kg_at_location(product, location)
        self.assertAlmostEqual(qty_kg, 1.0)

    def test_destination_rejects_other_company_location(self):
        other_company = self.env["res.company"].create({"name": "Other Co Slice2"})
        other_location = self.env["stock.location"].create(
            {
                "name": "Other Co Production",
                "usage": "production",
                "company_id": other_company.id,
            }
        )
        self.company.laplatine_consumption_destination_location_id = other_location
        with self.assertRaises(UserError):
            self.stock_ops.get_consumption_destination_location(self.company)

    def test_cockpit_menu_visible_for_consultation_user(self):
        user = self.env["res.users"].create(
            {
                "name": "Cockpit Consult Slice2",
                "login": "cockpit_consult_slice2",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.consult_group.id,
                        ],
                    )
                ],
            }
        )
        menu_env = self.env["ir.ui.menu"].with_user(user)
        config_menu = self.env.ref("stock.menu_stock_config_settings")
        root_menu = self.env.ref(
            "laplatine_procurement_control.menu_procurement_control_root"
        )
        cockpit_menu = self.env.ref(
            "laplatine_procurement_control.menu_procurement_control_cockpit"
        )
        for menu in (config_menu, root_menu, cockpit_menu):
            visible = menu_env.search([("id", "=", menu.id)])
            self.assertTrue(
                visible,
                f"Menu {menu.display_name!r} invisible pour le profil Consultation",
            )
