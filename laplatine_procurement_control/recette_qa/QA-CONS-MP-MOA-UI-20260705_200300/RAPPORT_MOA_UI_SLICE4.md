# Rapport MOA — Passe UI Slice 4 (lecture seule fécule)

| Élément | Valeur |
|---|---|
| Référence | `QA-CONS-MP-MOA-UI-LAB` |
| Run | `QA-CONS-MP-MOA-UI-20260705_200300` |
| Date | 2026-07-05 |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Git HEAD | `69f8bad` |
| Module | `18.0.1.4.0` |
| Opérateur | `qa_cons_mp_s4_operator_20260705_195544` |
| Production | **STOP** |

## Verdict

**GO_MOA_UI_SLICE4**

Passe MOA UI réalisée sans modification de la fécule pilote (`13 150 kg` conservés).

## Contrôles MOA

| ID | Contrôle | Résultat |
|---|---|---|
| MOA-UI-01 | Menu **Inventaire → La Platine → Consommation matière première** visible opérateur | OK |
| MOA-UI-02 | Wizard consommation ouvrable | OK |
| MOA-UI-03 | Passage mode correction via **Mettre à jour la quantité disponible** | OK |
| MOA-UI-04 | Lisibilité qty Odoo (`13 150 kg`), qty comptée, emplacement, motif | OK |
| MOA-UI-05 | Confirmation explicite (`confirm` sur **Appliquer la correction**) + libellés champs | OK |
| MOA-UI-06 | Notification succès correction (article jetable) | OK |
| MOA-UI-07 | Notification seuil min en `warning` (article jetable QA S4) | OK |
| MOA-UI-08 | Fécule **non modifiée** durant la passe | OK |

## Détail fécule (lecture seule)

| Champ | Valeur observée |
|---|---|
| Article | `[MP-FEC-MAN-001] FECULE DE MANIOC` |
| Emplacement | `WH/Stock/Conteneur Fécule` |
| Quantité Odoo affichée | `13 150 kg` |
| Correction appliquée | **Non** — motif saisi en lecture seule uniquement |

## Notifications observées (articles jetables)

**Succès :**
```
Correction appliquée
Stock avant : … kg
Stock compté : … kg
Écart : … kg
Stock après : … kg
```

**Seuil min :**
```
… (idem) …

Seuil de réapprovisionnement atteint
Stock restant : 4 940 kg
Seuil minimum : 5 000 kg
```

## Procédure lab exécutée

1. Upgrade `laplatine_procurement_control` → `18.0.1.4.0`
2. `docker compose restart odoo`
3. Script `scripts/moa_ui_pass_slice4_readonly.py`

## Point d'attention MOA humain

Cette passe valide le **comportement fonctionnel et les libellés** via wizard ORM sous profil opérateur. Une **validation visuelle navigateur** par le MOA (dialog natif Odoo, rendu des toasts) reste recommandée avant GO production, sans obligation de re-corriger la fécule.

## Conclusion

Le parcours opérateur S1–S4 est **prêt pour clôture V1 lab**. Décision production : **STOP** jusqu'à GO MOA production explicite.

Preuve : `moa_ui_pass_evidence.json`
