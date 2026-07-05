# Guide de recette fonctionnelle MOA — `laplatine_procurement_control` V1

| Élément | Valeur |
|---------|--------|
| Document | `GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md` |
| Version module | `18.0.1.1.0` |
| Commit Git de référence | `9e61e56` (branche `main`, dépôt `odoo18-addons-dorevia`) |
| Environnement | **Lab uniquement** — `laplatine-odoo18-lab` |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Production | **STOP** — aucun déploiement sans GO MOA explicite séparé |
| Spécification gelée | [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md) |
| Tests automatisés lab | **43/43 verts** (dernière exécution Dev avant recette) |
| Statut recette | ⏸ **À exécuter par la MOA** |

---

## 0. Objectif de la recette

Vérifier que le **cockpit de pilotage des approvisionnements** raconte la bonne histoire métier pour un utilisateur La Platine :

- lecture et interprétation au-dessus d’Achats / Stock / Fabrication ;
- statut principal unique et explicable (matrice §12.3) ;
- alertes cumulables distinctes (§11.3) ;
- fraîcheur explicite (actualisation manuelle, pas de recalcul silencieux) ;
- navigation vers les objets standards sans contourner les droits.

Ce guide distingue systématiquement :

| Type | Description |
|------|-------------|
| **Préparation** | Manipulation des données Odoo (stock, PO, orderpoint, article…) |
| **Actualiser** | Clic sur le bouton **Actualiser** du cockpit (Manager uniquement) |
| **Résultat attendu** | Ce que la MOA doit voir dans la liste ou la fiche ligne |
| **Preuves** | Captures, références document, horodatage |
| **Remise en état** | Actions pour restaurer l’article ou annuler la simulation |

---

## 1. Préambule obligatoire (à compléter avant tout scénario)

### 1.1 Relevé d’environnement

À remplir **avant** le premier scénario. Conserver une capture ou export.

| Champ | Valeur relevée | OK |
|-------|----------------|-----|
| Date et heure début recette | | ☐ |
| Société active (nom) | | ☐ |
| Entrepôt de pilotage configuré | | ☐ |
| Période de consommation (jours) | Attendu : **90** par défaut | ☐ |
| `min_history_days` | Attendu : **30** par défaut | ☐ |
| `watch_lead_days` | Attendu : **7** (décision MOA) | ☐ |
| `stale_warning_hours` | Attendu : **24** par défaut | ☐ |
| Utilisateur MOA recette (login) | | ☐ |
| Groupe Consultation attribué (oui/non) | | ☐ |
| Groupe Actualisation / Manager (oui/non) | | ☐ |
| Groupe Paramétrage (oui/non) | | ☐ |
| Module `laplatine_procurement_control` | État : **installé** | ☐ |
| Version module affichée | `18.0.1.1.0` | ☐ |

**Chemins Odoo lab :**

- Paramètres société : **Paramètres** → **Sociétés** → société active → onglet **Pilotage approvisionnements**
- Cockpit : **Inventaire** → **Pilotage approvisionnements** → **Cockpit**
- Criticité / consommation non traçable : fiche **Article** → onglet **Inventaire** → groupe **Pilotage approvisionnements** (groupe Paramétrage)

**Commande Dev (optionnelle — relevé technique) :**

```bash
cd laplatine-odoo18-lab
docker compose run --rm --no-deps odoo odoo shell \
  --config=/etc/odoo/odoo.conf \
  --database=laplatine_prod <<'PY'
company = env.company
print("Société:", company.name)
print("Entrepôt pilotage:", company.laplatine_procurement_warehouse_id.display_name)
print("Conso (j):", company.laplatine_procurement_consumption_days)
print("Min history (j):", company.laplatine_procurement_min_history_days)
print("Watch lead (j):", company.laplatine_procurement_watch_lead_days)
print("Stale warning (h):", company.laplatine_procurement_stale_warning_hours)
mod = env['ir.module.module'].search([('name','=','laplatine_procurement_control')])
print("Module:", mod.state, mod.latest_version)
PY
```

### 1.2 Utilisateurs de recette

Créer ou désigner **deux utilisateurs distincts** (recommandé) :

| Rôle | Groupe Odoo | Usage |
|------|-------------|-------|
| **Consultation** | Pilotage approvisionnements / Consultation | R1 — lecture seule |
| **Manager** | Pilotage approvisionnements / Actualisation | R2–R18 — actualisation |

