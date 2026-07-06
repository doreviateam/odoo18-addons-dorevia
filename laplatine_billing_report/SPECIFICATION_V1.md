# Spécification fonctionnelle V1 — `laplatine_billing_report`

## 1. Identification

| Élément | Valeur |
|---------|--------|
| Référence cadrage | `LP-FACT-REPORT-001` |
| Projet | SARL La Platine — Odoo 18 Community |
| Module technique | `laplatine_billing_report` |
| Emplacement | `addons/odoo18-addons-dorevia/laplatine_billing_report` |
| Nom fonctionnel | Rapport de facturation Ventes / Achats |
| Version cible V1 | `18.0.1.0.0` |
| Statut | **Spécification MOA validée — développement lab autorisé** |
| Développement lab | **Autorisé** — slices A → E |
| Production | **STOP** — aucune action sans GO explicite |
| Utilisatrices cibles | Véréna, Ethel, direction |
| Livrable principal | Fichier Excel `.xlsx` (2 onglets) |

### Complémentarité avec `laplatine_customer_statement`

| Module | Usage |
|--------|--------|
| `laplatine_customer_statement` | État **par client** — analyse individuelle, fiche partenaire |
| `laplatine_billing_report` | Extraction **globale** ventes + achats La Platine — transmission cabinet comptable |

Les deux modules restent **distincts** et **indépendants**.

---

## 2. Contexte et objectif

Chaque mois, Véréna ou Ethel prépare un rapport de facturation pour le cabinet comptable.
Le besoin est de fiabiliser et simplifier cette extraction depuis Odoo, sans retraitement manuel important.

Ce rapport est une **restitution comptable simple**, exhaustive et directement transmissible.
Ce n’est **pas** un outil d’analyse de gestion (évolution, marges, graphiques, etc.).

**Objectif V1** : permettre de générer un fichier Excel consolidant, sur une période donnée :

- les factures et avoirs **clients** comptabilisés ;
- les factures et avoirs **fournisseurs** comptabilisés ;

immédiatement exploitable et imprimable.

### 2.1 Référence fonctionnelle — extraction existante (arbitrage MOA 2026-07-06)

La capture de l’extraction mensuelle actuellement réalisée dans Odoo a été examinée par la MOA.

Elle confirme que le rapport destiné au cabinet comptable doit rester une **restitution simple,
lisible et proche de la liste standard des factures**. Elle constitue la **référence fonctionnelle
de base** pour l’onglet **Ventes**.

Le futur rapport **n’est pas** une simple copie de la vue Odoo actuelle. Il doit :

- conserver la simplicité de l’extraction mensuelle existante ;
- faire apparaître explicitement les **factures** et les **avoirs** ;
- restituer correctement l’**incidence négative** des avoirs sur les totaux ;
- permettre de connaître leur **état de règlement ou de solde**.

Les colonnes et leur ordre (§11 et §12) sont **validés MOA** sur cette base.
Les améliorations relatives aux avoirs et à leur règlement sont **confirmées**.

**Colonnes retirées en V1** (non observées dans le rapport cabinet) :

| Onglet | Colonne retirée | Réintégration possible |
|--------|-----------------|------------------------|
| Ventes | Référence / Origine | Uniquement si besoin confirmé par Véréna ou Ethel |
| Achats | Origine | Idem |

---

## 3. Navigation et parcours utilisateur

### 3.1 Arborescence cible

```text
Facturation
└── La Platine
    └── Rapport de facturation        ← V1
```

- Parent technique menu : `account.menu_finance`
- Créer le menu parent **La Platine** si absent
- **Ne pas** créer de menu `Analyse de facturation` en V1 (ticket séparé)

### 3.2 Parcours

1. L’utilisateur ouvre **Facturation → La Platine → Rapport de facturation**.
2. Un **assistant** (wizard) s’ouvre.
3. Les dates **mois M-1 complet** sont proposées par défaut.
4. L’utilisateur peut modifier librement la période (mois, trimestre, année, plage personnalisée).
5. Clic sur **Générer le rapport Excel**.
6. Odoo génère et télécharge un fichier `.xlsx`.

