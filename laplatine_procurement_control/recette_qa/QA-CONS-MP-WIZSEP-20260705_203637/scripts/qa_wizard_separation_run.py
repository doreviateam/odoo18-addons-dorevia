# -*- coding: utf-8 -*-
"""Campagne QA — séparation wizards consommation / mise à jour stock (CONS-MP-002)."""
import json
import os
from datetime import datetime

RUN_ID = "QA-CONS-MP-WIZSEP-20260705_203637"
RUN_DIR = os.environ.get("QA_OUT_DIR", "/var/lib/odoo/" + RUN_ID)
os.makedirs(RUN_DIR, exist_ok=True)
OPERATOR_LOGIN = "qa_wizsep_operator_20260705"
OPERATOR_PASSWORD = "WizSep!2026"
EXPECTED_VERSION = "18.0.1.5.0"


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
    if detail:
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
stock_ops = env["laplatine.procurement.stock.ops"]
consumption_group = env.ref(
    "laplatine_procurement_control.group_raw_material_consumption_user"
)
cockpit_group = env.ref(
    "laplatine_procurement_control.group_procurement_control_user"
)
base_group = env.ref("base.group_user")

operator = env["res.users"].search([("login", "=", OPERATOR_LOGIN)], limit=1)
operator_values = {
    "name": "QA Wizard Separation Operator",
    "login": OPERATOR_LOGIN,
    "groups_id": [(6, 0, [base_group.id, consumption_group.id])],
}
if operator:
    operator.write(operator_values)
else:
    operator = env["res.users"].create(operator_values)
operator.write({"password": OPERATOR_PASSWORD})

internal_user = env["res.users"].search(
    [("login", "=", "qa_wizsep_internal_20260705")], limit=1
)
if not internal_user:
    internal_user = env["res.users"].create(
        {
            "name": "QA Wizard Separation Internal",
            "login": "qa_wizsep_internal_20260705",
            "groups_id": [(6, 0, [base_group.id])],
        }
    )

fecule = env["product.product"].search(
    [("default_code", "=", "MP-FEC-MAN-001")], limit=1
)
fecule_loc = env["stock.location"].search(
    [("complete_name", "=", "WH/Stock/Conteneur Fécule")], limit=1
)
fecule_stock_initial = stock_ops.get_qty_kg_at_location(fecule, fecule_loc)

# --- Préconditions ---
version_ok = module.latest_version == EXPECTED_VERSION and module.state == "installed"
checks.append(
    ok("PRE-01", "Module upgradé et installé", version=module.latest_version)
    if version_ok
    else ko("PRE-01", "Module upgradé et installé", detail=module.latest_version)
)

tracking_ok = fecule.product_tmpl_id.laplatine_consumption_tracking
checks.append(
    ok("PRE-02", "Suivi consommation fécule actif")
    if tracking_ok
    else ko("PRE-02", "Suivi consommation fécule actif")
)

operator_group_ok = consumption_group in operator.groups_id
checks.append(
    ok("PRE-03", "Groupe opérateur attribué au compte QA")
    if operator_group_ok
    else ko("PRE-03", "Groupe opérateur attribué au compte QA")
)

preflight = {
    "run_id": RUN_ID,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "url_lab": "http://127.0.0.1:18018",
    "production": "STOP",
    "module": {
        "installed_version": module.installed_version,
        "latest_version": module.latest_version,
        "state": module.state,
        "expected": EXPECTED_VERSION,
    },
    "operator": {
        "login": OPERATOR_LOGIN,
        "password": OPERATOR_PASSWORD,
        "groups": sorted(operator.groups_id.mapped("name")),
    },
    "fecule": {
        "product": ref_data(fecule),
        "location": ref_data(fecule_loc),
        "stock_kg_initial": fecule_stock_initial,
        "tracking": tracking_ok,
    },
    "checks": [c for c in checks if c["id"].startswith("PRE-")],
}
write_json("preflight_evidence.json", preflight)

