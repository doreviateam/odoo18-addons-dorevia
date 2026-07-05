# laplatine_procurement_control

Module Odoo 18 CE — **Pilotage des approvisionnements** pour la SARL La Platine.

## Statut V1

| Élément | Statut |
|---------|--------|
| Version | `18.0.1.1.0` — **V1 en recette lab** |
| Note de cadrage | [`note_cadrage.md`](note_cadrage.md) V0.1 |
| Spécification | [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md) |
| GO faisabilité technique | ✅ |
| GO faisabilité MOA | ✅ |
| GO MOA spec V1 | ✅ |
| Arbitrage `watch_lead_days` | ✅ **7 jours** (défaut société, paramétrable) |
| GO développement | ✅ |
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
