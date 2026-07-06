#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test post-déploiement production — laplatine_billing_report.

Usage (sur le serveur production, après upgrade + restart) :

  docker compose run --rm odoo odoo shell \\
    --config=/etc/odoo/odoo.conf \\
    --database=laplatine_prod \\
    --no-http <<'PY'
exec(open("/chemin/vers/odoo18-addons-dorevia/laplatine_billing_report/scripts/prod_post_deploy_smoke.py").read())
PY

Ne pas exécuter avant le créneau MOA validé.
"""
from __future__ import annotations

import base64
import json
from datetime import date, datetime, timedelta

from odoo.exceptions import AccessError

MODULE = "laplatine_billing_report"
EXPECTED_VERSION = "18.0.1.0.0"

results = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "database": env.cr.dbname,
    "module": MODULE,
    "checks": {},
}


def record(name, ok, detail=""):
    results["checks"][name] = {"ok": bool(ok), "detail": detail}
    status = "OK" if ok else "KO"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))


# 1. Module installé
mod = env["ir.module.module"].search([("name", "=", MODULE)], limit=1)
record(
    "module_installed",
    mod and mod.state == "installed",
    f"state={mod.state if mod else 'absent'}, version={mod.latest_version if mod else '-'}",
)
record(
    "module_version",
    bool(mod and mod.latest_version == EXPECTED_VERSION),
    f"attendu {EXPECTED_VERSION}",
)

# 2. Menu parent position (Fournisseurs < La Platine < Comptabilité)
parent = env.ref("account.menu_finance")
vendors = env.ref("account.menu_finance_payables")
accounting = env.ref("account.menu_finance_entries")
laplatine = env.ref("laplatine_billing_report.menu_laplatine_finance")
siblings = env["ir.ui.menu"].search([("parent_id", "=", parent.id)], order="sequence, id")
ids = siblings.ids
menu_order_ok = (
    ids.index(vendors.id) < ids.index(laplatine.id) < ids.index(accounting.id)
)
record("menu_order", menu_order_ok, "Fournisseurs → La Platine → Comptabilité")

# 3. Droits groupe Facturation (modèle wizard chargé)
Wizard = env["laplatine.billing.report.wizard"]
record(
    "wizard_model_loaded",
    Wizard._name in env.registry,
    Wizard._name,
)

# 4. Génération export M-1 (période courte — mois calendaire précédent simulé)
first_this_month = date.today().replace(day=1)
period_to = first_this_month - timedelta(days=1)
period_from = period_to.replace(day=1)
wizard = Wizard.create({"date_from": period_from, "date_to": period_to})
action = wizard.action_generate_xlsx()
xlsx_ok = (
    action.get("type") == "ir.actions.act_url"
    and wizard.report_file
    and wizard.report_filename.endswith(".xlsx")
)
record("generate_xlsx", xlsx_ok, wizard.report_filename or "sans fichier")
if wizard.report_file:
    record("xlsx_size", len(base64.b64decode(wizard.report_file)) > 1000, "taille > 1 Ko")

# 5. Refus utilisateur sans groupe Facturation
denied = env["res.users"].search(
    [("login", "=", "smoke_fact_report_denied_prod")], limit=1
)
if not denied:
    denied = env["res.users"].create(
        {
            "name": "Smoke Fact Report Denied Prod",
            "login": "smoke_fact_report_denied_prod",
            "groups_id": [(6, 0, [env.ref("base.group_user").id])],
        }
    )
denied_blocked = False
try:
    Wizard.with_user(denied).create(
        {"date_from": period_from, "date_to": period_to}
    )
except AccessError:
    denied_blocked = True
record("access_denied_without_invoice_group", denied_blocked)

results["verdict"] = (
    "GO_SMOKE_PROD"
    if all(item["ok"] for item in results["checks"].values())
    else "NO_GO_SMOKE_PROD"
)
print("VERDICT:", results["verdict"])
print(json.dumps(results, indent=2, ensure_ascii=False))
