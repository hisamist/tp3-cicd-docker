from fastapi import APIRouter, HTTPException
from src.db import get_db_connection
from src.schemas.task import Task, TaskCreate, TaskUpdate
from typing import List

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/", response_model=List[Task])
async def get_tasks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks ORDER BY id")
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return tasks

@router.get("/{id}", response_model=Task)
async def get_task(id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    task = cur.fetchone()
    cur.close()
    conn.close()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task

@router.post("/", response_model=Task)
async def create_task(task: TaskCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, description) VALUES (%s, %s) RETURNING *",
        (task.title, task.description)
    )
    new_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_task

# PUT : On remplace TOUT (y compris completed)
@router.put("/{id}", response_model=Task)
async def update_task(id: int, task_data: TaskUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title = %s, description = %s, completed = %s WHERE id = %s RETURNING *",
        (task_data.title, task_data.description, task_data.completed, id)
    )
    updated_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not updated_task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return updated_task

# PATCH : On ne change que ce qui est envoyé
@router.patch("/{id}", response_model=Task)
async def patch_task(id: int, task_data: TaskUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # On extrait seulement les champs envoyés dans le JSON
    data = task_data.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="Aucun champ à modifier")

    # Construction dynamique de la requête SQL
    query = "UPDATE tasks SET " + ", ".join([f"{k} = %s" for k in data.keys()]) + " WHERE id = %s RETURNING *"
    values = list(data.values()) + [id]
    
    cur.execute(query, values)
    updated_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not updated_task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return updated_task

@router.delete("/{id}")
async def delete_task(id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (id,))
    deleted_id = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not deleted_id:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return {"message": f"Tâche {id} supprimée"}