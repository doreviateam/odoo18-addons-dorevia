# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


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

    def _format_kg_message_qty(self, qty_kg):
        if float_is_zero(qty_kg % 1.0, precision_digits=3):
            return f"{int(round(qty_kg)):,}".replace(",", " ")
        return f"{qty_kg:.2f}".replace(".", ",")

    def _format_signed_kg_message_qty(self, qty_kg):
        prefix = "+" if qty_kg > 0 else ""
        return f"{prefix}{self._format_kg_message_qty(qty_kg)}"

    def _build_operation_notification(self, title, message_lines, threshold):
        message = "\n".join(message_lines)
        notification_type = "success"
        if threshold.get("below_min"):
            message += (
                "\n\nSeuil de réapprovisionnement atteint\n"
                f"Stock restant : {self._format_kg_message_qty(threshold['remaining_kg'])} kg\n"
                f"Seuil minimum : {self._format_kg_message_qty(threshold['min_qty_kg'])} kg"
            )
            notification_type = "warning"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": notification_type,
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_register_consumption(self):
        self.ensure_one()
        if self.mode != "consumption":
            raise UserError(
                "L'enregistrement des consommations n'est disponible "
                "qu'en mode prélèvement."
            )
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        result = stock_ops.register_raw_material_consumption(
            self.env.company,
            self.product_id,
            self.location_id,
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
        if self.mode != "adjustment":
            raise UserError(
                "La correction de stock n'est disponible qu'en mode comptage."
            )
        stock_ops = self.env["laplatine.procurement.stock.ops"]
        result = stock_ops.register_raw_material_adjustment(
            self.env.company,
            self.product_id,
            self.location_id,
            self.qty_counted_kg,
            self.adjustment_reason,
        )
        return self._build_operation_notification(
            "Correction appliquée",
            [
                f"Stock avant : {self._format_kg_message_qty(result['before_kg'])} kg",
                f"Stock compté : {self._format_kg_message_qty(result['counted_kg'])} kg",
                f"Écart : {self._format_signed_kg_message_qty(result['diff_kg'])} kg",
                f"Stock après : {self._format_kg_message_qty(result['after_kg'])} kg",
            ],
            result["threshold"],
        )
