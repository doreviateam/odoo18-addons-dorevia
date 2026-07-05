# NOTE DE CADRAGE FONCTIONNEL V0.1  
## `laplatine_procurement_control` — La Platine — Pilotage des approvisionnements

**Date :** 05/07/2026  
**Statut :** Première note de cadrage transmise au Dev  
**Référentiel :** Odoo 18  
**Dépôt :** Dorevia  
**Environnement de travail :** `laplatine-odoo18-lab`  
**Base de lab :** `laplatine_prod`  
**Production :** **STOP jusqu’à GO MOA explicite**

---

## 1. Situation initiale

Le répertoire du module a été créé dans le dépôt Dorevia avec un squelette minimal :

```text
laplatine_procurement_control/
├── __init__.py
└── README.md
```

Les fichiers sont actuellement vides et le dossier n’est pas encore suivi par Git.

Le manifeste, les modèles, les vues, les droits et les dépendances ne doivent pas être créés avant validation du cadrage fonctionnel et GO faisabilité.

---

## 2. Identification du module

| Élément | Valeur retenue |
|---|---|
| Nom technique | `laplatine_procurement_control` |
| Nom fonctionnel | **La Platine — Pilotage des approvisionnements** |
| Version initiale pressentie | `18.0.1.0.0` |
| Convention | Cohérente avec `laplatine_customer_statement` |
| Positionnement | Couche de pilotage métier au-dessus du standard Odoo |

---

## 3. Contexte métier

La Platine achète et stocke plusieurs catégories d’articles nécessaires à son activité :

- matières premières ;
- ingrédients ;
- emballages ;
- consommables suivis en stock ;
- marchandises éventuellement achetées pour revente ;
- autres composants ou articles achetés et gérés en stock.

La fécule de manioc constitue le premier cas pilote critique :

- matière première principale ;
- provenance lointaine ;
- délai d’approvisionnement potentiellement long ;
- faible capacité de substitution ;
- impact économique majeur en cas de rupture.

Toutefois, elle ne doit pas bénéficier d’un circuit Odoo spécifique.

La doctrine retenue est de traiter de manière homogène tout article :

1. achetable ;
2. géré en stock ;
3. réceptionné ;
4. consommé, utilisé ou revendu ;
5. réapprovisionné selon les mécanismes standards Odoo.

La particularité d’un article critique doit être portée par son paramétrage et par les indicateurs de pilotage, pas par un processus parallèle.

---

## 4. Objectif métier

Le module doit permettre de :

> **Sécuriser la disponibilité des articles achetés et gérés en stock en donnant à La Platine une vision anticipée des risques de rupture et des actions d’approvisionnement à engager.**

Le besoin de départ n’est pas de recréer la gestion des achats ou du stock.

Le besoin consiste à consolider et interpréter les données déjà présentes dans Odoo afin de rendre les risques :

- visibles ;
- compréhensibles ;
- priorisables ;
- actionnables.

---

## 5. Doctrine fonctionnelle

Le module doit respecter les principes suivants :

### 5.1 Standard Odoo d’abord

Le cycle de référence reste :

> Besoin → Réapprovisionnement → Commande fournisseur → Réception → Stock → Consommation

Les mécanismes standards Odoo doivent rester la source de vérité pour :

- les articles ;
- les fournisseurs ;
- les délais ;
- les commandes fournisseurs ;
- les réceptions ;
- les mouvements de stock ;
- le stock disponible ;
- le stock prévisionnel ;
- les règles de réapprovisionnement.

### 5.2 Pas de duplication

Le module ne doit pas :

- maintenir un second stock ;
- recréer les commandes fournisseurs ;
- recréer les réceptions ;
- remplacer les règles de réapprovisionnement ;
- introduire un circuit propre à la fécule de manioc ;
- recopier durablement des données standards sans justification.

### 5.3 Spécifique limité au pilotage

