# -*- coding: utf-8 -*-
from datetime import date, datetime
from io import BytesIO

import xlsxwriter

META_ROW_COUNT = 5
HEADER_ROW = 5
FIRST_DATA_ROW = 6
EMPTY_MESSAGE_ROW = 6

META_TITLE_ROW_HEIGHT = 22
META_ROW_HEIGHT = 16
HEADER_ROW_HEIGHT = 24
DATA_ROW_HEIGHT = 16
SPACER_ROW_HEIGHT = 6

VENTES_HEADERS = [
    "Type",
    "Numéro",
    "Client",
    "Date de facture",
    "Date d'échéance",
    "Montant HT",
    "TVA",
    "Montant TTC",
    "Montant réglé / soldé",
    "Reste à payer / solder",
    "État du paiement",
]

ACHATS_HEADERS = [
    "Type",
    "Numéro Odoo",
    "Référence fournisseur",
    "Fournisseur",
    "Date de facture",
    "Date d'échéance",
    "Montant HT",
    "TVA",
    "Montant TTC",
    "Montant réglé / soldé",
    "Reste à payer / solder",
    "État du paiement",
]

VENTES_COLUMN_WIDTHS = [10, 18, 32, 11, 11, 14, 12, 14, 18, 18, 22]
ACHATS_COLUMN_WIDTHS = [10, 18, 18, 32, 11, 11, 14, 12, 14, 18, 18, 22]

EMPTY_SHEET_MESSAGE = "Aucun document trouvé sur la période sélectionnée."


def build_report_filename(date_from, date_to):
    return (
        f"Rapport_facturation_La_Platine_"
        f"{date_from.isoformat()}_{date_to.isoformat()}.xlsx"
    )


def report_sign(move_type):
    if move_type in ("out_refund", "in_refund"):
        return -1
    return 1


def document_type_label(move_type):
    if move_type in ("out_refund", "in_refund"):
        return "Avoir"
    return "Facture"


def signed_move_amounts(move):
    sign = report_sign(move.move_type)
    return {
        "amount_ht": sign * abs(move.amount_untaxed),
        "amount_tax": sign * abs(move.amount_tax),
        "amount_ttc": sign * abs(move.amount_total),
        "amount_paid": sign * abs(move.amount_total - move.amount_residual),
        "amount_due": sign * abs(move.amount_residual),
    }


def _date_to_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return None


def _write_string(worksheet, row, col, value, cell_format):
    worksheet.write_string(row, col, value or "", cell_format)