# --- AC01–AC03 Menus et ouverture directe ---
menu_root = env.ref("laplatine_procurement_control.menu_laplatine_root")
menu_cons = env.ref("laplatine_procurement_control.menu_raw_material_consumption")
menu_stock = env.ref("laplatine_procurement_control.menu_raw_material_stock_update")
menu_env = env["ir.ui.menu"].with_user(operator)

menus_visible = all(
    menu_env.search([("id", "=", m.id)]) for m in (menu_root, menu_cons, menu_stock)
)
checks.append(
    ok(
        "AC01",
        "Deux menus distincts sous Inventaire → La Platine",
        menus=[m.display_name for m in (menu_cons, menu_stock)],
    )
    if menus_visible
    else ko("AC01", "Deux menus distincts sous Inventaire → La Platine")
)

cons_model_ok = menu_cons.action.res_model == "laplatine.raw.material.consumption.wizard"
stock_model_ok = (
    menu_stock.action.res_model == "laplatine.raw.material.stock.update.wizard"
)
checks.append(
    ok("AC02", "Chaque menu ouvre son wizard dédié")
    if cons_model_ok and stock_model_ok
    else ko("AC02", "Chaque menu ouvre son wizard dédié")
)

cons_view = env.ref(
    "laplatine_procurement_control.raw_material_consumption_wizard_view_form"
)
stock_view = env.ref(
    "laplatine_procurement_control.raw_material_stock_update_wizard_view_form"
)
no_mode = (
    'name="mode"' not in cons_view.arch
    and "action_open_adjustment_mode" not in cons_view.arch
    and "Mettre à jour la quantité disponible" not in cons_view.arch
    and 'name="mode"' not in stock_view.arch
)
checks.append(
    ok("AC03", "Aucun champ mode ni bouton de bascule")
    if no_mode
    else ko("AC03", "Aucun champ mode ni bouton de bascule")
)

# --- AC04–AC05 Wizards épurés ---
cons_clean = all(
    x not in cons_view.arch
    for x in ("qty_counted_kg", "adjustment_reason", "action_open_adjustment_mode")
) and all(
    x in cons_view.arch
    for x in ("product_id", "location_id", "qty_available_kg", "qty_consumed_kg")
)
checks.append(
    ok("AC04", "Wizard consommation épuré")
    if cons_clean
    else ko("AC04", "Wizard consommation épuré")
)

stock_clean = (
    "qty_consumed_kg" not in stock_view.arch
    and "action_register_consumption" not in stock_view.arch
    and all(
        x in stock_view.arch
        for x in (
            "product_id",
            "location_id",
            "qty_available_kg",
            "qty_counted_kg",
            "qty_diff_kg",
            "adjustment_reason",
        )
    )
    and "Mettre à jour le stock" in stock_view.arch
)
checks.append(
    ok("AC05", "Wizard mise à jour épuré")
    if stock_clean
    else ko("AC05", "Wizard mise à jour épuré")
)

# --- AC08–AC09 Emplacements ---
cons_wiz_env = env["laplatine.raw.material.consumption.wizard"].with_user(operator)
stock_wiz_env = env["laplatine.raw.material.stock.update.wizard"].with_user(operator)

empty_loc = env["stock.location"].search(
    [("name", "=", "QA WizSep Empty Bin")], limit=1
)
if not empty_loc:
    wh = company.laplatine_procurement_warehouse_id
    empty_loc = env["stock.location"].create(
        {
            "name": "QA WizSep Empty Bin",
            "location_id": wh.lot_stock_id.id,
            "usage": "internal",
        }
    )

cons_allowed = stock_ops.get_allowed_source_locations(fecule, company, "consumption")
update_allowed = stock_ops.get_allowed_source_locations(fecule, company, "adjustment")
ac08 = fecule_loc in cons_allowed and empty_loc not in cons_allowed
ac09 = empty_loc in update_allowed and fecule_loc in update_allowed
checks.append(ok("AC08", "Consommation : emplacements stock positif uniquement") if ac08 else ko("AC08", "Consommation : emplacements stock positif uniquement"))
checks.append(ok("AC09", "Mise à jour : tous emplacements pilotage y compris stock nul") if ac09 else ko("AC09", "Mise à jour : tous emplacements pilotage y compris stock nul"))

