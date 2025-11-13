from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ..services import order_service, take_profit_service, risk_engine, exchange_manager, precision_service
from ..db.session import get_async_db

async def refresh_all_precisions():
    """
    Iterate through all unique exchange/symbol combinations and refresh their precision cache.
    """
    # TODO: Implement logic to get a database session and query for unique exchange/symbols
    # from the PositionGroup table. For now, we'll use a placeholder.
    print("Refreshing precision cache for all active symbols...")
    # async with get_async_db() as db:
    #     symbols = db.query(PositionGroup.exchange, PositionGroup.symbol).distinct().all()
    #     for exchange, symbol in symbols:
    #         await precision_service.fetch_and_cache_precision_rules(db, exchange, symbol)

def setup_scheduler():
    """
    Set up and start the task scheduler.
    """
    scheduler = AsyncIOScheduler()
    
    # Schedule tasks
    scheduler.add_job(order_service.monitor_order_fills, 'interval', seconds=10)
    scheduler.add_job(take_profit_service.check_take_profit_conditions, 'interval', seconds=15)
    scheduler.add_job(risk_engine.evaluate_risk_conditions, 'interval', seconds=30)
    scheduler.add_job(refresh_all_precisions, 'interval', minutes=5)
    # scheduler.add_job(exchange_manager.validate_exchange_connections, 'interval', minutes=5)
    
    return scheduler