Le spécifique éventuel devra uniquement couvrir les besoins non satisfaits clairement par le standard, par exemple :

- criticité métier ;
- couverture estimée ;
- statut de risque consolidé ;
- explication du risque ;
- priorisation des actions ;
- cockpit transverse.

---

## 6. Utilisateurs pressentis

### 6.1 Responsable des approvisionnements

Utilisateur principal.

Il doit pouvoir :

- identifier les articles à risque ;
- vérifier les approvisionnements déjà engagés ;
- contrôler les dates de réception attendues ;
- détecter les retards ;
- prioriser les actions à mener ;
- accéder rapidement aux objets Odoo standards concernés.

### 6.2 Direction

Usage principalement consultatif.

La direction doit pouvoir :

- visualiser les articles critiques ;
- comprendre les principaux risques de rupture ;
- apprécier le niveau de sécurisation des approvisionnements ;
- identifier les situations nécessitant une décision.

### 6.3 Production / magasin

Contribution indirecte.

Ces utilisateurs participent à la fiabilité du pilotage par :

- l’enregistrement des consommations ;
- la validation des mouvements de stock ;
- la saisie des réceptions ;
- le signalement d’une consommation inhabituelle ;
- la fiabilisation des inventaires.

Les rôles et droits définitifs restent à confirmer.

---

## 7. Questions auxquelles la V1 doit répondre

Pour chaque article acheté et géré en stock :

1. Quel est le stock disponible ?
2. Quel est le stock prévisionnel ?
3. Quelle quantité est déjà commandée ?
4. Quelles réceptions sont attendues ?
5. Quelle est la prochaine date de réception prévue ?
6. Quel est le délai fournisseur connu ?
7. À quel rythme l’article est-il consommé ?
8. Quelle est la couverture estimée du stock ?
9. Existe-t-il un risque de rupture avant la prochaine réception ?
10. L’article est-il critique pour l’activité ?
11. Quelle action faut-il engager ?
12. Pourquoi l’article est-il signalé ?

---

## 8. Point d’entrée Odoo envisagé

Le point d’entrée privilégié pour la V1 est un écran permanent de pilotage :

> **La Platine → Pilotage des approvisionnements**

Cet écran devra présenter une vue consolidée des articles concernés.

Le besoin initial ne correspond pas à un wizard ponctuel.

L’utilisateur doit pouvoir revenir régulièrement sur un cockpit de surveillance et de décision.

### Navigation attendue

Depuis une ligne du cockpit, l’utilisateur devra pouvoir accéder, selon le cas, à :

- la fiche article ;
- la fiche fournisseur ;
- la règle de réapprovisionnement ;
- la commande fournisseur ;
- la réception attendue ;
- les mouvements ou prévisions de stock pertinents.

Le module doit orienter vers les objets standards plutôt que dupliquer leur gestion.

---

## 9. Informations de pilotage pressenties

| Information | Finalité |
|---|---|
| Article | Identifier le produit concerné |
| Catégorie | Regrouper les articles |
| Fournisseur principal | Identifier la source d’approvisionnement |
| Criticité métier | Mesurer l’impact d’une rupture |
| Stock disponible | Connaître la situation physique actuelle |
| Stock prévisionnel | Intégrer les mouvements futurs confirmés |
| Quantité en commande | Identifier les achats déjà engagés |
| Prochaine réception | Connaître la date attendue |
| Délai fournisseur | Évaluer le temps de réaction nécessaire |
| Consommation moyenne | Mesurer le rythme d’utilisation |
| Couverture estimée | Exprimer l’autonomie en jours ou semaines |
| Seuil de sécurité | Comparer la situation au minimum attendu |
| Statut de risque | Qualifier la situation |
| Motif du statut | Expliquer le signalement |
| Action recommandée | Orienter l’utilisateur |

Cette liste est une base de cadrage et non un gel définitif de l’interface.

---

## 10. Statuts de risque pressentis

