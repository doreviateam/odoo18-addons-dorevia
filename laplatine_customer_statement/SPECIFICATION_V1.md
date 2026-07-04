# Spécification fonctionnelle V1 — `laplatine_customer_statement`

## 1. Identification

| Élément | Valeur |
|---|---|
| Projet | SARL La Platine — Odoo 18 Community |
| Module technique | `laplatine_customer_statement` |
| Emplacement | `addons/odoo18-addons-dorevia/laplatine_customer_statement` |
| Nom fonctionnel | État de facturation client |
| Version livrée | **V1.1 — `18.0.1.1.1`** (gelée) |
| Référence Git | branche `main`, version `18.0.1.1.1` |
| Statut | **V1.1 validée et clôturée** — confirmation usage Ethel / Véréna ultérieure |
| Utilisatrices principales | Ethel et Véréna |

## 2. Contexte

Ethel et Véréna produisent actuellement des états de facturation à partir
d'exports ou de tableaux repris manuellement dans Excel.

Les opérations observées comprennent notamment :

- la suppression de colonnes inutiles ;
- le raccourcissement de certains intitulés ;
- l'ajustement des largeurs et de la mise en page ;
- la préparation du document pour une impression au format A4 ;
- la transmission manuelle du résultat.

Cette pratique est chronophage, peu reproductible et peut créer des écarts
entre le document transmis et les données présentes dans Odoo.

## 3. Objectif

Permettre à Ethel ou Véréna de générer directement depuis Odoo, pour un
partenaire donné, un état de facturation sur les **90 derniers jours** (fenêtre
glissante, date du jour incluse).

Le résultat doit être un fichier Excel XLSX :

- lisible sans retraitement ;
- directement imprimable ;
- mis en page au format A4 ;
- exploitable sur une ou plusieurs pages selon le nombre de factures.

Le module ne doit pas créer de comptabilité parallèle ni dupliquer les données
standard d'Odoo.

## 4. Besoin fonctionnel retenu

Le document cible est un **état mensuel de facturation client**.

Il ne s'agit pas, en V1 :

- d'une balance âgée ;
- d'un état des seuls impayés ;
- d'un grand livre partenaire ;
- d'un relevé de compte chronologique avec règlements sur des lignes séparées.

## 5. Scénario utilisateur principal

> En tant qu'utilisatrice comptable ou administrative, je sélectionne un
> partenaire. Odoo me propose automatiquement les 90 derniers jours (date du
> jour incluse). Je génère un fichier Excel présentant toutes les factures
> client de cette période, y compris celles déjà payées. Le fichier est
> immédiatement imprimable au format A4 sans reprise manuelle.

## 6. Paramètres de génération

### 6.1 Partenaire

- Un partenaire client est sélectionné.
- Le rapport est généré pour un seul partenaire à la fois.
- Aucun partenaire, y compris EMD, EMI ou Saveur Caraïbe, ne doit être codé en dur.

### 6.2 Période

La période proposée par défaut est une **fenêtre glissante de 90 jours**,
date du jour incluse :

- `date_to` = aujourd'hui ;
- `date_from` = aujourd'hui − 89 jours.

Exemple :

- date de génération : 4 juillet 2026 ;
- date de début proposée : 6 avril 2026 ;
- date de fin proposée : 4 juillet 2026.

La période doit rester modifiable par l'utilisatrice avant génération.

### 6.3 Date de sélection des factures

La sélection repose sur la date de facture Odoo (`invoice_date`).

Elle ne repose pas sur :

- la date de création de l'enregistrement ;
- la date du règlement ;
- la date du dernier rapprochement.

## 7. Factures incluses

Le rapport inclut par défaut toutes les factures client correspondant au
partenaire et à la période sélectionnés, quel que soit leur état de paiement.

Les factures suivantes doivent donc apparaître :

- payées ;
- partiellement payées ;
- non payées.

### Règle de V1 à confirmer lors de la recette

Les factures comptabilisées sont incluses. Les brouillons et les factures
annulées sont exclus du rapport.

## 8. Avoirs

Les avoirs client ne sont pas inclus dans la V1 par défaut.

Ils ne doivent être ni déduits des totaux ni affichés sur des lignes séparées.

Une évolution ultérieure pourra prévoir :

- une option d'inclusion ;
- une présentation séparée ;
- une déduction dans le total net.

## 9. Colonnes du rapport

