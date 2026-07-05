# Rapport QA — CONS-MP-003 Recentrage cockpit

| Élément | Valeur |
|---------|--------|
| **Référence** | `LAPLATINE-CONS-MP-003` |
| **Date** | 2026-07-05 |
| **URL lab** | `http://127.0.0.1:18018` |
| **Module** | `laplatine_procurement_control` |
| **Version** | `18.0.1.6.0` |
| **Verdict** | **GO_QA_DEV_LAB** |
| **Production** | **STOP** |

---

## 1. Objectif

Limiter le cockpit aux articles marqués **Suivi consommation La Platine**
(`product.template.laplatine_consumption_tracking`).

---

## 2. Procédure exécutée

1. Upgrade module `laplatine_procurement_control` → `18.0.1.6.0`
2. Suite tests auto `--test-tags=laplatine_procurement_control` : **113/113 verts**
3. Vérification code : filtre ajouté dans `get_eligible_products()`

---

## 3. Critères d'acceptation automatisés

| ID | Test | Résultat |
|----|------|----------|
| AC01 / T35 | Article suivi visible | OK |
| AC02 / T36 | Article non suivi absent | OK |
| AC03 / T37–T38 | Orderpoint/fournisseur insuffisants sans suivi | OK |
| AC04 / T39 | Décochage retire la ligne | OK |
| AC05 / T40 | Cochage crée la ligne | OK |
| AC06 | Lignes obsolètes supprimées à l'actualisation | OK (existant + T39) |
| AC07 / T41 | Article incomplet visible avec alerte | OK |
| AC08 / T42 | Périmètre commun booléen suivi | OK |
| AC09 | Données standard Odoo | OK (non-régression) |
| AC10 / T43–T44 | Non-régression wizards | OK |
| AC11 | Alertes seuil | OK (non-régression suite) |
| AC12 / T45 | Opérateur sans accès actualisation cockpit | OK |

---

## 4. Correctifs inclus dans le lot

| Référence | Objet | Version |
|-----------|-------|---------|
| BUG-CONS-MP-003 | Emplacement auto consommation non persisté (`force_save` + `_resolve_location_id`) | inclus `18.0.1.6.0` |

---

## 5. Recette fonctionnelle MOA UI

À exécuter sur le lab avec les articles A / B / C décrits dans la note MOA CONS-MP-003.

---

## 6. Réserve

- Recette MOA UI CONS-MP-003 : **en attente**
- Production : **STOP**
