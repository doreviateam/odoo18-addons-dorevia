from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProcurementControlSkeleton(TransactionCase):
    def test_company_watch_lead_days_default(self):
        defaults = self.env["res.company"].default_get(
            ["laplatine_procurement_watch_lead_days"]
        )
        self.assertEqual(defaults["laplatine_procurement_watch_lead_days"], 7)

    def test_procurement_control_line_model_accessible(self):
        model = self.env["laplatine.procurement.control.line"]
        self.assertEqual(model._name, "laplatine.procurement.control.line")
