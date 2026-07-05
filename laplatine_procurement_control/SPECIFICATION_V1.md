# Spécification fonctionnelle V1 — `laplatine_procurement_control`

## 1. Identification

| Élément | Valeur |
|---|---|
| Projet | SARL La Platine — Odoo 18 Community |
| Module technique | `laplatine_procurement_control` |
| Emplacement | `addons/odoo18-addons-dorevia/laplatine_procurement_control` |
| Nom fonctionnel | La Platine — Pilotage des approvisionnements |
| Version cible | **V1 — `18.0.1.0.0`** (en conception) |
| Référence Git | branche `main` — non publié |
| Statut | **V1 gelée** — GO faisabilité MOA ✅ — GO MOA spec V1 ✅ — **GO développement ✅** |
| Document source | [`note_cadrage.md`](note_cadrage.md) V0.1 |
| Production | **STOP** jusqu'à GO MOA explicite de déploiement |

---

## 2. Contexte et objectif

La Platine achète et stocke des articles nécessaires à son activité (matières
premières, ingrédients, emballages, consommables, marchandises revendables, etc.).

Le cycle opérationnel de référence reste celui d'Odoo :

> Besoin → Réapprovisionnement → Commande fournisseur → Réception → Stock → Consommation

Le module **ne remplace pas** les applications Achats, Stock ni Fabrication.

Il doit permettre de **consolider et interpréter** les données déjà présentes
dans Odoo pour rendre les risques d'approvisionnement :

- visibles ;
- compréhensibles ;
- priorisables ;
- actionnables.

### Valeur métier distinctive

> **Une information positive de stock prévisionnel ne doit pas masquer une rupture
> susceptible de survenir avant l'arrivée de la marchandise confirmée.**

Le cockpit doit pouvoir détecter une rupture intermédiaire entre aujourd'hui et
la prochaine réception confirmée, en croisant couverture actuelle, consommation,
délai fournisseur et dates de réception.

---

## 3. Doctrine fonctionnelle (gelée V1)

### 3.1 Standard Odoo d'abord

Source de vérité pour :

- articles et variantes ;
- fournisseurs et délais ;
- commandes et réceptions ;
- stock disponible et prévisionnel ;
- règles de réapprovisionnement (`stock.warehouse.orderpoint`) ;
- mouvements de stock et ordres de fabrication.

### 3.2 Interdictions

Le module ne doit **pas** :

- maintenir un second stock ;
- dupliquer les commandes fournisseurs ou les réceptions ;
- remplacer le moteur standard de réapprovisionnement ;
- créer un circuit spécifique à la fécule de manioc ou à un article nommé ;
- introduire un second seuil métier parallèle au min/max standard en V1 ;
- conclure automatiquement à une situation **Normale** en l'absence de seuil exploitable.

### 3.3 Spécifique autorisé

Uniquement la couche de **pilotage** :

- criticité métier paramétrable ;
- indicateurs calculés ;
- statut de risque et alertes ;
- cockpit transverse ;
- navigation vers les objets standards.

---

## 4. Utilisateurs

| Profil | Usage V1 |
|---|---|
| Responsable des approvisionnements | Utilisateur principal — surveillance, priorisation, actions |
| Direction | Consultation — articles critiques, risques majeurs |
| Production / magasin | Contribution indirecte via fiabilité des mouvements et réceptions |

Les groupes de sécurité définitifs seront précisés à l'implémentation.

---

## 5. Point d'entrée

Menu permanent :

> **La Platine → Pilotage des approvisionnements**

Écran **cockpit liste** (pas un wizard ponctuel), consultable régulièrement.

Depuis chaque ligne, accès direct aux objets standards pertinents :

- fiche article / variante ;
- fiche fournisseur ;
- règle de réapprovisionnement ;
- commande fournisseur ;
- réception attendue ;
- mouvements de stock pertinents.

---

## 6. Périmètre stock et société (V1)

### 6.1 Entrepôt de référence

Le périmètre V1 est explicitement rattaché à **l'entrepôt principal de La Platine**.

