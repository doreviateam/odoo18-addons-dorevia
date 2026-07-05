from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    laplatine_procurement_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Entrepôt de pilotage approvisionnements",
        help="Entrepôt de référence pour le cockpit de pilotage.",
    )
    laplatine_procurement_consumption_days = fields.Integer(
        string="Période de consommation (jours)",
        default=90,
    )
    laplatine_procurement_min_history_days = fields.Integer(
        string="Historique minimum (jours)",
        default=30,
    )
    laplatine_procurement_watch_lead_days = fields.Integer(
        string="Marge « À surveiller » (jours)",
        default=7,
        help="Nombre de jours avant la date limite de commande déclenchant le statut « À surveiller ».",
    )
    laplatine_procurement_stale_warning_hours = fields.Integer(
        string="Avertissement données obsolètes (heures)",
        default=24,
    )
