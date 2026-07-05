# Preuves recette / QA lab — `laplatine_procurement_control`

Artefacts versionnés issus des campagnes QA et recette sur `laplatine_prod`.

## Procédure lab (avant recette ou livraison)

Après upgrade module ou changement de code monté en volume, **redémarrer le service Odoo** pour recharger le runtime web :

```bash
docker compose restart odoo
```

Sans ce redémarrage, l’UI peut encore exécuter l’ancien code (cf. réserve `ENV-CONS-MP-S3-001`).

## Campagnes

| Run | Date | Verdict | Dossier |
|-----|------|---------|---------|
| `QA-PC-V1-20260705_082258` | 2026-07-05 | **GO** 18/18 (bloquants 8/8) | [`QA-PC-V1-20260705_082258/`](QA-PC-V1-20260705_082258/) |
| `QA-CONS-MP-S12-20260705_183101` | 2026-07-05 | **NO_GO** (menu cockpit) | [`QA-CONS-MP-S12-20260705_183101/`](QA-CONS-MP-S12-20260705_183101/) |
| `QA-CONS-MP-S12-POSTFIX-20260705_185917` | 2026-07-05 | **GO_QA_SLICE12** | [`QA-CONS-MP-S12-POSTFIX-20260705_185917/`](QA-CONS-MP-S12-POSTFIX-20260705_185917/) |
| `QA-CONS-MP-S3-20260705_193007` | 2026-07-05 | **GO_QA_SLICE3_LAB** (réserve env.) | [`QA-CONS-MP-S3-20260705_193007/`](QA-CONS-MP-S3-20260705_193007/) |

Référentiel recette MOA : [`../GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md`](../GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md)

Production : **STOP** — aucun GO déploiement.
