# -*- coding: utf-8 -*-
import re
import unicodedata
from datetime import date, datetime
from io import BytesIO

import xlsxwriter

COLUMN_HEADERS = [
    "Facture",
    "Date",
    "Échéance",
    "Montant TTC",
    "Réglé",
    "Solde",
    "Statut",
]

META_ROWS = 4
SUMMARY_START_ROW = META_ROWS
SUMMARY_LINE_COUNT = 4
HEADER_ROW = SUMMARY_START_ROW + SUMMARY_LINE_COUNT + 1
FIRST_DATA_ROW = HEADER_ROW + 1

SUMMARY_LINES = (
    ("total_invoiced", "Total facturé"),
    ("total_paid", "Total réglé"),
    ("total_to_pay", "Montant total à régler à La Platine"),
    ("total_overdue", "Dont montant en retard"),
)

STATUS_OVERDUE_MARKER = "en retard"


def _date_to_datetime(value):
    if not value:
        return None
    return datetime.combine(value, datetime.min.time())


def _ensure_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


def is_due_date_overdue(invoice_date_due, reference_date):
    """Échéance dépassée si invoice_date_due < date du jour (égalité = pas en retard)."""
    due = _ensure_date(invoice_date_due)
    ref = _ensure_date(reference_date)
    if not due or not ref:
        return False
    return due < ref


def invoice_is_fully_paid(payment_state, amount_residual, currency=None):
    if payment_state == "paid":
        return True
    if currency is not None:
        return currency.is_zero(amount_residual)
    return not amount_residual


def invoice_display_status(payment_state, amount_total, amount_residual, invoice_date_due, reference_date, currency=None):
    """Libellé Statut tenant compte du paiement et de l'échéance."""
    if invoice_is_fully_paid(payment_state, amount_residual, currency=currency):
        return "Payée"
    if payment_state == "in_payment":
        return "Paiement en cours"

    overdue = is_due_date_overdue(invoice_date_due, reference_date)

    if payment_state == "partial" or (amount_residual and amount_total and amount_residual < amount_total):
        if not invoice_date_due:
            return "Partiellement payée"
        return "Partiellement payée — en retard" if overdue else "Partiellement payée"

    if not invoice_date_due:
        return "À payer"

    return "En retard" if overdue else "À payer"


def status_uses_overdue_highlight(status_label):
    return STATUS_OVERDUE_MARKER in (status_label or "").casefold()


def compute_report_summary(invoices, reference_date, currency=None):
    """Calcule les totaux du bloc de synthèse."""
    summary = {
        "total_invoiced": 0.0,
        "total_paid": 0.0,
        "total_to_pay": 0.0,
        "total_overdue": 0.0,
    }
    for invoice in invoices:
        amount_total = invoice.amount_total
        amount_residual = invoice.amount_residual
        amount_paid = amount_total - amount_residual

        summary["total_invoiced"] += amount_total
        summary["total_paid"] += amount_paid
        summary["total_to_pay"] += amount_residual

        if invoice_is_fully_paid(invoice.payment_state, amount_residual, currency=currency):
            continue

        due_date = invoice.invoice_date_due
        if due_date and is_due_date_overdue(due_date, reference_date):
            summary["total_overdue"] += amount_residual

    return summary


def slugify_partner_name(name):
    if not name:
        return "Partenaire"
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_name).strip("_")
    return slug or "Partenaire"


def build_filename(partner, date_from):
    partner_slug = slugify_partner_name(partner.display_name)
    period = date_from.strftime("%Y-%m")
    return f"Etat_facturation_{partner_slug}_{period}.xlsx"