Ne pas utiliser le super-utilisateur Admin pour valider la sécurité métier (R1), sauf pour la préparation des données.

### 1.3 Convention de preuves

Pour chaque scénario, archiver dans un dossier `recette_procurement_control_YYYYMMDD/` :

- capture écran liste cockpit (statut + alertes visibles) ;
- capture fiche ligne (motif, dates, navigation) ;
- références Odoo : `product.product` ID, PO (`purchase.order`), picking (`stock.picking`), orderpoint ID ;
- horodatage de l’**Actualiser** et utilisateur affiché.

---

## 2. Atelier min/max préalable — fécule de manioc (MOA métier)

> **Les valeurs min/max ne sont pas inventées par le Dev.**  
> Elles doivent être **proposées, saisies et validées par la MOA métier** avant les scénarios qui s’appuient sur la fécule.

### 2.1 Objectif

Paramétrer la **fécule de manioc** comme article critique pilote avec une règle de réapprovisionnement **unique et exploitable** sur l’entrepôt de pilotage.

### 2.2 Fiche atelier (à compléter MOA)

| Question | Réponse MOA |
|----------|-------------|
| Variante retenue (`product.product`, référence interne) | |
| Unité de stock | |
| Emplacement / entrepôt de la règle | = entrepôt de pilotage §1.1 |
| **Minimum** proposé | |
| **Maximum** proposé | |
| Justification métier du minimum | |
| Justification métier du maximum | |
| Fournisseur de référence | |
| Délai fournisseur (j) | |
| Criticité métier article | **Critique** (recommandé) |
| Règles concurrentes sur le même emplacement ? | Attendu : **non** |
| Validé par (nom, date) | |

### 2.3 Manipulations

1. Ouvrir la variante fécule (article stockable, achetable).
2. Vérifier **Inventaire → Règles de réapprovisionnement** : une seule règle sur `lot_stock` de l’entrepôt de pilotage.
3. Saisir `product_min_qty` **> 0** et `product_max_qty` ≥ min (valeurs MOA).
4. Vérifier fournisseur / `supplierinfo` avec délai renseigné.
5. Poser criticité **Critique** sur le modèle article.
6. **Ne pas** cocher « Consommation non traçable » sauf scénario R14.

### 2.4 Contrôles

| Contrôle | Attendu |
|----------|---------|
| Une seule règle sur l’emplacement principal | ☐ |
| Min > 0 | ☐ |
| Pas de deuxième règle ambiguë | ☐ |
| Fournisseur applicable | ☐ |

**Remise en état :** conserver les valeurs validées MOA pour toute la recette ; documenter tout écart.

---

## 3. Catalogue d’articles de recette

Préparer **cinq profils** (création ou sélection d’articles existants).  
**Aucune attente fonctionnelle ne doit reposer sur le nom « fécule »** — uniquement sur les données (stock, conso, orderpoint, PO…).

| ID recette | Profil | Rôle | Scénarios principaux |
|------------|--------|------|----------------------|
| **REC-ART-01** | Fécule de manioc | Critique pilote | Atelier §2, R3, R4–R7, R17 |
| **REC-ART-02** | Article criticité **Normale**, consommation régulière | Référence stable | R3, R9 |
| **REC-ART-03** | Sans consommation observée (historique OK, conso nette = 0) | Cas §8.4 B | R13 |
| **REC-ART-04** | Paramétrage min/max absent ou min ≤ 0 | Cas §9.3 | R11 |
| **REC-ART-05** | Consommation non traçable **cochée manuellement** | Cas §8.4 C | R14 |

Tenir un tableau de suivi :

| ID recette | `product.product` ID | Référence interne | Nom affiché | Prêt recette |
|------------|---------------------|-----------------|-------------|--------------|
| REC-ART-01 | | | | ☐ |
| REC-ART-02 | | | | ☐ |
| REC-ART-03 | | | | ☐ |
| REC-ART-04 | | | | ☐ |
| REC-ART-05 | | | | ☐ |

---

## 4. Légende des scénarios

Chaque scénario utilise le tableau de preuve suivant (à dupliquer ou compléter) :

