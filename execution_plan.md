# Execution Plan v4.0: Complete SoW-Compliant Execution Engine
## Comprehensive Development Roadmap

---

## 1.1 Executive Summary

This document provides a 100% complete, detailed execution plan to build the Execution Engine from the ground up to full SoW compliance. It has been upgraded to v4.0 to include critical business logic, operational runbooks, and user-centric workflows that were previously missing.

**This version now includes:**
- **Detailed implementation guidance** with algorithm pseudocode
- **Complete data models** and state machines
- **Explicit Business Rules & Formulas:** Precise calculations for PnL, fees, and position sizing.
- **Enhanced acceptance criteria** with technical, performance, and test metrics
- **Validation checkpoints** after each phase
- **User Journey Flows:** Step-by-step descriptions of user interactions, from onboarding to error recovery.
- **Operational Runbooks:** Procedures for monitoring, alerting, data migration, and deployment rollbacks.
- **Quality Gates & Enhanced Testing:** Clear criteria for phase completion, including performance and security testing plans.
- **Configuration Templates & Troubleshooting:** Practical examples and guides for users and operators.
- **Full SoW Traceability:** A matrix linking every requirement to its implementation phase.

**Target Outcome:** Production-ready, robust, and user-friendly packaged web application for Windows and macOS.

---

## 1.2 Current State Assessment

### Backend Status
- ✅ Clean service-oriented architecture established
- ⚠️ Placeholder logic in core services (grid, risk, queue)
- ⚠️ Incomplete precision validation
- ⚠️ Missing exchange abstraction layer
- ⚠️ No price monitoring service

### Frontend Status
- ✅ Component-based architecture in place
- ⚠️ Most UI views are placeholders
- ⚠️ No real-time data synchronization
- ⚠️ Missing WebSocket integration
- ⚠️ No state management configured

---

## 2. Architectural Decisions & Decision Frameworks

To provide clear guidance, the following core architectural decisions have been made:

- **State Management (Frontend):** `Zustand` is chosen over Redux for its simplicity, minimal boilerplate, and hook-based API, which is well-suited for the real-time nature of the application without overwhelming complexity.
- **Component Library (Frontend):** `Material-UI (MUI)` is selected for its comprehensive set of components, robust theming capabilities, and adherence to established design principles, ensuring a professional and consistent UI.
- **Backend Framework:** `FastAPI` is used for its high performance, asynchronous support (critical for handling concurrent exchange communications), and automatic OpenAPI documentation generation.
- **ORM:** `SQLAlchemy` (asyncio version) is used for its power and flexibility, providing a robust data access layer that protects against SQL injection.
- **Exchange Integration:** `ccxt` is the chosen library for interacting with exchanges due to its broad support for multiple exchanges and standardization of their APIs. An abstraction layer will be built on top of it to ensure our application's business logic is decoupled from the library itself.

---

## 3. Business Rules & Formulas

This section explicitly defines the core financial logic required for the engine to operate correctly.

### 3.1 PnL Calculation
- **Unrealized PnL (USD):** `(Current Market Price - Weighted Average Entry Price) * Total Filled Quantity` (For shorts: `(Weighted Average Entry Price - Current Market Price) * ...`)
- **Unrealized PnL (%):** `(Unrealized PnL (USD) / Total Invested USD) * 100`
- **Realized PnL (USD):** Sum of PnL from all closed trades or partially closed quantities. For a single closing trade: `(Exit Price - Entry Price) * Closed Quantity - Fees`
- **Fee Handling:** All PnL calculations must subtract exchange fees. The `ccxt` library provides fee data in order responses, which must be fetched, stored against the `DCAOrder`, and factored into `Realized PnL`.

### 3.2 Capital Allocation & Position Sizing
- **Total Capital:** A user-configurable value representing the total capital to be used by the engine (e.g., `$10,000`).
- **Max Concurrent Positions:** A user-configurable number (e.g., `10`) that the Execution Pool enforces.
- **Capital Per Position Group:** `Total Capital / Max Concurrent Positions`. This is the total capital allocated to a single `PositionGroup`.
- **Position Sizing (Per DCA Leg):** The capital for each DCA leg is determined by its `weight_percent` applied to the `Capital Per Position Group`. Example: `($1000 per group) * (20% weight for DCA0) = $200` for the first leg. The quantity is then `Leg Capital / Entry Price`.

---

## 4. Core Data Models & State Machines

### 4.1 PositionGroup Model

```python
from sqlalchemy import (Column, String, Integer, Numeric, DateTime, Boolean, JSON, ForeignKey, Enum as SQLAlchemyEnum)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Literal

# Assuming a Base declarative base is defined elsewhere
from .base import Base 

class PositionGroup(Base):
    """
    Represents a unique trading position defined by pair + timeframe.
    Contains multiple pyramids and DCA legs.
    """
    __tablename__ = "position_groups"
    
    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange = Column(String, nullable=False)  # "binance", "bybit", etc.
    symbol = Column(String, nullable=False)  # "BTCUSDT"
    timeframe = Column(Integer, nullable=False)  # in minutes (e.g., 15, 60, 240)
    side = Column(SQLAlchemyEnum("long", "short", name="position_side_enum"), nullable=False)
    
    # Status tracking
    status = Column(SQLAlchemyEnum(
        "waiting", "live", "partially_filled", "active", "closing", "closed", "failed",
        name="group_status_enum"
    ), nullable=False, default="waiting")
    
    # Pyramid tracking
    pyramid_count = Column(Integer, default=0)
    max_pyramids = Column(Integer, default=5)
    replacement_count = Column(Integer, default=0)
    
    # DCA tracking
    total_dca_legs = Column(Integer, nullable=False)
    filled_dca_legs = Column(Integer, default=0)
    
    # Financial metrics
    base_entry_price = Column(Numeric(20, 10), nullable=False)
    weighted_avg_entry = Column(Numeric(20, 10), nullable=False)
    total_invested_usd = Column(Numeric(20, 10), default=Decimal("0"))
    total_filled_quantity = Column(Numeric(20, 10), default=Decimal("0"))
    unrealized_pnl_usd = Column(Numeric(20, 10), default=Decimal("0"))
    unrealized_pnl_percent = Column(Numeric(10, 4), default=Decimal("0"))
    realized_pnl_usd = Column(Numeric(20, 10), default=Decimal("0"))
    
    # Take-profit configuration
    tp_mode = Column(SQLAlchemyEnum("per_leg", "aggregate", "hybrid", name="tp_mode_enum"), nullable=False)
    tp_aggregate_percent = Column(Numeric(10, 4))
    
    # Risk engine tracking
    risk_timer_start = Column(DateTime)
    risk_timer_expires = Column(DateTime)
    risk_eligible = Column(Boolean, default=False)
    risk_blocked = Column(Boolean, default=False)
    risk_skip_once = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Relationships
    pyramids = relationship("Pyramid", back_populates="group", cascade="all, delete-orphan")
    dca_orders = relationship("DCAOrder", back_populates="group", cascade="all, delete-orphan")
    risk_actions = relationship("RiskAction", back_populates="group", cascade="all, delete-orphan")
```

### 4.2 Pyramid Model

