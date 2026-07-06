# -*- coding: utf-8 -*-
import base64
from io import BytesIO
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from openpyxl import load_workbook
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "laplatine_billing_report")
class TestLaplatineBillingReportWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env["laplatine.billing.report.wizard"]

    def _wizard(self, date_from=None, date_to=None):
        if date_from is None or date_to is None:
            date_from, date_to = self.Wizard._default_period_bounds()
        return self.Wizard.create(
            {
                "date_from": date_from,
                "date_to": date_to,
            }
        )

    def test_t01_default_period_is_previous_calendar_month(self):
        """T01 — ouverture wizard : mois M-1 complet."""
        today = fields.Date.from_string("2026-07-06")
        with patch.object(
            type(self.Wizard),
            "_default_period_bounds",
            return_value=(
                today.replace(day=1) - relativedelta(months=1),
                today.replace(day=1) - relativedelta(days=1),
            ),
        ):
            defaults = self.Wizard.default_get(["date_from", "date_to"])
        self.assertEqual(defaults["date_from"], fields.Date.from_string("2026-06-01"))
        self.assertEqual(defaults["date_to"], fields.Date.from_string("2026-06-30"))

    def test_t01_default_period_january_uses_december_previous_year(self):
        """Gate slice A — M-1 correct en janvier."""
        today = fields.Date.from_string("2026-01-15")
        with patch.object(
            type(self.Wizard),
            "_default_period_bounds",
            return_value=(
                today.replace(day=1) - relativedelta(months=1),
                today.replace(day=1) - relativedelta(days=1),
            ),
        ):
            defaults = self.Wizard.default_get(["date_from", "date_to"])
        self.assertEqual(defaults["date_from"], fields.Date.from_string("2025-12-01"))
        self.assertEqual(defaults["date_to"], fields.Date.from_string("2025-12-31"))

    def test_t02_invalid_period_raises_user_error(self):
        """T02 — date_from > date_to refusée."""
        with self.assertRaises(UserError):
            self._wizard(
                date_from=fields.Date.from_string("2026-06-30"),
                date_to=fields.Date.from_string("2026-06-01"),
            )
        wizard = self.Wizard.new(
            {
                "date_from": fields.Date.from_string("2026-06-30"),
                "date_to": fields.Date.from_string("2026-06-01"),
            }
        )
        with self.assertRaises(UserError):
            wizard.action_generate_xlsx()

    def test_t03_custom_period_generates_downloadable_stub_xlsx(self):
        """T03 — période modifiable, génération OK."""
        date_from = fields.Date.from_string("2026-01-01")
        date_to = fields.Date.from_string("2026-03-31")
        attachment_count_before = self.env["ir.attachment"].search_count([])
        wizard = self._wizard(date_from=date_from, date_to=date_to)
        action = wizard.action_generate_xlsx()

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn("download=true", action["url"])
        self.assertIn(str(wizard.id), action["url"])
        self.assertTrue(wizard.report_file)
        self.assertEqual(
            wizard.report_filename,
            "Rapport_facturation_La_Platine_2026-01-01_2026-03-31.xlsx",
        )

        workbook = load_workbook(BytesIO(base64.b64decode(wizard.report_file)))
        self.assertEqual(workbook.sheetnames, ["Ventes", "Achats"])

        attachment_count_after = self.env["ir.attachment"].search_count([])
        self.assertEqual(attachment_count_before, attachment_count_after)
