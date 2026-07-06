# Rapport MOA — Rapport de facturation La Platine

| Élément | Valeur |
|---------|--------|
| Référence | `LP-FACT-REPORT-001` |
| Module | `laplatine_billing_report` |
| Version | `18.0.1.0.0` |
| Date | 2026-07-06 |
| Environnement validé | Lab `http://127.0.0.1:18018` |
| Base PostgreSQL lab | `laplatine_prod` *(base locale de recette — **aucune action sur la production réelle**)* |
| Dépôt | `doreviateam/odoo18-addons-dorevia` — branche `main` |
| Spécification | [`SPECIFICATION_V1.md`](../../SPECIFICATION_V1.md) |
| Production réelle | **STOP** |

### Références Git (clôture lab)

| Rôle | Commit | Contenu |
|------|--------|---------|
| **Correctif fonctionnel recetté** | `ddad53b` | BUG-FACT-REPORT-D-001, test D07, code `billing_report_xlsx.py` |
| Slice E (sécurité) | `309253a` | Inclus dans l'ancêtre de `ddad53b` |
| Alignement rapports lab | `53e3e0f` | Références commit dans rapports slice D/E — documentaire uniquement |
| Rapport MOA initial | `9e022c7` | Première version de ce document |
| **Archivage GO MOA (ce document)** | *commit `docs(laplatine): archivage GO_MOA_LAB…` sur `main`* | Signature David Baron, réconciliation tests |

> **Référence code recetté** : `ddad53b`. Les commits documentaires ultérieurs ne modifient pas le comportement applicatif.

---

## 1. Objet du rapport

Ce document synthétise, pour la **maîtrise d'ouvrage (MOA)**, les résultats du développement et de la recette du module **Rapport de facturation** dans l'environnement lab.

Il vise à permettre :

1. la **validation fonctionnelle** du livrable lab ;
2. la décision distincte d'un éventuel **GO production** (hors périmètre de ce rapport).

---

## 2. Verdict MOA

| Périmètre | Verdict |
|-----------|---------|
| Développement lab slices A → E | **GO** — `GO_MOA_LAB_LP_FACT_REPORT_001` |
| Recette automatisée | **GO** — 42 méthodes de test, 0 échec |
| Recette visuelle impression (slice D) | **GO** — re-QA R06 |
| Smoke sécurité (slice E) | **GO** |
| Déploiement production | **Non accordé** — **Production STOP** |

> **Production : STOP** jusqu'à `GO_MOA_PROD_LP_FACT_REPORT_001` explicite.

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

| Slice | Commit | Contenu | Gate spec |
|-------|--------|---------|-----------|
| A | `2d7a14a` | Wizard, menu, M-1, binaire | T01–T03 |
| B | `4c3b134` | Onglet Ventes (11 col.) | T04–T16 |
| C | `6e35d70` | Onglet Achats (12 col.) | T08, T17, T19, C01–C03 |
| D | `4f45998` | Présentation XLSX, impression | D01–D06 |
| E | `309253a` | Sécurité, onglets vides, anti-formule | T18, T20–T22, E01–E07 |
| D-fix | `ddad53b` | Libellé totaux impression (BUG-D-001) | D07, GO_R06 |

**Aucune réouverture des slices A à E requise** pour la clôture lab.

---

## 5. Recette et preuves

### Tests automatisés lab — réconciliation du décompte

Odoo exécute **42 méthodes** `test_*` taguées `laplatine_billing_report` :

```
0 failed, 0 error(s) of 42 tests when loading database 'laplatine_prod'
```

Ce total est le nombre de **méthodes de test Python**, pas le nombre d'identifiants spec distincts.

