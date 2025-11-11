from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend.app.api import webhooks, position_groups, auth, logs, keys
from backend.app.db.session import get_db, init_db_session
from backend.app.services.risk_engine import RiskEngine, get_risk_engine
from backend.app.services.tp_manager import TPManager, get_tp_manager
from backend.app.services.pool_manager import ExecutionPoolManager, get_pool_manager
from backend.app.services.queue_manager import QueueManager, get_queue_manager
from backend.app.tasks.log_cleanup import scheduler
import asyncio
import time
import os

app = FastAPI()

async def main_loop_task():
    print("Starting main loop task...")
    while True:
        db_session = next(get_db())
        try:
            risk_engine = get_risk_engine(db_session)
            tp_manager = get_tp_manager(db_session)
            pool_manager = get_pool_manager(db_session)
            queue_manager = get_queue_manager(db_session)

            print("Main loop running...")
            # TODO: Implement main loop logic here
            # 1. Check for new signals in the queue
            # 2. Process signals (e.g., open new positions if slots available)
            # 3. Check for TP hits
            # 4. Run risk engine
            
        finally:
            db_session.close()
        
        await asyncio.sleep(5) # Run every 5 seconds for now

# Initialize database session and start background tasks on startup
@app.on_event("startup")
async def startup_event():
    init_db_session()
    scheduler.start()
    if os.environ.get("TESTING") != "True":
        asyncio.create_task(main_loop_task())

app.include_router(webhooks.router, prefix="/api")
app.include_router(position_groups.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(logs.router, prefix="/api/logs")
app.include_router(keys.router, prefix="/api/keys")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
