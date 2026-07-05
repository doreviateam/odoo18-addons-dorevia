# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.tools.float_utils import float_is_zero


class LaplatineRawMaterialWizardMixin(models.AbstractModel):
    _name = "laplatine.raw.material.wizard.mixin"
    _description = "Helpers partagés wizards consommation / mise à jour stock MP"

    @api.model
    def _domain_eligible_products(self):
        products = self.env["laplatine.procurement.stock.ops"].get_eligible_consumption_products(
            self.env.company
        )
        return [("id", "in", products.ids)]

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
