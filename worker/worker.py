import signal
import time
import json
import logging
from core.broker import RedisBroker
from core.schemas import TaskSchema
from .executor import run_task
from .retry import handle_failure

# Configure logging to see what's happening in Docker logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Worker")

class DistributedWorker:
    def __init__(self):
        self.broker = RedisBroker()
        self.keep_running = True
        self.current_task_id = None
        
        # Listen for shutdown signals (SIGTERM for Docker, SIGINT for Ctrl+C)
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, signum, frame):
        """Sets flag to stop after the current task finishes."""
        logger.info("Shutdown signal received. Finishing current job then exiting...")
        self.keep_running = False

    def is_already_processed(self, task_id: str) -> bool:
        """
        Idempotency Check: Ensures we don't process the same task twice 
        if it's delivered multiple times by the broker.
        """
        lock_key = f"processed_lock:{task_id}"
        # nx=True means only set the key if it doesn't exist
        # ex=86400 keeps the lock for 24 hours
        is_new = self.broker.conn.set(lock_key, "true", nx=True, ex=86400)
        return not is_new

    def run(self):
        logger.info("Worker initialized. Listening for [high_priority, low_priority]...")
        
        while self.keep_running:
            try:
                # Use blpop on multiple keys for priority: high_priority checked first
                # Timeout allows the loop to check self.keep_running periodically
                result = self.broker.conn.blpop(["high_priority", "low_priority"], timeout=5)
                
                if result:
                    queue_name, data = result
                    task = TaskSchema.model_validate_json(data)
                    self.current_task_id = task.id

                    # 1. Idempotency Guard
                    if self.is_already_processed(task.id):
                        logger.warning(f"Task {task.id} already processed. Skipping.")
                        continue

                    # 2. Mark as Processing in Result Store
                    logger.info(f"Processing {task.task_type} Task: {task.id} from {queue_name}")
                    self.broker.set_result(task.id, "processing")
                    
                    try:
                        # 3. Execute the actual business logic
                        outcome = run_task(task)
                        
                        # 4. Success - Store Result
                        self.broker.set_result(task.id, "completed", outcome)
                        logger.info(f"Task {task.id} finished successfully.")
                    
                    except Exception as e:
                        # 5. Failure - Trigger Retry/DLQ Logic
                        logger.error(f"Task {task.id} failed: {str(e)}")
                        handle_failure(self.broker, task, e)
                        self.broker.set_result(task.id, "failed", str(e))
                    
                    finally:
                        self.current_task_id = None

            except Exception as e:
                logger.error(f"Worker Loop Error: {e}")
                time.sleep(1) # Prevent rapid-fire errors if Redis is down

        logger.info("Worker shut down gracefully.")

if __name__ == "__main__":
    worker = DistributedWorker()
    worker.run()