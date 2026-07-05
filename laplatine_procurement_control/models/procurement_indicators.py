# -*- coding: utf-8 -*-
from datetime import timedelta
from math import ceil

from odoo import api, fields, models

from .risk_matrix import ProcurementRiskInput, compute_procurement_risk


class LaplatineProcurementIndicators(models.AbstractModel):
    _name = "laplatine.procurement.indicators"
    _description = "Collecte des indicateurs cockpit approvisionnements"

    @api.model
    def get_eligible_products(self, company):
        return self.env["product.product"].search(
            [
                ("active", "=", True),
                ("purchase_ok", "=", True),
                ("is_storable", "=", True),
            ]
        )

    @api.model
    def get_pilot_warehouse(self, company):
        return company.laplatine_procurement_warehouse_id

    @api.model
    def build_risk_input(self, product, company, today=None):
        today = today or fields.Date.context_today(self)
        warehouse = self.get_pilot_warehouse(company)
        params = self._company_params(company)

        if not warehouse:
            return ProcurementRiskInput(
                today=today,
                watch_lead_days=params["watch_lead_days"],
                qty_available=0.0,
                daily_consumption=0.0,
                warehouse_configured=False,
            )

        qty_available = self._get_qty_available(product, warehouse)
        consumption = self._compute_consumption(product, warehouse, company, today, params)
        orderpoint = self._get_orderpoint(product, warehouse)
        supplier_delay = self._get_supplier_delay(product, company, today)
        reception = self._get_next_reception(product, company)

        min_qty_exploitable = bool(orderpoint and orderpoint.product_min_qty > 0)
        min_qty = orderpoint.product_min_qty if min_qty_exploitable else 0.0
        daily_consumption = consumption["daily_consumption"]

        stock_break_date = None
        order_deadline_date = None
        projected_qty_at_reception = None

        if daily_consumption > 0:
            stock_break_date = self._project_stock_break_date(
                today, qty_available, daily_consumption
            )
            if min_qty_exploitable and supplier_delay is not None:
                min_reach_date = self._project_min_reach_date(
                    today, qty_available, min_qty, daily_consumption
                )
                order_deadline_date = min_reach_date - timedelta(days=supplier_delay)

            if reception.get("date"):
                days_to_reception = (reception["date"] - today).days
                projected_qty_at_reception = qty_available - (
                    days_to_reception * daily_consumption
                )

        return ProcurementRiskInput(
            today=today,
            watch_lead_days=params["watch_lead_days"],
            qty_available=qty_available,
            daily_consumption=daily_consumption,
            history_insufficient=consumption["history_insufficient"],
            warehouse_configured=True,
            essential_data_missing=not bool(product.uom_id),
            min_qty_exploitable=min_qty_exploitable,
            min_qty=min_qty,
            stock_break_date=stock_break_date,
            order_deadline_date=order_deadline_date,
            next_reception_date=reception.get("date"),
            projected_qty_at_reception=projected_qty_at_reception,
        )

    @api.model
    def evaluate_product(self, product, company, today=None):
        risk_input = self.build_risk_input(product, company, today=today)
        result = compute_procurement_risk(risk_input)
        return {
            "risk_input": risk_input,
            "risk_status": result["risk_status"],
            "risk_reason": result["risk_reason"],
            "action_recommended": result["action_recommended"],
        }

    @api.model
    def _company_params(self, company):
        return {
            "consumption_days": company.laplatine_procurement_consumption_days or 90,
            "min_history_days": company.laplatine_procurement_min_history_days or 30,
            "watch_lead_days": company.laplatine_procurement_watch_lead_days or 7,
        }

    @api.model
    def _get_qty_available(self, product, warehouse):
        return product.with_context(warehouse=warehouse.id).qty_available

    @api.model
    def _get_internal_location_ids(self, warehouse):
        return self.env["stock.location"].search(
            [
                ("id", "child_of", warehouse.view_location_id.id),
                ("usage", "=", "internal"),
            ]
        ).ids

    @api.model
    def _get_consumption_destination_ids(self):
        return self.env["stock.location"].search(
            [("usage", "in", ("production", "customer"))]
        ).ids

    @api.model
    def _compute_consumption(self, product, warehouse, company, today, params):
        consumption_days = params["consumption_days"]
        min_history_days = params["min_history_days"]
        period_start = today - timedelta(days=consumption_days)
        internal_ids = self._get_internal_location_ids(warehouse)
        destination_ids = self._get_consumption_destination_ids()

        if not internal_ids or not destination_ids:
            return {"daily_consumption": 0.0, "history_insufficient": True}

        move_domain_base = [
            ("product_id", "=", product.id),
            ("state", "=", "done"),
            ("date", ">=", fields.Datetime.to_datetime(period_start)),
            ("date", "<=", fields.Datetime.to_datetime(today) + timedelta(days=1)),
        ]
        outgoing = self.env["stock.move"].search(
            move_domain_base
            + [
                ("location_id", "in", internal_ids),
                ("location_dest_id", "in", destination_ids),
            ]
        )
        incoming = self.env["stock.move"].search(
            move_domain_base
            + [
                ("location_id", "in", destination_ids),
                ("location_dest_id", "in", internal_ids),
            ]
        )

        move_dates = (outgoing | incoming).mapped(
            lambda move: fields.Date.to_date(move.date)
        )
        if not move_dates:
            product_age_ok = (
                fields.Date.to_date(product.create_date) <= period_start
                if product.create_date
                else False
            )
            return {
                "daily_consumption": 0.0,
                "history_insufficient": not product_age_ok,
            }

        first_move_date = min(move_dates)
        history_insufficient = first_move_date > today - timedelta(days=min_history_days)
        if history_insufficient:
            return {"daily_consumption": 0.0, "history_insufficient": True}

        net_qty = sum(outgoing.mapped("product_uom_qty")) - sum(
            incoming.mapped("product_uom_qty")
        )
        daily_consumption = net_qty / consumption_days if consumption_days else 0.0
        if daily_consumption < 0:
            daily_consumption = 0.0
        return {
            "daily_consumption": daily_consumption,
            "history_insufficient": False,
        }

    @api.model
    def _get_orderpoint(self, product, warehouse):
        orderpoints = self.env["stock.warehouse.orderpoint"].search(
            [
                ("product_id", "=", product.id),
                ("warehouse_id", "=", warehouse.id),
                ("location_id", "=", warehouse.lot_stock_id.id),
            ]
        )
        if len(orderpoints) != 1:
            return False
        return orderpoints

    @api.model
    def _get_supplier_delay(self, product, company, today):
        seller = product._select_seller(
            partner_id=False,
            quantity=1.0,
            date=today,
            uom_id=product.uom_po_id,
            params={"company_id": company.id},
        )
        if not seller:
            return None
        return seller.delay or 0

    @api.model
    def _get_next_reception(self, product, company):
        lines = self.env["purchase.order.line"].search(
            [
                ("product_id", "=", product.id),
                ("order_id.state", "=", "purchase"),
                ("order_id.company_id", "=", company.id),
            ]
        ).filtered(lambda line: line.product_qty > line.qty_received)
        if not lines:
            return {"date": None, "qty": 0.0}

        receptions = []
        for line in lines:
            reception_date = self._get_reception_date(line)
            if not reception_date:
                continue
            remaining_qty = line.product_qty - line.qty_received
            if remaining_qty <= 0:
                continue
            receptions.append(
                {
                    "date": reception_date,
                    "qty": remaining_qty,
                }
            )

        if not receptions:
            return {"date": None, "qty": 0.0}

        closest = min(receptions, key=lambda item: item["date"])
        same_day_qty = sum(
            item["qty"] for item in receptions if item["date"] == closest["date"]
        )
        return {"date": closest["date"], "qty": same_day_qty}

    @api.model
    def _get_reception_date(self, po_line):
        moves = po_line.move_ids.filtered(
            lambda move: move.state not in ("done", "cancel")
            and move.picking_type_id.code == "incoming"
        )
        move_dates = [
            fields.Date.to_date(move.date)
            for move in moves
            if move.date
        ]
        if move_dates:
            return min(move_dates)
        if po_line.date_planned:
            return fields.Date.to_date(po_line.date_planned)
        return None

    @api.model
    def _project_stock_break_date(self, today, qty_available, daily_consumption):
        if daily_consumption <= 0:
            return None
        days = qty_available / daily_consumption
        return today + timedelta(days=ceil(days) if days > 0 else 0)

    @api.model
    def _project_min_reach_date(self, today, qty_available, min_qty, daily_consumption):
        if daily_consumption <= 0:
            return None
        days = max(0.0, (qty_available - min_qty) / daily_consumption)
        return today + timedelta(days=ceil(days) if days > 0 else 0)
