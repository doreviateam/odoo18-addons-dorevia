# Rapport QA — Séparation wizards consommation / mise à jour stock

| Élément | Valeur |
|---|---|
| Référence cadrage | `LAPLATINE-CONS-MP-002` |
| Run | `QA-CONS-MP-WIZSEP-20260705_203637` |
| Date recette | 2026-07-05 |
| Testeur | Agent QA (backend wizard ORM + tests auto) |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Module | `laplatine_procurement_control` |
| Version installée | `18.0.1.5.0` |
| Tests auto | **100/100 verts** |
| Production | **STOP — aucun déploiement production** |

## Verdict

**GO_QA_WIZSEP_LAB**

Séparation des wizards validée sur le lab : deux menus distincts, deux modèles transient, logique stock inchangée, fécule protégée en recette ergonomique.

| Contrôle | Résultat |
|---|---|
| Procédure lab (upgrade + restart) | OK — version `18.0.1.5.0` |
| Deux menus La Platine | OK |
| Wizard consommation épuré (sans mode correction) | OK |
| Wizard mise à jour épuré (sans prélèvement) | OK |
| Emplacements consommation (stock > 0) | OK |
| Emplacements mise à jour (y compris stock nul) | OK |
| Sécurité opérateur sans cockpit | OK |
| Cockpit non régressé | OK |
| Recette ergonomique fécule (sans validation) | OK — stock inchangé `13 000 kg` |
| Consommation métier (produit jetable) | OK — 5 kg prélevés |
| Correction métier (produit jetable) | OK — notification « Stock mis à jour » |
| Correction depuis stock nul | OK |
| Motif obligatoire / qty négative | OK |
| Seuil min après consommation et correction | OK — alerte `warning` |
| Fécule finale | OK — `13 000 kg` (identique début campagne) |

## Procédure lab exécutée

1. Upgrade module `laplatine_procurement_control` → `18.0.1.5.0`
2. `docker compose restart odoo`
3. Campagne QA fonctionnelle (`scripts/qa_wizard_separation_run.py`)
4. Suite tests auto `--test-tags=laplatine_procurement_control` : **100/100**

## Grille QA (23 contrôles)

| ID | Intitulé | Bloquant | Résultat | Preuve |
|---|---|---|---|---|
| PRE-01 | Module upgradé `18.0.1.5.0` | Oui | OK | `preflight_evidence.json` |
| PRE-02 | Suivi consommation fécule | Oui | OK | `preflight_evidence.json` |
| PRE-03 | Groupe opérateur QA | Oui | OK | `preflight_evidence.json` |
| AC01 | Deux menus distincts | Oui | OK | `final_evidence.json` |
| AC02 | Ouverture wizard dédié par menu | Oui | OK | `final_evidence.json` |
| AC03 | Aucun mode / bascule | Oui | OK | `final_evidence.json` |
| AC04 | Wizard consommation épuré | Oui | OK | `final_evidence.json` |
| AC05 | Wizard mise à jour épuré | Oui | OK | `final_evidence.json` |
| AC08 | Emplacements consommation (stock > 0) | Oui | OK | `final_evidence.json` |
| AC09 | Emplacements mise à jour (stock nul inclus) | Oui | OK | `final_evidence.json` |
| AC10 | Sécurité opérateur | Oui | OK | `final_evidence.json` |
| AC13 | Non-régression cockpit | Oui | OK | `final_evidence.json` |
| ERG-01 | Recette ergonomique consommation fécule | Oui | OK | `ergo_fecule_evidence.json` |
| ERG-02 | Recette ergonomique mise à jour fécule | Oui | OK | `ergo_fecule_evidence.json` |
| AC15 | Fécule protégée (sans validation) | Oui | OK | `ergo_fecule_evidence.json` |
| AC06 | Consommation nominale | Oui | OK | `business_evidence.json` |
| AC06b | Contrôles consommation | Oui | OK | `business_evidence.json` |
| AC07 | Correction nominale | Oui | OK | `business_evidence.json` |
| BIZ-03 | Correction emplacement stock nul | Oui | OK | `business_evidence.json` |
| BIZ-04 | Motif / qty négative | Oui | OK | `business_evidence.json` |
| AC12 | Seuil min après mise à jour | Oui | OK | `business_evidence.json` |
| AC12b | Seuil min après consommation | Oui | OK | `business_evidence.json` |
| FEC-FINAL | Fécule inchangée fin campagne | Oui | OK | `final_evidence.json` |

**Score : 23/23 OK — 0 bloquant KO**

## Méthode QA

- **Wizard ORM** sous profil opérateur (`qa_wizsep_operator_20260705`) : même code métier que les boutons UI.
- **Recette ergonomique fécule** : ouverture des deux wizards, saisie des champs, **aucune validation** (AC15).
- **Recette métier** : produits jetables QA (`QA WizSep Probe Product`, etc.) pour consommation, correction, seuil.
- **Pas de capture navigateur** dans ce run — passe MOA UI recommandée avant production.

## Compte QA créé

| Login | Mot de passe | Groupes |
|---|---|---|
| `qa_wizsep_operator_20260705` | `WizSep!2026` | Utilisateur interne + Consommation MP |

## Observations

- Stock fécule lab au moment du run : **13 000 kg** sur `WH/Stock/Conteneur Fécule` (inchangé durant la campagne).
- Notification correction conforme cadrage : titre « Stock mis à jour », format avant / après comptage / écart.
- Warnings Odoo connus `compute_sudo/store` sur le cockpit : non bloquants.

## Prochaine étape

- **Passe MOA UI** en lecture seule sur les deux menus (validation visuelle des parcours Véréna / Ethel / Michel).
- Production maintenue en **STOP** jusqu'à GO MOA UI + commit code.

## Conclusion

Évolution CONS-MP-002 validée QA lab. Le code `18.0.1.5.0` peut être commité côté QA. Production **STOP**.
