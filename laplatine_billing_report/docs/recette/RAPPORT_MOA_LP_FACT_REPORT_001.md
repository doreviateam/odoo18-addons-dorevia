# Rapport MOA — Rapport de facturation La Platine

| Élément | Valeur |
|---------|--------|
| Référence | `LP-FACT-REPORT-001` |
| Module | `laplatine_billing_report` |
| Version | `18.0.1.0.0` |
| Date | 2026-07-06 |
| Environnement validé | Lab `http://127.0.0.1:18018` — base `laplatine_prod` |
| Dépôt | `doreviateam/odoo18-addons-dorevia` — branche `main` |
| Commit de clôture lab | `ddad53b` (poussé `53e3e0f`) |
| Spécification | [`SPECIFICATION_V1.md`](../../SPECIFICATION_V1.md) |
| Production | **STOP** |

---

## 1. Objet du rapport

Ce document synthétise, pour la **maîtrise d'ouvrage (MOA)**, les résultats du développement et de la recette du module **Rapport de facturation** dans l'environnement lab.

Il vise à permettre :

1. la **validation fonctionnelle** du livrable lab ;
2. la décision distincte d'un éventuel **GO production** (hors périmètre de ce rapport).

---

## 2. Verdict proposé

| Périmètre | Verdict technique | Décision MOA attendue |
|-----------|-------------------|------------------------|
| Développement lab slices A → E | **GO** | ☐ `GO_MOA_LAB_LP_FACT_REPORT_001` |
| Recette automatisée (42 tests) | **GO** | — |
| Recette visuelle impression (slice D) | **GO** (re-QA R06) | — |
| Smoke sécurité (slice E) | **GO** | — |
| Déploiement production | **Non évalué** | ☐ `GO_MOA_PROD_LP_FACT_REPORT_001` *(distinct, explicite)* |

> **Production : STOP** jusqu'à signature MOA production explicite.

---

## 3. Livrable fonctionnel

### Accès utilisateur

**Facturation → La Platine → Rapport de facturation**

| Élément | Valeur MOA |
|---------|------------|
| Profil autorisé | Groupe **Facturation** (`account.group_account_invoice`) |
| Action | Assistant avec période **M-1** par défaut, dates modifiables |
| Sortie | Fichier `.xlsx` téléchargé (2 onglets **Ventes** / **Achats**) |
| Stockage | Champs binaires du wizard — **aucune pièce jointe permanente** |

### Contenu du fichier

| Règle MOA | Implémentation |
|-----------|----------------|
| Une ligne par document (facture ou avoir) | OK |
| 11 colonnes Ventes / 12 colonnes Achats — ordre §11/§12 | OK |
| Colonne **Type** (Facture / Avoir) | OK |
| Avoirs en montants **négatifs** | OK |
| Totaux algébriques | OK |
| Libellés **Montant réglé / soldé** et **Reste à payer / solder** | OK |
| Filtre `invoice_date`, société active uniquement | OK |
| Blocage devise ≠ société | OK |
| Onglet vide : message + totaux à 0 | OK |
| Nom fichier `Rapport_facturation_La_Platine_YYYY-MM-DD_YYYY-MM-DD.xlsx` | OK |

### Impression (cabinet comptable)

| Critère | Résultat |
|---------|----------|
| A4 paysage, 1 page en largeur | OK (QA LibreOffice) |
| En-têtes lignes 1–6 répétés sur chaque page | OK |
| Volets figés sous la ligne 6 | OK |
| Pied de page `Page X / Y` | OK |
| Ligne **Nombre de documents** + totaux lisibles | OK (après correctif R06) |
| Montants et avoirs lisibles (jeu juin 2026 + annexe février) | OK |

---

## 4. Historique de développement (slices)

| Slice | Commit | Contenu | Gate |
|-------|--------|---------|------|
| A | `2d7a14a` | Wizard, menu, M-1, binaire | T01–T03 |
| B | `4c3b134` | Onglet Ventes (11 col.) | T04–T16 |
| C | `6e35d70` | Onglet Achats (12 col.) | T08, T17, T19, C01–C03 |
| D | `4f45998` | Présentation XLSX, impression | D01–D06 |
| E | `309253a` | Sécurité, onglets vides, anti-formule | T18, T20–T22, E01–E07 |
| D-fix | `ddad53b` | Libellé totaux impression (BUG-D-001) | D07, GO_R06 |

---

## 5. Recette et preuves

### Tests automatisés lab

**42/42 verts** (`laplatine_billing_report`)

| Plage | Tests |
|-------|-------|
| Métier slices A–C | T01–T19, C01–C03 (29) |
| Présentation slice D | D01–D07 (7) |
| Sécurité slice E | T18, T20–T22, E01–E07 (6) |

### Recette visuelle QA