- Paramètre au niveau **société** (`res.company`) : entrepôt de pilotage.
- Valeur par défaut : entrepôt principal de la société La Platine.
- Stock affiché, règles de réappro et calculs de couverture : **périmètre de cet entrepôt**.
- Aucune agrégation silencieuse de plusieurs entrepôts ou emplacements.

### 6.2 Contexte explicite

Le cockpit affiche ou permet de retrouver :

- la société ;
- l'entrepôt de pilotage ;
- la période de consommation utilisée ;
- l'unité de mesure de l'article.

---

## 7. Articles entrant dans le périmètre

Un article est éligible au cockpit s'il est :

- actif ;
- `purchase_ok = True` ;
- stockable (`is_storable = True` sur le modèle produit Odoo 18).

Aucune règle basée sur le nom, la référence ou l'identité de la fécule de manioc.

---

## 8. Consommation moyenne

### 8.1 Période

- **90 jours glissants** par défaut ;
- paramètre configurable **au niveau société** (pas article par article en V1) ;
- la période effectivement utilisée est **affichée dans le cockpit**.

### 8.2 Mouvements retenus

Consommation = mouvements **terminés** (`done`) qui quittent un emplacement
**interne** de l'entrepôt de pilotage vers :

- un emplacement de **production** ;
- un emplacement **client**.

Les **retours** correspondants (production/client → interne) sont **déduits**
de la consommation nette sur la période.

### 8.3 Exclusions V1

Ne participent **pas** à la moyenne :

- transferts interne → interne ;
- mouvements annulés ;
- ajustements d'inventaire ;
- rebuts (traitement ultérieur possible) ;
- mouvements planifiés ou en attente.

### 8.4 Trois cas distincts (consommation)

Les situations suivantes **ne doivent pas être confondues** :

#### A. Historique insuffisant

L'article possède des flux exploitables, mais la période observée est **trop
courte** pour établir une moyenne fiable.

Critère V1 (paramètre société `min_history_days`, défaut **30 jours**) :

- la première date de mouvement de consommation exploitable dans la fenêtre est
  postérieure à `today − min_history_days` ;
- **ou** la fenêtre glissante configurée n'est pas entièrement couverte par
  l'historique disponible.

→ Statut principal : **Données insuffisantes**  
→ Alerte : **Historique insuffisant**

#### B. Aucune consommation observée

La période est **suffisamment longue** (historique exploitable sur toute la
fenêtre), mais la consommation nette sur la période est **nulle**.

Cela peut être **légitime** (article dormant, stock de sécurité, saisonnalité).

→ **Ne pas** qualifier automatiquement de « non traçable »  
→ La couverture en jours n'est **pas calculée** (division par zéro interdite)  
→ Le statut de risque repose alors sur le stock, les seuils, les réceptions et
  les alertes — **pas** sur une couverture journalière  
→ Alerte optionnelle informative : **Aucune consommation observée** (non bloquante)

#### C. Consommation non traçable (déclaratif V1)

La réalité métier indique une consommation, mais celle-ci **ne passe pas** par
des mouvements Odoo exploitables (§8.2).

**En V1, ce cas ne peut pas être déduit automatiquement** de l'absence de
mouvements.

Champ manuel sur **`product.template`** :

- `laplatine_procurement_consumption_untraceable` (booléen)

Lorsque coché :

→ Alerte : **Consommation non traçable**  
→ Message explicite dans le motif : les indicateurs de couverture peuvent être
  non significatifs

**Interdit** : déduire automatiquement « non traçable » d'une consommation nulle
ou d'un historique court.

### 8.5 Données indispensables absentes

Outre l'historique, le statut **Données insuffisantes** s'applique aussi si
des données **indispensables au calcul** sont absentes (ex. variante sans unité
de mesure stock, entrepôt de pilotage non configuré sur la société).

---

## 9. Seuils de sécurité

### 9.1 Source unique V1

Les seuils proviennent des **règles de réapprovisionnement standard Odoo**
(`stock.warehouse.orderpoint`) :

- `product_min_qty` ;
- `product_max_qty` ;
- règle rattachée à l'entrepôt / emplacement de pilotage.

