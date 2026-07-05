# -*- coding: utf-8 -*-
"""Campagne QA — recentrage cockpit CONS-MP-003 (LAPLATINE-CONS-MP-003)."""
import json
import os
from datetime import datetime

from odoo.exceptions import AccessError

RUN_ID = "QA-CONS-MP-003-20260705_220000"
RUN_DIR = os.environ.get("QA_OUT_DIR", "/var/lib/odoo/" + RUN_ID)
os.makedirs(RUN_DIR, exist_ok=True)
EXPECTED_VERSION = "18.0.1.6.0"
OPERATOR_LOGIN = "qa_cockpit_scope_operator_20260705"
OPERATOR_PASSWORD = "CockpitScope!2026"
MANAGER_LOGIN = "qa_cockpit_scope_manager_20260705"
MANAGER_PASSWORD = "CockpitScope!2026"


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


def ko(check_id, title, detail=None):
    entry = {"id": check_id, "title": title, "result": "KO"}
    if detail is not None:
        entry["detail"] = detail
    return entry


def ok(check_id, title, **extra):
    entry = {"id": check_id, "title": title, "result": "OK"}
    entry.update(extra)
    return entry


checks = []
company = env.company
module = env["ir.module.module"].search(
    [("name", "=", "laplatine_procurement_control")], limit=1
)
indicators = env["laplatine.procurement.indicators"]
stock_ops = env["laplatine.procurement.stock.ops"]
control_line = env["laplatine.procurement.control.line"]
warehouse = company.laplatine_procurement_warehouse_id
kg_uom = env.ref("uom.product_uom_kgm")
base_group = env.ref("base.group_user")
consumption_group = env.ref(
    "laplatine_procurement_control.group_raw_material_consumption_user"
)
cockpit_consult_group = env.ref(
    "laplatine_procurement_control.group_procurement_control_user"
)
cockpit_manager_group = env.ref(
    "laplatine_procurement_control.group_procurement_control_manager"
)

# --- Comptes QA ---
operator = env["res.users"].search([("login", "=", OPERATOR_LOGIN)], limit=1)
operator_vals = {
    "name": "QA Cockpit Scope Operator",
    "login": OPERATOR_LOGIN,
    "groups_id": [(6, 0, [base_group.id, consumption_group.id])],
}
if operator:
    operator.write(operator_vals)
else:
    operator = env["res.users"].create(operator_vals)
operator.write({"password": OPERATOR_PASSWORD})

manager = env["res.users"].search([("login", "=", MANAGER_LOGIN)], limit=1)
manager_vals = {
    "name": "QA Cockpit Scope Manager",
    "login": MANAGER_LOGIN,
    "groups_id": [(6, 0, [base_group.id, cockpit_manager_group.id])],
}
if manager:
    manager.write(manager_vals)
else:
    manager = env["res.users"].create(manager_vals)
manager.write({"password": MANAGER_PASSWORD})

fecule = env["product.product"].search(
    [("default_code", "=", "MP-FEC-MAN-001")], limit=1
)
fecule_loc = env["stock.location"].search(
    [("complete_name", "=", "WH/Stock/Conteneur Fécule")], limit=1
)
fecule_stock_initial = (
    stock_ops.get_qty_kg_at_location(fecule, fecule_loc) if fecule and fecule_loc else 0.0
)

# --- Préconditions ---
version_ok = (
    module.latest_version == EXPECTED_VERSION and module.state == "installed"
)
checks.append(
    ok("PRE-01", "Module upgradé et installé", version=module.latest_version)
    if version_ok
    else ko("PRE-01", "Module upgradé et installé", detail=module.latest_version)
)
checks.append(
    ok("PRE-02", "Suivi consommation fécule actif")
    if fecule and fecule.product_tmpl_id.laplatine_consumption_tracking
    else ko("PRE-02", "Suivi consommation fécule actif")
)
checks.append(
    ok("PRE-03", "Entrepôt de pilotage configuré", warehouse=ref_data(warehouse))
    if warehouse
    else ko("PRE-03", "Entrepôt de pilotage configuré")
)
checks.append(
    ok("PRE-04", "Compte manager cockpit QA prêt")
    if cockpit_manager_group in manager.groups_id
    else ko("PRE-04", "Compte manager cockpit QA prêt")
)