| Élément | Contenu |
|---------|---------|
| **Identifiant** | R01…R18 |
| **Préconditions** | Données et utilisateur |
| **Préparation** | Manipulations Odoo (hors Actualiser) |
| **Actualiser** | Qui clique, quand |
| **Résultat attendu** | Statut, alertes, chiffres, motif |
| **Résultat obtenu** | *(MOA)* |
| **Preuves** | Captures + références |
| **Verdict** | GO / KO / Réserve |
| **Commentaire** | Écarts, décisions |
| **Remise en état** | *(si applicable)* |

---

## 5. Scénarios MOA

### R01 — Accès et sécurité

| Élément | Détail |
|---------|--------|
| **Identifiant** | R01 |
| **Préconditions** | Utilisateurs Consultation et Manager créés ; module installé |
| **Préparation** | Aucune |
| **Actualiser** | — |

**Manipulations :**

1. Se connecter en **Consultation** → ouvrir **Inventaire → Pilotage approvisionnements → Cockpit**.
2. Vérifier que la liste s’affiche (lecture).
3. Vérifier que le bouton **Actualiser** est **absent ou inaccessible** ; tenter un rafraîchissement (doit échouer ou être impossible).
4. Se connecter en **Manager** → vérifier que **Actualiser** est visible et fonctionne.
5. Depuis une ligne, tester **Article** ; avec un utilisateur **sans** droit Achats sur un PO, vérifier qu’ouvrir **Commande** respecte les droits (accès refusé ou menu absent selon profil).

| Résultat attendu | |
|------------------|---|
| Consultation : accès cockpit OK, pas d’actualisation | ☐ |
| Manager : actualisation OK | ☐ |
| Navigation : pas de contournement des droits standards | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | — |

**Critère bloquant clôture :** oui.

---

### R02 — Rafraîchissement et fraîcheur

| Élément | Détail |
|---------|--------|
| **Identifiant** | R02 |
| **Préconditions** | Manager ; au moins un article éligible dans le périmètre |
| **Préparation** | Paramétrer `stale_warning_hours = 24` sur la société |
| **Actualiser** | Manager — deux fois de suite ; puis test obsolescence |

**Manipulations :**

1. Manager : ouvrir le cockpit **sans** cliquer Actualiser → noter l’état (données vides ou anciennes — **pas** de recalcul automatique).
2. Cliquer **Actualiser** → noter **Dernière actualisation** et **Actualisé par**.
3. Compter les lignes pour un article donné → recliquer **Actualiser** → **une seule ligne** par article/société.
4. *(Simulation obsolescence)* : soit attendre > 24 h, soit demander au Dev de baisser temporairement `stale_warning_hours` à **1** sur le lab, rouvrir le cockpit → bandeau / surbrillance « données obsolètes ».
5. Remettre `stale_warning_hours = 24` après le test.

| Résultat attendu | |
|------------------|---|
| Bouton Actualiser visible (Manager) | ☐ |
| Date + utilisateur renseignés après actualisation | ☐ |
| Pas de doublon après 2 actualisations | ☐ |
| Avertissement obsolescence visible si délai dépassé | ☐ |
| Pas de recalcul silencieux à l’ouverture | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Restaurer `stale_warning_hours = 24` |

---

### R03 — Situation normale

| Élément | Détail |
|---------|--------|
| **Identifiant** | R03 |
| **Préconditions** | REC-ART-02 (ou fécule après atelier §2) |
| **Préparation** | Voir ci-dessous |
| **Actualiser** | Manager |

**Préparation (REC-ART-02 type) :**

- Stock disponible **> minimum** (entrepôt pilotage).
- Orderpoint : min > 0, max ≥ min, **règle unique**.
- Historique consommation ≥ `min_history_days` avec conso journalière > 0.
- Fournisseur + délai renseignés.
- PO confirmée couvrant le besoin **ou** stock suffisant jusqu’à prochaine réception sans rupture intermédiaire.
- Date limite de commande **non** atteinte et **hors** fenêtre 7 jours si calculable.

| Résultat attendu | |
|------------------|---|
| Statut **Normal** | ☐ |
| Pas d’alerte bloquante (alertes informatives acceptées) | ☐ |
| Motif cite priorité 7 ou équivalent compréhensible | ☐ |
| Couverture (j), dates cohérentes avec stock et conso | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Conserver ou documenter jeux de données |

**Critère bloquant clôture :** oui.

---

### R04 — Date limite proche (À surveiller)