### 9.2 Absence de second seuil

**Aucun champ « seuil métier » supplémentaire** n'est créé en V1.

### 9.3 Paramétrage incomplet

Si aucune règle exploitable n'existe, ou si `product_min_qty` n'est pas
renseigné de façon utilisable (`<= 0` ou règle absente) :

- alerte **Règle de réapprovisionnement absente ou incomplète** ;
- le cockpit **ne conclut pas** à une situation **Normale** faute de seuil ;
- le paramétrage min/max devient un **prérequis recette** pour les articles critiques.

### 9.4 Règles multiples et emplacements (V1)

Lorsqu'une variante possède :

- plusieurs règles de réapprovisionnement ;
- plusieurs emplacements ;
- des unités de mesure différentes ;
- une règle ne correspondant pas à l'entrepôt de pilotage ;

**Règle V1** :

> Ne retenir que la règle correspondant à **l'emplacement de stock principal**
> de l'entrepôt de pilotage (stock location de l'entrepôt).

En présence de **plusieurs règles concurrentes ou ambiguës** pour cet emplacement :

→ Alerte **Règle de réapprovisionnement absente ou incomplète** (ou alerte
  dédiée « paramétrage ambigu »)  
→ **Ne pas** sélectionner arbitrairement une règle

Toutes les quantités comparées (stock, min, max, reliquats PO) sont **converties
dans l'unité de mesure de stock de la variante** avant comparaison.

### 9.5 Prérequis recette

La fécule de manioc et les autres articles critiques devront faire l'objet d'un
**atelier de paramétrage min/max** avant la recette métier définitive.

---

## 10. Criticité métier (article)

Champ spécifique sur **`product.template`** :

| Valeur | Signification |
|---|---|
| Normale | Impact limité d'une rupture |
| Élevée | Impact significatif |
| Critique | Impact majeur sur l'activité |

Champ complémentaire V1 :

- `laplatine_procurement_consumption_untraceable` (booléen) — §8.4 C

La criticité exprime l'**impact métier** d'une rupture. Elle est **distincte**
du statut de risque calculé.

Un article peut être :

- intrinsèquement **Critique** ;
- et afficher un statut de risque **Normal** si l'approvisionnement est sécurisé.

Les quantités et le cockpit sont calculés au niveau **`product.product`**
(variante), les stocks Odoo étant gérés par variante.

---

## 11. Statuts, alertes et filtres

### 11.1 Principe

**Ne pas mélanger** dans un seul code :

- le niveau de risque ;
- le retard de réception ;
- l'absence de paramétrage ;
- le manque d'historique.

Plusieurs alertes peuvent coexister sur une même ligne.

### 11.2 Statut principal de risque (unique par ligne)

| Statut | Sens fonctionnel (V1) |
|---|---|
| **Données insuffisantes** | Historique ou données de base insuffisants pour conclure |
| **Normal** | Couverture et approvisionnements engagés compatibles avec le besoin |
| **À surveiller** | Couverture en baisse, seuil approché ou vigilance requise |
| **Action requise** | Commande, relance ou sécurisation à engager |
| **Critique** | Risque de rupture avant couverture suffisante, compte tenu des réceptions et délais |
| **Rupture** | Stock indisponible ou besoin non couvert à court terme |

Chaque statut doit être **explicable** par un motif lisible (`risk_reason`).

### 11.3 Alertes complémentaires (cumulables)

| Alerte | Condition type |
|---|---|
| Réception en retard | Flux entrant logistique attendu en retard (§13) — **n'écrase pas** le statut principal |
| Règle de réapprovisionnement absente ou incomplète | Pas de min exploitable, règle absente ou ambiguë (§9.4) |
| Fournisseur ou délai manquant | Aucun vendeur applicable ou délai absent |
| Historique insuffisant | Période d'observation trop courte (§8.4 A) |
| Aucune consommation observée | Période suffisante, conso nette nulle (§8.4 B) — informative |
| Aucune commande confirmée | Besoin identifié sans approvisionnement engagé (selon règle §12) |
| Consommation non traçable | Case manuelle cochée sur l'article (§8.4 C) — **jamais automatique** |

