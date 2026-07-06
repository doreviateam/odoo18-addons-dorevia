# Rapport lab — slice D présentation XLSX

**Référence** : `LP-FACT-REPORT-001`  
**Date** : 2026-07-06  
**Environnement** : `laplatine-odoo18-lab` / base `laplatine_prod`  
**Commit** : `ddad53b`  
**Production** : **STOP**

## Périmètre slice D

Finition XLSX uniquement — **aucune modification** des domaines, colonnes métier, signes ou formules des slices B/C.

## Livrables techniques

| Élément | Statut |
|---------|--------|
| Présentation homogène Ventes / Achats | OK |
| Largeurs colonnes et hauteurs de lignes | OK |
| Formats dates, montants, textes | OK |
| En-têtes et totaux distincts (fond gris totaux) | OK |
| Montants négatifs en rouge | OK |
| Volets figés + autofiltre ligne 6 | OK |
| A4 paysage, 1 page largeur | OK |
| `repeat_rows` lignes 1–6 | OK |
| Marges, zone impression, pied de page | OK |
| Nom fichier avec période | OK (régression T19) |
| Libellé **Nombre de documents** lisible à l'impression | OK (BUG-FACT-REPORT-D-001) |

## Tests automatisés

| Plage | Résultat |
|-------|----------|
| T01–T19, C01–C03 | **29/29 verts** |
| D01–D07 (présentation XLSX) | **7/7 verts** |

### Matrice D01–D07

| ID | Scénario | Attendu |
|----|----------|---------|
| D01 | Impression Ventes | Paysage, A4, fit 1 page largeur, titres 1:6 |
| D02 | Impression Achats | Idem |
| D03 | Bloc méta | Titre, période, date génération |
| D04 | Ligne 6 | En-têtes MOA Ventes et Achats |
| D05 | Largeurs colonnes | Colonnes dimensionnées (pas de défaut Excel) |
| D06 | Autofiltre + totaux | Filtre ligne 6, totaux dans zone impression |
| D07 | Libellé totaux | Colonne A ≥ longueur « Nombre de documents » |

## Recette visuelle QA

| Rapport | Verdict |
|---------|---------|
| [`recette_qa/SLICE-D-IMPRESSION/RAPPORT_QA_SLICE_D_IMPRESSION.md`](../../recette_qa/SLICE-D-IMPRESSION/RAPPORT_QA_SLICE_D_IMPRESSION.md) | NO_GO initial (R06 KO) |
| [`recette_qa/SLICE-D-IMPRESSION/REQA-R06-20260706_140940/RAPPORT_QA_R06_RETEST.md`](../../recette_qa/SLICE-D-IMPRESSION/REQA-R06-20260706_140940/RAPPORT_QA_R06_RETEST.md) | **GO_R06** |

Grille complète : [`docs/recette/RECETTE_SLICE_D_IMPRESSION.md`](RECETTE_SLICE_D_IMPRESSION.md)

| Étape | Statut |
|-------|--------|
| Génération fichier M-1 représentatif (juin 2026, 44/47 docs) | OK |
| Aperçu impression Ventes / Achats (LibreOffice PDF) | OK |
| R06 libellé totaux lisible | OK (re-QA) |
| Preuves dans `recette_qa/SLICE-D-IMPRESSION/` | OK |

## Correctif BUG-FACT-REPORT-D-001

Colonne A élargie (10 → 22), libellé de synthèse aligné à gauche avec `shrink: False`.

## Verdict

> **GO technique slice D** — gate automatisée et recette visuelle validées.  
> **Production : STOP.**
