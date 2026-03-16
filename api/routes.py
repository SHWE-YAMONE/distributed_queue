import uuid
from fastapi import APIRouter, HTTPException
from core.broker import RedisBroker
from core.schemas import TaskSchema

router = APIRouter()
broker = RedisBroker()

@router.post("/tasks/{task_type}")
async def submit_task(task_type: str, payload: dict):
    """
    Accepts a task, validates it, and routes it to the 
    appropriate priority queue.
    """
    # 1. Generate unique ID for tracking
    task_id = str(uuid.uuid4())
    
    # 2. Validate data against our shared schema
    try:
        task_obj = TaskSchema(
            id=task_id,
            task_type=task_type,
            payload=payload,
            retries=0
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid task data: {str(e)}")

    # 3. Determine Priority
    # Emails are high priority; everything else is low priority
    queue_name = "high_priority" if task_type == "email" else "low_priority"
    
    # 4. Push to Redis
    try:
        broker.conn.rpush(queue_name, task_obj.model_dump_json())
        # Initial status entry in the result store
        broker.set_result(task_id, "queued")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Broker connection failed")

    return {
        "status": "accepted",
        "task_id": task_id,
        "queue": queue_name
    }

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Polls the result store for the current state of a task.
    """
    result = broker.get_result(task_id)
    
    # If broker.get_result returns None/Default, handle it
    if not result or result.get("status") == "pending":
         # If it's not in the result store yet, it's either non-existent or brand new
         return {"task_id": task_id, "status": "not_found_or_queued"}
         
    return {
        "task_id": task_id,
        "status": result.get("status"),
        "result": result.get("result"),
        "error": result.get("error") if result.get("status") == "failed" else None
    }