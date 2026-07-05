# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class LaplatineRawMaterialConsumptionWizard(models.TransientModel):
    _name = "laplatine.raw.material.consumption.wizard"
    _description = "Consommation matière première La Platine"

    mode = fields.Selection(
        selection=[
            ("consumption", "Enregistrer un prélèvement"),
            ("adjustment", "Correction après comptage"),
        ],
        string="Mode",
        default="consumption",
        required=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Matière première",
        domain=lambda self: self._domain_eligible_products(),
    )
    location_id = fields.Many2one(
        "stock.location",
        string="Localisation",
        domain="[('usage', '=', 'internal')]",
    )
    qty_available_kg = fields.Float(
        string="Quantité disponible (kg)",
        digits="Product Unit of Measure",
        readonly=True,
    )
    qty_consumed_kg = fields.Float(
        string="Quantité prélevée (kg)",
        digits="Product Unit of Measure",
    )
    qty_counted_kg = fields.Float(
        string="Quantité réellement comptée (kg)",
        digits="Product Unit of Measure",
    )
    adjustment_reason = fields.Char(string="Motif")

    @api.model
    def _domain_eligible_products(self):
        products = self.env["laplatine.procurement.stock.ops"].get_eligible_consumption_products(
            self.env.company
        )
        return [("id", "in", products.ids)]

    def action_register_consumption(self):
        self.ensure_one()
        raise UserError(
            "L'enregistrement des consommations sera disponible au Slice 3."
        )

    def action_open_adjustment_mode(self):
        self.ensure_one()
        self.mode = "adjustment"
        return {
            "type": "ir.actions.act_window",
            "name": "Consommation matière première",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_apply_adjustment(self):
        self.ensure_one()
        raise UserError(
            "La correction de stock sera disponible au Slice 4."
        )