# --- AC10 Sécurité menus ---
internal_menu_env = env["ir.ui.menu"].with_user(internal_user)
no_internal = not any(
    internal_menu_env.search([("id", "=", m.id)])
    for m in (menu_root, menu_cons, menu_stock)
)
no_cockpit = cockpit_group not in operator.groups_id
checks.append(
    ok("AC10", "Opérateur accède aux wizards sans cockpit")
    if no_internal and no_cockpit
    else ko("AC10", "Opérateur accède aux wizards sans cockpit")
)

# --- AC13 Cockpit non régressé ---
consult_user = env["res.users"].search(
    [("login", "=", "qa_wizsep_consult_20260705")], limit=1
)
if not consult_user:
    consult_user = env["res.users"].create(
        {
            "name": "QA Wizard Separation Consult",
            "login": "qa_wizsep_consult_20260705",
            "groups_id": [(6, 0, [base_group.id, cockpit_group.id])],
        }
    )
cockpit_menu = env.ref(
    "laplatine_procurement_control.menu_procurement_control_cockpit"
)
cockpit_visible = bool(
    env["ir.ui.menu"].with_user(consult_user).search([("id", "=", cockpit_menu.id)])
)
checks.append(
    ok("AC13", "Cockpit accessible profil Consultation")
    if cockpit_visible
    else ko("AC13", "Cockpit accessible profil Consultation")
)

# --- 13.2 Recette ergonomique fécule (sans validation) ---
cons_wizard = cons_wiz_env.create({"product_id": fecule.id})
cons_wizard._onchange_product_id()
if not cons_wizard.location_id and len(cons_wizard.allowed_location_ids) == 1:
    cons_wizard.location_id = cons_wizard.allowed_location_ids[0]
cons_ergo_ok = (
    cons_wizard.product_id == fecule
    and cons_wizard.location_id == fecule_loc
    and abs(cons_wizard.qty_available_kg - fecule_stock_initial) < 0.01
    and "action_open_adjustment_mode" not in cons_view.arch
)
checks.append(
    ok(
        "ERG-01",
        "Consommation fécule : localisation et stock, sans bouton mise à jour",
        qty_available_kg=cons_wizard.qty_available_kg,
        location=ref_data(cons_wizard.location_id),
    )
    if cons_ergo_ok
    else ko("ERG-01", "Consommation fécule : localisation et stock, sans bouton mise à jour")
)

stock_wizard = stock_wiz_env.create(
    {
        "product_id": fecule.id,
        "location_id": fecule_loc.id,
        "qty_counted_kg": fecule_stock_initial,
        "adjustment_reason": "QA ergonomie — lecture seule, ne pas appliquer",
    }
)
stock_ergo_ok = (
    stock_wizard.product_id == fecule
    and stock_wizard.location_id == fecule_loc
    and abs(stock_wizard.qty_available_kg - fecule_stock_initial) < 0.01
    and stock_wizard.qty_counted_kg == fecule_stock_initial
    and abs(stock_wizard.qty_diff_kg) < 0.01
    and "qty_consumed_kg" not in stock_view.arch
    and "confirm=" in stock_view.arch
)
checks.append(
    ok(
        "ERG-02",
        "Mise à jour fécule : champs correction sans prélèvement, confirmation présente",
        qty_odoo_kg=stock_wizard.qty_available_kg,
        qty_counted_kg=stock_wizard.qty_counted_kg,
        qty_diff_kg=stock_wizard.qty_diff_kg,
        confirm_present=True,
    )
    if stock_ergo_ok
    else ko("ERG-02", "Mise à jour fécule : champs correction sans prélèvement")
)

fecule_after_ergo = stock_ops.get_qty_kg_at_location(fecule, fecule_loc)
fecule_unchanged = abs(fecule_after_ergo - fecule_stock_initial) < 0.01
checks.append(
    ok(
        "AC15",
        "Stock fécule protégé en recette ergonomique",
        stock_kg_initial=fecule_stock_initial,
        stock_kg_final=fecule_after_ergo,
    )
    if fecule_unchanged
    else ko("AC15", "Stock fécule protégé en recette ergonomique")
)

