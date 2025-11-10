from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services import order_service, take_profit_service, risk_engine, exchange_manager
from app.db.session import get_db

def setup_scheduler():
    """
    Set up and start the task scheduler.
    """
    scheduler = AsyncIOScheduler()
    
    # Schedule tasks
    scheduler.add_job(order_service.monitor_order_fills, 'interval', seconds=10)
    scheduler.add_job(take_profit_service.check_take_profit_conditions, 'interval', seconds=15)
    scheduler.add_job(risk_engine.evaluate_risk_conditions, 'interval', seconds=30)
    # scheduler.add_job(exchange_manager.validate_exchange_connections, 'interval', minutes=5)
    
    return scheduler