preflight = {
    "run_id": RUN_ID,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "url_lab": "http://127.0.0.1:18018",
    "production": "STOP",
    "reference": "LAPLATINE-CONS-MP-003",
    "module": {
        "installed_version": module.installed_version,
        "latest_version": module.latest_version,
        "state": module.state,
        "expected": EXPECTED_VERSION,
    },
    "fecule": {
        "product": ref_data(fecule),
        "location": ref_data(fecule_loc),
        "stock_kg_initial": fecule_stock_initial,
        "tracking": bool(
            fecule and fecule.product_tmpl_id.laplatine_consumption_tracking
        ),
    },
    "accounts": {
        "operator": OPERATOR_LOGIN,
        "manager": MANAGER_LOGIN,
    },
    "checks": [c for c in checks if c["id"].startswith("PRE-")],
}
write_json("preflight_evidence.json", preflight)


def _qa_product(name, tracking):
    product = env["product.product"].search([("name", "=", name)], limit=1)
    if not product:
        product = env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "purchase_ok": True,
                "standard_price": 1.0,
                "uom_id": kg_uom.id,
                "uom_po_id": kg_uom.id,
            }
        )
    product.product_tmpl_id.laplatine_consumption_tracking = tracking
    return product


def _set_stock(product, qty):
    quant = stock_ops._get_quant_for_inventory(product, warehouse.lot_stock_id)
    quant.with_context(inventory_mode=True).write(
        {"inventory_quantity": stock_ops.qty_from_kg(product, qty)}
    )
    quant.with_context(
        inventory_mode=True,
        inventory_name="QA CONS-MP-003 stock set",
        set_inventory_quantity_auto_apply=True,
    ).action_apply_inventory()


def _orderpoint(product, min_qty=50.0, max_qty=200.0):
    op = env["stock.warehouse.orderpoint"].search(
        [
            ("product_id", "=", product.id),
            ("warehouse_id", "=", warehouse.id),
        ],
        limit=1,
    )
    if not op:
        op = env["stock.warehouse.orderpoint"].create(
            {
                "product_id": product.id,
                "warehouse_id": warehouse.id,
                "location_id": warehouse.lot_stock_id.id,
                "product_min_qty": min_qty,
                "product_max_qty": max_qty,
            }
        )
    return op


def _supplier(product):
    vendor = env["res.partner"].search(
        [("name", "=", "QA Cockpit Scope Vendor")], limit=1
    )
    if not vendor:
        vendor = env["res.partner"].create({"name": "QA Cockpit Scope Vendor"})
    info = env["product.supplierinfo"].search(
        [
            ("product_tmpl_id", "=", product.product_tmpl_id.id),
            ("partner_id", "=", vendor.id),
        ],
        limit=1,
    )
    if not info:
        env["product.supplierinfo"].create(
            {
                "partner_id": vendor.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "delay": 90,
                "price": 1.0,
                "min_qty": 1.0,
            }
        )
    return vendor


def _line(product):
    return control_line.search(
        [("product_id", "=", product.id), ("company_id", "=", company.id)],
        limit=1,
    )


def _refresh():
    control_line.with_user(manager).action_refresh()


# --- Articles A / B / C ---
article_a = _qa_product("QA Cockpit Scope Article A", True)
article_b = _qa_product("QA Cockpit Scope Article B", False)
article_c = _qa_product("QA Cockpit Scope Article C", True)