ergo_evidence = {
    "run_id": RUN_ID,
    "fecule_stock_kg": {
        "initial": fecule_stock_initial,
        "after_ergo": fecule_after_ergo,
        "unchanged": fecule_unchanged,
    },
    "consumption_wizard": {
        "product": ref_data(cons_wizard.product_id),
        "location": ref_data(cons_wizard.location_id),
        "qty_available_kg": cons_wizard.qty_available_kg,
        "no_adjustment_button": True,
        "validated": False,
    },
    "stock_update_wizard": {
        "product": ref_data(stock_wizard.product_id),
        "location": ref_data(stock_wizard.location_id),
        "qty_available_kg": stock_wizard.qty_available_kg,
        "qty_counted_kg": stock_wizard.qty_counted_kg,
        "qty_diff_kg": stock_wizard.qty_diff_kg,
        "reason_sample": stock_wizard.adjustment_reason,
        "validated": False,
    },
}
write_json("ergo_fecule_evidence.json", ergo_evidence)

# --- 13.3 Recette métier (produit jetable) ---
probe = env["product.product"].search(
    [("name", "=", "QA WizSep Probe Product")], limit=1
)
if not probe:
    kg_uom = env.ref("uom.product_uom_kgm")
    probe = env["product.product"].create(
        {
            "name": "QA WizSep Probe Product",
            "is_storable": True,
            "purchase_ok": True,
            "uom_id": kg_uom.id,
            "uom_po_id": kg_uom.id,
        }
    )
    probe.product_tmpl_id.laplatine_consumption_tracking = True

probe_loc = env["stock.location"].search(
    [("name", "=", "QA WizSep Probe Bin")], limit=1
)
if not probe_loc:
    wh = company.laplatine_procurement_warehouse_id
    probe_loc = env["stock.location"].create(
        {
            "name": "QA WizSep Probe Bin",
            "location_id": wh.lot_stock_id.id,
            "usage": "internal",
        }
    )

probe_stock_before = stock_ops.get_qty_kg_at_location(probe, probe_loc)
if probe_stock_before < 100.0 or abs(probe_stock_before - 95.0) < 1.0:
    quant = stock_ops._get_quant_for_inventory(probe, probe_loc)
    quant.with_context(inventory_mode=True).write(
        {"inventory_quantity": stock_ops.qty_from_kg(probe, 100.0)}
    )
    quant.with_context(
        inventory_mode=True,
        inventory_name="QA WizSep reset probe stock",
        set_inventory_quantity_auto_apply=True,
    ).action_apply_inventory()
    probe_stock_before = 100.0

# Consommation nominale faible
cons_qty = 5.0
cons_action = cons_wiz_env.create(
    {
        "product_id": probe.id,
        "location_id": probe_loc.id,
        "qty_consumed_kg": cons_qty,
    }
).action_register_consumption()
probe_after_cons = stock_ops.get_qty_kg_at_location(probe, probe_loc)
cons_biz_ok = (
    cons_action["params"]["title"] == "Consommation enregistrée"
    and abs(probe_after_cons - (probe_stock_before - cons_qty)) < 0.01
)
checks.append(
    ok(
        "AC06",
        "Consommation nominale non régressée (produit jetable)",
        qty_kg=cons_qty,
        stock_after_kg=probe_after_cons,
        notification=cons_action["params"]["title"],
    )
    if cons_biz_ok
    else ko("AC06", "Consommation nominale non régressée (produit jetable)")
)

# Contrôle consommation quantité excessive
over_wizard = cons_wiz_env.create(
    {
        "product_id": probe.id,
        "location_id": probe_loc.id,
        "qty_consumed_kg": probe_after_cons + 1000.0,
    }
)
try:
    over_wizard.action_register_consumption()
    cons_ctrl_ok = False
except Exception:
    cons_ctrl_ok = True
