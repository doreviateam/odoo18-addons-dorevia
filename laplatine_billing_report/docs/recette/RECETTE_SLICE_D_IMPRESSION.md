# Recette manuelle slice D — impression XLSX

**Référence** : `LP-FACT-REPORT-001` — slice D  
**Module** : `laplatine_billing_report`  
**Environnement** : lab uniquement (`http://127.0.0.1:18018`, base `laplatine_prod`)  
**Production** : **STOP**

## Objectif

Valider la présentation et l'impression du rapport sur un jeu de données représentatif (≥ 25–50 documents par onglet si possible), conformément au §18 de `SPECIFICATION_V1.md`.

## Préparation du fichier test

### Option A — période réelle M-1 (recommandée MOA)

1. Se connecter au **lab** avec un compte Facturation (`account.group_account_invoice`).
2. Ouvrir **Facturation → La Platine → Rapport de facturation**.
3. Conserver le mois M-1 proposé ou choisir une période riche en factures et avoirs.
4. Générer le fichier Excel.

### Option B — script lab (volume contrôlé)

Depuis le conteneur Odoo lab :

```bash
docker compose exec odoo odoo shell \
  --config=/etc/odoo/odoo.conf \
  --database=laplatine_prod
```

Puis exécuter le script :

```python
exec(open("/mnt/extra-addons/odoo18-addons-dorevia/laplatine_billing_report/scripts/generate_sample_report_slice_d.py").read())
```

Le fichier est écrit dans `recette_qa/SLICE-D-IMPRESSION/` (dans le dépôt addons).

## Grille de recette manuelle

| # | Critère | Ventes | Achats | OK |
|---|---------|--------|--------|-----|
| R01 | Fichier `.xlsx` s'ouvre sans erreur dans Excel / LibreOffice | ☐ | ☐ | |
| R02 | Titre, société, période et date de génération visibles en tête | ☐ | ☐ | |
| R03 | En-têtes colonnes ligne 6 — ordre MOA validé | ☐ | ☐ | |
| R04 | Aucune colonne tronquée (`###`) sur les montants | ☐ | ☐ | |
| R05 | Montants négatifs (avoirs) lisibles | ☐ | ☐ | |
| R06 | Ligne **Nombre de documents** et totaux en bas de tableau | ☐ | ☐ | |
| R07 | Aperçu avant impression **A4 paysage** | ☐ | ☐ | |
| R08 | Largeur = **1 page** sans réglage manuel | ☐ | ☐ | |
| R09 | Lignes 1 à 6 répétées sur les pages suivantes | ☐ | ☐ | |
| R10 | Totaux visibles sur la dernière page | ☐ | ☐ | |
| R11 | Pied de page `Page X / Y` centré | ☐ | ☐ | |
| R12 | Volets figés sous la ligne d'en-têtes (navigation) | ☐ | ☐ | |
| R13 | Nom fichier = `Rapport_facturation_La_Platine_YYYY-MM-DD_YYYY-MM-DD.xlsx` | ☐ | — | |

## Preuves attendues

Joindre au dossier `recette_qa/SLICE-D-IMPRESSION/` :

- capture ou PDF de l'**aperçu avant impression** (onglet Ventes, ≥ 2 pages si possible) ;
- capture ou PDF de l'**aperçu avant impression** (onglet Achats) ;
- copie du fichier `.xlsx` généré.

## Tests automatisés associés (gate technique)

| ID | Couverture |
|----|------------|
| T01–T19, C01–C03 | Régression métier slices A–C |
| D01–D06 | Propriétés XLSX et impression vérifiables (openpyxl) |

## Verdict

| Statut | Signataire | Date |
|--------|------------|------|
| ☐ GO recette slice D | | |
| ☐ Ajustements requis | | |
