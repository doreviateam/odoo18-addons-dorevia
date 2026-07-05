# Rapport MOA UI — Séparation wizards consommation / mise à jour stock

| Élément | Valeur |
|---|---|
| Référence | `LAPLATINE-CONS-MP-002` |
| Run | `QA-CONS-MP-MOA-UI-WIZSEP-20260705_204100` |
| Date | 2026-07-05 |
| Profil | Opérateur MP (`qa_wizsep_operator_20260705`) |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Module | `laplatine_procurement_control` `18.0.1.5.0` |
| Production | **STOP** |

## Verdict

**GO_MOA_UI_WIZSEP**

Les deux parcours sont distincts, lisibles et immédiatement compréhensibles pour un opérateur terrain. Aucune modification du stock fécule.

## Critère MOA principal

| Intention opérateur | Menu | Validé |
|---|---|---|
| « J'ai prélevé de la matière » | Consommation matière première | OK |
| « J'ai compté le stock physique » | Mise à jour des quantités en stock | OK |

Aucune connaissance des mouvements, ajustements ou emplacements techniques n'est requise pour choisir le bon parcours.

## Parcours 1 — Consommation matière première

| Contrôle | Résultat | Observation |
|---|---|---|
| Menu accessible | OK | `Inventaire → La Platine → Consommation matière première` |
| Fécule sélectionnée | OK | `[MP-FEC-MAN-001] FECULE DE MANIOC` |
| Localisation | OK | `WH/Stock/Conteneur Fécule` |
| Quantité disponible | OK | `13 000,00 kg` |
| Quantité prélevée | OK | Champ éditable présent |
| Bouton principal | OK | **Enregistrer la consommation** |
| Absence bascule correction | OK | Aucun mode, aucun bouton mise à jour |
| Validation | — | **Annulé** (lecture seule) |

Capture : `screenshots/04_consumption_wizard_fecule_selected.png`

## Parcours 2 — Mise à jour des quantités en stock

| Contrôle | Résultat | Observation |
|---|---|---|
| Menu accessible | OK | `Inventaire → La Platine → Mise à jour des quantités en stock` |
| Fécule sélectionnée | OK | `[MP-FEC-MAN-001] FECULE DE MANIOC` |
| Localisation | OK | `WH/Stock/Conteneur Fécule` |
| Quantité Odoo | OK | `13 000,00 kg` |
| Quantité comptée | OK | Champ présent |
| Écart calculé | OK | `0,00 kg` (comptée = Odoo) |
| Motif | OK | Saisi puis non appliqué |
| Absence prélèvement | OK | Pas de « Quantité prélevée » |
| Confirmation | OK | « Confirmez-vous la mise à jour du stock selon la quantité comptée ? » |
| Validation | — | **Annulé** via Cancel sur la confirmation |

Captures :
- `screenshots/06_stock_update_wizard_fecule_filled.png`
- `screenshots/07_stock_update_confirm_dialog.png`

## Menus La Platine

Capture : `screenshots/02_la_platine_submenu.png`

Deux entrées visibles :
1. Consommation matière première
2. Mise à jour des quantités en stock

## Stock fécule

| Mesure | Valeur |
|---|---|
| Stock avant passe | 13 000 kg |
| Stock après passe | **13 000 kg** |
| Impact | **Aucun** |

## Grille MOA UI (11/11)

| ID | Intitulé | Résultat |
|---|---|---|
| MOA-UI-01 | Deux menus sous La Platine | OK |
| MOA-UI-02 | Consommation : Conteneur Fécule | OK |
| MOA-UI-03 | Consommation : 13 000 kg | OK |
| MOA-UI-04 | Consommation : champs prélèvement uniquement | OK |
| MOA-UI-05 | Consommation : pas de bascule correction | OK |
| MOA-UI-06 | Mise à jour : quantité Odoo 13 000 kg | OK |
| MOA-UI-07 | Mise à jour : comptée, écart, motif | OK |
| MOA-UI-08 | Mise à jour : pas de prélèvement | OK |
| MOA-UI-09 | Dialogue confirmation puis annulation | OK |
| MOA-UI-10 | Parcours distincts prélèvement / comptage | OK |
| MOA-UI-11 | Fécule inchangée 13 000 kg | OK |

## Preuves

| Fichier | Description |
|---|---|
| `moa_ui_wizsep_evidence.json` | Synthèse automatisée |
| `screenshots/02_la_platine_submenu.png` | Menus La Platine |
| `screenshots/04_consumption_wizard_fecule_selected.png` | Wizard consommation |
| `screenshots/06_stock_update_wizard_fecule_filled.png` | Wizard mise à jour |
| `screenshots/07_stock_update_confirm_dialog.png` | Dialogue confirmation |

## Conclusion

Passe MOA UI **GO** sur le lab. L'évolution CONS-MP-002 est ergonomiquement validée pour Véréna, Ethel et Michel.

Production : **STOP** — commit et déploiement production restent soumis à GO MOA déploiement explicite.
