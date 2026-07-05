from odoo import fields, models


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

    def action_refresh(self):
        """Rafraîchissement explicite — logique métier à implémenter avec la matrice §12.3."""
        return True
