# -*- coding: utf-8 -*-
"""Smoke Slice E for the visual QA run."""
import base64
import json
import os
from datetime import date, datetime

from odoo.exceptions import AccessError


OUTPUT_DIR = "/tmp/laplatine_billing_report_slice_d_visual_qa"
os.makedirs(OUTPUT_DIR, exist_ok=True)

base_group = env.ref("base.group_user")
invoice_group = env.ref("account.group_account_invoice")
menu = env.ref("laplatine_billing_report.menu_laplatine_billing_report")
Wizard = env["laplatine.billing.report.wizard"]


def ensure_user(login, name, groups):
    user = env["res.users"].search([("login", "=", login)], limit=1)
    values = {
        "name": name,
        "login": login,
        "groups_id": [(6, 0, [group.id for group in groups])],
    }
    if user:
        user.write(values)
    else:
        user = env["res.users"].create(values)
    user.write({"password": "FactReportQA!2026"})
    return user


invoice_user = ensure_user(
    "qa_fact_report_invoice_20260706",
    "QA Fact Report Facturation",
    [base_group, invoice_group],
)
denied_user = ensure_user(
    "qa_fact_report_denied_20260706",
    "QA Fact Report Sans Facturation",
    [base_group],
)

invoice_menu_visible = bool(
    env["ir.ui.menu"].with_user(invoice_user).search([("id", "=", menu.id)])
)
denied_menu_visible = bool(
    env["ir.ui.menu"].with_user(denied_user).search([("id", "=", menu.id)])
)

period_from = date(2099, 12, 1)
period_to = date(2099, 12, 31)
wizard = Wizard.with_user(invoice_user).create(
    {"date_from": period_from, "date_to": period_to}
)
action = wizard.action_generate_xlsx()
empty_xlsx_path = os.path.join(OUTPUT_DIR, wizard.report_filename)
with open(empty_xlsx_path, "wb") as handle:
    handle.write(base64.b64decode(wizard.report_file))

denied_create_blocked = False
try:
    Wizard.with_user(denied_user).create(
        {"date_from": period_from, "date_to": period_to}
    )
except AccessError:
    denied_create_blocked = True

payload = {
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "production": "STOP - lab uniquement",
    "invoice_user": invoice_user.login,
    "denied_user": denied_user.login,
    "invoice_menu_visible": invoice_menu_visible,
    "denied_menu_visible": denied_menu_visible,
    "invoice_export_ok": action["type"] == "ir.actions.act_url"
    and bool(wizard.report_file),
    "empty_period": {
        "date_from": period_from.isoformat(),
        "date_to": period_to.isoformat(),
        "filename": wizard.report_filename,
        "xlsx_path": empty_xlsx_path,
    },
    "denied_create_blocked": denied_create_blocked,
}
json_path = os.path.join(OUTPUT_DIR, "smoke_slice_e_evidence.json")
with open(json_path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

env.cr.commit()
print("QA_SLICE_E_JSON=%s" % json_path)
print("QA_SLICE_E_EMPTY_XLSX=%s" % empty_xlsx_path)
