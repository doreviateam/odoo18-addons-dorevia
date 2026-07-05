# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime


OUTPUT = os.environ.get(
    "QA_OUTPUT",
    "/tmp/QA-CONS-MP-S3-20260705_193007_state.json",
)
LABEL = os.environ.get("QA_LABEL", "state")
REFERENCE = "Consommation MP La Platine"


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
source_location = env["stock.location"].search(
    [("complete_name", "=", "WH/Stock/Conteneur Fécule")], limit=1
)
moves = env["stock.move"].search(
    [
        ("product_id", "=", product.id if product else 0),
        ("reference", "=", REFERENCE),
    ],
    order="id desc",
)
latest_move = moves[:1]

move_payload = False
if latest_move:
    move_payload = {
        "move": ref_data(latest_move),
        "state": latest_move.state,
        "name": latest_move.name,
        "reference": latest_move.reference,
        "product": ref_data(latest_move.product_id),
        "product_uom_qty": latest_move.product_uom_qty,
        "quantity": latest_move.quantity,
        "product_uom": ref_data(latest_move.product_uom),
        "source": ref_data(latest_move.location_id),
        "destination": ref_data(latest_move.location_dest_id),
        "create_uid": ref_data(latest_move.create_uid),
        "date": latest_move.date.isoformat() if latest_move.date else False,
        "move_lines": [
            {
                "line": ref_data(line),
                "quantity": line.quantity,
                "product_uom": ref_data(line.product_uom_id),
                "source": ref_data(line.location_id),
                "destination": ref_data(line.location_dest_id),
            }
            for line in latest_move.move_line_ids
        ],
    }

payload = {
    "run_id": "QA-CONS-MP-S3-20260705_193007",
    "label": LABEL,
    "generated_at": datetime.utcnow().isoformat(),
    "database": env.cr.dbname,
    "production": "STOP - lab uniquement",
    "module": {
        "installed_version": module.installed_version,
        "latest_version": module.latest_version,
        "state": module.state,
    },
    "company": ref_data(company),
    "product": ref_data(product),
    "source_location": ref_data(source_location),
    "source_qty_kg": stock_ops.get_qty_kg_at_location(product, source_location)
    if product and source_location
    else False,
    "destination": ref_data(company.laplatine_consumption_destination_location_id),
    "destination_usage": company.laplatine_consumption_destination_location_id.usage,
    "consumption_move_count": len(moves),
    "latest_consumption_move": move_payload,
}

with open(OUTPUT, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=2)
    fh.write("\n")

print("QA_CONS_MP_S3_STATE_JSON=%s" % OUTPUT)
