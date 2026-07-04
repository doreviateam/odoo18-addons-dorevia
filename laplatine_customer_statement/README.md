# laplatine_customer_statement

Module Odoo 18 CE — **État mensuel de facturation client** pour la SARL La Platine.

## Statut V1.1

| Élément | Statut |
|---------|--------|
| Version | `18.0.1.1.1` (V1.1 gelée) |
| Commit GitHub | `b7e40e8` — [odoo18-addons-dorevia](https://github.com/doreviateam/odoo18-addons-dorevia) |
| GO technique | ✅ — 16 tests, 0 échec, 0 erreur |
| GO fonctionnel représentatif | ✅ |
| GO visuel / impression | ✅ |
| GO clôture lab | ✅ |
| Confirmation usage Ethel / Véréna | Ultérieure — non bloquante |
| Déploiement production | ⏸ — GO explicite requis |

Spécification détaillée : [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md)  
Artefacts de recette : [`outputs/laplatine_customer_statement_visual_qa/`](../../../outputs/laplatine_customer_statement_visual_qa/)

### Décisions finales V1.1

- Période par défaut : **90 derniers jours**, modifiable.
- Factures payées, partielles et ouvertes incluses ; **avoirs exclus**.
- Statuts : Payée, À payer, En retard, partiellement payée (± en retard).
- Bloc synthèse : total facturé, réglé, **montant à régler à La Platine**, **dont en retard**.
- **XLSX = format maître** ; impression ou PDF via le tableur (LibreOffice / Excel).
- PDF natif Odoo : **hors périmètre**.

## Objectif

Permettre à une utilisatrice comptable ou administrative de générer, pour un
partenaire client donné, un **état de facturation** sur une période choisie,
au format **XLSX** :

- lisible sans retraitement Excel ;
- imprimable directement en A4 paysage ;
- aligné sur les données comptables standard Odoo.

Le module ne crée aucune comptabilité parallèle.

## Utilisatrices visées

Ethel et Véréna — génération et contrôle des états de facturation transmis aux
clients.

## Point d'entrée

Depuis la **fiche partenaire client** : bouton **État de facturation**
(droit requis : Facturation / `account.group_account_invoice`).

Le wizard ouvre avec :

- le partenaire prérempli ;
- la période par défaut = **90 derniers jours glissants** (aujourd'hui inclus,
  modifiable).

Exemple si génération le 4 juillet 2026 : du **6 avril 2026** au **4 juillet
2026** (`date_from` = aujourd'hui − 89 jours, `date_to` = aujourd'hui).

## Périmètre V1 (gelé)

### Inclus

- Sélection d'un partenaire client (un seul à la fois).
- Sélection d'une période (début / fin), défaut = 90 derniers jours (date du
  jour incluse).
- Génération d'un fichier `.xlsx` prêt à consulter, imprimer et transmettre.
- **Bloc de synthèse** avant le tableau : total facturé, total réglé,
  montant total à régler à La Platine, dont montant en retard.
- Une ligne par facture client comptabilisée sur la période.
- Colonnes : Facture, Date, Échéance, Montant TTC, Réglé, Solde, Statut.
- Statut enrichi avec la notion de **retard** (échéance vs date de génération).
- Totaux en pied de tableau : facturé, réglé, restant dû.
- Factures **payées**, **partiellement payées** et **non payées**.
- Mise en page A4 paysage (1 page en largeur, hauteur libre).
- En-têtes de tableau répétés à l'impression, footer `Page X / Y`.

### Exclus (V2 ou ultérieur)

- Balance âgée, grand livre partenaire, relevé de compte chronologique.
- Avoirs client (ni lignes, ni déduction dans les totaux).
- Règlements sur lignes séparées, solde progressif.
- PDF natif, envoi e-mail automatique, relances, pénalités.
- Portail client, tableaux de bord, consolidation multi-partenaires.
- Clients codés en dur (EMD, EMI, Saveur Caraïbe, etc.).
- Modification des écritures comptables.

## Règles métier

### Sélection des factures

Domaine appliqué :

```python
[
    ("commercial_partner_id", "=", partner.commercial_partner_id.id),
    ("move_type", "=", "out_invoice"),
    ("state", "=", "posted"),
    ("payment_state", "!=", "reversed"),
    ("invoice_date", ">=", date_from),
    ("invoice_date", "<=", date_to),
]
```

| Règle | Détail |
|-------|--------|
| Partenaire | Entité commerciale — inclut les factures des contacts / adresses enfants |
| Date de sélection | `invoice_date` uniquement (pas date de création ni de règlement) |
| État | Factures comptabilisées ; brouillons et annulées exclus |
| Extournées | Exclues (`payment_state != reversed`) |
| Avoirs | Exclus (`out_refund` non sélectionné) |

### Montants

- **Montant TTC** : `amount_total`
- **Solde** : `amount_residual`
- **Réglé** : `amount_total - amount_residual` (calcul à la volée, non stocké)

### Devise

Une seule devise par génération. Si plusieurs devises sont détectées, Odoo
bloque avec un message explicite.

### Statuts affichés

Date de référence : `fields.Date.context_today(self)` (date de génération).

Une échéance est en retard si `invoice_date_due < date_du_jour`. Une échéance
égale à la date du jour **n'est pas** en retard. Sans date d'échéance : statut
basé sur le paiement uniquement, sans retrait automatique.

