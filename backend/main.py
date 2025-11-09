from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.api import webhooks, position_groups
from app.db.session import get_db, init_db_session
from app.services.risk_engine import RiskEngine
from app.services.tp_manager import TPManager
from app.services.pool_manager import ExecutionPoolManager
from app.services.queue_manager import QueueManager
import asyncio
import time

app = FastAPI()

async def main_loop_task(
    db: Session,
    risk_engine: RiskEngine,
    tp_manager: TPManager,
    pool_manager: ExecutionPoolManager,
    queue_manager: QueueManager
):
    while True:
        print("Main loop running...")
        # TODO: Implement main loop logic here
        # 1. Check for new signals in the queue
        # 2. Process signals (e.g., open new positions if slots available)
        # 3. Check for TP hits
        # 4. Run risk engine
        await asyncio.sleep(5) # Run every 5 seconds for now

# Initialize database session and start background tasks on startup
@app.on_event("startup")
async def startup_event():
    init_db_session()
    # Create a dummy session for the background task. In a real app, use a proper session management for background tasks.
    # For now, we'll pass a new session to the main_loop_task.
    # This is a simplified approach for demonstration and will need refinement for production.
    db_session = next(get_db())
    asyncio.create_task(main_loop_task(
        db=db_session,
        risk_engine=RiskEngine(db_session),
        tp_manager=TPManager(db_session),
        pool_manager=ExecutionPoolManager(db_session),
        queue_manager=QueueManager(db_session)
    ))

app.include_router(webhooks.router)
app.include_router(position_groups.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
