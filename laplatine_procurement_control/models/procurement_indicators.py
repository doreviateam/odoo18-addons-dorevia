# -*- coding: utf-8 -*-
from datetime import timedelta
from math import ceil

from odoo import api, fields, models

from .alert_matrix import ProcurementAlertInput, compute_procurement_alerts
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
    def evaluate_product(self, product, company, today=None):
        today = today or fields.Date.context_today(self)
        warehouse = self.get_pilot_warehouse(company)
        params = self._company_params(company)
        snapshot = self._collect_snapshot(product, company, warehouse, today, params)
        risk_input = snapshot["risk_input"]
        risk_result = compute_procurement_risk(risk_input)
        alert_input = ProcurementAlertInput(
            risk_status=risk_result["risk_status"],
            orderpoint_status=snapshot["orderpoint_status"],
            supplier_missing=snapshot["supplier_missing"],
            history_insufficient=snapshot["history_insufficient"],
            zero_consumption_observed=snapshot["zero_consumption_observed"],
            consumption_untraceable=snapshot["consumption_untraceable"],
            confirmed_po_qty=snapshot["confirmed_po_qty"],
            reception_date=snapshot["next_reception_date"],
            today=today,
            has_open_reception=snapshot["has_open_reception"],
        )
        alert_codes = compute_procurement_alerts(alert_input)
        return {
            "risk_input": risk_input,
            "risk_status": risk_result["risk_status"],
            "risk_reason": risk_result["risk_reason"],
            "action_recommended": risk_result["action_recommended"],
            "alert_codes": alert_codes,
            "line_values": self._build_line_values(
                product, company, warehouse, snapshot, risk_result, alert_codes
            ),
        }

    @api.model
    def build_risk_input(self, product, company, today=None):
        return self.evaluate_product(product, company, today=today)["risk_input"]

    @api.model
    def _collect_snapshot(self, product, company, warehouse, today, params):
        if not warehouse:
            return {
                "risk_input": ProcurementRiskInput(
                    today=today,
                    watch_lead_days=params["watch_lead_days"],
                    qty_available=0.0,
                    daily_consumption=0.0,
                    warehouse_configured=False,
                ),
                "orderpoint_status": "missing",
                "supplier_missing": True,
                "history_insufficient": False,
                "zero_consumption_observed": False,
                "consumption_untraceable": bool(
                    product.product_tmpl_id.laplatine_procurement_consumption_untraceable
                ),
                "confirmed_po_qty": 0.0,
                "next_reception_date": None,
                "has_open_reception": False,
                "qty_available": 0.0,
                "virtual_available": 0.0,
                "daily_consumption": 0.0,
                "min_qty": 0.0,
                "max_qty": 0.0,
                "supplier_delay": None,
                "coverage_days": 0.0,
                "stock_break_date": None,
                "min_reach_date": None,
                "order_deadline_date": None,
                "next_reception_qty": 0.0,
                "supplier_id": False,
                "orderpoint_id": False,
                "purchase_order_id": False,
                "picking_id": False,
                "consumption_period_days": params["consumption_days"],
                "warehouse_id": False,
            }

        qty_available = self._get_qty_available(product, warehouse)
        virtual_available = self._get_virtual_available(product, warehouse)
        consumption = self._compute_consumption(product, warehouse, company, today, params)
        orderpoint_info = self._resolve_orderpoint(product, warehouse)
        seller = self._get_seller(product, company, today)
        supplier_delay = seller.delay if seller else None
        supplier_missing = not seller
        reception = self._get_next_reception(product, company)
        confirmed_po_qty = self._get_confirmed_po_qty(product, company)

        orderpoint = orderpoint_info["orderpoint"]
        min_qty_exploitable = orderpoint_info["status"] == "ok"
        min_qty = (
            self._convert_qty(product, orderpoint.product_min_qty, product.uom_id)
            if orderpoint and min_qty_exploitable
            else 0.0
        )
        max_qty = (
            self._convert_qty(product, orderpoint.product_max_qty, product.uom_id)
            if orderpoint
            else 0.0
        )
        daily_consumption = consumption["daily_consumption"]
        history_insufficient = consumption["history_insufficient"]
        zero_consumption_observed = (
            not history_insufficient
            and daily_consumption == 0
            and consumption["history_evaluated"]
        )

        stock_break_date = None
        min_reach_date = None
        order_deadline_date = None
        projected_qty_at_reception = None
        coverage_days = 0.0

        if daily_consumption > 0:
            coverage_days = qty_available / daily_consumption
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

        risk_input = ProcurementRiskInput(
            today=today,
            watch_lead_days=params["watch_lead_days"],
            qty_available=qty_available,
            daily_consumption=daily_consumption,
            history_insufficient=history_insufficient,
            warehouse_configured=True,
            essential_data_missing=not bool(product.uom_id),
            min_qty_exploitable=min_qty_exploitable,
            min_qty=min_qty,
            stock_break_date=stock_break_date,
            order_deadline_date=order_deadline_date,
            next_reception_date=reception.get("date"),
            projected_qty_at_reception=projected_qty_at_reception,
        )

        return {
            "risk_input": risk_input,
            "orderpoint_status": orderpoint_info["status"],
            "supplier_missing": supplier_missing,
            "history_insufficient": history_insufficient,
            "zero_consumption_observed": zero_consumption_observed,
            "consumption_untraceable": bool(
                product.product_tmpl_id.laplatine_procurement_consumption_untraceable
            ),
            "confirmed_po_qty": confirmed_po_qty,
            "next_reception_date": reception.get("date"),
            "has_open_reception": bool(reception.get("date")),
            "qty_available": qty_available,
            "virtual_available": virtual_available,
            "daily_consumption": daily_consumption,
            "min_qty": min_qty,
            "max_qty": max_qty,
            "supplier_delay": supplier_delay,
            "coverage_days": coverage_days,
            "stock_break_date": stock_break_date,
            "min_reach_date": min_reach_date,
            "order_deadline_date": order_deadline_date,
            "next_reception_qty": reception.get("qty", 0.0),
            "supplier_id": seller.partner_id.id if seller else False,
            "orderpoint_id": orderpoint.id if orderpoint else False,
            "purchase_order_id": reception.get("purchase_order_id"),
            "picking_id": reception.get("picking_id"),
            "consumption_period_days": params["consumption_days"],
            "warehouse_id": warehouse.id,
        }

    @api.model
    def _build_line_values(self, product, company, warehouse, snapshot, risk_result, alert_codes):
        alert_types = self.env["laplatine.procurement.alert.type"].search(
            [("code", "in", alert_codes)]
        )
        return {
            "product_id": product.id,
            "company_id": company.id,
            "warehouse_id": snapshot["warehouse_id"],
            "qty_available": snapshot["qty_available"],
            "virtual_available": snapshot["virtual_available"],
            "daily_consumption": snapshot["daily_consumption"],
            "coverage_days": snapshot["coverage_days"],
            "min_qty": snapshot["min_qty"],
            "max_qty": snapshot["max_qty"],
            "confirmed_po_qty": snapshot["confirmed_po_qty"],
            "next_reception_qty": snapshot["next_reception_qty"],
            "supplier_delay": snapshot["supplier_delay"] or 0,
            "consumption_period_days": snapshot["consumption_period_days"],
            "stock_break_date": snapshot["stock_break_date"],
            "min_reach_date": snapshot["min_reach_date"],
            "order_deadline_date": snapshot["order_deadline_date"],
            "next_reception_date": snapshot["next_reception_date"],
            "supplier_id": snapshot["supplier_id"],
            "orderpoint_id": snapshot["orderpoint_id"],
            "purchase_order_id": snapshot["purchase_order_id"],
            "picking_id": snapshot["picking_id"],
            "risk_status": risk_result["risk_status"],
            "risk_reason": risk_result["risk_reason"],
            "action_recommended": risk_result["action_recommended"],
            "alert_ids": [(6, 0, alert_types.ids)],
            "alert_codes": ",".join(sorted(alert_codes)),
        }

    @api.model
    def _company_params(self, company):
        return {
            "consumption_days": company.laplatine_procurement_consumption_days or 90,
            "min_history_days": company.laplatine_procurement_min_history_days or 30,
            "watch_lead_days": company.laplatine_procurement_watch_lead_days or 7,
            "stale_warning_hours": company.laplatine_procurement_stale_warning_hours or 24,
        }

    @api.model
    def _convert_qty(self, product, qty, from_uom):
        if not from_uom or from_uom == product.uom_id:
            return qty
        return from_uom._compute_quantity(qty, product.uom_id)

    @api.model
    def _get_qty_available(self, product, warehouse):
        return product.with_context(warehouse=warehouse.id).qty_available

    @api.model
    def _get_virtual_available(self, product, warehouse):
        return product.with_context(warehouse=warehouse.id).virtual_available

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
            return {
                "daily_consumption": 0.0,
                "history_insufficient": True,
                "history_evaluated": True,
            }

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
                "history_evaluated": True,
            }

        first_move_date = min(move_dates)
        history_insufficient = first_move_date > today - timedelta(days=min_history_days)
        if history_insufficient:
            return {
                "daily_consumption": 0.0,
                "history_insufficient": True,
                "history_evaluated": True,
            }

        net_qty = sum(
            self._convert_qty(product, move.product_uom_qty, move.product_uom)
            for move in outgoing
        ) - sum(
            self._convert_qty(product, move.product_uom_qty, move.product_uom)
            for move in incoming
        )
        daily_consumption = net_qty / consumption_days if consumption_days else 0.0
        if daily_consumption < 0:
            daily_consumption = 0.0
        return {
            "daily_consumption": daily_consumption,
            "history_insufficient": False,
            "history_evaluated": True,
        }

    @api.model
    def _resolve_orderpoint(self, product, warehouse):
        orderpoints = self.env["stock.warehouse.orderpoint"].search(
            [
                ("product_id", "=", product.id),
                ("warehouse_id", "=", warehouse.id),
                ("location_id", "=", warehouse.lot_stock_id.id),
            ]
        )
        if not orderpoints:
            return {"orderpoint": False, "status": "missing"}
        if len(orderpoints) > 1:
            return {"orderpoint": False, "status": "ambiguous"}
        orderpoint = orderpoints[0]
        min_qty = self._convert_qty(
            product, orderpoint.product_min_qty, product.uom_id
        )
        if min_qty <= 0:
            return {"orderpoint": orderpoint, "status": "incomplete"}
        return {"orderpoint": orderpoint, "status": "ok"}

    @api.model
    def _get_seller(self, product, company, today):
        return product._select_seller(
            partner_id=False,
            quantity=1.0,
            date=today,
            uom_id=product.uom_po_id,
            params={"company_id": company.id},
        )

    @api.model
    def _get_confirmed_po_qty(self, product, company):
        lines = self._get_confirmed_po_lines(product, company)
        return sum(self._get_line_remaining_qty(product, line) for line in lines)

    @api.model
    def _get_confirmed_po_lines(self, product, company):
        return self.env["purchase.order.line"].search(
            [
                ("product_id", "=", product.id),
                ("order_id.state", "=", "purchase"),
                ("order_id.company_id", "=", company.id),
            ]
        ).filtered(lambda line: line.product_qty > line.qty_received)

    @api.model
    def _get_line_remaining_qty(self, product, po_line):
        remaining = po_line.product_qty - po_line.qty_received
        return self._convert_qty(product, remaining, po_line.product_uom)

    @api.model
    def _get_next_reception(self, product, company):
        lines = self._get_confirmed_po_lines(product, company)
        if not lines:
            return {"date": None, "qty": 0.0}

        receptions = []
        for line in lines:
            reception_date = self._get_reception_date(line)
            if not reception_date:
                continue
            remaining_qty = self._get_line_remaining_qty(product, line)
            if remaining_qty <= 0:
                continue
            picking = self._get_incoming_picking(line)
            receptions.append(
                {
                    "date": reception_date,
                    "qty": remaining_qty,
                    "purchase_order_id": line.order_id.id,
                    "picking_id": picking.id if picking else False,
                }
            )

        if not receptions:
            return {"date": None, "qty": 0.0}

        closest = min(receptions, key=lambda item: item["date"])
        same_day = [item for item in receptions if item["date"] == closest["date"]]
        return {
            "date": closest["date"],
            "qty": sum(item["qty"] for item in same_day),
            "purchase_order_id": closest["purchase_order_id"],
            "picking_id": closest["picking_id"],
        }

    @api.model
    def _get_incoming_picking(self, po_line):
        moves = po_line.move_ids.filtered(
            lambda move: move.state not in ("done", "cancel")
            and move.picking_type_id.code == "incoming"
        )
        pickings = moves.mapped("picking_id")
        return pickings[:1]

    @api.model
    def _get_reception_date(self, po_line):
        moves = po_line.move_ids.filtered(
            lambda move: move.state not in ("done", "cancel")
            and move.picking_type_id.code == "incoming"
        )
        move_dates = [
            fields.Date.to_date(move.date) for move in moves if move.date
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
