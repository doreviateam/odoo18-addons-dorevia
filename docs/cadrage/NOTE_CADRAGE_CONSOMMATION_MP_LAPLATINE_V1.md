# NOTE DE CADRAGE — CONSOMMATION SIMPLIFIÉE DES MATIÈRES PREMIÈRES

| Élément | Valeur |
|---------|--------|
| **Référence** | `LAPLATINE-CONS-MP-001` |
| **Module** | `laplatine_procurement_control` |
| **Version cible** | `18.0.1.2.0` |
| **Environnement initial** | lab `laplatine-odoo18-lab` / base `laplatine_prod` |
| **Statut** | GO Dev — Slice 1 ouvert |
| **Production** | **STOP** jusqu'au GO MOA explicite |
| **Base Git** | `7311b20` |

---

## 1. Contexte

Le cockpit actuel répond au pilotage administratif (stock, seuils, fournisseur, alertes, risque).

Le besoin opérationnel quotidien de Véréna, Ethel et Michel est différent :

> Enregistrer un prélèvement de matière première en quelques secondes, sans écrans techniques Stock.

**Doctrine :** Odoo exécute les mouvements et ajustements. L'interface La Platine simplifie l'usage.

---

## 2. Objectif du lot

Wizard unique permettant de :

1. sélectionner une matière première éligible ;
2. voir emplacement et quantité disponible ;
3. saisir une quantité prélevée (kg) ;
4. enregistrer la consommation (mouvement standard) ;
5. corriger après comptage (ajustement standard) ;
6. être informé si le seuil min de réappro est atteint.

---

## 3. Navigation cible

```text
Inventaire
├── La Platine
│   └── Consommation matière première        ← wizard opérationnel
└── Configuration
    └── Pilotage approvisionnements
        └── Cockpit                          ← supervision (inchangé fonctionnellement)
```

---

## 4. Éligibilité des articles

### 4.1 Champ `laplatine_consumption_tracking`

- Modèle : `product.template`
- Libellé : **Suivi consommation La Platine**
- Onglet Inventaire, bloc **LA PLATINE**
- Filtre uniquement le wizard — **ne modifie pas** l'éligibilité cockpit sans décision MOA

### 4.2 Domaine wizard

Articles proposés si :

- actifs ;
- stockables (`is_storable`) ;
- `laplatine_consumption_tracking = True` ;
- société courante ou partagé ;
- UoM de la catégorie **Poids** (saisie kg + conversion).

---

## 5. Configuration société (verrouillage MOA)

### 5.1 Entrepôt de pilotage

Existant : `laplatine_procurement_warehouse_id`.

**Périmètre emplacements sources** : uniquement les emplacements internes de cet entrepôt.

### 5.2 Emplacement de destination des consommations

Nouveau champ sur `res.company` :

> **Emplacement de destination des consommations La Platine**

- `Many2one(stock.location)`
- Domaine : `usage = production`
- Défaut : emplacement virtuel Production standard de la société
- **Obligatoire** — jamais de sélection arbitraire du premier `usage=production`

---

## 6. Wizard — modes

| Mode | Libellé | Action principale |
|------|---------|-------------------|
| `consumption` | Enregistrer un prélèvement | Mouvement internal → production |
| `adjustment` | Correction après comptage | Ajustement inventaire standard |

### 6.1 Emplacements sources

**Consommation :**

- emplacements internes du warehouse de pilotage **avec stock > 0** ;
- auto-sélection si un seul ;
- choix explicite si plusieurs.

**Correction :**

- emplacements internes du warehouse de pilotage **même si stock = 0**.

### 6.2 Consommation

- Champ **Quantité prélevée** (kg), obligatoire, > 0, ≤ disponible
- Mouvement `done`, référence `Consommation MP La Platine`
- Confirmation utilisateur possible pour toute consommation — **sans paramètre métier de seuil %**

### 6.3 Correction

- **Quantité réellement comptée** (stock final, ≥ 0)
- **Motif obligatoire** — rattaché au **mouvement d'ajustement standard** (`stock.move`), jamais seul sur `stock.quant`
- Confirmation explicite avant application

---

## 7. Seuil de réapprovisionnement (post-opération)

Relire la règle standard via `_resolve_orderpoint()` (sous-emplacements inclus).

Messages :

- stock > min : notification normale ;
- stock ≤ min : **Seuil de réapprovisionnement atteint** ;
- pas de commande fournisseur auto en V1.