### 3.3 Période par défaut (M-1)

Exemple si date du jour = 6 juillet 2026 :

| Champ | Valeur |
|-------|--------|
| Date de début | 1er juin 2026 |
| Date de fin | 30 juin 2026 |

Algorithme :

```python
today = fields.Date.context_today(wizard)
date_from = (today.replace(day=1) - relativedelta(months=1))
date_to = today.replace(day=1) - relativedelta(days=1)
```

---

## 4. Assistant de génération

### 4.1 Modèle

| Propriété | Valeur |
|-----------|--------|
| Modèle technique | `laplatine.billing.report.wizard` |
| Type | `TransientModel` |

### 4.2 Champs

| Champ | Type | Obligatoire | Défaut |
|-------|------|-------------|--------|
| `date_from` | Date | Oui | Premier jour du mois M-1 |
| `date_to` | Date | Oui | Dernier jour du mois M-1 |
| `report_file` | Binary | Non | Rempli à la génération — §4.4 |
| `report_filename` | Char | Non | Nom de fichier — §9.3 |

### 4.3 Contrôles

| Règle | Comportement |
|-------|--------------|
| `date_from > date_to` | `UserError` — message explicite |
| Devise document ≠ devise société | `UserError` — voir §6.5 |
| Onglet sans document | Génération **autorisée** |
| Société | `env.company` uniquement — pas de multi-société V1 |

### 4.4 Action et téléchargement

| Bouton | Méthode | Résultat |
|--------|---------|----------|
| **Générer le rapport Excel** | `action_generate_xlsx` | Téléchargement `.xlsx` |

**Ne pas** bloquer la génération si un onglet est vide (contrairement à `laplatine_customer_statement`).

#### Cycle de vie du fichier généré (arbitrage MOA)

La génération **ne doit pas** entraîner une accumulation permanente de pièces jointes
techniques dans la base.

**Option retenue V1** — champs binaires sur le wizard `TransientModel` :

| Champ | Type | Rôle |
|-------|------|------|
| `report_file` | Binary | Contenu `.xlsx` généré |
| `report_filename` | Char | Nom de fichier §9.2 |

Parcours :

1. Génération en mémoire (`BytesIO` / `xlsxwriter`) ;
2. Écriture dans `report_file` / `report_filename` sur le wizard ;
3. Retour d’une action de téléchargement pointant vers le champ binaire du wizard
   (sans créer d’`ir.attachment` persistant).

Lors du nettoyage automatique des enregistrements `TransientModel`, le fichier disparaît
avec le wizard.

> **Note** : `laplatine_customer_statement` utilise un `ir.attachment` rattaché au wizard
> transient — pattern **non repris** ici pour éviter l’accumulation de fichiers en base.

**Interdit en V1** : créer un `ir.attachment` permanent à chaque génération sans politique
de nettoyage explicite.

---

## 5. Périmètre société et sécurité

### 5.1 Société active

Toutes les recherches incluent :

```python
("company_id", "=", env.company.id)
```

- Pas de consolidation multi-sociétés en V1
- Pas de sélecteur de société dans l’assistant
- Respect des règles d’accès `account.move` standard
- **Interdit** : `sudo()` pour contourner les droits comptables

### 5.2 Groupes et menus

| Élément | Groupe |
|---------|--------|
| Menu **La Platine** | `account.group_account_invoice` |
| Menu **Rapport de facturation** | `account.group_account_invoice` |
| Wizard / action | `account.group_account_invoice` |

Les groupes supérieurs (`account.group_account_manager`, etc.) conservent l’accès par héritage Odoo.

Un utilisateur ne doit pas exporter des données qu’il ne peut pas consulter dans Odoo.

---

## 6. Sources de données

### 6.1 Modèle unique

`account.move` — lecture seule, **aucune écriture** comptable.

### 6.2 États inclus / exclus

| Inclus | Exclus |
|--------|--------|
| `state = 'posted'` | Brouillons (`draft`) |
| | Annulées (`cancel`) |

### 6.3 Date de filtrage (arbitrage MOA)