| Élément | Détail |
|---------|--------|
| **Identifiant** | R04 |
| **Préconditions** | Article avec conso > 0, min exploitable, délai fournisseur connu |
| **Préparation** | Ajuster stock / min / conso pour que **date limite ∈ [today ; today+7]** et priorités 1–5 non actives |
| **Actualiser** | Manager |

**Indication de construction (MOA + Dev lab) :**

- Réduire le stock au-dessus du min mais proche de la zone où `date_limite − today ≤ 7 j`.
- Vérifier en fiche ligne : **Date limite commande** dans les 7 prochains jours.

| Résultat attendu | |
|------------------|---|
| Statut **À surveiller** | ☐ |
| Motif mentionne date limite et marge 7 j | ☐ |
| Pas de statut Action requise si today < date limite | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Rétablir stock / min d’origine |

---

### R05 — Date limite atteinte (Action requise)

| Élément | Détail |
|---------|--------|
| **Identifiant** | R05 |
| **Préconditions** | Même article que R04 possible, autre jeu de données |
| **Préparation** | `today ≥ date limite commande` ; priorités 1–4 **non** actives |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Statut **Action requise** (priorité 5) | ☐ |
| Action recommandée explicite (commander / sécuriser) | ☐ |
| **Pas** de bascule Critique si règle 3 ne s’applique pas | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Rétablir paramètres stock |

**Critère bloquant clôture :** oui.

---

### R06 — Rupture avant prochaine réception (Critique)

| Élément | Détail |
|---------|--------|
| **Identifiant** | R06 |
| **Préconditions** | Conso > 0 ; PO confirmée future ; REC-ART-01 ou REC-ART-02 |
| **Préparation** | Cas central V1 : |

**Construction du cas :**

1. Stock actuel modeste mais **> 0**.
2. Consommation journalière telle que **date rupture physique < date prochaine réception**.
3. **Stock prévisionnel (`virtual_available`) peut rester positif** (réception incluse trop tard).
4. PO en état **purchase** avec date réception **après** la rupture projetée.

| Résultat attendu | |
|------------------|---|
| Statut **Critique** | ☐ |
| Date rupture **<** date prochaine réception | ☐ |
| Motif cite priorité 3 et les deux dates | ☐ |
| `virtual_available` positif **n’a pas** masqué le risque | ☐ |

| Résultat obtenu | |
| Preuves | Capture : stock dispo, stock prévi., dates, statut |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Annuler PO test ou réceptionner ; rétablir stock |

**Critère bloquant clôture :** oui.

---

### R07 — Rupture physique

| Élément | Détail |
|---------|--------|
| **Identifiant** | R07 |
| **Préconditions** | Données suffisantes (entrepôt OK, pas historique insuffisant seul) |
| **Préparation** | Stock physique **≤ 0** sur entrepôt pilotage (inventaire ou consommation) |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Statut **Rupture** (priorité 2) | ☐ |
| Motif lisible (stock ≤ 0) | ☐ |
| Si historique insuffisant **simultané** : priorité 1 gagne (R12) — documenter | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Réintégrer stock |

**Critère bloquant clôture :** oui.

---

### R08 — Réception en retard

| Élément | Détail |
|---------|--------|
| **Identifiant** | R08 |
| **Préconditions** | PO confirmée avec reliquat ; date flux entrant **< today** |
| **Préparation** | |

**Construction :**

1. Confirmer une PO avec réception planifiée **dans le passé** (date mouvement entrant ou `date_planned` en repli).
2. Laisser le picking entrant **non terminé**.
3. Noter le statut principal **avant** actualisation (pour vérifier qu’il ne devient pas « retard » seul).

| Résultat attendu | |
|------------------|---|
| Alerte **Réception en retard** présente | ☐ |
| Statut principal **inchangé** par l’alerte seule | ☐ |
| Lien **Commande** / **Réception** fonctionnel | ☐ |
| Date retenue = flux logistique entrant si mouvement ouvert | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Réceptionner ou annuler PO test |

**Critère bloquant clôture :** oui.

---

### R09 — Réception partielle

| Élément | Détail |
|---------|--------|
| **Identifiant** | R09 |
| **Préconditions** | PO confirmée 100 unités (ex.) |
| **Préparation** | Réceptionner **40** ; laisser **60** en reliquat |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Qté en commande = **60** (pas 100) | ☐ |
| Qté prochaine réception cohérente avec reliquat | ☐ |
| Pas de double comptage des 40 reçues | ☐ |

