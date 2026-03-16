import redis
import json
import time
from .config import settings

class RedisBroker:
    def __init__(self):
        self.conn = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            decode_responses=True
        )
        self.dlq_name = "tasks_dead_letter"
        self.scheduled_name = "tasks_scheduled"

    def enqueue(self, task_json: str, priority: str = "low"):
        queue = "high_priority" if priority == "high" else "low_priority"
        self.conn.rpush(queue, task_json)

    def schedule(self, task_json: str, delay_seconds: int):
        execute_at = time.time() + delay_seconds
        self.conn.zadd(self.scheduled_name, {task_json: execute_at})

    def set_result(self, task_id: str, status: str, result=None, error=None):
        data = json.dumps({"status": status, "result": result, "error": error})
        self.conn.setex(f"result:{task_id}", 86400, data)

    def get_result(self, task_id: str):
        data = self.conn.get(f"result:{task_id}")
        return json.loads(data) if data else None