# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero

CONSUMPTION_MOVE_REFERENCE = "Consommation MP La Platine"


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
        if location.company_id and location.company_id != company:
            raise UserError(
                "L'emplacement de destination des consommations doit "
                "appartenir à la société courante ou être partagé."
            )
        return location

    @api.model
    def get_kg_uom(self):
        return self.env.ref("uom.product_uom_kgm")

    @api.model
    def qty_to_kg(self, product, qty, from_uom=None):
        kg_uom = self.get_kg_uom()
        source_uom = from_uom or product.uom_id
        return source_uom._compute_quantity(qty, kg_uom)

    @api.model
    def qty_from_kg(self, product, qty_kg):
        kg_uom = self.get_kg_uom()
        return kg_uom._compute_quantity(qty_kg, product.uom_id)

    @api.model
    def get_pilot_internal_locations(self, company):
        warehouse = self.get_pilot_warehouse(company)
        location_ids = self.get_internal_location_ids(warehouse)
        return self.env["stock.location"].browse(location_ids).exists()

    @api.model
    def get_qty_at_location(self, product, location):
        quants = self.env["stock.quant"].search(
            [
                ("product_id", "=", product.id),
                ("location_id", "=", location.id),
            ]
        )
        return sum(quants.mapped("quantity"))

    @api.model
    def get_qty_kg_at_location(self, product, location):
        return self.qty_to_kg(product, self.get_qty_at_location(product, location))

    @api.model
    def get_locations_with_positive_stock(self, product, company):
        locations = []
        for location in self.get_pilot_internal_locations(company):
            if self.get_qty_at_location(product, location) > 0:
                locations.append(location)
        return self.env["stock.location"].concat(*locations) if locations else self.env["stock.location"]

    @api.model
    def get_allowed_source_locations(self, product, company, mode):
        if mode == "consumption":
            return self.get_locations_with_positive_stock(product, company)
        return self.get_pilot_internal_locations(company)

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

    @api.model
    def _validate_consumption_request(self, company, product, location, qty_kg):
        if not product:
            raise UserError("Veuillez sélectionner une matière première.")
        if not location:
            raise UserError("Veuillez sélectionner un emplacement.")
        if qty_kg is None or float_is_zero(qty_kg, precision_digits=6):
            raise UserError("La quantité prélevée doit être strictement positive.")
        if qty_kg < 0:
            raise UserError("La quantité prélevée ne peut pas être négative.")

        eligible = self.get_eligible_consumption_products(company)
        if product not in eligible:
            raise UserError(
                "Cet article n'est plus éligible à la consommation matière première."
            )

        allowed = self.get_allowed_source_locations(product, company, "consumption")
        if location not in allowed:
            raise UserError(
                "L'emplacement sélectionné n'est pas autorisé pour cette consommation."
            )

        available_kg = self.get_qty_kg_at_location(product, location)
        if float_compare(qty_kg, available_kg, precision_digits=6) > 0:
            raise UserError(
                "La quantité prélevée (%.2f kg) dépasse le stock disponible (%.2f kg)."
                % (qty_kg, available_kg)
            )

        return self.get_consumption_destination_location(company)

    @api.model
    def register_raw_material_consumption(self, company, product, location, qty_kg):
        destination = self._validate_consumption_request(
            company, product, location, qty_kg
        )
        qty_product_uom = self.qty_from_kg(product, qty_kg)
        move = self.env["stock.move"].create(
            {
                "name": CONSUMPTION_MOVE_REFERENCE,
                "reference": CONSUMPTION_MOVE_REFERENCE,
                "product_id": product.id,
                "product_uom_qty": qty_product_uom,
                "product_uom": product.uom_id.id,
                "location_id": location.id,
                "location_dest_id": destination.id,
                "company_id": company.id,
            }
        )
        move._action_confirm()
        move._action_assign()
        move.quantity = qty_product_uom
        move.picked = True
        move._action_done()

        return {
            "move": move,
            "qty_kg": qty_kg,
            "remaining_kg": self.get_qty_kg_at_location(product, location),
            "product_name": product.display_name,
        }
