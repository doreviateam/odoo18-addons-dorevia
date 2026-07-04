# odoo18-addons-dorevia

**Dépôt GitHub** : [doreviateam/odoo18-addons-dorevia](https://github.com/doreviateam/odoo18-addons-dorevia)

## Objet

Répertoire **addons Odoo 18 Community Edition** pour modules Dorevia / clients (ex. La Platine), versionnés et publiés comme dépôt **autonome**, sur le même principe que [odoo19-addons-dorevia](https://github.com/doreviateam/odoo19-addons-dorevia).

## Modules présents

| Module | Description courte |
|--------|-------------------|
| [laplatine_invoice_payment_info](laplatine_invoice_payment_info/README.md) | Libellé « Info facture » sur règlement + PDF facture (La Platine) |
| [laplatine_customer_statement](laplatine_customer_statement/README.md) | État de facturation client XLSX — synthèse, statuts retard (La Platine) |

## Configuration locale

Exemple de `addons_path` : voir [`odoo.conf.example`](odoo.conf.example) à la racine de ce dépôt.

## Publier sur GitHub (comme pour odoo19-addons-dorevia)

1. Créer sur GitHub un dépôt vide **`doreviateam/odoo18-addons-dorevia`** (sans README licence si vous poussez depuis ce clone).

2. Dans ce répertoire :

```bash
cd odoo18-addons-dorevia
git init
git checkout -b main
git add .
git commit -m "Initial commit: addons Odoo 18 Dorevia"
git remote add origin git@github.com:doreviateam/odoo18-addons-dorevia.git
git push -u origin main
```

Mises à jour ultérieures :

```bash
git add -A && git commit -m "…" && git push origin main
```

Si le dépôt Git existe déjà avec historique, utiliser `git remote -v` puis `git pull origin main --rebase` avant le premier push si besoin.

## Version cible

- **Odoo** : 18.0 (Community Edition)
