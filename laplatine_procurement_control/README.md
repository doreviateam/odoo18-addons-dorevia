# laplatine_procurement_control

Module Odoo 18 CE — **Pilotage des approvisionnements** pour la SARL La Platine.

## Statut V1

| Élément | Statut |
|---------|--------|
| Version | `18.0.1.1.0` — **GO QA pré-recette lab** |
| QA lab (2026-07-05) | **18/18 GO** — run `QA-PC-V1-20260705_082258`, bloquants 8/8 — preuves [`recette_qa/`](recette_qa/) |
| Note de cadrage | [`note_cadrage.md`](note_cadrage.md) V0.1 |
| Spécification | [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md) |
| GO faisabilité technique | ✅ |
| GO faisabilité MOA | ✅ |
| GO MOA spec V1 | ✅ |
| Arbitrage `watch_lead_days` | ✅ **7 jours** (défaut société, paramétrable) |
| GO développement | ✅ |
| Recette MOA lab | [`GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md`](GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md) — **GO QA** ; recette humaine MOA (atelier fécule) à planifier |
| Déploiement production | ⏸ — STOP jusqu'à GO MOA explicite |

Spécification détaillée : [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md)

## Objectif

Cockpit transverse de lecture et d'interprétation au-dessus des applications
**Achats**, **Stock** et **Fabrication** — sans second stock, sans duplication
des commandes ou réceptions, sans circuit spécifique à un article.

## Environnement

- Lab : `laplatine-odoo18-lab` / base `laplatine_prod`
- Production : **STOP** — non déployé

## Dépendances

- `stock`, `purchase`, `purchase_stock`, `mrp`

## Dette technique

Paramètres temporairement exposés sur `res.company` en raison du conflit de
validation `facturx_level` sur la base lab ; migration vers `res.config.settings`
à réaliser lorsque le socle le permettra.
