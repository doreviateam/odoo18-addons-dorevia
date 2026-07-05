# Rapport MOA UI — Recentrage cockpit CONS-MP-003

| Élément | Valeur |
|---|---|
| Référence | `LAPLATINE-CONS-MP-003` |
| Run | `QA-CONS-MP-MOA-UI-003-20260705_220400` |
| Date | 2026-07-05 |
| Profil manager | `qa_cockpit_scope_manager_20260705` |
| Profil opérateur | `qa_cockpit_scope_operator_20260705` |
| Base | `laplatine_prod` |
| URL lab | `http://127.0.0.1:18018` |
| Module | `laplatine_procurement_control` `18.0.1.6.0` |
| Commit code | `6046175` |
| Commit QA | `cee366d` |
| Production | **STOP** |

## Verdict

**GO_MOA_UI_CONS_MP_003**

Le cockpit est accessible, son intitulé est compréhensible pour un responsable approvisionnements, et le périmètre affiché correspond strictement aux articles marqués « Suivi consommation La Platine ». Aucun impact sur le stock fécule.

## Navigation et compréhension

| Contrôle | Résultat | Observation |
|---|---|---|
| Chemin menu | OK | `Inventaire → Configuration → Pilotage approvisionnements → Cockpit` |
| Intitulé écran | OK | **Pilotage approvisionnements** — bouton **Actualiser** visible |
| Compréhension MOA | OK | Vue synthétique des matières suivies par La Platine |

Captures : `screenshots/02_cockpit_menu_navigation.png`, `screenshots/08_cockpit_overview_tracked_products.png`

## Périmètre visible (articles A / B / C + fécule)

| Article | Attendu | Résultat | Preuve |
|---|---|---|---|
| Fécule de manioc | Visible | OK | `03_cockpit_fecule_search.png` |
| Article A — suivi + paramétré | Visible | OK | `04_cockpit_article_a.png` |
| Article B — non suivi + paramétré | Absent | OK | `05_cockpit_article_b_search_empty.png` (liste vide, filtre seul) |
| Article C — suivi incomplet | Visible + alertes | OK | `06_cockpit_article_c_list.png`, `07_cockpit_article_c_alerts_form.png` |

## Fécule

| Donnée | Attendu | Observé UI |
|---|---|---|
| Stock disponible | 13 500 kg | **13 500,00** |
| Stock minimum | 5 000 kg | **5 000,00** (fiche cockpit) |
| Fournisseur | Kastell | **KASTELL NEGOCE SAS** |

| Mesure | Valeur |
|---|---|
| Stock avant passe | 13 500 kg |
| Stock après passe | **13 500 kg** |
| Impact | **Aucun** |

Capture fiche : `screenshots/03b_cockpit_fecule_form.png`

> Réserve connue : stock lab à 13 500 kg (historique recette 13 000 kg). Critère MOA respecté : **inchangé durant la passe**.

## Article C — lisibilité des alertes

Alertes visibles et compréhensibles dans l’interface :

- Règle de réapprovisionnement absente ou incomplète
- Fournisseur ou délai manquant
- Historique insuffisant

Capture : `screenshots/07_cockpit_article_c_alerts_form.png`

## Sécurité opérateur

| Contrôle | Résultat | Observation |
|---|---|---|
| Menus La Platine (×2) | OK | Consommation + Mise à jour stock |
| Menu cockpit | OK | Absent sous Configuration |
| Accès direct action cockpit | OK | Refus / écran hors périmètre |
| Wizards ouvrables | OK | Actions 659 / 660 accessibles |

Captures : `10_operator_la_platine_menus.png`, `11_operator_no_cockpit_menu.png`, `12_operator_cockpit_direct_denied.png`, `13_operator_wizards_accessible.png`

## Grille MOA UI (12/12)

| ID | Intitulé | Résultat |
|---|---|---|
| MOA-UI-01 | Navigation cockpit accessible | OK |
| MOA-UI-02 | Intitulé compréhensible | OK |
| MOA-UI-03 | Fécule visible | OK |
| MOA-UI-04 | Fécule : 13 500 / 5 000 / Kastell | OK |
| MOA-UI-05 | Article A visible | OK |
| MOA-UI-06 | Article B absent (recherche) | OK |
| MOA-UI-07 | Article C visible | OK |
| MOA-UI-08 | Article C : alertes lisibles | OK |
| MOA-UI-09 | Opérateur : wizards accessibles | OK |
| MOA-UI-10 | Opérateur : pas de menu cockpit | OK |
| MOA-UI-11 | Opérateur : accès cockpit refusé | OK |
| MOA-UI-12 | Opérateur : wizards ouvrables | OK |

## Preuves

| Fichier | Description |
|---|---|
| `moa_ui_cons_mp_003_evidence.json` | Synthèse automatisée Playwright |
| `screenshots/02_cockpit_menu_navigation.png` | Menu d’accès cockpit |
| `screenshots/03_cockpit_fecule_search.png` | Fécule dans la liste |
| `screenshots/03b_cockpit_fecule_form.png` | Fiche fécule (stock / min / fournisseur) |
| `screenshots/05_cockpit_article_b_search_empty.png` | Recherche Article B sans ligne |
| `screenshots/07_cockpit_article_c_alerts_form.png` | Article C avec alertes |
| `screenshots/08_cockpit_overview_tracked_products.png` | Vue générale articles suivis |
| `screenshots/10_operator_la_platine_menus.png` | Profil opérateur — wizards |
| `screenshots/11_operator_no_cockpit_menu.png` | Profil opérateur — pas de cockpit |

## Conclusion

Passe MOA UI **GO** sur le lab pour CONS-MP-003. Le recentrage du cockpit sur le booléen **Suivi consommation La Platine** est validé côté interface responsable et opérateur.

**Production : STOP** — déploiement production soumis à décision MOA explicite.
