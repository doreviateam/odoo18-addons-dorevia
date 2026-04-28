# laplatine_invoice_payment_info

Module Odoo 18 CE spécifique à la SARL La Platine.

## Objectif

Permettre à l’utilisateur de sélectionner un mode de paiement lisible métier lors de l’enregistrement d’un règlement, puis afficher cette information sur la facture PDF une fois la facture payée.

Exemple attendu sur le PDF :

> Payé le 23/04/2026 par Carte bancaire

Le module ne modifie pas la logique comptable standard d’Odoo.  
Le journal comptable reste utilisé pour la comptabilité ; l’information sélectionnée sert uniquement à l’affichage client sur la facture.

## Composants ajoutés

- Un champ « Info facture » sur le wizard d’enregistrement de paiement (voir ci‑dessous selon le journal).
- Un champ de stockage du mode sur `account.payment`, recopié sur le paiement créé.
- Une adaptation du rapport PDF de facture pour afficher la mention de paiement lorsque la facture est payée.
- Une surcharge du layout PDF pour agrandir le logo société sur les factures imprimées.

### Distinction de la sélection selon le journal

Le wizard utilise **deux listes déroulantes** techniques ; **une seule** est affichée à la fois, selon que le journal sélectionné est traité comme **caisse** ou non :

| Journal « comme caisse » | Liste « Info facture » affichée |
|--------------------------|----------------------------------|
| Oui | **Uniquement Espèces** |
| Non | **Carte bancaire**, **Virement**, **Chèque**, **Autre** (sans Espèces) |

Un journal est considéré comme **caisse** pour ce module si :

- son **type** Odoo est **Caisse** (`cash`), **ou**
- son **nom** ou son **code** évoque les espèces (après normalisation : accents, apostrophes, etc.), pour les dossiers où une caisse est modélisée autrement qu’en journal standard « caisse ».

Quand l’utilisateur change de journal dans le wizard, une valeur « Info facture » qui ne serait plus permise est **effacée** ; à l’enregistrement du paiement, une combinaison incohérente est **refusée** avec un message d’erreur.

## Modes de paiement prévus en V1

- Espèces
- Carte bancaire
- Virement
- Chèque
- Autre

## Hors périmètre V1

- Gestion avancée des paiements multiples.
- Modification des journaux comptables.
- Modification de la logique de lettrage ou de rapprochement bancaire.
- Gestion spécifique des moyens de paiement par client.
- Personnalisation multi-société avancée.

## Critères d’acceptation

1. Depuis une facture client, l’utilisateur clique sur “Enregistrer un paiement”.
2. Le wizard affiche le champ “Info facture”.
3. Le paiement créé conserve l’information sélectionnée.
4. Une fois la facture payée, le PDF affiche une mention du type :  
   `Payé le JJ/MM/AAAA par <mode de paiement>`
5. Si aucun mode de paiement n’a été renseigné, aucune mention incorrecte ne doit être affichée.
6. Le PDF de facture affiche le logo société dans une taille plus visible que le rendu standard Odoo.

## Tests

Le module embarque des tests dans `tests/` (tag `laplatine_invoice_payment_info`) : règles « journal caisse / Info facture », contraintes sur `account.payment`, et injection depuis le wizard.

**Port HTTP** : un second processus Odoo (`odoo -c … --test-enable`) écoute aussi sur le port HTTP par défaut (**8069**). Si une instance tourne déjà (Docker, service local), la commande échoue avec *Address already in use*. Utiliser un port libre explicite, par exemple `--http-port=8079` ou `--http-port=8179`.

Exemple (mise à jour + exécution des tests du module) :

```bash
odoo -d <base> -c <odoo.conf> --addons-path=... --http-port=8079 \
  --test-enable --stop-after-init -u laplatine_invoice_payment_info \
  --test-tags /laplatine_invoice_payment_info
```

## Compatibilité

- Odoo 18 Community Edition
- Projet La Platine

Le répertoire parent du module doit figurer dans `addons_path` (voir `../odoo.conf.example` à la racine de `odoo18-addons-dorevia`).
