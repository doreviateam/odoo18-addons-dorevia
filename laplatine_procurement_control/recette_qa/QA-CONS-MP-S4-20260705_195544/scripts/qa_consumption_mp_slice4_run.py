# -*- coding: utf-8 -*-
"""Campagne QA Slice 4 — exécution backend (wizard ORM, même code que l'UI)."""
import json
import os
from datetime import datetime

RUN_ID = "QA-CONS-MP-S4-20260705_195544"
RUN_DIR = os.environ.get("QA_OUT_DIR", "/tmp/" + RUN_ID)
os.makedirs(RUN_DIR, exist_ok=True)
OPERATOR_LOGIN = "qa_cons_mp_s4_operator_20260705_195544"
OPERATOR_PASSWORD = "S4Qa!2026"
PILOT_REASON = "Ancienne consommation non enregistrée"
PILOT_COUNTED_KG = 13150.0
PILOT_EXPECTED_BEFORE_KG = 13175.0


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


def stock_kg(product, location):
    return stock_ops.get_qty_kg_at_location(product, location)


def set_stock_kg(product, location, qty_kg):
    qty_uom = stock_ops.qty_from_kg(product, qty_kg)
    quant = env["stock.quant"].search(
        [
            ("product_id", "=", product.id),
            ("location_id", "=", location.id),
            ("lot_id", "=", False),
            ("package_id", "=", False),
        ],
        limit=1,
    )
    if not quant:
        quant = env["stock.quant"].with_context(inventory_mode=True).create(
            {"product_id": product.id, "location_id": location.id}
        )
    quant.with_context(inventory_mode=True).write({"inventory_quantity": qty_uom})
    quant.with_context(
        inventory_mode=True,
        inventory_name="QA S4 préparation stock",
        set_inventory_quantity_auto_apply=True,
    ).action_apply_inventory()


results = []
blocking = []

company = env.company
module = env["ir.module.module"].search(
    [("name", "=", "laplatine_procurement_control")], limit=1
)
stock_ops = env["laplatine.procurement.stock.ops"]
product = env["product.product"].search(
    [("default_code", "=", "MP-FEC-MAN-001")], limit=1
)
source_location = env["stock.location"].search(
    [("complete_name", "=", "WH/Stock/Conteneur Fécule")], limit=1
)

consumption_group = env.ref(
    "laplatine_procurement_control.group_raw_material_consumption_user"
)
base_group = env.ref("base.group_user")
operator = env["res.users"].search([("login", "=", OPERATOR_LOGIN)], limit=1)
operator_values = {
    "name": "QA CONS MP S4 Opérateur",
    "login": OPERATOR_LOGIN,
    "groups_id": [(6, 0, [base_group.id, consumption_group.id])],
}
if operator:
    operator.write(operator_values)
else:
    operator = env["res.users"].create(operator_values)
operator.write({"password": OPERATOR_PASSWORD})

# --- Préparation stock pilote ---
before_prep_kg = stock_kg(product, source_location)
if abs(before_prep_kg - PILOT_EXPECTED_BEFORE_KG) > 0.01:
    set_stock_kg(product, source_location, PILOT_EXPECTED_BEFORE_KG)

preflight = {
    "run_id": RUN_ID,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "production": "STOP - lab uniquement",
    "module": {
        "installed_version": module.installed_version,
        "latest_version": module.latest_version,
        "state": module.state,
    },
    "operator": {
        "login": OPERATOR_LOGIN,
        "password": OPERATOR_PASSWORD,
        "groups": sorted(operator.groups_id.mapped("name")),
    },
    "fecule": {
        "product": ref_data(product),
        "source_location": ref_data(source_location),
        "stock_before_prep_kg": before_prep_kg,
        "stock_prepared_kg": stock_kg(product, source_location),
        "tracking": product.product_tmpl_id.laplatine_consumption_tracking,
    },
}
write_json("preflight_evidence.json", preflight)

# --- S4-01 Pilote correction -25 kg ---
wizard_env = env["laplatine.raw.material.consumption.wizard"].with_user(operator)
before_kg = stock_kg(product, source_location)
inventory_moves_before = env["stock.move"].search_count(
    [
        ("product_id", "=", product.id),
        ("is_inventory", "=", True),
        ("state", "=", "done"),
    ]
)

