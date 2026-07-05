# -*- coding: utf-8 -*-
from odoo import fields, models


class LaplatineProcurementAlertType(models.Model):
    _name = "laplatine.procurement.alert.type"
    _description = "Type d'alerte cockpit approvisionnements"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        (
            "code_unique",
            "unique(code)",
            "Le code d'alerte doit être unique.",
        ),
    ]
