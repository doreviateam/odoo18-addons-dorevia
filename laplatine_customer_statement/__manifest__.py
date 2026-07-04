{
    "name": "La Platine - État de facturation client",
    "summary": "Génère un état mensuel de facturation client au format XLSX",
    "version": "18.0.1.1.1",
    "category": "Accounting",
    "author": "Dorevia",
    "license": "LGPL-3",
    "depends": ["account"],
    "external_dependencies": {
        "python": ["xlsxwriter"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/customer_statement_wizard_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
