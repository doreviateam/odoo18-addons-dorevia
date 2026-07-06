# -*- coding: utf-8 -*-
import base64
from io import BytesIO
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from openpyxl import load_workbook
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..report.billing_report_xlsx import (
    ACHATS_HEADERS,
    FIRST_DATA_ROW,
    HEADER_ROW,
    VENTES_HEADERS,
    document_type_label,
    report_sign,
    signed_move_amounts,
)


@tagged("post_install", "-at_install", "laplatine_billing_report")
class TestLaplatineBillingReportWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env["laplatine.billing.report.wizard"]
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Client Test Billing Report",
                "customer_rank": 1,
            }
        )
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Fournisseur Test Billing Report",
                "supplier_rank": 1,
            }
        )
        cls.sale_journal = cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        cls.purchase_journal = cls.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        cls.income_account = cls.env["account.account"].search(
            [("account_type", "=", "income")],
            limit=1,
        )
        cls.expense_account = cls.env["account.account"].search(
            [("account_type", "=", "expense")],
            limit=1,
        )
        assert cls.sale_journal, "Journal de vente requis."
        assert cls.purchase_journal, "Journal d'achat requis."
        assert cls.income_account, "Compte de produit requis."
        assert cls.expense_account, "Compte de charge requis."

        cls.period_from = fields.Date.from_string("2099-06-01")
        cls.period_to = fields.Date.from_string("2099-06-30")

    def _wizard(self, date_from=None, date_to=None):
        if date_from is None:
            date_from = self.period_from
        if date_to is None:
            date_to = self.period_to
        return self.Wizard.create(
            {
                "date_from": date_from,
                "date_to": date_to,
            }
        )

    def _create_customer_move(
        self,
        move_type="out_invoice",
        amount=100.0,
        invoice_date=None,
        partner=None,
        currency=None,
        company=None,
    ):
        partner = partner or self.partner
        invoice_date = invoice_date or self.period_from
        env = self.env
        if company:
            env = env.with_company(company).sudo()
        account = self.income_account if company is None else company.env["account.account"].search(
            [("account_type", "=", "income")],
            limit=1,
        )
        journal = self.sale_journal if company is None else company.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", company.id)],
            limit=1,
        )
        values = {
            "move_type": move_type,
            "partner_id": partner.id,
            "invoice_date": invoice_date,
            "journal_id": journal.id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Ligne test rapport facturation",
                        "quantity": 1,
                        "price_unit": amount,
                        "account_id": account.id,
                    },
                )
            ],
        }
        if currency:
            values["currency_id"] = currency.id
        move = env["account.move"].create(values)
        move.action_post()
        return move

    def _create_vendor_move(self, amount=80.0, invoice_date=None, vendor_ref=None):
        invoice_date = invoice_date or self.period_from
        values = {
            "move_type": "in_invoice",
            "partner_id": self.vendor.id,
            "invoice_date": invoice_date,
            "journal_id": self.purchase_journal.id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Ligne test achat",
                        "quantity": 1,
                        "price_unit": amount,
                        "account_id": self.expense_account.id,
                    },
                )
            ],
        }
        if vendor_ref:
            values["ref"] = vendor_ref
        move = self.env["account.move"].create(values)
        move.action_post()
        return move

    def _load_ventes_sheet(self, wizard):
        workbook = load_workbook(BytesIO(base64.b64decode(wizard.report_file)))
        return workbook["Ventes"]

    def _load_workbook(self, wizard):
        return load_workbook(BytesIO(base64.b64decode(wizard.report_file)))

    def _load_achats_sheet(self, wizard):
        return self._load_workbook(wizard)["Achats"]

    def _sheet_headers(self, worksheet, headers):
        header_row_excel = HEADER_ROW + 1
        return [
            worksheet.cell(header_row_excel, col).value
            for col in range(1, len(headers) + 1)
        ]

    def _ventes_headers(self, worksheet):
        return self._sheet_headers(worksheet, VENTES_HEADERS)

    def _achats_headers(self, worksheet):
        return self._sheet_headers(worksheet, ACHATS_HEADERS)

    def _data_rows(self, worksheet, header_count):
        first_data_excel = FIRST_DATA_ROW + 1
        rows = []
        row_idx = first_data_excel
        while True:
            first_cell = worksheet.cell(row_idx, 1).value
            if first_cell == "Nombre de documents":
                break
            if first_cell in ("Facture", "Avoir"):
                rows.append(row_idx)
            elif first_cell == "Aucun document trouvé sur la période sélectionnée.":
                break
            else:
                break
            row_idx += 1
        return rows

    def _ventes_data_rows(self, worksheet):
        return self._data_rows(worksheet, len(VENTES_HEADERS))

    def _achats_data_rows(self, worksheet):
        return self._data_rows(worksheet, len(ACHATS_HEADERS))

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

    def test_t03_custom_period_generates_downloadable_xlsx(self):
        """T03 — période modifiable, génération OK."""
        date_from = fields.Date.from_string("2026-01-01")
        date_to = fields.Date.from_string("2026-03-31")
        attachment_count_before = self.env["ir.attachment"].search_count([])
        wizard = self._wizard(date_from=date_from, date_to=date_to)
        action = wizard.action_generate_xlsx()

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn("download=true", action["url"])
        self.assertTrue(wizard.report_file)
        workbook = load_workbook(BytesIO(base64.b64decode(wizard.report_file)))
        self.assertEqual(workbook.sheetnames, ["Ventes", "Achats"])
        self.assertEqual(attachment_count_before, self.env["ir.attachment"].search_count([]))

    def test_t04_posted_customer_invoice_in_ventes_sheet(self):
        """T04 — facture client comptabilisée dans la période."""
        invoice = self._create_customer_move(amount=500.0)
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_ventes_sheet(wizard)
        data_rows = self._ventes_data_rows(worksheet)
        self.assertEqual(len(data_rows), 1)
        row = data_rows[0]
        self.assertEqual(worksheet.cell(row, 1).value, "Facture")
        self.assertEqual(worksheet.cell(row, 2).value, invoice.name)
        self.assertEqual(worksheet.cell(row, 3).value, self.partner.display_name)

    def test_t05_draft_and_cancelled_excluded(self):
        """T05 — brouillon et annulée absents."""
        draft = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": self.period_from,
                "journal_id": self.sale_journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Brouillon",
                            "quantity": 1,
                            "price_unit": 50.0,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        cancelled = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": self.period_from,
                "journal_id": self.sale_journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Annulée",
                            "quantity": 1,
                            "price_unit": 75.0,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        cancelled.action_post()
        cancelled.button_cancel()
        wizard = self._wizard()
        moves = wizard._fetch_sale_moves()
        self.assertNotIn(draft, moves)
        self.assertNotIn(cancelled, moves)

    def test_t08_posted_vendor_invoice_on_achats_sheet(self):
        """T08 — facture fournisseur comptabilisée sur l'onglet Achats."""
        vendor_bill = self._create_vendor_move(amount=80.0, vendor_ref="REF-FOURN-TEST-001")
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_achats_sheet(wizard)
        rows = self._achats_data_rows(worksheet)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(worksheet.cell(row, 1).value, "Facture")
        self.assertEqual(worksheet.cell(row, 2).value, vendor_bill.name)
        self.assertEqual(worksheet.cell(row, 3).value, "REF-FOURN-TEST-001")
        self.assertEqual(worksheet.cell(row, 4).value, self.vendor.display_name)

    def test_t17_two_sheets_always_present(self):
        """T17 — fichier avec exactement 2 onglets Ventes et Achats."""
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        workbook = self._load_workbook(wizard)
        self.assertEqual(workbook.sheetnames, ["Ventes", "Achats"])

    def test_t19_filename_contains_period_dates(self):
        """T19 — nom de fichier avec les deux dates de période."""
        date_from = fields.Date.from_string("2099-03-01")
        date_to = fields.Date.from_string("2099-03-31")
        wizard = self._wizard(date_from=date_from, date_to=date_to)
        wizard.action_generate_xlsx()
        self.assertEqual(
            wizard.report_filename,
            "Rapport_facturation_La_Platine_2099-03-01_2099-03-31.xlsx",
        )

    def test_c01_achats_column_order(self):
        """Slice C — 12 colonnes Achats dans l'ordre MOA."""
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_achats_sheet(wizard)
        self.assertEqual(self._achats_headers(worksheet), ACHATS_HEADERS)

    def test_c02_vendor_refund_negative_amounts_on_achats(self):
        """Slice C — in_refund montants négatifs, Type Avoir."""
        bill = self._create_vendor_move(amount=200.0)
        refund = bill._reverse_moves(
            default_values_list=[{"invoice_date": self.period_from}]
        )
        refund.action_post()
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_achats_sheet(wizard)
        refund_row = None
        for row_idx in self._achats_data_rows(worksheet):
            if worksheet.cell(row_idx, 1).value == "Avoir":
                refund_row = row_idx
        self.assertIsNotNone(refund_row)
        self.assertLess(worksheet.cell(refund_row, 9).value, 0)

    def test_c03_achats_totals_algebraic_sum(self):
        """Slice C — totaux algébriques facture + avoir fournisseur."""
        bill = self._create_vendor_move(amount=500.0)
        refund = bill._reverse_moves(
            default_values_list=[{"invoice_date": self.period_from}]
        )
        refund.action_post()
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_achats_sheet(wizard)

        purchase_moves = wizard._fetch_purchase_moves()
        expected_ttc = sum(
            signed_move_amounts(move)["amount_ttc"] for move in purchase_moves
        )

        totals_row = None
        for row_idx in range(FIRST_DATA_ROW + 1, worksheet.max_row + 1):
            if worksheet.cell(row_idx, 1).value == "Nombre de documents":
                totals_row = row_idx
                break
        self.assertIsNotNone(totals_row)
        self.assertEqual(worksheet.cell(totals_row, 2).value, 2)
        self.assertAlmostEqual(worksheet.cell(totals_row, 9).value, expected_ttc)

    def test_t06_domain_filters_active_company(self):
        """T06 — filtre company_id = env.company.id (inspection domaine)."""
        wizard = self._wizard()
        domain = wizard._move_base_domain()
        self.assertIn(("company_id", "=", self.env.company.id), domain)

    def test_t06_other_company_excluded(self):
        """T06 — autre société absente (domaine company_id = env.company.id)."""
        other_company = self.env["res.company"].search(
            [("id", "!=", self.company.id)], limit=1
        )
        if not other_company:
            self.skipTest("Seconde société requise pour ce test.")
        other_partner = self.env["res.partner"].create(
            {"name": "Client autre société billing", "customer_rank": 1}
        )
        self._create_customer_move(
            amount=120.0,
            partner=other_partner,
            company=other_company,
        )
        own_invoice = self._create_customer_move(amount=90.0)
        wizard = self._wizard()
        moves = wizard._fetch_sale_moves()
        self.assertIn(own_invoice, moves)
        self.assertEqual(len(moves), 1)

    def test_t07_invoice_date_outside_period_excluded(self):
        """T07 — invoice_date hors période absente."""
        self._create_customer_move(
            amount=100.0,
            invoice_date=fields.Date.from_string("2099-05-31"),
        )
        in_period = self._create_customer_move(amount=200.0)
        wizard = self._wizard()
        moves = wizard._fetch_sale_moves()
        self.assertEqual(moves, in_period)

    def test_t09_foreign_currency_blocked(self):
        """T09 — devise étrangère bloque la génération."""
        usd = self.env["res.currency"].search([("name", "=", "USD")], limit=1)
        self.assertTrue(usd)
        self._create_customer_move(amount=100.0)
        self._create_customer_move(amount=50.0, currency=usd)
        wizard = self._wizard()
        with self.assertRaises(UserError):
            wizard.action_generate_xlsx()

    def test_t10_customer_invoice_positive_amounts(self):
        """T10 — out_invoice montants positifs, Type Facture."""
        self._create_customer_move(amount=1000.0)
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_ventes_sheet(wizard)
        row = self._ventes_data_rows(worksheet)[0]
        self.assertEqual(worksheet.cell(row, 1).value, "Facture")
        self.assertGreater(worksheet.cell(row, 8).value, 0)

    def test_t11_customer_refund_negative_amounts(self):
        """T11 — out_refund montants négatifs, Type Avoir."""
        invoice = self._create_customer_move(amount=200.0)
        refund = invoice._reverse_moves(
            default_values_list=[{"invoice_date": self.period_from}]
        )
        refund.action_post()
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_ventes_sheet(wizard)
        refund_row = None
        for row_idx in self._ventes_data_rows(worksheet):
            if worksheet.cell(row_idx, 1).value == "Avoir":
                refund_row = row_idx
                break
        self.assertIsNotNone(refund_row)
        self.assertLess(worksheet.cell(refund_row, 8).value, 0)

    def test_t12_totals_algebraic_sum(self):
        """T12 / T13 — totaux algébriques facture + avoir (Ventes)."""
        invoice = self._create_customer_move(amount=1000.0)
        refund = invoice._reverse_moves(
            default_values_list=[{"invoice_date": self.period_from}]
        )
        refund.action_post()
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_ventes_sheet(wizard)

        sale_moves = wizard._fetch_sale_moves()
        expected_ttc = sum(signed_move_amounts(move)["amount_ttc"] for move in sale_moves)

        totals_row = None
        for row_idx in range(FIRST_DATA_ROW + 1, worksheet.max_row + 1):
            if worksheet.cell(row_idx, 1).value == "Nombre de documents":
                totals_row = row_idx
                break
        self.assertIsNotNone(totals_row)
        self.assertEqual(worksheet.cell(totals_row, 2).value, len(sale_moves))
        self.assertAlmostEqual(worksheet.cell(totals_row, 8).value, expected_ttc)
        self.assertEqual(len(sale_moves), 2)

    def test_t14_payment_state_uses_odoo_label(self):
        """T14 — libellé payment_state traduit Odoo."""
        self._create_customer_move(amount=100.0)
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        labels = wizard._payment_state_labels()
        worksheet = self._load_ventes_sheet(wizard)
        row = self._ventes_data_rows(worksheet)[0]
        move = wizard._fetch_sale_moves().filtered(
            lambda m: m.partner_id == self.partner
        )
        self.assertEqual(len(move), 1)
        expected = labels.get(move.payment_state, move.payment_state)
        self.assertEqual(worksheet.cell(row, 11).value, expected)
        self.assertNotEqual(worksheet.cell(row, 11).value, "not_paid")

    def test_t15_settled_amount_formula(self):
        """T15 — Montant réglé / soldé = sign * abs(total - residual)."""
        move = self._create_customer_move(amount=300.0)
        amounts = signed_move_amounts(move)
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_ventes_sheet(wizard)
        row = next(
            row_idx
            for row_idx in self._ventes_data_rows(worksheet)
            if worksheet.cell(row_idx, 2).value == move.name
        )
        self.assertAlmostEqual(worksheet.cell(row, 9).value, amounts["amount_paid"])

    def test_t16_ventes_column_order(self):
        """T16 — 11 colonnes dans l'ordre MOA."""
        wizard = self._wizard()
        wizard.action_generate_xlsx()
        worksheet = self._load_ventes_sheet(wizard)
        self.assertEqual(self._ventes_headers(worksheet), VENTES_HEADERS)


@tagged("post_install", "-at_install", "laplatine_billing_report")
class TestLaplatineBillingReportHelpers(TransactionCase):
    def test_report_sign_and_type_labels(self):
        self.assertEqual(report_sign("out_invoice"), 1)
        self.assertEqual(report_sign("out_refund"), -1)
        self.assertEqual(document_type_label("out_invoice"), "Facture")
        self.assertEqual(document_type_label("out_refund"), "Avoir")
