# laplatine_billing_report

Module Odoo 18 CE — **Rapport de facturation Ventes / Achats** pour la SARL La Platine.

## Statut

| Élément | Statut |
|---------|--------|
| Référence | `LP-FACT-REPORT-001` |
| Version cible | `18.0.1.0.0` |
| Spécification | [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md) — **MOA validée** |
| Développement lab | **Clôturé** — slices A → E, commit `ddad53b` |
| Recette lab | **GO technique** — 42 tests + QA visuelle (GO_R06) |
| Rapport MOA | [`docs/recette/RAPPORT_MOA_LP_FACT_REPORT_001.md`](docs/recette/RAPPORT_MOA_LP_FACT_REPORT_001.md) |
| Production | **STOP** — GO MOA production distinct requis |

## Objectif

Générer un fichier Excel `.xlsx` (onglets **Ventes** et **Achats**) pour transmission au cabinet comptable, depuis :

**Facturation → La Platine → Rapport de facturation**

## Complémentarité

| Module | Usage |
|--------|--------|
| [`laplatine_customer_statement`](../laplatine_customer_statement/README.md) | État par **client** (fiche partenaire) |
| **laplatine_billing_report** | Extraction **globale** ventes + achats |

## Documentation

- Spécification V1 : [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md)
- Recette impression slice D : [`docs/recette/RECETTE_SLICE_D_IMPRESSION.md`](docs/recette/RECETTE_SLICE_D_IMPRESSION.md)
- Rapport MOA clôture lab : [`docs/recette/RAPPORT_MOA_LP_FACT_REPORT_001.md`](docs/recette/RAPPORT_MOA_LP_FACT_REPORT_001.md)