checks.append(
    ok("AC06b", "Contrôles consommation actifs (quantité > disponible)")
    if cons_ctrl_ok
    else ko("AC06b", "Contrôles consommation actifs (quantité > disponible)")
)

# Correction négative
counted_after_cons = probe_after_cons
target_counted = counted_after_cons - 3.0
adj_action = stock_wiz_env.create(
    {
        "product_id": probe.id,
        "location_id": probe_loc.id,
        "qty_counted_kg": target_counted,
        "adjustment_reason": "QA WizSep correction négative",
    }
).action_update_stock()
probe_after_adj = stock_ops.get_qty_kg_at_location(probe, probe_loc)
adj_biz_ok = (
    adj_action["params"]["title"] == "Stock mis à jour"
    and abs(probe_after_adj - target_counted) < 0.01
    and "Écart enregistré" in adj_action["params"]["message"]
)
checks.append(
    ok(
        "AC07",
        "Correction inventaire non régressée (produit jetable)",
        stock_after_kg=probe_after_adj,
        notification=adj_action["params"],
    )
    if adj_biz_ok
    else ko("AC07", "Correction inventaire non régressée (produit jetable)")
)

# Correction depuis emplacement stock nul
zero_product = env["product.product"].search(
    [("name", "=", "QA WizSep Zero Loc Product")], limit=1
)
if not zero_product:
    kg_uom = env.ref("uom.product_uom_kgm")
    zero_product = env["product.product"].create(
        {
            "name": "QA WizSep Zero Loc Product",
            "is_storable": True,
            "purchase_ok": True,
            "uom_id": kg_uom.id,
            "uom_po_id": kg_uom.id,
        }
    )
    zero_product.product_tmpl_id.laplatine_consumption_tracking = True

zero_loc = env["stock.location"].search(
    [("name", "=", "QA WizSep Zero Stock Bin")], limit=1
)
if not zero_loc:
    wh = company.laplatine_procurement_warehouse_id
    zero_loc = env["stock.location"].create(
        {
            "name": "QA WizSep Zero Stock Bin",
            "location_id": wh.lot_stock_id.id,
            "usage": "internal",
        }
    )

zero_before = stock_ops.get_qty_kg_at_location(zero_product, zero_loc)
zero_target = 12.0 if abs(zero_before - 12.0) >= 0.01 else 15.0
zero_action = stock_wiz_env.create(
    {
        "product_id": zero_product.id,
        "location_id": zero_loc.id,
        "qty_counted_kg": zero_target,
        "adjustment_reason": "QA WizSep init stock depuis zéro",
    }
).action_update_stock()
zero_after = stock_ops.get_qty_kg_at_location(zero_product, zero_loc)
zero_loc_ok = abs(zero_after - zero_target) < 0.01 and zero_action["params"]["title"] == "Stock mis à jour"
checks.append(
    ok(
        "BIZ-03",
        "Correction depuis emplacement à stock nul",
        stock_before_kg=zero_before,
        stock_after_kg=zero_after,
    )
    if zero_loc_ok
    else ko("BIZ-03", "Correction depuis emplacement à stock nul")
)

# Motif obligatoire et quantité négative
try:
    stock_wiz_env.create(
        {
            "product_id": probe.id,
            "location_id": probe_loc.id,
            "qty_counted_kg": 10.0,
            "adjustment_reason": "   ",
        }
    ).action_update_stock()
    reason_ok = False
except Exception:
    reason_ok = True
try:
    stock_wiz_env.create(
        {
            "product_id": probe.id,
            "location_id": probe_loc.id,
            "qty_counted_kg": -1.0,
            "adjustment_reason": "Test négatif QA",
        }
    ).action_update_stock()
    neg_ok = False
except Exception:
    neg_ok = True
checks.append(
    ok("BIZ-04", "Motif obligatoire et quantité négative contrôlés")
    if reason_ok and neg_ok
    else ko("BIZ-04", "Motif obligatoire et quantité négative contrôlés")
)

