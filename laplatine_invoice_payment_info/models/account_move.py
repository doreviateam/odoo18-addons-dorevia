from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _selection_label_map(self, field):
        """Retourne un mapping value -> libelle pour un champ Selection."""
        selection_pairs = field._description_selection(self.env)
        return dict(selection_pairs or [])

    def _compute_payments_widget_reconciled_info(self):
        super()._compute_payments_widget_reconciled_info()

        all_move_ids = set()
        for move in self:
            widget = move.invoice_payments_widget
            if not isinstance(widget, dict):
                continue
            content = widget.get("content")
            if not isinstance(content, list):
                continue
            for payment_dict in content:
                if not isinstance(payment_dict, dict):
                    continue
                payment_move_id = payment_dict.get("move_id")
                if payment_move_id:
                    all_move_ids.add(payment_move_id)

        if not all_move_ids:
            return

        payments = self.env["account.payment"].search([("move_id", "in", list(all_move_ids))])
        payment_by_move_id = {payment.move_id.id: payment for payment in payments}

        for move in self:
            widget = move.invoice_payments_widget
            if not isinstance(widget, dict):
                continue
            content = widget.get("content")
            if not isinstance(content, list):
                continue
            for payment_dict in content:
                if not isinstance(payment_dict, dict):
                    continue
                payment_move_id = payment_dict.get("move_id")
                if not payment_move_id:
                    continue
                payment = payment_by_move_id.get(payment_move_id)
                if not (payment and payment.laplatine_display_payment_mode):
                    continue

                selection_map = self._selection_label_map(
                    payment._fields["laplatine_display_payment_mode"]
                )
                payment_dict["laplatine_display_payment_mode"] = payment.laplatine_display_payment_mode
                payment_dict["laplatine_display_payment_mode_label"] = selection_map.get(
                    payment.laplatine_display_payment_mode
                )
