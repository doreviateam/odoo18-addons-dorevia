# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


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
    warehouse_id = fields.Many2one("stock.warehouse", string="Entrepôt", readonly=True)
    supplier_id = fields.Many2one("res.partner", string="Fournisseur", readonly=True)
    orderpoint_id = fields.Many2one(
        "stock.warehouse.orderpoint",
        string="Règle de réapprovisionnement",
        readonly=True,
    )
    purchase_order_id = fields.Many2one(
        "purchase.order",
        string="Commande fournisseur",
        readonly=True,
    )
    picking_id = fields.Many2one(
        "stock.picking",
        string="Réception attendue",
        readonly=True,
    )
    criticality = fields.Selection(
        related="product_id.product_tmpl_id.laplatine_procurement_criticality",
        string="Criticité métier",
        readonly=True,
    )
    qty_available = fields.Float(string="Stock disponible", readonly=True)
    virtual_available = fields.Float(string="Stock prévisionnel", readonly=True)
    daily_consumption = fields.Float(string="Conso moyenne / jour", readonly=True)
    coverage_days = fields.Float(string="Couverture (j)", readonly=True)
    consumption_period_days = fields.Integer(string="Période conso (j)", readonly=True)
    min_qty = fields.Float(string="Minimum réappro", readonly=True)
    max_qty = fields.Float(string="Maximum réappro", readonly=True)
    confirmed_po_qty = fields.Float(string="Qté en commande", readonly=True)
    next_reception_qty = fields.Float(string="Qté prochaine réception", readonly=True)
    supplier_delay = fields.Integer(string="Délai fournisseur (j)", readonly=True)
    stock_break_date = fields.Date(string="Rupture physique estimée", readonly=True)
    min_reach_date = fields.Date(string="Atteinte minimum estimée", readonly=True)
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
    alert_ids = fields.Many2many(
        "laplatine.procurement.alert.type",
        "laplatine_proc_alert_line_rel",
        "line_id",
        "alert_type_id",
        string="Alertes",
        readonly=True,
    )
    alert_codes = fields.Char(string="Codes alertes", readonly=True, index=True)
    last_refresh = fields.Datetime(string="Dernière actualisation", readonly=True)
    refreshed_by_id = fields.Many2one(
        "res.users",
        string="Actualisé par",
        readonly=True,
    )
    is_data_stale = fields.Boolean(
        string="Données obsolètes",
        compute="_compute_data_freshness",
        store=True,
    )
    stale_warning_message = fields.Char(
        string="Avertissement fraîcheur",
        compute="_compute_data_freshness",
    )

    _sql_constraints = [
        (
            "product_company_uniq",
            "unique(product_id, company_id)",
            "Une seule ligne cockpit par article et par société.",
        ),
    ]

    @api.depends("last_refresh", "company_id.laplatine_procurement_stale_warning_hours")
    def _compute_data_freshness(self):
        now = fields.Datetime.now()
        for line in self:
            hours = line.company_id.laplatine_procurement_stale_warning_hours or 24
            if not line.last_refresh:
                line.is_data_stale = True
                line.stale_warning_message = (
                    "Cockpit jamais actualisé — lancer Actualiser."
                )
                continue
            age = now - line.last_refresh
            line.is_data_stale = age > timedelta(hours=hours)
            if line.is_data_stale:
                line.stale_warning_message = (
                    "Données actualisées il y a plus de %s h — lancer Actualiser."
                    % hours
                )
            else:
                line.stale_warning_message = False

    def action_refresh(self):
        if not self.env.user.has_group(
            "laplatine_procurement_control.group_procurement_control_manager"
        ):
            raise AccessError(
                "Seuls les utilisateurs autorisés au pilotage approvisionnements "
                "peuvent actualiser le cockpit."
            )
        company = self.env.company
        indicators = self.env["laplatine.procurement.indicators"]
        products = indicators.get_eligible_products(company)
        now = fields.Datetime.now()
        refreshed_ids = []

        for product in products:
            evaluation = indicators.evaluate_product(product, company)
            vals = dict(evaluation["line_values"])
            vals.update(
                {
                    "last_refresh": now,
                    "refreshed_by_id": self.env.user.id,
                }
            )
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

    def _action_open_record(self, model, res_id):
        self.ensure_one()
        if not res_id:
            raise UserError("Aucun enregistrement associé à ouvrir.")
        record = self.env[model].browse(res_id)
        record.check_access("read")
        return {
            "type": "ir.actions.act_window",
            "name": record.display_name,
            "res_model": model,
            "res_id": res_id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_product(self):
        self.ensure_one()
        return self._action_open_record("product.product", self.product_id.id)

    def action_open_supplier(self):
        self.ensure_one()
        return self._action_open_record("res.partner", self.supplier_id.id)

    def action_open_orderpoint(self):
        self.ensure_one()
        return self._action_open_record(
            "stock.warehouse.orderpoint", self.orderpoint_id.id
        )

    def action_open_purchase_order(self):
        self.ensure_one()
        return self._action_open_record("purchase.order", self.purchase_order_id.id)

    def action_open_picking(self):
        self.ensure_one()
        return self._action_open_record("stock.picking", self.picking_id.id)
