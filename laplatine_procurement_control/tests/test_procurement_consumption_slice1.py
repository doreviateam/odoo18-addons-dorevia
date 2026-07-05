# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementConsumptionSlice1(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.stock_ops = cls.env["laplatine.procurement.stock.ops"]
        cls.weight_uom = cls.env.ref("uom.product_uom_kgm")
        cls.weight_category = cls.env.ref("uom.product_uom_categ_kgm")
        cls.unit_uom = cls.env.ref("uom.product_uom_unit")
        cls.consumption_group = cls.env.ref(
            "laplatine_procurement_control.group_raw_material_consumption_user"
        )
        cls.cockpit_user_group = cls.env.ref(
            "laplatine_procurement_control.group_procurement_control_user"
        )

    def _create_product(self, name, tracking=False, storable=True, uom=None):
        uom = uom or self.weight_uom
        product = self.env["product.product"].create(
            {
                "name": name,
                "is_storable": storable,
                "purchase_ok": True,
                "standard_price": 1.0,
                "uom_id": uom.id,
                "uom_po_id": uom.id,
            }
        )
        product.product_tmpl_id.laplatine_consumption_tracking = tracking
        return product

    def test_t01_eligible_products_with_tracking(self):
        tracked = self._create_product("Tracked MP", tracking=True)
        eligible = self.stock_ops.get_eligible_consumption_products(self.company)
        self.assertIn(tracked, eligible)

    def test_t02_excludes_non_storable_products(self):
        service = self._create_product("Service MP", tracking=True, storable=False)
        eligible = self.stock_ops.get_eligible_consumption_products(self.company)
        self.assertNotIn(service, eligible)

    def test_t03_excludes_products_without_tracking(self):
        untracked = self._create_product("Untracked MP", tracking=False)
        eligible = self.stock_ops.get_eligible_consumption_products(self.company)
        self.assertNotIn(untracked, eligible)

    def test_t04_excludes_non_weight_uom(self):
        unit_product = self._create_product(
            "Unit MP", tracking=True, uom=self.unit_uom
        )
        eligible = self.stock_ops.get_eligible_consumption_products(self.company)
        self.assertNotIn(unit_product, eligible)

    def test_t19_consumption_user_can_access_wizard(self):
        user = self.env["res.users"].create(
            {
                "name": "Consumption Operator",
                "login": "consumption_operator_slice1",
                "groups_id": [(6, 0, [self.consumption_group.id])],
            }
        )
        wizard = self.env["laplatine.raw.material.consumption.wizard"].with_user(
            user
        ).create({})
        self.assertTrue(wizard)

    def test_t20_consumption_user_has_no_cockpit_group_by_default(self):
        user = self.env["res.users"].create(
            {
                "name": "Consumption Only",
                "login": "consumption_only_slice1",
                "groups_id": [(6, 0, [self.consumption_group.id])],
            }
        )
        self.assertNotIn(self.cockpit_user_group, user.groups_id)

    def test_t21_cockpit_menu_under_configuration(self):
        menu = self.env.ref(
            "laplatine_procurement_control.menu_procurement_control_root"
        )
        config_menu = self.env.ref("stock.menu_stock_config_settings")
        self.assertEqual(menu.parent_id, config_menu)

    def test_consumption_menu_under_la_platine(self):
        menu = self.env.ref(
            "laplatine_procurement_control.menu_raw_material_consumption"
        )
        root = self.env.ref("laplatine_procurement_control.menu_laplatine_root")
        self.assertEqual(menu.parent_id, root)
        action = menu.action
        self.assertEqual(action.res_model, "laplatine.raw.material.consumption.wizard")

    def test_company_consumption_destination_defaults_to_production(self):
        location = self.company.laplatine_consumption_destination_location_id
        if not location:
            location = self.env["stock.location"].search(
                [("usage", "=", "production")], limit=1
            )
            self.company.laplatine_consumption_destination_location_id = location
        self.assertEqual(location.usage, "production")
        dest = self.stock_ops.get_consumption_destination_location(self.company)
        self.assertEqual(dest.usage, "production")