Le filtre **Réceptions en retard** reste disponible ; le retard **n'écrase pas**
le statut principal.

---

## 12. Principe de calcul du risque (V1)

### 12.1 Limites de la formule simple

La seule formule :

```text
couverture = virtual_available / consommation journalière
```

est **insuffisante** : le stock prévisionnel peut inclure une réception trop
tardive pour éviter une rupture intermédiaire.

### 12.2 Indicateurs et dates (gelés V1)

| Indicateur | Définition |
|---|---|
| **Stock actuel** | `qty_available` — périmètre entrepôt de pilotage |
| **Stock prévisionnel** | `virtual_available` — affiché, **non seul** critère de risque |
| **Consommation journalière moyenne** | Conso nette période / nb jours période (si > 0) |
| **Couverture actuelle (jours)** | Stock actuel / conso journalière — **si conso > 0** |
| **Quantité en commande confirmée** | Somme reliquats PO `purchase` non reçus |
| **Prochaine réception confirmée** | Date + qté — §13 |
| **Délai fournisseur** | Jours — vendeur applicable (§14) |
| **Date estimée de rupture physique** | Si conso > 0 : `today + (stock_actuel / conso_jour)` ; sinon **indéterminable** |
| **Date estimée d'atteinte du minimum** | Si conso > 0 et min exploitable : `today + max(0, (stock_actuel − min) / conso_jour)` ; sinon **indéterminable** |
| **Date limite de commande** | Si min exploitable et conso > 0 : `date_atteinte_minimum − délai_fournisseur` ; sinon **indéterminable** |
| **Date d'arrivée si commande aujourd'hui** | `today + délai_fournisseur` — **information seule**, distincte de la date limite |

Si seuil min **non exploitable** :

```text
Date limite de commande = indéterminable
Alerte = Règle de réapprovisionnement absente ou incomplète
```

### 12.3 Matrice déterministe du statut principal (gelée V1)

Le statut principal est déterminé par **priorité décroissante** — **première
situation applicable** :

| Priorité | Situation | Statut principal |
|---:|---|---|
| 1 | Données indispensables absentes (§8.5, historique §8.4 A, entrepôt non configuré…) | **Données insuffisantes** |
| 2 | Stock physique ≤ 0 | **Rupture** |
| 3 | Rupture physique projetée **avant** la prochaine réception confirmée (date estimée rupture < date prochaine réception, conso > 0) | **Critique** |
| 4 | Passage sous le **minimum** projeté **avant** la prochaine réception confirmée | **Action requise** |
| 5 | Date limite de commande **atteinte ou dépassée** (`today ≥ date_limite_commande`) | **Action requise** |
| 6 | Date limite de commande **proche** (`today ≥ date_limite_commande − marge_surveillance`) | **À surveiller** |
| 7 | Couverture et approvisionnements compatibles, paramétrage exploitable, données complètes | **Normal** |

**Paramètre société** `watch_lead_days` (marge « proche ») — **décision MOA : 7 jours** :

- paramétrable au niveau **`res.company`**, valeur par défaut **7** ;
- **jamais codée en dur** dans le moteur de calcul ;
- règle déterministe associée (sous réserve des priorités supérieures de la matrice) :

```text
Aujourd'hui < date_limite − watch_lead_days     → ne déclenche pas « À surveiller » seul
date_limite − watch_lead_days ≤ Aujourd'hui < date_limite → À surveiller (priorité 6)
Aujourd'hui ≥ date_limite                       → Action requise (priorité 5)
```

Si le paramétrage min/max est incomplet : le statut **Normal** (priorité 7) est
**inaccessible** ; les alertes de paramétrage sont posées.

Si conso = 0 (§8.4 B) : les priorités 3–6 basées sur les dates projetées ne
s'appliquent pas ; le statut repose sur stock, min, réceptions et alertes.

Chaque statut retourné doit inclure un **motif** (`risk_reason`) citant la
priorité et les dates/chiffres ayant déclenché la décision.

### 12.4 Projection « rupture avant prochaine réception »

