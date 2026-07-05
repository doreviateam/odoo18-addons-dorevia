# Guide de déploiement production — Consommation MP V1

| Élément | Valeur |
|---------|--------|
| **Référence** | `DEPLOY-CONS-MP-V1` |
| **Module** | `laplatine_procurement_control` |
| **Version cible** | `18.0.1.4.0` minimum |
| **Commit de référence lab** | `09d801e` |
| **Prérequis** | Note de clôture V1 signée MOA + **GO déploiement production explicite** |
| **Statut actuel** | **Production STOP** |

---

## 0. Principe

Ce guide couvre le déploiement du lot **Consommation matières premières** (Slices 1–4) inclus dans `laplatine_procurement_control`. Il s'applique à la **production** après validation MOA ; la procédure lab est identique sur `laplatine-odoo18-lab`.

> **Rappel critique** : upgrade module **+ redémarrage Odoo** obligatoire. Réserve documentée : `ENV-CONS-MP-S3-001`.

---

## 1. Pré-checks avant déploiement

| # | Contrôle | OK |
|---|----------|-----|
| 1 | GO MOA déploiement production obtenu et daté | ☐ |
| 2 | Commit `origin/main` ≥ `09d801e` identifié pour la prod | ☐ |
| 3 | Sauvegarde base + filestore production planifiée | ☐ |
| 4 | Fenêtre de maintenance communiquée aux opérateurs | ☐ |
| 5 | Accès admin production disponible | ☐ |

---

## 2. Déploiement technique

Adapter les chemins et noms de service à l'environnement production.

### 2.1 Récupération du code

```bash
cd /chemin/vers/odoo18-addons-dorevia
git fetch origin
git checkout main
git pull origin main
git rev-parse HEAD   # attendu : ≥ 09d801e
```

### 2.2 Upgrade module

**Docker (modèle lab)** :

```bash
cd /chemin/vers/environnement-odoo
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d NOM_BASE_PROD \
  -u laplatine_procurement_control --stop-after-init
```

**Systemd / bare metal** :

```bash
odoo -c /etc/odoo/odoo.conf -d NOM_BASE_PROD \
  -u laplatine_procurement_control --stop-after-init
```

### 2.3 Redémarrage Odoo (obligatoire)

```bash
docker compose restart odoo
# ou : systemctl restart odoo
```

Attendre le démarrage complet (~30–60 s) avant toute recette utilisateur.

### 2.4 Contrôle version chargée

**Interface** : Apps → `La Platine - Pilotage des approvisionnements` → version **18.0.1.4.0**.

**Shell (recommandé)** :

```bash
docker compose run --rm odoo odoo shell -c /etc/odoo/odoo.conf -d NOM_BASE_PROD --no-http <<'PY'
m = env["ir.module.module"].search([("name", "=", "laplatine_procurement_control")], limit=1)
print("installed:", m.installed_version, "state:", m.state)
PY
```

Résultat attendu : `installed: 18.0.1.4.0 state: installed`.

---

## 3. Paramétrage société

Menu : **Paramètres → Sociétés → SARL La Platine** (ou société active).

| Paramètre | Attendu production |
|-----------|-------------------|
| Entrepôt de pilotage approvisionnements | Entrepôt La Platine |
| Emplacement destination consommations | Emplacement **Production** société |

Vérifier sur chaque matière première opérationnelle :

| Paramètre article | Attendu |
|-------------------|---------|
| Suivi consommation La Platine | Coché |
| Stockable | Oui |
| UoM | Catégorie Poids (kg) |

---

## 4. Groupes utilisateurs

Menu : **Paramètres → Utilisateurs → [utilisateur] → Droits d'accès**.

### 4.1 Opérateurs consommation (Véréna, Ethel, Michel)

| Groupe | Obligatoire |
|--------|-------------|
| Utilisateur interne | Oui |
| Inventaire / Utilisateur | Oui (impliqué) |
| **La Platine — Consommation matières premières** | Oui |

**Ne pas** attribuer les groupes cockpit sauf besoin explicite.

### 4.2 Supervision (si applicable)

| Profil | Groupes |
|--------|---------|
| Consultation cockpit | Utilisateur interne + **Pilotage approvisionnements / Consultation** |
| Actualisation cockpit | + **Pilotage approvisionnements / Actualisation** |
| Paramétrage cockpit | + **Pilotage approvisionnements / Paramétrage** |

