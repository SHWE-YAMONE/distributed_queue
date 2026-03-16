import time
import random

def run_task(task):
    # Simulation delay
    time.sleep(random.uniform(0.5, 1.5))

    if task.task_type == "email":
        if random.random() < 0.2:
            raise ConnectionError("SMTP Server Timeout")
        return f"Email sent to user {task.payload.get('user_id')}"
    
    if task.task_type == "image_proc":
        return f"Image {task.payload.get('content')} processed"
    
    return "Task completed"