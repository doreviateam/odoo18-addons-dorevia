# Guide de recette manuelle QA — Consommation MP (Slices 1 & 2)

| Élément | Valeur |
|---------|--------|
| Référence | `QA-CONS-MP-S12-LAB` |
| Cadrage | [`docs/cadrage/NOTE_CADRAGE_CONSOMMATION_MP_LAPLATINE_V1.md`](../docs/cadrage/NOTE_CADRAGE_CONSOMMATION_MP_LAPLATINE_V1.md) |
| Module | `laplatine_procurement_control` |
| Version module | `18.0.1.2.0` |
| Commit Git de référence | `cfc44f3` (`origin/main`) |
| Environnement | **Lab uniquement** — `laplatine-odoo18-lab` |
| Base | `laplatine_prod` |
| URL | `http://127.0.0.1:18018` |
| Production | **STOP** — aucun déploiement |
| Périmètre recette | **Slices 1 & 2 uniquement** |
| Hors périmètre | Enregistrement consommation (Slice 3), correction stock (Slice 4), alerte seuil |

---

## 0. Demande QA

> **Objectif :** valider manuellement le socle navigation + lecture stock du wizard
> **Consommation matière première**, avant ouverture du Slice 3 Dev.
>
> **Verdict attendu :** `GO_QA_SLICE12` ou `NO_GO` avec fiches anomalies numérotées.
>
> **Tests automatisés lab (référence) :** 63/63 verts sur `laplatine_prod` au commit `cfc44f3`.

---

## 1. Préambule obligatoire

### 1.1 Relevé d'environnement

| Champ | Valeur relevée | OK |
|-------|----------------|-----|
| Date / heure début | | ☐ |
| Testeur (nom, login) | | ☐ |
| Société active | SARL La Platine | ☐ |
| Version module | `18.0.1.2.0` | ☐ |
| Commit Git local = `cfc44f3` | | ☐ |
| Entrepôt pilotage configuré | Attendu : **La Platine** | ☐ |
| Destination consommations configurée | Attendu : emplacement **Production** | ☐ |

**Chemins lab :**

| Élément | Menu |
|---------|------|
| Wizard consommation | **Inventaire → La Platine → Consommation matière première** |
| Cockpit | **Inventaire → Configuration → Pilotage approvisionnements → Cockpit** |
| Paramètres société | **Paramètres → Sociétés → … → Pilotage approvisionnements** |
| Suivi consommation article | **Article → Inventaire → LA PLATINE** |

### 1.2 Comptes à utiliser

Préparer **deux comptes** (ou basculer les groupes sur le lab) :

| Profil | Groupes Odoo requis | Usage recette |
|--------|---------------------|---------------|
| **Opérateur MP** | `La Platine — Consommation matières premières` + Utilisateur interne | Scénarios wizard |
| **Consultant cockpit** | `Pilotage approvisionnements / Consultation` + Utilisateur interne | Scénario navigation cockpit |
| **Administrator** | (référence) | Préparation données si besoin |

> L'opérateur MP **ne doit pas** avoir les groupes cockpit sauf test croisé explicite.

### 1.3 Préparation article pilote

Sur `[MP-FEC-MAN-001] FÉCULE DE MANIOC` :

| Champ | Valeur attendue |
|-------|-----------------|
| Suivi consommation La Platine | **Coché** |
| Stock `WH/Stock/Conteneur Fécule` | **13 250 kg** (ou valeur lab actuelle — noter) |
| Unité | kg |

---

## 2. Scénarios bloquants

### QA-S12-01 — Menu opérationnel (AC01)

| | |
|-|-|
| **Profil** | Opérateur MP |
| **Action** | Ouvrir **Inventaire → La Platine → Consommation matière première** |
| **Attendu** | Wizard modal « Consommation matière première », mode « Enregistrer un prélèvement » |
| **OK** | ☐ |

### QA-S12-02 — Cockpit sous Configuration (AC02)

| | |
|-|-|
| **Profil** | Consultant cockpit |
| **Action** | Naviguer vers **Inventaire → Configuration → Pilotage approvisionnements → Cockpit** |
| **Attendu** | Liste cockpit accessible ; **pas** de menu cockpit sous « La Platine » |
| **OK** | ☐ |

### QA-S12-03 — Éligibilité article (AC03)

| | |
|-|-|
| **Profil** | Opérateur MP |
| **Action** | Ouvrir le wizard → champ **Matière première** → rechercher la fécule |
| **Attendu** | Fécule visible si **Suivi consommation** coché ; articles non suivis absents du cockpit après actualisation (CONS-MP-003) |
| **Action 2** | Décocher **Suivi consommation** sur un article test → rouvrir wizard |
| **Attendu 2** | Article disparu de la liste |
| **Remise en état** | Recocher Suivi consommation sur fécule |
| **OK** | ☐ |

### QA-S12-04 — Lecture stock fécule, emplacement auto (AC04, T05)