```python
class Pyramid(Base):
    """
    Represents a single pyramid entry within a PositionGroup.
    """
    __tablename__ = "pyramids"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_index = Column(Integer, nullable=False) # 0-4
    
    entry_price = Column(Numeric(20, 10), nullable=False)
    entry_timestamp = Column(DateTime, nullable=False)
    signal_id = Column(String) # TradingView signal ID
    
    status = Column(SQLAlchemyEnum("pending", "submitted", "filled", "cancelled", name="pyramid_status_enum"), nullable=False)
    dca_config = Column(JSON, nullable=False)
    
    group = relationship("PositionGroup", back_populates="pyramids")
    dca_orders = relationship("DCAOrder", back_populates="pyramid", cascade="all, delete-orphan")
```

### 4.3 DCAOrder Model

```python
class DCAOrder(Base):
    """
    Represents a single DCA order (limit order at specific price level).
    """
    __tablename__ = "dca_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_id = Column(UUID(as_uuid=True), ForeignKey("pyramids.id"), nullable=False)
    
    exchange_order_id = Column(String)
    leg_index = Column(Integer, nullable=False)
    
    symbol = Column(String, nullable=False)
    side = Column(SQLAlchemyEnum("buy", "sell", name="order_side_enum"), nullable=False)
    order_type = Column(SQLAlchemyEnum("limit", "market", name="order_type_enum"), default="limit")
    price = Column(Numeric(20, 10), nullable=False)
    quantity = Column(Numeric(20, 10), nullable=False)
    
    gap_percent = Column(Numeric(10, 4), nullable=False)
    weight_percent = Column(Numeric(10, 4), nullable=False)
    tp_percent = Column(Numeric(10, 4), nullable=False)
    tp_price = Column(Numeric(20, 10), nullable=False)
    
    status = Column(SQLAlchemyEnum("pending", "open", "partially_filled", "filled", "cancelled", "failed", name="order_status_enum"), nullable=False)
    filled_quantity = Column(Numeric(20, 10), default=Decimal("0"))
    avg_fill_price = Column(Numeric(20, 10))
    
    tp_hit = Column(Boolean, default=False)
    tp_order_id = Column(String)
    tp_executed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    group = relationship("PositionGroup", back_populates="dca_orders")
    pyramid = relationship("Pyramid", back_populates="dca_orders")
```

### 4.4 QueuedSignal Model

```python
class QueuedSignal(Base):
    """
    Represents a signal waiting in the queue.
    """
    __tablename__ = "queued_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(Integer, nullable=False)
    side = Column(SQLAlchemyEnum("long", "short", name="signal_side_enum"), nullable=False)
    entry_price = Column(Numeric(20, 10), nullable=False)
    signal_payload = Column(JSON, nullable=False)
    
    queued_at = Column(DateTime, default=datetime.utcnow)
    replacement_count = Column(Integer, default=0)
    priority_score = Column(Numeric(20, 4), default=0.0)
    
    is_pyramid_continuation = Column(Boolean, default=False)
    current_loss_percent = Column(Numeric(10, 4))
    
    status = Column(SQLAlchemyEnum("queued", "promoted", "cancelled", name="queue_status_enum"), nullable=False)
    promoted_at = Column(DateTime)
```

### 4.5 RiskAction Model

```python
class RiskAction(Base):
    """
    Records actions taken by the Risk Engine.
    """
    __tablename__ = "risk_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    
    action_type = Column(SQLAlchemyEnum("offset_loss", "manual_block", "manual_skip", name="risk_action_type_enum"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Details for offset_loss
    loser_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"))
    loser_pnl_usd = Column(Numeric(20, 10))
    
    # Details for winners (JSON array of {group_id, pnl_usd, quantity_closed})
    winner_details = Column(JSON)
    
    notes = Column(String)
    
    group = relationship("PositionGroup", foreign_keys=[group_id], back_populates="risk_actions")
    loser_group = relationship("PositionGroup", foreign_keys=[loser_group_id])
```

### 4.6 State Machine: PositionGroup Status

```
State Flow:
┌─────────┐
│ waiting │ (In queue, pool full)
└────┬────┘
     │ Pool slot available
     ↓
┌──────────┐
│   live   │ (Orders submitted, no fills yet)
└────┬─────┘
     │ First DCA filled
     ↓
┌──────────────────┐
│ partially_filled │ (Some DCA filled, some pending)
└────┬─────────────┘
     │ All DCA filled OR monitoring active
     ↓
┌──────────┐
│  active  │ (Full grid filled, TP monitoring running)
└────┬─────┘
     │ Exit signal OR TP hit OR Risk engine action
     ↓
┌─────────┐
│ closing │ (Exit orders being placed)
└────┬────┘
     │ All positions closed
     ↓
┌────────┐
│ closed │ (Final state, slot released)
└────────┘
```

### 4.7 State Machine: Order Status

```
Order Lifecycle:
┌─────────┐
│ pending │ (Created, not submitted)
└────┬────┘
     │ Submit to exchange
     ↓
┌──────┐
│ open │ (On exchange order book)
└──┬───┘
   │
   ├──→ partially_filled (Partial execution)
   │         │
   │         ├──→ filled (Rest filled)
   │         └──→ cancelled (User cancels)
   │
   ├──→ filled (Full execution)
   │
   └──→ cancelled (User/system cancels)
```

---

## 5. Algorithm Specifications

### 5.1 Queue Priority Calculation

```python
def calculate_queue_priority(signal: QueuedSignal, active_groups: List[PositionGroup]) -> float:
    """
    Four-tier priority system as per SoW Section 5.3:
    
    Priority 1 (Highest): Pyramid continuation of active group
    Priority 2: Deepest current loss percentage
    Priority 3: Highest replacement count
    Priority 4 (Lowest): FIFO (oldest first)
    
    Returns a composite score where higher = higher priority.
    """
    
    # Tier 1: Check if pyramid continuation
    existing_group = find_active_group(
        active_groups, 
        signal.symbol, 
        signal.timeframe
    )
    
    if existing_group:
        # Pyramid continuation - highest priority tier
        # Score: 1,000,000 + inverse age (newer = higher)
        time_in_queue = (datetime.utcnow() - signal.queued_at).total_seconds()
        return 1_000_000 + (10_000 - time_in_queue)
    
    # Tier 2: Loss percentage (higher loss = higher priority)
    # Score: 100,000 + (loss_percent * 1000)
    # Example: -8% loss = 100,000 + 8,000 = 108,000
    if signal.current_loss_percent:
        loss_score = abs(signal.current_loss_percent) * 1000
        return 100_000 + loss_score
    
    # Tier 3: Replacement count
    # Score: 10,000 + (replacement_count * 100)
    if signal.replacement_count > 0:
        return 10_000 + (signal.replacement_count * 100)
    
    # Tier 4: FIFO (oldest = highest priority in this tier)
    # Score: 1,000 + inverse timestamp
    # Earlier queued signals get higher scores
    time_in_queue = (datetime.utcnow() - signal.queued_at).total_seconds()
    fifo_score = min(time_in_queue, 999)  # Cap at 999 seconds
    return 1_000 + fifo_score


def promote_from_queue(queued_signals: List[QueuedSignal], 
                       active_groups: List[PositionGroup]) -> Optional[QueuedSignal]:
    """
    Select highest priority signal from queue.
    Pyramid continuations bypass max position limit.
    """
    if not queued_signals:
        return None
    
    # Calculate priority for all queued signals
    prioritized = [
        (signal, calculate_queue_priority(signal, active_groups))
        for signal in queued_signals
    ]
    
    # Sort by priority score (descending)
    prioritized.sort(key=lambda x: x[1], reverse=True)
    
    # Return highest priority signal
    selected_signal, priority_score = prioritized[0]
    
    logger.info(
        f"Promoting signal {selected_signal.id} "
        f"(priority: {priority_score}, "
        f"replacement_count: {selected_signal.replacement_count})"
    )
    
    return selected_signal
```

