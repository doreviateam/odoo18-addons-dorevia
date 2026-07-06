# Rapport lab — slice D présentation XLSX

**Référence** : `LP-FACT-REPORT-001`  
**Date** : 2026-07-06  
**Environnement** : `laplatine-odoo18-lab` / base `laplatine_prod`  
**Commit** : *(à compléter après push)*  
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

## Tests automatisés

| Plage | Résultat |
|-------|----------|
| T01–T19, C01–C03 | **29/29 verts** |
| D01–D06 (présentation XLSX) | **6/6 verts** |

### Matrice D01–D06

| ID | Scénario | Attendu |
|----|----------|---------|
| D01 | Impression Ventes | Paysage, A4, fit 1 page largeur, titres 1:6 |
| D02 | Impression Achats | Idem |
| D03 | Bloc méta | Titre, période, date génération |
| D04 | Ligne 6 | En-têtes MOA Ventes et Achats |
| D05 | Largeurs colonnes | Colonnes dimensionnées (pas de défaut Excel) |
| D06 | Autofiltre + totaux | Filtre ligne 6, totaux dans zone impression |

## Recette manuelle §18

Grille complète : [`docs/recette/RECETTE_SLICE_D_IMPRESSION.md`](../docs/recette/RECETTE_SLICE_D_IMPRESSION.md)

| Étape | Statut MOA |
|-------|------------|
| Génération fichier M-1 représentatif (≥ 25 docs si possible) | ☐ À faire |
| Aperçu impression Ventes (multi-pages) | ☐ À faire |
| Aperçu impression Achats | ☐ À faire |
| Captures / PDF joints dans `recette_qa/SLICE-D-IMPRESSION/` | ☐ À faire |

Script lab : `scripts/generate_sample_report_slice_d.py`

## Verdict technique

> **GO technique slice D** — gate automatisée validée.  
> **Recette manuelle MOA** en attente de captures d'aperçu impression.