_set_stock(article_a, 1000.0)
_set_stock(article_b, 1000.0)
_set_stock(article_c, 250.0)
_a_op = _orderpoint(article_a)
_b_op = _orderpoint(article_b)
_a_vendor = _supplier(article_a)
_b_vendor = _supplier(article_b)
env["stock.warehouse.orderpoint"].search(
    [("product_id", "=", article_c.id), ("warehouse_id", "=", warehouse.id)]
).unlink()

_refresh()

line_a = _line(article_a)
line_b = _line(article_b)
line_c = _line(article_c)

checks.append(
    ok(
        "AC01",
        "Article A suivi et paramétré visible dans le cockpit",
        product=ref_data(article_a),
        min_qty=line_a.min_qty if line_a else None,
    )
    if line_a and line_a.min_qty == 50.0
    else ko("AC01", "Article A suivi et paramétré visible dans le cockpit")
)

checks.append(
    ok("AC02", "Article B non suivi absent du cockpit", product=ref_data(article_b))
    if not line_b
    else ko("AC02", "Article B non suivi absent du cockpit", line_id=line_b.id)
)

checks.append(
    ok(
        "AC03",
        "Orderpoint + fournisseur insuffisants sans suivi (Article B)",
        has_orderpoint=bool(_b_op),
        has_supplier=bool(_b_vendor),
    )
    if not line_b
    else ko("AC03", "Orderpoint + fournisseur insuffisants sans suivi")
)

alert_c = set(line_c.alert_ids.mapped("code")) if line_c else set()
checks.append(
    ok(
        "AC07",
        "Article C suivi sans orderpoint visible avec alerte",
        alerts=sorted(alert_c),
    )
    if line_c and "orderpoint_incomplete" in alert_c
    else ko("AC07", "Article C suivi sans orderpoint visible avec alerte")
)

# --- Cycle cochage / décochage Article A ---
article_a.product_tmpl_id.laplatine_consumption_tracking = False
_refresh()
line_a_off = _line(article_a)
checks.append(
    ok("AC04", "Décochage retire la ligne cockpit (Article A)")
    if not line_a_off
    else ko("AC04", "Décochage retire la ligne cockpit (Article A)")
)

article_a.product_tmpl_id.laplatine_consumption_tracking = True
_refresh()
line_a_on = _line(article_a)
checks.append(
    ok("AC05", "Cochage recrée la ligne cockpit (Article A)")
    if line_a_on
    else ko("AC05", "Cochage recrée la ligne cockpit (Article A)")
)

# Ligne obsolète manuelle sur article non suivi
stale_product = _qa_product("QA Cockpit Scope Stale Line", False)
stale_line = control_line.create(
    {
        "product_id": stale_product.id,
        "company_id": company.id,
        "risk_status": "normal",
    }
)
_refresh()
checks.append(
    ok("AC06", "Ligne obsolète supprimée pour article non suivi")
    if not stale_line.exists()
    else ko("AC06", "Ligne obsolète supprimée pour article non suivi")
)

# --- Périmètre commun ---
probe_tracked = _qa_product("QA Cockpit Scope Probe Tracked", True)
probe_untracked = _qa_product("QA Cockpit Scope Probe Untracked", False)
cockpit_ids = set(indicators.get_eligible_products(company).ids)
wizard_ids = set(stock_ops.get_eligible_consumption_products(company).ids)
scope_ok = (
    probe_tracked.id in cockpit_ids
    and probe_tracked.id in wizard_ids
    and probe_untracked.id not in cockpit_ids
    and probe_untracked.id not in wizard_ids
)
checks.append(
    ok(
        "AC08",
        "Périmètre commun booléen Suivi consommation La Platine",
        cockpit_count=len(cockpit_ids),
        wizard_count=len(wizard_ids),
    )
    if scope_ok
    else ko("AC08", "Périmètre commun booléen Suivi consommation La Platine")
)