**Hors V1 :** préalerte à 50 % (`warning_threshold_ratio`) — **supprimée**.

---

## 8. Architecture technique

### 8.1 Service partagé ciblé

Modèle abstract `laplatine.procurement.stock.ops` :

- opérations partagées wizard / futur ;
- encapsule ou délègue `_get_internal_location_ids()`, `_resolve_orderpoint()`, `_convert_qty()` ;
- **pas de refonte cockpit** en Slice 1.

### 8.2 Doctrine

- aucun stock parallèle ;
- aucun registre concurrent ;
- traçabilité = mouvements et ajustements Odoo standards.

---

## 9. Droits

| Groupe | Accès |
|--------|-------|
| **La Platine — Consommation matières premières** | Menu La Platine, wizard |
| Groupes cockpit existants | Consultation / Actualisation / Paramétrage (inchangés) |

Le groupe consommation **n'implique pas** les groupes cockpit.

---

## 10. Cas pilote — Fécule

`[MP-FEC-MAN-001]` — `WH/Stock/Conteneur Fécule` — min 5 000 / max 18 250 kg.

Scénarios bloquants recette : consommation 75 kg ; correction 13 150 kg avec motif.

---

## 11. Critères d'acceptation (AC01–AC15)

| ID | Critère |
|----|---------|
| AC01 | Menu `Inventaire > La Platine > Consommation matière première` ouvre le wizard |
| AC02 | Cockpit sous `Inventaire > Configuration > Pilotage approvisionnements` |
| AC03 | Seuls articles éligibles (actif, stockable, booléen, poids) |
| AC04 | Quantité disponible = stock Odoo de l'emplacement |
| AC05 | Consommation crée mouvement production, stock diminue |
| AC06 | Traçabilité auteur, date, article, emplacement, qty, référence |
| AC07 | Refus si qty > disponible |
| AC08 | Correction via ajustement standard |
| AC09 | Motif obligatoire sur mouvement d'ajustement |
| AC10 | Indication seuil min après opération |
| AC11 | Aucun compteur stock parallèle |
| AC12 | Opérateurs sans accès menus techniques config |
| AC13 | Non-régression cockpit |
| AC14 | Multi-emplacements : choix explicite + qty par emplacement |
| AC15 | Conversion kg → UoM stock (catégorie Poids) |

---

## 12. Tests automatisés (T01–T22)

| ID | Test |
|----|------|
| T01 | Domaine articles éligibles |
| T02 | Exclusion non stockables |
| T03 | Exclusion sans booléen |
| T04 | Exclusion hors catégorie Poids |
| T05 | Emplacement auto si unique avec stock |
| T06 | Choix si plusieurs emplacements |
| T07 | Consommation nominale |
| T08 | Diminution stock effective |
| T09 | Mouvement vers destination société configurée |
| T10 | Refus qty nulle |
| T11 | Refus qty négative |
| T12 | Refus qty > disponible |
| T13 | Conversion kg |
| T14 | Correction inventaire positive |
| T15 | Correction inventaire négative |
| T16 | Correction à zéro |
| T17 | Motif obligatoire |
| T18 | Alerte seuil min atteint |
| T19 | Accès groupe opérationnel |
| T20 | Absence accès cockpit sans groupe adapté |
| T21 | Menu cockpit sous Configuration |
| T22 | Non-régression tests cockpit existants |

---

## 13. Découpage Dev (4 slices)

| Slice | Contenu | Tests cibles |
|-------|---------|--------------|
| **1** | Cadrage, booléen, config société, groupes, menus, wizard squelette, stock.ops minimal | T01–T04, T19–T21 |
| **2** | Lecture emplacement / stock | T05–T06, T04, AC04, AC14 |
| **3** | Consommation mouvement standard | T07–T13, AC05–AC07 |
| **4** | Correction + motif sur move + seuil + doc + bump 18.0.1.2.0 | T14–T18, AC08–AC13, T22 |

---

## 14. Hors périmètre V1

PO auto, MRP, code-barres, sacs, mobile, workflow approbation, emails, lots, auto-décochage « consommation non traçable », préalerte 50 %.

---

## 15. Décision MOA

> GO Dev par slices. Production STOP. Cas pilote fécule bloquant recette finale.

Verrouillages intégrés : destination Production configurée ; pas de préalerte 50 % ; motif sur mouvement ; AC/T séparés ; mutualisation limitée ; emplacements = warehouse pilotage.