| | |
|-|-|
| **Profil** | Opérateur MP |
| **Précondition** | Stock fécule sur **un seul** emplacement interne avec qty > 0 |
| **Action** | Sélectionner `[MP-FEC-MAN-001] FÉCULE DE MANIOC` |
| **Attendu** | **Localisation** = `Conteneur Fécule` (ou nom lab équivalent), **lecture seule** |
| **Attendu** | **Quantité disponible** = stock réel en kg (ex. **13 250,00**) |
| **OK** | ☐ |

### QA-S12-05 — Boutons neutralisés (Slice 3/4 non ouverts)

| | |
|-|-|
| **Profil** | Opérateur MP |
| **Action** | Saisir une quantité (ex. 75 kg) → **Enregistrer la consommation** |
| **Attendu** | Message explicite « disponible au Slice 3 » — **aucun mouvement créé** |
| **Action 2** | **Mettre à jour la quantité disponible** → mode correction → **Appliquer** |
| **Attendu 2** | Message « disponible au Slice 4 » — **aucun ajustement** |
| **Vérif stock** | Stock inchangé après les deux tentatives |
| **OK** | ☐ |

### QA-S12-06 — Mode correction, emplacement à stock nul

| | |
|-|-|
| **Profil** | Opérateur MP |
| **Action** | Basculer en **Correction après comptage** |
| **Attendu** | **Localisation** sélectionnable parmi emplacements internes du warehouse pilotage |
| **Attendu** | Emplacement sans stock **sélectionnable** ; quantité Odoo = **0 kg** |
| **OK** | ☐ |

### QA-S12-07 — Destination Production sur société

| | |
|-|-|
| **Profil** | Administrator |
| **Action** | **Sociétés → Pilotage approvisionnements** → champ **Emplacement destination consommations La Platine** |
| **Attendu** | Liste filtrée sur emplacements **Production** de la société ou partagés |
| **OK** | ☐ |

### QA-S12-08 — Non-régression cockpit fécule

| | |
|-|-|
| **Profil** | Administrator (Manager) |
| **Action** | Cockpit → **Actualiser** → ouvrir ligne fécule |
| **Attendu** | Min **5 000** / Max **18 250**, fournisseur **Kastell**, délai **90 j** — comportement post `7311b20` inchangé |
| **OK** | ☐ |

---

## 3. Scénarios recommandés (non bloquants)

### QA-S12-09 — Multi-emplacements (AC14, T06)

Si un second emplacement interne avec stock > 0 est disponible sur le lab :

| | |
|-|-|
| **Attendu** | **Localisation** **non** auto ; choix explicite ; qty recalculée selon emplacement |
| **OK** | ☐ / N/A |

### QA-S12-10 — Article hors catégorie Poids

| | |
|-|-|
| **Action** | Article stockable + Suivi coché + UoM **Unité** |
| **Attendu** | Absent du wizard |
| **OK** | ☐ / N/A |

---

## 4. Grille de synthèse

| ID | Intitulé | Bloquant | Résultat | Anomalie |
|----|----------|----------|----------|----------|
| QA-S12-01 | Menu opérationnel | Oui | ☐ OK ☐ KO | |
| QA-S12-02 | Cockpit Configuration | Oui | ☐ OK ☐ KO | |
| QA-S12-03 | Éligibilité article | Oui | ☐ OK ☐ KO | |
| QA-S12-04 | Stock + emplacement auto | Oui | ☐ OK ☐ KO | |
| QA-S12-05 | Boutons neutralisés | Oui | ☐ OK ☐ KO | |
| QA-S12-06 | Correction stock nul | Oui | ☐ OK ☐ KO | |
| QA-S12-07 | Destination société | Oui | ☐ OK ☐ KO | |
| QA-S12-08 | Non-régression cockpit | Oui | ☐ OK ☐ KO | |
| QA-S12-09 | Multi-emplacements | Non | ☐ OK ☐ KO ☐ N/A | |
| QA-S12-10 | Hors catégorie Poids | Non | ☐ OK ☐ KO ☐ N/A | |

**Verdict global :**

| Verdict | Cocher |
|---------|--------|
| **GO_QA_SLICE12** — ouverture Slice 3 autorisée | ☐ |
| **NO_GO** — corrections requises avant Slice 3 | ☐ |

---

## 5. Livrables QA attendus

1. Grille §4 complétée avec date et testeur.
2. Captures : menu La Platine, wizard fécule (stock lu), message Slice 3, cockpit Configuration.
3. Fiches anomalies au format : `BUG-CONS-MP-XXX` + étapes + attendu / obtenu.
4. Dossier preuves (optionnel) : `laplatine_procurement_control/recette_qa/QA-CONS-MP-S12-YYYYMMDD_HHMMSS/`

---

## 6. Rappels

- **Ne pas tester** l'enregistrement effectif de consommation ni la correction stock (Slices 3/4).
- **Ne pas déployer** en production.
- Toute anomalie cockpit préexistante hors wizard doit être signalée séparément de la recette consommation MP.
