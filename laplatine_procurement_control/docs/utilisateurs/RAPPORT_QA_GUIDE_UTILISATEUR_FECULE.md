# Rapport QA — Guide utilisateur fécule de manioc

| Élément | Valeur |
|---------|--------|
| **Référence** | `LAPLATINE-CONS-MP-USER-001` |
| **Run** | `QA-USER-FECULE-YYYYMMDD_HHMMSS` |
| **Environnement** | Production — `https://prod.sarl-la-platine.fr` |
| **Compte de test** | |
| **Date** | |
| **Verdict** | ☐ `GO_QA_GUIDE_UTILISATEUR_FECULE` / ☐ `NO_GO` |

---

## 1. Contrôles profil utilisateur

| # | Contrôle | Résultat | Preuve |
|---|----------|----------|--------|
| 1 | Menus **Consommation matière première** et **Mise à jour des quantités en stock** visibles | ☐ OK / ☐ KO | |
| 2 | Cockpit **non** visible | ☐ OK / ☐ KO | |
| 3 | **FÉCULE DE MANIOC** sélectionnable dans les deux wizards | ☐ OK / ☐ KO | |
| 4 | Stock disponible lisible | ☐ OK / ☐ KO | |
| 5 | Aucune étape nécessite un droit absent du profil | ☐ OK / ☐ KO | |

---

## 2. Captures produites

| Fichier | Présent | Conforme |
|---------|---------|----------|
| `01_menu_la_platine.png` | ☐ | ☐ |
| `02_consommation_fecule.png` | ☐ | ☐ |
| `03_confirmation_consommation.png` | ☐ | ☐ |
| `04_mise_a_jour_fecule.png` | ☐ | ☐ |
| `05_confirmation_mise_a_jour.png` | ☐ | ☐ |
| `06_alerte_stock_minimum.png` | ☐ | ☐ |

---

## 3. Conformité libellés interface

| Libellé guide | Libellé production | Identique |
|---------------|-------------------|-----------|
| Consommation matière première | | ☐ |
| Mise à jour des quantités en stock | | ☐ |
| Enregistrer la consommation | | ☐ |
| Mettre à jour le stock | | ☐ |
| Quantité disponible (kg) | | ☐ |
| Quantité prélevée (kg) | | ☐ |
| Quantité enregistrée dans Odoo | | ☐ |
| Quantité réellement comptée | | ☐ |
| Écart calculé | | ☐ |
| Motif | | ☐ |
| Message alerte seuil | | ☐ |

---

## 4. Données production constatées (fécule)

| Indicateur | Valeur |
|------------|--------|
| Stock fécule au moment des captures | |
| Seuil minimum configuré | |
| Alerte déclenchée lors du test | ☐ Oui / ☐ Non |
| Impact stock des opérations de capture | |

---

## 5. Guide livré

| Livrable | Chemin | Statut |
|----------|--------|--------|
| Guide utilisateur | [`GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.md`](GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.md) | ☐ Finalisé |
| Captures | [`captures/guide_fecule/`](captures/guide_fecule/) | ☐ Complet |

---

## 6. Écarts / remarques

*(À compléter par QA)*

---

## 7. Verdict

```text
☐ GO_QA_GUIDE_UTILISATEUR_FECULE
☐ NO_GO — motif :
```