wizard = wizard_env.create(
    {
        "mode": "adjustment",
        "product_id": product.id,
        "location_id": source_location.id,
        "qty_counted_kg": PILOT_COUNTED_KG,
        "adjustment_reason": PILOT_REASON,
    }
)
action = wizard.action_apply_adjustment()
after_kg = stock_kg(product, source_location)
latest_inv_move = env["stock.move"].search(
    [
        ("product_id", "=", product.id),
        ("is_inventory", "=", True),
        ("state", "=", "done"),
    ],
    order="id desc",
    limit=1,
)

pilot_ok = (
    abs(before_kg - PILOT_EXPECTED_BEFORE_KG) < 0.01
    and abs(after_kg - PILOT_COUNTED_KG) < 0.01
    and abs(after_kg - before_kg + 25.0) < 0.01
    and latest_inv_move
    and latest_inv_move.state == "done"
    and latest_inv_move.name == PILOT_REASON
    and latest_inv_move.reference == PILOT_REASON
    and latest_inv_move.create_uid == operator
    and action["params"]["title"] == "Correction appliquée"
    and "13 150 kg" in action["params"]["message"]
    and "Écart : -25 kg" in action["params"]["message"]
)
results.append(
    {
        "id": "S4-01",
        "title": "Correction pilote fécule -25 kg",
        "blocking": True,
        "result": "OK" if pilot_ok else "KO",
        "before_kg": before_kg,
        "after_kg": after_kg,
        "move": ref_data(latest_inv_move),
        "move_state": latest_inv_move.state if latest_inv_move else False,
        "move_name": latest_inv_move.name if latest_inv_move else False,
        "move_reference": latest_inv_move.reference if latest_inv_move else False,
        "move_author": ref_data(latest_inv_move.create_uid) if latest_inv_move else False,
        "notification": action.get("params"),
    }
)
if not pilot_ok:
    blocking.append("S4-01")

pilot_evidence = write_json(
    "pilot_adjustment_evidence.json",
    {
        "run_id": RUN_ID,
        "generated_at": datetime.utcnow().isoformat(),
        "before_kg": before_kg,
        "counted_kg": PILOT_COUNTED_KG,
        "after_kg": after_kg,
        "diff_kg": after_kg - before_kg,
        "reason": PILOT_REASON,
        "inventory_moves_before": inventory_moves_before,
        "inventory_moves_after": env["stock.move"].search_count(
            [
                ("product_id", "=", product.id),
                ("is_inventory", "=", True),
                ("state", "=", "done"),
            ]
        ),
        "latest_inventory_move": {
            "move": ref_data(latest_inv_move),
            "state": latest_inv_move.state,
            "name": latest_inv_move.name,
            "reference": latest_inv_move.reference,
            "origin": latest_inv_move.origin,
            "is_inventory": latest_inv_move.is_inventory,
            "source": ref_data(latest_inv_move.location_id),
            "destination": ref_data(latest_inv_move.location_dest_id),
            "create_uid": ref_data(latest_inv_move.create_uid),
            "date": latest_inv_move.date.isoformat() if latest_inv_move.date else False,
        },
        "notification": action,
        "pilot_ok": pilot_ok,
    },
)

# --- S4-02 Motif obligatoire ---
try:
    wizard_env.create(
        {
            "mode": "adjustment",
            "product_id": product.id,
            "location_id": source_location.id,
            "qty_counted_kg": after_kg,
            "adjustment_reason": "   ",
        }
    ).action_apply_adjustment()
    results.append({"id": "S4-02", "title": "Motif obligatoire", "blocking": True, "result": "KO"})
    blocking.append("S4-02")
except Exception as exc:
    ok = "motif" in str(exc).lower() or "Motif" in str(exc)
    results.append(
        {
            "id": "S4-02",
            "title": "Motif obligatoire",
            "blocking": True,
            "result": "OK" if ok else "KO",
            "error": str(exc),
        }
    )
    if not ok:
        blocking.append("S4-02")

# --- S4-03 Quantité comptée négative ---
try:
    wizard_env.create(
        {
            "mode": "adjustment",
            "product_id": product.id,
            "location_id": source_location.id,
            "qty_counted_kg": -1.0,
            "adjustment_reason": "Test négatif QA",
        }
    ).action_apply_adjustment()
    results.append({"id": "S4-03", "title": "Refus qty négative", "blocking": True, "result": "KO"})
    blocking.append("S4-03")
except Exception as exc:
    ok = "négative" in str(exc).lower()
    results.append(
        {
            "id": "S4-03",
            "title": "Refus qty négative",
            "blocking": True,
            "result": "OK" if ok else "KO",
            "error": str(exc),
        }
    )
    if not ok:
        blocking.append("S4-03")