Pour la priorité 3, comparer :

- **date estimée de rupture physique** (§12.2) ;
- **date prochaine réception confirmée** (§13).

Si rupture projetée **strictement avant** la réception → **Critique**.

Pour la priorité 4, comparer la projection de stock à la date de réception
avec le **minimum** orderpoint.

### 12.5 Action recommandée

Champ texte orienté utilisateur (ex. « Vérifier commande P0042 », « Relancer
fournisseur », « Paramétrer min/max ») — **sans exécuter** l'action dans Odoo.

---

## 13. Commandes fournisseurs et dates de réception

### 13.1 États de commande

| État PO | Traitement V1 |
|---|---|
| **Confirmée** (`purchase`) | Prise en compte dans approvisionnements engagés |
| **Brouillon / envoyée** (`draft`, `sent`) | Non considérée comme entrée sécurisée ; peut être signalée à part |
| **Annulée** | Exclue |
| Quantité reçue | Déduite du reliquat attendu |

### 13.2 Date opérationnelle de réception (priorité gelée)

Pour la **prochaine réception** et l'appréciation des **retards**, la date
retenue suit cet ordre de priorité :

1. **Date planifiée du mouvement entrant** ou du **transfert de réception**
   encore ouvert (`stock.move` / `stock.picking` entrants non terminés, liés à
   un reliquat PO confirmé) ;
2. **`purchase.order.line.date_planned`** en solution de repli ;
3. Si aucune date exploitable → alerte dédiée ; la réception n'est pas utilisée
   silencieusement dans les comparaisons de dates.

La **réception en retard** est appréciée à partir du **flux logistique entrant
réellement attendu** (priorité 1), et non uniquement de la ligne d'achat.

### 13.3 Agrégation

- **Prochaine réception** = entrée confirmée la plus proche (date la plus
  proche, reliquat > 0) ;
- quantités agrégées si plusieurs lignes le même jour ;
- demandes de prix en cours : information séparée, **ne couvrent pas** le besoin
  dans le calcul de risque.

---

## 14. Fournisseur de référence

Le fournisseur affiché et le délai utilisés proviennent de la **logique standard
Odoo** de sélection des vendeurs (`product.supplierinfo`), en tenant compte
autant que possible de :

- séquence fournisseur ;
- société ;
- dates de validité ;
- quantité minimale ;
- unité d'achat applicable ;
- contexte de la variante.

**Interdit en V1** : règle simpliste « premier fournisseur » ou « dernier achat »
sans logique standard.

Si aucun fournisseur n'est clairement applicable → alerte **Fournisseur ou délai
manquant** ; pas de choix arbitraire silencieux.

---

## 15. Informations affichées dans le cockpit (V1)

Liste minimale — base de cadrage, ajustable à l'implémentation :

| Colonne | Source / nature |
|---|---|
| Article | `product.product` |
| Catégorie | Standard |
| Criticité métier | Champ spécifique template |
| Fournisseur de référence | Sélection standard |
| Délai (j) | `supplierinfo.delay` |
| Stock disponible | Standard, périmètre entrepôt |
| Stock prévisionnel | Standard |
| Qté en commande (confirmée) | Calcul PO |
| Prochaine réception | Date + qté |
| Conso moyenne / jour | Calcul module |
| Période conso | Paramètre société (affichage global ou colonne info) |
| Couverture actuelle (j) | Calcul module (si conso > 0) |
| Date estimée rupture physique | Calcul module (§12.2) |
| Date estimée atteinte minimum | Calcul module (§12.2) |
| Date limite de commande | Calcul module (§12.2) |
| Min / max réappro | Orderpoint entrepôt (§9.4) |
| Statut de risque | Matrice §12.3 |
| Motif du statut | Texte |
| Alertes | Tags cumulables |
| Action recommandée | Texte |
| Dernière actualisation | Horodatage rafraîchissement cockpit |
| Actualisé par | Utilisateur (si disponible) |

---

## 16. Architecture technique proposée

### 16.1 Options comparées

