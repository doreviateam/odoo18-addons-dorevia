# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged

from odoo.addons.laplatine_invoice_payment_info.models.account_payment import (
    laplatine_allowed_codes_for_journal,
    laplatine_journal_is_cash_like,
)


@tagged("laplatine_invoice_payment_info", "at_install", "-post_install")
class TestLaplatineHelpers(TransactionCase):
    """Logique pure journal / codes autorisés (sans chart template lourd)."""

    def test_journal_cash_type_is_cash_like(self):
        j = self.env["account.journal"].new({"type": "cash", "name": "Caisse", "code": "CSH"})
        self.assertTrue(laplatine_journal_is_cash_like(j))

    def test_journal_bank_named_especes_is_cash_like(self):
        j = self.env["account.journal"].new({"type": "bank", "name": "Espèces", "code": "BNK"})
        self.assertTrue(laplatine_journal_is_cash_like(j))

    def test_journal_bank_named_virement_not_cash_like(self):
        j = self.env["account.journal"].new({"type": "bank", "name": "Virement", "code": "VIR"})
        self.assertFalse(laplatine_journal_is_cash_like(j))

    def test_empty_journal_not_cash_like(self):
        self.assertFalse(laplatine_journal_is_cash_like(self.env["account.journal"]))

    def test_allowed_codes_cash_journal_only_cash(self):
        j = self.env["account.journal"].new({"type": "cash", "name": "C", "code": "C"})
        self.assertEqual(laplatine_allowed_codes_for_journal(j), {"cash"})

    def test_allowed_codes_bank_journal_excludes_cash(self):
        j = self.env["account.journal"].new({"type": "bank", "name": "Banque", "code": "BNK"})
        allowed = laplatine_allowed_codes_for_journal(j)
        self.assertNotIn("cash", allowed)
        self.assertIn("card", allowed)
        self.assertIn("transfer", allowed)
