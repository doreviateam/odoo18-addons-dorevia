# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import date
from typing import Optional


NEED_SUPPLY_STATUSES = frozenset(
    {"watch", "action_required", "critical", "stockout"}
)


@dataclass(frozen=True)
class ProcurementAlertInput:
    """Indicateurs pré-calculés pour les alertes cumulables §11.3."""

    risk_status: str
    orderpoint_status: str
    supplier_missing: bool
    history_insufficient: bool
    zero_consumption_observed: bool
    consumption_untraceable: bool
    confirmed_po_qty: float
    reception_date: Optional[date] = None
    today: Optional[date] = None
    has_open_reception: bool = False


def compute_procurement_alerts(input_data: ProcurementAlertInput):
    """Retourne les codes d'alerte cumulables, sans modifier le statut principal."""
    alerts = []

    if input_data.has_open_reception and input_data.reception_date and input_data.today:
        if input_data.reception_date < input_data.today:
            alerts.append("reception_late")

    if input_data.orderpoint_status in ("missing", "incomplete", "ambiguous"):
        alerts.append("orderpoint_incomplete")

    if input_data.supplier_missing:
        alerts.append("supplier_missing")

    if input_data.history_insufficient:
        alerts.append("history_insufficient")

    if input_data.zero_consumption_observed:
        alerts.append("no_consumption")

    if (
        input_data.risk_status in NEED_SUPPLY_STATUSES
        and input_data.confirmed_po_qty <= 0
    ):
        alerts.append("no_confirmed_po")

    if input_data.consumption_untraceable:
        alerts.append("consumption_untraceable")

    return alerts
