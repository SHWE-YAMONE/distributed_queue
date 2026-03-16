import time
import os
from core.broker import RedisBroker

def get_stats():
    broker = RedisBroker()
    r = broker.conn
    
    # Priority Queues + DLQ
    pending = r.llen("high_priority") + r.llen("low_priority")
    failed = r.llen("tasks_dead_letter")
    scheduled = r.zcard("tasks_scheduled")
    
    # Results Scanning
    completed = 0
    processing = 0
    for key in r.scan_iter("result:*"):
        task_id = key.split(":")[-1]
        data = broker.get_result(task_id)
        if data:
            if data['status'] == "completed": completed += 1
            if data['status'] == "processing": processing += 1

    return {
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "scheduled": scheduled,
        "memory": r.info().get('used_memory_human')
    }

def run_dashboard():
    while True:
        s = get_stats()
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{'='*30}\nQUEUE MONITOR\n{'='*30}")
        print(f"PENDING:    {s['pending']}")
        print(f"PROCESSING: {s['processing']}")
        print(f"COMPLETED:  {s['completed']}")
        print(f"FAILED:     {s['failed']}")
        print(f"SCHEDULED:  {s['scheduled']}")
        print(f"MEMORY:     {s['memory']}\n{'='*30}")
        time.sleep(1)

if __name__ == "__main__":
    run_dashboard()