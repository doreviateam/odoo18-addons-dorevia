# Preuves recette / QA lab — `laplatine_procurement_control`

Artefacts versionnés issus des campagnes QA et recette sur `laplatine_prod`.

## Procédure lab (avant recette ou livraison)

1. **Upgrade** du module sur la base cible :

```bash
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d laplatine_prod \
  -u laplatine_procurement_control --stop-after-init
```

2. **Redémarrer** le service Odoo pour recharger le runtime web :

```bash
docker compose restart odoo
```

3. **Contrôler** la version chargée (UI ou shell) — attendu : version manifest du commit livré.

4. **Recette fonctionnelle** MOA/QA sur le lab avant tout GO production.

Sans redémarrage après upgrade, l’UI peut encore exécuter l’ancien code (cf. réserve `ENV-CONS-MP-S3-001`).

## Campagnes

| Run | Date | Verdict | Dossier |
|-----|------|---------|---------|
| `QA-PC-V1-20260705_082258` | 2026-07-05 | **GO** 18/18 (bloquants 8/8) | [`QA-PC-V1-20260705_082258/`](QA-PC-V1-20260705_082258/) |
| `QA-CONS-MP-S12-20260705_183101` | 2026-07-05 | **NO_GO** (menu cockpit) | [`QA-CONS-MP-S12-20260705_183101/`](QA-CONS-MP-S12-20260705_183101/) |
| `QA-CONS-MP-S12-POSTFIX-20260705_185917` | 2026-07-05 | **GO_QA_SLICE12** | [`QA-CONS-MP-S12-POSTFIX-20260705_185917/`](QA-CONS-MP-S12-POSTFIX-20260705_185917/) |
| `QA-CONS-MP-S3-20260705_193007` | 2026-07-05 | **GO_QA_SLICE3_LAB** (réserve env.) | [`QA-CONS-MP-S3-20260705_193007/`](QA-CONS-MP-S3-20260705_193007/) |
| `QA-CONS-MP-S4-20260705_195544` | 2026-07-05 | **GO_QA_SLICE4_LAB** | [`QA-CONS-MP-S4-20260705_195544/`](QA-CONS-MP-S4-20260705_195544/) |
| `QA-CONS-MP-MOA-UI-20260705_200300` | 2026-07-05 | **GO_MOA_UI_SLICE4** | [`QA-CONS-MP-MOA-UI-20260705_200300/`](QA-CONS-MP-MOA-UI-20260705_200300/) |

Référentiel recette MOA : [`../GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md`](../GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md)

Clôture V1 consommation MP : [`../NOTE_CLOTURE_V1_CONSOMMATION_MP.md`](../NOTE_CLOTURE_V1_CONSOMMATION_MP.md)

Déploiement production : [`../GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md`](../GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md)

Production : **STOP** — aucun GO déploiement.
