from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.api import webhooks
from app.db.session import get_db, init_db_session
from app.services.risk_engine import RiskEngine
from app.services.tp_manager import TPManager
from app.services.pool_manager import ExecutionPoolManager
from app.services.queue_manager import QueueManager

app = FastAPI()

# Initialize database session on startup
@app.on_event("startup")
async def startup_event():
    init_db_session()

app.include_router(webhooks.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/run_main_loop")
async def run_main_loop(
    db: Session = Depends(get_db),
    risk_engine: RiskEngine = Depends(RiskEngine),
    tp_manager: TPManager = Depends(TPManager),
    pool_manager: ExecutionPoolManager = Depends(ExecutionPoolManager),
    queue_manager: QueueManager = Depends(QueueManager)
):
    # Placeholder for the main loop logic
    # TODO: Implement main loop logic here
    print("Main loop triggered!")
    return {"status": "Main loop triggered"}