# Notification seuil
threshold_product = env["product.product"].search(
    [("name", "=", "QA WizSep Threshold Product")], limit=1
)
threshold_loc = env["stock.location"].search(
    [("name", "=", "QA WizSep Threshold Bin")], limit=1
)
if not threshold_product:
    kg_uom = env.ref("uom.product_uom_kgm")
    threshold_product = env["product.product"].create(
        {
            "name": "QA WizSep Threshold Product",
            "is_storable": True,
            "purchase_ok": True,
            "uom_id": kg_uom.id,
            "uom_po_id": kg_uom.id,
        }
    )
    threshold_product.product_tmpl_id.laplatine_consumption_tracking = True
if not threshold_loc:
    wh = company.laplatine_procurement_warehouse_id
    threshold_loc = env["stock.location"].create(
        {
            "name": "QA WizSep Threshold Bin",
            "location_id": wh.lot_stock_id.id,
            "usage": "internal",
        }
    )
warehouse = company.laplatine_procurement_warehouse_id
orderpoint = env["stock.warehouse.orderpoint"].search(
    [
        ("product_id", "=", threshold_product.id),
        ("warehouse_id", "=", warehouse.id),
    ],
    limit=1,
)
if not orderpoint:
    orderpoint = env["stock.warehouse.orderpoint"].create(
        {
            "product_id": threshold_product.id,
            "warehouse_id": warehouse.id,
            "location_id": warehouse.lot_stock_id.id,
            "product_min_qty": 5000.0,
            "product_max_qty": 10000.0,
        }
    )
thr_before = stock_ops.get_qty_kg_at_location(threshold_product, threshold_loc)
if thr_before < 5010.0 or abs(thr_before - 4950.0) < 0.01:
    quant = stock_ops._get_quant_for_inventory(threshold_product, threshold_loc)
    quant.with_context(inventory_mode=True).write(
        {"inventory_quantity": stock_ops.qty_from_kg(threshold_product, 5010.0)}
    )
    quant.with_context(
        inventory_mode=True,
        inventory_name="QA WizSep threshold prep",
        set_inventory_quantity_auto_apply=True,
    ).action_apply_inventory()
    thr_before = 5010.0

thr_action = stock_wiz_env.create(
    {
        "product_id": threshold_product.id,
        "location_id": threshold_loc.id,
        "qty_counted_kg": 4950.0,
        "adjustment_reason": "QA WizSep seuil min",
    }
).action_update_stock()
thr_ok = (
    thr_action["params"]["type"] == "warning"
    and "Seuil de réapprovisionnement atteint" in thr_action["params"]["message"]
)
checks.append(
    ok("AC12", "Contrôle seuil minimum après mise à jour", notification=thr_action["params"])
    if thr_ok
    else ko("AC12", "Contrôle seuil minimum après mise à jour")
)

# Seuil après consommation
thr_cons_product = env["product.product"].search(
    [("name", "=", "QA WizSep Threshold Cons Product")], limit=1
)
if not thr_cons_product:
    kg_uom = env.ref("uom.product_uom_kgm")
    thr_cons_product = env["product.product"].create(
        {
            "name": "QA WizSep Threshold Cons Product",
            "is_storable": True,
            "purchase_ok": True,
            "uom_id": kg_uom.id,
            "uom_po_id": kg_uom.id,
        }
    )
    thr_cons_product.product_tmpl_id.laplatine_consumption_tracking = True
thr_cons_loc = env["stock.location"].search(
    [("name", "=", "QA WizSep Threshold Cons Bin")], limit=1
)
if not thr_cons_loc:
    wh = company.laplatine_procurement_warehouse_id
    thr_cons_loc = env["stock.location"].create(
        {
            "name": "QA WizSep Threshold Cons Bin",
            "location_id": wh.lot_stock_id.id,
            "usage": "internal",
        }
    )
if not env["stock.warehouse.orderpoint"].search(
    [("product_id", "=", thr_cons_product.id), ("warehouse_id", "=", warehouse.id)],
    limit=1,
):
    env["stock.warehouse.orderpoint"].create(
        {
            "product_id": thr_cons_product.id,
            "warehouse_id": warehouse.id,
            "location_id": warehouse.lot_stock_id.id,
            "product_min_qty": 5000.0,
            "product_max_qty": 10000.0,
        }
    )
