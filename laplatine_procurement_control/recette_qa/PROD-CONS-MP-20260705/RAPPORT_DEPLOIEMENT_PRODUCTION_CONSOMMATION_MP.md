# Rapport de déploiement production — Consommation MP V1

| Élément | Valeur |
|---------|--------|
| **Run** | `PROD-CONS-MP-20260705` |
| **Module** | `laplatine_procurement_control` |
| **Version** | `18.0.1.6.0` (V1.2) |
| **Commit déployé** | `2af0fc1b14d7b9ff1552eb61d72c62613babff43` |
| **Date intervention** | 2026-07-05 |
| **Environnement** | `/opt/laplatine` — `https://prod.sarl-la-platine.fr` |
| **Base** | `laplatine_prod` |

---

## Verdict

> **Déploiement production : GO**
>
> **Recette de fumée : GO**
>
> **Exploitation : GO depuis le 05/07/2026**

---

## 1. Séquence exécutée

| # | Étape | Résultat |
|---|-------|----------|
| 1 | Sauvegarde base + filestore (Odoo arrêté) | OK |
| 2 | Fermeture accès utilisateurs (`docker compose stop odoo_prod`) | OK |
| 3 | Checkout détaché `2af0fc1b14d7b9ff1552eb61d72c62613babff43` | OK |
| 4 | Installation `laplatine_procurement_control` (`-i`, première mise en prod) | OK |
| 5 | Redémarrage Odoo | OK |
| 6 | Contrôle version `18.0.1.6.0` / `installed` | OK |
| 7 | Paramétrage société + groupes utilisateurs | OK |
| 8 | Recette FUM-01 à FUM-05 | GO |
| 9 | Réouverture exploitation | GO |

> **Note** : le module n'existait pas encore en production — intervention en **installation** (`-i`), non upgrade.

---

## 2. Sauvegardes

| Artefact | Chemin |
|----------|--------|
| Base PostgreSQL | `backups/20260705_202118_pre_laplatine_procurement_control/laplatine_prod.dump` (9,0 Mo — `pg_restore --list` OK, 13 042 entrées TOC) |
| Filestore | `backups/20260705_202118_pre_laplatine_procurement_control/filestore_laplatine_prod.tar.gz` (15 Mo) |

---

## 3. Paramétrage post-installation

| Paramètre | Valeur appliquée |
|-----------|------------------|
| Entrepôt de pilotage approvisionnements | La Platine |
| Emplacement destination consommations | Virtual Locations/Production |
| Suivi consommation La Platine | Activé sur les 10 MPs en stock (fécule, cannelle, farine, sucre, etc.) |

### Groupes utilisateurs

| Utilisateur | Groupes attribués |
|-------------|-------------------|
| Michel | La Platine — Consommation matières premières |
| Véréna | La Platine — Consommation matières premières |
| Ethel | La Platine — Consommation matières premières |
| David | Pilotage approvisionnements / Consultation + Actualisation |

---

## 4. Recette de fumée production

| Test | Verdict | Détail |
|------|---------|--------|
| FUM-01 | GO | Opérateur (Ethel) : menus Consommation + Mise à jour stock visibles ; cockpit non visible. David : cockpit accessible. |
| FUM-02 | GO | Consommation 0,5 kg Cannelle moulue — move #537, dest. Production, stock 19,96 → 19,46 kg |
| FUM-03 | GO | Correction +0,25 kg Cannelle — comptée 19,71 kg, motif « FUM-03 recette production » |
| FUM-04 | GO | Qty négative, motif vide et qty > stock refusées |
| FUM-05 | GO | David actualise le cockpit ; fécule visible ; article non suivi (Cookies vrac) absent ; opérateur bloqué sur `action_refresh` |

### Impact fumée sur stock

| Article | Opération | Solde net |
|---------|-----------|-----------|
| Cannelle moulue | FUM-02 (−0,5 kg) + FUM-03 (+0,25 kg) | **−0,25 kg** |

---

## 5. État production constaté

| Indicateur | Valeur |
|------------|--------|
| Version module | `18.0.1.6.0` — `installed` |
| HTTP production | `200` (`/web/login`) |
| Stock fécule | **929,23 kg** (entrepôt La Platine) |
| État dépôt Git | Checkout détaché sur `2af0fc1` |

> **Écart lab / prod connu** : stock fécule lab ~13 500 kg vs prod 929,23 kg — non bloquant pour la fumée.

---

## 6. Actions post-ouverture

1. **David** : lancer l'**actualisation cockpit** depuis l'interface et vérifier la ligne fécule.
2. Confirmer le **seuil minimum** réellement configuré en production et l'état d'alerte affiché (stock 929,23 kg).
3. **Ethel / Véréna / Michel** : valider la visibilité des deux wizards à la première connexion.
4. Formation courte opérateurs (wizard + correction + alerte seuil).

---

## 7. Références

| Document | Lien |
|----------|------|
| Guide déploiement | [`../GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md`](../../GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md) |
| Note de clôture V1 | [`../NOTE_CLOTURE_V1_CONSOMMATION_MP.md`](../../NOTE_CLOTURE_V1_CONSOMMATION_MP.md) |
| Journal §9 | Guide déploiement §9 |
