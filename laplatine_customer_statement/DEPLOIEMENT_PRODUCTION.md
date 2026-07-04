# Procédure de déploiement production — `laplatine_customer_statement`

**Version module cible** : `18.0.1.1.1` (V1.1)  
**Commit Git de référence** : `62546160532a2307dc7494a0b4cacb19f1532103`  
**Dépôt** : [doreviateam/odoo18-addons-dorevia](https://github.com/doreviateam/odoo18-addons-dorevia) — branche `main`  
**Commit production actuel** : `c06a386d883f4e1c2ccfed94cce0721a3cfd1609`  
**Commit déployé en production** : `4ba7befb8c1cb00d34b271b9081ad87dccd585ed`  
**Date de rédaction** : 2026-07-04  
**Dernière révision** : 2026-07-05 — déploiement exécuté, GO production fonctionnel MOA

---

## Statut production — V1.1 en service

| Élément | Statut |
|---------|--------|
| Clôture documentaire lab | ✅ |
| Pré-vol infrastructure prod | ✅ |
| Déploiement exécuté (2026-07-04) | ✅ — stratégie A |
| Module en production | `18.0.1.1.1` — `installed` |
| GO production fonctionnel MOA | ✅ — 2026-07-05 |
| Confirmation usage Ethel / Véréna | Ultérieure — non bloquante |
| Chantier logo PDF | Reporté — GO MOA séparé |

> Cette procédure documente l'intervention réalisée. Toute **nouvelle** intervention (mise à jour module, rollback, autre environnement) requiert un GO MOA explicite.

---

## ⚠️ Archive — contexte pré-déploiement

**Aucun déploiement ne doit être exécuté sans GO explicite de la MOA** (Maîtrise d'ouvrage — décision métier La Platine).

**Aucun déploiement supplémentaire** ne doit être exécuté sans GO explicite de la MOA.

Cette procédure a servi au déploiement du 2026-07-04. Elle reste la référence pour rollback ou réplication.

| Élément | Statut (historique pré-déploiement) |
|---------|--------|
| Stratégie de livraison | ✅ **Option A retenue** |
| Commit module cible | `6254616` / procédure `4ba7bef` |
| Procédure préparatoire | ✅ **GO — validée** |
| Déploiement production (avant exécution) | **STOP — en attente GO MOA d'exécution** |

---

## 1. Objectif

Installer ou mettre à jour **uniquement** le module `laplatine_customer_statement` sur l'environnement Odoo 18 CE de production La Platine, sans modifier les autres modules ni le périmètre fonctionnel V1.1.

**Hors périmètre** : évolutions V2, PDF natif Odoo, mise à jour `laplatine_invoice_payment_info`, évolution taille logo PDF (chantier séparé).

### 1.1 Stratégie de livraison retenue — option A

Analyse Git entre `c06a386` (production actuelle) et `6254616` (cible) :

- **Ajout principal** : module `laplatine_customer_statement` + documentation.
- **Effet de bord sur disque** : `laplatine_invoice_payment_info/views/report_layout.xml` (taille logos PDF, commit `76dca4d`) — **sans impact base** tant qu'aucune mise à jour de ce module n'est lancée.

**Décision retenue** :

1. Checkout détaché sur `62546160532a2307dc7494a0b4cacb19f1532103`.
2. Installation **uniquement** : `-i laplatine_customer_statement`.
3. **Interdit** : `-u laplatine_invoice_payment_info`, `-u all`, ou toute mise à jour globale.
4. Le fichier XML logo présent sur disque après checkout **n'est pas chargé en base** — à consigner au journal d'intervention.
5. L'évolution de taille du logo sera traitée dans un **chantier séparé**, sur GO MOA dédié.

---

## 2. Prérequis

### 2.1 Environnement

| Prérequis | Détail |
|-----------|--------|
| Odoo | 18.0 Community Edition (même branche / image que la production actuelle) |
| Base PostgreSQL | Base de production La Platine (ex. `laplatine_prod` — **à confirmer sur site**) |
| Module `account` | Déjà installé en production (requis par `depends`) |
| `addons_path` | Doit inclure le répertoire contenant `odoo18-addons-dorevia` |
| Accès opérateur | SSH / accès hôte, droits Docker ou service systemd selon l'infra prod |
| Fenêtre d'intervention | Plage validée MOA + utilisateurs prévenus — **indisponibilité Odoo pendant toute la séquence §4 à §7** |

### 2.2 Variables d'environnement (à adapter)

```bash
export PROD_ROOT="/opt/laplatine"
export DB_NAME="laplatine_prod"
export DB_SERVICE="db_prod"
export DB_USER="odoo_prod"
export ODOO_SERVICE="odoo_prod"
export PROD_URL="https://prod.sarl-la-platine.fr"
export BACKUP_DIR="/opt/laplatine/backups/$(date +%Y%m%d_%H%M%S)_pre_laplatine_customer_statement"
export DOREVIA_REPO="/opt/laplatine/addons/odoo18-addons-dorevia"
export FILESTORE_SRC="/opt/laplatine/data/filestore_prod"
export TARGET_COMMIT="62546160532a2307dc7494a0b4cacb19f1532103"
export PROD_COMMIT_BEFORE="c06a386d883f4e1c2ccfed94cce0721a3cfd1609"
export MODULE="laplatine_customer_statement"
export MODULE_VERSION="18.0.1.1.1"
```

### 2.3 Checklist pré-vol (avant toute action)

- [ ] **GO MOA d'exécution obtenu et archivé** (distinct du GO stratégie technique)
- [ ] Fenêtre d'intervention validée (indisponibilité Odoo acceptée)
- [ ] Espace disque suffisant pour sauvegarde PG + filestore
- [ ] Accès GitHub / clone du dépôt Dorevia opérationnel
- [ ] `xlsxwriter` vérifié (§3)
- [ ] Connexion DB du processus isolé vérifiée (§7) — **obligatoire avant `-i` / `-u`**
- [ ] Procédure de rollback lue et comprise par l'opérateur
- [ ] Contact MOA / métier disponible pour la recette post-installation

---

## 3. Vérification de `xlsxwriter` (pré-vol)

Le module déclare `xlsxwriter` en dépendance Python externe (`external_dependencies` dans `__manifest__.py`). **L'installation échouera** si la bibliothèque est absente de l'image ou du conteneur Odoo.

> Effectuer **avant** l'arrêt d'Odoo (§4), tant que le service est encore accessible.

### 3.1 Contrôle dans le conteneur Odoo

```bash
cd "$PROD_ROOT"

docker compose exec -T "$ODOO_SERVICE" python3 -c \
  "import xlsxwriter; print('xlsxwriter OK — version', xlsxwriter.__version__)"
```

**Résultat attendu** : message `xlsxwriter OK — version X.Y.Z` (sur le lab : `3.1.9`).

> Si Odoo est déjà arrêté, utiliser `docker compose run --rm --no-deps "$ODOO_SERVICE" python3 -c "import xlsxwriter; ..."`.

### 3.2 Si la bibliothèque est absente

**Option A — Image Docker (recommandée, persistante)** : ajouter dans le `Dockerfile` de production :

```dockerfile
RUN python3 -m pip install --no-cache-dir --break-system-packages xlsxwriter
```

Puis reconstruire l'image **avant** l'intervention :

```bash
cd "$PROD_ROOT"
docker compose build "$ODOO_SERVICE"
```

**Option B — Conteneur existant (dépannage ponctuel, non recommandé en prod durable)** :

```bash
docker compose exec -u root "$ODOO_SERVICE" \
  python3 -m pip install --no-cache-dir --break-system-packages xlsxwriter
```

> **Important** : l'option B est perdue au prochain rebuild d'image. Préférer l'option A pour la production.

### 3.3 Critère de passage

- [ ] `import xlsxwriter` réussi dans le conteneur qui exécutera `-i` / `-u`
- [ ] Si modification Dockerfile : image rebuildée et tag prod documenté

---

## 4. Séquence d'intervention — arrêt Odoo puis sauvegardes

**Règle impérative** : arrêter Odoo **avant** toute sauvegarde. Le service reste arrêté jusqu'à la fin de l'installation (§8), puis seul le redémarrage final le remet en ligne.

Cela garantit que le dump PostgreSQL et le filestore correspondent **exactement au même instant**, sans risque de pièce jointe créée entre les deux opérations.

```bash
cd "$PROD_ROOT"

# 1. Arrêt Odoo — début de la fenêtre d'indisponibilité
docker compose stop "$ODOO_SERVICE"

# 2. Sauvegarde PostgreSQL        (§5)
# 3. Sauvegarde filestore          (§6)
# 4. Récupération du code          (§6)
# 5. Test connexion DB             (§7)
# 6. Installation ciblée           (§8)

# 7. Redémarrage Odoo — fin de la fenêtre d'indisponibilité
docker compose up -d "$ODOO_SERVICE"
```

> **Ne jamais** lancer `-i` / `-u` via `docker compose exec` sur un conteneur Odoo déjà actif (conflit port HTTP 8069). Utiliser un **processus Odoo isolé** (`docker compose run`) pendant que le service principal reste arrêté.

---

## 5. Sauvegarde PostgreSQL

**Prérequis** : Odoo arrêté (§4).

```bash
mkdir -p "$BACKUP_DIR"

cd "$PROD_ROOT"

docker compose exec -T "$DB_SERVICE" pg_dump \
  -U "$DB_USER" \
  -Fc \
  --no-owner \
  --no-acl \
  "$DB_NAME" \
  > "$BACKUP_DIR/${DB_NAME}.dump"
```

### 5.1 Vérifications

```bash
# Taille non nulle
ls -lh "$BACKUP_DIR/${DB_NAME}.dump"

# Intégrité du dump (via conteneur DB — pas de pg_restore requis sur l'hôte)
cat "$BACKUP_DIR/${DB_NAME}.dump" | \
  docker compose exec -T "$DB_SERVICE" pg_restore --list - | \
  head -20
```

**Critères de passage** :

- [ ] Fichier `.dump` présent, taille cohérente avec la base
- [ ] `pg_restore --list` sans erreur fatale
- [ ] Chemin `$BACKUP_DIR` consigné dans le journal d'intervention

---

## 6. Sauvegarde filestore et récupération du code

**Prérequis** : Odoo arrêté (§4), sauvegarde PostgreSQL terminée (§5).

### 6.1 Sauvegarde filestore

```bash
tar -czf "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz" \
  -C "$(dirname "$FILESTORE_SRC")" "$(basename "$FILESTORE_SRC")"
```

#### Vérifications

```bash
tar -tzf "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz" | head -10
ls -lh "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz"
```

**Critères de passage** :

- [ ] Archive tar.gz créée
- [ ] Contenu listable (`filestore/...` ou structure équivalente Odoo 18)
- [ ] Horodatage aligné avec la sauvegarde PostgreSQL (même fenêtre, Odoo arrêté)

### 6.2 Récupération du commit `6254616` (checkout détaché — stratégie A)

La production doit exécuter un **commit précis**, pas suivre automatiquement `main`. Utiliser un checkout **détaché** après contrôle d'un working tree propre.

#### Clone initial (si le dépôt n'existe pas encore en prod)

```bash
git clone https://github.com/doreviateam/odoo18-addons-dorevia.git "$DOREVIA_REPO"
cd "$DOREVIA_REPO"
git fetch origin main
git checkout --detach "$TARGET_COMMIT"
```

#### Mise à jour d'un clone existant

```bash
cd "$DOREVIA_REPO"

if [ -n "$(git status --porcelain)" ]; then
  echo "STOP : le dépôt contient des modifications locales."
  git status --short
  exit 1
fi

git fetch origin main
git checkout --detach "$TARGET_COMMIT"

test "$(git rev-parse HEAD)" = "$TARGET_COMMIT" \
  || { echo "STOP : commit inattendu"; exit 1; }
```

**Résultat attendu** :

```
62546160532a2307dc7494a0b4cacb19f1532103
```

#### Vérifications du code déployé

```bash
test -f "$DOREVIA_REPO/laplatine_customer_statement/__manifest__.py"
grep '"version"' "$DOREVIA_REPO/laplatine_customer_statement/__manifest__.py"
```

**Résultat attendu** : `"version": "18.0.1.1.1"`

#### Verrou de référence (recommandé)

Sur le lab, le commit est figé dans `addons-lock.tsv`. En production, consigner le hash dans le journal d'intervention ou reproduire le mécanisme de lock lors du lot « versioning lab ».

**Critères de passage** :

- [ ] Working tree Git propre avant checkout
- [ ] HEAD = `62546160532a2307dc7494a0b4cacb19f1532103` (mode détaché)
- [ ] Version manifest = `18.0.1.1.1`
- [ ] Répertoire visible dans `addons_path` (montage volume — pas de redémarrage requis pour le chemin seul)
- [ ] **Écart disque connu** : `laplatine_invoice_payment_info/views/report_layout.xml` diffère de la base — **ne pas `-u` ce module**

---

## 7. Test préalable de connexion DB (obligatoire)

**Prérequis** : Odoo arrêté, code au commit cible, sauvegardes terminées.

Avant toute installation du module, vérifier que le processus Odoo isolé se connecte correctement à PostgreSQL. Ce contrôle évite le problème rencontré en lab (`database: default@default:default`).

```bash
cd "$PROD_ROOT"

docker compose run --rm --no-deps \
  "$ODOO_SERVICE" \
  odoo \
  --config=/etc/odoo/odoo.conf \
  --database="$DB_NAME" \
  --stop-after-init \
  --no-http
```

### 7.1 Critères de passage

- [ ] Code de sortie `0`
- [ ] Aucune traceback Python
- [ ] Dans les logs, la connexion ressemble à :

  ```text
  database: <utilisateur>@<service-db>:5432
  ```

  et **non** à :

  ```text
  database: default@default:default
  ```

> **Adapter si nécessaire** : variables `HOST` / `USER` / `PASSWORD` dans `compose.yml` (section `environment` du service `odoo`). Sur le lab, elles sont injectées automatiquement ; en production, vérifier qu'elles sont bien présentes pour `docker compose run`.

**En cas d'échec** : ne pas poursuivre. Corriger la configuration DB, ou exécuter le rollback si une modification partielle a eu lieu.

---

## 8. Installation ciblée du module (stratégie A)

**Prérequis** : test connexion DB réussi (§7).

**Production La Platine** : première installation — le module est absent de la base.

### 8.1 Commande autorisée — `-i` uniquement

```bash
cd "$PROD_ROOT"

docker compose run --rm --no-deps \
  "$ODOO_SERVICE" \
  odoo \
  --config=/etc/odoo/odoo.conf \
  --database="$DB_NAME" \
  -i "$MODULE" \
  --stop-after-init \
  --no-http
```

### 8.2 Commandes interdites

Ne **pas** exécuter :

```bash
# INTERDIT — effet de bord logos PDF (report_layout.xml)
-u laplatine_invoice_payment_info

# INTERDIT — risque de mise à jour involontaire d'autres modules
-u all

# INTERDIT — mise à jour globale implicite
-u base,web,account,...
```

En cas de doute, n'utiliser que le flag **`-i laplatine_customer_statement`** explicitement.

### 8.3 Mise à jour ultérieure (hors périmètre intervention initiale)

Si le module est déjà installé lors d'une intervention future, remplacer `-i` par `-u "$MODULE"` **uniquement** — jamais `-u all`.

### 8.4 Redémarrage Odoo

```bash
docker compose up -d "$ODOO_SERVICE"
```

### 8.5 Note logo PDF (stratégie A)

Après checkout `6254616`, le fichier `laplatine_invoice_payment_info/views/report_layout.xml` sur disque contient des styles de logo agrandis (`76dca4d`). Comme **aucune** mise à jour de `laplatine_invoice_payment_info` n'est lancée :

- les vues PDF facture en base restent celles de `c06a386` ;
- le comportement PDF production est **inchangé** ;
- l'évolution taille logo = **chantier séparé**, sur GO MOA dédié.

**Critères de passage immédiat** :

- [ ] Commande `-i laplatine_customer_statement` terminée avec code de sortie `0`
- [ ] Aucune traceback Python dans la sortie console
- [ ] Aucune commande `-u laplatine_invoice_payment_info` ni `-u all` exécutée
- [ ] Service Odoo redémarré

---

## 9. Contrôles de logs, version et disponibilité HTTP

### 9.1 Logs post-installation

```bash
cd "$PROD_ROOT"

docker compose logs "$ODOO_SERVICE" --tail=200
```

**Rechercher** :

- absence de `ERROR` / `CRITICAL` liés à `laplatine_customer_statement`
- message de chargement module sans exception
- connexion DB correcte au démarrage

### 9.2 Contrôle HTTP automatisé

```bash
for i in $(seq 1 30); do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' "$PROD_URL/web/login" || true)"

  if [ "$CODE" = "200" ]; then
    echo "Odoo opérationnel."
    break
  fi

  sleep 2
done
```

**Résultat attendu** : HTTP `200` sur `/web/login` dans les 60 secondes.

### 9.3 Version installée en base

```bash
docker compose exec -T "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c \
  "SELECT name, state, latest_version FROM ir_module_module WHERE name = 'laplatine_customer_statement';"
```

**Résultat attendu** :

| name | state | latest_version |
|------|-------|----------------|
| laplatine_customer_statement | installed | 18.0.1.1.1 |

### 9.4 Dépendance Python (sanity check)

```bash
docker compose exec -T "$ODOO_SERVICE" python3 -c \
  "import xlsxwriter; print(xlsxwriter.__version__)"
```

### 9.5 Accès interface

- [ ] Odoo accessible (`$PROD_URL`)
- [ ] Connexion utilisatrice comptable (Ethel / Véréna ou compte équivalent) OK
- [ ] Bouton **État de facturation** visible sur une fiche client (droit `account.group_account_invoice`)

**Critères de passage** :

- [ ] Module `installed` en version `18.0.1.1.1`
- [ ] Logs sans erreur bloquante
- [ ] HTTP 200 + interface accessible

---

## 10. Recette post-installation (production)

Recette à réaliser **sur la production** avec un compte métier, sur **1 à 2 clients représentatifs** (dont un avec factures en retard si possible).

| ID | Contrôle | Attendu |
|----|----------|---------|
| R-01 | Bouton wizard | Ouverture depuis fiche partenaire client |
| R-02 | Période par défaut | 90 derniers jours glissants |
| R-03 | Génération XLSX | Fichier `.xlsx` téléchargé, ouvrable |
| R-04 | Bloc synthèse | Total facturé, réglé, à régler, dont en retard |
| R-05 | Lignes factures | Colonnes spec ; avoirs absents |
| R-06 | Statuts retard | Texte rouge foncé gras, sans fond sur les lignes |
| R-07 | Impression | A4 paysage, 1 page en largeur, en-têtes répétés |
| R-08 | Devise unique | Message d'erreur clair si multi-devises |
| R-09 | Période vide | Message spec, pas de fichier vide |
| R-10 | Non-régression | Facturation / paiements existants inchangés |

**Verdict recette** : à consigner par la MOA (GO / NO-GO). En cas de NO-GO → section 11 (rollback).

---

## 11. Procédure de rollback

Exécuter si : échec installation, erreurs bloquantes, recette post-installation NO-GO, ou incident métier.

### 11.1 Principe

Restaurer l'état **exact** antérieur à l'intervention à partir des sauvegardes §5 et §6. Ne pas tenter un rollback partiel (désinstallation seule) sauf avis technique contraire documenté.

### 11.2 Garde-fous variables (obligatoire)

Avant toute opération destructive :

```bash
: "${PROD_ROOT:?PROD_ROOT non défini}"
: "${DB_NAME:?DB_NAME non défini}"
: "${BACKUP_DIR:?BACKUP_DIR non défini}"
: "${FILESTORE_SRC:?FILESTORE_SRC non défini}"
: "${DOREVIA_REPO:?DOREVIA_REPO non défini}"

test -f "$BACKUP_DIR/${DB_NAME}.dump" \
  || { echo "STOP : dump introuvable"; exit 1; }
test -f "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz" \
  || { echo "STOP : archive filestore introuvable"; exit 1; }
```

### 11.3 Étapes

```bash
cd "$PROD_ROOT"

# 1. Arrêter Odoo
docker compose stop "$ODOO_SERVICE"

# 2. Restaurer PostgreSQL (DESTRUCTIF sur la base courante)
docker compose exec -T "$DB_SERVICE" dropdb -U "$DB_USER" --if-exists "$DB_NAME"
docker compose exec -T "$DB_SERVICE" createdb -U "$DB_USER" "$DB_NAME"
cat "$BACKUP_DIR/${DB_NAME}.dump" | docker compose exec -T "$DB_SERVICE" \
  pg_restore -U "$DB_USER" -d "$DB_NAME" --no-owner --no-acl

# 3. Restaurer filestore
rm -rf "$FILESTORE_SRC"
mkdir -p "$(dirname "$FILESTORE_SRC")"
tar -xzf "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz" -C "$(dirname "$FILESTORE_SRC")"

# 4. Revenir au commit Dorevia antérieur (stratégie A : c06a386)
cd "$DOREVIA_REPO"
git checkout --detach "$PROD_COMMIT_BEFORE"

# 5. Redémarrer Odoo
docker compose up -d "$ODOO_SERVICE"
```

### 11.4 Vérifications post-rollback

```bash
docker compose logs "$ODOO_SERVICE" --tail=100

docker compose exec -T "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c \
  "SELECT name, state FROM ir_module_module WHERE name = 'laplatine_customer_statement';"
```

Contrôle HTTP (§9.2) :

```bash
for i in $(seq 1 30); do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' "$PROD_URL/web/login" || true)"
  if [ "$CODE" = "200" ]; then echo "Odoo opérationnel."; break; fi
  sleep 2
done
```

- [ ] Odoo accessible
- [ ] Module absent ou à l'état pré-intervention
- [ ] Facturation / paiements fonctionnels (smoke test MOA)

### 11.5 Délais et communication

- Documenter l'incident et la cause
- Informer MOA et utilisateurs
- Ne pas retenter le déploiement sans analyse de cause et nouveau GO MOA

---

## 12. Journal d'intervention — déploiement 2026-07-04

| Champ | Valeur |
|-------|--------|
| Date / heure début | 2026-07-04 22:36 UTC |
| Date / heure fin | 2026-07-04 22:38 UTC |
| Opérateur | Dorevia (intervention automatisée) |
| GO MOA d'exécution (réf.) | Session 2026-07-04 — GO MOA explicite |
| GO production fonctionnel MOA | **GO — 2026-07-05** |
| Stratégie | Option A — checkout détaché `4ba7bef`, `-i` seul |
| Commit avant intervention | `c06a386` |
| Commit déployé | `4ba7bef` |
| Version module | `18.0.1.1.1` |
| Type opération | `-i laplatine_customer_statement` **uniquement** |
| `-u laplatine_invoice_payment_info` / `-u all` | Non — confirmé |
| Odoo arrêté avant sauvegardes | Oui |
| Test connexion DB préalable | OK — `odoo_prod@db_prod:5432` |
| Sauvegarde PG | `/opt/laplatine/backups/20260704_223642_pre_laplatine_customer_statement/laplatine_prod.dump` |
| Sauvegarde filestore | `.../filestore_laplatine_prod.tar.gz` |
| Écart disque logo XML | Oui — `report_layout.xml` sur disque ≠ base ; **non chargé** |
| Chantier logo PDF | Reporté — traitement séparé |
| Résultat recette technique | GO — XLSX généré (SAVEUR KARAYB, 19 factures) |
| Résultat recette MOA | **GO production fonctionnel — 2026-07-05** |
| Rollback effectué | Non |
| Observations | Erreurs préexistantes `calendar_public_holiday` / `hr_holidays_public` — hors périmètre |

---

## 13. Références

| Document | Emplacement |
|----------|-------------|
| README module | [`README.md`](README.md) |
| Spécification V1.1 | [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md) |
| Recette visuelle lab | [`outputs/laplatine_customer_statement_visual_qa/`](../../../outputs/laplatine_customer_statement_visual_qa/) |
| Verrou commit lab | [`addons-lock.tsv`](../../../addons-lock.tsv) (racine lab) |

---

## 14. Rappel final

> **V1.1 en production** — GO fonctionnel MOA 2026-07-05.  
> Module `laplatine_customer_statement` `18.0.1.1.1` opérationnel sur `https://prod.sarl-la-platine.fr`.  
> Toute nouvelle intervention (mise à jour, rollback) requiert un GO MOA explicite.
