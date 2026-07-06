# Procédure de déploiement production — `laplatine_billing_report`

| Élément | Valeur |
|---------|--------|
| **Référence** | `DEPLOY-FACT-REPORT-001` / `LP-FACT-REPORT-001` |
| **Module** | `laplatine_billing_report` |
| **Version cible** | `18.0.1.0.0` |
| **Commit cible** | `b0bfaaa059bb1cf88bb3be3195651c3754585de7` |
| **Code fonctionnel recetté** | inclus dans `b0bfaaa` (ancêtre `ddad53b`) |
| **Dépôt** | [doreviateam/odoo18-addons-dorevia](https://github.com/doreviateam/odoo18-addons-dorevia) — branche `main` |
| **Commit production connu (avant intervention)** | `2af0fc1b14d7b9ff1552eb61d72c62613babff43` *(à reconfirmer sur site)* |
| **URL production** | `https://prod.sarl-la-platine.fr` |
| **Fenêtre d'intervention** | **Nuit du 6 au 7 juillet 2026** — **00 h 30 – 01 h 00** (France métropole) = **18 h 30 – 19 h 00** (Guadeloupe) |
| **Statut** | **DÉPLOYÉ** — 2026-07-07 00 h 18 FR — rapport [`recette_qa/PROD-FACT-REPORT-20260707/`](recette_qa/PROD-FACT-REPORT-20260707/) |

---

## ⚠️ Règles impératives

1. **Ne rien déployer avant** le créneau validé ci-dessus.
2. **Uniquement** `-i` ou `-u laplatine_billing_report` — **jamais** `-u all` ni autre module.
3. Checkout du dépôt sur `b0bfaaa` : d'autres fichiers (docs `laplatine_procurement_control`) coexistent sur disque mais **ne doivent pas être mis à jour en base**.
4. Conserver le chemin de sauvegarde pour le rollback (§9).

---

## 0. État du dépôt (contrôle préparatoire — 2026-07-06)

Contrôle réalisé sur le dépôt de référence :

| Contrôle | Résultat |
|----------|----------|
| Branche | `main` |
| HEAD | `b0bfaaa` |
| Working tree | propre |
| `origin/main` | synchronisé |
| Périmètre commits module | `4c3b134` … `b0bfaaa` (slices B→E, correctif R06, menu UX) |
| Fichiers hors `laplatine_billing_report/` entre `2af0fc1` et `b0bfaaa` | 19 — **documentation et scripts guide fécule uniquement** (pas de `.py` / `.xml` métier procurement chargé par Odoo) |

**Commandes de vérification (à rejouer sur le serveur production avant intervention)** :

```bash
cd "$DOREVIA_REPO"
git fetch origin
git status --porcelain          # doit être vide
git rev-parse HEAD              # doit être b0bfaaa… après checkout cible
test -f laplatine_billing_report/__manifest__.py
grep '"version"' laplatine_billing_report/__manifest__.py   # 18.0.1.0.0
```

---

## 1. Variables d'environnement (à adapter sur site)

```bash
export PROD_ROOT="/opt/laplatine"
export DB_NAME="laplatine_prod"
export DB_SERVICE="db_prod"          # ou nom du service PostgreSQL
export DB_USER="odoo_prod"
export ODOO_SERVICE="odoo_prod"
export PROD_URL="https://prod.sarl-la-platine.fr"
export BACKUP_DIR="/opt/laplatine/backups/$(date +%Y%m%d_%H%M%S)_pre_laplatine_billing_report"
export DOREVIA_REPO="/opt/laplatine/addons/odoo18-addons-dorevia"
export FILESTORE_SRC="/opt/laplatine/data/filestore_prod"   # à confirmer
export TARGET_COMMIT="b0bfaaa059bb1cf88bb3be3195651c3754585de7"
export PROD_COMMIT_BEFORE=""           # renseigner après git rev-parse HEAD sur prod
export MODULE="laplatine_billing_report"
export MODULE_VERSION="18.0.1.0.0"
```

> **Avant toute action** : `export PROD_COMMIT_BEFORE="$(cd "$DOREVIA_REPO" && git rev-parse HEAD)"` et consigner la valeur dans le journal §10.

---

## 2. Checklist pré-vol (J-0 / avant 00 h 30 FR)

- [ ] GO MOA déploiement production obtenu (distinct du GO lab)
- [ ] Fenêtre 00 h 30 – 01 h 00 FR communiquée aux utilisateurs
- [ ] Espace disque suffisant (dump PG + filestore)
- [ ] `xlsxwriter` présent dans l'image Odoo (§3)
- [ ] Procédure de rollback lue (§9)
- [ ] Contact MOA / Véréna ou Ethel disponible pour recette UI post-déploiement (P2)

---

## 3. Vérification `xlsxwriter` (avant arrêt Odoo)

```bash
cd "$PROD_ROOT"
docker compose exec -T "$ODOO_SERVICE" python3 -c \
  "import xlsxwriter; print('xlsxwriter OK —', xlsxwriter.__version__)"
```

**Critère** : import réussi (lab : `3.1.9`).

---

## 4. Séquence d'intervention

**Odoo reste indisponible** entre l'arrêt (étape 1) et le redémarrage final (étape 7).

```text
1. Arrêter Odoo
2. Sauvegarde PostgreSQL
3. Sauvegarde filestore
4. Checkout code b0bfaaa
5. Test connexion DB (processus isolé)
6. Installation / upgrade UNIQUEMENT laplatine_billing_report
7. Redémarrer Odoo
8. Contrôles techniques + smoke (§7–§8)
9. Recette UI MOA (§8.2)
```

### 4.1 Arrêt Odoo

```bash
cd "$PROD_ROOT"
docker compose stop "$ODOO_SERVICE"
```

### 4.2 Sauvegarde PostgreSQL

```bash
mkdir -p "$BACKUP_DIR"
cd "$PROD_ROOT"

docker compose exec -T "$DB_SERVICE" pg_dump \
  -U "$DB_USER" -Fc --no-owner --no-acl \
  "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}.dump"

ls -lh "$BACKUP_DIR/${DB_NAME}.dump"
cat "$BACKUP_DIR/${DB_NAME}.dump" | \
  docker compose exec -T "$DB_SERVICE" pg_restore --list - | head -10
```

### 4.3 Sauvegarde filestore

```bash
tar -czf "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz" \
  -C "$(dirname "$FILESTORE_SRC")" "$(basename "$FILESTORE_SRC")"
ls -lh "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz"
```

### 4.4 Récupération du code (checkout détaché)

```bash
cd "$DOREVIA_REPO"

if [ -n "$(git status --porcelain)" ]; then
  echo "STOP : modifications locales non commitées"
  exit 1
fi

export PROD_COMMIT_BEFORE="$(git rev-parse HEAD)"
echo "Commit avant intervention : $PROD_COMMIT_BEFORE"

git fetch origin main
git checkout --detach "$TARGET_COMMIT"

test "$(git rev-parse HEAD)" = "$TARGET_COMMIT" \
  || { echo "STOP : commit inattendu"; exit 1; }

grep '"version"' laplatine_billing_report/__manifest__.py
```

**Écart disque documenté** : entre `2af0fc1` et `b0bfaaa`, seuls des fichiers documentation/scripts hors module Odoo procurement changent — **ne pas** lancer `-u laplatine_procurement_control`.

### 4.5 Test connexion DB (obligatoire)

```bash
cd "$PROD_ROOT"

docker compose run --rm --no-deps "$ODOO_SERVICE" odoo \
  --config=/etc/odoo/odoo.conf \
  --database="$DB_NAME" \
  --stop-after-init \
  --no-http
```

**Critère** : code de sortie `0`, connexion DB `utilisateur@service-db:5432` (pas `default@default`).

### 4.6 Installation du module — commande autorisée

**Première installation production** (module absent de la base) :

```bash
cd "$PROD_ROOT"

docker compose run --rm --no-deps "$ODOO_SERVICE" odoo \
  --config=/etc/odoo/odoo.conf \
  --database="$DB_NAME" \
  -i "$MODULE" \
  --stop-after-init \
  --no-http
```

Si le module est déjà en base (`uninstalled` / mise à jour) :

```bash
# Remplacer -i par -u UNIQUEMENT si confirmé en base
-u "$MODULE"
```

### 4.7 Commandes interdites

```bash
# INTERDIT
-u all
-u laplatine_procurement_control
-u laplatine_customer_statement
# toute autre mise à jour globale ou croisée
```

### 4.8 Redémarrage Odoo

```bash
cd "$PROD_ROOT"
docker compose up -d "$ODOO_SERVICE"
```

---

## 5. Contrôles techniques post-déploiement

### 5.1 HTTP

```bash
for i in $(seq 1 30); do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' "$PROD_URL/web/login" || true)"
  [ "$CODE" = "200" ] && echo "Odoo opérationnel (HTTP $CODE)" && break
  sleep 2
done
```

### 5.2 Version en base

```bash
docker compose exec -T "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c \
  "SELECT name, state, latest_version FROM ir_module_module WHERE name = 'laplatine_billing_report';"
```

**Attendu** : `installed` / `18.0.1.0.0`

### 5.3 Smoke automatisé (shell Odoo)

```bash
cd "$PROD_ROOT"

docker compose run --rm odoo odoo shell \
  --config=/etc/odoo/odoo.conf \
  --database="$DB_NAME" \
  --no-http <<'PY'
exec(open("/opt/laplatine/addons/odoo18-addons-dorevia/laplatine_billing_report/scripts/prod_post_deploy_smoke.py").read())
PY
```

**Verdict attendu** : `GO_SMOKE_PROD`

---

## 6. Vérification des droits utilisateurs

Menu : **Paramètres → Utilisateurs**.

### Profils devant voir le menu

| Utilisateur | Groupe requis |
|-------------|---------------|
| Véréna / Ethel (comptabilité) | **Facturation** (`account.group_account_invoice`) |
| David (si accès facturation) | idem |

### Profils sans accès

| Profil | Attendu |
|--------|---------|
| Opérateur stock seul (consommation MP) | Menu **La Platine** absent sous **Facturation** |
| Utilisateur interne sans Facturation | Pas de création wizard |

---

## 7. Recette UI — smoke manuel (Facturation)

À réaliser avec un compte **Facturation** pendant ou juste après la fenêtre.

| ID | Contrôle | Attendu |
|----|----------|---------|
| FUM-01 | Navigation | **Facturation → La Platine → Rapport de facturation** visible |
| FUM-02 | Ordre menus | **La Platine** entre **Fournisseurs** et **Comptabilité** |
| FUM-03 | Wizard | Période M-1 proposée par défaut |
| FUM-04 | Génération | Fichier `.xlsx` téléchargé, 2 onglets Ventes / Achats |
| FUM-05 | Nom fichier | `Rapport_facturation_La_Platine_YYYY-MM-DD_YYYY-MM-DD.xlsx` |
| FUM-06 | Ouverture Excel | Fichier s'ouvre sans alerte bloquante |
| FUM-07 | Non-régression | Facturation / paiements existants inchangés |

**Verdict** : GO / NO-GO — à consigner au journal §10.

---

## 8. Prérequis MOA post-déploiement (P1 / P2 — non bloquants installation)

| # | Gate | Statut |
|---|------|--------|
| P1 | Validation **Excel natif** Windows/Mac sur export réel | ☐ À faire (lendemain acceptable) |
| P2 | Validation métier **Véréna / Ethel** sur export M-1 réel | ☐ À faire |

---

## 9. Plan de rollback

### 9.1 Garde-fous

```bash
: "${PROD_ROOT:?}"
: "${DB_NAME:?}"
: "${BACKUP_DIR:?}"
: "${FILESTORE_SRC:?}"
: "${DOREVIA_REPO:?}"
: "${PROD_COMMIT_BEFORE:?}"

test -f "$BACKUP_DIR/${DB_NAME}.dump" || exit 1
test -f "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz" || exit 1
```

### 9.2 Restauration

```bash
cd "$PROD_ROOT"
docker compose stop "$ODOO_SERVICE"

docker compose exec -T "$DB_SERVICE" dropdb -U "$DB_USER" --if-exists "$DB_NAME"
docker compose exec -T "$DB_SERVICE" createdb -U "$DB_USER" "$DB_NAME"
cat "$BACKUP_DIR/${DB_NAME}.dump" | \
  docker compose exec -T "$DB_SERVICE" \
  pg_restore -U "$DB_USER" -d "$DB_NAME" --no-owner --no-acl

rm -rf "$FILESTORE_SRC"
tar -xzf "$BACKUP_DIR/filestore_${DB_NAME}.tar.gz" \
  -C "$(dirname "$FILESTORE_SRC")"

cd "$DOREVIA_REPO"
git checkout --detach "$PROD_COMMIT_BEFORE"

docker compose up -d "$ODOO_SERVICE"
```

### 9.3 Vérifications post-rollback

- [ ] HTTP 200 sur `$PROD_URL/web/login`
- [ ] `laplatine_billing_report` absent ou état pré-intervention
- [ ] Smoke facturation / stock / consommation MP OK

---

## 10. Journal d'intervention (à compléter sur site)

| Champ | Valeur |
|-------|--------|
| Date / heure début | |
| Date / heure fin | |
| Opérateur | |
| GO MOA exécution | |
| Commit avant (`PROD_COMMIT_BEFORE`) | |
| Commit déployé | `b0bfaaa` |
| Type opération | `-i` ou `-u laplatine_billing_report` uniquement |
| Sauvegarde PG | `$BACKUP_DIR/...` |
| Sauvegarde filestore | `$BACKUP_DIR/...` |
| Smoke automatisé | GO_SMOKE_PROD / NO_GO |
| Recette UI FUM-01–07 | |
| Rollback | Oui / Non |
| Observations | |

---

## 11. Références

| Document | Emplacement |
|----------|-------------|
| Spécification MOA | [`SPECIFICATION_V1.md`](SPECIFICATION_V1.md) |
| Rapport MOA clôture lab | [`docs/recette/RAPPORT_MOA_LP_FACT_REPORT_001.md`](docs/recette/RAPPORT_MOA_LP_FACT_REPORT_001.md) |
| Smoke script production | [`scripts/prod_post_deploy_smoke.py`](scripts/prod_post_deploy_smoke.py) |
| Preuves QA lab | [`recette_qa/SLICE-D-IMPRESSION/`](recette_qa/SLICE-D-IMPRESSION/) |

---

## 12. Rappel final

> **Ne pas exécuter avant le 7 juillet 2026 00 h 30 (France).**  
> **Module seul** : `laplatine_billing_report` @ `b0bfaaa` / `18.0.1.0.0`.  
> Rollback documenté §9 — sauvegardes obligatoires avant upgrade.
