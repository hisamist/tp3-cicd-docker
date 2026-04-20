from pydantic import BaseModel
from typing import Optional

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    # Pour le PUT et PATCH, on utilise les mêmes champs
    pass

class Task(TaskBase):
    id: int