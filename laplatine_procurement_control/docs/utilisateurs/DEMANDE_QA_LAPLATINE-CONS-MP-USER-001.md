# DEMANDE QA — Document utilisateur fécule de manioc

| Élément | Valeur |
|---------|--------|
| **Référence** | `LAPLATINE-CONS-MP-USER-001` |
| **Objet** | Préparer le guide utilisateur destiné à Vérena et Ethel |
| **Périmètre** | Fécule de manioc uniquement |
| **Module** | `laplatine_procurement_control` |
| **Version production** | `18.0.1.6.0` |
| **Public visé** | Vérena et Ethel |
| **Environnement de capture** | **Production** — `https://prod.sarl-la-platine.fr` |
| **Format attendu** | Guide court, illustré et imprimable |
| **Niveau de langage** | Simple, opérationnel, sans vocabulaire technique Odoo |
| **Statut** | **En attente QA** |

---

## 1. Objectif du document

Le document doit permettre à Vérena et Ethel d'utiliser seules les deux fonctions disponibles pour la fécule de manioc :

```text
Inventaire
└── La Platine
    ├── Consommation matière première
    └── Mise à jour des quantités en stock
```

### Hors périmètre (interdit dans le guide)

- autres matières premières ;
- cockpit ;
- mouvements de stock techniques ;
- règles de réapprovisionnement ;
- groupes de sécurité ;
- administration Odoo.

### Message principal

> **Je prélève de la fécule : Consommation matière première.**
> **Je compte la fécule restante : Mise à jour des quantités en stock.**

---

## 2. Partie 1 — Consommation de fécule

### Quand utiliser cet écran ?

À chaque fois qu'une quantité de fécule est retirée du stock pour la production.

### Parcours à documenter

```text
Inventaire → La Platine → Consommation matière première
```

### Étapes

1. sélectionner **FÉCULE DE MANIOC** ;
2. vérifier l'emplacement proposé ;
3. lire la **Quantité disponible (kg)** ;
4. saisir la **Quantité prélevée (kg)** ;
5. cliquer sur **Enregistrer la consommation** ;
6. lire la confirmation.

### Message important

La quantité saisie correspond à **la quantité de fécule retirée du stock** — pas à la quantité restante.

### Exemple utilisateur (illustratif — QA : reprendre les valeurs réelles production)

```text
Quantité disponible : 929,23 kg
Quantité prélevée :    25,00 kg
Stock restant :       904,23 kg
```

> **Recette capture consommation** : utiliser une quantité faible (ex. 1 kg) pour limiter l'impact stock production. Annuler si le scénario ne nécessite pas d'enregistrement réel.

---

## 3. Partie 2 — Mise à jour de la quantité en stock

### Quand utiliser cet écran ?

Après un comptage physique, lorsque la quantité de fécule réellement présente est différente de celle affichée dans Odoo.

### Parcours à documenter

```text
Inventaire → La Platine → Mise à jour des quantités en stock
```

### Étapes

1. sélectionner **FÉCULE DE MANIOC** ;
2. vérifier l'emplacement ;
3. lire la **Quantité enregistrée dans Odoo** ;
4. saisir la **Quantité réellement comptée** ;
5. saisir le **Motif** ;
6. cliquer sur **Mettre à jour le stock** ;
7. lire le message de confirmation ;
8. confirmer l'opération (dialogue : *« Confirmez-vous la mise à jour du stock selon la quantité comptée ? »*).

### Message important

La quantité saisie correspond à **la quantité totale de fécule réellement présente après comptage** — pas à l'écart.

Exemple :

```text
Quantité Odoo :       929,23 kg
Quantité comptée :    920,00 kg
Écart calculé :        -9,23 kg
```

Il faut saisir **920,00 kg** — et **non** `-9,23 kg`.

> **Recette capture mise à jour** : privilégier une simulation sans enregistrement (saisie + **Annuler**) sauf si une correction réelle est validée MOA.

---

## 4. Alerte de stock minimum

Expliquer clairement l'alerte visible par Vérena et Ethel dans le wizard après enregistrement.

### Libellés interface (référence code — QA : vérifier à l'identique en production)

Le message attendu dans la notification inclut notamment :

```text
Seuil de réapprovisionnement atteint
Stock restant : … kg
Seuil minimum : … kg
```

> Le titre d'exemple « Stock minimum de fécule atteint » du cadrage MOA est **illustratif**. Le guide final doit reprendre **exactement** les libellés affichés en production.

### Points à préciser dans le guide

- l'alerte est visible directement dans le wizard (notification après enregistrement) ;
- il n'est pas nécessaire d'accéder au cockpit ;
- l'alerte **n'empêche pas** l'enregistrement de l'opération ;
- elle signifie que le niveau de fécule est devenu faible par rapport au minimum défini.

