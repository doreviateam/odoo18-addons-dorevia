# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass(frozen=True)
class ProcurementRiskInput:
    """Indicateurs pré-calculés alimentant la matrice déterministe §12.3."""

    today: date
    watch_lead_days: int
    qty_available: float
    daily_consumption: float
    history_insufficient: bool = False
    warehouse_configured: bool = True
    essential_data_missing: bool = False
    min_qty_exploitable: bool = True
    min_qty: float = 0.0
    stock_break_date: Optional[date] = None
    order_deadline_date: Optional[date] = None
    next_reception_date: Optional[date] = None
    projected_qty_at_reception: Optional[float] = None


def compute_procurement_risk(input_data: ProcurementRiskInput) -> dict:
    """Matrice déterministe du statut principal — spec §12.3."""
    missing_reason = _missing_data_reason(input_data)
    if missing_reason:
        return _result(
            "insufficient_data",
            missing_reason,
            "Compléter les données indispensables au pilotage",
        )

    if input_data.qty_available <= 0:
        return _result(
            "stockout",
            "Priorité 2 — stock physique ≤ 0 (%.2f u)." % input_data.qty_available,
            "Sécuriser l'approvisionnement — stock indisponible",
        )

    if _priority_3_critical(input_data):
        return _result(
            "critical",
            _critical_reason(input_data),
            "Commander ou accélérer la réception avant la rupture projetée",
        )

    if _priority_4_below_min_before_reception(input_data):
        return _result(
            "action_required",
            _below_min_reason(input_data),
            "Sécuriser l'approvisionnement avant la prochaine réception",
        )

    if _priority_5_deadline_reached(input_data):
        return _result(
            "action_required",
            _deadline_reached_reason(input_data),
            "Passer commande — date limite atteinte ou dépassée",
        )

    if _priority_6_watch_window(input_data):
        return _result(
            "watch",
            _watch_reason(input_data),
            "Anticiper la commande — date limite proche",
        )

    if _priority_7_normal(input_data):
        return _result(
            "normal",
            "Priorité 7 — couverture, approvisionnements et paramétrage compatibles.",
            "Aucune action urgente",
        )

    if not input_data.min_qty_exploitable:
        return _result(
            "insufficient_data",
            "Paramétrage min/max incomplet — statut Normal inaccessible (§12.3).",
            "Paramétrer la règle de réapprovisionnement (min/max)",
        )

    return _result(
        "insufficient_data",
        "Situation non classée en Normal — vérifier les indicateurs de pilotage.",
        "Analyser les données de pilotage",
    )


def _result(risk_status, risk_reason, action_recommended):
    return {
        "risk_status": risk_status,
        "risk_reason": risk_reason,
        "action_recommended": action_recommended,
    }


def _missing_data_reason(input_data):
    reasons = []
    if not input_data.warehouse_configured:
        reasons.append("entrepôt de pilotage non configuré")
    if input_data.history_insufficient:
        reasons.append("historique insuffisant")
    if input_data.essential_data_missing:
        reasons.append("données article indispensables absentes")
    if not reasons:
        return None
    return "Priorité 1 — %s." % ", ".join(reasons)


def _dates_projection_enabled(input_data):
    return input_data.daily_consumption > 0


def _priority_3_critical(input_data):
    if not _dates_projection_enabled(input_data):
        return False
    if not input_data.stock_break_date or not input_data.next_reception_date:
        return False
    return input_data.stock_break_date < input_data.next_reception_date


def _critical_reason(input_data):
    return (
        "Priorité 3 — rupture physique projetée le %s avant réception confirmée le %s."
        % (input_data.stock_break_date, input_data.next_reception_date)
    )


def _priority_4_below_min_before_reception(input_data):
    if not _dates_projection_enabled(input_data):
        return False
    if not input_data.min_qty_exploitable or not input_data.next_reception_date:
        return False
    if input_data.projected_qty_at_reception is None:
        return False
    return input_data.projected_qty_at_reception < input_data.min_qty


def _below_min_reason(input_data):
    return (
        "Priorité 4 — stock projeté %.2f u à la réception du %s "
        "inférieur au minimum %.2f u."
        % (
            input_data.projected_qty_at_reception,
            input_data.next_reception_date,
            input_data.min_qty,
        )
    )


def _priority_5_deadline_reached(input_data):
    if not _dates_projection_enabled(input_data):
        return False
    if not input_data.order_deadline_date:
        return False
    return input_data.today >= input_data.order_deadline_date


def _deadline_reached_reason(input_data):
    return (
        "Priorité 5 — date limite de commande atteinte ou dépassée "
        "(%s, aujourd'hui %s)."
        % (input_data.order_deadline_date, input_data.today)
    )


def _priority_6_watch_window(input_data):
    if not _dates_projection_enabled(input_data):
        return False
    if not input_data.order_deadline_date:
        return False
    watch_start = input_data.order_deadline_date - timedelta(
        days=input_data.watch_lead_days
    )
    return watch_start <= input_data.today < input_data.order_deadline_date


def _watch_reason(input_data):
    watch_start = input_data.order_deadline_date - timedelta(
        days=input_data.watch_lead_days
    )
    return (
        "Priorité 6 — date limite de commande le %s "
        "(fenêtre surveillance depuis %s, marge %s j)."
        % (
            input_data.order_deadline_date,
            watch_start,
            input_data.watch_lead_days,
        )
    )


def _priority_7_normal(input_data):
    if not input_data.min_qty_exploitable:
        return False
    if input_data.qty_available <= 0:
        return False
    if _dates_projection_enabled(input_data):
        if _priority_3_critical(input_data):
            return False
        if _priority_4_below_min_before_reception(input_data):
            return False
        if _priority_5_deadline_reached(input_data):
            return False
        if _priority_6_watch_window(input_data):
            return False
    return True