| Usage | Champ |
|-------|--------|
| Filtre période | `invoice_date` |
| Colonne affichée | **Date de facture** (`invoice_date`) |
| Borne | Inclusif `date_from` ≤ `invoice_date` ≤ `date_to` |

Le champ comptable `date` **n’est pas** utilisé comme critère de sélection en V1.

**Documents sans `invoice_date`** : exclus du rapport (cas marginal sur pièces comptabilisées).

### 6.4 Types de documents

| Onglet | `move_type` inclus |
|--------|-------------------|
| **Ventes** | `out_invoice`, `out_refund` |
| **Achats** | `in_invoice`, `in_refund` |

### 6.5 Devises (arbitrage MOA — revue 2026-07-06)

- Usage courant La Platine : **EUR** (`company.currency_id`)
- Format monétaire du classeur : devise de la société
- Conversion ou consolidation multi-devises : **hors périmètre V1**

**Garde-fou obligatoire** : si au moins un document sélectionné utilise une devise
différente de `company.currency_id`, **interrompre** la génération avec un message explicite.

Exemple de message :

```text
Le rapport contient N document(s) dans une devise différente de l'EUR.
La génération multidevise n'est pas prise en charge dans cette version.
```

Implémentation de référence :

```python
foreign = moves.filtered(lambda m: m.currency_id != company.currency_id)
if foreign:
    raise UserError(...)
```

Pas de conversion silencieuse. Pas d’addition de montants hétérogènes.

---

## 7. Règles de signe et identification des avoirs

### 7.1 Principe

Ne **pas** supposer que `amount_untaxed`, `amount_tax`, `amount_total` ou `amount_residual`
portent déjà le signe attendu dans `account.move`.

Odoo distingue montants bruts, montants signés et `direction_sign` selon le type de document.
Le rapport applique un **signe de restitution métier** explicite.

### 7.2 Signe de restitution (`report_sign`)

| `move_type` | `report_sign` | Type affiché |
|-------------|---------------|--------------|
| `out_invoice` | `+1` | Facture |
| `out_refund` | `-1` | Avoir |
| `in_invoice` | `+1` | Facture |
| `in_refund` | `-1` | Avoir |

### 7.3 Formules de montants signés

Pour chaque `account.move` `move` :

```python
sign = report_sign(move.move_type)
amount_ht   = sign * abs(move.amount_untaxed)
amount_tax  = sign * abs(move.amount_tax)
amount_ttc  = sign * abs(move.amount_total)
amount_paid = sign * abs(move.amount_total - move.amount_residual)
amount_due  = sign * abs(move.amount_residual)
```

- `abs()` sur les champs bruts **avant** application du signe métier
- Les **totaux** en fin d’onglet sont la **somme algébrique** des lignes signées
- Les avoirs **diminuent** donc correctement les totaux cabinet

**Exemple MOA validé** :

| Type | Montant TTC | Montant réglé / soldé | Reste à payer / solder |
|------|------------:|----------------------:|-----------------------:|
| Facture | 1 000 € | 600 € | 400 € |
| Avoir | −200 € | −200 € | 0 € |

Pour un avoir : montants HT, TVA, TTC, réglé/soldé et reste à solder sont **négatifs**.
La prise en compte est **algébrique** dans tous les totaux de synthèse.

### 7.4 Colonne Type

Colonne obligatoire dans **Ventes** et **Achats** :

| Valeur affichée | Condition |
|-----------------|-----------|
| `Facture` | `move_type` ∈ (`out_invoice`, `in_invoice`) |
| `Avoir` | `move_type` ∈ (`out_refund`, `in_refund`) |

Les avoirs ne sont **pas** identifiés uniquement par le signe des montants ou le numéro.

### 7.5 Libellés « réglé / soldé » et « reste à payer / solder »

Colonnes concernées (Ventes et Achats) :

| Libellé colonne | Champ Odoo sous-jacent | Formule §7.3 |
|-----------------|------------------------|--------------|
| **Montant réglé / soldé** | `amount_total - amount_residual` | `amount_paid` |
| **Reste à payer / solder** | `amount_residual` | `amount_due` |