La V1 doit présenter au minimum les colonnes suivantes :

| Colonne | Contenu |
|---|---|
| Facture | Numéro de la facture client |
| Date | Date de facture |
| Échéance | Date d'échéance |
| Montant TTC | Montant total de la facture |
| Réglé | Montant déjà réglé |
| Solde | Montant restant dû |
| Statut | Libellé selon paiement et échéance (voir §9.1) |

Le montant réglé doit être calculé à partir des montants standard Odoo :

`Montant réglé = Montant total - Montant restant dû`

Aucun nouveau montant comptable stocké ne doit être créé.

### 9.1 Statut et retard

Date de référence : date du jour Odoo à la génération
(`fields.Date.context_today(self)`).

| Situation | Statut affiché |
| --- | --- |
| Facture totalement soldée | Payée |
| Partiellement réglée, échéance non dépassée | Partiellement payée |
| Partiellement réglée, échéance dépassée | Partiellement payée — en retard |
| Non réglée, échéance dépassée | En retard |
| Non réglée, échéance du jour ou future | À payer |
| Paiement en cours | Paiement en cours |

Échéance dépassée si `invoice_date_due < date_du_jour`. Échéance égale à la
date du jour : pas en retard. Sans échéance : statut non bloquant selon
l'état de paiement, sans retrait automatique.

Les statuts « en retard » sont visuellement identifiables par un texte rouge
foncé gras, sans fond coloré. Le fond rouge pâle est réservé à la ligne de
synthèse « Dont montant en retard ».

## 10. Synthèse et totaux

### 10.1 Bloc de synthèse (avant le tableau)

| Indicateur | Calcul |
| --- | --- |
| Total facturé | Σ `amount_total` |
| Total réglé | Σ (`amount_total` − `amount_residual`) |
| Montant total à régler à La Platine | Σ `amount_residual` |
| Dont montant en retard | Σ `amount_residual` des factures non soldées dont `invoice_date_due < date_du_jour` |

### 10.2 Totaux en pied de tableau

Le rapport doit afficher en fin de tableau :

- le total facturé ;
- le total réglé ;
- le total restant dû.

Les totaux doivent porter uniquement sur les factures incluses dans le rapport.

## 11. Format de sortie

Le format principal de la V1 est un fichier **XLSX**.

Il ne s'agit pas d'un export brut de données. Le fichier doit être construit
comme un rapport prêt à consulter, imprimer et transmettre.

Le PDF n'est pas prioritaire dans la V1.

## 12. Mise en page Excel et impression A4

### 12.1 Règle générale

Le rapport doit être imprimable sur une ou plusieurs pages A4 selon le volume.

La mise en page attendue est :

- format papier A4 ;
- orientation paysage ;
- une page maximum en largeur ;
- autant de pages que nécessaire en hauteur ;
- aucune colonne répartie sur une seconde page horizontale.

### 12.2 Éléments de présentation

Le classeur doit contenir :

- un titre : `État de facturation` ;
- le nom du partenaire ;
- la période couverte ;
- la date de génération ;
- un bloc de synthèse (totaux facturé, réglé, à régler, en retard) ;
- les en-têtes de colonnes ;
- le tableau des factures ;
- les totaux ;
- une pagination de type `Page X / Y`.

### 12.3 Réglages d'impression

Le fichier doit intégrer :

- une zone d'impression limitée au rapport ;
- des marges adaptées ;
- une mise à l'échelle sur une page en largeur ;
- une hauteur libre sur plusieurs pages ;
- la répétition de la ligne d'en-tête sur chaque page ;
- des largeurs de colonnes définies ;
- les montants alignés à droite ;
- un format monétaire cohérent ;
- les dates dans un format lisible ;
- le gel de la ligne d'en-tête pour la consultation à l'écran.

L'utilisatrice ne doit pas avoir à :

- supprimer des colonnes ;
- modifier les largeurs ;
- redéfinir la zone d'impression ;
- modifier l'orientation ;
- ajouter manuellement les totaux.

## 13. Sources de données Odoo

Le module doit utiliser les modèles et champs standard, notamment :

- `res.partner` pour le partenaire ;
- `account.move` pour les factures client ;
- `invoice_date` pour la date de facture ;
- `invoice_date_due` pour l'échéance ;
- `amount_total` pour le montant total ;
- `amount_residual` pour le solde restant ;
- `payment_state` pour l'état de paiement.