# --- S4-04 Confirmation explicite (vue) ---
view = env.ref("laplatine_procurement_control.raw_material_consumption_wizard_view_form")
confirm_ok = "confirm=" in view.arch and "Confirmer l'application" in view.arch
results.append(
    {
        "id": "S4-04",
        "title": "Confirmation explicite UI",
        "blocking": True,
        "result": "OK" if confirm_ok else "KO",
    }
)
if not confirm_ok:
    blocking.append("S4-04")

# --- S4-05 Non-régression consommation Slice 3 ---
set_stock_kg(product, source_location, after_kg + 10.0)
cons_wizard = wizard_env.create(
    {
        "mode": "consumption",
        "product_id": product.id,
        "location_id": source_location.id,
        "qty_consumed_kg": 10.0,
    }
)
cons_action = cons_wizard.action_register_consumption()
stock_after_cons = stock_kg(product, source_location)
cons_ok = (
    cons_action["params"]["title"] == "Consommation enregistrée"
    and abs(stock_after_cons - after_kg) < 0.01
)
results.append(
    {
        "id": "S4-05",
        "title": "Non-régression consommation Slice 3",
        "blocking": True,
        "result": "OK" if cons_ok else "KO",
        "stock_after_kg": stock_after_cons,
    }
)
if not cons_ok:
    blocking.append("S4-05")

# --- S4-06 Seuil min (article QA jetable) ---
threshold_product = env["product.product"].search(
    [("name", "=", "QA S4 Threshold Product")], limit=1
)
if not threshold_product:
    threshold_product = env["product.product"].create(
        {
            "name": "QA S4 Threshold Product",
            "is_storable": True,
            "purchase_ok": True,
            "uom_id": env.ref("uom.product_uom_kgm").id,
            "uom_po_id": env.ref("uom.product_uom_kgm").id,
        }
    )
    threshold_product.product_tmpl_id.laplatine_consumption_tracking = True

threshold_loc = env["stock.location"].search(
    [("name", "=", "QA S4 Threshold Bin")], limit=1
)
if not threshold_loc:
    wh = company.laplatine_procurement_warehouse_id or env["stock.warehouse"].search(
        [("company_id", "=", company.id)], limit=1
    )
    threshold_loc = env["stock.location"].create(
        {
            "name": "QA S4 Threshold Bin",
            "location_id": wh.lot_stock_id.id,
            "usage": "internal",
        }
    )

env["stock.warehouse.orderpoint"].search(
    [("product_id", "=", threshold_product.id)]
).unlink()
env["stock.warehouse.orderpoint"].create(
    {
        "product_id": threshold_product.id,
        "warehouse_id": company.laplatine_procurement_warehouse_id.id,
        "location_id": company.laplatine_procurement_warehouse_id.lot_stock_id.id,
        "product_min_qty": 5000.0,
        "product_max_qty": 10000.0,
    }
)
set_stock_kg(threshold_product, threshold_loc, 5010.0)
thr_action = wizard_env.create(
    {
        "mode": "adjustment",
        "product_id": threshold_product.id,
        "location_id": threshold_loc.id,
        "qty_counted_kg": 4950.0,
        "adjustment_reason": "QA S4 seuil min",
    }
).action_apply_adjustment()
thr_ok = (
    thr_action["params"]["type"] == "warning"
    and "Seuil de réapprovisionnement atteint" in thr_action["params"]["message"]
    and "4 950 kg" in thr_action["params"]["message"]
    and "5 000 kg" in thr_action["params"]["message"]
)
results.append(
    {
        "id": "S4-06",
        "title": "Alerte seuil min après correction",
        "blocking": True,
        "result": "OK" if thr_ok else "KO",
        "notification": thr_action.get("params"),
    }
)
if not thr_ok:
    blocking.append("S4-06")

verdict = "GO_QA_SLICE4_LAB" if not blocking else "NO_GO"
final = {
    "run_id": RUN_ID,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "production": "STOP - lab uniquement",
    "module_version": module.installed_version,
    "verdict": verdict,
    "blocking_ko": blocking,
    "results": results,
    "fecule_final_stock_kg": stock_kg(product, source_location),
}
final_path = write_json("final_evidence.json", final)

env.cr.commit()
print("QA_CONS_MP_S4_VERDICT=%s" % verdict)
print("QA_CONS_MP_S4_FINAL_JSON=%s" % final_path)
print("QA_CONS_MP_S4_OPERATOR=%s" % OPERATOR_LOGIN)
print("QA_CONS_MP_S4_PASSWORD=%s" % OPERATOR_PASSWORD)
for row in results:
    print("  %s %s: %s" % (row["id"], row["result"], row["title"]))
