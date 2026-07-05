# Rapport QA post-fix - Consommation MP Slices 1 & 2

| Élément | Valeur |
|---|---|
| Référence | `QA-CONS-MP-S12-LAB` |
| Run initial | `QA-CONS-MP-S12-20260705_183101` |
| Run post-fix | `QA-CONS-MP-S12-POSTFIX-20260705_185917` |
| Date recette | 2026-07-05 |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Module | `laplatine_procurement_control` |
| Version installée | `18.0.1.2.1` |
| Tests auto de référence | 63/63 verts communiqués par Dev, non relancés dans ce run QA |
| Production | **STOP - aucun déploiement production** |

## Verdict

**GO_QA_SLICE12 post-fix**

Le correctif `BUG-CONS-MP-001` est validé sur le lab : le profil `Pilotage approvisionnements / Consultation` voit désormais le chemin attendu sous **Inventaire -> Configuration -> Pilotage approvisionnements -> Cockpit** et ouvre le cockpit depuis la navigation UI.

La recette bloquante S12 passe donc de **NO_GO** à **GO_QA_SLICE12**, sous réserve de validation MOA pour l'ouverture du Slice 3. La production reste en STOP.

| Total bloquants | OK | KO |
|---:|---:|---:|
| 8 | 8 | 0 |

## Reprise BUG-CONS-MP-001

| Champ | Résultat post-fix |
|---|---|
| Classification | Anomalie logicielle droits-menu |
| Statut | **Corrigée / clôturable QA** |
| Profil testé | Utilisateur interne + `Pilotage approvisionnements / Consultation` uniquement |
| Chemin UI | OK - `Inventory -> Configuration -> Pilotage approvisionnements -> Cockpit` |
| Cockpit direct | OK - la liste `Pilotage approvisionnements` s'ouvre depuis le menu |
| Parcours La Platine | OK - absent pour le consultant |
| Effet de bord attendu | OK - `Products` / unités visibles sous Configuration; pas d'entrée admin observée |

## Grille bloquants

| ID | Intitulé | Résultat initial | Résultat post-fix | Anomalie |
|---|---|---|---|---|
| QA-S12-01 | Menu opérationnel | OK | OK | |
| QA-S12-02 | Cockpit Configuration | KO | **OK** | `BUG-CONS-MP-001` corrigé |
| QA-S12-03 | Éligibilité article | OK | OK | |
| QA-S12-04 | Stock + emplacement auto | OK | OK | |
| QA-S12-05 | Boutons neutralisés | OK | OK | |
| QA-S12-06 | Correction stock nul | OK | OK | |
| QA-S12-07 | Destination société | OK | OK | |
| QA-S12-08 | Non-régression cockpit | OK | OK | |

## Contrôles post-fix

- Menu consultant : `Configuration`, `Pilotage approvisionnements` et `Cockpit` visibles.
- Menu consultant : parcours `La Platine` absent.
- Menu opérateur MP : parcours `La Platine -> Consommation matière première` toujours visible; cockpit absent.
- Fécule : `Suivi consommation La Platine` coché, article éligible, unité `kg`.
- Stock fécule : `13 250 kg` sur `WH/Stock/Conteneur Fécule`; emplacements internes à stock nul toujours disponibles en correction.
- Actions Slice 3/4 : messages de neutralisation attendus, aucun mouvement ni stock modifié.
- Destination société : `Virtual Locations/Production`, usage `production`.
- Cockpit fécule : min `5 000`, max `18 250`, fournisseur `KASTELL NEGOCE SAS`, délai `90 j`, période conso `90 j`.

## Preuves

| Preuve | Fichier |
|---|---|
| Relevé serveur post-fix | `postfix_evidence.json` |
| Relevé UI post-fix | `postfix_ui_evidence.json` |
| Inventaire consultant avec Configuration | `screenshots/01_consultant_inventory_configuration_visible.png` |
| Configuration avec Pilotage approvisionnements / Cockpit | `screenshots/02_consultant_configuration_dropdown.png` |
| Cockpit ouvert depuis le menu | `screenshots/03_consultant_cockpit_opened_from_menu.png` |
| Preuves initiales S12 complètes | `../QA-CONS-MP-S12-20260705_183101/` |

## Réserves et limites

- Aucun commit, push ou déploiement production effectué par le QA.
- Les valeurs min/max fécule n'ont pas été inventées ni modifiées par le QA.
- Le refresh cockpit du run post-fix a actualisé le snapshot de lignes de pilotage, sans impact stock.
- Warnings Odoo déjà observés : incohérence `compute_sudo/store` sur `is_data_stale` / `stale_warning_message`; non bloquant pour S12.
