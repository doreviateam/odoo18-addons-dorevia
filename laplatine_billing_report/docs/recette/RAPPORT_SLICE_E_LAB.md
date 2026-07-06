# Rapport lab — slice E sécurité et clôture XLSX

**Référence** : `LP-FACT-REPORT-001`  
**Date** : 2026-07-06  
**Environnement** : `laplatine-odoo18-lab` / base `laplatine_prod` *(recette locale — pas la production réelle)*  
**Commit code recetté** : `ddad53b`  
**Production** : **STOP**

## Périmètre slice E

Robustesse et sécurité finale — **aucune modification** du métier ni de la présentation validés en slices B/C/D.

## Livrables techniques

| Élément | Statut |
|---------|--------|
| Menu, action et wizard limités à `account.group_account_invoice` | OK |
| Refus accès direct utilisateur non autorisé | OK |
| Domaine `company_id = env.company.id` (régression T06) | OK |
| Aucun `sudo()` dans le module métier | OK |
| Téléchargement impossible sans droit fonctionnel | OK |
| Deux feuilles présentes même si vide | OK |
| Message « Aucun document trouvé sur la période sélectionnée » | OK |
| Totaux à 0 document et montants nuls | OK |
| Textes Odoo via `write_string` (anti-formule Excel) | OK |
| Aucun `ir.attachment` permanent à la génération | OK |
| Mise en page slice D conservée | OK |

## Tests automatisés

**42 méthodes `test_*` — 0 échec** (voir inventaire détaillé dans [`RAPPORT_MOA_LP_FACT_REPORT_001.md`](RAPPORT_MOA_LP_FACT_REPORT_001.md) §5).

| Catégorie | Méthodes | IDs spec |
|-----------|:--------:|----------|
| Wizard / période | 4 | T01–T03 |
| Métier ventes | 12 | T04–T07, T09–T16 (T13 → T12) |
| Achats / transversal | 6 | T08, T17, T19, C01–C03 |
| Slice E hors sécurité | 6 | T18, T20, T21, E01, E02, E04 |
| Présentation slice D | 7 | D01–D07 |
| Sécurité slice E | 6 | T22 (×3), E05–E07 |
| Helper unitaire | 1 | hors matrice spec |

### Matrice T18 / T20 / T21 / T22

| ID | Scénario | Test automatisé |
|----|----------|-----------------|
| T18 | Aucun document sur la période | `test_t18_both_sheets_empty` |
| T20 | Ligne de synthèse | `test_t20_nombre_de_documents_label` |
| T21 | Injection Excel | `test_t21_excel_formula_injection_written_as_text` |
| T22 | Droits utilisateur (×3 méthodes) | `test_t22_*` dans `test_billing_report_security.py` |

### Matrice complémentaire slice E

| ID | Scénario | Test automatisé |
|----|----------|-----------------|
| E01 | Ventes vide, Achats avec données | `test_e01_ventes_empty_achats_with_data` |
| E02 | Achats vide, Ventes avec données | `test_e02_achats_empty_ventes_with_data` |
| E04 | Mise en page slice D sur export vide | `test_e04_slice_d_print_setup_preserved_on_empty_export` |
| E05 | Menu et droits wizard (profil autorisé) | `test_e05_invoice_user_can_access_menu_and_action` |
| E06 | Menu masqué (profil refusé) | `test_e06_denied_user_cannot_see_menu` |
| E07 | Génération fichier (profil autorisé) | `test_e07_invoice_user_can_generate_report` |

## Contrôles manuels lab (gate finale)

| Contrôle | Statut |
|----------|--------|
| Profil Facturation → menu visible, export OK | OK (smoke QA) |
| Profil sans Facturation → menu absent | OK (smoke QA) |
| Export période vide | OK (T18 + smoke QA) |
| Recette impression slice D | OK (GO_R06) |

## Verdict technique

> **GO technique slice E** — 42 méthodes de test, 0 échec.  
> **GO_MOA_LAB_LP_FACT_REPORT_001** — signé 06/07/2026.  
> **Production : STOP.**
