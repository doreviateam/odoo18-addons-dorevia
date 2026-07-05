from odoo import api, fields, models


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
    laplatine_consumption_destination_location_id = fields.Many2one(
        "stock.location",
        string="Emplacement destination consommations La Platine",
        domain="[('usage', '=', 'production'), '|', ('company_id', '=', False), ('company_id', '=', id)]",
        default=lambda self: self._default_laplatine_consumption_destination_location_id(),
        help="Emplacement de production cible pour les prélèvements "
        "enregistrés via le wizard Consommation matière première.",
    )

    @api.model
    def _default_laplatine_consumption_destination_location_id(self):
        return self.env["stock.location"].search(
            [
                ("usage", "=", "production"),
                "|",
                ("company_id", "=", self.env.company.id),
                ("company_id", "=", False),
            ],
            limit=1,
        ).id
