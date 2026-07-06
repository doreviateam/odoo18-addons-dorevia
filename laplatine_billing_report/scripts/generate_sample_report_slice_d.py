# -*- coding: utf-8 -*-
"""Génère un rapport de facturation lab pour la recette impression slice D.

Usage (odoo shell, base laplatine_prod) :

    exec(open("/mnt/extra-addons/odoo18-addons-dorevia/laplatine_billing_report/scripts/generate_sample_report_slice_d.py").read())
"""
import base64
import os
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields

OUTPUT_DIR = (
    "/mnt/extra-addons/odoo18-addons-dorevia/laplatine_billing_report/recette_qa/SLICE-D-IMPRESSION"
)

Wizard = env["laplatine.billing.report.wizard"]
today = fields.Date.context_today(Wizard)
date_from = today.replace(day=1) - relativedelta(months=1)
date_to = today.replace(day=1) - relativedelta(days=1)

wizard = Wizard.create({"date_from": date_from, "date_to": date_to})
wizard.action_generate_xlsx()

os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, wizard.report_filename)
with open(output_path, "wb") as handle:
    handle.write(base64.b64decode(wizard.report_file))

sale_count = len(wizard._fetch_sale_moves())
purchase_count = len(wizard._fetch_purchase_moves())
print(f"Fichier généré : {output_path}")
print(f"Période : {date_from} → {date_to}")
print(f"Documents Ventes : {sale_count} | Achats : {purchase_count}")
