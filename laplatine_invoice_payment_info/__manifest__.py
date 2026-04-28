{
    "name": "La Platine - Invoice Payment Display Info",
    "summary": "Affiche un mode de paiement client sur les factures payees",
    "version": "18.0.1.3.0",
    "category": "Accounting",
    "author": "Dorevia",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "views/account_payment_views.xml",
        "views/account_payment_register_views.xml",
        "views/report_layout.xml",
        "views/report_invoice.xml",
    ],
    "assets": {
        "web.report_assets_pdf": [
            "laplatine_invoice_payment_info/static/src/scss/report_invoice_logo.scss",
        ],
    },
    "installable": True,
    "application": False,
}
