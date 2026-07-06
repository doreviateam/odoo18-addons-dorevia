{
    "name": "La Platine - Rapport de facturation",
    "summary": "Rapport mensuel Ventes / Achats XLSX pour le cabinet comptable",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "author": "Dorevia",
    "license": "LGPL-3",
    "depends": ["account"],
    "external_dependencies": {
        "python": ["xlsxwriter"],
    },
    "data": [
        "security/ir.model.access.csv",
        "wizard/billing_report_wizard_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": False,
}
