# Rapport QA — Recentrage cockpit CONS-MP-003

| Élément | Valeur |
|---|---|
| Référence cadrage | `LAPLATINE-CONS-MP-003` |
| Run | `QA-CONS-MP-003-20260705_220000` |
| Date recette | 2026-07-05 |
| Testeur | Agent QA (shell Odoo + tests auto) |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Module | `laplatine_procurement_control` |
| Version installée | `18.0.1.6.0` |
| Commit de référence | `6046175` |
| Tests auto | **113/113 verts** |
| Production | **STOP — aucun déploiement production** |

## Verdict

**GO_QA_CONS_MP_003_LAB**

Le cockpit ne présente plus que les articles marqués **Suivi consommation La Platine**. Les critères d'acceptation MOA AC01–AC12 sont validés sur le lab, avec non-régression wizards et correctif BUG-CONS-MP-003.

| Contrôle | Résultat |
|---|---|
| Procédure lab (upgrade + restart) | OK — version `18.0.1.6.0` |
| Article A suivi + paramétré → visible | OK |
| Article B non suivi + paramétré → absent | OK |
| Orderpoint/fournisseur seuls → insuffisants | OK |
| Article C suivi incomplet → visible + alertes | OK |
| Cycle décochage / recochage | OK |
| Ligne obsolète supprimée | OK |
| Périmètre commun cockpit / wizards | OK (10 / 10 articles) |
| Fécule dans cockpit (min 5 000, Kastell, délai) | OK |
| Non-régression consommation | OK |
| BUG-CONS-MP-003 emplacement auto | OK |
| Alerte seuil après consommation | OK |
| Opérateur sans actualisation cockpit | OK |
| Stock fécule inchangé durant la campagne | OK — 13 500 kg |

**Score : 18/18 OK — 0 bloquant KO**

## Procédure lab exécutée

1. Upgrade module `laplatine_procurement_control` → `18.0.1.6.0`
2. `docker compose restart odoo`
3. Suite tests auto `--test-tags=laplatine_procurement_control` : **113/113**
4. Campagne QA fonctionnelle (`scripts/qa_cockpit_tracking_scope_run.py`)

## Grille QA (18 contrôles)

| ID | Intitulé | Bloquant | Résultat | Preuve |
|---|---|---|---|---|
| PRE-01 | Module upgradé `18.0.1.6.0` | Oui | OK | `preflight_evidence.json` |
| PRE-02 | Suivi consommation fécule | Oui | OK | `preflight_evidence.json` |
| PRE-03 | Entrepôt de pilotage configuré | Oui | OK | `preflight_evidence.json` |
| PRE-04 | Compte manager cockpit QA | Oui | OK | `preflight_evidence.json` |
| AC01 | Article A visible (suivi + OP + fournisseur) | Oui | OK | `cockpit_scope_evidence.json` |
| AC02 | Article B absent (non suivi) | Oui | OK | `cockpit_scope_evidence.json` |
| AC03 | Paramétrage standard insuffisant sans suivi | Oui | OK | `final_evidence.json` |
| AC04 | Décochage retire la ligne | Oui | OK | `cockpit_scope_evidence.json` |
| AC05 | Cochage recrée la ligne | Oui | OK | `cockpit_scope_evidence.json` |
| AC06 | Ligne obsolète supprimée | Oui | OK | `final_evidence.json` |
| AC07 | Article C incomplet visible + alerte | Oui | OK | `cockpit_scope_evidence.json` |
| AC08 | Périmètre commun booléen suivi | Oui | OK | `final_evidence.json` |
| AC09 | Fécule présente après actualisation | Oui | OK | `final_evidence.json` |
| AC10 | Non-régression wizard consommation | Oui | OK | `final_evidence.json` |
| BUG-003 | Emplacement auto consommation persisté | Oui | OK | `final_evidence.json` |
| AC11 | Alerte seuil après consommation | Oui | OK | `final_evidence.json` |
| AC12 | Sécurité opérateur cockpit | Oui | OK | `final_evidence.json` |
| FEC-FINAL | Fécule inchangée fin campagne | Oui | OK | `final_evidence.json` |

## Articles de recette MOA (§13)

| Article | Suivi | Orderpoint | Fournisseur | Attendu | Résultat |
|---|---|---|---|---|---|
| **A** | Oui | Oui | Oui | Visible, données complètes | OK — min 50 kg |
| **B** | Non | Oui | Oui | Absent | OK |
| **C** | Oui | Non | Non | Visible + alertes | OK — `orderpoint_incomplete`, `supplier_missing`, `history_insufficient` |

Cycle cochage/décochage Article A : **OK** (`toggle_cycle` dans `cockpit_scope_evidence.json`).

## Comptes QA créés

| Login | Mot de passe | Groupes |
|---|---|---|
| `qa_cockpit_scope_operator_20260705` | `CockpitScope!2026` | Utilisateur interne + Consommation MP |
| `qa_cockpit_scope_manager_20260705` | `CockpitScope!2026` | Utilisateur interne + Actualisation cockpit |

## Observations

- Stock fécule lab au moment du run : **13 500 kg** sur `WH/Stock/Conteneur Fécule` (inchangé durant la campagne ; écart vs recette historique 13 000 kg — à noter pour MOA, non bloquant QA technique).
- L'actualisation cockpit a rafraîchi le snapshot ; les lignes QA jetables restent en base mais n'impactent pas la fécule.
- Warnings Odoo connus `compute_sudo/store` sur `laplatine.procurement.control.line` : non bloquants.

## Prochaine étape

- **Passe MOA UI** : validation visuelle du cockpit (filtrage perçu, libellés, navigation).
- Production maintenue en **STOP**.

## Conclusion

Évolution CONS-MP-003 validée QA lab. Le code `18.0.1.6.0` (`6046175`) est **GO QA**. Production **STOP**.