| Option | Avantages | Inconvénients |
|---|---|---|
| **A. Extension `product.product`** avec champs calculés | Simple, peu de modèles | Filtres/tri sur champs non stockés difficiles ; pollution fiche produit |
| **B. Modèle cockpit dédié** (`laplatine.procurement.control.line`) | Filtres, tri, statuts stockables ; séparation pilotage / fiche produit | Modèle supplémentaire ; rafraîchissement à gérer |
| **C. Vue SQL `_auto = False`** | Lecture performante | Moins flexible ; actions et liens plus lourds ; maintenance SQL |

### 16.2 Choix retenu pour la V1

**Option B — modèle cockpit dédié**, alimenté par **rafraîchissement explicite** :

- une ligne par variante éligible dans le périmètre entrepôt ;
- champs calculés **stockés** lors du rafraîchissement ;
- **aucune duplication** du stock : valeurs lues depuis les modèles standard au moment du calcul ;
- extension **`product.template`** : criticité métier + indicateur consommation non traçable (§8.4 C) ;
- paramètres **`res.company`** : entrepôt de pilotage, période de consommation (jours), `min_history_days`, `watch_lead_days`.

### 16.3 Fraîcheur du cockpit (obligatoire V1)

Le cockpit est une **photographie temporaire**. Il affiche :

- **Dernière actualisation** (date/heure) ;
- **Actualisé par** (utilisateur, si disponible) ;
- bouton **Actualiser** visible et explicite ;
- **avertissement visible** si les données dépassent un âge configurable (paramètre société `stale_warning_hours`, défaut proposé : **24 h**).

L'ouverture du menu **ne déclenche pas** silencieusement un recalcul long : l'utilisateur
autorisé lance **Actualiser** (recalcul ~20 articles acceptable en V1).

### 16.4 Sécurité (V1)

| Groupe | Droits |
|---|---|
| Consultation cockpit | Lecture cockpit + navigation vers objets **déjà autorisés** par les droits standards |
| Pilotage approvisionnements | Actualiser le cockpit |
| Paramétrage | Modifier criticité, consommation non traçable, paramètres société |

Le cockpit **ne contourne pas** les droits sur commandes, réceptions, fournisseurs
ou articles.

### 16.5 Dépendances minimales

| Module | Obligatoire V1 |
|---|---|
| `stock` | Oui |
| `purchase` | Oui |
| `purchase_stock` | Oui |
| `mrp` | Oui — consommation production ; installé en lab/prod |

Pas de dépendance `account` en V1.

Volume actuel lab (~20 articles) : calcul à la demande **acceptable**.  
Évolution V1.1+ : cron de rafraîchissement si le volume ou les performances l'exigent.

Aucun module OCA supplémentaire requis sans justification ultérieure.

---

## 17. Périmètre V1

### 17.1 Inclus

- Menu cockpit permanent ;
- articles stockables et achetables ;
- indicateurs §15 ;
- statuts §11.2 et alertes §11.3 ;
- calcul de risque §12 ;
- paramètres société (entrepôt, période conso) ;
- navigation vers objets standards ;
- recette fécule de manioc + articles génériques ;
- tests automatisés sur règles de statut et alertes (jeu de données lab).

### 17.2 Exclus

- Second stock ou second seuil métier ;
- Workflow validation commandes ;
- génération automatique de commandes ;
- alertes email / messagerie ;
- portail fournisseur ;
- circuit codé fécule ;
- prévision commerciale avancée ;
- coût financier de rupture ;
- rebuts dans la conso moyenne ;
- déploiement production sans GO MOA.

---

## 18. Critères d'acceptation fonctionnels (CA)