La V1 pourra s’appuyer sur une classification simple, à confirmer pendant la faisabilité :

- **Normal** : aucune action immédiate ;
- **À surveiller** : couverture en baisse ou seuil approché ;
- **Action requise** : commande, relance ou sécurisation nécessaire ;
- **Critique** : risque de rupture avant réception ou délai de réaction insuffisant ;
- **Rupture** : stock indisponible ou besoin non couvert ;
- **Réception en retard** : approvisionnement engagé mais non reçu à la date attendue.

Chaque statut devra être explicable par une règle métier lisible.

Aucun code couleur ou libellé définitif n’est imposé à ce stade.

---

## 11. Périmètre V1 proposé

### 11.1 Inclus

- articles achetables et gérés en stock ;
- lecture du stock disponible ;
- lecture du stock prévisionnel ;
- lecture des commandes fournisseurs en cours ;
- lecture des réceptions attendues ;
- identification de la prochaine réception ;
- prise en compte du délai fournisseur ;
- prise en compte des seuils ou règles de réapprovisionnement existants ;
- criticité métier ;
- estimation de couverture ;
- statut de risque ;
- motif du risque ;
- filtres de pilotage ;
- navigation vers les objets Odoo standards ;
- recette initiale sur la fécule de manioc ;
- vérification sur quelques articles moins critiques afin de confirmer le caractère générique.

### 11.2 Exclus de la V1

- nouveau workflow de validation des commandes fournisseurs ;
- remplacement du moteur standard de réapprovisionnement ;
- génération automatique complète des commandes fournisseurs ;
- prévision commerciale avancée ;
- planification industrielle complète ;
- calcul financier détaillé du coût d’une rupture ;
- automatisation transport ou transit international ;
- portail fournisseur ;
- alertes externes par email ou messagerie ;
- circuit codé spécifiquement pour la fécule de manioc ;
- gestion de production complète si elle n’est pas déjà utilisée et cadrée ;
- dépendance comptable sans besoin métier démontré.

---

## 12. Dépendances Odoo pressenties

La faisabilité devra confirmer les dépendances minimales.

Le socle métier attendu repose principalement sur :

- Achats ;
- Stock ;
- Produits ;
- articulation standard achats / stock.

Une dépendance à la fabrication ne devra être retenue que si la consommation doit être calculée depuis les ordres de fabrication.

Une dépendance comptable ne devra être retenue que si des indicateurs financiers sont explicitement intégrés au périmètre.

Les modules OCA déjà présents en production devront être inventoriés, mais aucun module OCA supplémentaire ne doit être ajouté sans justification fonctionnelle et technique.

---

## 13. User story principale

> **En tant que responsable des approvisionnements de La Platine, je veux disposer d’une vue consolidée des articles achetés et gérés en stock afin d’identifier suffisamment tôt les risques de rupture, de vérifier si les commandes en cours couvrent les besoins et de prioriser les actions à engager.**

---

## 14. Critères d’acceptation fonctionnels initiaux

La V1 sera considérée comme utile si l’utilisateur peut, depuis un même point d’entrée :

1. retrouver les articles achetés et gérés en stock entrant dans le périmètre ;
2. distinguer les situations normales, à surveiller, critiques et en rupture ;
3. consulter le stock disponible et le stock prévisionnel ;
4. connaître les quantités déjà commandées ;
5. identifier la prochaine réception attendue ;
6. détecter une réception en retard ;
7. connaître ou retrouver le délai fournisseur ;
8. comprendre la couverture estimée ;
9. comprendre pourquoi un article est signalé ;
10. accéder directement à l’objet Odoo permettant d’agir ;
11. filtrer les articles critiques ou nécessitant une action ;
12. utiliser la même logique pour la fécule de manioc et les autres articles stockés.

---

## 15. Cas pilote

### Fécule de manioc

Le cas pilote doit permettre de valider notamment :