### 5.2 Risk Engine: Loser and Winner Selection

```python
def select_loser_and_winners(
    position_groups: List[PositionGroup],
    config: RiskEngineConfig
) -> Tuple[Optional[PositionGroup], List[PositionGroup], Decimal]:
    """
    Risk Engine selection logic (SoW Section 4.4 & 4.5):
    
    Loser Selection (by % loss):
    1. Highest loss percentage
    2. If tied → highest unrealized loss USD
    3. If tied → oldest trade
    
    Winner Selection (by $ profit):
    - Rank all winning positions by unrealized profit USD
    - Select up to max_winners_to_combine (default: 3)
    
    Offset Execution:
    - Calculate required_usd to cover loser
    - Close winners partially to realize that amount
    """
    
    # Filter eligible losers
    eligible_losers = []
    for pg in position_groups:
        # Must meet all conditions
        if not all([
            pg.status == "active",
            pg.pyramid_count >= 5 if config.require_full_pyramids else True,
            pg.risk_timer_expires and pg.risk_timer_expires <= datetime.utcnow(),
            pg.unrealized_pnl_percent <= config.loss_threshold_percent,
            not pg.risk_blocked,
            not pg.risk_skip_once
        ]):
            continue
        
        # Age filter (optional)
        if config.use_trade_age_filter:
            age_minutes = (datetime.utcnow() - pg.created_at).total_seconds() / 60
            if age_minutes < config.age_threshold_minutes:
                continue
        
        eligible_losers.append(pg)
    
    if not eligible_losers:
        return None, [], Decimal("0")
    
    # Sort losers by priority
    selected_loser = max(eligible_losers, key=lambda pg: (
        abs(pg.unrealized_pnl_percent),  # Primary: highest loss %
        abs(pg.unrealized_pnl_usd),      # Secondary: highest loss $
        -pg.created_at.timestamp()        # Tertiary: oldest
    ))
    
    required_usd = abs(selected_loser.unrealized_pnl_usd)
    
    # Select winners
    winning_positions = [
        pg for pg in position_groups
        if pg.status == "active" and pg.unrealized_pnl_usd > 0
    ]
    
    # Sort by USD profit (descending)
    winning_positions.sort(
        key=lambda pg: pg.unrealized_pnl_usd,
        reverse=True
    )
    
    # Take up to max_winners_to_combine
    selected_winners = winning_positions[:config.max_winners_to_combine]
    
    # Verify sufficient profit
    total_available_profit = sum(w.unrealized_pnl_usd for w in selected_winners)
    
    if total_available_profit < required_usd:
        logger.warning(
            f"Insufficient profit to cover loss. "
            f"Required: {required_usd}, Available: {total_available_profit}"
        )
        # Still return - caller decides whether to execute partial offset
    
    return selected_loser, selected_winners, required_usd


def calculate_partial_close_quantities(
    winners: List[PositionGroup],
    required_usd: Decimal,
    precision_rules: Dict
) -> List[Tuple[PositionGroup, Decimal]]:
    """
    Calculate how much to close from each winner to realize required_usd.
    
    Returns: List of (PositionGroup, quantity_to_close)
    """
    close_plan = []
    remaining_needed = required_usd
    
    for winner in winners:
        if remaining_needed <= 0:
            break
        
        # Calculate how much profit this winner can contribute
        available_profit = winner.unrealized_pnl_usd
        
        # Determine how much of this winner to close
        profit_to_take = min(available_profit, remaining_needed)
        
        # Calculate quantity to close to realize this profit
        # profit_per_unit = current_price - avg_entry
        current_price = get_current_price(winner.symbol)
        profit_per_unit = current_price - winner.weighted_avg_entry
        
        quantity_to_close = profit_to_take / profit_per_unit
        
        # Round to step size
        step_size = precision_rules[winner.symbol]["step_size"]
        quantity_to_close = round_to_step_size(quantity_to_close, step_size)
        
        # Check minimum notional
        notional_value = quantity_to_close * current_price
        min_notional = precision_rules[winner.symbol]["min_notional"]
        
        if notional_value < min_notional:
            logger.warning(
                f"Partial close for {winner.symbol} below min notional "
                f"({notional_value} < {min_notional}). Skipping."
            )
            continue
        
        close_plan.append((winner, quantity_to_close))
        remaining_needed -= profit_to_take
    
    return close_plan
```

### 5.3 Take-Profit Monitoring

```python
async def check_take_profit_conditions(
    position_group: PositionGroup,
    current_price: Decimal
) -> List[DCAOrder]:
    """
    Check TP conditions based on tp_mode.
    Returns list of DCA orders that hit their TP target.
    
    Three modes (SoW Section 2.4):
    1. per_leg: Each DCA closes independently
    2. aggregate: Entire position closes when avg entry reaches TP
    3. hybrid: Both logics run, whichever closes first
    """
    orders_to_close = []
    
    if position_group.tp_mode == "per_leg":
        # Check each filled DCA leg individually
        for order in position_group.dca_orders:
            if order.status == "filled" and not order.tp_hit:
                if is_tp_reached(order, current_price, position_group.side):
                    orders_to_close.append(order)
    
    elif position_group.tp_mode == "aggregate":
        # Check if weighted average entry reached aggregate TP
        target_price = calculate_aggregate_tp_price(
            position_group.weighted_avg_entry,
            position_group.tp_aggregate_percent,
            position_group.side
        )
        
        if is_price_beyond_target(current_price, target_price, position_group.side):
            # Close entire position
            orders_to_close = [
                order for order in position_group.dca_orders
                if order.status == "filled" and not order.tp_hit
            ]
    
    elif position_group.tp_mode == "hybrid":
        # Check both per-leg and aggregate
        # Whichever triggers first wins
        
        # Per-leg check
        per_leg_triggered = []
        for order in position_group.dca_orders:
            if order.status == "filled" and not order.tp_hit:
                if is_tp_reached(order, current_price, position_group.side):
                    per_leg_triggered.append(order)
        
        # Aggregate check
        aggregate_target = calculate_aggregate_tp_price(
            position_group.weighted_avg_entry,
            position_group.tp_aggregate_percent,
            position_group.side
        )
        aggregate_triggered = is_price_beyond_target(
            current_price, aggregate_target, position_group.side
        )
        
        if per_leg_triggered:
            # Per-leg TP hit - close those legs only
            orders_to_close = per_leg_triggered
        elif aggregate_triggered:
            # Aggregate TP hit - close entire position
            orders_to_close = [
                order for order in position_group.dca_orders
                if order.status == "filled" and not order.tp_hit
            ]
    
    return orders_to_close


def is_tp_reached(order: DCAOrder, current_price: Decimal, side: str) -> bool:
    """
    Check if current price reached the TP target for this order.
    TP is calculated from actual fill price, not original entry.
    """
    if side == "long":
        # Long: current_price >= tp_price
        return current_price >= order.tp_price
    else:
        # Short: current_price <= tp_price
        return current_price <= order.tp_price


def calculate_aggregate_tp_price(
    weighted_avg_entry: Decimal,
    tp_percent: Decimal,
    side: str
) -> Decimal:
    """
    Calculate aggregate TP price from weighted average entry.
    """
    if side == "long":
        return weighted_avg_entry * (1 + tp_percent / 100)
    else:
        return weighted_avg_entry * (1 - tp_percent / 100)
```

