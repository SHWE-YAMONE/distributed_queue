from fastapi import FastAPI, Request, Response
from .rate_limit import limiter
from .routes import router

app = FastAPI()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # Only rate limit POST requests (submitting tasks)
    if request.method == "POST":
        if not limiter.is_allowed(client_ip):
            return Response(
                content='{"error": "Rate limit exceeded. Slow down your submissions!"}',
                status_code=429,
                media_type="application/json"
            )
    
    return await call_next(request)

app.include_router(router)