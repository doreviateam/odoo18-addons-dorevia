# Rapport lab — slice E sécurité et clôture XLSX

**Référence** : `LP-FACT-REPORT-001`  
**Date** : 2026-07-06  
**Environnement** : `laplatine-odoo18-lab` / base `laplatine_prod`  
**Commit** : `b3a20d7`  
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

| Plage | Résultat |
|-------|----------|
| T01–T19, C01–C03 | **29/29 verts** (non-régression) |
| D01–D06 (présentation XLSX) | **6/6 verts** (non-régression) |
| D07 (libellé totaux R06) | **1/1 vert** |
| T18, T20, T21, T22 | **4/4 verts** |
| E01–E07 (slice E) | **7/7 verts** |

**Total gate slice E** : **42/42 verts**

### Matrice T18 / T20 / T21 / T22

| ID | Scénario | Attendu | Test automatisé |
|----|----------|---------|-----------------|
| T18 | Aucun document sur la période | Deux feuilles, 11/12 colonnes, message vide, 0 doc, montants à 0, fichier ouvrable | `test_t18_both_sheets_empty` |
| T20 | Ligne de synthèse | Libellé exact « Nombre de documents » Ventes et Achats | `test_t20_nombre_de_documents_label` |
| T21 | Injection Excel (`=1+1`, `+CMD`, `-TEST`, `@REF`) | Cellules texte littérales, `data_type != 'f'` | `test_t21_excel_formula_injection_written_as_text` |
| T22 | Droits utilisateur | Groupe Facturation requis ; refus création/génération/lecture ; pas d'`ir.attachment` | `test_t22_*` dans `test_billing_report_security.py` |

### Matrice complémentaire slice E

| ID | Scénario | Test automatisé |
|----|----------|-----------------|
| E01 | Ventes vide, Achats avec données | `test_e01_ventes_empty_achats_with_data` |
| E02 | Achats vide, Ventes avec données | `test_e02_achats_empty_ventes_with_data` |
| E04 | Mise en page slice D sur export vide | `test_e04_slice_d_print_setup_preserved_on_empty_export` |
| E05 | Menu et action visibles (profil autorisé) | `test_e05_invoice_user_can_access_menu_and_action` |
| E06 | Menu masqué (profil refusé) | `test_e06_denied_user_cannot_see_menu` |
| E07 | Génération fichier (profil autorisé) | `test_e07_invoice_user_can_generate_report` |

## Contrôles manuels lab (gate finale)

| Contrôle | Statut MOA |
|----------|------------|
| Connexion profil Facturation → menu visible, export OK | OK (smoke QA) |
| Connexion profil sans Facturation → menu absent | OK (smoke QA) |
| Export période sans ventes | OK (auto E01) |
| Export période sans achats | OK (auto E02) |
| Export période totalement vide | OK (auto T18 + smoke QA) |
| Ouverture XLSX sans alerte Excel | OK (QA LibreOffice) |
| Recette impression slice D (§18) | OK (GO_R06) |

## Verdict technique

> **GO technique slice E** — gate automatisée validée (42 tests).  
> **GO recette visuelle slice D** — re-QA R06 validée.  
> **Clôture lab LP-FACT-REPORT-001** : GO technique ; signature MOA production en attente.  
> **Production : STOP.**
