# -*- coding: utf-8 -*-
from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.laplatine_procurement_control.models.risk_matrix import (
    ProcurementRiskInput,
    compute_procurement_risk,
)


TODAY = date(2026, 7, 5)


def _baseline(**overrides):
    values = {
        "today": TODAY,
        "watch_lead_days": 7,
        "qty_available": 100.0,
        "daily_consumption": 10.0,
        "history_insufficient": False,
        "warehouse_configured": True,
        "essential_data_missing": False,
        "min_qty_exploitable": True,
        "min_qty": 50.0,
        "stock_break_date": date(2026, 7, 20),
        "order_deadline_date": date(2026, 7, 25),
        "next_reception_date": date(2026, 7, 22),
        "projected_qty_at_reception": 80.0,
    }
    values.update(overrides)
    return ProcurementRiskInput(**values)


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementControlMatrix(TransactionCase):
    def _evaluate(self, **overrides):
        return compute_procurement_risk(_baseline(**overrides))

    def test_priority_1_warehouse_not_configured(self):
        result = self._evaluate(warehouse_configured=False)
        self.assertEqual(result["risk_status"], "insufficient_data")
        self.assertIn("Priorité 1", result["risk_reason"])
        self.assertIn("entrepôt", result["risk_reason"])

    def test_priority_1_history_insufficient(self):
        result = self._evaluate(history_insufficient=True)
        self.assertEqual(result["risk_status"], "insufficient_data")
        self.assertIn("historique insuffisant", result["risk_reason"])

    def test_priority_1_wins_over_stockout(self):
        result = self._evaluate(
            qty_available=0.0,
            history_insufficient=True,
        )
        self.assertEqual(result["risk_status"], "insufficient_data")
        self.assertIn("Priorité 1", result["risk_reason"])

    def test_priority_2_stockout(self):
        result = self._evaluate(qty_available=0.0)
        self.assertEqual(result["risk_status"], "stockout")
        self.assertIn("Priorité 2", result["risk_reason"])

    def test_priority_3_critical_before_reception(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 10),
            next_reception_date=date(2026, 7, 15),
        )
        self.assertEqual(result["risk_status"], "critical")
        self.assertIn("Priorité 3", result["risk_reason"])

    def test_priority_3_wins_over_deadline_reached(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 10),
            next_reception_date=date(2026, 7, 15),
            order_deadline_date=date(2026, 7, 4),
        )
        self.assertEqual(result["risk_status"], "critical")
        self.assertIn("Priorité 3", result["risk_reason"])

    def test_priority_4_below_min_before_reception(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 30),
            projected_qty_at_reception=40.0,
            min_qty=50.0,
        )
        self.assertEqual(result["risk_status"], "action_required")
        self.assertIn("Priorité 4", result["risk_reason"])

    def test_priority_4_wins_over_watch_window(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 30),
            projected_qty_at_reception=40.0,
            order_deadline_date=date(2026, 7, 8),
            watch_lead_days=7,
        )
        self.assertEqual(result["risk_status"], "action_required")
        self.assertIn("Priorité 4", result["risk_reason"])

    def test_priority_5_deadline_reached(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 30),
            projected_qty_at_reception=80.0,
            order_deadline_date=date(2026, 7, 5),
        )
        self.assertEqual(result["risk_status"], "action_required")
        self.assertIn("Priorité 5", result["risk_reason"])

    def test_priority_6_watch_window(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 30),
            projected_qty_at_reception=80.0,
            order_deadline_date=date(2026, 7, 10),
            watch_lead_days=7,
        )
        self.assertEqual(result["risk_status"], "watch")
        self.assertIn("Priorité 6", result["risk_reason"])
        self.assertIn("7 j", result["risk_reason"])

    def test_watch_lead_days_read_from_input_not_hardcoded(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 30),
            projected_qty_at_reception=80.0,
            order_deadline_date=date(2026, 7, 12),
            watch_lead_days=10,
        )
        self.assertEqual(result["risk_status"], "watch")
        self.assertIn("marge 10 j", result["risk_reason"])

        outside_window = self._evaluate(
            stock_break_date=date(2026, 7, 30),
            projected_qty_at_reception=80.0,
            order_deadline_date=date(2026, 7, 20),
            watch_lead_days=10,
        )
        self.assertEqual(outside_window["risk_status"], "normal")

    def test_priority_7_normal(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 30),
            projected_qty_at_reception=80.0,
            order_deadline_date=date(2026, 8, 1),
        )
        self.assertEqual(result["risk_status"], "normal")
        self.assertIn("Priorité 7", result["risk_reason"])

    def test_min_not_exploitable_forbids_normal(self):
        result = self._evaluate(
            min_qty_exploitable=False,
            order_deadline_date=None,
            stock_break_date=None,
            next_reception_date=None,
            projected_qty_at_reception=None,
            daily_consumption=0.0,
        )
        self.assertNotEqual(result["risk_status"], "normal")
        self.assertEqual(result["risk_status"], "insufficient_data")
        self.assertIn("min/max incomplet", result["risk_reason"])

    def test_zero_consumption_skips_date_priorities(self):
        result = self._evaluate(
            daily_consumption=0.0,
            stock_break_date=date(2026, 7, 10),
            order_deadline_date=date(2026, 7, 4),
            next_reception_date=date(2026, 7, 15),
            projected_qty_at_reception=10.0,
        )
        self.assertEqual(result["risk_status"], "normal")

    def test_zero_consumption_does_not_use_break_date_in_critical_path(self):
        result = compute_procurement_risk(
            ProcurementRiskInput(
                today=TODAY,
                watch_lead_days=7,
                qty_available=100.0,
                daily_consumption=0.0,
                min_qty_exploitable=True,
                min_qty=50.0,
                stock_break_date=date(2026, 7, 6),
                order_deadline_date=date(2026, 7, 6),
                next_reception_date=date(2026, 7, 20),
                projected_qty_at_reception=10.0,
            )
        )
        self.assertNotEqual(result["risk_status"], "critical")
        self.assertNotEqual(result["risk_status"], "action_required")
        self.assertEqual(result["risk_status"], "normal")

    def test_risk_reason_matches_triggered_rule(self):
        result = self._evaluate(
            stock_break_date=date(2026, 7, 30),
            projected_qty_at_reception=80.0,
            order_deadline_date=date(2026, 7, 5),
        )
        self.assertEqual(result["risk_status"], "action_required")
        self.assertIn("date limite", result["risk_reason"].lower())
        self.assertTrue(result["action_recommended"])
