from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .account_payment import (
    DISPLAY_PAYMENT_MODE_SELECTION,
    laplatine_allowed_codes_for_journal,
    laplatine_journal_is_cash_like,
)

# Listes statiques : pas de Selection dynamique (bug client web), mais liste correcte selon le journal via deux champs + invisible.
LAPLATINE_INFO_FACTURE_CASH_SELECTION = [("cash", "Espèces")]
LAPLATINE_INFO_FACTURE_OTHER_SELECTION = [
    (k, v) for k, v in DISPLAY_PAYMENT_MODE_SELECTION if k != "cash"
]


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    laplatine_journal_is_cash = fields.Boolean(
        compute="_compute_laplatine_journal_is_cash",
        string="Journal caisse La Platine",
    )

    laplatine_info_facture_cash = fields.Selection(
        LAPLATINE_INFO_FACTURE_CASH_SELECTION,
        string="Info facture",
        help="Affiche sur le PDF client (journal caisse).",
    )
    laplatine_info_facture_other = fields.Selection(
        LAPLATINE_INFO_FACTURE_OTHER_SELECTION,
        string="Info facture",
        help="Affiche sur le PDF client (hors caisse).",
    )

    @api.depends("journal_id")
    def _compute_laplatine_journal_is_cash(self):
        for wiz in self:
            wiz.laplatine_journal_is_cash = laplatine_journal_is_cash_like(wiz.journal_id)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        journal_id = res.get("journal_id") or self.env.context.get("default_journal_id")
        if journal_id:
            journal = self.env["account.journal"].browse(journal_id)
            if laplatine_journal_is_cash_like(journal) and "laplatine_info_facture_cash" in fields_list:
                res.setdefault("laplatine_info_facture_cash", "cash")
        return res

    def _laplatine_mode_code_for_payment(self):
        self.ensure_one()
        if laplatine_journal_is_cash_like(self.journal_id):
            return self.laplatine_info_facture_cash
        return self.laplatine_info_facture_other

    @api.onchange("journal_id")
    def _onchange_journal_id_laplatine_info_facture(self):
        for wiz in self:
            allowed = laplatine_allowed_codes_for_journal(wiz.journal_id)
            code = wiz._laplatine_mode_code_for_payment()
            if code not in allowed:
                wiz.laplatine_info_facture_cash = False
                wiz.laplatine_info_facture_other = False

    def _inject_laplatine_display_payment_mode(self, vals):
        code = self._laplatine_mode_code_for_payment()
        if not code:
            return vals
        if isinstance(vals, dict):
            vals["laplatine_display_payment_mode"] = code
            return vals
        if isinstance(vals, list):
            for item in vals:
                if isinstance(item, dict):
                    item["laplatine_display_payment_mode"] = code
        return vals

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        return self._inject_laplatine_display_payment_mode(vals)

    def _create_payment_vals_from_batch(self, batch_result):
        vals = super()._create_payment_vals_from_batch(batch_result)
        return self._inject_laplatine_display_payment_mode(vals)

    def action_create_payments(self):
        for wiz in self:
            code = wiz._laplatine_mode_code_for_payment()
            if code and code not in laplatine_allowed_codes_for_journal(wiz.journal_id):
                raise UserError(
                    _(
                        "La valeur « Info facture » n'est pas compatible avec le journal sélectionné."
                    )
                )
        return super().action_create_payments()
