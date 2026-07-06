# -*- coding: utf-8 -*-
"""Find lab periods with posted invoices and refunds for Slice D QA."""
from collections import defaultdict


moves = env["account.move"].search(
    [
        ("state", "=", "posted"),
        ("move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"]),
        ("invoice_date", "!=", False),
    ]
)

stats = defaultdict(lambda: defaultdict(int))
for move in moves:
    key = move.invoice_date.strftime("%Y-%m")
    stats[key][move.move_type] += 1

print("period,out_invoice,out_refund,in_invoice,in_refund,total,refunds")
for period in sorted(stats):
    item = stats[period]
    total = sum(item.values())
    refunds = item["out_refund"] + item["in_refund"]
    if total >= 10 or refunds:
        print(
            "%s,%s,%s,%s,%s,%s,%s"
            % (
                period,
                item["out_invoice"],
                item["out_refund"],
                item["in_invoice"],
                item["in_refund"],
                total,
                refunds,
            )
        )
