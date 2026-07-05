# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LaplatineRawMaterialConsumptionWizard(models.TransientModel):
    _name = "laplatine.raw.material.consumption.wizard"
    _inherit = "laplatine.raw.material.wizard.mixin"
    _description = "Consommation matière première La Platine"

    product_id = fields.Many2one(
        "product.product",
        string="Matière première",
        domain=lambda self: self._domain_eligible_products(),
    )
    allowed_location_ids = fields.Many2many(
        "stock.location",
        compute="_compute_allowed_location_ids",
        string="Emplacements autorisés",
    )
    location_id = fields.Many2one(
        "stock.location",
        string="Localisation",
        domain="[('id', 'in', allowed_location_ids)]",
    )
    location_is_auto = fields.Boolean(
        string="Emplacement auto-sélectionné",
        compute="_compute_location_is_auto",
    )
    qty_available_kg = fields.Float(
        string="Quantité disponible (kg)",
        digits="Product Unit of Measure",
        compute="_compute_qty_available_kg",
    )
    qty_consumed_kg = fields.Float(
        string="Quantité prélevée (kg)",
        digits="Product Unit of Measure",
    )

    @api.depends("product_id")
    def _compute_allowed_location_ids(self):
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        for wizard in self:
            if not wizard.product_id:
                wizard.allowed_location_ids = False
                continue
            wizard.allowed_location_ids = stock_ops.get_allowed_source_locations(
                wizard.product_id, self.env.company, "consumption"
            )

    @api.depends("allowed_location_ids")
    def _compute_location_is_auto(self):
        for wizard in self:
            wizard.location_is_auto = len(wizard.allowed_location_ids) == 1

    @api.depends("product_id", "location_id")
    def _compute_qty_available_kg(self):
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        for wizard in self:
            if not wizard.product_id or not wizard.location_id:
                wizard.qty_available_kg = 0.0
                continue
            wizard.qty_available_kg = stock_ops.get_qty_kg_at_location(
                wizard.product_id, wizard.location_id
            )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        if not self.product_id:
            self.location_id = False
            return
        allowed = stock_ops.get_allowed_source_locations(
            self.product_id, self.env.company, "consumption"
        )
        if len(allowed) == 1:
            self.location_id = allowed[0]
        elif self.location_id not in allowed:
            self.location_id = False

    def _resolve_location_id(self):
        """Retourne l'emplacement effectif, y compris si auto-sélection UI non persisté."""
        self.ensure_one()
        if self.location_id:
            return self.location_id
        if not self.product_id:
            return self.env["stock.location"]
        allowed = self.env["laplatine.procurement.stock.ops"].get_allowed_source_locations(
            self.product_id, self.env.company, "consumption"
        )
        if len(allowed) == 1:
            return allowed[0]
        return self.env["stock.location"]

    def action_register_consumption(self):
        self.ensure_one()
        location = self._resolve_location_id()
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        result = stock_ops.register_raw_material_consumption(
            self.env.company,
            self.product_id,
            location,
            self.qty_consumed_kg,
        )
        qty_text = self._format_kg_message_qty(result["qty_kg"])
        remaining_text = self._format_kg_message_qty(result["remaining_kg"])
        return self._build_operation_notification(
            "Consommation enregistrée",
            [
                f"{qty_text} kg de {result['product_name']} ont été prélevés.",
                f"Stock restant : {remaining_text} kg.",
            ],
            result["threshold"],
        )