### 4.3 Matrice de vérification post-attribution

| Utilisateur | Menu La Platine visible | Cockpit visible | Config technique |
|-------------|---------------------------|-----------------|------------------|
| Opérateur MP | ☐ Oui | ☐ Non | ☐ Non |
| Consultant | ☐ Non (sauf double profil) | ☐ Oui | ☐ Configuration only |

---

## 5. Recette de fumée production (15–20 min)

Exécuter **après** upgrade, restart et paramétrage groupes.

### FUM-01 — Navigation opérateur

| Étape | Action | Attendu |
|-------|--------|---------|
| 1 | Connexion opérateur MP | OK |
| 2 | **Inventaire → La Platine → Consommation matière première** | Wizard s'ouvre |
| 3 | Sélectionner une MP éligible (test non fécule si possible) | Emplacement + stock affichés |

### FUM-02 — Consommation (quantité faible)

| Étape | Action | Attendu |
|-------|--------|---------|
| 1 | Saisir qty prélevée > 0, ≤ stock | OK |
| 2 | **Enregistrer la consommation** | Notification succès, wizard fermé |
| 3 | Vérifier stock diminué | Cohérent |
| 4 | Historique mouvements Odoo | Move `done`, réf. `Consommation MP La Platine`, dest. Production |

### FUM-03 — Correction après comptage

| Étape | Action | Attendu |
|-------|--------|---------|
| 1 | Rouvrir wizard, **Mettre à jour la quantité disponible** | Mode correction |
| 2 | Saisir qty comptée + motif | Champs lisibles |
| 3 | **Appliquer la correction** | Dialog confirmation natif Odoo |
| 4 | Confirmer | Notification récap. avant/après/écart |
| 5 | Historique | Move inventaire `done`, motif = texte saisi |

### FUM-04 — Contrôles bloquants (sans impact stock si annulé)

| Test | Attendu |
|------|---------|
| Qty négative | Refus |
| Motif vide | Refus |
| Qty > stock (consommation) | Refus |

### FUM-05 — Cockpit non-régression (consultant)

| Étape | Attendu |
|-------|---------|
| **Inventaire → Configuration → Pilotage approvisionnements → Cockpit** | Accessible consultant |
| Ligne fécule (si présente) | Données cohérentes, pas d'erreur bloquante |

### FUM-06 — Seuil min (optionnel)

Si une MP est proche du seuil min : vérifier notification **Seuil de réapprovisionnement atteint** après opération, sans commande auto.

---

## 6. Rollback

En cas d'échec fumée ou incident :

1. **Ne pas** laisser les opérateurs sur la nouvelle version ;
2. Restaurer sauvegarde base + filestore prise avant déploiement ;
3. Redémarrer Odoo ;
4. Documenter l'incident et reprendre depuis §1.

Downgrade module seul **non recommandé** — préférer restauration backup.

---

## 7. Go-live opérationnel

| # | Action | Responsable | OK |
|---|--------|-------------|-----|
| 1 | Fumée production verte | QA / MOA | ☐ |
| 2 | Groupes opérateurs validés | Admin | ☐ |
| 3 | Communication équipe (wizard disponible) | MOA | ☐ |
| 4 | Production **GO** formalisé par écrit | MOA | ☐ |

---

## 8. Références

| Document | Lien |
|----------|------|
| Note de clôture V1 | [`NOTE_CLOTURE_V1_CONSOMMATION_MP.md`](NOTE_CLOTURE_V1_CONSOMMATION_MP.md) |
| Cadrage lot | [`docs/cadrage/NOTE_CADRAGE_CONSOMMATION_MP_LAPLATINE_V1.md`](../docs/cadrage/NOTE_CADRAGE_CONSOMMATION_MP_LAPLATINE_V1.md) |
| Preuves QA lab | [`recette_qa/README.md`](recette_qa/README.md) |
| Procédure lab | [`recette_qa/README.md`](recette_qa/README.md) § Procédure |

---

## 9. Journal de déploiement (à compléter)

| Champ | Valeur |
|-------|--------|
| Date déploiement | |
| Exécutant | |
| Base production | |
| Commit déployé | |
| Version module constatée | |
| Restart Odoo | ☐ Oui |
| Fumée | ☐ GO / ☐ NO_GO |
| Décision MOA production | ☐ STOP / ☐ GO |
