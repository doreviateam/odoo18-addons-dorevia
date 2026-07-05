# NOTE DE CADRAGE — SÉPARATION DES WIZARDS CONSOMMATION ET MISE À JOUR DU STOCK

| Élément                                       | Valeur                                                                    |
| --------------------------------------------- | ------------------------------------------------------------------------- |
| **Référence**                                 | `LAPLATINE-CONS-MP-002`                                                   |
| **Intitulé**                                  | Séparation de la consommation et de la mise à jour des quantités en stock |
| **Module**                                    | `laplatine_procurement_control`                                           |
| **Version actuelle**                          | `18.0.1.4.0`                                                              |
| **Version cible proposée**                    | `18.0.1.5.0`                                                              |
| **Base Git de départ**                        | `origin/main` — commit `8b77aee`                                          |
| **Environnement de développement et recette** | `laplatine-odoo18-lab` / base `laplatine_prod`                            |
| **Production**                                | **STOP**                                                                  |
| **Priorité**                                  | Haute — simplification opérationnelle                                     |
| **Nature**                                    | Évolution ergonomique sans changement de doctrine stock                   |

## Décision MOA

> Le wizard unique est remplacé par deux interfaces distinctes.
>
> `Consommation matière première` est exclusivement dédié aux prélèvements.
>
> `Mise à jour des quantités en stock` est exclusivement dédié aux corrections après comptage.
>
> Les traitements standards Odoo déjà validés sont conservés sans changement.
>
> **GO Dev sur le lab. Production maintenue en STOP.**

## Navigation cible

```text
Inventaire
└── La Platine
    ├── Consommation matière première
    └── Mise à jour des quantités en stock
```

## Modèles

| Wizard | Modèle |
|--------|--------|
| Consommation | `laplatine.raw.material.consumption.wizard` |
| Mise à jour stock | `laplatine.raw.material.stock.update.wizard` |

## Identifiants XML

| Ressource | XML ID |
|-----------|--------|
| Vue consommation | `raw_material_consumption_wizard_view_form` |
| Action consommation | `raw_material_consumption_wizard_action` |
| Menu consommation | `menu_raw_material_consumption` |
| Vue mise à jour | `raw_material_stock_update_wizard_view_form` |
| Action mise à jour | `raw_material_stock_update_wizard_action` |
| Menu mise à jour | `menu_raw_material_stock_update` |

## Critères d'acceptation

- AC01–AC15 : voir note complète MOA (réf. `LAPLATINE-CONS-MP-002`)
- Tests automatisés T23–T34 dans `tests/test_procurement_consumption_wizards_separation.py`
- 85 tests existants + nouveaux tests = 100 % verts

## Implémentation

| Slice | Contenu |
|-------|---------|
| A | Nouveau modèle transient, vues, menus, sécurité, simplification wizard consommation |
| B | Branchement métier, notifications, seuil, tests T23–T34, non-régression |

Service partagé inchangé : `laplatine.procurement.stock.ops`
