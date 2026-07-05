# -*- coding: utf-8 -*-
import json


actions = env["ir.actions.act_window"].search(
    [("res_model", "=", "stock.move")],
    order="id",
)
payload = []
for action in actions:
    xmlid = action.get_external_id().get(action.id)
    payload.append(
        {
            "id": action.id,
            "name": action.name,
            "xmlid": xmlid,
            "view_mode": action.view_mode,
            "domain": action.domain,
        }
    )

print(json.dumps(payload, ensure_ascii=False, indent=2))