| Résultat obtenu | |
| Preuves | PO + capture cockpit |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Clôturer ou annuler PO test |

---

### R10 — Demande de prix non sécurisée

| Élément | Détail |
|---------|--------|
| **Identifiant** | R10 |
| **Préconditions** | Article avec besoin identifié ; **aucune** PO `purchase` |
| **Préparation** | Créer RFQ **draft** ou **sent** (quantité significative) **sans** confirmer |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Qté en commande confirmée = **0** | ☐ |
| RFQ n’entre pas dans prochaine réception sécurisée | ☐ |
| Risque calculé **sans** cette entrée | ☐ |
| Alerte « Aucune commande confirmée » possible si statut l’exige | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Annuler RFQ |

---

### R11 — Min/max absent ou ambigu

| Élément | Détail |
|---------|--------|
| **Identifiant** | R11 |
| **Préconditions** | REC-ART-04 |
| **Préparation** | Variante A : **aucune** règle ; Variante B : **deux** règles même emplacement (si Odoo le permet) ou min = 0 |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Alerte **Règle de réapprovisionnement absente ou incomplète** | ☐ |
| Statut **Normal** **inaccessible** | ☐ |
| Aucune sélection arbitraire de min | ☐ |
| Action recommandée orientée paramétrage | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Supprimer règles test ; recréer règle valide |

**Critère bloquant clôture :** oui.

---

### R12 — Historique insuffisant

| Élément | Détail |
|---------|--------|
| **Identifiant** | R12 |
| **Préconditions** | Article **récent** ou premiers mouvements conso **< min_history_days** |
| **Préparation** | Créer article + 1 mouvement conso sur les **5 derniers jours** seulement |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Statut **Données insuffisantes** | ☐ |
| Alerte **Historique insuffisant** | ☐ |
| Couverture (j) **non** affichée de façon trompeuse | ☐ |
| Pas de projection date si conso non fiable | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Archiver article test |

**Critère bloquant clôture :** oui.

---

### R13 — Consommation nulle légitime

| Élément | Détail |
|---------|--------|
| **Identifiant** | R13 |
| **Préconditions** | REC-ART-03 — article ancien, **aucun** mouvement conso sur 90 j |
| **Préparation** | Vérifier case « Consommation non traçable » **décochée** |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Conso moyenne / jour = **0** | ☐ |
| Couverture (j) **non** calculée (0 ou vide) | ☐ |
| Alerte **Aucune consommation observée** (informative) possible | ☐ |
| **Pas** d’alerte « Consommation non traçable » automatique | ☐ |
| Décision via stock / seuils / réceptions | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | — |

---

### R14 — Consommation non traçable déclarée

| Élément | Détail |
|---------|--------|
| **Identifiant** | R14 |
| **Préconditions** | REC-ART-05 |
| **Préparation** | Cocher **Consommation non traçable** sur le modèle article |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Alerte **Consommation non traçable** | ☐ |
| Message : indicateurs de couverture **peuvent être non significatifs** | ☐ |
| **Pas** de déduction auto depuis conso nulle (R13) | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Décocher la case |

---

### R15 — Fournisseur ou délai manquant

| Élément | Détail |
|---------|--------|
| **Identifiant** | R15 |
| **Préconditions** | Article sans `supplierinfo` applicable |
| **Préparation** | Retirer ou désactiver fournisseurs ; conserver orderpoint et stock |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Alerte **Fournisseur ou délai manquant** | ☐ |
| Aucun fournisseur affiché arbitrairement | ☐ |
| Date limite indéterminable si délai requis | ☐ |
| Motif / action compréhensibles | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Rétablir supplierinfo |

---

### R16 — Conversion d’unités

| Élément | Détail |
|---------|--------|
| **Identifiant** | R16 |
| **Préconditions** | Article stock en **Unité(s)** ; achat en **Douzaine(s)** |
| **Préparation** | PO confirmée : 2 douzaines ; réception partielle 1 douzaine → reliquat 12 unités |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Qté en commande ≈ **12 unités** (pas 24 ni 1) | ☐ |
| Min/max et stock comparés en **unité de stock** | ☐ |
| Affichage cohérent (pas de mélange douzaines/unités sur une même colonne) | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Annuler PO ; remettre UoM standard si besoin |

