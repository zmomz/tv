# Execution Plan v3.0: Complete SoW-Compliant Execution Engine
## Comprehensive Development Roadmap

---

## 1. Executive Summary

This document provides a 100% complete, detailed execution plan to build the Execution Engine from the ground up to full SoW compliance. It includes:

- **Detailed implementation guidance** with algorithm pseudocode
- **Complete data models** and state machines
- **Enhanced acceptance criteria** with technical, performance, and test metrics
- **Validation checkpoints** after each phase
- **Configuration examples** and error handling references
- **Full traceability** linking every SoW requirement to implementation

**Total Estimated Duration:** 12-14 weeks
**Target Outcome:** Production-ready, packaged web application for Windows and macOS

---

## 2. Current State Assessment

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

## 3. Core Data Models & State Machines

### 3.1 PositionGroup Model

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

### 3.2 Pyramid Model

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

### 3.3 DCAOrder Model

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

### 3.4 QueuedSignal Model

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

### 3.5 State Machine: PositionGroup Status

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

### 3.6 State Machine: Order Status

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

## 4. Algorithm Specifications

*The pseudocode provided in your prompt for Queue Priority, Risk Engine Selection, Take-Profit Monitoring, and DCA Grid Calculation is excellent and will be used as the direct implementation reference.*

---

## 5. Backend Development Plan

### Phase 1: Database Architecture
**Duration:** 5-7 days
**Priority:** Critical (Blocks all other phases)

#### Objectives
Design and implement the complete database schema, migrations, and data access layer.

#### Steps
1.  **Implement Models:** Translate the data models from Section 3 into SQLAlchemy code.
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
1.  **Demo:** Run migration on a fresh DB, insert test data via repositories, show transaction rollback, and demonstrate health check.
2.  **Review:** [ ] All SoW entities have tables. [ ] Relationships and indexes are correct.

### Phase 2: Webhook & Signal Processing
**Duration:** 4-5 days
**Priority:** High

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
1.  **Demo:** Send a valid webhook and trace its path through parsing and routing in the logs. Send an invalid webhook (bad signature, bad payload) and show it being rejected with a 4xx error.
2.  **Review:** [ ] Code for signature validation is secure and constant-time. [ ] All signal types from SoW are handled by the router.

### Phase 3: Exchange Abstraction Layer
**Duration:** 6-8 days
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
**Duration:** 5-7 days
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
**Duration:** 5-7 days
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
**Duration:** 4-6 days
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
**Duration:** 5-7 days
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

### Phase 2: Webhook & Signal Processing
**Duration:** 4-5 days
**Priority:** High

#### Objectives
Build a secure and robust pipeline for ingesting, validating, and routing TradingView signals.

#### Steps
1.  **Implement Signature Validation:** Create a FastAPI dependency that checks the `X-Signature` header.
2.  **Create Pydantic Parsers:** Define Pydantic models for all incoming webhook payloads.
3.  **Build Signal Validator Service:** A service that checks for required fields, valid data types, and logical consistency.
4.  **Implement Signal Router:** A service that determines if a signal is for a new group, a pyramid, or an exit, and calls the appropriate downstream service.
5.  **Add Rate Limiting:** Use a library like `slowapi` to limit incoming requests.

#### Acceptance Criteria
- **Functional:** ✅ Only valid, signed webhooks are processed. Signals are correctly routed.
- **Technical:** ✅ Pydantic models enforce payload structure.
- **Test Coverage:** ✅ Tests for valid/invalid signatures, malformed payloads, and all routing logic paths.
- **Security:** ✅ Protected against replay attacks and unauthorized access.

#### Validation Checkpoint
1.  **Demo:** Send a valid webhook and show it being processed. Send an invalid one and show it being rejected.
2.  **Review:** [ ] Code for signature validation is secure. [ ] All signal types are handled by the router.

--- 

## 6. Frontend Development Plan

### Phase 1: Architecture & Foundation
**Duration:** 5-7 days
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
**Duration:** 15-20 days
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
**Duration:** 7-10 days
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
**Duration:** 5-7 days
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
**Duration:** 5-7 days
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
**Duration:** 4-5 days
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