| Rapport | Verdict |
|---------|---------|
| [`recette_qa/SLICE-D-IMPRESSION/RAPPORT_QA_SLICE_D_IMPRESSION.md`](../../recette_qa/SLICE-D-IMPRESSION/RAPPORT_QA_SLICE_D_IMPRESSION.md) | NO_GO initial (R06) |
| [`recette_qa/SLICE-D-IMPRESSION/REQA-R06-20260706_140940/RAPPORT_QA_R06_RETEST.md`](../../recette_qa/SLICE-D-IMPRESSION/REQA-R06-20260706_140940/RAPPORT_QA_R06_RETEST.md) | **GO_R06** |

Jeu principal contrôlé : **juin 2026** (44 ventes / 47 achats). Annexe avoirs : **février 2026**.

### Rapports techniques lab

| Document | Rôle |
|----------|------|
| [`RAPPORT_SLICE_D_LAB.md`](RAPPORT_SLICE_D_LAB.md) | Gate technique + recette slice D |
| [`RAPPORT_SLICE_E_LAB.md`](RAPPORT_SLICE_E_LAB.md) | Gate technique slice E |
| [`RECETTE_SLICE_D_IMPRESSION.md`](RECETTE_SLICE_D_IMPRESSION.md) | Grille R01–R13 |

---

## 6. Anomalie traitée en recette

### BUG-FACT-REPORT-D-001

| Champ | Détail |
|-------|--------|
| Symptôme | Libellé **Nombre de documents** tronqué en `e documents` à l'impression |
| Cause | Colonne A trop étroite + alignement à droite |
| Correctif | Colonne A élargie (22), libellé aligné à gauche (`ddad53b`) |
| Statut | **Clos** — GO_R06 |

---

## 7. Grille critères d'acceptation MOA (§18)

### Assistant

| Critère | Lab |
|---------|-----|
| Menu ouvre un wizard | OK |
| M-1 par défaut | OK |
| Dates modifiables | OK |
| Période incorrecte refusée | OK |
| Devise étrangère refusée | OK |

### Fichier Excel

| Critère | Lab |
|---------|-----|
| 2 onglets Ventes / Achats | OK |
| Une ligne par document | OK |
| Brouillons / annulées exclus | OK |
| Type Facture / Avoir | OK |
| Avoirs négatifs, totaux algébriques | OK |
| Onglet vide avec message | OK |
| Colonnes conformes §11 / §12 | OK |
| Pas d'`ir.attachment` permanent | OK |

### Impression

| Critère | Lab |
|---------|-----|
| A4 paysage, 1 page largeur | OK |
| `repeat_rows` 1–6 | OK |
| Volets figés | OK |
| Zone impression jusqu'aux totaux | OK |
| Numéros de page | OK |
| Jeu représentatif ≥ 25 docs | OK (juin 2026) |
| Aperçu impression lisible | OK (LibreOffice PDF) |

---

## 8. Points d'attention MOA

1. **Excel desktop natif** : la recette visuelle a été réalisée avec **LibreOffice** (PDF). Une validation rapide sur Excel Windows/Mac par les utilisatrices reste recommandée avant production.
2. **Validation métier cabinet** : la spec prévoit une validation par **Véréna / Ethel** sur un export M-1 représentatif (§21).
3. **Production** : aucun déploiement n'a été effectué ; le module n'est pas installé en production à ce stade.
4. **Complémentarité** : ce module ne remplace pas [`laplatine_customer_statement`](../../../laplatine_customer_statement/README.md) (état par client).

---

## 9. Utilisation attendue (rappel)

1. Se connecter avec un compte **Facturation**.
2. Ouvrir **Facturation → La Platine → Rapport de facturation**.
3. Vérifier la période (M-1 proposé par défaut).
4. Cliquer **Générer le rapport Excel**.
5. Transmettre le fichier `.xlsx` au cabinet comptable.

---

## 10. Décision MOA

### Clôture lab

| Décision | Signataire | Date | Commentaire |
|----------|------------|------|-------------|
| ☐ **GO_MOA_LAB_LP_FACT_REPORT_001** | | | Développement et recette lab acceptés |
| ☐ **NO_GO** — ajustements requis | | | Préciser : |

### Production *(décision distincte)*

| Décision | Signataire | Date | Commentaire |
|----------|------------|------|-------------|
| ☐ **GO_MOA_PROD_LP_FACT_REPORT_001** | | | Autorise déploiement production |
| ☐ **Report / refus** | | | |

---

## 11. Conclusion

Le module `laplatine_billing_report` répond aux arbitrages MOA de `SPECIFICATION_V1.md` dans l'environnement lab :

- extraction globale Ventes / Achats conforme à l'extraction mensuelle de référence ;
- présentation et impression validées après correction du libellé de synthèse ;
- sécurité et robustesse (droits, onglets vides, anti-formule Excel) validées.

**Recommandation équipe technique** : **GO clôture lab** — décision MOA production à traiter séparément après validation utilisatrices sur un export réel M-1.

**Production : STOP.**