---

### R17 — Navigation

| Élément | Détail |
|---------|--------|
| **Identifiant** | R17 |
| **Préconditions** | Ligne cockpit avec liens renseignés (fournisseur, PO, picking, orderpoint) |
| **Préparation** | Jeu R06 ou R09 |
| **Actualiser** | Manager puis tests Consultation |

**Manipulations :** depuis la **fiche ligne**, cliquer : Article | Fournisseur | Règle réappro | Commande | Réception.

| Résultat attendu | |
|------------------|---|
| Chaque bouton ouvre le **bon** enregistrement | ☐ |
| Boutons masqués si lien absent | ☐ |
| Utilisateur sans droit : accès refusé Odoo standard | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | — |

---

### R18 — Suppression du périmètre

| Élément | Détail |
|---------|--------|
| **Identifiant** | R18 |
| **Préconditions** | Article présent au cockpit |
| **Préparation** | Désactiver `Achat` (`purchase_ok = False`) ou archiver l’article |
| **Actualiser** | Manager |

| Résultat attendu | |
|------------------|---|
| Ligne **supprimée** du cockpit | ☐ |
| Pas de ligne orpheline | ☐ |
| Réactiver achat + Actualiser → ligne **réapparaît** | ☐ |

| Résultat obtenu | |
| Preuves | |
| Verdict | ☐ GO ☐ KO ☐ Réserve |
| Commentaire | |
| Remise en état | Réactiver `purchase_ok` |

---

## 6. Synthèse des scénarios

| ID | Intitulé | Bloquant clôture | Verdict |
|----|----------|------------------|---------|
| R01 | Accès et sécurité | **Oui** | |
| R02 | Rafraîchissement et fraîcheur | Non | |
| R03 | Situation normale | **Oui** | |
| R04 | Date limite proche | Non | |
| R05 | Action requise | **Oui** | |
| R06 | Rupture avant réception | **Oui** | |
| R07 | Rupture physique | **Oui** | |
| R08 | Réception en retard | **Oui** | |
| R09 | Réception partielle | Non | |
| R10 | RFQ non sécurisée | Non | |
| R11 | Min/max absent ou ambigu | **Oui** | |
| R12 | Historique insuffisant | **Oui** | |
| R13 | Consommation nulle | Non | |
| R14 | Consommation non traçable | Non | |
| R15 | Fournisseur manquant | Non | |
| R16 | Conversion UoM | Non | |
| R17 | Navigation | Non | |
| R18 | Suppression périmètre | Non | |

---

## 7. Verdict global de recette

À compléter par la MOA après exécution de **tous** les scénarios bloquants.

| Verdict | Condition |
|---------|-----------|
| **GO recette V1** | Tous les scénarios **bloquants** en GO ; écarts mineurs documentés et acceptés |
| **GO avec réserves** | Bloquants OK ; réserves sur scénarios non bloquants avec plan de correction |
| **KO recette** | Au moins un scénario **bloquant** en KO non accepté |

### 7.1 Scénarios bloquants (rappel)

R01, R03, R05, R06, R07, R08, R11, R12.

### 7.2 Décision MOA

| Champ | Valeur |
|-------|--------|
| Verdict global | ☐ GO recette V1 ☐ GO avec réserves ☐ KO recette |
| Date | |
| Signataire MOA | |
| Réserve / actions correctives | |
| GO déploiement production | ☐ Non — **STOP maintenu** ☐ Oui — *(GO séparé requis)* |

---

## 8. Dettes connues (hors périmètre recette V1)

| Dette | Impact recette lab | Production |
|-------|-------------------|------------|
| Paramètres sur `res.company` (pas `res.config.settings`) | Acceptable lab | Migration avant prod |
| Conflit `facturx_level` sur base lab | N’empêche pas la recette | À traiter avant prod |
| Cron de rafraîchissement | Non testé V1 | V1.1+ |

---

## 9. Références

- Spécification gelée : [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md)
- Note de cadrage : [`note_cadrage.md`](note_cadrage.md)
- README module : [`README.md`](README.md)
- Dépôt Git : `doreviateam/odoo18-addons-dorevia` — commit `9e61e56`

---

*Document préparé pour exécution MOA sur lab — production maintenue en STOP.*
