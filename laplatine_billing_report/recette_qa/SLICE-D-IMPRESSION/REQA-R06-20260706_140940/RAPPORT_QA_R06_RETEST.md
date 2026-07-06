# Rapport re-QA R06 - BUG-FACT-REPORT-D-001

## Verdict

**GO_R06**

Le correctif de presentation est valide sur le perimetre cible R06. Le libelle **Nombre de documents** est entierement lisible dans le rendu LibreOffice/PDF sur les deux onglets, pour le jeu juin 2026 et pour l'export vide.

BUG-FACT-REPORT-D-001 est cloturable cote QA.

## Contexte

| Element | Valeur |
|---|---|
| Reference | REQA-R06-20260706_140940 |
| Date de controle | 06/07/2026 |
| Lab | http://127.0.0.1:18018 |
| Base | laplatine_prod |
| Commit de reference | 309253a |
| Etat code | Correctif local non commite |
| Production | STOP |

## Perimetre

Controle cible R06 uniquement, conformement a la demande :

| Controle | Resultat |
|---|---|
| Libelle `Nombre de documents` entierement lisible sur Ventes | OK |
| Libelle `Nombre de documents` entierement lisible sur Achats | OK |
| Compteurs inchanges | OK |
| Totaux inchanges | OK |
| Reconversion LibreOffice du jeu juin 2026 | OK |
| Reconversion LibreOffice de l'export vide | OK |

R01-R05 et R07-R13 n'ont pas ete rejoues integralement. Aucune regression visible n'a ete constatee pendant le controle cible.

## Resultats detailles

| Export | Onglet | Page PDF | Libelle | Compteur | Totaux |
|---|---:|---:|---|---:|---|
| Juin 2026 | Ventes | 2/4 | OK lisible | 44 | Inchangés |
| Juin 2026 | Achats | 4/4 | OK lisible | 47 | Inchangés |
| Vide 2099-12 | Ventes | 1/2 | OK lisible | 0 | 0,00 EUR |
| Vide 2099-12 | Achats | 2/2 | OK lisible | 0 | 0,00 EUR |

Valeurs controlees via openpyxl :

| Export | Onglet | HT | TVA | TTC | Regle / solde | Reste / solde |
|---|---|---:|---:|---:|---:|---:|
| Juin 2026 | Ventes | 33 695,23 | 701,60 | 34 396,83 | 4 313,99 | 30 082,84 |
| Juin 2026 | Achats | 23 701,24 | 836,87 | 24 538,11 | 18 890,23 | 5 647,88 |
| Vide 2099-12 | Ventes | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| Vide 2099-12 | Achats | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |

Comparaison avec la passe QA initiale :

| Controle | Resultat |
|---|---|
| Compteurs et totaux juin 2026 identiques | OK |
| Compteurs et totaux export vide identiques | OK |
| Largeur colonne A avant correctif | 10,7109375 |
| Largeur colonne A apres correctif | 22,7109375 |

## Preuves

| Fichier | Role |
|---|---|
| `REQA_R06_Rapport_facturation_La_Platine_2026-06-01_2026-06-30.xlsx` | Export juin regenere |
| `REQA_R06_Rapport_facturation_La_Platine_2099-12-01_2099-12-31_EMPTY.xlsx` | Export vide regenere |
| `pdf/REQA_R06_Rapport_facturation_La_Platine_2026-06-01_2026-06-30.pdf` | PDF LibreOffice juin |
| `pdf/REQA_R06_Rapport_facturation_La_Platine_2099-12-01_2099-12-31_EMPTY.pdf` | PDF LibreOffice vide |
| `png/reqa_r06_june-2.png` | Preuve Ventes juin, ligne R06 |
| `png/reqa_r06_june-4.png` | Preuve Achats juin, ligne R06 |
| `png/reqa_r06_empty-1.png` | Preuve Ventes vide, ligne R06 |
| `png/reqa_r06_empty-2.png` | Preuve Achats vide, ligne R06 |
| `reqa_r06_inspection.json` | Inspection openpyxl et comparaison initiale |

## Notes d'execution

La conversion LibreOffice a reussi pour les deux fichiers. Les avertissements Fontconfig sur les repertoires de cache non accessibles sont non bloquants et n'empechent pas la production des PDF.

Les avertissements Odoo `laplatine.procurement.control.line` observes au lancement du shell sont hors perimetre facturation et n'ont pas d'impact sur l'export controle.

Aucun commit, push ou deploiement production n'a ete effectue.
