# Nom de l'image (à adapter si nécessaire)
IMAGE_NAME=mon-projet-api:latest

# --- Commandes de base ---

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

# --- Section Sécurité ---

# 1. Vérifier si l'utilisateur est bien "appuser"
check-user:
	@echo "🔍 Vérification de l'utilisateur courant dans le conteneur..."
	docker compose exec api whoami

# 2. Scan complet avec Trivy
scan:
	@echo "🛡️ Lancement du scan de sécurité complet..."
	docker run --rm -v //var/run/docker.sock:/var/run/docker.sock \
	  aquasec/trivy image $(IMAGE_NAME)

# 3. Scan rapide (uniquement CRITICAL et HIGH)
scan-fast:
	@echo "⚡ Scan rapide (Vulnérabilités CRITICAL et HIGH uniquement)..."
	docker run --rm -v //var/run/docker.sock:/var/run/docker.sock \
	  aquasec/trivy image --severity CRITICAL,HIGH $(IMAGE_NAME)

# --- Nettoyage ---

clean:
	docker system prune -f