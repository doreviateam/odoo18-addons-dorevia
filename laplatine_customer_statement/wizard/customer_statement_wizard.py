# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..report.customer_statement_xlsx import LaplatineCustomerStatementXlsx


class LaplatineCustomerStatementWizard(models.TransientModel):
    _name = "laplatine.customer.statement.wizard"
    _description = "Assistant état de facturation client La Platine"

    partner_id = fields.Many2one(
        "res.partner",
        string="Partenaire",
        required=True,
        domain=[("customer_rank", ">", 0)],
    )
    date_from = fields.Date(string="Date de début", required=True)
    date_to = fields.Date(string="Date de fin", required=True)

    @api.model
    def _default_period_bounds(self):
        today = fields.Date.context_today(self)
        date_from = today - relativedelta(days=89)
        return date_from, today

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        date_from, date_to = self._default_period_bounds()
        if "date_from" in fields_list and "date_from" not in res:
            res["date_from"] = date_from
        if "date_to" in fields_list and "date_to" not in res:
            res["date_to"] = date_to
        return res

    @api.constrains("date_from", "date_to")
    def _check_period(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_from > wizard.date_to:
                raise UserError(_("La date de début doit être antérieure à la date de fin."))

    def _invoice_domain(self):
        self.ensure_one()
        commercial_partner = self.partner_id.commercial_partner_id
        return [
            ("commercial_partner_id", "=", commercial_partner.id),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("payment_state", "!=", "reversed"),
            ("invoice_date", ">=", self.date_from),
            ("invoice_date", "<=", self.date_to),
        ]

    def _fetch_invoices(self):
        self.ensure_one()
        return self.env["account.move"].search(
            self._invoice_domain(),
            order="invoice_date, name",
        )

    def _check_single_currency(self, invoices):
        currencies = invoices.mapped("currency_id")
        if len(currencies) > 1:
            currency_names = ", ".join(currencies.mapped("display_name"))
            raise UserError(
                _(
                    "Les factures sélectionnées utilisent plusieurs devises (%(currencies)s). "
                    "Veuillez restreindre la période ou le partenaire pour n'inclure "
                    "qu'une seule devise par génération.",
                    currencies=currency_names,
                )
            )

    def action_generate_xlsx(self):
        self.ensure_one()
        invoices = self._fetch_invoices()
        if not invoices:
            raise UserError(
                _(
                    "Aucune facture comptabilisée n'a été trouvée pour ce partenaire "
                    "sur la période sélectionnée."
                )
            )

        self._check_single_currency(invoices)

        generator = LaplatineCustomerStatementXlsx(
            partner=self.partner_id.commercial_partner_id,
            date_from=self.date_from,
            date_to=self.date_to,
            invoices=invoices,
            generation_date=fields.Date.context_today(self),
        )
        content, filename = generator.generate()

        attachment = self.env["ir.attachment"].create(
            {
                "name": filename,
                "type": "binary",
                "raw": content,
                "mimetype": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                "res_model": self._name,
                "res_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }
