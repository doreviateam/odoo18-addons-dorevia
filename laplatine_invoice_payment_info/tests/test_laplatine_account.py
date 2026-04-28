# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("laplatine_invoice_payment_info", "post_install", "-at_install")
class TestLaplatineAccountPayment(AccountTestInvoicingCommon):
    """account.payment : contraintes « Info facture » / journal."""

    def test_payment_cash_journal_rejects_non_cash_mode(self):
        copy_rec = self.copy_account(self.company_data["default_account_receivable"])
        cash_journal = self.company_data["default_journal_cash"]
        with self.assertRaises(ValidationError):
            self.env["account.payment"].create(
                {
                    "amount": 10.0,
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": self.partner_a.id,
                    "destination_account_id": copy_rec.id,
                    "journal_id": cash_journal.id,
                    "laplatine_display_payment_mode": "card",
                }
            )

    def test_payment_cash_journal_accepts_cash_mode(self):
        copy_rec = self.copy_account(self.company_data["default_account_receivable"])
        cash_journal = self.company_data["default_journal_cash"]
        payment = self.env["account.payment"].create(
            {
                "amount": 10.0,
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner_a.id,
                "destination_account_id": copy_rec.id,
                "journal_id": cash_journal.id,
                "laplatine_display_payment_mode": "cash",
            }
        )
        self.assertEqual(payment.laplatine_display_payment_mode, "cash")

    def test_payment_bank_journal_rejects_cash_mode(self):
        copy_rec = self.copy_account(self.company_data["default_account_receivable"])
        bank_journal = self.company_data["default_journal_bank"]
        with self.assertRaises(ValidationError):
            self.env["account.payment"].create(
                {
                    "amount": 10.0,
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": self.partner_a.id,
                    "destination_account_id": copy_rec.id,
                    "journal_id": bank_journal.id,
                    "laplatine_display_payment_mode": "cash",
                }
            )

    def test_payment_bank_journal_accepts_card_mode(self):
        copy_rec = self.copy_account(self.company_data["default_account_receivable"])
        bank_journal = self.company_data["default_journal_bank"]
        payment = self.env["account.payment"].create(
            {
                "amount": 10.0,
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner_a.id,
                "destination_account_id": copy_rec.id,
                "journal_id": bank_journal.id,
                "laplatine_display_payment_mode": "card",
            }
        )
        self.assertEqual(payment.laplatine_display_payment_mode, "card")


@tagged("laplatine_invoice_payment_info", "post_install", "-at_install")
class TestLaplatinePaymentRegister(AccountTestInvoicingCommon):
    """Wizard : injection vers account.payment."""

    def test_register_injects_cash_mode(self):
        invoice = self.init_invoice("out_invoice", amounts=[100.0], post=True)
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=invoice.ids,
        ).create({"payment_date": invoice.invoice_date})
        wizard.journal_id = self.company_data["default_journal_cash"]
        wizard.laplatine_info_facture_cash = "cash"
        payments = wizard._create_payments()
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments.laplatine_display_payment_mode, "cash")

    def test_register_injects_card_for_bank_journal(self):
        invoice = self.init_invoice("out_invoice", amounts=[50.0], post=True)
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=invoice.ids,
        ).create({"payment_date": invoice.invoice_date})
        wizard.journal_id = self.company_data["default_journal_bank"]
        wizard.laplatine_info_facture_other = "card"
        payments = wizard._create_payments()
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments.laplatine_display_payment_mode, "card")
