# Rapport déploiement production — `laplatine_billing_report`

| Élément | Valeur |
|---------|--------|
| **Référence** | `DEPLOY-FACT-REPORT-001` / `LP-FACT-REPORT-001` |
| **Date / heure** | 2026-07-07 00 h 18–00 h 20 (France) / 2026-07-06 22 h 18–22 h 20 UTC |
| **Environnement** | `/opt/laplatine` — `https://prod.sarl-la-platine.fr` |
| **Opérateur** | Dorevia (intervention automatisée) |
| **Production** | **DÉPLOYÉ** |

## Verdict technique

**GO déploiement production**

Module `laplatine_billing_report` `18.0.1.0.0` installé. Smoke technique OK. Recette UI MOA (P1/P2) en attente.

## Commits

| Rôle | Hash |
|------|------|
| Avant intervention | `2af0fc1b14d7b9ff1552eb61d72c62613babff43` |
| Déployé | `e47f4ea2adeb284b0f7bd0af4394770ac5cf8de3` |
| Code fonctionnel recetté | inclus (`b0bfaaa` ancêtre) |

## Sauvegardes

| Fichier | Chemin |
|---------|--------|
| PostgreSQL | `/opt/laplatine/backups/20260706_221848_pre_laplatine_billing_report/laplatine_prod.dump` (9,1 Mo) |
| Filestore | `/opt/laplatine/backups/20260706_221848_pre_laplatine_billing_report/filestore_laplatine_prod.tar.gz` (15 Mo) |

## Séquence exécutée

| Étape | Résultat |
|-------|----------|
| Pré-vol `xlsxwriter` | OK — 3.1.9 |
| Arrêt Odoo | OK |
| Sauvegarde PG + filestore | OK |
| Checkout détaché `e47f4ea` | OK |
| Test connexion DB | OK — `odoo_prod@db_prod:5432` |
| `-i laplatine_billing_report` uniquement | OK |
| Redémarrage Odoo | OK |
| HTTP `/web/login` | OK — 200 |

## Contrôles post-déploiement

| Contrôle | Résultat |
|----------|----------|
| Module en base | `installed` / `18.0.1.0.0` |
| Menu ordre | Tableau de bord → Clients → Fournisseurs → **La Platine** → Comptabilité → … |
| Génération XLSX juin 2026 | OK — `Rapport_facturation_La_Platine_2026-06-01_2026-06-30.xlsx` (18 744 octets) |
| Refus sans groupe Facturation | OK |
| `-u` autre module | **Non exécuté** |

## Prérequis MOA post-déploiement

| # | Gate | Statut |
|---|------|--------|
| P1 | Validation Excel natif Windows/Mac | ☐ À faire |
| P2 | Validation Véréna / Ethel export M-1 réel | ☐ À faire |
| P3 | `GO_MOA_PROD_LP_FACT_REPORT_001` explicite | ☐ En attente P1 + P2 |

## Observations

- Warnings préexistants `calendar_public_holiday` / `hr_holidays_public` — hors périmètre, identiques aux déploiements antérieurs.
- Warnings `laplatine.procurement.control.line` au shell — hors périmètre facturation.
- Script `prod_post_deploy_smoke.py` : bug `NameError` corrigé post-déploiement (ordre définition `Wizard`).

## Rollback

Non effectué. Procédure : [`DEPLOIEMENT_PRODUCTION.md`](../../DEPLOIEMENT_PRODUCTION.md) §9 — restaurer sauvegardes ci-dessus + checkout `2af0fc1`.

## Conclusion

> **GO technique déploiement** — module opérationnel en production.  
> **Recette métier P1/P2** à planifier avec Véréna / Ethel.
