import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Retrieve the connection string from Environment Variables (set in docker-compose.yml)
# Default format: postgresql://username:password@hostname:port/database_name
# 'db' refers to the service name defined in your Docker Compose file
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:secret@db:5432/todo_db")

def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database.
    
    Using RealDictCursor ensures that query results are returned as 
    Python dictionaries (e.g., {'id': 1, 'task': 'Buy milk'}) 
    instead of plain tuples (e.g., (1, 'Buy milk')).
    """
    # Connect to the database using the URL
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()