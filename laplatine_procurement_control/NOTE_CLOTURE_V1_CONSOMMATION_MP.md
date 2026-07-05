# Note de clôture V1 — Consommation matières premières La Platine

| Élément | Valeur |
|---------|--------|
| **Référence lot** | `LAPLATINE-CONS-MP-001` |
| **Module** | `laplatine_procurement_control` |
| **Version livrable** | `18.0.1.6.0` (V1.2 — recentrage cockpit) |
| **Commit de référence** | _voir `origin/main` après push CONS-MP-002_ |
| **Date clôture lab** | 2026-07-05 |
| **Production** | **STOP** — en attente de décision de déploiement explicite |

---

## 1. Verdict consolidé

> **Slices 1 à 4 : GO Dev / GO QA / GO MOA UI sur le lab.**
>
> **CONS-MP-002 (V1.1) : GO Dev / GO QA / GO MOA UI sur le lab — wizards séparés.**
>
> **CONS-MP-003 (V1.2) : GO Dev lab — cockpit limité aux articles « Suivi consommation La Platine ».**
>
> **V1 Consommation matières premières : fonctionnellement complète.**
>
> **Production : STOP jusqu'à GO MOA déploiement.**

| Slice / lot | Contenu | Verdict |
|-------------|---------|---------|
| 1 | Socle, booléen article, config société, groupes, menus, wizard squelette | GO |
| 2 | Lecture emplacement / stock, auto-sélection | GO |
| 3 | Enregistrement consommation (mouvement standard → Production) | GO |
| 4 | Correction inventaire, motif traçable, seuil min post-opération | GO |
| **CONS-MP-002** | **Séparation consommation / mise à jour stock (deux wizards, deux menus)** | **GO** |
| **CONS-MP-003** | **Cockpit limité au booléen Suivi consommation La Platine** | **GO Dev lab** |

**Tests automatisés module** : **100/100 verts** (lab, 2026-07-05).

---

## 2. Périmètre V1 livré

### 2.1 Wizards opérationnels (V1.1 — CONS-MP-002)

Menus sous **Inventaire → La Platine** :

| Menu | Modèle | Action | Traitement Odoo |
|------|--------|--------|-----------------|
| **Consommation matière première** | `laplatine.raw.material.consumption.wizard` | **Enregistrer la consommation** | `stock.move` `done`, réf. `Consommation MP La Platine`, internal → Production société |
| **Mise à jour des quantités en stock** | `laplatine.raw.material.stock.update.wizard` | **Mettre à jour le stock** (avec confirmation) | Ajustement inventaire standard, motif sur le mouvement |

> Une intention métier = un menu = un wizard. Aucun champ `mode` ni bascule entre prélèvement et correction.

### 2.2 Supervision (inchangée fonctionnellement)

Menu : **Inventaire → Configuration → Pilotage approvisionnements → Cockpit**

### 2.3 Hors périmètre V1 (non livré / explicitement exclu)

- Commande fournisseur automatique ;
- modification automatique de « Consommation non traçable » ;
- préalerte seuil à 50 % ;
- registre ou stock parallèle.

---

## 3. Campagnes QA / MOA lab

| Run | Verdict | Référence |
|-----|---------|-----------|
| `QA-CONS-MP-S12` (post-fix menu cockpit) | GO_QA_SLICE12 | [`recette_qa/QA-CONS-MP-S12-POSTFIX-20260705_185917/`](recette_qa/QA-CONS-MP-S12-POSTFIX-20260705_185917/) |
| `QA-CONS-MP-S3` | GO_QA_SLICE3_LAB | [`recette_qa/QA-CONS-MP-S3-20260705_193007/`](recette_qa/QA-CONS-MP-S3-20260705_193007/) |
| `QA-CONS-MP-S4` | GO_QA_SLICE4_LAB | [`recette_qa/QA-CONS-MP-S4-20260705_195544/`](recette_qa/QA-CONS-MP-S4-20260705_195544/) |
| `QA-CONS-MP-MOA-UI` (Slice 4) | GO_MOA_UI_SLICE4 (8/8) | [`recette_qa/QA-CONS-MP-MOA-UI-20260705_200300/`](recette_qa/QA-CONS-MP-MOA-UI-20260705_200300/) |
| `QA-CONS-MP-WIZSEP` (CONS-MP-002) | GO_QA_WIZSEP_LAB (23/23) | [`recette_qa/QA-CONS-MP-WIZSEP-20260705_203637/`](recette_qa/QA-CONS-MP-WIZSEP-20260705_203637/) |
| `QA-CONS-MP-MOA-UI-WIZSEP` | GO_MOA_UI_WIZSEP (11/11) | [`recette_qa/QA-CONS-MP-MOA-UI-WIZSEP-20260705_204100/`](recette_qa/QA-CONS-MP-MOA-UI-WIZSEP-20260705_204100/) |