Le libellé **Montant réglé / soldé** est retenu à la place de « Montant réglé » ou
« Montant remboursé ».

Un avoir soldé dans Odoo peut avoir été :

- remboursé au client ou par le fournisseur ;
- imputé sur une autre facture ;
- rapproché avec une autre écriture.

La V1 montre qu’il est **soldé**, sans affirmer qu’un mouvement bancaire de remboursement
a nécessairement eu lieu.

**Hors périmètre V1** : distinction entre remboursement bancaire, imputation sur facture
ou autre rapprochement comptable — sauf si une méthode standard Odoo fiable et simple
permet de la restituer sans complexifier le rapport.

### 7.6 État du paiement

Champ source : `payment_state` (sélection standard Odoo).

**Libellés** : obtenus depuis la sélection standard **traduite** par Odoo — **pas** de dictionnaire français codé en dur dans le module.

La sélection `payment_state` doit être **chargée une seule fois** par génération de rapport
(au démarrage du générateur XLSX), puis réutilisée pour toutes les lignes :

```python
# Une fois par génération (pas par facture)
payment_state_labels = dict(
    env["account.move"].fields_get(["payment_state"])["payment_state"]["selection"]
)
label = payment_state_labels.get(move.payment_state, move.payment_state)
```

États standard attendus (libellés FR selon traduction Odoo installée) :

- Non payé (`not_paid`)
- En cours de paiement (`in_payment`)
- Payé (`paid`)
- Partiellement payé (`partial`)
- Inversé (`reversed`)
- Bloqué (`blocked`)

---

## 8. Domaines de recherche

### 8.1 Ventes

```python
[
    ("company_id", "=", company.id),
    ("state", "=", "posted"),
    ("move_type", "in", ["out_invoice", "out_refund"]),
    ("invoice_date", "!=", False),
    ("invoice_date", ">=", date_from),
    ("invoice_date", "<=", date_to),
]
```

Tri : `order="invoice_date, name"`

### 8.2 Achats

```python
[
    ("company_id", "=", company.id),
    ("state", "=", "posted"),
    ("move_type", "in", ["in_invoice", "in_refund"]),
    ("invoice_date", "!=", False),
    ("invoice_date", ">=", date_from),
    ("invoice_date", "<=", date_to),
]
```

Tri : `order="invoice_date, name"`

---

## 9. Contenu du fichier Excel

### 9.1 Structure

| Propriété | Valeur |
|-----------|--------|
| Format | `.xlsx` (`xlsxwriter`) |
| Nombre d’onglets | **Exactement 2** : `Ventes`, `Achats` |
| Onglets toujours présents | Oui — même si vides |

### 9.2 Granularité des lignes

**Chaque onglet contient une ligne par facture ou avoir** (`account.move`).

Il n’y a **pas** d’export des lignes de produits (`account.move.line`) ni de détail
article par article.

### 9.3 Nom de fichier

```text
Rapport_facturation_La_Platine_YYYY-MM-DD_YYYY-MM-DD.xlsx
```

Exemple : `Rapport_facturation_La_Platine_2026-06-01_2026-06-30.xlsx`

Les dates correspondent à `date_from` et `date_to` de l’assistant.

### 9.4 Onglet vide

Si aucun document sur la période :

- conserver titre + en-têtes de colonnes ;
- afficher une ligne de mention : **« Aucun document trouvé sur la période sélectionnée. »** ;
- ligne de totaux avec **Nombre de documents = 0** et montants à 0.

---

## 10. Grille de mise en page Excel (figée)

Constantes **identiques** sur les onglets `Ventes` et `Achats` (index **0-based** xlsxwriter) :

| Ligne Excel (1-based) | Index | Contenu |
|----------------------|-------|---------|
| 1 | 0 | Titre : `Rapport de facturation — Ventes` ou `… — Achats` |
| 2 | 1 | Société (`company.display_name`) |
| 3 | 2 | Période : `Du JJ/MM/AAAA au JJ/MM/AAAA` |
| 4 | 3 | `Généré le JJ/MM/AAAA` |
| 5 | 4 | Ligne vide |
| 6 | 5 | **En-têtes des colonnes** |
| 7+ | 6+ | **Une ligne par document** (facture ou avoir) |
| Dernière | `last_row` | **Ligne de totaux** |

