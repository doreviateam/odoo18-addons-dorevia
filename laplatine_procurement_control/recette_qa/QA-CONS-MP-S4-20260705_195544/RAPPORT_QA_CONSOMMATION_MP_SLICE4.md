# Rapport QA — Consommation MP Slice 4

| Élément | Valeur |
|---|---|
| Référence | `QA-CONS-MP-S4-LAB` |
| Run | `QA-CONS-MP-S4-20260705_195544` |
| Date recette | 2026-07-05 |
| Testeur | Agent QA (backend wizard ORM + tests auto) |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Module | `laplatine_procurement_control` |
| Version installée | `18.0.1.4.0` |
| Référence Git locale | HEAD `70ea358`, code Slice 4 non commité |
| Tests auto relancés QA | **85/85 verts** |
| Production | **STOP — aucun déploiement production** |

## Verdict

**GO_QA_SLICE4_LAB**

La correction pilote sur `[MP-FEC-MAN-001] FECULE DE MANIOC` est validée, ainsi que les contrôles bloquants et la non-régression Slice 3.

| Contrôle | Résultat |
|---|---|
| Procédure lab (upgrade + restart) | OK |
| Stock initial pilote | OK — `13 175 kg` sur `WH/Stock/Conteneur Fécule` |
| Correction comptée | OK — `13 150 kg`, motif « Ancienne consommation non enregistrée » |
| Écart | OK — `-25 kg` |
| Stock final fécule | OK — `13 150 kg` |
| Mouvement inventaire Odoo | OK — `stock.move(1068)` en `done`, `is_inventory=True` |
| Motif sur mouvement | OK — `name` et `reference` = motif saisi |
| Origine | OK — `Correction MP La Platine` |
| Utilisateur | OK — `QA CONS MP S4 Opérateur` |
| Motif obligatoire | OK — refus si vide |
| Quantité négative | OK — refus |
| Confirmation UI | OK — attribut `confirm` sur le bouton |
| Seuil min post-correction | OK — alerte `warning` sur article QA jetable |
| Non-régression consommation | OK — prélèvement 10 kg après correction |

## Procédure lab exécutée

Conformément à `recette_qa/README.md` :

1. Upgrade module `laplatine_procurement_control` → `18.0.1.4.0`
2. `docker compose restart odoo`
3. Contrôle version installée via shell
4. Campagne QA fonctionnelle (script `scripts/qa_consumption_mp_slice4_run.py`)
5. Suite tests auto `/laplatine_procurement_control` : **85/85**

## Grille QA

| ID | Intitulé | Bloquant | Résultat | Preuve |
|---|---|---|---|---|
| S4-01 | Correction pilote fécule −25 kg | Oui | OK | `pilot_adjustment_evidence.json` |
| S4-02 | Motif obligatoire | Oui | OK | `final_evidence.json` |
| S4-03 | Refus qty négative | Oui | OK | `final_evidence.json` |
| S4-04 | Confirmation explicite UI | Oui | OK | `final_evidence.json` |
| S4-05 | Non-régression consommation Slice 3 | Oui | OK | `final_evidence.json` |
| S4-06 | Alerte seuil min après correction | Oui | OK | `final_evidence.json` |

## Méthode QA

- **Wizard ORM** sous profil opérateur (`qa_cons_mp_s4_operator_20260705_195544`) : même code métier que les boutons UI **Appliquer la correction** / **Enregistrer la consommation**.
- **Pas de capture navigateur** dans ce run — validation fonctionnelle backend + tests auto. Une passe UI manuelle MOA reste recommandée avant production pour confirmer dialogs et notifications visuelles.

## Observations

- Le stock fécule lab est passé de `13 175 kg` à `13 150 kg` (correction pilote). Un prélèvement de non-régression `10 kg` a été annulé net (stock préparé à `13 160 kg` puis consommé).
- L'alerte seuil S4-06 utilise un article QA jetable (`QA S4 Threshold Product`) pour ne pas impacter le paramétrage fécule (min `5 000 kg` non atteint à `13 150 kg`).
- Warnings Odoo connus `compute_sudo/store` sur le cockpit : non bloquants.

## Compte QA créé

| Login | Mot de passe | Groupes |
|---|---|---|
| `qa_cons_mp_s4_operator_20260705_195544` | `S4Qa!2026` | Utilisateur interne + Consommation MP |

## Conclusion

Slice 4 validée sur le lab. Le commit/push du code `18.0.1.4.0` peut être autorisé côté QA. Production maintenue en **STOP** jusqu'à recette finale S1–S4 complète et GO MOA production explicite.
