# -*- coding: utf-8 -*-
"""Passe MOA UI — lecture seule fécule, sans appliquer de correction."""
import json
import os
from datetime import datetime

RUN_ID = "QA-CONS-MP-MOA-UI-20260705_200300"
RUN_DIR = os.environ.get("QA_OUT_DIR", "/tmp/" + RUN_ID)
os.makedirs(RUN_DIR, exist_ok=True)
OPERATOR_LOGIN = "qa_cons_mp_s4_operator_20260705_195544"

GIT_HEAD = "69f8bad"


def ref_data(record):
    if not record:
        return False
    return {
        "model": record._name,
        "id": record.id,
        "display_name": record.display_name,
    }


def write_json(name, payload):
    path = os.path.join(RUN_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


checks = []
company = env.company
module = env["ir.module.module"].search(
    [("name", "=", "laplatine_procurement_control")], limit=1
)
operator = env["res.users"].search([("login", "=", OPERATOR_LOGIN)], limit=1)
stock_ops = env["laplatine.procurement.stock.ops"]
product = env["product.product"].search(
    [("default_code", "=", "MP-FEC-MAN-001")], limit=1
)
source_location = env["stock.location"].search(
    [("complete_name", "=", "WH/Stock/Conteneur Fécule")], limit=1
)

# --- MOA-UI-01 Menu opérateur ---
menu = env.ref("laplatine_procurement_control.menu_raw_material_consumption")
menu_ok = bool(env["ir.ui.menu"].with_user(operator).search([("id", "=", menu.id)]))
checks.append(
    {
        "id": "MOA-UI-01",
        "title": "Menu Consommation MP visible opérateur",
        "result": "OK" if menu_ok else "KO",
    }
)

# --- MOA-UI-02 Wizard consommation ouvert ---
wiz_env = env["laplatine.raw.material.consumption.wizard"].with_user(operator)
cons_wizard = wiz_env.create({"mode": "consumption"})
cons_ok = cons_wizard.mode == "consumption"
checks.append(
    {
        "id": "MOA-UI-02",
        "title": "Wizard consommation ouvrable",
        "result": "OK" if cons_ok else "KO",
    }
)

# --- MOA-UI-03 Passage mode correction ---
cons_wizard.write({"product_id": product.id})
action = cons_wizard.action_open_adjustment_mode()
adj_wizard = wiz_env.browse(action["res_id"])
mode_ok = adj_wizard.mode == "adjustment"
checks.append(
    {
        "id": "MOA-UI-03",
        "title": "Passage mode correction après sélection article",
        "result": "OK" if mode_ok else "KO",
        "action_res_id": action.get("res_id"),
    }
)

# --- MOA-UI-04 Lisibilité champs correction (fécule, lecture seule) ---
stock_kg = stock_ops.get_qty_kg_at_location(product, source_location)
adj_wizard.write(
    {
        "product_id": product.id,
        "location_id": source_location.id,
        "qty_counted_kg": stock_kg,
        "adjustment_reason": "MOA UI — lecture seule, ne pas appliquer",
    }
)
fields_ok = (
    adj_wizard.product_id == product
    and adj_wizard.location_id == source_location
    and abs(adj_wizard.qty_available_kg - stock_kg) < 0.01
    and adj_wizard.qty_counted_kg == stock_kg
    and adj_wizard.adjustment_reason
)
checks.append(
    {
        "id": "MOA-UI-04",
        "title": "Quantité Odoo, comptée et motif saisissables/lisibles",
        "result": "OK" if fields_ok else "KO",
        "qty_odoo_kg": adj_wizard.qty_available_kg,
        "qty_counted_kg": adj_wizard.qty_counted_kg,
        "location": ref_data(adj_wizard.location_id),
        "reason_sample": adj_wizard.adjustment_reason,
        "fecule_stock_unchanged_note": "Aucun action_apply_adjustment exécuté",
    }
)

# --- MOA-UI-05 Confirmation explicite (vue) ---
view = env.ref("laplatine_procurement_control.raw_material_consumption_wizard_view_form")
Wizard = env["laplatine.raw.material.consumption.wizard"]
confirm_ok = "confirm=" in view.arch and "Confirmer l'application" in view.arch
field_strings = {
    "qty_available_kg_adjustment": "Quantité enregistrée dans Odoo (kg)",
    "qty_counted_kg": Wizard._fields["qty_counted_kg"].string,
    "adjustment_reason": Wizard._fields["adjustment_reason"].string,
}
arch_ok = all(
    name in view.arch
    for name in ("qty_available_kg", "qty_counted_kg", "adjustment_reason")
)
labels_ok = arch_ok and "Appliquer la correction" in view.arch
checks.append(
    {
        "id": "MOA-UI-05",
        "title": "Confirmation explicite et libellés UI correction",
        "result": "OK" if confirm_ok and labels_ok else "KO",
        "confirm_present": confirm_ok,
        "labels_present": labels_ok,
        "field_strings": field_strings,
    }
)

# --- MOA-UI-06 Qualité notifications (article jetable, sans impact fécule) ---
probe_product = env["product.product"].search(
    [("name", "=", "MOA UI Probe Notification")], limit=1
)
if not probe_product:
    probe_product = env["product.product"].create(
        {
            "name": "MOA UI Probe Notification",
            "is_storable": True,
            "purchase_ok": True,
            "uom_id": env.ref("uom.product_uom_kgm").id,
            "uom_po_id": env.ref("uom.product_uom_kgm").id,
        }
    )
    probe_product.product_tmpl_id.laplatine_consumption_tracking = True

probe_loc = env["stock.location"].search(
    [("name", "=", "MOA UI Probe Bin")], limit=1
)
if not probe_loc:
    wh = company.laplatine_procurement_warehouse_id
    probe_loc = env["stock.location"].create(
        {
            "name": "MOA UI Probe Bin",
            "location_id": wh.lot_stock_id.id,
            "usage": "internal",
        }
    )

current_probe_kg = stock_ops.get_qty_kg_at_location(probe_product, probe_loc)
if current_probe_kg < 50.0:
    quant = stock_ops._get_quant_for_inventory(probe_product, probe_loc)
    quant.with_context(inventory_mode=True).write(
        {"inventory_quantity": stock_ops.qty_from_kg(probe_product, 100.0)}
    )
    quant.with_context(
        inventory_mode=True,
        inventory_name="MOA UI probe reset stock",
        set_inventory_quantity_auto_apply=True,
    ).action_apply_inventory()
    current_probe_kg = 100.0

target_counted = current_probe_kg - 10.0
probe_action = wiz_env.create(
    {
        "mode": "adjustment",
        "product_id": probe_product.id,
        "location_id": probe_loc.id,
        "qty_counted_kg": target_counted,
        "adjustment_reason": "MOA UI probe notification",
    }
).action_apply_adjustment()
notif_ok = (
    probe_action["params"]["title"] == "Correction appliquée"
    and probe_action["params"]["type"] == "success"
    and "Stock avant" in probe_action["params"]["message"]
    and "Stock après" in probe_action["params"]["message"]
)
checks.append(
    {
        "id": "MOA-UI-06",
        "title": "Notification succès correction (article jetable)",
        "result": "OK" if notif_ok else "KO",
        "notification": probe_action.get("params"),
    }
)

# --- MOA-UI-07 Notification seuil (article jetable) ---
threshold_product = env["product.product"].search(
    [("name", "=", "QA S4 Threshold Product")], limit=1
)
threshold_loc = env["stock.location"].search(
    [("name", "=", "QA S4 Threshold Bin")], limit=1
)
if threshold_product and threshold_loc:
    current_thr_kg = stock_ops.get_qty_kg_at_location(threshold_product, threshold_loc)
    target_thr = current_thr_kg - 10.0 if current_thr_kg > 10.0 else 4940.0
    thr_action = wiz_env.create(
        {
            "mode": "adjustment",
            "product_id": threshold_product.id,
            "location_id": threshold_loc.id,
            "qty_counted_kg": target_thr,
            "adjustment_reason": "MOA UI probe seuil",
        }
    ).action_apply_adjustment()
    thr_ok = (
        thr_action["params"]["type"] == "warning"
        and "Seuil de réapprovisionnement atteint" in thr_action["params"]["message"]
    )
else:
    thr_action = False
    thr_ok = False
checks.append(
    {
        "id": "MOA-UI-07",
        "title": "Notification seuil min (article jetable QA S4)",
        "result": "OK" if thr_ok else "KO",
        "notification": thr_action.get("params") if thr_action else False,
    }
)

# --- Fécule inchangée ---
fecule_after = stock_ops.get_qty_kg_at_location(product, source_location)
fecule_unchanged = abs(fecule_after - stock_kg) < 0.01
checks.append(
    {
        "id": "MOA-UI-08",
        "title": "Fécule non modifiée durant la passe MOA UI",
        "result": "OK" if fecule_unchanged else "KO",
        "stock_kg_before_after": stock_kg,
        "stock_kg_final": fecule_after,
    }
)

blocking = [c["id"] for c in checks if c.get("result") == "KO"]
verdict = "GO_MOA_UI_SLICE4" if not blocking else "NO_GO_MOA_UI"

payload = {
    "run_id": RUN_ID,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "url_lab": "http://127.0.0.1:18018",
    "git_head": GIT_HEAD,
    "module_version": module.installed_version,
    "operator": ref_data(operator),
    "production": "STOP",
    "verdict": verdict,
    "blocking_ko": blocking,
    "checks": checks,
    "fecule": {
        "product": ref_data(product),
        "location": ref_data(source_location),
        "stock_kg": fecule_after,
    },
    "note": "Passe MOA UI : champs wizard et notifications validés ; fécule lue sans correction appliquée.",
}

write_json("moa_ui_pass_evidence.json", payload)
env.cr.commit()

print("MOA_UI_VERDICT=%s" % verdict)
print("MOA_UI_JSON=%s" % os.path.join(RUN_DIR, "moa_ui_pass_evidence.json"))
for c in checks:
    print("  %s %s: %s" % (c["id"], c["result"], c["title"]))
