from fastapi import FastAPI, Response
from src.db import get_db_connection
from src.cache import get_redis
import time
from src.routes import tasks

app = FastAPI(title="CI/CD TP API")
app.include_router(tasks.router)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Todo API"}

@app.get("/health")
async def health_check(response: Response):
     # Initialize the health report
    status = {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "services": {
            "database": "unknown",
            "cache": "unknown"
        }
    }

    # 1. Database Connectivity Check
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        status["services"]["database"] = "connected"
    except Exception as e:
        status["status"] = "unhealthy"
        status["services"]["database"] = f"error: {str(e)}"

    # 2. Redis Cache Connectivity Check
    try:
        r = get_redis()
        r.ping()
        status["services"]["cache"] = "connected"
    except Exception as e:
        status["status"] = "unhealthy"
        status["services"]["cache"] = f"error: {str(e)}"

    # If any dependency fails, return HTTP 503 (Service Unavailable)
    if status["status"] == "unhealthy":
        response.status_code = 503
        
    return status

@app.on_event("startup")
def startup_event():
    from src.db import init_db
    init_db()