| ID | Critère |
|---|---|
| CA-01 | Accès au cockpit **La Platine → Pilotage des approvisionnements** |
| CA-02 | Liste des articles stockables et achetables du périmètre entrepôt |
| CA-03 | Affichage stock disponible et prévisionnel (standard) |
| CA-04 | Consommation moyenne 90 j (paramètre société visible) |
| CA-05 | Distinction criticité métier vs statut de risque |
| CA-06 | Statuts principaux §11.2 avec motif explicite |
| CA-07 | Alertes cumulables §11.3, dont réception en retard sans écraser le statut |
| CA-08 | Détection paramétrage min/max incomplet ou ambigu — jamais « Normal » par défaut |
| CA-09 | Historique insuffisant (§8.4 A) → **Données insuffisantes** — distinct de conso nulle |
| CA-09b | Conso nulle sur période suffisante (§8.4 B) — **sans** alerte auto « non traçable » |
| CA-10 | Prise en compte PO confirmées uniquement pour approvisionnements engagés |
| CA-11 | Prochaine réception : priorité mouvement/picking entrant, repli `date_planned` PO |
| CA-12 | Fournisseur de référence via logique standard Odoo |
| CA-13 | Rupture projetée **avant** prochaine réception → **Critique** (matrice §12.3) |
| CA-14 | Navigation vers fiche article, PO, orderpoint, fournisseur |
| CA-15 | Filtres : critique métier, action requise, rupture, réceptions en retard |
| CA-16 | Même logique pour fécule et articles non critiques |
| CA-17 | Aucune règle codée sur le nom « fécule » ou « manioc » |
| CA-18 | Cockpit affiche dernière actualisation ; bouton **Actualiser** pour recalcul |
| CA-19 | Consultation vs paramétrage / actualisation selon groupes — pas de contournement des droits standards |

---

## 19. Cas pilote — fécule de manioc

Validation sur l'article **FÉCULE DE MANIOC** (données lab/prod) :

- criticité = **Critique** ;
- min/max orderpoint paramétrés en atelier préalable ;
- scénarios recette : stock confortable, commande en retard, risque rupture avant réception, paramétrage absent.

Aucune règle logicielle basée sur l'identifiant ou le libellé de l'article.

---

## 20. Prérequis données (avant recette métier définitive)

- [ ] Atelier min/max sur fécule et articles critiques ;
- [ ] Délais fournisseurs renseignés sur les articles pilotés ;
- [ ] Confirmation entrepôt principal de pilotage ;
- [ ] Identification des articles à consommation non traçable (liste recette) ;
- [ ] Jeu de PO confirmées / en retard pour scénarios de test.

---

## 21. Gouvernance

| Règle | Statut |
|---|---|
| GO faisabilité MOA | ✅ |
| GO MOA spec V1 | ✅ |
| Arbitrage `watch_lead_days` | ✅ **7 jours** (défaut société, paramétrable) |
| GO développement | ✅ **accordé — périmètre V1 gelé** |
| GO déploiement production | ⏸ — GO MOA explicite séparé |
| Travail initial | Lab `laplatine-odoo18-lab` / `laplatine_prod` uniquement |
| Gel périmètre V1 | ✅ |

---

## 22. Questions ouvertes résiduelles

1. Affichage des PO `sent` : colonne info ou panneau latéral (cosmétique).
2. Cron de rafraîchissement : différé V1.1 sauf besoin recette.

---

## 23. Historique

### 5 juillet 2026 — Spec V1 initiale

- Note de cadrage V0.1 transmise.
- GO faisabilité technique Dev.
- GO faisabilité MOA avec réserves : consommation 90 j, orderpoint seul, criticité
  article, statuts + alertes séparés, risque avant prochaine réception, PO
  confirmées, fournisseur standard Odoo, entrepôt principal.
- Rédaction `SPECIFICATION_V1.md`.

### 5 juillet 2026 — Revue MOA spec V1

- **GO MOA** sur la spécification fonctionnelle V1.
- Corrections intégrées : dates limite/atteinte minimum/rupture, matrice
  déterministe §12.3, trois cas consommation §8.4, date réception opérationnelle
  §13, fraîcheur cockpit §16.3, orderpoints multiples §9.4, CA-18/CA-19.
- **GO développement conditionnel** : confirmation `watch_lead_days` (7 j proposés).

### 5 juillet 2026 — Gel V1 et GO développement

- **Arbitrage MOA** : `watch_lead_days = 7 jours` (paramètre société, défaut 7).
- **GO développement complet V1** accordé — périmètre fonctionnel gelé.
- Production : STOP jusqu'à GO MOA explicite séparé.
