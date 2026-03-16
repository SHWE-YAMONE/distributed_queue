from pydantic import BaseModel, Field
from typing import Dict, Any

class TaskSchema(BaseModel):
    id: str
    task_type: str
    payload: Dict[str, Any]
    retries: int = 0