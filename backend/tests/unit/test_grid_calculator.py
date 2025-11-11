import pytest
from decimal import Decimal

from backend.app.services.grid_calculator import calculate_dca_levels, calculate_position_size, calculate_take_profit_prices

def test_calculate_dca_levels():
    """
    Test calculation of DCA level prices.
    """
    entry_price = Decimal("100.00")
    dca_config = {
        "dca_levels": 3,
        "price_gaps": [Decimal("0.01"), Decimal("0.02"), Decimal("0.03")] # 1%, 2%, 3% below entry
    }
    
    expected_levels = [
        {"price": Decimal("99.00")},  # 100 * (1 - 0.01)
        {"price": Decimal("98.00")},  # 100 * (1 - 0.02)
        {"price": Decimal("97.00")}   # 100 * (1 - 0.03)
    ]

    result = calculate_dca_levels(entry_price, dca_config)
    assert result == expected_levels

def test_calculate_position_size():
    """
    Test calculation of individual DCA order sizes based on weights.
    """
    total_risk_usd = Decimal("1000.00")
    dca_weights = [Decimal("0.25"), Decimal("0.50"), Decimal("0.25")]

    expected_sizes = [
        Decimal("250.00"), # 1000 * 0.25
        Decimal("500.00"), # 1000 * 0.50
        Decimal("250.00")  # 1000 * 0.25
    ]

    result = calculate_position_size(total_risk_usd, dca_weights)
    assert result == expected_sizes

def test_calculate_take_profit_prices():
    """
    Test calculation of take-profit prices for each DCA level.
    """
    entry_prices = [Decimal("99.00"), Decimal("98.00"), Decimal("97.00")]
    tp_percent = Decimal("0.01") # 1% take profit

    expected_tp_prices = [
        Decimal("99.99"), # 99 * (1 + 0.01)
        Decimal("98.98"), # 98 * (1 + 0.01)
        Decimal("97.97")  # 97 * (1 + 0.01)
    ]

    result = calculate_take_profit_prices(entry_prices, tp_percent)
    assert result == expected_tp_prices
