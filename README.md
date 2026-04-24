# TP3 — CI/CD & Docker

[![CI/CD Pipeline](https://github.com/hisamist/tp3-cicd-docker/actions/workflows/ci.yml/badge.svg)](https://github.com/hisamist/tp3-cicd-docker/actions/workflows/ci.yml)
[![Docker Image](https://ghcr.io/hisamist/tp3-cicd-docker/state)](https://github.com/hisamist/tp3-cicd-docker/pkgs/container/tp3-cicd-docker)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](https://github.com/hisamist/tp3-cicd-docker/actions)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

API REST FastAPI avec pipeline CI/CD complet, déploiement Docker multi-service et stratégie blue/green.

---

## Stack

| Composant | Technologie |
|-----------|-------------|
| API | FastAPI + Python 3.13 |
| Base de données | PostgreSQL 16 |
| Cache | Redis 7 |
| Reverse proxy | Nginx |
| Conteneurisation | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Registry | GitHub Container Registry (GHCR) |
| Sécurité image | Trivy |
| Linter | Ruff |
| Tests | pytest + pytest-cov |

---

## Structure

```
.
├── src/
│   ├── main.py          # App FastAPI + health check
│   ├── db.py            # Connexion PostgreSQL
│   ├── cache.py         # Connexion Redis
│   ├── routes/
│   │   └── tasks.py     # Endpoints CRUD /api/tasks
│   └── schemas/
│       └── task.py      # Modèles Pydantic
├── tests/
│   ├── unit/            # Tests schemas, db, cache (mocks)
│   └── integration/     # Tests API via TestClient
├── nginx/
│   ├── default.conf     # Config dev
│   └── blue-green.conf  # Config blue/green prod
├── Dockerfile           # Multi-stage, non-root, Alpine
├── docker-compose.yml   # Stack de développement
├── docker-compose.prod.yml  # Stack blue/green production
├── deploy-green.sh      # Script de déploiement zero-downtime
└── .github/workflows/
    └── ci.yml           # Pipeline CI/CD
```

---

## Lancer en développement

```bash
# Copier les variables d'environnement
cp .env.example .env

# Démarrer la stack complète
docker compose up -d --build

# Vérifier
curl http://localhost/health
```

L'API est disponible sur `http://localhost`.

---

## Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Message de bienvenue |
| GET | `/health` | État de l'API, DB et Redis |
| GET | `/api/tasks/` | Liste toutes les tâches |
| GET | `/api/tasks/{id}` | Récupère une tâche |
| POST | `/api/tasks/` | Crée une tâche |
| PUT | `/api/tasks/{id}` | Remplace une tâche complète |
| PATCH | `/api/tasks/{id}` | Modifie des champs partiels |
| DELETE | `/api/tasks/{id}` | Supprime une tâche |

---

## Tests

```bash
# Installer les dépendances de dev
uv sync --group dev

# Lancer tous les tests
uv run pytest

# Avec couverture
uv run pytest --cov=src --cov-report=term-missing

# Lint
uv run ruff check src/
```

Couverture actuelle : **99%**

---

## Pipeline CI/CD

Le pipeline GitHub Actions se déclenche sur chaque push et PR vers `main`.

### Job 1 — test (toujours)

1. Lint avec Ruff
2. Tests unitaires + intégration
3. Rapport de couverture uploadé en artefact

### Job 2 — build-and-push (push sur `main` uniquement)

1. Build de l'image Docker avec cache GitHub Actions
2. Push vers GHCR (`ghcr.io/<owner>/<repo>`)
3. Scan de vulnérabilités Trivy — bloque si CVE `CRITICAL` ou `HIGH`

---

## Déploiement Blue/Green

La stack de production fait tourner deux versions de l'API en parallèle. Nginx route le trafic vers la version active.

### Démarrer la stack prod

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Déployer une nouvelle version (blue → green)

```bash
bash deploy-green.sh
```

Le script effectue 5 étapes :

1. Build et démarrage de `api-green`
2. Attente du healthcheck Docker (`healthy`)
3. Test de green via `/test-standby/health` avant tout switch
4. Bascule Nginx (`sed` + `nginx -s reload`) — zero downtime
5. Vérification finale + rollback automatique si échec

### Rollback manuel (green → blue)

```bash
sed -i 's|server api-green:8000;|server api-blue:8000;|g' nginx/blue-green.conf
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Arrêter blue après validation

```bash
docker compose -f docker-compose.prod.yml stop api-blue
```

---

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL PostgreSQL | `postgresql://postgres:secret@db:5432/todo_db` |
| `REDIS_HOST` | Hôte Redis | `redis` |
| `REDIS_PORT` | Port Redis | `6379` |
| `POSTGRES_USER` | Utilisateur PostgreSQL | — |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | — |
| `POSTGRES_DB` | Nom de la base | — |
