from decimal import Decimal
from ..services import exchange_manager
from sqlalchemy.orm import Session

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
    precision = await exchange_manager.get_precision_rules(db, exchange, symbol)
    
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

async def fetch_precision_info(db: Session, exchange: str, symbol: str) -> dict:
    """
    Fetch precision information for a symbol on an exchange.
    """
    return await exchange_manager.get_precision_rules(db, exchange, symbol)

def calculate_min_notional(quantity: Decimal, price: Decimal) -> Decimal:
    """
    Calculate the notional value of an order.
    """
    return quantity * price