Constantes code :

```python
META_ROW_COUNT = 5          # lignes 1 à 5 (index 0–4)
HEADER_ROW = 5                # ligne 6 Excel — en-têtes colonnes
FIRST_DATA_ROW = 6            # ligne 7 Excel — première ligne document
EMPTY_MESSAGE_ROW = 6         # si onglet vide : message sur cette ligne
```

Règles dérivées :

| Mécanisme | Réglage |
|-----------|---------|
| Volets figés | `freeze_panes(FIRST_DATA_ROW, 0)` — sous la ligne d’en-têtes |
| Autofiltre | Ligne `HEADER_ROW` (ligne 6) |
| Répétition à l’impression | `repeat_rows(0, HEADER_ROW)` — lignes 1 à 6 sur chaque page |
| Zone d’impression | `(0, 0)` → `(last_row, last_col)` |
| Ligne vide | Index 4 — sépare le bloc méta des en-têtes |

Le **titre, la société, la période, la date de génération et les en-têtes** doivent
être visibles sur **chaque page imprimée**, pas uniquement sur la première.

### 10.1 Sécurisation des cellules texte

Les valeurs textuelles issues d’Odoo (numéros, références, origines, noms tiers, libellés
de paiement) doivent être écrites avec **`write_string()`** — jamais interprétées comme
des formules Excel.

Règle : tout champ texte dont la valeur commence par `=`, `+`, `-`, `@` ou `\t` doit
quand même être écrit en tant que **chaîne littérale** (comportement natif de
`write_string()` dans xlsxwriter).

---

## 11. Colonnes — onglet Ventes

Ordre **validé MOA** (référence : extraction mensuelle existante + colonne Type et règles avoirs).

| # | Colonne | Source Odoo | Remarque |
|---|---------|-------------|----------|
| 1 | Type | dérivé `move_type` | Facture / Avoir |
| 2 | Numéro | `name` | |
| 3 | Client | `partner_id.display_name` | |
| 4 | Date de facture | `invoice_date` | Format `dd/mm/yyyy` |
| 5 | Date d’échéance | `invoice_date_due` | Vide si absent |
| 6 | Montant HT | signé §7.3 | `amount_untaxed` |
| 7 | TVA | signé §7.3 | `amount_tax` |
| 8 | Montant TTC | signé §7.3 | `amount_total` |
| 9 | Montant réglé / soldé | signé §7.3 | `amount_total - amount_residual` — §7.5 |
| 10 | Reste à payer / solder | signé §7.3 | `amount_residual` — §7.5 |
| 11 | État du paiement | `payment_state` | Libellé traduit §7.6 |

**Hors V1** : colonne « Référence / Origine » (`invoice_origin` / `ref`) — voir §2.1.

### 11.1 Ligne de synthèse (totaux)

Libellé de comptage : **Nombre de documents** (factures + avoirs).

| Indicateur | Calcul |
|------------|--------|
| Nombre de documents | `len(moves)` |
| Total HT | Σ Montant HT |
| Total TVA | Σ TVA |
| Total TTC | Σ Montant TTC |
| Total réglé / soldé | Σ Montant réglé / soldé |
| Total restant à payer / solder | Σ Reste à payer / solder |

Les avoirs **diminuent** tous les totaux concernés.

---

## 12. Colonnes — onglet Achats

Même logique que Ventes, adaptée aux fournisseurs. Ordre **validé MOA**.

