# Note de clôture V1 — Consommation matières premières La Platine

| Élément | Valeur |
|---------|--------|
| **Référence lot** | `LAPLATINE-CONS-MP-001` |
| **Module** | `laplatine_procurement_control` |
| **Version livrable** | `18.0.1.4.0` |
| **Commit de référence** | `09d801e` (`origin/main`) |
| **Date clôture lab** | 2026-07-05 |
| **Production** | **STOP** — en attente de décision de déploiement explicite |

---

## 1. Verdict consolidé

> **Slices 1 à 4 : GO Dev / GO QA / GO MOA UI sur le lab.**
>
> **V1 Consommation matières premières : fonctionnellement complète.**
>
> **Production : STOP jusqu'à GO MOA déploiement.**

| Slice | Contenu | Verdict |
|-------|---------|---------|
| 1 | Socle, booléen article, config société, groupes, menus, wizard squelette | GO |
| 2 | Lecture emplacement / stock, auto-sélection | GO |
| 3 | Enregistrement consommation (mouvement standard → Production) | GO |
| 4 | Correction inventaire, motif traçable, seuil min post-opération | GO |

**Tests automatisés module** : **85/85 verts** (lab, 2026-07-05).

---

## 2. Périmètre V1 livré

### 2.1 Wizard opérationnel

Menu : **Inventaire → La Platine → Consommation matière première**

| Mode | Action | Traitement Odoo |
|------|--------|-----------------|
| Prélèvement | **Enregistrer la consommation** | `stock.move` `done`, réf. `Consommation MP La Platine`, internal → Production société |
| Correction | **Appliquer la correction** (avec confirmation) | Ajustement inventaire standard, motif sur le mouvement |

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
| `QA-CONS-MP-MOA-UI` | GO_MOA_UI_SLICE4 (8/8) | [`recette_qa/QA-CONS-MP-MOA-UI-20260705_200300/`](recette_qa/QA-CONS-MP-MOA-UI-20260705_200300/) |

Cockpit V1 (lot séparé, non régressé) : **GO** — [`recette_qa/QA-PC-V1-20260705_082258/`](recette_qa/QA-PC-V1-20260705_082258/).

---

## 4. Cas pilote fécule — historique lab

Article `[MP-FEC-MAN-001]`, emplacement `WH/Stock/Conteneur Fécule`.

| Opération | Date lab | Stock avant | Stock après | Preuve |
|-----------|----------|-------------|-------------|--------|
| Consommation 75 kg (Slice 3) | 2026-07-05 | 13 250 kg | 13 175 kg | `QA-CONS-MP-S3` — move 957 |
| Correction −25 kg (Slice 4) | 2026-07-05 | 13 175 kg | 13 150 kg | `QA-CONS-MP-S4` — move 1068 |
| Passe MOA UI (lecture seule) | 2026-07-05 | 13 150 kg | 13 150 kg | `QA-CONS-MP-MOA-UI` |

Paramétrage fécule lab : min/max **5 000 / 18 250 kg**, fournisseur Kastell, délai **90 j** — non modifié par les recettes.

---

## 5. Anomalies traitées

| ID | Description | Résolution | Commit |
|----|-------------|------------|--------|
| BUG-CONS-MP-001 | Menu cockpit invisible profil Consultation | Extension groupe sur menu Configuration Stock | `5655b9c` |
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
| Suivi consommation La Platine (article) | Oui par MP | Filtre wizard |

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
| Dev / Dorevia | | 2026-07-05 | Livrable `18.0.1.4.0` : ☑ GO |
| QA | | 2026-07-05 | Recettes S1–S4 + MOA UI : ☑ GO |
| Production | | | Déploiement : ☐ STOP / ☐ GO |
