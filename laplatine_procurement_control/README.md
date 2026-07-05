# laplatine_procurement_control

Module Odoo 18 CE — **Pilotage des approvisionnements** et **Consommation matières premières** pour la SARL La Platine.

## Statut

| Élément | Statut |
|---------|--------|
| Version module | `18.0.1.6.0` |
| Cockpit approvisionnements | **GO QA lab** — périmètre articles « Suivi consommation La Platine » |
| Consommation MP V1 (Slices 1–4) | **GO Dev / GO QA / GO MOA UI lab** |
| Séparation wizards (CONS-MP-002) | **GO QA + GO MOA UI lab** — [`recette_qa/QA-CONS-MP-WIZSEP-20260705_203637/`](recette_qa/QA-CONS-MP-WIZSEP-20260705_203637/) |
| Recentrage cockpit (CONS-MP-003) | **GO QA + GO MOA UI lab** — [`recette_qa/QA-CONS-MP-003-20260705_220000/`](recette_qa/QA-CONS-MP-003-20260705_220000/) + [`MOA UI`](recette_qa/QA-CONS-MP-MOA-UI-003-20260705_220400/) |
| Tests automatisés | **113/113** verts (lab) |
| Déploiement production | **GO exploitation** depuis le 2026-07-05 — [`RAPPORT`](recette_qa/PROD-CONS-MP-20260705/RAPPORT_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP.md) |
| Commit production | `2af0fc1b14d7b9ff1552eb61d72c62613babff43` — version `18.0.1.6.0` |

## Documentation

| Document | Description |
|----------|-------------|
| [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md) | Spécification cockpit |
| [`docs/cadrage/NOTE_CADRAGE_SEPARATION_WIZARDS_MP_LAPLATINE_V1_1.md`](../docs/cadrage/NOTE_CADRAGE_SEPARATION_WIZARDS_MP_LAPLATINE_V1_1.md) | Cadrage CONS-MP-002 |
| [`NOTE_CLOTURE_V1_CONSOMMATION_MP.md`](NOTE_CLOTURE_V1_CONSOMMATION_MP.md) | Clôture V1 + V1.1 consommation |
| [`GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md`](GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md) | Guide déploiement production |
| [`docs/utilisateurs/DEMANDE_QA_LAPLATINE-CONS-MP-USER-001.md`](docs/utilisateurs/DEMANDE_QA_LAPLATINE-CONS-MP-USER-001.md) | Demande QA guide fécule Vérena / Ethel |
| [`recette_qa/README.md`](recette_qa/README.md) | Index preuves QA / MOA |

## Périmètre cockpit

Le cockpit ne présente que les articles dont la case **« Suivi consommation La Platine »**
(`product.template.laplatine_consumption_tracking`) est cochée. Ce même indicateur pilote
les wizards consommation et mise à jour stock.

## Navigation

```text
Inventaire
├── La Platine
│   ├── Consommation matière première          ← prélèvements production
│   └── Mise à jour des quantités en stock     ← corrections après comptage
└── Configuration
    └── Pilotage approvisionnements
        └── Cockpit                            ← supervision
```

## Environnement

- Lab : `laplatine-odoo18-lab` / base `laplatine_prod` / `http://127.0.0.1:18018`
- Production : `/opt/laplatine` — `https://prod.sarl-la-platine.fr` — **GO exploitation** (2026-07-05)

## Dépendances

- `stock`, `purchase`, `purchase_stock`, `mrp`