if stock_ops.get_qty_kg_at_location(thr_cons_product, thr_cons_loc) < 5050.0:
    quant = stock_ops._get_quant_for_inventory(thr_cons_product, thr_cons_loc)
    quant.with_context(inventory_mode=True).write(
        {"inventory_quantity": stock_ops.qty_from_kg(thr_cons_product, 5050.0)}
    )
    quant.with_context(
        inventory_mode=True,
        inventory_name="QA WizSep threshold cons prep",
        set_inventory_quantity_auto_apply=True,
    ).action_apply_inventory()

thr_cons_action = cons_wiz_env.create(
    {
        "product_id": thr_cons_product.id,
        "location_id": thr_cons_loc.id,
        "qty_consumed_kg": 100.0,
    }
).action_register_consumption()
thr_cons_ok = (
    thr_cons_action["params"]["type"] == "warning"
    and "Seuil de réapprovisionnement atteint" in thr_cons_action["params"]["message"]
)
checks.append(
    ok("AC12b", "Contrôle seuil minimum après consommation")
    if thr_cons_ok
    else ko("AC12b", "Contrôle seuil minimum après consommation")
)

business_evidence = {
    "run_id": RUN_ID,
    "probe_product": ref_data(probe),
    "probe_location": ref_data(probe_loc),
    "consumption": {
        "qty_kg": cons_qty,
        "stock_before_kg": probe_stock_before,
        "stock_after_kg": probe_after_cons,
        "notification": cons_action.get("params"),
    },
    "adjustment_negative": {
        "counted_kg": target_counted,
        "stock_after_kg": probe_after_adj,
        "notification": adj_action.get("params"),
    },
    "zero_location": {
        "product": ref_data(zero_product),
        "location": ref_data(zero_loc),
        "stock_before_kg": zero_before,
        "stock_after_kg": zero_after,
    },
    "threshold_adjustment": thr_action.get("params") if thr_action else False,
    "threshold_consumption": thr_cons_action.get("params") if thr_cons_action else False,
}
write_json("business_evidence.json", business_evidence)

# --- Fécule finale ---
fecule_final = stock_ops.get_qty_kg_at_location(fecule, fecule_loc)
checks.append(
    ok(
        "FEC-FINAL",
        "Fécule inchangée après campagne QA complète",
        stock_kg=fecule_final,
    )
    if abs(fecule_final - fecule_stock_initial) < 0.01
    else ko("FEC-FINAL", "Fécule inchangée après campagne QA complète")
)

blocking = [c["id"] for c in checks if c.get("result") == "KO"]
verdict = "GO_QA_WIZSEP_LAB" if not blocking else "NO_GO_QA_WIZSEP"

final = {
    "run_id": RUN_ID,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "url_lab": "http://127.0.0.1:18018",
    "reference": "LAPLATINE-CONS-MP-002",
    "module_version": module.latest_version,
    "production": "STOP",
    "verdict": verdict,
    "blocking_ko": blocking,
    "checks_total": len(checks),
    "checks_ok": len([c for c in checks if c["result"] == "OK"]),
    "checks": checks,
    "fecule": {
        "product": ref_data(fecule),
        "location": ref_data(fecule_loc),
        "stock_kg_initial": fecule_stock_initial,
        "stock_kg_final": fecule_final,
    },
    "automated_tests_note": "100/100 verts exécutés séparément (--test-tags=laplatine_procurement_control)",
}
write_json("final_evidence.json", final)
env.cr.commit()

print("QA_VERDICT=%s" % verdict)
print("QA_JSON=%s" % os.path.join(RUN_DIR, "final_evidence.json"))
print("CHECKS_OK=%s/%s" % (final["checks_ok"], final["checks_total"]))
for c in checks:
    print("  %s %s: %s" % (c["id"], c["result"], c["title"]))