| # | Colonne | Source Odoo | Remarque |
|---|---------|-------------|----------|
| 1 | Type | dérivé `move_type` | Facture / Avoir |
| 2 | Numéro Odoo | `name` | |
| 3 | Référence fournisseur | `ref` | Numéro porté sur la facture fournisseur |
| 4 | Fournisseur | `partner_id.display_name` | |
| 5 | Date de facture | `invoice_date` | Format `dd/mm/yyyy` |
| 6 | Date d’échéance | `invoice_date_due` | |
| 7 | Montant HT | signé §7.3 | |
| 8 | TVA | signé §7.3 | |
| 9 | Montant TTC | signé §7.3 | |
| 10 | Montant réglé / soldé | signé §7.3 | §7.5 |
| 11 | Reste à payer / solder | signé §7.3 | §7.5 |
| 12 | État du paiement | `payment_state` | Libellé traduit §7.6 |

**Hors V1** : colonne « Origine » (`invoice_origin`) — voir §2.1.

Ligne de synthèse : identique à §11.1 (**Nombre de documents** et totaux §7.5).

---

## 13. Présentation XLSX et impression

Style sobre et professionnel — **aucun graphique**.

Chaque onglet doit comporter :

| Élément | Détail |
|---------|--------|
| En-têtes colonnes | Fond gris clair, gras, bordures |
| Formats monétaires | Devise société, séparateur milliers |
| Dates | Format français `dd/mm/yyyy` |
| Ligne totaux | Gras, distincte du tableau |
| Autofiltre | Ligne 6 — voir §10 |
| Volets figés | Sous la ligne 6 — voir §10 |

### 13.1 Paramètres d’impression (par onglet)

Reprise du pattern `laplatine_customer_statement`, avec grille figée §10 :

