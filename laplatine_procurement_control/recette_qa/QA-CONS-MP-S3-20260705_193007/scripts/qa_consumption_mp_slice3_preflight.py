# -*- coding: utf-8 -*-
import json
from datetime import datetime


RUN_ID = "QA-CONS-MP-S3-20260705_193007"
OUTPUT = "/tmp/QA-CONS-MP-S3-20260705_193007_preflight.json"
OPERATOR_LOGIN = "qa_cons_mp_s3_operator_20260705_193007"
OPERATOR_PASSWORD = "S3Qa!2026"


def ref_data(record):
    if not record:
        return False
    return {
        "model": record._name,
        "id": record.id,
        "display_name": record.display_name,
    }


company = env.company
module = env["ir.module.module"].search(
    [("name", "=", "laplatine_procurement_control")], limit=1
)
stock_ops = env["laplatine.procurement.stock.ops"]
product = env["product.product"].search(
    [("default_code", "=", "MP-FEC-MAN-001")], limit=1
)
if not product:
    product = env["product.product"].search(
        [("display_name", "ilike", "FECULE DE MANIOC")], limit=1
    )

consumption_group = env.ref(
    "laplatine_procurement_control.group_raw_material_consumption_user"
)
base_group = env.ref("base.group_user")
operator = env["res.users"].search([("login", "=", OPERATOR_LOGIN)], limit=1)
operator_values = {
    "name": "QA CONS MP S3 Opérateur",
    "login": OPERATOR_LOGIN,
    "groups_id": [(6, 0, [base_group.id, consumption_group.id])],
}
if operator:
    operator.write(operator_values)
else:
    operator = env["res.users"].create(operator_values)
operator.write({"password": OPERATOR_PASSWORD})
group_external_ids = operator.groups_id.get_external_id()

stock_locations = []
source_location = env["stock.location"]
if product:
    for location in stock_ops.get_pilot_internal_locations(company):
        qty = stock_ops.get_qty_at_location(product, location)
        qty_kg = stock_ops.qty_to_kg(product, qty)
        item = {
            "location": ref_data(location),
            "complete_name": location.complete_name,
            "usage": location.usage,
            "quantity": qty,
            "quantity_kg": qty_kg,
        }
        stock_locations.append(item)
        if qty_kg > 0 and "Conteneur Fécule" in location.complete_name:
            source_location = location

latest_move = env["stock.move"].search(
    [
        ("product_id", "=", product.id if product else 0),
        ("reference", "=", "Consommation MP La Platine"),
    ],
    order="id desc",
    limit=1,
)

payload = {
    "run_id": RUN_ID,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "production": "STOP - lab uniquement",
    "git_reference": {
        "head_short": "5655b9c",
        "slice3_code_committed": False,
    },
    "module": {
        "installed_version": module.installed_version,
        "latest_version": module.latest_version,
        "state": module.state,
    },
    "operator": {
        "login": OPERATOR_LOGIN,
        "password": OPERATOR_PASSWORD,
        "groups": sorted(
            group_external_ids.get(group.id, group.display_name)
            for group in operator.groups_id
        ),
    },
    "company": {
        "company": ref_data(company),
        "warehouse": ref_data(company.laplatine_procurement_warehouse_id),
        "destination": ref_data(
            company.laplatine_consumption_destination_location_id
        ),
        "destination_usage": company.laplatine_consumption_destination_location_id.usage,
    },
    "fecule": {
        "product": ref_data(product),
        "default_code": product.default_code if product else False,
        "tracking_consumption": product.product_tmpl_id.laplatine_consumption_tracking
        if product
        else False,
        "uom": ref_data(product.uom_id) if product else False,
        "stock_locations": stock_locations,
        "source_location": ref_data(source_location),
        "source_qty_kg": stock_ops.get_qty_kg_at_location(product, source_location)
        if product and source_location
        else False,
    },
    "before": {
        "consumption_move_count": env["stock.move"].search_count(
            [
                ("product_id", "=", product.id if product else 0),
                ("reference", "=", "Consommation MP La Platine"),
            ]
        ),
        "latest_consumption_move": ref_data(latest_move),
        "latest_consumption_move_state": latest_move.state if latest_move else False,
    },
}

with open(OUTPUT, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=2)
    fh.write("\n")

env.cr.commit()
print("QA_CONS_MP_S3_PREFLIGHT_JSON=%s" % OUTPUT)
print("QA_CONS_MP_S3_OPERATOR=%s" % OPERATOR_LOGIN)
print("QA_CONS_MP_S3_PASSWORD=%s" % OPERATOR_PASSWORD)
