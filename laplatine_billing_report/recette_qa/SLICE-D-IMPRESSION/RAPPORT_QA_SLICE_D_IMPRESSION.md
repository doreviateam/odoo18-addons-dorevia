# Rapport QA - Slice D impression XLSX

| Élément | Valeur |
|---|---|
| Référence | `LP-FACT-REPORT-001` |
| Module | `laplatine_billing_report` |
| Run QA | `SLICE-D-IMPRESSION` |
| Date | 2026-07-06 |
| Lab | `http://127.0.0.1:18018` / base `laplatine_prod` |
| Commit | `309253a` |
| Version installée | `18.0.1.0.0` |
| Production | **STOP - aucun déploiement production** |

## Verdict

**NO_GO_RECETTE_SLICE_D_IMPRESSION**

La majorité du rendu impression est conforme, mais la ligne de synthèse **Nombre de documents** est tronquée dans le rendu LibreOffice/PDF sur les pages de totaux. Ce défaut impacte R06 et bloque le GO recette visuelle Slice D.

Le smoke Slice E est **OK** en annexe.

## Jeu Principal

| Élément | Valeur |
|---|---|
| Fichier | `Rapport_facturation_La_Platine_2026-06-01_2026-06-30.xlsx` |
| Période | 2026-06-01 -> 2026-06-30 |
| Ventes | 44 documents |
| Achats | 47 documents |
| PDF LibreOffice | 4 pages, A4 paysage |

Le mois M-1 n'avait aucun avoir en lab. Pour tester R05, une annexe avoirs a été générée sur février 2026.

## Grille R01-R13

| # | Critère | Ventes | Achats | Résultat |
|---|---|---|---|---|
| R01 | Fichier `.xlsx` ouvert / converti LibreOffice sans erreur bloquante | OK | OK | OK |
| R02 | Titre, société, période et date visibles | OK | OK | OK |
| R03 | En-têtes ligne 6, ordre MOA | OK | OK | OK |
| R04 | Aucune colonne `###` sur les montants | OK | OK | OK |
| R05 | Montants négatifs lisibles | N/A juin | OK annexe avoirs | OK |
| R06 | Ligne **Nombre de documents** et totaux en bas | KO libellé tronqué | KO libellé tronqué | **KO** |
| R07 | Aperçu A4 paysage | OK | OK | OK |
| R08 | Largeur = 1 page | OK | OK | OK |
| R09 | Lignes 1 à 6 répétées | OK | OK | OK |
| R10 | Totaux visibles dernière page | OK | OK | OK |
| R11 | Pied de page `Page X / Y` centré | OK | OK | OK |
| R12 | Volets figés sous en-tête | OK | OK | OK |
| R13 | Nom fichier attendu | OK | - | OK |

## Anomalies

### BUG-FACT-REPORT-D-001 - Libellé `Nombre de documents` tronqué à l'impression

| Champ | Valeur |
|---|---|
| Sévérité | Bloquante recette visuelle |
| Classification | Anomalie logicielle / présentation XLSX |
| Étapes | Générer le rapport, convertir/ouvrir en aperçu impression LibreOffice |
| Attendu | Ligne de synthèse lisible : `Nombre de documents` + compteur + totaux |
| Obtenu | Le libellé est tronqué visuellement en `e documents` sur Ventes/Achats, y compris export vide |
| Preuves | `png/slice_d_print-2.png`, `png/slice_d_print-4.png`, `png/slice_d_avoirs-4.png`, `png/smoke_e_empty-1.png` |
| Hypothèse | Colonne A trop étroite pour le libellé de synthèse; la valeur existe dans le XLSX mais n'est pas lisible au rendu |
| Suggestion QA | Élargir ou fusionner la zone de libellé de la ligne de synthèse, puis reconvertir PDF |

## Smoke Slice E

| Contrôle | Résultat | Preuve |
|---|---|---|
| Profil Facturation : menu visible | OK | `smoke_slice_e_evidence.json` |
| Profil Facturation : export OK | OK | `Rapport_facturation_La_Platine_2099-12-01_2099-12-31_SMOKE_E_VIDE.xlsx` |
| Profil sans Facturation : menu absent | OK | `smoke_slice_e_evidence.json` |
| Profil sans Facturation : création wizard refusée | OK | `smoke_slice_e_evidence.json` |
| Période vide : fichier ouvrable, message visible | OK | `png/smoke_e_empty-1.png`, `png/smoke_e_empty-2.png` |

## Preuves

| Type | Fichier |
|---|---|
| XLSX principal | `Rapport_facturation_La_Platine_2026-06-01_2026-06-30.xlsx` |
| PDF principal | `pdf/Rapport_facturation_La_Platine_2026-06-01_2026-06-30.pdf` |
| PNG principal | `png/slice_d_print-1.png` à `png/slice_d_print-4.png` |
| XLSX annexe avoirs | `Rapport_facturation_La_Platine_2026-02-01_2026-02-28_ANNEXE_AVOIRS.xlsx` |
| PDF annexe avoirs | `pdf/Rapport_facturation_La_Platine_2026-02-01_2026-02-28_ANNEXE_AVOIRS.pdf` |
| PNG annexe avoirs | `png/slice_d_avoirs-1.png` à `png/slice_d_avoirs-4.png` |
| Smoke E période vide | `Rapport_facturation_La_Platine_2099-12-01_2099-12-31_SMOKE_E_VIDE.xlsx` |
| PDF période vide | `pdf/Rapport_facturation_La_Platine_2099-12-01_2099-12-31_SMOKE_E_VIDE.pdf` |
| JSON génération | `generation_evidence.json`, `generation_evidence_annexe_avoirs_2026-02.json` |
| JSON smoke E | `smoke_slice_e_evidence.json` |

## Réserves

- Ouverture validée avec LibreOffice headless. Excel desktop natif n'est pas disponible dans cet environnement QA.
- LibreOffice signale des warnings de cache fontconfig non bloquants; les PDF sont générés et lisibles.
- Le script officiel `scripts/generate_sample_report_slice_d.py` ne peut pas écrire directement depuis le conteneur dans ce lab car le montage `/mnt/extra-addons` est en lecture seule. Le QA a généré dans `/tmp` puis copié les artefacts.

## Conclusion

Slice D reste bloquée en recette visuelle à cause de `BUG-FACT-REPORT-D-001`. Slice E reste techniquement OK au smoke. Le verdict global de clôture lab reste **bloqué** jusqu'à correction du libellé de synthèse imprimé, reconversion PDF et validation MOA.
