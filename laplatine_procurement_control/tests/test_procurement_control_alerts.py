# -*- coding: utf-8 -*-
from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.laplatine_procurement_control.models.alert_matrix import (
    ProcurementAlertInput,
    compute_procurement_alerts,
)


@tagged("post_install", "-at_install", "laplatine_procurement_control")
class TestProcurementControlAlerts(TransactionCase):
    def _alerts(self, **kwargs):
        values = {
            "risk_status": "normal",
            "orderpoint_status": "ok",
            "supplier_missing": False,
            "history_insufficient": False,
            "zero_consumption_observed": False,
            "consumption_untraceable": False,
            "confirmed_po_qty": 10.0,
            "reception_date": date(2026, 7, 10),
            "today": date(2026, 7, 5),
            "has_open_reception": True,
        }
        values.update(kwargs)
        return compute_procurement_alerts(ProcurementAlertInput(**values))

    def test_reception_late_alert(self):
        alerts = self._alerts(reception_date=date(2026, 7, 1))
        self.assertIn("reception_late", alerts)

    def test_orderpoint_incomplete_alert(self):
        for status in ("missing", "incomplete", "ambiguous"):
            alerts = self._alerts(orderpoint_status=status)
            self.assertIn("orderpoint_incomplete", alerts)

    def test_supplier_missing_alert(self):
        self.assertIn("supplier_missing", self._alerts(supplier_missing=True))

    def test_history_insufficient_alert(self):
        self.assertIn(
            "history_insufficient", self._alerts(history_insufficient=True)
        )

    def test_no_consumption_alert(self):
        self.assertIn(
            "no_consumption", self._alerts(zero_consumption_observed=True)
        )

    def test_no_confirmed_po_when_need_supply(self):
        alerts = self._alerts(
            risk_status="action_required",
            confirmed_po_qty=0.0,
        )
        self.assertIn("no_confirmed_po", alerts)

    def test_no_confirmed_po_not_raised_when_normal(self):
        alerts = self._alerts(
            risk_status="normal",
            confirmed_po_qty=0.0,
        )
        self.assertNotIn("no_confirmed_po", alerts)

    def test_consumption_untraceable_alert(self):
        self.assertIn(
            "consumption_untraceable",
            self._alerts(consumption_untraceable=True),
        )

    def test_alerts_are_cumulative_and_do_not_change_risk_status(self):
        alerts = self._alerts(
            risk_status="normal",
            supplier_missing=True,
            zero_consumption_observed=True,
            consumption_untraceable=True,
        )
        self.assertEqual(
            set(alerts),
            {"supplier_missing", "no_consumption", "consumption_untraceable"},
        )

    def test_refresh_stores_alerts_without_overwriting_risk_status(self):
        company = self.env.company
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", company.id)], limit=1
        )
        company.write({"laplatine_procurement_warehouse_id": warehouse.id})
        self.env.ref(
            "laplatine_procurement_control.group_procurement_control_manager"
        ).users = [(4, self.env.uid)]
        product = self.env["product.product"].create(
            {
                "name": "Alert Product",
                "is_storable": True,
                "purchase_ok": True,
            }
        )
        product.product_tmpl_id.laplatine_procurement_consumption_untraceable = True

        self.env["laplatine.procurement.control.line"].action_refresh()
        line = self.env["laplatine.procurement.control.line"].search(
            [("product_id", "=", product.id)]
        )
        self.assertTrue(line)
        self.assertTrue(line.risk_status)
        alert_codes = set(line.alert_ids.mapped("code"))
        self.assertIn("consumption_untraceable", alert_codes)
        self.assertIn("orderpoint_incomplete", alert_codes)