### Interdit dans le guide

Ne pas inventer de consigne supplémentaire : courriel, appel David, activité Odoo, blocage production, etc. La conduite métier associée sera communiquée séparément si nécessaire.

### Capture alerte (`06_alerte_stock_minimum.png`)

Avec un stock fécule production ~**929 kg** et un seuil minimum configuré (ex. **5 000 kg** en lab — **à confirmer en prod**), l'alerte doit apparaître après une consommation ou une mise à jour. QA : constater le seuil min réel en production avant rédaction.

---

## 5. Captures attendues

Compte utilisateur **identique au profil Vérena ou Ethel** (groupe *La Platine — Consommation matières premières* uniquement — pas cockpit).

| Fichier | Contenu |
|---------|---------|
| `01_menu_la_platine.png` | Les deux menus disponibles |
| `02_consommation_fecule.png` | Fécule sélectionnée, stock disponible et quantité prélevée |
| `03_confirmation_consommation.png` | Notification de consommation enregistrée |
| `04_mise_a_jour_fecule.png` | Quantité Odoo, quantité comptée, écart et motif |
| `05_confirmation_mise_a_jour.png` | Dialogue de confirmation |
| `06_alerte_stock_minimum.png` | Alerte visible dans le wizard |

### Exclusions captures

- menus administrateur inutiles ;
- données sensibles ;
- mots de passe ;
- écrans techniques de stock ;
- articles de recette jetables.

Répertoire de dépôt : [`captures/guide_fecule/`](captures/guide_fecule/)

---

## 6. Format du guide

| Élément | Valeur |
|---------|--------|
| Fichier | [`GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.md`](GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.md) |
| PDF imprimable | [`GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.pdf`](GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.pdf) |
| Génération PDF | `python3 docs/utilisateurs/scripts/generate_guide_fecule_pdf.py` |
| Longueur cible | 2 à 4 pages |
| Style | Une idée par section, captures annotées, phrases courtes, **boutons et menus en gras** |
| Usage | Présentation 10 min, aide-mémoire imprimé, envoi message/courriel |
| PDF | Version imprimable produite ultérieurement à partir du MD validé |

Un **brouillon structurel** est fourni — QA : compléter les captures, ajuster les libellés et valider sur production.

---

## 7. Encadré récapitulatif obligatoire

À placer en première ou dernière page du guide :

### À retenir

| Situation | Action |
|-----------|--------|
| Je retire de la fécule pour produire | **Consommation matière première** |
| Je compte la fécule restante | **Mise à jour des quantités en stock** |
| Une alerte de stock minimum apparaît | Je termine correctement l'enregistrement et je prends connaissance du niveau affiché |
| Je ne suis pas sûre de la quantité | J'annule avant de valider |

**Phrase centrale :**

> **Je prélève = Consommation. Je compte = Mise à jour du stock.**

---

## 8. Validation QA demandée

Avant livraison, vérifier avec les profils Vérena / Ethel (ou compte équivalent production) :

| # | Contrôle | OK |
|---|----------|-----|
| 1 | Les deux menus La Platine sont visibles | ☐ |
| 2 | Le cockpit n'est pas visible | ☐ |
| 3 | FÉCULE DE MANIOC est sélectionnable | ☐ |
| 4 | Le stock disponible est lisible | ☐ |
| 5 | L'alerte de stock minimum est visible lorsqu'elle s'applique | ☐ |
| 6 | Les libellés du guide = libellés interface production | ☐ |
| 7 | Aucune étape ne nécessite un droit absent du profil | ☐ |

### Verdict attendu

```text
GO_QA_GUIDE_UTILISATEUR_FECULE
```

---

## 9. Livrables attendus

```text
docs/utilisateurs/GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.md
docs/utilisateurs/GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.pdf
docs/utilisateurs/captures/guide_fecule/*.png
docs/utilisateurs/RAPPORT_QA_GUIDE_UTILISATEUR_FECULE.md
```

Rapport QA : modèle fourni dans [`RAPPORT_QA_GUIDE_UTILISATEUR_FECULE.md`](RAPPORT_QA_GUIDE_UTILISATEUR_FECULE.md).

---

## 10. Références

| Document | Lien |
|----------|------|
| Déploiement production | [`../../GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md`](../../GUIDE_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP_V1.md) |
| Rapport prod | [`../../recette_qa/PROD-CONS-MP-20260705/RAPPORT_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP.md`](../../recette_qa/PROD-CONS-MP-20260705/RAPPORT_DEPLOIEMENT_PRODUCTION_CONSOMMATION_MP.md) |
| Groupes utilisateurs | [`../../NOTE_CLOTURE_V1_CONSOMMATION_MP.md`](../../NOTE_CLOTURE_V1_CONSOMMATION_MP.md) §6 |