class LaplatineBillingReportXlsx:
    """Génère le classeur XLSX du rapport de facturation La Platine."""

    def __init__(
        self,
        company,
        date_from,
        date_to,
        sale_moves,
        purchase_moves,
        generation_date,
        payment_state_labels,
    ):
        self.company = company
        self.date_from = date_from
        self.date_to = date_to
        self.sale_moves = sale_moves.sorted(key=lambda move: (move.invoice_date, move.name))
        self.purchase_moves = purchase_moves.sorted(
            key=lambda move: (move.invoice_date, move.name)
        )
        self.generation_date = generation_date
        self.payment_state_labels = payment_state_labels
        self.currency = company.currency_id

    def generate(self):
        buffer = BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        self._write_ventes_sheet(workbook)
        self._write_achats_sheet(workbook)
        workbook.close()
        buffer.seek(0)
        return buffer.read()

    def _build_formats(self, workbook):
        currency = self.currency
        decimals = currency.decimal_places if currency else 2
        symbol = currency.symbol if currency else ""
        num_format = f'#,##0.{"0" * decimals} "{symbol}"'
        border = {"border": 1}

        return {
            "title": workbook.add_format({"bold": True, "font_size": 14}),
            "meta": workbook.add_format({"font_size": 11}),
            "header": workbook.add_format(
                {
                    "bold": True,
                    "bg_color": "#EEEEEE",
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                    "text_wrap": True,
                }
            ),
            "text": workbook.add_format({**border, "align": "left", "indent": 1, "valign": "vcenter"}),
            "date": workbook.add_format(
                {**border, "num_format": "dd/mm/yyyy", "align": "center", "valign": "vcenter"}
            ),
            "amount": workbook.add_format(
                {**border, "num_format": num_format, "align": "right", "valign": "vcenter"}
            ),
            "amount_negative": workbook.add_format(
                {
                    **border,
                    "num_format": num_format,
                    "align": "right",
                    "valign": "vcenter",
                    "font_color": "#9E0000",
                }
            ),
            "empty_message": workbook.add_format({"italic": True, "font_size": 11}),
            "total_label": workbook.add_format(
                {"bold": True, "border": 1, "align": "right", "valign": "vcenter", "bg_color": "#F5F5F5"}
            ),
            "total_count": workbook.add_format(
                {"bold": True, "border": 1, "align": "center", "valign": "vcenter", "bg_color": "#F5F5F5"}
            ),
            "total_amount": workbook.add_format(
                {
                    "bold": True,
                    "num_format": num_format,
                    "border": 1,
                    "align": "right",
                    "valign": "vcenter",
                    "bg_color": "#F5F5F5",
                }
            ),
            "total_amount_negative": workbook.add_format(
                {
                    "bold": True,
                    "num_format": num_format,
                    "border": 1,
                    "align": "right",
                    "valign": "vcenter",
                    "bg_color": "#F5F5F5",
                    "font_color": "#9E0000",
                }
            ),
        }

    def _amount_format(self, formats, value):
        if value < 0:
            return formats["amount_negative"]
        return formats["amount"]

    def _total_amount_format(self, formats, value):
        if value < 0:
            return formats["total_amount_negative"]
        return formats["total_amount"]

    def _write_amount(self, worksheet, row, col, value, formats):
        worksheet.write_number(row, col, value, self._amount_format(formats, value))

    def _write_meta_block(self, worksheet, formats, title, headers):
        last_col = len(headers) - 1
        period_label = (
            f"Du {self.date_from.strftime('%d/%m/%Y')} "
            f"au {self.date_to.strftime('%d/%m/%Y')}"
        )
        worksheet.merge_range(0, 0, 0, last_col, title, formats["title"])
        worksheet.merge_range(1, 0, 1, last_col, self.company.display_name, formats["meta"])
        worksheet.merge_range(2, 0, 2, last_col, period_label, formats["meta"])
        worksheet.merge_range(
            3,
            0,
            3,
            last_col,
            f"Généré le {self.generation_date.strftime('%d/%m/%Y')}",
            formats["meta"],
        )
        worksheet.set_row(0, META_TITLE_ROW_HEIGHT)
        worksheet.set_row(1, META_ROW_HEIGHT)
        worksheet.set_row(2, META_ROW_HEIGHT)
        worksheet.set_row(3, META_ROW_HEIGHT)
        worksheet.set_row(4, SPACER_ROW_HEIGHT)

    def _write_headers(self, worksheet, formats, headers):
        for col, header in enumerate(headers):
            worksheet.write_string(HEADER_ROW, col, header, formats["header"])
        worksheet.set_row(HEADER_ROW, HEADER_ROW_HEIGHT)

    def _write_totals_row(self, worksheet, formats, moves, amount_col_start):
        totals = {
            "amount_ht": 0.0,
            "amount_tax": 0.0,
            "amount_ttc": 0.0,
            "amount_paid": 0.0,
            "amount_due": 0.0,
        }
        for move in moves:
            amounts = signed_move_amounts(move)
            for key in totals:
                totals[key] += amounts[key]

        totals_row = FIRST_DATA_ROW + (1 if not moves else len(moves))
        worksheet.set_row(totals_row, DATA_ROW_HEIGHT)
        worksheet.write_string(totals_row, 0, "Nombre de documents", formats["total_label"])
        worksheet.write_number(totals_row, 1, len(moves), formats["total_count"])

        for offset, key in enumerate(
            ("amount_ht", "amount_tax", "amount_ttc", "amount_paid", "amount_due")
        ):
            value = totals[key]
            worksheet.write_number(
                totals_row,
                amount_col_start + offset,
                value,
                self._total_amount_format(formats, value),
            )
        return totals_row, totals

    def _write_ventes_rows(self, worksheet, formats, moves):
        row = FIRST_DATA_ROW
        if not moves:
            worksheet.merge_range(
                EMPTY_MESSAGE_ROW,
                0,
                EMPTY_MESSAGE_ROW,
                len(VENTES_HEADERS) - 1,
                EMPTY_SHEET_MESSAGE,
                formats["empty_message"],
            )
            return row + 1

        for move in moves:
            worksheet.set_row(row, DATA_ROW_HEIGHT)
            amounts = signed_move_amounts(move)
            payment_label = self.payment_state_labels.get(
                move.payment_state, move.payment_state or ""
            )

            _write_string(
                worksheet, row, 0, document_type_label(move.move_type), formats["text"]
            )
            _write_string(worksheet, row, 1, move.name, formats["text"])
            _write_string(
                worksheet, row, 2, move.partner_id.display_name, formats["text"]
            )

            invoice_dt = _date_to_datetime(move.invoice_date)
            if invoice_dt:
                worksheet.write_datetime(row, 3, invoice_dt, formats["date"])
            else:
                _write_string(worksheet, row, 3, "", formats["text"])

            due_dt = _date_to_datetime(move.invoice_date_due)
            if due_dt:
                worksheet.write_datetime(row, 4, due_dt, formats["date"])
            else:
                _write_string(worksheet, row, 4, "", formats["text"])

            self._write_amount(worksheet, row, 5, amounts["amount_ht"], formats)
            self._write_amount(worksheet, row, 6, amounts["amount_tax"], formats)
            self._write_amount(worksheet, row, 7, amounts["amount_ttc"], formats)
            self._write_amount(worksheet, row, 8, amounts["amount_paid"], formats)
            self._write_amount(worksheet, row, 9, amounts["amount_due"], formats)
            _write_string(worksheet, row, 10, payment_label, formats["text"])
            row += 1

        return row

    def _write_achats_rows(self, worksheet, formats, moves):
        row = FIRST_DATA_ROW
        if not moves:
            worksheet.merge_range(
                EMPTY_MESSAGE_ROW,
                0,
                EMPTY_MESSAGE_ROW,
                len(ACHATS_HEADERS) - 1,
                EMPTY_SHEET_MESSAGE,
                formats["empty_message"],
            )
            return row + 1

        for move in moves:
            worksheet.set_row(row, DATA_ROW_HEIGHT)
            amounts = signed_move_amounts(move)
            payment_label = self.payment_state_labels.get(
                move.payment_state, move.payment_state or ""
            )

            _write_string(
                worksheet, row, 0, document_type_label(move.move_type), formats["text"]
            )
            _write_string(worksheet, row, 1, move.name, formats["text"])
            _write_string(worksheet, row, 2, move.ref, formats["text"])
            _write_string(
                worksheet, row, 3, move.partner_id.display_name, formats["text"]
            )

            invoice_dt = _date_to_datetime(move.invoice_date)
            if invoice_dt:
                worksheet.write_datetime(row, 4, invoice_dt, formats["date"])
            else:
                _write_string(worksheet, row, 4, "", formats["text"])

            due_dt = _date_to_datetime(move.invoice_date_due)
            if due_dt:
                worksheet.write_datetime(row, 5, due_dt, formats["date"])
            else:
                _write_string(worksheet, row, 5, "", formats["text"])

            self._write_amount(worksheet, row, 6, amounts["amount_ht"], formats)
            self._write_amount(worksheet, row, 7, amounts["amount_tax"], formats)
            self._write_amount(worksheet, row, 8, amounts["amount_ttc"], formats)
            self._write_amount(worksheet, row, 9, amounts["amount_paid"], formats)
            self._write_amount(worksheet, row, 10, amounts["amount_due"], formats)
            _write_string(worksheet, row, 11, payment_label, formats["text"])
            row += 1

        return row

    def _configure_column_widths(self, worksheet, widths):
        for index, width in enumerate(widths):
            worksheet.set_column(index, index, width)

    def _apply_print_setup(self, worksheet, headers, last_row):
        last_col = len(headers) - 1
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.4, right=0.4, top=0.5, bottom=0.55)
        worksheet.fit_to_pages(1, 0)
        worksheet.set_footer("&CPage &P / &N", {"margin": 0.25})
        worksheet.repeat_rows(0, HEADER_ROW)
        worksheet.freeze_panes(FIRST_DATA_ROW, 0)
        worksheet.autofilter(HEADER_ROW, 0, max(last_row, HEADER_ROW), last_col)
        worksheet.print_area(0, 0, last_row, last_col)
        worksheet.hide_gridlines(2)

    def _write_data_sheet(
        self,
        workbook,
        sheet_name,
        title,
        headers,
        column_widths,
        moves,
        amount_col_start,
        write_rows_method,
    ):
        worksheet = workbook.add_worksheet(sheet_name)
        formats = self._build_formats(workbook)
        self._write_meta_block(worksheet, formats, title, headers)
        self._write_headers(worksheet, formats, headers)
        write_rows_method(worksheet, formats, moves)
        last_row, _totals = self._write_totals_row(
            worksheet, formats, moves, amount_col_start
        )
        self._configure_column_widths(worksheet, column_widths)
        self._apply_print_setup(worksheet, headers, last_row)
        return worksheet

    def _write_ventes_sheet(self, workbook):
        self._write_data_sheet(
            workbook,
            "Ventes",
            "Rapport de facturation — Ventes",
            VENTES_HEADERS,
            VENTES_COLUMN_WIDTHS,
            self.sale_moves,
            5,
            self._write_ventes_rows,
        )

    def _write_achats_sheet(self, workbook):
        self._write_data_sheet(
            workbook,
            "Achats",
            "Rapport de facturation — Achats",
            ACHATS_HEADERS,
            ACHATS_COLUMN_WIDTHS,
            self.purchase_moves,
            6,
            self._write_achats_rows,
        )


def generate_billing_report_xlsx(
    company,
    date_from,
    date_to,
    sale_moves,
    purchase_moves,
    generation_date,
    payment_state_labels,
):
    generator = LaplatineBillingReportXlsx(
        company=company,
        date_from=date_from,
        date_to=date_to,
        sale_moves=sale_moves,
        purchase_moves=purchase_moves,
        generation_date=generation_date,
        payment_state_labels=payment_state_labels,
    )
    return generator.generate()
