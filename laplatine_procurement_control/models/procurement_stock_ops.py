# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import UserError


class LaplatineProcurementStockOps(models.AbstractModel):
    _name = "laplatine.procurement.stock.ops"
    _description = "Opérations stock partagées La Platine (consommation MP)"

    @api.model
    def get_pilot_warehouse(self, company):
        warehouse = company.laplatine_procurement_warehouse_id
        if not warehouse:
            raise UserError(
                "Aucun entrepôt de pilotage n'est configuré sur la société."
            )
        return warehouse

    @api.model
    def get_consumption_destination_location(self, company):
        location = company.laplatine_consumption_destination_location_id
        if not location:
            raise UserError(
                "Aucun emplacement de destination des consommations n'est "
                "configuré sur la société."
            )
        if location.usage != "production":
            raise UserError(
                "L'emplacement de destination des consommations doit être "
                "un emplacement de production."
            )
        return location

    @api.model
    def get_internal_location_ids(self, warehouse):
        indicators = self.env["laplatine.procurement.indicators"]
        return indicators._get_internal_location_ids(warehouse)

    @api.model
    def resolve_orderpoint(self, product, warehouse):
        indicators = self.env["laplatine.procurement.indicators"]
        return indicators._resolve_orderpoint(product, warehouse)

    @api.model
    def convert_qty(self, product, qty, from_uom):
        indicators = self.env["laplatine.procurement.indicators"]
        return indicators._convert_qty(product, qty, from_uom)

    @api.model
    def _get_weight_uom_category(self):
        category = self.env.ref("uom.product_uom_categ_kgm", raise_if_not_found=False)
        if category:
            return category
        return self.env["uom.category"].search([("name", "ilike", "weight")], limit=1)

    @api.model
    def get_eligible_consumption_products(self, company):
        weight_category = self._get_weight_uom_category()
        if not weight_category:
            return self.env["product.product"]
        return self.env["product.product"].search(
            [
                ("active", "=", True),
                ("is_storable", "=", True),
                ("product_tmpl_id.laplatine_consumption_tracking", "=", True),
                ("uom_id.category_id", "=", weight_category.id),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", company.id),
            ]
        )