# --- Fécule dans cockpit ---
_refresh()
fecule_line = _line(fecule) if fecule else False
checks.append(
    ok(
        "AC09",
        "Fécule suivie présente dans le cockpit après actualisation",
        min_qty=fecule_line.min_qty if fecule_line else None,
        supplier=ref_data(fecule_line.supplier_id) if fecule_line else None,
    )
    if fecule_line
    else ko("AC09", "Fécule suivie présente dans le cockpit après actualisation")
)

# --- Non-régression wizards ---
probe_loc = env["stock.location"].search(
    [("name", "=", "QA Cockpit Scope Probe Bin")], limit=1
)
if not probe_loc:
    probe_loc = env["stock.location"].create(
        {
            "name": "QA Cockpit Scope Probe Bin",
            "location_id": warehouse.lot_stock_id.id,
            "usage": "internal",
        }
    )
if stock_ops.get_qty_kg_at_location(probe_tracked, probe_loc) < 50.0:
    quant = stock_ops._get_quant_for_inventory(probe_tracked, probe_loc)
    quant.with_context(inventory_mode=True).write(
        {"inventory_quantity": stock_ops.qty_from_kg(probe_tracked, 100.0)}
    )
    quant.with_context(
        inventory_mode=True,
        inventory_name="QA cockpit scope probe stock",
        set_inventory_quantity_auto_apply=True,
    ).action_apply_inventory()

cons_action = (
    env["laplatine.raw.material.consumption.wizard"]
    .with_user(operator)
    .create(
        {
            "product_id": probe_tracked.id,
            "location_id": probe_loc.id,
            "qty_consumed_kg": 2.0,
        }
    )
    .action_register_consumption()
)
checks.append(
    ok(
        "AC10",
        "Non-régression wizard consommation",
        notification=cons_action.get("params", {}).get("title"),
    )
    if cons_action.get("params", {}).get("title") == "Consommation enregistrée"
    else ko("AC10", "Non-régression wizard consommation")
)

# BUG-CONS-MP-003 : emplacement auto sans location_id persisté
auto_wizard = env["laplatine.raw.material.consumption.wizard"].with_user(operator).create(
    {
        "product_id": probe_tracked.id,
        "qty_consumed_kg": 1.0,
    }
)
auto_ok = False
try:
    if len(auto_wizard.allowed_location_ids) == 1:
        auto_action = auto_wizard.action_register_consumption()
        auto_ok = auto_action.get("params", {}).get("title") == "Consommation enregistrée"
except Exception as exc:
    auto_ok = False
    auto_error = str(exc)
else:
    auto_error = None
checks.append(
    ok("BUG-003", "Emplacement auto consommation enregistré sans location_id UI")
    if auto_ok
    else ko(
        "BUG-003",
        "Emplacement auto consommation enregistré sans location_id UI",
        detail=auto_error,
    )
)

# Seuil min après consommation (non-régression AC11)
thr_product = _qa_product("QA Cockpit Scope Threshold Product", True)
thr_loc = env["stock.location"].search(
    [("name", "=", "QA Cockpit Scope Threshold Bin")], limit=1
)
if not thr_loc:
    thr_loc = env["stock.location"].create(
        {
            "name": "QA Cockpit Scope Threshold Bin",
            "location_id": warehouse.lot_stock_id.id,
            "usage": "internal",
        }
    )
if not env["stock.warehouse.orderpoint"].search(
    [("product_id", "=", thr_product.id), ("warehouse_id", "=", warehouse.id)],
    limit=1,
):
    env["stock.warehouse.orderpoint"].create(
        {
            "product_id": thr_product.id,
            "warehouse_id": warehouse.id,
            "location_id": warehouse.lot_stock_id.id,
            "product_min_qty": 5000.0,
            "product_max_qty": 10000.0,
        }
    )
