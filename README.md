# distributed_queue

## Summary
A high-performance, asynchronous job processing system built from scratch using FastAPI and Redis. This project implements core distributed system patterns similar to Celery, featuring priority routing, worker scaling, and automated retries.

## Key Features
**Priority Routing:** Separate queues for high_priority (e.g., emails) and low_priority tasks.
**Worker Scalability:** Horizontally scalable workers via Docker Compose replicas.
**Idempotency & Locks:** Atomic Redis locks ensure a task is never processed twice even if delivered twice.
**Reliability:** Exponential backoff retries and a Dead-Letter Queue (DLQ) for terminal failures.
**Delayed Tasks:** Scheduling support for future task execution using Redis Sorted Sets.(ZSET).
**Real-time Monitoring:** Custom terminal dashboard for live visibility into queue health.
**Traffic Control:** Sliding window rate limiter to protect the API from spikes.

## Getting Started
### Build (Docker)
```
docker-compose up --build -d
```

### Open the Monitor
```
docker-compose exec dashboard python -m dashboard.monitor
```

### Run the Test Suite
```
python test_script.py
```

## Scaling the System
```
docker-compose up -d --scale worker=10
```

## Maintenance
To clear all data and reset the dashboard to zero:
```
docker-compose exec api python -m core.cleanup
```

## Future Improvements
- Visibility Timeouts (Reliable Queue Pattern)
- WebSocket Real-Time Updates
- Task Chaining & Workflows
- Adaptive Auto-Scaling
- User Authentication & Scoped Rate Limiting
- Pluggable Backends