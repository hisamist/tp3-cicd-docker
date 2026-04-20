import os
import redis

# On récupère l'hôte Redis depuis les variables d'environnement de Docker Compose
# Par défaut, l'hôte est "redis" (le nom du service dans docker-compose.yml)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Configuration du client Redis
# decode_responses=True permet de récupérer des chaînes de caractères (str) 
# au lieu de données binaires (bytes)
r = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    decode_responses=True
)

def get_redis():
    """
    Retourne l'instance de connexion Redis.
    """
    return r