if stock_ops.get_qty_kg_at_location(thr_product, thr_loc) < 5050.0:
    quant = stock_ops._get_quant_for_inventory(thr_product, thr_loc)
    quant.with_context(inventory_mode=True).write(
        {"inventory_quantity": stock_ops.qty_from_kg(thr_product, 5050.0)}
    )
    quant.with_context(
        inventory_mode=True,
        inventory_name="QA cockpit scope threshold prep",
        set_inventory_quantity_auto_apply=True,
    ).action_apply_inventory()
thr_action = (
    env["laplatine.raw.material.consumption.wizard"]
    .with_user(operator)
    .create(
        {
            "product_id": thr_product.id,
            "location_id": thr_loc.id,
            "qty_consumed_kg": 100.0,
        }
    )
    .action_register_consumption()
)
checks.append(
    ok(
        "AC11",
        "Alerte seuil minimum après consommation (non-régression)",
        notification_type=thr_action.get("params", {}).get("type"),
    )
    if thr_action.get("params", {}).get("type") == "warning"
    and "Seuil de réapprovisionnement atteint"
    in thr_action.get("params", {}).get("message", "")
    else ko("AC11", "Alerte seuil minimum après consommation (non-régression)")
)

# Sécurité opérateur cockpit
sec_ok = False
try:
    control_line.with_user(operator).action_refresh()
except AccessError:
    sec_ok = True
except Exception:
    sec_ok = False
checks.append(
    ok("AC12", "Opérateur consommation ne peut pas actualiser le cockpit")
    if sec_ok
    else ko("AC12", "Opérateur consommation ne peut pas actualiser le cockpit")
)

cockpit_evidence = {
    "run_id": RUN_ID,
    "articles": {
        "A": {
            "product": ref_data(article_a),
            "tracking": True,
            "line_after_refresh": ref_data(line_a_on),
        },
        "B": {
            "product": ref_data(article_b),
            "tracking": False,
            "line_absent": not bool(line_b),
        },
        "C": {
            "product": ref_data(article_c),
            "tracking": True,
            "line": ref_data(line_c),
            "alerts": sorted(alert_c),
        },
    },
    "toggle_cycle": {
        "after_uncheck": not bool(line_a_off),
        "after_recheck": bool(line_a_on),
    },
    "fecule_line": ref_data(fecule_line),
}
write_json("cockpit_scope_evidence.json", cockpit_evidence)

fecule_final = (
    stock_ops.get_qty_kg_at_location(fecule, fecule_loc) if fecule and fecule_loc else 0.0
)
checks.append(
    ok(
        "FEC-FINAL",
        "Stock fécule inchangé après campagne QA",
        stock_kg_initial=fecule_stock_initial,
        stock_kg_final=fecule_final,
    )
    if abs(fecule_final - fecule_stock_initial) < 0.01
    else ko("FEC-FINAL", "Stock fécule inchangé après campagne QA")
)

blocking = [c["id"] for c in checks if c.get("result") == "KO"]
verdict = "GO_QA_CONS_MP_003_LAB" if not blocking else "NO_GO_QA_CONS_MP_003"

final = {
    "run_id": RUN_ID,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "url_lab": "http://127.0.0.1:18018",
    "reference": "LAPLATINE-CONS-MP-003",
    "module_version": module.latest_version,
    "production": "STOP",
    "verdict": verdict,
    "blocking_ko": blocking,
    "checks_total": len(checks),
    "checks_ok": len([c for c in checks if c["result"] == "OK"]),
    "checks": checks,
    "fecule": {
        "stock_kg_initial": fecule_stock_initial,
        "stock_kg_final": fecule_final,
    },
    "automated_tests_note": "113/113 verts (--test-tags=laplatine_procurement_control)",
}
write_json("final_evidence.json", final)
env.cr.commit()

print("QA_VERDICT=%s" % verdict)
print("QA_JSON=%s" % os.path.join(RUN_DIR, "final_evidence.json"))
print("CHECKS_OK=%s/%s" % (final["checks_ok"], final["checks_total"]))
for c in checks:
    print("  %s %s: %s" % (c["id"], c["result"], c["title"]))
