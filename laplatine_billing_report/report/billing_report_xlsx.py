# -*- coding: utf-8 -*-
from io import BytesIO

import xlsxwriter


def build_report_filename(date_from, date_to):
    return (
        f"Rapport_facturation_La_Platine_"
        f"{date_from.isoformat()}_{date_to.isoformat()}.xlsx"
    )


def generate_stub_workbook():
    """Slice A — classeur minimal sans logique métier Ventes / Achats."""
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
    workbook.add_worksheet("Ventes")
    workbook.add_worksheet("Achats")
    workbook.close()
    buffer.seek(0)
    return buffer.read()
