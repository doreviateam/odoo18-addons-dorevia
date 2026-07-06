# -*- coding: utf-8 -*-
"""Generate the Slice D visual QA workbook in /tmp from an Odoo shell."""
import base64
import json
import os
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields


OUTPUT_DIR = "/tmp/laplatine_billing_report_slice_d_visual_qa"

module = env["ir.module.module"].search(
    [("name", "=", "laplatine_billing_report")],
    limit=1,
)
Wizard = env["laplatine.billing.report.wizard"]
today = fields.Date.context_today(Wizard)
if os.environ.get("QA_DATE_FROM") and os.environ.get("QA_DATE_TO"):
    date_from = date.fromisoformat(os.environ["QA_DATE_FROM"])
    date_to = date.fromisoformat(os.environ["QA_DATE_TO"])
else:
    date_from = today.replace(day=1) - relativedelta(months=1)
    date_to = today.replace(day=1) - relativedelta(days=1)

wizard = Wizard.create({"date_from": date_from, "date_to": date_to})
wizard.action_generate_xlsx()

os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, wizard.report_filename)
with open(output_path, "wb") as handle:
    handle.write(base64.b64decode(wizard.report_file))

payload = {
    "module": {
        "installed_version": module.installed_version,
        "latest_version": module.latest_version,
        "state": module.state,
    },
    "database": env.cr.dbname,
    "date_from": date_from.isoformat(),
    "date_to": date_to.isoformat(),
    "filename": wizard.report_filename,
    "output_path": output_path,
    "sale_count": len(wizard._fetch_sale_moves()),
    "purchase_count": len(wizard._fetch_purchase_moves()),
    "production": "STOP - lab uniquement",
}
json_path = os.path.join(OUTPUT_DIR, "generation_evidence.json")
with open(json_path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

print("QA_SLICE_D_XLSX=%s" % output_path)
print("QA_SLICE_D_JSON=%s" % json_path)
print(
    "QA_SLICE_D_COUNTS=ventes:%s achats:%s"
    % (payload["sale_count"], payload["purchase_count"])
)
