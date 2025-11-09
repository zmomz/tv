from fastapi import FastAPI
from app.api import webhooks

app = FastAPI()

app.include_router(webhooks.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
