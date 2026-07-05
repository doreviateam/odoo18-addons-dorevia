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

    @api.depends("product_id", "mode")
    def _compute_allowed_location_ids(self):
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        for wizard in self:
            if not wizard.product_id:
                wizard.allowed_location_ids = False
                continue
            wizard.allowed_location_ids = stock_ops.get_allowed_source_locations(
                wizard.product_id, self.env.company, wizard.mode
            )

    @api.depends("mode", "allowed_location_ids")
    def _compute_location_is_auto(self):
        for wizard in self:
            wizard.location_is_auto = (
                wizard.mode == "consumption" and len(wizard.allowed_location_ids) == 1
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

    @api.onchange("product_id", "mode")
    def _onchange_product_mode(self):
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        if not self.product_id:
            self.location_id = False
            return
        allowed = stock_ops.get_allowed_source_locations(
            self.product_id, self.env.company, self.mode
        )
        if self.mode == "consumption":
            if len(allowed) == 1:
                self.location_id = allowed[0]
            elif self.location_id not in allowed:
                self.location_id = False
            return
        if self.location_id not in allowed:
            self.location_id = False

    def action_register_consumption(self):
        self.ensure_one()
        raise UserError(
            "L'enregistrement des consommations sera disponible au Slice 3."
        )

    def action_open_adjustment_mode(self):
        self.ensure_one()
        self.mode = "adjustment"
        self._onchange_product_mode()
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
