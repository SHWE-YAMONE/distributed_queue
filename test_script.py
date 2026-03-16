import asyncio
import httpx
import time
import random

# Configuration
API_BASE_URL = "http://localhost:8000/tasks"
TOTAL_TASKS = 30
CONCURRENT_TASKS = 5  # Number of tasks to submit at once to avoid smashing the limiter

async def submit_single_task(client, i):
    """Submits a task and returns the task_id if successful."""
    task_type = random.choice(["email", "image_proc", "data_cleanup"])
    payload = {
        "user_id": 1000 + i,
        "content": f"Test payload for job number {i}",
        "timestamp": time.time()
    }
    
    try:
        response = await client.post(f"{API_BASE_URL}/{task_type}", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Submitted {task_type}: {data['task_id']} (Queue: {data['queue']})")
            return data['task_id']
        elif response.status_code == 429:
            print(f"Task {i} rate limited (429).")
        else:
            print(f"Failed to submit task {i}: {response.status_code}")
    except Exception as e:
        print(f"Request error on task {i}: {e}")
    return None

async def poll_task_status(client, task_id):
    """Polls a specific task until it is no longer 'queued' or 'processing'."""
    while True:
        try:
            response = await client.get(f"{API_BASE_URL}/{task_id}")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status in ["completed", "failed"]:
                    return status
            elif response.status_code == 429:
                # If we get rate limited while polling, wait a bit longer
                await asyncio.sleep(2)
        except Exception:
            pass
        
        await asyncio.sleep(1) # Wait 1 second before polling again

async def main():
    print(f"Starting Distributed Queue Test: {TOTAL_TASKS} tasks")
    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Submission Phase
        submission_tasks = []
        for i in range(TOTAL_TASKS):
            submission_tasks.append(submit_single_task(client, i))
            # Small delay to respect the sliding window limiter
            if i % CONCURRENT_TASKS == 0:
                await asyncio.sleep(0.5)

        results = await asyncio.gather(*submission_tasks)
        active_task_ids = [tid for tid in results if tid is not None]
        
        print(f"\nSubmissions complete. {len(active_task_ids)}/{TOTAL_TASKS} tasks accepted.")
        print("Monitoring worker progress...\n")

        # 2. Polling Phase
        if active_task_ids:
            polling_tasks = [poll_task_status(client, tid) for tid in active_task_ids]
            final_statuses = await asyncio.gather(*polling_tasks)
            
            success_count = final_statuses.count("completed")
            fail_count = final_statuses.count("failed")
            
            total_time = time.perf_counter() - start_time
            print(f"\n" + "="*40)
            print(f"TEST COMPLETE")
            print(f"Total Time:   {total_time:.2f}s")
            print(f"Completed:    {success_count}")
            print(f"Failed:       {fail_count}")
            print(f"Throughput:   {len(active_task_ids)/total_time:.2f} tasks/sec")
            print("="*40)
        else:
            print("No tasks were accepted by the API. Check your Rate Limiter settings.")

if __name__ == "__main__":
    asyncio.run(main())