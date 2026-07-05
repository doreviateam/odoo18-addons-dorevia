# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LaplatineRawMaterialStockUpdateWizard(models.TransientModel):
    _name = "laplatine.raw.material.stock.update.wizard"
    _inherit = "laplatine.raw.material.wizard.mixin"
    _description = "Mise à jour des quantités en stock La Platine"

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
    qty_available_kg = fields.Float(
        string="Quantité enregistrée dans Odoo",
        digits="Product Unit of Measure",
        compute="_compute_qty_available_kg",
    )
    qty_counted_kg = fields.Float(
        string="Quantité réellement comptée",
        digits="Product Unit of Measure",
    )
    qty_diff_kg = fields.Float(
        string="Écart calculé",
        digits="Product Unit of Measure",
        compute="_compute_qty_diff_kg",
    )
    adjustment_reason = fields.Char(string="Motif")

    @api.depends("product_id")
    def _compute_allowed_location_ids(self):
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        for wizard in self:
            if not wizard.product_id:
                wizard.allowed_location_ids = False
                continue
            wizard.allowed_location_ids = stock_ops.get_allowed_source_locations(
                wizard.product_id, self.env.company, "adjustment"
            )

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

    @api.depends("qty_available_kg", "qty_counted_kg")
    def _compute_qty_diff_kg(self):
        for wizard in self:
            wizard.qty_diff_kg = wizard.qty_counted_kg - wizard.qty_available_kg

    @api.onchange("product_id")
    def _onchange_product_id(self):
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        if not self.product_id:
            self.location_id = False
            return
        allowed = stock_ops.get_allowed_source_locations(
            self.product_id, self.env.company, "adjustment"
        )
        if self.location_id not in allowed:
            self.location_id = False

    def action_update_stock(self):
        self.ensure_one()
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        result = stock_ops.register_raw_material_adjustment(
            self.env.company,
            self.product_id,
            self.location_id,
            self.qty_counted_kg,
            self.adjustment_reason,
        )
        return self._build_operation_notification(
            "Stock mis à jour",
            [
                result["product_name"],
                f"Quantité avant : {self._format_kg_message_qty(result['before_kg'])} kg",
                (
                    "Quantité après comptage : "
                    f"{self._format_kg_message_qty(result['counted_kg'])} kg"
                ),
                (
                    "Écart enregistré : "
                    f"{self._format_signed_kg_message_qty(result['diff_kg'])} kg."
                ),
            ],
            result["threshold"],
        )