class LaplatineCustomerStatementXlsx:
    """Génère le classeur XLSX de l'état de facturation client."""

    def __init__(self, partner, date_from, date_to, invoices, generation_date):
        self.partner = partner
        self.date_from = date_from
        self.date_to = date_to
        self.invoices = invoices.sorted(key=lambda move: (move.invoice_date, move.name))
        self.generation_date = generation_date
        self.currency = invoices[:1].currency_id

    def generate(self):
        buffer = BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        worksheet = workbook.add_worksheet("État de facturation")
        formats = self._build_formats(workbook)

        self._write_meta_block(worksheet, formats)
        summary = compute_report_summary(
            self.invoices, self.generation_date, currency=self.currency
        )
        self._write_summary_block(worksheet, formats, summary)
        self._write_column_headers(worksheet, formats)
        totals = self._write_invoice_lines(worksheet, formats)
        last_row = self._write_totals(worksheet, formats, totals)

        self._apply_print_setup(worksheet, last_row)

        workbook.close()
        buffer.seek(0)
        return buffer.getvalue(), build_filename(self.partner, self.date_from)

    def _build_formats(self, workbook):
        currency = self.currency
        decimals = currency.decimal_places if currency else 2
        symbol = currency.symbol if currency else ""
        num_format = f'#,##0.{"0" * decimals} "{symbol}"'

        return {
            "title": workbook.add_format({"bold": True, "font_size": 14}),
            "meta": workbook.add_format({"font_size": 11}),
            "summary_label": workbook.add_format({"font_size": 11, "align": "left", "bold": True}),
            "summary_label_primary": workbook.add_format(
                {"font_size": 11, "align": "left", "bold": True, "underline": 1}
            ),
            "summary_amount": workbook.add_format(
                {"font_size": 11, "num_format": num_format, "align": "right", "bold": True}
            ),
            "summary_overdue_label": workbook.add_format(
                {
                    "font_size": 11,
                    "align": "left",
                    "bold": True,
                    "bg_color": "#FFEBEE",
                    "font_color": "#9E0000",
                }
            ),
            "summary_overdue_amount": workbook.add_format(
                {
                    "font_size": 11,
                    "num_format": num_format,
                    "align": "right",
                    "bold": True,
                    "bg_color": "#FFEBEE",
                    "font_color": "#9E0000",
                }
            ),
            "header": workbook.add_format(
                {
                    "bold": True,
                    "bg_color": "#EEEEEE",
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                }
            ),
            "text": workbook.add_format({"border": 1, "align": "left", "indent": 1}),
            "date": workbook.add_format({"num_format": "dd/mm/yyyy", "border": 1, "align": "center"}),
            "amount": workbook.add_format(
                {"num_format": num_format, "border": 1, "align": "right"}
            ),
            "status": workbook.add_format({"border": 1, "align": "left", "indent": 1}),
            "status_overdue": workbook.add_format(
                {
                    "border": 1,
                    "align": "left",
                    "indent": 1,
                    "bold": True,
                    "font_color": "#9E0000",
                }
            ),
            "total_label": workbook.add_format({"bold": True, "border": 1, "align": "right"}),
            "total_amount": workbook.add_format(
                {"bold": True, "num_format": num_format, "border": 1, "align": "right"}
            ),
        }

    def _write_meta_block(self, worksheet, formats):
        period_label = (
            f"Du {self.date_from.strftime('%d/%m/%Y')} "
            f"au {self.date_to.strftime('%d/%m/%Y')}"
        )
        last_col = len(COLUMN_HEADERS) - 1
        worksheet.merge_range(0, 0, 0, last_col, "État de facturation", formats["title"])
        worksheet.merge_range(1, 0, 1, last_col, self.partner.display_name, formats["meta"])
        worksheet.merge_range(2, 0, 2, last_col, period_label, formats["meta"])
        worksheet.merge_range(
            3,
            0,
            3,
            last_col,
            f"Généré le {self.generation_date.strftime('%d/%m/%Y')}",
            formats["meta"],
        )
        worksheet.set_row(0, 22)

    def _write_summary_block(self, worksheet, formats, summary):
        last_col = len(COLUMN_HEADERS) - 1
        amount_col_start = 3
        for index, (key, label) in enumerate(SUMMARY_LINES):
            row = SUMMARY_START_ROW + index
            if key == "total_to_pay":
                label_fmt = formats["summary_label_primary"]
                amount_fmt = formats["summary_amount"]
            elif key == "total_overdue":
                label_fmt = formats["summary_overdue_label"]
                amount_fmt = formats["summary_overdue_amount"]
            else:
                label_fmt = formats["summary_label"]
                amount_fmt = formats["summary_amount"]

            worksheet.merge_range(row, 0, row, amount_col_start - 1, label, label_fmt)
            worksheet.write_number(row, amount_col_start, summary[key], amount_fmt)
            for col in range(amount_col_start + 1, last_col + 1):
                worksheet.write_blank(row, col, None, amount_fmt if key == "total_overdue" else formats["summary_amount"])

        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 2, 12)
        worksheet.set_column(3, 5, 18)
        worksheet.set_column(6, 6, 30)

    def _write_column_headers(self, worksheet, formats):
        for col, header in enumerate(COLUMN_HEADERS):
            worksheet.write(HEADER_ROW, col, header, formats["header"])
        worksheet.set_row(HEADER_ROW, 20)

    def _write_invoice_lines(self, worksheet, formats):
        totals = {"invoiced": 0.0, "paid": 0.0, "residual": 0.0}
        row = FIRST_DATA_ROW

        for invoice in self.invoices:
            amount_total = invoice.amount_total
            amount_residual = invoice.amount_residual
            amount_paid = amount_total - amount_residual
            due_date = invoice.invoice_date_due
            status_label = invoice_display_status(
                invoice.payment_state,
                amount_total,
                amount_residual,
                due_date,
                self.generation_date,
                currency=self.currency,
            )
            status_fmt = (
                formats["status_overdue"]
                if status_uses_overdue_highlight(status_label)
                else formats["status"]
            )

            worksheet.write(row, 0, invoice.name or "", formats["text"])
            worksheet.write_datetime(row, 1, _date_to_datetime(invoice.invoice_date), formats["date"])
            if due_date:
                worksheet.write_datetime(row, 2, _date_to_datetime(due_date), formats["date"])
            else:
                worksheet.write(row, 2, "", formats["text"])
            worksheet.write_number(row, 3, amount_total, formats["amount"])
            worksheet.write_number(row, 4, amount_paid, formats["amount"])
            worksheet.write_number(row, 5, amount_residual, formats["amount"])
            worksheet.write(row, 6, status_label, status_fmt)

            totals["invoiced"] += amount_total
            totals["paid"] += amount_paid
            totals["residual"] += amount_residual
            row += 1

        return totals

    def _write_totals(self, worksheet, formats, totals):
        row = FIRST_DATA_ROW + len(self.invoices)
        worksheet.write(row, 2, "Totaux", formats["total_label"])
        worksheet.write_number(row, 3, totals["invoiced"], formats["total_amount"])
        worksheet.write_number(row, 4, totals["paid"], formats["total_amount"])
        worksheet.write_number(row, 5, totals["residual"], formats["total_amount"])
        return row

    def _apply_print_setup(self, worksheet, last_row):
        last_col = len(COLUMN_HEADERS) - 1
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.4, right=0.4, top=0.5, bottom=0.55)
        worksheet.fit_to_pages(1, 0)
        worksheet.set_footer("&CPage &P / &N", {"margin": 0.25})
        worksheet.repeat_rows(HEADER_ROW, HEADER_ROW)
        worksheet.freeze_panes(FIRST_DATA_ROW, 0)
        worksheet.print_area(0, 0, last_row, last_col)
        worksheet.hide_gridlines(2)
