# -*- coding: utf-8 -*-
import base64

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..report.billing_report_xlsx import (
    build_report_filename,
    generate_billing_report_xlsx,
)


class LaplatineBillingReportWizard(models.TransientModel):
    _name = "laplatine.billing.report.wizard"
    _description = "Assistant rapport de facturation La Platine"

    date_from = fields.Date(string="Date de début", required=True)
    date_to = fields.Date(string="Date de fin", required=True)
    report_file = fields.Binary(string="Rapport Excel", readonly=True, attachment=False)
    report_filename = fields.Char(string="Nom du fichier", readonly=True)

    @api.model
    def _default_period_bounds(self):
        today = fields.Date.context_today(self)
        date_from = today.replace(day=1) - relativedelta(months=1)
        date_to = today.replace(day=1) - relativedelta(days=1)
        return date_from, date_to

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
                raise UserError(_("La date de début doit être antérieure ou égale à la date de fin."))

    def _move_base_domain(self):
        self.ensure_one()
        return [
            ("company_id", "=", self.env.company.id),
            ("state", "=", "posted"),
            ("invoice_date", "!=", False),
            ("invoice_date", ">=", self.date_from),
            ("invoice_date", "<=", self.date_to),
        ]

    def _fetch_sale_moves(self):
        self.ensure_one()
        domain = self._move_base_domain() + [
            ("move_type", "in", ["out_invoice", "out_refund"]),
        ]
        return self.env["account.move"].search(domain, order="invoice_date, name")

    def _fetch_purchase_moves(self):
        self.ensure_one()
        domain = self._move_base_domain() + [
            ("move_type", "in", ["in_invoice", "in_refund"]),
        ]
        return self.env["account.move"].search(domain, order="invoice_date, name")

    def _payment_state_labels(self):
        selection = self.env["account.move"].fields_get(["payment_state"])["payment_state"][
            "selection"
        ]
        return dict(selection)

    def _check_foreign_currency(self, moves):
        company_currency = self.env.company.currency_id
        foreign = moves.filtered(lambda move: move.currency_id != company_currency)
        if not foreign:
            return
        currency_name = company_currency.name
        raise UserError(
            _(
                "Le rapport contient %(count)s document(s) dans une devise différente "
                "de l'%(currency)s. La génération multidevise n'est pas prise en charge "
                "dans cette version.",
                count=len(foreign),
                currency=currency_name,
            )
        )

    def action_generate_xlsx(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("La date de début doit être antérieure ou égale à la date de fin."))

        sale_moves = self._fetch_sale_moves()
        purchase_moves = self._fetch_purchase_moves()
        all_moves = sale_moves | purchase_moves
        self._check_foreign_currency(all_moves)

        content = generate_billing_report_xlsx(
            company=self.env.company,
            date_from=self.date_from,
            date_to=self.date_to,
            sale_moves=sale_moves,
            purchase_moves=purchase_moves,
            generation_date=fields.Date.context_today(self),
            payment_state_labels=self._payment_state_labels(),
        )
        filename = build_report_filename(self.date_from, self.date_to)
        self.write(
            {
                "report_file": base64.b64encode(content),
                "report_filename": filename,
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": (
                "/web/content/?model=%s&field=report_file&filename_field=report_filename"
                "&download=true&id=%s"
            )
            % (self._name, self.id),
            "target": "self",
        }