Cockpit V1 (lot séparé, non régressé) : **GO** — [`recette_qa/QA-PC-V1-20260705_082258/`](recette_qa/QA-PC-V1-20260705_082258/).

---

## 4. Cas pilote fécule — historique lab

Article `[MP-FEC-MAN-001]`, emplacement `WH/Stock/Conteneur Fécule`.

| Opération | Date lab | Stock avant | Stock après | Preuve |
|-----------|----------|-------------|-------------|--------|
| Consommation 75 kg (Slice 3) | 2026-07-05 | 13 250 kg | 13 175 kg | `QA-CONS-MP-S3` — move 957 |
| Correction −25 kg (Slice 4) | 2026-07-05 | 13 175 kg | 13 150 kg | `QA-CONS-MP-S4` — move 1068 |
| Passe MOA UI (lecture seule) | 2026-07-05 | 13 150 kg | 13 150 kg | `QA-CONS-MP-MOA-UI` |
| Passe MOA UI wizards séparés (lecture seule) | 2026-07-05 | 13 000 kg | 13 000 kg | `QA-CONS-MP-MOA-UI-WIZSEP` |

Paramétrage fécule lab : min/max **5 000 / 18 250 kg**, fournisseur Kastell, délai **90 j** — non modifié par les recettes.

---

## 5. Anomalies traitées

| ID | Description | Résolution | Commit |
|----|-------------|------------|--------|
| BUG-CONS-MP-001 | Menu cockpit invisible profil Consultation | Extension groupe sur menu Configuration Stock | `5655b9c` |
| BUG-CONS-MP-003 | Emplacement auto consommation non persisté à l'enregistrement | `force_save` + `_resolve_location_id()` | `18.0.1.6.0` |
| ENV-CONS-MP-S3-001 | Runtime web non rechargé après upgrade | Procédure restart documentée | `70ea358`, `recette_qa/README.md` |

---

## 6. Groupes utilisateurs

| Groupe Odoo | Usage V1 |
|-------------|----------|
| **La Platine — Consommation matières premières** | Véréna, Ethel, Michel — wizard opérationnel |
| **Pilotage approvisionnements / Consultation** | Lecture cockpit (sans actualisation) |
| **Pilotage approvisionnements / Actualisation** | Bouton Actualiser cockpit |
| **Pilotage approvisionnements / Paramétrage** | Paramétrage cockpit |

Le groupe consommation **n'implique pas** les groupes cockpit.

---

## 7. Paramétrage société requis

| Paramètre | Obligatoire | Usage |
|-----------|-------------|-------|
| Entrepôt de pilotage approvisionnements | Oui | Emplacements sources wizard + cockpit |
| Emplacement destination consommations | Oui (`usage=production`) | Cible des prélèvements |
| Suivi consommation La Platine (article) | Oui par MP | Filtre wizards **et cockpit** |

---

## 8. Réserve environnement (transmissible production)

Après tout **upgrade module**, un **redémarrage du service Odoo** est obligatoire avant recette ou ouverture aux utilisateurs. Sans cela, l'UI peut exécuter l'ancien code neutralisé (cf. `ENV-CONS-MP-S3-001`).

Procédure détaillée : [`GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md`](GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md).

---

## 9. Dette technique connue (non bloquante V1)

- Warnings Odoo `compute_sudo` / `store` sur `laplatine.procurement.control.line` (`is_data_stale`) ;
- Paramètres société cockpit sur `res.company` (migration `res.config.settings` différée).

---

## 10. Prochaine étape

1. Décision MOA **GO déploiement production** ;
2. Exécution du guide de déploiement + recette de fumée production ;
3. Attribution des groupes aux utilisateurs métier ;
4. Formation courte opérateurs (wizard + correction + alerte seuil).

---

## 11. Signatures (à compléter)

| Rôle | Nom | Date | Décision |
|------|-----|------|----------|
| MOA | | | Clôture V1 lab : ☐ GO |
| Dev / Dorevia | | 2026-07-05 | Livrable `18.0.1.5.0` : ☑ GO |
| QA | | 2026-07-05 | Recettes S1–S4 + CONS-MP-002 : ☑ GO |
| MOA UI | | 2026-07-05 | Wizards séparés : ☑ GO |
| Production | | | Déploiement : ☐ STOP / ☐ GO |
