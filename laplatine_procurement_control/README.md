# laplatine_procurement_control

Module Odoo 18 CE — **Pilotage des approvisionnements** et **Consommation matières premières** pour la SARL La Platine.

## Statut V1

| Élément | Statut |
|---------|--------|
| Version module | `18.0.1.4.0` |
| Commit de référence | `09d801e` (`origin/main`) |
| Cockpit approvisionnements | **GO QA lab** — [`recette_qa/QA-PC-V1-20260705_082258/`](recette_qa/QA-PC-V1-20260705_082258/) |
| Consommation MP (Slices 1–4) | **GO Dev / GO QA / GO MOA UI lab** |
| Note de clôture V1 consommation | [`NOTE_CLOTURE_V1_CONSOMMATION_MP.md`](NOTE_CLOTURE_V1_CONSOMMATION_MP.md) |
| Guide déploiement production | [`GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md`](GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md) |
| Tests automatisés | **85/85** verts (lab) |
| Déploiement production | **STOP** — GO MOA déploiement requis |

## Documentation

| Document | Description |
|----------|-------------|
| [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md) | Spécification cockpit |
| [`note_cadrage.md`](note_cadrage.md) | Cadrage cockpit V0.1 |
| [`docs/cadrage/NOTE_CADRAGE_CONSOMMATION_MP_LAPLATINE_V1.md`](../docs/cadrage/NOTE_CADRAGE_CONSOMMATION_MP_LAPLATINE_V1.md) | Cadrage consommation MP |
| [`GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md`](GUIDE_RECETTE_MOA_LAB_PROCUREMENT_CONTROL_V1.md) | Recette MOA cockpit |
| [`GUIDE_RECETTE_QA_CONSOMMATION_MP_SLICE12_LAB.md`](GUIDE_RECETTE_QA_CONSOMMATION_MP_SLICE12_LAB.md) | Recette QA Slices 1–2 |
| [`recette_qa/README.md`](recette_qa/README.md) | Index preuves QA + procédure lab |

## Objectifs

- **Cockpit** : lecture et interprétation des approvisionnements (Achats / Stock / Fabrication).
- **Consommation MP** : wizard opérationnel prélèvement + correction après comptage, via mouvements Odoo standards.

## Navigation

```text
Inventaire
├── La Platine
│   └── Consommation matière première     ← opérateurs MP
└── Configuration
    └── Pilotage approvisionnements
        └── Cockpit                       ← supervision
```

## Environnement

- Lab : `laplatine-odoo18-lab` / base `laplatine_prod` / `http://127.0.0.1:18018`
- Production : **STOP** — non déployé

## Dépendances

- `stock`, `purchase`, `purchase_stock`, `mrp`

## Dette technique

- Paramètres temporairement sur `res.company` (migration `res.config.settings` différée).
- Warnings `compute_sudo` sur `laplatine.procurement.control.line` (non bloquants).
