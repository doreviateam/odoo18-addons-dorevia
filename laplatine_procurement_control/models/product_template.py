from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    laplatine_procurement_criticality = fields.Selection(
        selection=[
            ("normal", "Normale"),
            ("high", "Élevée"),
            ("critical", "Critique"),
        ],
        string="Criticité approvisionnement",
        default="normal",
    )
    laplatine_procurement_consumption_untraceable = fields.Boolean(
        string="Consommation non traçable",
        help="Indique manuellement que la consommation ne peut pas être calculée "
        "de façon fiable à partir des mouvements de stock.",
    )
    laplatine_consumption_tracking = fields.Boolean(
        string="Suivi consommation La Platine",
        help="Rend cet article disponible dans l'interface simplifiée "
        "de consommation des matières premières de La Platine.",
    )
