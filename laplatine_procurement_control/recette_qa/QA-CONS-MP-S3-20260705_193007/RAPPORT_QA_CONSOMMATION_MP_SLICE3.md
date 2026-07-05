# Rapport QA - Consommation MP Slice 3

| Élément | Valeur |
|---|---|
| Référence | `QA-CONS-MP-S3-LAB` |
| Run | `QA-CONS-MP-S3-20260705_193007` |
| Date recette | 2026-07-05 |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Module | `laplatine_procurement_control` |
| Version installée | `18.0.1.3.0` |
| Référence Git locale | HEAD `5655b9c`, code Slice 3 non commité |
| Tests auto de référence | 75/75 verts communiqués par Dev, non relancés par QA |
| Production | **STOP - aucun déploiement production** |

## Verdict

**GO_QA_SLICE3_LAB avec réserve environnement**

Le prélèvement pilote de `75 kg` sur `[MP-FEC-MAN-001] FECULE DE MANIOC` est validé après redémarrage du service Odoo du lab.

| Contrôle | Résultat |
|---|---|
| Stock initial | OK - `13 250 kg` sur `WH/Stock/Conteneur Fécule` |
| Prélèvement UI | OK - `75 kg` via le wizard opérateur |
| Notification | OK - succès observé, wizard fermé |
| Stock final | OK - `13 175 kg` |
| Mouvement Odoo | OK - `stock.move(957)` en `done` |
| Source | OK - `WH/Stock/Conteneur Fécule` |
| Destination | OK - `Virtual Locations/Production` |
| Référence | OK - `Consommation MP La Platine` |
| Utilisateur | OK - `QA CONS MP S3 Opérateur` |
| Slice 4 | OK - correction toujours neutralisée, aucun impact stock additionnel |

## Réserve Environnement

### ENV-CONS-MP-S3-001 - Runtime web non rechargé avant recette

| Champ | Valeur |
|---|---|
| Classification | Défaut de préparation lab / runtime Odoo |
| Sévérité | Non bloquante après correction lab |
| Constat initial | Malgré le module installé en `18.0.1.3.0`, le premier clic UI affichait encore `L'enregistrement des consommations sera disponible au Slice 3.` |
| Impact métier | Aucun - stock resté à `13 250 kg`, zéro mouvement créé |
| Action QA | Redémarrage du service Odoo lab : `docker compose restart odoo` |
| Retest | OK - comportement Slice 3 chargé et validé |
| Point d'attention | Prévoir redémarrage/reload Odoo dans toute procédure de livraison lab/prod avant recette |

## Grille QA

| ID | Intitulé | Résultat | Preuve |
|---|---|---|---|
| S3-01 | Version et prérequis fécule | OK | `preflight_evidence.json` |
| S3-02 | Navigation opérateur vers wizard | OK | `screenshots/01_operator_inventory_laplatine_menu_available.png`, `screenshots/02_operator_laplatine_dropdown.png` |
| S3-03 | Stock fécule auto avant prélèvement | OK | `screenshots/07_after_restart_wizard_fecule_13250_qty75_before_validation.png` |
| S3-04 | Enregistrement consommation 75 kg | OK après restart | `ui_evidence.json` |
| S3-05 | Stock final 13 175 kg | OK | `after_success_evidence.json`, `final_evidence.json` |
| S3-06 | Mouvement done en historique Odoo | OK | `screenshots/09_stock_move_history_form_957.png`, `after_success_evidence.json` |
| S3-07 | Correction Slice 4 toujours neutralisée | OK | `screenshots/11_slice4_still_neutralized_after_slice3.png`, `final_evidence.json` |

## Observations

- Le message de succès utilise le `display_name` Odoo de l'article : `[MP-FEC-MAN-001] FECULE DE MANIOC`. Fonctionnellement OK; à arbitrer seulement si la MOA veut un libellé plus lisible sans code article.
- Les valeurs min/max fécule n'ont pas été modifiées par le QA.
- Le prélèvement pilote a volontairement modifié le stock du lab de `13 250 kg` à `13 175 kg`.
- Les warnings Odoo déjà connus `compute_sudo/store` sur `is_data_stale` / `stale_warning_message` restent présents et non bloquants pour Slice 3.

## Preuves

| Preuve | Fichier |
|---|---|
| Pré-contrôle version/stock/utilisateur | `preflight_evidence.json` |
| Premier essai UI non chargé Slice 3 | `screenshots/05_initial_stale_runtime_slice3_neutralized.png` |
| État après premier essai | `after_initial_ui_evidence.json` |
| Preuve UI consolidée | `ui_evidence.json` |
| État après succès | `after_success_evidence.json` |
| État final après non-régression Slice 4 | `final_evidence.json` |
| Wizard rempli avant validation | `screenshots/07_after_restart_wizard_fecule_13250_qty75_before_validation.png` |
| Historique mouvement Odoo | `screenshots/09_stock_move_history_form_957.png` |
| Correction Slice 4 neutralisée | `screenshots/11_slice4_still_neutralized_after_slice3.png` |

## Conclusion

La Slice 3 est validée sur le lab après rechargement du serveur Odoo. Le commit/push du code peut être autorisé côté QA, avec mention explicite de la réserve environnement `ENV-CONS-MP-S3-001` et maintien de la production en STOP jusqu'à validation MOA.
