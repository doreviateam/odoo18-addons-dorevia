# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero

CONSUMPTION_MOVE_REFERENCE = "Consommation MP La Platine"
ADJUSTMENT_MOVE_REFERENCE_PREFIX = "Correction MP La Platine"


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

        threshold = self.get_reorder_threshold_status(company, product)
        return {
            "move": move,
            "qty_kg": qty_kg,
            "remaining_kg": self.get_qty_kg_at_location(product, location),
            "product_name": product.display_name,
            "threshold": threshold,
        }

    @api.model
    def get_total_qty_kg_in_pilot_warehouse(self, product, company):
        total = 0.0
        for location in self.get_pilot_internal_locations(company):
            total += self.get_qty_kg_at_location(product, location)
        return total

    @api.model
    def get_reorder_threshold_status(self, company, product):
        warehouse = company.laplatine_procurement_warehouse_id
        if not warehouse:
            return {"below_min": False}

        orderpoint_info = self.resolve_orderpoint(product, warehouse)
        if orderpoint_info["status"] != "ok":
            return {"below_min": False}

        orderpoint = orderpoint_info["orderpoint"]
        min_qty = self.convert_qty(product, orderpoint.product_min_qty, product.uom_id)
        min_qty_kg = self.qty_to_kg(product, min_qty)
        remaining_kg = self.get_total_qty_kg_in_pilot_warehouse(product, company)
        below_min = float_compare(remaining_kg, min_qty_kg, precision_digits=6) <= 0
        return {
            "below_min": below_min,
            "remaining_kg": remaining_kg,
            "min_qty_kg": min_qty_kg,
        }

    @api.model
    def _validate_adjustment_request(
        self, company, product, location, qty_counted_kg, reason
    ):
        if not product:
            raise UserError("Veuillez sélectionner une matière première.")
        if not location:
            raise UserError("Veuillez sélectionner un emplacement.")
        if qty_counted_kg is None:
            raise UserError("Veuillez saisir la quantité réellement comptée.")
        if qty_counted_kg < 0:
            raise UserError("La quantité comptée ne peut pas être négative.")
        if not (reason or "").strip():
            raise UserError("Le motif de correction est obligatoire.")

        eligible = self.get_eligible_consumption_products(company)
        if product not in eligible:
            raise UserError(
                "Cet article n'est plus éligible à la consommation matière première."
            )

        allowed = self.get_allowed_source_locations(product, company, "adjustment")
        if location not in allowed:
            raise UserError(
                "L'emplacement sélectionné n'appartient pas à l'entrepôt de pilotage."
            )

    @api.model
    def _get_quant_for_inventory(self, product, location):
        quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", product.id),
                ("location_id", "=", location.id),
                ("lot_id", "=", False),
                ("package_id", "=", False),
            ],
            limit=1,
        )
        if not quant:
            quant = self.env["stock.quant"].with_context(inventory_mode=True).create(
                {
                    "product_id": product.id,
                    "location_id": location.id,
                }
            )
        return quant

    @api.model
    def _find_last_inventory_move(self, product, location):
        return self.env["stock.move"].search(
            [
                ("product_id", "=", product.id),
                ("is_inventory", "=", True),
                ("state", "=", "done"),
                "|",
                ("location_id", "=", location.id),
                ("location_dest_id", "=", location.id),
            ],
            order="id desc",
            limit=1,
        )

    @api.model
    def register_raw_material_adjustment(
        self, company, product, location, qty_counted_kg, reason
    ):
        self._validate_adjustment_request(
            company, product, location, qty_counted_kg, reason
        )
        reason = (reason or "").strip()
        odoo_qty_kg = self.get_qty_kg_at_location(product, location)
        counted_product_uom = self.qty_from_kg(product, qty_counted_kg)
        odoo_product_uom = self.get_qty_at_location(product, location)

        if float_compare(
            counted_product_uom,
            odoo_product_uom,
            precision_rounding=product.uom_id.rounding,
        ) == 0:
            raise UserError(
                "La quantité comptée correspond déjà au stock enregistré dans Odoo."
            )

        quant = self._get_quant_for_inventory(product, location)
        quant.with_context(inventory_mode=True).write(
            {"inventory_quantity": counted_product_uom}
        )
        quant.with_context(
            inventory_mode=True,
            inventory_name=reason,
            set_inventory_quantity_auto_apply=True,
        ).action_apply_inventory()

        move = self._find_last_inventory_move(product, location)
        if move:
            move.write(
                {
                    "reference": reason,
                    "origin": ADJUSTMENT_MOVE_REFERENCE_PREFIX,
                }
            )

        after_kg = self.get_qty_kg_at_location(product, location)
        threshold = self.get_reorder_threshold_status(company, product)
        return {
            "move": move,
            "before_kg": odoo_qty_kg,
            "after_kg": after_kg,
            "diff_kg": after_kg - odoo_qty_kg,
            "counted_kg": qty_counted_kg,
            "product_name": product.display_name,
            "reason": reason,
            "threshold": threshold,
        }