| Paramètre | Valeur |
|-----------|--------|
| Format papier | A4 |
| Orientation | Paysage |
| Ajustement largeur | 1 page en largeur (`fit_to_pages(1, 0)`) |
| Hauteur | Automatique selon lignes |
| En-têtes répétés | `repeat_rows(0, HEADER_ROW)` — lignes 1 à 6 (méta + en-têtes colonnes) |
| Marges | Confortables (≈ 0,4–0,55") |
| Pied de page | `Page &P / &N` centré |
| Zone d’impression | Lignes 1 à `last_row` — bloc méta + données + totaux |
| Grille | Masquée à l’impression |

---

## 14. Architecture technique (lab)

### 14.1 Structure module

```text
laplatine_billing_report/
├── __manifest__.py
├── __init__.py
├── SPECIFICATION_V1.md
├── README.md
├── wizard/
│   ├── billing_report_wizard.py
│   └── billing_report_wizard_views.xml
├── report/
│   └── billing_report_xlsx.py
├── views/
│   └── menu.xml
├── security/
│   └── ir.model.access.csv
└── tests/
    └── test_billing_report.py
```

### 14.2 Dépendances

| Dépendance | Type |
|------------|------|
| `account` | Module Odoo |
| `xlsxwriter` | `external_dependencies` Python |

### 14.3 Principes

- Pas de duplication de données en base
- Pas de stockage de montants recalculés
- Pas de règles spécifiques à un client/fournisseur codées en dur
- Génération à la volée (pas de modèle de reporting persistant V1)
- Pas d’`ir.attachment` permanent par génération (§4.4)

---

## 15. Hors périmètre V1

- Comparaison entre périodes, évolution, analyse 20/80
- Classements clients / fournisseurs, graphiques, marges
- Analyse par produit, prévision de trésorerie
- Retards de paiement détaillés (au-delà du `payment_state` standard)
- Envoi e-mail automatique au cabinet
- Planification mensuelle automatique
- PDF dédié
- Menu **Analyse de facturation**
- Consolidation multi-sociétés
- Gestion multi-devises avancée
- Filtre sur `date` comptable
- Colonnes **Référence / Origine** (Ventes) et **Origine** (Achats) — sauf demande utilisatrices
- Distinction remboursement bancaire / imputation / rapprochement sur avoirs soldés (§7.5)

---

## 16. Plan de développement lab (slices)

| Slice | Contenu | Tests |
|-------|---------|-------|
| **A** | Squelette module, menu, wizard M-1, validation période, champs binaires téléchargement | T01–T03 |
| **B** | Générateur onglet Ventes + signe + Type + totaux + garde-fou devise | T04–T13 |
| **C** | Onglet Achats + fichier 2 feuilles + nom fichier | T08, T17, T19 |
| **D** | Présentation XLSX + grille §10 + impression A4 paysage | Recette §18 (manuelle) |
| **E** | Sécurité + onglets vides + `write_string` + pas d’`ir.attachment` | T18, T21, T22 |

**Production : STOP** jusqu’à GO MOA distinct.

---

## 17. Cas de test automatisés

### 17.1 Assistant et période

| ID | Scénario | Attendu |
|----|----------|---------|
| T01 | Ouverture wizard | `date_from` / `date_to` = mois M-1 complet |
| T02 | `date_from > date_to` | `UserError` |
| T03 | Période modifiable | Génération OK sur plage personnalisée |

### 17.2 Sélection et société

| ID | Scénario | Attendu |
|----|----------|---------|
| T04 | Facture client posted dans période | Présente onglet Ventes |
| T05 | Brouillon / annulée | Absente |
| T06 | Autre société | Absente (`company_id` filtré) |
| T07 | `invoice_date` hors période | Absente |
| T08 | Facture fournisseur posted | Présente onglet Achats |
| T09 | Document en devise ≠ `company.currency_id` | `UserError` explicite — génération bloquée |

### 17.3 Signe et avoirs

| ID | Scénario | Attendu |
|----|----------|---------|
| T10 | `out_invoice` 1000 € TTC | Montants **positifs**, Type = Facture |
| T11 | `out_refund` 200 € TTC (brut positif en base) | Montants **négatifs** −200, Type = Avoir |
| T12 | `in_refund` fournisseur | Montants **négatifs**, Type = Avoir |
| T13 | Totaux avec facture + avoir | Somme algébrique correcte |

### 17.4 Paiement et colonnes

| ID | Scénario | Attendu |
|----|----------|---------|
| T14 | `payment_state = paid` | Libellé = sélection Odoo traduite, pas chaîne technique |
| T15 | Montant réglé / soldé | `sign * abs(total - residual)` — en-tête colonne exact |
| T16 | Ordre colonnes Ventes | 11 colonnes — ordre §11 (Type en 1, pas de Référence/Origine) |

### 17.5 Fichier, sécurité et onglets vides

| ID | Scénario | Attendu |
|----|----------|---------|
| T17 | Ventes seules | 2 onglets présents |
| T18 | Aucun document | Fichier généré, mention « Aucun document trouvé… », totaux à 0 |
| T19 | Nom fichier | Contient les deux dates période |
| T20 | Nombre de documents | Libellé exact en ligne de synthèse |
| T21 | Numéro commençant par `=` | Cellule texte littérale (`write_string`) |
| T22 | Droits utilisateur invoice | Accès wizard ; utilisateur sans groupe → refus ; **aucun** `ir.attachment` créé |

### 17.6 Données de test suggérées (lab)

Jeux minimal par slice :

1. **Ventes** : 1 `out_invoice` + 1 `out_refund` même période, montants bruts positifs
2. **Achats** : 1 `in_invoice` + 1 `in_refund`
3. **Contrôle totaux** : vérifier que total TTC = facture − avoir (valeurs signées)

---

## 18. Critères d’acceptation MOA (recette)

### Assistant

- [ ] Menu **Rapport de facturation** ouvre un wizard
- [ ] Mois M-1 complet proposé par défaut
- [ ] Dates modifiables
- [ ] Période incorrecte refusée avec message clair
- [ ] Devise étrangère refusée avec message explicite (§6.5)

### Fichier Excel

- [ ] Format `.xlsx`, exactement 2 onglets `Ventes` et `Achats`
- [ ] **Une ligne par document** (facture ou avoir) — pas de lignes produits
- [ ] Même période sur les deux onglets
- [ ] Brouillons et annulées absents
- [ ] Comptabilisées présentes
- [ ] Colonne **Type** Facture / Avoir en première colonne
- [ ] Libellés **Montant réglé / soldé** et **Reste à payer / solder**
- [ ] Avoirs en montants **négatifs** (HT, TVA, TTC, réglé/soldé, reste)
- [ ] Totaux = somme algébrique — avoirs diminuent tous les totaux
- [ ] Dates et montants formatés
- [ ] Nom fichier avec période
- [ ] Génération OK si un onglet vide — message **« Aucun document trouvé… »**
- [ ] Colonnes et ordre conformes §11 / §12 (référence extraction MOA §2.1)
- [ ] Aucune pièce jointe technique permanente en base (§4.4)
- [ ] Pas de colonnes Référence/Origine (Ventes) ni Origine (Achats) en V1

### Impression (automatisé)

- [ ] A4 paysage, 1 page en largeur
- [ ] `repeat_rows` lignes 1 à 6 (méta + en-têtes)
- [ ] Volets figés sous la ligne 6
- [ ] Zone d’impression jusqu’à la ligne de totaux
- [ ] Numéros de page

### Impression (recette manuelle obligatoire)

Les tests automatisés ne garantissent pas la lisibilité réelle des onze à douze colonnes.

- [ ] Générer les deux onglets avec un jeu représentatif d’**au moins 25 à 50 documents**
- [ ] Vérifier visuellement l’**aperçu avant impression** ou une impression réelle en **A4 paysage**
- [ ] Le fichier tient sur **une page en largeur** sans textes ni montants illisibles
- [ ] Titre, société, période et en-têtes restent visibles sur **chaque page** imprimée

---

## 19. Arbitrages MOA — synthèse

| Sujet | Décision |
|-------|----------|
| Module | `laplatine_billing_report` dédié |
| Statut document | **MOA validée — développement lab autorisé** (2026-07-06) |
| Référence métier | Extraction mensuelle Odoo existante — onglet Ventes |
| Colonnes Ventes | 11 colonnes — ordre §11 ; pas de Référence/Origine en V1 |
| Colonnes Achats | 12 colonnes — ordre §12 ; pas d’Origine en V1 |
| Libellés montants | **Montant réglé / soldé** ; **Reste à payer / solder** |
| Date filtre | `invoice_date` uniquement |
| Société | `env.company` uniquement |
| Devises | **Blocage** si devise document ≠ devise société |
| Fichier généré | Champs binaires wizard — pas d’`ir.attachment` permanent |
| Mise en page | Grille figée §10 (lignes 1–6 méta + en-têtes) |
| Granularité | **Une ligne par document** |
| Avoirs | Colonne Type + signe explicite `report_sign` + totaux algébriques |
| Montants | `sign * abs(champ_brut)` |
| Soldes avoirs | Montre le solde, pas le mode de règlement (§7.5) |
| Paiement | Libellés `payment_state` via Odoo — chargés une fois |
| Texte Excel | `write_string()` pour champs texte Odoo |
| Menu | Facturation → La Platine → Rapport de facturation |
| Comptage | **Nombre de documents** |
| Sécurité | `account.group_account_invoice` |
| Production | **STOP** |

### Conclusion documentaire (arbitrage MOA 2026-07-06)

> La capture de l’extraction existante valide la philosophie et la structure de l’onglet Ventes.
> Les colonnes, l’ordre, les libellés réglé/soldé et les règles de signe des avoirs sont intégrés.
> Le développement lab des slices A à E est **autorisé**.
> La production reste **STOP** jusqu’à GO MOA distinct.

---

## 20. Références

| Document | Lien |
|----------|------|
| Cadrage MOA | `LP-FACT-REPORT-001` |
| Module complémentaire | `laplatine_customer_statement/SPECIFICATION_V1.md` |
| Odoo 18 `account.move` | [account_move.py](https://github.com/odoo/odoo/blob/18.0/addons/account/models/account_move.py) |
| Menus Facturation | [account_menuitem.xml](https://github.com/odoo/odoo/blob/18.0/addons/account/views/account_menuitem.xml) |

---

## 21. Prochaine étape

1. **Développement lab** slices A → E (GO MOA 2026-07-06)
2. Recette lab (automatisée + impression manuelle §18) + tests T01–T22
3. Validation utilisatrices (Véréna / Ethel) sur un export M-1 représentatif
4. GO MOA **production** distinct du GO développement lab
