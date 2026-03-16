import redis
from core.config import settings

def clear_system_data():
    r = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        decode_responses=True
    )
    
    # 1. Define patterns to delete
    patterns = [
        "result:*",              # Completed/Failed task data
        "rate_limit:*",          # Rate limiter windows
        "rate_limit_sliding:*",  # Sliding window sets
        "processed_lock:*"       # Idempotency locks
    ]
    
    print("Starting system cleanup...")
    
    total_deleted = 0
    for pattern in patterns:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
            print(f"  - Deleted {len(keys)} keys matching '{pattern}'")
            total_deleted += len(keys)

    # 2. Clear the Priority Queues
    queues = ["high_priority", "low_priority", "tasks_dead_letter", "tasks_scheduled"]
    for q in queues:
        if r.exists(q):
            r.delete(q)
            print(f"  - Flushed queue: {q}")

    print(f"\n Cleanup complete. Total keys removed: {total_deleted}")
    print("Your dashboard should now show 0 across all metrics.")

if __name__ == "__main__":
    clear_system_data()