- forte criticité ;
- délai d’approvisionnement long ;
- stock de sécurité renforcé ;
- suivi des commandes en cours ;
- suivi des réceptions attendues ;
- détection d’un risque de rupture avant la prochaine réception ;
- lisibilité de l’action à mener.

Le développement ne devra contenir aucune règle basée sur le nom, la référence ou l’identité spécifique de cet article.

La criticité et les règles applicables doivent être paramétrables et réutilisables.

---

## 16. Questions ouvertes à instruire pendant la faisabilité

Le Dev est invité à analyser les points suivants sans les figer prématurément :

1. Quelle donnée standard utiliser pour la consommation moyenne ?
2. Sur quelle période calculer cette consommation ?
3. Faut-il raisonner en jours, semaines ou les deux ?
4. Comment traiter un article sans historique suffisant ?
5. Comment traiter les consommations irrégulières ?
6. Quelle date de réception utiliser : date planifiée de commande ou date du mouvement entrant ?
7. Comment agréger plusieurs commandes ou plusieurs réceptions ?
8. Comment traiter les commandes brouillon, envoyées, confirmées, annulées ou en retard ?
9. Comment gérer plusieurs fournisseurs et plusieurs délais ?
10. La criticité doit-elle être portée par l’article, la catégorie ou une combinaison des deux ?
11. Quels champs ou règles standards peuvent couvrir le besoin sans spécifique ?
12. Quel est l’impact éventuel de la configuration actuelle de la production et des consommations ?
13. Quels modules OCA déjà installés peuvent être réutilisés ?
14. Faut-il stocker certains indicateurs ou les calculer à la volée ?
15. Quel niveau de performance attendre selon le volume d’articles et de mouvements ?

---

## 17. Attendu du Dev — prochaine étape

À partir de cette note, le Dev doit préparer un **GO faisabilité** comprenant :

### Analyse du standard

- objets Odoo concernés ;
- champs standards réutilisables ;
- vues et actions standards disponibles ;
- mécanismes de réapprovisionnement existants ;
- limites du standard face au besoin.

### Analyse des données

- qualité des fiches articles ;
- fournisseurs et délais renseignés ;
- règles de réapprovisionnement existantes ;
- historique de consommation disponible ;
- commandes et réceptions en cours ;
- configuration des emplacements et flux ;
- cohérence de la base de lab.

### Proposition d’architecture fonctionnelle et technique

- dépendances minimales ;
- éventuels champs spécifiques ;
- indicateurs calculés ;
- point d’entrée proposé ;
- filtres et regroupements ;
- navigation vers le standard ;
- sécurité et droits ;
- risques de performance ;
- stratégie de tests.

### Découpage recommandé

Le Dev pourra proposer :

- un socle V1 minimal ;
- des options différées ;
- les prérequis de données ;
- les arbitrages nécessitant une décision MOA.

---

## 18. Gouvernance

- Aucun développement fonctionnel complet avant retour de faisabilité.
- Aucun déploiement en production avant GO MOA explicite.
- Travail initial exclusivement sur le lab.
- README et spécification fonctionnelle à compléter avant gel du périmètre.
- Toute extension doit préserver la doctrine « standard Odoo d’abord ».
- Toute donnée spécifique doit avoir une justification métier.
- Toute automatisation d’action doit être distincte du simple pilotage et soumise à arbitrage MOA.

---

## 19. Décision de cadrage V0.1

Le module `laplatine_procurement_control` est cadré comme un **cockpit transverse de sécurisation des approvisionnements**.

Il concerne tous les articles achetés et gérés en stock.

Il ne remplace pas les applications Achats et Stock.

La fécule de manioc constitue le premier cas pilote critique, sans traitement logiciel spécifique.

La prochaine décision attendue est un **GO faisabilité Dev**, suivi d’une proposition de périmètre V1 détaillé et de critères d’acceptation consolidés.