| Situation | Libellé rapport |
|-----------|-----------------|
| Facture totalement soldée | Payée |
| Partiellement réglée, échéance non dépassée | Partiellement payée |
| Partiellement réglée, échéance dépassée | Partiellement payée — en retard |
| Non réglée, échéance dépassée | En retard |
| Non réglée, échéance du jour ou future | À payer |
| Paiement en cours | Paiement en cours |

Les statuts « en retard » sont affichés en **texte rouge foncé gras** (sans fond
coloré). Le fond rouge pâle `#FFEBEE` est réservé à la ligne de synthèse
**Dont montant en retard**.

### Bloc de synthèse

Affiché avant le tableau des factures :

| Indicateur | Calcul |
|------------|--------|
| Total facturé | Σ `amount_total` |
| Total réglé | Σ (`amount_total` − `amount_residual`) |
| **Montant total à régler à La Platine** | Σ `amount_residual` |
| Dont montant en retard | Σ `amount_residual` des factures non soldées dont l'échéance est dépassée |

Le montant à régler inclut les échéances futures ; le montant en retard
uniquement les soldes dont l'échéance est antérieure à la date du jour.

### Absence de résultat

Si aucune facture ne correspond : message d'erreur, **pas de fichier vide**.

> Aucune facture comptabilisée n'a été trouvée pour ce partenaire sur la
> période sélectionnée.

### Nom de fichier

Convention : `Etat_facturation_<Partenaire>_<AAAA-MM>.xlsx`

Exemple : `Etat_facturation_EMD_2026-06.xlsx`

## Critères d'acceptation V1

| ID | Critère | Couverture |
|----|---------|------------|
| CA-01 | Fenêtre glissante 90 jours proposée à l'ouverture | Test automatisé |
| CA-02 | Période modifiable avant génération | Wizard |
| CA-03 | Rapport pour le partenaire sélectionné uniquement | Test automatisé |
| CA-04 | Factures payées incluses | Test automatisé |
| CA-05 | Factures ouvertes incluses | Test automatisé |
| CA-06 | Avoirs exclus | Domaine + spec |
| CA-07 | Exactitude des montants par facture | Test automatisé |
| CA-08 | Exactitude des totaux | Test automatisé |
| CA-09 | Fichier `.xlsx` ouvrable | Test automatisé |
| CA-10 | Impression A4 paysage, 1 page en largeur | Recette visuelle ✅ |
| CA-11 | En-têtes répétés sur pages suivantes | Recette visuelle ✅ |
| CA-12 | Impression sans retraitement manuel | Recette visuelle ✅ |
| CA-13 | Statuts avec notion de retard | Tests + recette visuelle ✅ |
| CA-14 | Bloc de synthèse (à régler / en retard) | Tests + recette visuelle ✅ |

## Dépendances

- Module Odoo : `account`
- Python : `xlsxwriter` (déclaré dans `external_dependencies`)
- Indépendant de `laplatine_invoice_payment_info`

## Tests

Tag : `laplatine_customer_statement`

```bash
docker compose exec -T odoo sh -c \
  'odoo --config=/etc/odoo/odoo.conf --database=laplatine_prod \
   --db_host="$HOST" --db_user="$USER" --db_password="$PASSWORD" \
   -u laplatine_customer_statement --test-enable \
   --test-tags /laplatine_customer_statement --stop-after-init \
   --http-port=18019'
```

Résultat attendu : **16 tests, 0 failed, 0 error**.

## Installation (lab ou environnement cible)

1. S'assurer que le dépôt `odoo18-addons-dorevia` est dans `addons_path`.
2. Vérifier que `xlsxwriter` est disponible dans l'image Odoo.
3. Installer ou mettre à jour le module via un **processus Odoo isolé** (serveur
   principal arrêté, sans conflit HTTP sur le port 8069).

**Installation :**

```bash
cd "$LAB"
docker compose stop odoo

docker compose run --rm --no-deps \
  odoo \
  odoo \
  --config=/etc/odoo/odoo.conf \
  --database=laplatine_prod \
  -i laplatine_customer_statement \
  --stop-after-init \
  --no-http

docker compose up -d odoo
```

**Mise à jour :**

```bash
cd "$LAB"
docker compose stop odoo

docker compose run --rm --no-deps \
  odoo \
  odoo \
  --config=/etc/odoo/odoo.conf \
  --database=laplatine_prod \
  -u laplatine_customer_statement \
  --stop-after-init \
  --no-http

docker compose up -d odoo
```

`$LAB` désigne la racine du projet `laplatine-odoo18-lab`.

4. Tester depuis une fiche client : **État de facturation**.

## Historique

### 2026-07-04 — V1 gelée

- Cadrage fonctionnel et spécification V1.
- Développement wizard + générateur XLSX + tests (7 tests).
- Règles métier figées : entité commerciale, devise unique, extournées exclues.
- Recette visuelle interne CA-10 à CA-12 validée.
- Périmètre V1 gelé en attente de recette métier utilisatrices.

### 2026-07-04 — Ajustement post-recette métier

- Période par défaut : fenêtre glissante 90 jours (remplace le mois civil N-1).
- Statuts enrichis avec notion de retard (échéance vs date de génération).
- Bloc de synthèse : montant à régler et montant en retard.
- Version `18.0.1.1.0` — 16 tests automatisés.

### 2026-07-04 — Clôture V1.1

- GO technique, fonctionnel représentatif, visuel et clôture lab.
- Retouche finale : statuts en retard en texte rouge gras (sans fond).
- Version `18.0.1.1.1` commitée et poussée (`b7e40e8`).
- Production : décision séparée sur GO explicite.
