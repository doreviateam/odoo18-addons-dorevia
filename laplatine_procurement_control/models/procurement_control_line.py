# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LaplatineProcurementControlLine(models.Model):
    _name = "laplatine.procurement.control.line"
    _description = "Ligne cockpit pilotage approvisionnements"
    _order = "risk_status desc, product_id"

    product_id = fields.Many2one(
        "product.product",
        string="Article",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Société",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    qty_available = fields.Float(string="Stock disponible", readonly=True)
    daily_consumption = fields.Float(string="Conso moyenne / jour", readonly=True)
    min_qty = fields.Float(string="Minimum réappro", readonly=True)
    order_deadline_date = fields.Date(string="Date limite commande", readonly=True)
    next_reception_date = fields.Date(string="Prochaine réception", readonly=True)
    risk_status = fields.Selection(
        selection=[
            ("insufficient_data", "Données insuffisantes"),
            ("normal", "Normal"),
            ("watch", "À surveiller"),
            ("action_required", "Action requise"),
            ("critical", "Critique"),
            ("stockout", "Rupture"),
        ],
        string="Statut de risque",
        readonly=True,
    )
    risk_reason = fields.Char(string="Motif du statut", readonly=True)
    action_recommended = fields.Char(string="Action recommandée", readonly=True)
    last_refresh = fields.Datetime(string="Dernière actualisation", readonly=True)
    refreshed_by_id = fields.Many2one(
        "res.users",
        string="Actualisé par",
        readonly=True,
    )

    _sql_constraints = [
        (
            "product_company_uniq",
            "unique(product_id, company_id)",
            "Une seule ligne cockpit par article et par société.",
        ),
    ]

    @api.model
    def action_refresh(self):
        company = self.env.company
        indicators = self.env["laplatine.procurement.indicators"]
        products = indicators.get_eligible_products(company)
        now = fields.Datetime.now()
        refreshed_ids = []

        for product in products:
            evaluation = indicators.evaluate_product(product, company)
            risk_input = evaluation["risk_input"]
            vals = {
                "product_id": product.id,
                "company_id": company.id,
                "qty_available": risk_input.qty_available,
                "daily_consumption": risk_input.daily_consumption,
                "min_qty": risk_input.min_qty if risk_input.min_qty_exploitable else 0.0,
                "order_deadline_date": risk_input.order_deadline_date,
                "next_reception_date": risk_input.next_reception_date,
                "risk_status": evaluation["risk_status"],
                "risk_reason": evaluation["risk_reason"],
                "action_recommended": evaluation["action_recommended"],
                "last_refresh": now,
                "refreshed_by_id": self.env.user.id,
            }
            line = self.search(
                [
                    ("product_id", "=", product.id),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )
            if line:
                line.write(vals)
                refreshed_ids.append(line.id)
            else:
                refreshed_ids.append(self.create(vals).id)

        obsolete_lines = self.search(
            [
                ("company_id", "=", company.id),
                ("id", "not in", refreshed_ids),
            ]
        )
        obsolete_lines.unlink()
        return True