### 5.4 DCA Grid Calculation

```python
def calculate_dca_levels(
    base_price: Decimal,
    dca_config: List[Dict],
    side: Literal["long", "short"],
    precision_rules: Dict
) -> List[Dict]:
    """
    Calculate DCA price levels with per-layer configuration.
    
    dca_config format (SoW Section 2.3):
    [
        {"gap_percent": 0.0, "weight_percent": 20, "tp_percent": 1.0},
        {"gap_percent": -0.5, "weight_percent": 20, "tp_percent": 0.5},
        ...
    ]
    
    Returns list of:
    {
        "leg_index": 0,
        "price": Decimal("50000.00"),
        "quantity": Decimal("0.001"),
        "gap_percent": Decimal("0.0"),
        "weight_percent": Decimal("20"),
        "tp_percent": Decimal("1.0"),
        "tp_price": Decimal("50500.00")
    }
    """
    tick_size = precision_rules["tick_size"]
    step_size = precision_rules["step_size"]
    
    dca_levels = []
    
    for idx, layer in enumerate(dca_config):
        gap_percent = Decimal(str(layer["gap_percent"]))
        weight_percent = Decimal(str(layer["weight_percent"]))
        tp_percent = Decimal(str(layer["tp_percent"]))
        
        # Calculate DCA entry price
        if side == "long":
            # Long: negative gap means lower price (discount)
            dca_price = base_price * (1 + gap_percent / 100)
        else:
            # Short: negative gap means higher price
            dca_price = base_price * (1 - gap_percent / 100)
        
        # Round to tick size
        dca_price = round_to_tick_size(dca_price, tick_size)
        
        # Calculate TP price (from DCA entry, not base price)
        if side == "long":
            tp_price = dca_price * (1 + tp_percent / 100)
        else:
            tp_price = dca_price * (1 - tp_percent / 100)
        
        tp_price = round_to_tick_size(tp_price, tick_size)
        
        dca_levels.append({
            "leg_index": idx,
            "price": dca_price,
            "gap_percent": gap_percent,
            "weight_percent": weight_percent,
            "tp_percent": tp_percent,
            "tp_price": tp_price
        })
    
    return dca_levels


def calculate_order_quantities(
    dca_levels: List[Dict],
    total_capital_usd: Decimal,
    precision_rules: Dict
) -> List[Dict]:
    """
    Calculate order quantity for each DCA level based on weight allocation.
    """
    step_size = precision_rules["step_size"]
    min_qty = precision_rules["min_qty"]
    min_notional = precision_rules["min_notional"]
    
    for level in dca_levels:
        # Calculate capital for this leg
        leg_capital = total_capital_usd * (level["weight_percent"] / 100)
        
        # Calculate quantity: capital / price
        quantity = leg_capital / level["price"]
        
        # Round to step size
        quantity = round_to_step_size(quantity, step_size)
        
        # Validate minimum quantity
        if quantity < min_qty:
            raise ValidationError(
                f"Quantity {quantity} below minimum {min_qty}"
            )
        
        # Validate minimum notional
        notional = quantity * level["price"]
        if notional < min_notional:
            raise ValidationError(
                f"Notional {notional} below minimum {min_notional}"
            )
        
        level["quantity"] = quantity
    
    return dca_levels
```

---


## 6. User Journeys

### 6.1 First-Time User Onboarding
1.  **Registration/Login:** User creates an account and logs in.
2.  **Welcome Screen:** A modal or welcome page appears, guiding the user through the initial setup.
3.  **Exchange API Setup:**
    - User is prompted to navigate to the "Settings" page.
    - User selects an exchange (e.g., Binance).
    - User enters their API Key and Secret Key.
    - The application performs a connectivity and permissions check (`fetchBalance`).
    - On success, the keys are encrypted and saved. On failure, a specific error is shown (e.g., "Invalid API Key" or "Missing 'Futures Trading' permission").
4.  **Initial Configuration:** The user is guided to set critical parameters like `Total Capital` and `Max Concurrent Positions`. A "Quick Start" configuration template is provided.
5.  **Dashboard Activation:** Once the API keys and initial configuration are saved, the main dashboard becomes active, and the engine starts its monitoring loops.

### 6.2 Error Recovery UX
- **Invalid API Key:** If an API call fails with an authentication error, the system will:
    - Immediately pause all trading activity for that user.
    - Set the "Engine Status" banner to "Error: Invalid API Credentials".
    - Display a persistent notification prompting the user to update their keys in the Settings page.
    - The `PositionGroup`s will enter a `failed` state.
- **Insufficient Funds:** When placing an order, if the exchange returns an insufficient funds error:
    - The order is marked as `failed`.
    - A high-priority alert is added to the "Logs & Alerts" page.
    - The user is notified via a UI notification.
    - The system will not attempt to place further orders for that `PositionGroup`.

---

## 7. Operational Runbook & Monitoring

### 7.1 Monitoring & Alerting
- **Health Checks:** The `/api/health` endpoint will be expanded to check:
    - Database connectivity (`SELECT 1`).
    - Exchange API connectivity (pinging the exchange).
    - Background task status (e.g., is the order monitor running?).
- **Performance Benchmarks:**
    - **Webhook to Order Placement Latency:** < 500ms.
    - **API Response Time (p95):** < 200ms for all GET requests.
    - **Price Update to TP Execution Latency:** < 1 second.
- **Alerting:** An external monitoring service (like UptimeRobot or Prometheus) should be configured to poll the health check endpoint. If the endpoint returns an unhealthy status or fails to respond for > 2 minutes, an alert (e.g., email, Slack) should be triggered.

### 7.2 Data Migration & Rollbacks
- **Data Migration:** All database schema changes **must** be handled through Alembic migrations. The process is:
    1.  Generate a new migration file: `alembic revision --autogenerate -m "description"`.
    2.  Manually review and test the migration script in a staging environment.
    3.  Apply the migration during a scheduled maintenance window: `alembic upgrade head`.
- **Deployment Rollback Procedure:**
    1.  If a new deployment is found to be faulty, the previous Docker container tag should be redeployed immediately.
    2.  If a database migration was part of the faulty deployment, the corresponding `alembic downgrade` command must be run to revert the schema change. This is a critical step and requires that all migrations have a correctly implemented `downgrade` function.

---

## 8. Quality Gates & Testing Strategy

This section defines the quality assurance approach for the project, including clear gates that must be passed before moving between phases or deploying.

### 8.1 Quality Gates
Each major development phase (e.g., Backend Phase 1, Frontend Phase 1) will conclude with a Quality Gate review. To pass the gate, the following criteria must be met:
- **Code Review:** All code has been peer-reviewed and approved.
- **Unit Test Coverage:** All new code meets or exceeds the 85% unit test coverage threshold.
- **Integration Tests:** All related integration tests are passing.
- **SoW Compliance:** A check is performed to ensure all SoW requirements for that phase are met (verified against the Traceability Matrix).
- **Documentation:** All new components, services, and endpoints are documented.

