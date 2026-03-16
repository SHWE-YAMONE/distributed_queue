def handle_failure(broker, task, exception):
    if task.retries < 3:
        task.retries += 1
        wait_time = 2 ** task.retries
        print(f"Task {task.id} failed ({exception}). Retrying in {wait_time}s...")
        broker.schedule(task.model_dump_json(), wait_time)
    else:
        print(f"Task {task.id} failed permanently. Moving to DLQ.")
        broker.conn.rpush(broker.dlq_name, task.model_dump_json())