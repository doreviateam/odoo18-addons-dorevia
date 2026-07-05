# Rapport QA manuelle - Consommation MP Slices 1 & 2

| Élément | Valeur |
|---|---|
| Référence | `QA-CONS-MP-S12-LAB` |
| Run | `QA-CONS-MP-S12-20260705_183101` |
| Date recette | 2026-07-05 |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Module | `laplatine_procurement_control` |
| Version installée | `18.0.1.2.0` |
| Commit code attendu | `cfc44f3` |
| Commit guide attendu | `533caa8` |
| Production | **STOP - aucun déploiement production** |

## Verdict

**NO_GO**

Un scénario bloquant est KO : le profil `Pilotage approvisionnements / Consultation` accède au cockpit par action directe, mais le menu attendu sous **Inventaire → Configuration → Pilotage approvisionnements → Cockpit** n'est pas visible dans la navigation UI avec les seuls groupes documentés.

| Total bloquants | OK | KO |
|---:|---:|---:|
| 8 | 7 | 1 |

## Préambule

| Contrôle | Résultat |
|---|---|
| Société active | OK - SARL La Platine |
| Entrepôt pilotage | OK - La Platine |
| Destination consommations | OK - `Virtual Locations/Production`, usage `production` |
| Fécule stock | OK - `13 250 kg` sur `WH/Stock/Conteneur Fécule` |
| Fécule unité | OK - kg |
| Fécule min/max | OK - `5 000 / 18 250`, non modifiés par le QA |
| Fécule fournisseur/délai | OK - `KASTELL NEGOCE SAS`, `90 j` |
| Suivi consommation fécule | Pré-requis initialement décoché, coché par QA conformément au guide. Preuve : `prereq_adjustment_evidence.json` |

## Grille §4

| ID | Intitulé | Bloquant | Résultat | Anomalie |
|---|---|---|---|---|
| QA-S12-01 | Menu opérationnel | Oui | OK | |
| QA-S12-02 | Cockpit Configuration | Oui | KO | `BUG-CONS-MP-001` |
| QA-S12-03 | Éligibilité article | Oui | OK | |
| QA-S12-04 | Stock + emplacement auto | Oui | OK | |
| QA-S12-05 | Boutons neutralisés | Oui | OK | |
| QA-S12-06 | Correction stock nul | Oui | OK | |
| QA-S12-07 | Destination société | Oui | OK | |
| QA-S12-08 | Non-régression cockpit | Oui | OK | |
| QA-S12-09 | Multi-emplacements | Non | N/A | Cas pilote fécule avec un seul emplacement positif |
| QA-S12-10 | Hors catégorie Poids | Non | OK | Article unité QA absent du wizard |

## Anomalies

### BUG-CONS-MP-001 - Menu cockpit absent pour le consultant

| Champ | Valeur |
|---|---|
| Sévérité | Bloquante |
| Classification | Anomalie logicielle / droits-menu |
| Profil | Utilisateur interne + `Pilotage approvisionnements / Consultation` |
| Étapes | Se connecter avec `qa_cons_mp_s12_consult_20260705_183101`, ouvrir Inventory |
| Attendu | Menu **Configuration → Pilotage approvisionnements → Cockpit** visible et utilisable |
| Obtenu | Top menu Inventory visible avec Overview / Operations / Products, sans Configuration, Pilotage approvisionnements ni Cockpit |
| Preuve | `screenshots/12_consultant_inventory_menu.png` |
| Contrôle croisé | Accès direct `/odoo/action-658` ouvre bien le cockpit en lecture |
| Preuve croisée | `screenshots/13_consultant_cockpit_direct_access.png` |
| Hypothèse | Le menu enfant est autorisé, mais le parent `Inventaire/Configuration` reste inaccessible au profil consultation seul |

## Contrôles OK

- QA-S12-01 : l'opérateur MP voit le menu **La Platine** et l'entrée **Consommation matière première**, sans cockpit dans ce parcours.
- QA-S12-03 : fécule visible après prérequis `Suivi consommation La Platine`; article test kg visible quand coché et absent quand décoché; article unité absent.
- QA-S12-04 : sélection fécule avec emplacement auto `WH/Stock/Conteneur Fécule`, stock `13 250,00 kg`.
- QA-S12-05 : clic **Enregistrer la consommation** affiche le message Slice 3; clic **Appliquer la correction** affiche le message Slice 4; stock et nombre de mouvements inchangés.
- QA-S12-06 : en correction, l'emplacement interne `WH/Stock` à stock nul est sélectionnable et affiche `0,00 kg`.
- QA-S12-07 : destination société configurée sur un emplacement `production`; domaine du champ limité aux emplacements `production` de la société ou partagés.
- QA-S12-08 : cockpit rafraîchi par le profil admin QA; ligne fécule à `min=5000`, `max=18250`, fournisseur `KASTELL NEGOCE SAS`, délai `90`, période `90`.

## Preuves

| Preuve | Fichier |
|---|---|
| Relevé initial prérequis | `prepare_evidence_initial_precondition.json` |
| Ajustement prérequis fécule | `prereq_adjustment_evidence.json` |
| Relevé principal | `prepare_evidence.json` |
| Contrôle final stock/cockpit | `final_evidence.json` |
| Nettoyage articles QA | `cleanup_evidence.json` |
| Menu La Platine opérateur | `screenshots/04_menu_laplatine_dropdown_operator.png` |
| Wizard fécule stock | `screenshots/06_wizard_fecule_stock_operator.png` |
| Message Slice 3 | `screenshots/07_message_slice3_consumption_neutralized.png` |
| Correction stock nul | `screenshots/09_adjustment_zero_location_operator.png` |
| Message Slice 4 | `screenshots/10_message_slice4_adjustment_neutralized.png` |
| Consultant sans Configuration | `screenshots/12_consultant_inventory_menu.png` |
| Cockpit direct consultant | `screenshots/13_consultant_cockpit_direct_access.png` |

## Nettoyage

- Articles de test `QA-CONS-MP-S12-20260705_183101-*` archivés après recette.
- Comptes QA conservés pour reproduction : opérateur, consultant cockpit, administrateur.
- Fécule : suivi consommation laissé coché car attendu par le guide.
- Aucun stock, mouvement, ajustement, min/max, fournisseur ou délai fécule modifié par le QA.

## Réserves techniques

- Warnings Odoo déjà observés au chargement : incohérence `compute_sudo/store` sur `is_data_stale` / `stale_warning_message`.
- Le login admin UI a été instable dans le navigateur intégré; les contrôles admin R07/R08 ont donc été finalisés par shell Odoo avec preuves JSON. Le KO bloquant retenu ne dépend pas de ce point.