### 8.2 Testing Strategy
- **Unit Testing:** `pytest` for the backend, `Jest` & `React Testing Library` for the frontend. Focuses on isolating and testing individual functions and components.
- **Integration Testing:** A dedicated `pytest` suite that runs against a Dockerized environment (app + DB + mock exchange). It tests the interactions between services (e.g., webhook ingestion to order placement).
- **Performance Testing:** A `locust.io` test suite will be created to simulate high-load scenarios, specifically:
    - High volume of incoming webhooks (100+ per minute).
    - High number of concurrent open positions (200+).
    - The test will measure API response times and PnL calculation latency under load to ensure they meet the benchmarks defined in the Operational Runbook.
- **Security Testing:**
    - **Dependency Scanning:** `pip-audit` will be integrated into the CI/CD pipeline to check for vulnerabilities in dependencies.
    - **Penetration Testing (Manual):** Before final release, a manual penetration test will be conducted focusing on:
        - SQL Injection (verifying ORM protection).
        - Cross-Site Scripting (XSS) in the frontend.
        - Insecure Direct Object References (e.g., ensuring a user cannot access another user's data via API).
- **User Acceptance Testing (UAT):** A set of test cases will be defined for end-users to perform in a staging environment. The application is considered "done" when:
    - Users can complete the entire onboarding journey without assistance.
    - Users can successfully create and monitor a position from a webhook signal.
    - The dashboard and PnL metrics correctly reflect the user's trading activity.
    - The user finds the UI intuitive and the provided documentation sufficient.

---

## 9. Configuration Templates & Troubleshooting

### 9.1 Example `.env` Configuration

```env
# --- Database ---
DATABASE_URL=postgresql://tv_user:your_password@db:5432/tv_engine_db

# --- Security ---
JWT_SECRET=a_very_strong_and_long_secret_key_for_jwt
ENCRYPTION_KEY=a_32_byte_long_secret_key_for_encrypting_api_keys

# --- Application Settings ---
LOG_LEVEL=INFO
# Set to "binance" or "bybit" to use a real exchange, or "mock" for testing
EXCHANGE_TYPE=mock 
```

### 9.2 Example User Configuration (JSON for UI Settings Panel)

```json
{
  "total_capital_usd": 10000,
  "max_open_groups": 10,
  "exchange_api": {
    "binance": {
      "api_key": "YOUR_BINANCE_API_KEY",
      "secret_key": "YOUR_BINANCE_SECRET_KEY"
    },
    "bybit": {
      "api_key": "YOUR_BYBIT_API_KEY",
      "secret_key": "YOUR_BYBIT_SECRET_KEY"
    }
  },
  "risk_engine": {
    "loss_threshold_percent": -5.0,
    "require_full_pyramids": true,
    "timer_start_condition": "after_all_dca_filled",
    "max_winners_to_combine": 3
  },
  "dca_grid_config_default": [
    {"gap_percent": 0.0, "weight_percent": 20, "tp_percent": 1.0},
    {"gap_percent": -0.5, "weight_percent": 20, "tp_percent": 0.5},
    {"gap_percent": -1.0, "weight_percent": 20, "tp_percent": 0.5},
    {"gap_percent": -2.0, "weight_percent": 20, "tp_percent": 0.5},
    {"gap_percent": -4.0, "weight_percent": 20, "tp_percent": 0.5}
  ]
}
```

### 9.3 Troubleshooting Guide

| Symptom | Possible Cause | Troubleshooting Steps |
|---|---|---|
| **500 Internal Server Error on API** | A backend programming error occurred. | 1. Check the backend logs for a Python traceback: `docker compose logs app --tail=50`. <br> 2. The traceback will point to the exact file and line causing the error. |
| **403 Forbidden Error** | Your user role does not have permission for this action. | 1. Verify your user role in the database or via the `/api/auth/me` endpoint. <br> 2. This is expected if a "trader" tries to access an admin-only page. |
| **Engine Status is "Error: Invalid API Credentials"** | The saved API key/secret for your exchange is incorrect or has expired. | 1. Go to the Settings page. <br> 2. Re-enter your API Key and Secret for the configured exchange. <br> 3. The system will re-validate them. A success message will appear, and the engine status will return to "Running". |
| **Orders are not placing, "Insufficient Funds" in logs** | The exchange reports you do not have enough capital for the trade. | 1. Check your available balance on the exchange website. <br> 2. In the Settings panel, ensure your `total_capital_usd` and `max_open_groups` are set correctly, as this determines the capital allocated per trade. |

---

## 10. Development Plan

### Backend Phase 1: Database Architecture


#### Objectives
Design and implement the complete database schema, migrations, and data access layer.

#### Steps
1.  **Implement Models (TDD):** For each model, first write a test that tries to create and save it, then implement the model to make the test pass. (✅ User model implemented)
2.  **Generate Initial Migration:** Run `alembic revision --autogenerate -m "initial_schema"`. Manually review and refine the generated script.
3.  **Create Repository Pattern:** Implement a `BaseRepository` and specific repositories (e.g., `PositionGroupRepository`) for all major models.
4.  **Configure Connection Pooling:** Set up the SQLAlchemy engine with `pool_size=20`, `max_overflow=10`.
5.  **Implement Transaction Management:** Create a dependency-injected database session that ensures `commit` on success and `rollback` on failure.
6.  **Script Backup/Restore:** Create `scripts/backup_db.sh` and `scripts/restore_db.sh`.
7.  **Add Health Check Endpoint:** Create a `/api/health/db` endpoint that performs a `SELECT 1` query.

#### Acceptance Criteria
- **Functional:** ✅ Schema supports all SoW entities. Migrations are repeatable.
- **Technical:** ✅ Connection pooling is active. Transactions auto-rollback. Indexes are on `(user_id)`, `(symbol, timeframe, status)`.
- **Test Coverage:** ✅ >90% on all repository methods.
- **Performance:** ✅ `get_by_id` < 5ms. `get_active_groups` < 20ms.
- **Error Handling:** ✅ Handles DB connection timeouts with retries.

#### Validation Checkpoint
1.  **Demo:** Run migration, insert data, show rollback, demo health check.
2.  **Review:** [ ] Schema matches models. [ ] Indexes are correct.
3.  **Quality Gate Checklist:**
    - [ ] Code Reviewed & Approved
    - [ ] Unit Test Coverage > 85%
    - [ ] SoW Requirements Met
    - [ ] Documentation Updated

### Backend Phase 2: Webhook & Signal Processing


#### Objectives
Build a secure and robust pipeline for ingesting, validating, and routing TradingView signals.

#### Steps
1.  **Implement Signature Validation:** Create a FastAPI dependency that compares a hash of the request body with a secret key.
2.  **Create Pydantic Parsers:** Define strict Pydantic models for all incoming webhook payloads to ensure type safety and validation.
3.  **Build Signal Validator Service:** Create `SignalValidatorService` to check for logical consistency (e.g., `action` matches `strategy`).
4.  **Implement Signal Router Service:** Create `SignalRouterService` that takes a validated signal and determines if it's a new group, a pyramid, or an exit, then calls the appropriate downstream service (`PositionManager`, `QueueManager`, etc.).
5.  **Add Rate Limiting:** Use a library like `slowapi` to limit incoming requests per user to prevent abuse.

#### Acceptance Criteria
- **Functional:** ✅ Only valid, signed webhooks are processed. Signals are correctly routed based on SoW logic.
- **Technical:** ✅ Pydantic models enforce payload structure. Services are decoupled and testable.
- **Test Coverage:** ✅ Unit tests for valid/invalid signatures, malformed payloads, and all routing logic paths.
- **Security:** ✅ Protected against replay attacks and unauthorized access via signature validation.

#### Validation Checkpoint
1.  **Demo:** Show valid webhook processing and invalid webhook rejection.
2.  **Review:** [ ] Signature validation is secure. [ ] All signal types are routed.
3.  **Quality Gate Checklist:**
    - [ ] Code Reviewed & Approved
    - [ ] Unit Test Coverage > 85%
    - [ ] SoW Requirements Met
    - [ ] Documentation Updated

### Phase 3: Exchange Abstraction Layer
**Duration:** 6-8 days (Week 3)
**Priority:** High

#### Objectives
Create a flexible and extensible exchange integration layer that can support multiple exchanges (Binance, Bybit initially).

#### Steps
1.  **Design `ExchangeInterface`:** Create an Abstract Base Class (ABC) with methods like `get_precision_rules`, `place_order`, `get_order_status`, `cancel_order`, `get_current_price`.
2.  **Implement `BinanceConnector`:** Implement the interface for the Binance exchange using the `ccxt` library.
3.  **Implement `BybitConnector`:** Implement the interface for the Bybit exchange.
4.  **Implement Precision Service:** Create a background service that periodically fetches and caches precision rules for all configured user exchanges.
5.  **Standardize Models:** Create internal Pydantic models for `Order`, `Fill`, `Precision` to standardize the data returned from all connectors.
6.  **Implement Error Mapping:** Create a decorator or utility to catch `ccxt` exceptions and map them to custom application exceptions like `InsufficientFundsError` or `InvalidOrderError`.

#### Acceptance Criteria
- **Functional:** ✅ The system can place orders, check status, and fetch precision on both Binance and Bybit.
- **Technical:** ✅ All exchange interactions go through the abstraction layer. Connectors are interchangeable via a factory pattern.
- **Test Coverage:** ✅ Unit tests with mock `ccxt` responses for each connector.
- **Error Handling:** ✅ Exchange-specific errors are caught and mapped to standardized application exceptions.

#### Validation Checkpoint
1.  **Demo:** Show the application fetching precision rules from both Binance and Bybit testnets. Place a test order on each exchange through the standardized interface.
2.  **Review:** [ ] The `ExchangeInterface` covers all required actions. [ ] Error handling correctly captures and standardizes common exchange errors.

### Phase 4: Order Management Service
**Duration:** 5-7 days (Week 4)
**Priority:** High

#### Objectives
Implement a robust and reliable order management system that can handle the full lifecycle of an order.

#### Steps
1.  **Implement Order Submission:** Create an `OrderService` that uses the Exchange Abstraction Layer to place orders. Include retry logic with exponential backoff for transient network errors.
2.  **Create Order Fill Monitor:** Implement a background `Task` (e.g., using `asyncio.create_task`) that periodically queries the status of all `open` or `partially_filled` orders.
3.  **Handle Partial Fills:** Update the `DCAOrder` model in the database with `filled_quantity` and `avg_fill_price` upon detecting a partial fill.
4.  **Implement Cancellation Workflow:** Add a method to `OrderService` to cancel an order on the exchange and update its status to `cancelled`.
5.  **Implement Order State Machine:** Use the `status` field on the `DCAOrder` model and ensure all state transitions are valid (e.g., `open` -> `filled`, not `pending` -> `filled`).
6.  **Implement Startup Reconciliation:** On application startup, fetch all open orders from the exchange and reconcile their status with the database.

#### Acceptance Criteria
- **Functional:** ✅ System can reliably place, monitor, and cancel orders, and correctly handle partial fills.
- **Technical:** ✅ Order states are managed by a state machine. A background task handles monitoring.
- **Test Coverage:** ✅ Unit tests for all state transitions and order operations using a mock exchange.
- **Performance:** ✅ Order status checks are batched where possible to avoid hitting API rate limits.

#### Validation Checkpoint
1.  **Demo:** Place a limit order, show it as `open`. Manually fill it on the exchange and show the monitor detecting the `filled` state. Place another order and cancel it through the service.
2.  **Review:** [ ] The state machine logic is robust. [ ] The startup reconciliation logic correctly handles discrepancies.

### Phase 5: Grid Trading Logic
**Duration:** 5-7 days (Week 5)
**Priority:** High

#### Objectives
Implement the core trading strategy, including DCA calculation, take-profit modes, and exit signals.

#### Steps
1.  **Implement `GridCalculatorService`:** Create a service to implement the logic from `4.4 DCA Grid Calculation`.
2.  **Implement Per-Layer Config Parser:** Use Pydantic to parse and validate the DCA configuration from the user settings.
3.  **Implement `TakeProfitService`:** Create a service that continuously monitors the current price for all `active` `PositionGroup`s and implements the logic from `4.3 Take-Profit Monitoring`.
4.  **Handle Fill Price:** Ensure the `TakeProfitService` calculates TP targets based on the actual `avg_fill_price` of an order, not the intended price.
5.  **Implement Exit Logic:** When an exit signal is received, the `PositionManager` will use the `OrderService` to cancel all open DCA orders and market close the current position.

#### Acceptance Criteria
- **Functional:** ✅ DCA levels are calculated correctly based on per-layer config. All three TP modes (`Per-Leg`, `Aggregate`, `Hybrid`) are implemented and functional.
- **Technical:** ✅ All financial calculations use Python's `Decimal` type for precision.
- **Test Coverage:** ✅ Unit tests for each calculation and take-profit mode with various price scenarios.
- **Performance:** ✅ TP checks for all active positions complete within the price monitoring interval (e.g., < 1 second).

#### Validation Checkpoint
1.  **Demo:** Create a position. Show the calculated DCA levels and TP prices in the logs/DB. Manually move the "current price" and show the TP service triggering a close for each of the three modes.
2.  **Review:** [ ] The logic for all three TP modes is correctly implemented as per the SoW. [ ] Edge cases like partial fills are handled in TP calculations.

### Phase 6: Execution Pool & Queue
**Duration:** 4-6 days (Week 6)
**Priority:** High

#### Objectives
Implement the system for managing concurrent positions and prioritizing incoming signals.

#### Steps
1.  **Implement `ExecutionPoolManager`:** A service that atomically checks and manages the number of active `PositionGroup`s against the `max_open_groups` setting.
2.  **Implement `QueueManagerService`:** A service that adds signals to the `QueuedSignal` table when the pool is full.
3.  **Implement Priority Calculator:** Implement the `calculate_queue_priority` function from `4.1 Algorithm Specifications`.
4.  **Implement Queue Promotion:** Create a background task that runs periodically (e.g., every 5 seconds). It gets a free slot from the pool, then calls the `QueueManagerService` to promote the highest-priority signal.
5.  **Handle Signal Replacement:** When a new signal arrives for a symbol/timeframe already in the queue, update the existing entry and increment its `replacement_count`.
6.  **Implement Queue Persistence:** Since signals are saved to the database, ensure on startup that the queue promotion task is running.

#### Acceptance Criteria
- **Functional:** ✅ The pool correctly limits active positions. Pyramids bypass the limit. The queue correctly prioritizes signals based on the four-tier system.
- **Technical:** ✅ Pool slot checks and queue promotion are atomic operations to prevent race conditions.
- **Test Coverage:** ✅ Unit tests for all pool/queue operations, especially the priority calculation logic.
- **Performance:** ✅ A queue promotion check completes in < 50ms.

#### Validation Checkpoint
1.  **Demo:** Fill the execution pool. Send a new signal and show it entering the queue. Send a higher-priority signal (e.g., for a position with a deep loss) and show it being ranked higher. Release a slot and show the highest-priority signal being promoted.
2.  **Review:** [ ] The priority calculation algorithm exactly matches the SoW. [ ] Race conditions are handled correctly.

### Phase 7: Risk Engine
**Duration:** 5-7 days (Week 7)
**Priority:** High

#### Objectives
Implement the sophisticated, multi-conditional Risk Engine to offset losing trades.

#### Steps
1.  **Implement `RiskEngineService`:** A service that runs periodically (e.g., every minute) to evaluate all `active` positions.
2.  **Implement Timer Logic:** On a `PositionGroup`, set the `risk_timer_expires` based on the three possible start conditions (`after_5_pyramids`, etc.).
3.  **Implement Selection Logic:** Implement the `select_loser_and_winners` function from `4.2 Algorithm Specifications`.
4.  **Implement Partial Close Calculator:** Implement the `calculate_partial_close_quantities` function.
5.  **Execute Offset:** The service will call the `OrderService` to place market orders to partially close the winners and fully close the loser.
6.  **Log Risk Actions:** Record every evaluation and execution in a `RiskAction` table, linking to the loser and winner `PositionGroup`s.
7.  **Implement Manual Controls:** Add API endpoints to allow the UI to set the `risk_blocked` or `risk_skip_once` flags on a `PositionGroup`.

#### Acceptance Criteria
- **Functional:** ✅ The risk engine correctly identifies and offsets losing trades based on the SoW's rules. All three timer modes are implemented.
- **Technical:** ✅ Risk engine evaluations are performed in a background task. All actions are logged for audit.
- **Test Coverage:** ✅ Unit tests for all risk conditions, timer modes, and the winner/loser selection algorithms.
- **Error Handling:** ✅ The engine is resilient to exchange errors during the closing of positions.

#### Validation Checkpoint
1.  **Demo:** Create a scenario with one clear loser and several winners. Show the risk engine timer activate. Once expired, show the engine correctly selecting the loser and winners, calculating the partial close amounts, and logging the action.
2.  **Review:** [ ] The loser/winner selection logic exactly matches the SoW. [ ] The partial close calculations are precise.


--- 

## 6. Frontend Development Plan

### Phase 1: Architecture & Foundation
**Duration:** 5-7 days (Week 8)
**Priority:** Critical (Blocks all other phases)

#### Objectives
Set up a modern, scalable, and maintainable frontend architecture.

#### Steps
1.  **Initialize Project:** Use `create-react-app` with the TypeScript template.
2.  **Install Core Libraries:** Add `react-router-dom`, `axios`, `zustand` (for state management), `@mui/material`, `@emotion/react`, `@emotion/styled`.
3.  **Set up Folder Structure:** Create a standard folder structure: `/components`, `/pages`, `/hooks`, `/services`, `/state`, `/theme`.
4.  **Implement State Management:** Set up a Zustand store for global state (User, Auth Token, System Status).
5.  **Configure API Client:** Create an `axios` instance in `/services/api.js` with interceptors to automatically add the JWT `Authorization` header to requests and handle 401/403 errors globally.
6.  **Implement Routing:** Set up `react-router-dom` with protected routes that require authentication.
7.  **Create Theme:** Define a Material UI theme in `/theme/theme.js` with the application's color palette, typography, and component overrides.
8.  **Implement WebSocket Manager:** Create a `/services/websocket.js` service to manage the WebSocket connection, including automatic reconnection logic.

#### Acceptance Criteria
- **Functional:** ✅ A user can log in, the JWT is stored, and subsequent API calls are authenticated. Protected routes are inaccessible to logged-out users.
- **Technical:** ✅ Zustand is used for global state. Axios interceptors handle auth headers and errors. A central theme file controls all styling.
- **Test Coverage:** ✅ Unit tests for the auth hook (`useAuth`), protected route component, and Zustand store actions.
- **Performance:** ✅ Initial app load time is < 2 seconds.

#### Validation Checkpoint
1.  **Demo:** Log in and show the JWT being stored in local storage/Zustand. Navigate to a protected page. Show the auth header being sent in the network tab. Log out and show redirection to the login page.
2.  **Review:** [ ] The folder structure is logical. [ ] The state management approach is sound. [ ] The API client correctly handles auth.

### Phase 2: UI Components & Views
**Duration:** 15-20 days (Weeks 9-11)
**Priority:** High

#### Objectives
Build all the UI components and pages specified in the SoW with a focus on clarity, usability, and real-time data display.

#### Steps
1.  **Implement Layout:** Create a `MainLayout` component with the sidebar, header, and content area.
2.  **Build Dashboard Page:** Implement the `DashboardPage` with all widgets (PnL, Pool Usage, etc.) using static data initially.
3.  **Build Positions Page:** Implement the `PositionsPage` with the main data grid and the expandable row view for DCA legs. Use a library like `MUI X Data Grid`.
4.  **Build Risk Engine & Queue Pages:** Implement the dedicated pages for the Risk Engine and Waiting Queue, including their respective data tables and action buttons.
5.  **Build Settings Page:** Implement the `SettingsPage` with tabbed navigation for each configuration section. Use a form library like `react-hook-form` for validation.
6.  **Build Logs Page:** Implement the `SystemLogsPage` with filtering, search, and auto-scrolling capabilities.
7.  **Connect to Real-time Data:** Refactor all pages to subscribe to the WebSocket service and the Zustand store for live data updates, removing static data.

#### Acceptance Criteria
- **Functional:** ✅ All pages and components from the SoW are implemented. Data updates in real-time without requiring a page refresh.
- **Technical:** ✅ Components are reusable and follow best practices. State is managed efficiently.
- **Test Coverage:** ✅ Jest/React Testing Library tests for each major component to verify rendering and basic interactions.
- **Performance:** ✅ The UI remains responsive even with 100+ positions and a high frequency of WebSocket messages.

#### Validation Checkpoint
1.  **Demo:** Showcase each page of the application. Demonstrate real-time updates by changing data in the database and having it reflect instantly on the Positions page. Show form validation on the Settings page.
2.  **Review:** [ ] The UI matches the SoW requirements. [ ] The component hierarchy is logical. [ ] Real-time data handling is efficient.

---

## 7. Cross-Cutting Phases

### Phase 1: Integration Testing
**Duration:** 7-10 days (Week 11)
**Priority:** High

#### Objectives
Build a suite of end-to-end tests to verify that the entire application works together as expected.

#### Steps
1.  **Set up Test Environment:** Use `docker-compose` to create an isolated test environment with the app, a test database, and a mock exchange server.
2.  **Write Test Scenarios:** Use `pytest` to write integration tests that simulate user actions and API calls.
3.  **Test Full Signal Flow:** Create a test that sends a webhook and verifies that a `PositionGroup` and `DCAOrder`s are created correctly in the database.
4.  **Test Risk Engine Flow:** Create a test that sets up a losing and winning position, waits for the risk engine to trigger, and verifies that the correct offsetting trades are executed via the mock exchange.
5.  **Test Queue Promotion Flow:** Create a test that fills the execution pool, queues a signal, releases a slot, and verifies the signal is promoted and executed.
6.  **Test Recovery:** Create a test that starts a trade, crashes the application, restarts it, and verifies that the system correctly reconciles the state of the trade.

#### Acceptance Criteria
- **Functional:** ✅ The main user flows (trading, risk management, queueing) are tested end-to-end.
- **Technical:** ✅ Tests run in an isolated, repeatable Docker environment.
- **Test Coverage:** ✅ At least one end-to-end test for each major feature described in the SoW.

#### Validation Checkpoint
1.  **Demo:** Run the entire `pytest` integration suite and show all tests passing.
2.  **Review:** [ ] The test scenarios cover the most critical and complex workflows. [ ] The mock exchange is sufficient to simulate real-world conditions.

### Phase 2: Security & Error Handling
**Duration:** 5-7 days (Week 12)
**Priority:** Critical

#### Objectives
Harden the application against common vulnerabilities and ensure it handles errors gracefully.

#### Steps
1.  **Implement Encryption:** Use a library like `cryptography` to encrypt all user API keys stored in the database.
2.  **Implement Role-Based Access Control (RBAC):** Create FastAPI dependencies that check the user's role (from the JWT) and restrict access to admin-only endpoints (e.g., system-wide settings, user management).
3.  **Implement Global Exception Handler:** Create a FastAPI middleware to catch all unhandled exceptions and return a standardized JSON error response, logging the full traceback.
4.  **Implement Circuit Breaker:** Wrap critical external calls (e.g., to the exchange) in a circuit breaker pattern to prevent cascading failures.
5.  **Perform Dependency Audit:** Use a tool like `pip-audit` to scan for known vulnerabilities in dependencies.

#### Acceptance Criteria
- **Functional:** ✅ Sensitive data is encrypted at rest. Users can only access endpoints permitted by their role.
- **Technical:** ✅ A central middleware handles all exceptions. The circuit breaker prevents repeated calls to a failing service.
- **Security:** ✅ No known high-severity vulnerabilities in dependencies. Application is protected against basic SQL injection (via ORM) and unauthorized access.

#### Validation Checkpoint
1.  **Demo:** Show an encrypted API key in the database. Try to access an admin endpoint as a non-admin user and show the 403 Forbidden error. Trigger an unhandled exception and show the standardized 500 error response.
2.  **Review:** [ ] The encryption method is strong. [ ] The RBAC logic is correctly applied to all relevant endpoints.

### Phase 3: Deployment & Packaging
**Duration:** 5-7 days (Week 12)
**Priority:** High

#### Objectives
Package the application into self-contained, distributable installers for Windows and macOS.

#### Steps
1.  **Create Build Scripts:** Use a tool like PyInstaller to create a single executable file that bundles the Python backend.
2.  **Package Frontend:** Build the static React frontend and configure the backend (e.g., using `StaticFiles`) to serve it.
3.  **Create Windows Installer:** Use a tool like Inno Setup to create a `.exe` installer for Windows.
4.  **Create macOS Installer:** Use a tool like `dmgbuild` to create a `.dmg` file for macOS.
5.  **Implement Update Mechanism:** Integrate a library or service that can check for new application versions and prompt the user to update.
6.  **Set up Production Monitoring:** Configure logging to a file and document how to set up external monitoring tools to watch the application's health.

#### Acceptance Criteria
- **Functional:** ✅ The application can be installed and run on clean Windows and macOS machines without manual dependency installation.
- **Technical:** ✅ The final output is a single `.exe` for Windows and a `.dmg` for macOS.
- **Performance:** ✅ The packaged application starts within 10 seconds.

#### Validation Checkpoint
1.  **Demo:** Run the installer on a clean Windows VM and a clean macOS machine. Launch the application and verify it is fully functional.
2.  **Review:** [ ] The build scripts are reliable and documented. [ ] The update mechanism is user-friendly.

### Phase 4: Documentation
**Duration:** 4-5 days (Week 13)
**Priority:** Medium

#### Objectives
Create clear, comprehensive documentation for both end-users and developers.

#### Steps
1.  **Write User Guide:** Create a user guide that covers installation, configuration of every setting in the UI, and basic troubleshooting steps.
2.  **Write Developer Guide:** Update the `README.md` to include detailed instructions for setting up a development environment, running tests, and building the project.
3.  **Document API:** Generate OpenAPI (Swagger) documentation for the REST API automatically from the FastAPI code.
4.  **Document Architecture:** Create a high-level architecture diagram and document the key design decisions in a `/docs` folder.

#### Acceptance Criteria
- **Functional:** ✅ A non-technical user can install and configure the application using the guide. A new developer can set up and run the project.
- **Technical:** ✅ The API documentation is automatically generated and always in sync with the code.

#### Validation Checkpoint
1.  **Demo:** Showcase the User Guide, the updated `README.md`, and the live Swagger UI for the API.
2.  **Review:** [ ] The documentation is clear, concise, and covers all major aspects of the application.

---

## 8. SoW Traceability Matrix

| SoW Section | SoW Requirement | Execution Plan Phase |
|-------------|-----------------|----------------------|
| 2.1         | TradingView Webhook Ingestion | Backend Phase 2      |
| 2.2         | First signal creates Position Group | Backend Phase 2      |
| 2.2         | Pyramids don't create new positions | Backend Phase 6      |
| 2.3         | DCA per-layer configuration | Backend Phase 5      |
| 2.4         | Take-Profit Modes (Per-Leg, Aggregate, Hybrid) | Backend Phase 5      |
| 2.5         | Exit Logic (Market Close) | Backend Phase 5      |
| 3           | Exchange Integration (Binance, Bybit) | Backend Phase 3      |
| 3.1         | Precision Validation | Backend Phase 3      |
| 4           | Risk Engine (Timer, Selection, Offset) | Backend Phase 7      |
| 5           | Execution Pool & Queue (Priority, Limits) | Backend Phase 6      |
| 6           | Order Management (Placement, Monitoring, Fills) | Backend Phase 4      |
| 7           | UI - Live Dashboard | Frontend Phase 2     |
| 7           | UI - Positions & Pyramids View | Frontend Phase 2     |
| 7           | UI - Risk Engine Panel | Frontend Phase 2     |
| 7           | UI - Waiting Queue View | Frontend Phase 2     |
| 7           | UI - Logs & Alerts | Frontend Phase 2     |
| 7           | UI - Settings Panel | Frontend Phase 2     |
| 7           | UI - Performance & Portfolio Dashboard | Frontend Phase 2     |
| 8           | Real-time Data Synchronization | Frontend Phase 2     |
| 9           | Authentication & Authorization | Frontend Phase 1, Cross-Cutting Phase 2 |
| 10          | Configuration Management | Cross-Cutting Phase 3 |
| 11          | Logging & Monitoring | Cross-Cutting Phase 1, 2 |
| 12          | Error Handling & Recovery | Cross-Cutting Phase 2 |
| 13          | Deployment & Packaging (Windows, macOS) | Cross-Cutting Phase 3 |
| 14          | Documentation (User, Developer, API) | Cross-Cutting Phase 4 |
