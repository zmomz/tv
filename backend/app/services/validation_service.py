from decimal import Decimal
from sqlalchemy.orm import Session

from ..services import precision_service, exchange_manager

async def validate_and_adjust_order(
    db: Session,
    exchange: str,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
) -> tuple[Decimal, Decimal]:
    """
    Validate and adjust order parameters based on exchange precision rules.
    """
    precision = await precision_service.fetch_precision_info(db, exchange, symbol)
    
    if not precision:
        # As per SoW, if precision metadata is missing, signal is held (queued).
        # For now, we'll raise an error, and the calling service will handle queuing.
        raise ValueError(f"Precision rules not available for {exchange}:{symbol}. Cannot validate order.")
    
    # Adjust quantity
    quantity = Decimal(exchange_manager.ccxt.decimal_to_precision(
        float(quantity),
        exchange_manager.ccxt.ROUND,
        precision['amount'],
    ))
    
    # Adjust price
    price = Decimal(exchange_manager.ccxt.decimal_to_precision(
        float(price),
        exchange_manager.ccxt.ROUND,
        precision['price'],
    ))
    
    return quantity, price
