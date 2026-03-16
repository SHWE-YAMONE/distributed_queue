import time
from core.broker import RedisBroker

def run_scheduler():
    broker = RedisBroker()
    print("Scheduler active: Watching for delayed tasks...")
    
    while True:
        now = time.time()
        # Find tasks where the score is
        tasks = broker.conn.zrangebyscore("tasks_scheduled", 0, now)
        
        for task_data in tasks:
            # Move to main queue and remove from scheduled set
            if broker.conn.zrem("tasks_scheduled", task_data):
                broker.enqueue(task_data)
                print("Scheduled task released to main queue.")
        
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()