Le domaine fonctionnel pressenti pour la V1 est fondé sur :

- le partenaire sélectionné ;
- `move_type = 'out_invoice'` ;
- la période sur `invoice_date` ;
- les factures comptabilisées.

## 14. Principes de conception

- Utiliser en priorité le standard Odoo.
- Ne pas dupliquer les montants ou statuts comptables.
- Ne pas modifier les écritures comptables.
- Ne pas coder de clients particuliers en dur.
- Garder le module indépendant du module
  `laplatine_invoice_payment_info`.
- Limiter la V1 à la génération du rapport XLSX.
- Prévoir des tests automatisés sur les règles de sélection et les totaux.

## 15. Hors périmètre V1

Sont exclus de la V1 :

- les relances automatiques ;
- les pénalités de retard ;
- le rapprochement bancaire spécifique ;
- le portail client ;
- l'envoi automatique par e-mail ;
- le PDF ;
- l'affichage des règlements sur des lignes distinctes ;
- le solde comptable progressif ;
- les avoirs ;
- les tableaux de bord ;
- la consolidation de plusieurs partenaires dans un même rapport.

## 16. Critères d'acceptation

### CA-01 — Fenêtre glissante 90 jours

Lors de l'ouverture de l'assistant, la période proposée correspond aux
90 derniers jours, date du jour incluse.

### CA-13 — Statuts avec retard

Les statuts affichés tiennent compte de l'échéance par rapport à la date de
génération, conformément au tableau §9.1.

### CA-14 — Bloc de synthèse

Le rapport affiche avant le tableau le montant total à régler à La Platine
et le montant en retard, distincts et conformes aux définitions §10.1.

### CA-02 — Période modifiable

Ethel ou Véréna peut modifier les dates avant de générer le rapport.

### CA-03 — Partenaire unique

Le rapport est généré pour le partenaire sélectionné uniquement.

### CA-04 — Factures payées incluses

Une facture payée dont la date de facture appartient à la période apparaît
dans le rapport.

### CA-05 — Factures ouvertes incluses

Les factures partiellement payées et non payées de la période apparaissent
également.

### CA-06 — Avoirs exclus

Les avoirs ne figurent pas dans le rapport et ne modifient pas les totaux.

### CA-07 — Exactitude des montants

Pour chaque facture :

- le montant total correspond à Odoo ;
- le solde correspond à `amount_residual` ;
- le montant réglé correspond à la différence entre total et solde.

### CA-08 — Totaux

Les totaux facturé, réglé et restant dû correspondent à la somme des lignes
du rapport.

### CA-09 — Fichier XLSX

La génération produit un fichier `.xlsx` ouvrable dans Excel ou un logiciel
compatible.

### CA-10 — Impression A4

Le fichier est configuré en A4 paysage, sur une page en largeur et une ou
plusieurs pages en hauteur.

### CA-11 — En-têtes répétés

Sur un rapport occupant plusieurs pages, les en-têtes du tableau sont répétés
sur chaque page imprimée.

### CA-12 — Absence de retraitement manuel

Le fichier peut être imprimé sans supprimer de colonnes ni refaire la mise en
page.

## 17. Points à confirmer pendant la recette

Les points suivants restent à valider sur un exemple réel :

- libellé fonctionnel définitif du rapport ;
- ordre exact des colonnes ;
- présence éventuelle d'une référence client ou d'un numéro de commande ;
- format monétaire attendu ;
- comportement en cas de factures dans plusieurs devises ;
- inclusion ou non des contacts enfants du partenaire ;
- message à afficher lorsque la période ne contient aucune facture ;
- nom exact du fichier téléchargé.

## 18. Nom de fichier pressenti

Le fichier peut suivre la convention suivante :

`Etat_facturation_<Partenaire>_<AAAA-MM>.xlsx`

Exemple :

`Etat_facturation_EMD_2026-06.xlsx`

## 19. Historique

### 4 juillet 2026 — clôture V1.1

- Cadrage, développement, recettes technique, visuelle et métier représentative.
- Période par défaut : fenêtre glissante 90 jours.
- Statuts avec retard + bloc de synthèse (montant à régler / en retard).
- Retouche visuelle finale : statuts en texte rouge gras, fond réservé à la synthèse.
- Version `18.0.1.1.1` publiée sur `main`.
- XLSX format maître ; PDF via tableur ; PDF natif Odoo hors périmètre.
- Production : GO explicite requis.