| Catégorie | Méthodes | Identifiants spec couverts | Remarque |
|-----------|:--------:|----------------------------|----------|
| Wizard / période | 4 | T01, T02, T03 | T01 scindé en 2 cas (M-1 calendaire + janvier) |
| Métier ventes | 12 | T04–T07, T09–T12, T14–T16 | T13 volontairement absent (couvert par T12, cf. spec) |
| Achats / transversal | 6 | T08, T17, T19, C01–C03 | |
| Slice E (hors sécurité) | 6 | T18, T20, T21, E01, E02, E04 | E03 non implémenté (hors périmètre V1) |
| Présentation slice D | 7 | D01–D07 | D07 ajouté avec correctif R06 |
| Sécurité slice E | 6 | T22, E05, E06, E07 | T22 scindé en 3 méthodes (création, génération, pas d'attachment) |
| Helper unitaire | 1 | — | `test_report_sign_and_type_labels` (hors matrice Txx) |
| **Total** | **42** | **37 identifiants spec** | 5 méthodes supplémentaires = scissions T01, T06 (×2), T22 (×3) − helper |

#### Inventaire des 42 méthodes

| # | Méthode | ID spec |
|---|---------|---------|
| 1–2 | `test_t01_default_period_*` (×2) | T01 |
| 3 | `test_t02_invalid_period_raises_user_error` | T02 |
| 4 | `test_t03_custom_period_generates_downloadable_xlsx` | T03 |
| 5 | `test_t04_posted_customer_invoice_in_ventes_sheet` | T04 |
| 6 | `test_t05_draft_and_cancelled_excluded` | T05 |
| 7–8 | `test_t06_*` (×2) | T06 |
| 9 | `test_t07_invoice_date_outside_period_excluded` | T07 |
| 10 | `test_t08_posted_vendor_invoice_on_achats_sheet` | T08 |
| 11 | `test_t09_foreign_currency_blocked` | T09 |
| 12 | `test_t10_customer_invoice_positive_amounts` | T10 |
| 13 | `test_t11_customer_refund_negative_amounts` | T11 |
| 14 | `test_t12_totals_algebraic_sum` | T12 (+ T13) |
| 15 | `test_t14_payment_state_uses_odoo_label` | T14 |
| 16 | `test_t15_settled_amount_formula` | T15 |
| 17 | `test_t16_ventes_column_order` | T16 |
| 18 | `test_t17_two_sheets_always_present` | T17 |
| 19 | `test_t18_both_sheets_empty` | T18 |
| 20 | `test_t19_filename_contains_period_dates` | T19 |
| 21 | `test_t20_nombre_de_documents_label` | T20 |
| 22 | `test_t21_excel_formula_injection_written_as_text` | T21 |
| 23–25 | `test_t22_*` (×3) | T22 |
| 26–28 | `test_c01` … `test_c03` | C01–C03 |
| 29–35 | `test_d01` … `test_d07` | D01–D07 |
| 36–38 | `test_e01`, `test_e02`, `test_e04` | E01, E02, E04 |
| 39–41 | `test_e05` … `test_e07` | E05–E07 |
| 42 | `test_report_sign_and_type_labels` | helper |

Commande de reproduction :

```bash
docker compose run --rm odoo odoo --config=/etc/odoo/odoo.conf \
  --database=laplatine_prod -u laplatine_billing_report \
  --test-enable --test-tags=laplatine_billing_report --stop-after-init
```

### Recette visuelle QA

| Rapport | Verdict |
|---------|---------|
| [`recette_qa/SLICE-D-IMPRESSION/RAPPORT_QA_SLICE_D_IMPRESSION.md`](../../recette_qa/SLICE-D-IMPRESSION/RAPPORT_QA_SLICE_D_IMPRESSION.md) | NO_GO initial (R06) |
| [`recette_qa/SLICE-D-IMPRESSION/REQA-R06-20260706_140940/RAPPORT_QA_R06_RETEST.md`](../../recette_qa/SLICE-D-IMPRESSION/REQA-R06-20260706_140940/RAPPORT_QA_R06_RETEST.md) | **GO_R06** |

Jeu principal : **juin 2026** (44 ventes / 47 achats). Annexe avoirs : **février 2026**.

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

### Assistant — validé lab

| Critère | Lab |
|---------|-----|
| Menu ouvre un wizard | OK |
| M-1 par défaut | OK |
| Dates modifiables | OK |
| Période incorrecte refusée | OK |
| Devise étrangère refusée | OK |

### Fichier Excel — validé lab

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

### Impression — validé lab (LibreOffice)

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

## 8. Prérequis obligatoires avant GO production

Les contrôles ci-dessous ne sont **pas** des réserves optionnelles : ils constituent les **gates bloquantes** avant `GO_MOA_PROD_LP_FACT_REPORT_001`.

| # | Prérequis | Responsable | Statut |
|---|-----------|-------------|--------|
| P1 | Ouverture et aperçu impression du fichier `.xlsx` dans **Excel natif** (Windows ou Mac) — vérifier largeurs, pagination, zone d'impression et libellé de synthèse | MOA / utilisatrices | ☐ À faire |
| P2 | Validation métier par **Véréna ou Ethel** sur un **export réel M-1** (contenu, montants, lisibilité cabinet) | MOA | ☐ À faire |
| P3 | Décision MOA production explicite (`GO_MOA_PROD_LP_FACT_REPORT_001`) | David Baron | ☐ En attente P1 + P2 |

> LibreOffice valide la mise en page en lab ; le document final est destiné à être transmis sous Excel. La validation native (P1) évite les écarts de rendu entre moteurs.

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
| ☑ **GO_MOA_LAB_LP_FACT_REPORT_001** | David Baron | 06/07/2026 | Développement et recette lab acceptés. Réserves documentaires corrigées (décompte tests, commits). Production STOP. |
| ☐ **NO_GO** — ajustements requis | | | |

### Production *(décision distincte)*

| Décision | Signataire | Date | Commentaire |
|----------|------------|------|-------------|
| ☐ **GO_MOA_PROD_LP_FACT_REPORT_001** | | | |
| ☑ **Report / refus** | David Baron | 06/07/2026 | En attente validation Véréna/Ethel sur export M-1 réel et vérification Excel natif (prérequis P1–P2). |

---

## 11. Conclusion

Le module `laplatine_billing_report` répond aux arbitrages MOA de `SPECIFICATION_V1.md` dans l'environnement lab.

> **GO clôture lab** — sans réouverture du développement slices A à E.  
> **GO production non accordé — Production STOP.**
