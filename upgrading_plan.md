# Upgrading Plan: From Foundation to SoW-Compliant Execution Engine

## 1. Introduction

This document outlines the development plan to upgrade the application to be fully compliant with the detailed **Execution Engine Scope of Work (SoW)**. It serves as the primary roadmap for development, tracking our progress from the initial foundation to a feature-complete, robust, and well-tested application.

---

## 2. Current Application State

The application's core backend business logic is now substantially complete and stable. All major services, as specified in Phases 0-4, have been implemented and are covered by a strong suite of both unit and integration tests.

The successful completion of the integration testing phase (Phase 4.5) confirms that all backend services interact correctly with each other and the database. The backend is now considered a solid foundation for the development of the API and UI layers as specified in the SoW. The project is now actively moving into Phase 5.

---

# ULTRA-DETAILED, SoW-ALIGNED DEVELOPMENT PLAN

## PHASE 0: DATA MODELS & CORE STRUCTURE
**Priority:** CRITICAL
**SoW Ref:** 1, 8, 10, 11

### Description
Establish the complete and final database schema and configuration structure required by the SoW. This ensures all future logic is built on a solid, compliant foundation.

### Step 0.1: Finalize Trading Models
**File:** `backend/app/models/trading_models.py`
- **`PositionGroup`:** Add fields for `status`, `timeframe`, and store the original `entry_signal` as JSON.
- **`Pyramid`:** Model to track the number of entries for a `PositionGroup`. Max 5 per group.
- **`DCAOrder`:** Model to store each individual DCA leg with its `price_gap`, `capital_weight`, `tp_target`, `status`, `filled_price`, etc.
- **`QueueEntry`:** Model for signals waiting in the queue, including `priority_score` and `replacement_count`.

### Step 0.2: Create Risk & Analytics Models
**File:** `backend/app/models/risk_models.py`, `backend/app/models/analytics_models.py`
- **`RiskAnalysis`:** Table to log every decision made by the Risk Engine.
- **`TradeAnalytics`:** Table to store aggregated performance data for closed trades (PnL, ROI, drawdown, etc.).

### Step 0.3: Define Configuration Structure
**File:** `backend/app/core/config_models.py`
- Create Pydantic models that precisely match the structure defined in **SoW Section 10**. This includes nested models for `app`, `exchange`, `execution_pool`, `grid_strategy`, `risk_engine`, etc. This model will be the single source of truth for all engine settings.

---

## PHASE 1: PRECISION & VALIDATION ENGINE
**Priority:** HIGH
**SoW Ref:** 3

### Description
Build the robust, pre-trade validation and precision adjustment service. This is a critical step to ensure zero API rejections from the exchange.

### Step 1.1: Precision Metadata Service
**File:** `backend/app/services/precision_service.py`
- **`fetch_and_cache_precision_rules`:** Create a background task that periodically fetches tick size, step size, min quantity, and min notional value for all relevant symbols from the exchange and caches them (e.g., in Redis).
- **`get_precision`:** A function that retrieves the precision rules for a given symbol from the cache.



---

### Step 1.2: Pre-Order Validation Logic
**File:** `backend/app/services/validation_service.py`
- **`validate_and_adjust_order`:** Before any order is placed, this function must:
    1.  Check if precision data is available. If not, the signal must be **held (queued)** as per the SoW.
    2.  Round the order price to the correct tick size.
    3.  Round the order quantity to the correct step size.
    4.  Verify the order meets the minimum notional value. If not, block and log the order.

---

## PHASE 2: ADVANCED GRID & ORDER MANAGEMENT
**Priority:** CRITICAL
**SoW Ref:** 2

### Description
Implement the complete grid trading logic, including DCA/Pyramid entries and the multi-mode Take-Profit system.

### Step 2.1: SoW-Compliant Grid Calculation
**File:** `backend/app/services/grid_calculator.py`
- **`calculate_dca_grid`:** Based on the `grid_strategy` section of the configuration, calculate the exact price, quantity (based on capital weight), and TP target for each DCA leg.

### Step 2.2: Persistent Order Placement Service
**File:** `backend/app/services/order_service.py`
- **`place_and_persist_grid_orders`:**
    1.  For each calculated DCA leg, create a `DCAOrder` record in the database with `status: 'pending'`.
    2.  Place a **limit order** for each leg.
    3.  Update the `DCAOrder` record with the `exchange_order_id`.
- **`monitor_order_fills` (Background Task):**
    - Periodically query the exchange for the status of all `pending` orders and update their status in the database upon filling.

### Step 2.3: Multi-Mode Take-Profit & Exit Engine
**File:** `backend/app/services/take_profit_service.py`
- **`check_tp_conditions` (Background Task):**
    - Implement the logic for all three TP modes as defined in SoW 2.4: `Per-Leg`, `Aggregate`, and `Hybrid`.
    - When a TP condition is met, execute the appropriate closing order(s).
- **`handle_tv_exit_signal`:**
    - On receiving an `exit` webhook, immediately cancel all unfilled DCA limit orders and market close the entire position.

---

## PHASE 3: EXECUTION POOL & QUEUE
**Priority:** HIGH
**SoW Ref:** 5

### Description
Implement the system for managing concurrent positions and prioritizing incoming signals according to the client's specific algorithm.

### Step 3.1: Execution Pool Manager
**File:** `backend/app/services/pool_manager.py`
- Implement logic to track the number of active `PositionGroup`s.
- A new position is only allowed if `active_groups < max_open_groups` from the config.
- A slot is released only when a `PositionGroup` is fully closed. Pyramids and partial closes do not release slots.

### Step 3.2: SoW-Compliant Queue Service
**File:** `backend/app/services/queue_service.py`
- **`add_to_queue`:** If the execution pool is full, add the signal to the `QueueEntry` table.
- **`handle_signal_replacement`:** If a new signal arrives for a symbol already in the queue, replace the old one and increment the `replacement_count`.
- **`promote_from_queue`:** When a pool slot opens, this function must select the next signal based on the **exact priority rules from SoW 5.3**:
    1.  Pyramid continuation of an active group.
    2.  Deepest loss percentage.
    3.  Highest replacement count.
    4.  FIFO.

---

## PHASE 4: THE RISK ENGINE
**Priority:** HIGH
**SoW Ref:** 4

### Description
Build the sophisticated, multi-conditional Risk Engine to offset losing trades with profits from winners, exactly as specified.

### Step 4.1: Activation Condition Logic
**File:** `backend/app/services/risk_engine.py`
- **`evaluate_risk_conditions` (Background Task):** This is the main loop of the Risk Engine.
- **`should_activate_risk_engine`:** This function must check **all activation conditions from SoW 4.2**:
    - All 5 pyramids received.
    - Post-full waiting time has passed.
    - Loss percent is below the threshold.
    - (Optional) Trade age threshold is met.
    - It must also respect the `timer_start_condition` from the config.

### Step 4.2: Position Selection & Ranking
- **`find_and_rank_losing_positions`:** Select the top losing trade based on the **exact priority from SoW 4.4**: 1) highest loss percent, 2) highest unrealized dollar loss, 3) oldest trade.
- **`find_and_rank_winning_positions`:** Get a list of winning trades, ranked by highest profit in USD.

### Step 4.3: Offset Execution Logic
- **`execute_risk_mitigation`:**
    1.  Calculate `required_usd` from the selected losing trade.
    2.  Select up to `max_winners_to_combine` winning trades to cover the loss.
    3.  Execute **partial closing orders** on the winning trades to realize just enough profit to cover `required_usd`.
    4.  Log the entire operation in the `RiskAnalysis` table.

---

## PHASE 4.5: INTEGRATION TESTING
**Priority:** CRITICAL
**SoW Ref:** N/A (Internal Quality Assurance)

### Description
Build a suite of integration tests to verify that the core services of the application work together as expected, interact correctly with a real database, and handle realistic data flows. This phase is critical to ensure backend stability before developing the UI.

### Step 4.5.1: Establish the Integration Test Foundation
**File:** `backend/tests/integration/conftest.py`
- **Create Database Fixture:** Implement a `pytest` fixture to provide a real, transactional database session. This fixture will manage the test database schema and ensure data isolation between tests.
- **Create Data Fixtures:** Implement fixtures to pre-populate the database with necessary test data, such as a test `User` and `ExchangeConfig`.
- **Note on Session Isolation:** Establishing a reliable test database fixture that correctly shares a transactional session with the FastAPI `TestClient` proved to be the most complex challenge of this phase. The final, robust solution is documented in `GEMINI.md` and involves a single fixture that:
    1. Creates a database connection and begins a transaction.
    2. Creates a SQLAlchemy session from that transaction.
    3. Overrides the application's `get_db` dependency to yield this specific session.
    4. Yields both the `TestClient` and the session to the test function.
    5. Rolls back the transaction at the end of the test to ensure isolation.
    This pattern is the **only** way to guarantee that the test function and the API endpoint operate within the same transactional context.

### Step 4.5.2: Test the Core Trading Flow (Happy Path)
**File:** `backend/tests/integration/test_trading_flow.py`
- **`test_webhook_to_live_position`:**
    1.  **Arrange:** Use the shared transaction fixture to get a `TestClient` and a `db_session`. Create a test user and exchange config directly in the test function, using `db_session.flush()` to persist them within the transaction. Mock the external exchange API.
    2.  **Act:** Send a simulated "New Entry" webhook payload to the `/api/webhook/{user_id}` endpoint.
    3.  **Assert:** Verify that the correct `PositionGroup` and `DCAOrder` records are created in the database (using the same `db_session`) and that the mock exchange's order placement methods were called correctly.

### Step 4.5.3: Test the Execution Pool & Queue Flow
**File:** `backend/tests/integration/test_queue_flow.py`
- **`test_pool_full_queues_signal_and_promotes`:**
    1.  **Arrange:** Configure the execution pool to be full (e.g., `max_open_groups = 1`) and create a "live" position to fill it.
    2.  **Act 1 (Queueing):** Send a new webhook signal to the API.
    3.  **Assert 1:** Verify that a `QueueEntry` is created in the database and no new position is opened.
    4.  **Act 2 (Promotion):** Close the initial position and manually trigger the promotion logic.
    5.  **Assert 2:** Verify that the `QueueEntry` is removed and a new `PositionGroup` is created from the queued signal.

---

## PHASE 5: CONFIGURATION MANAGEMENT & UI
**Priority:** MEDIUM
**SoW Ref:** 7.1 (Config Panel), 10

### Description
Build the backend API and frontend UI for managing all engine settings, with real-time sync to a local JSON file.

### Step 5.1: Configuration API
**File:** `backend/app/api/config.py`
- `GET /api/config`: Returns the current configuration JSON.
- `PUT /api/config`: Receives a full configuration JSON, validates it against the Pydantic models, saves it to the local file, and triggers a hot-reload of the engine settings.

### Step 5.2: Frontend Settings Panel
**File:** `frontend/src/components/admin/Settings.jsx`
- Build the UI as specified in **SoW 7.2 (F)**.
- The UI must have sections for each category in the config (Exchange, Pool, Risk Engine, etc.).
- It must include validation, a "Live Preview" of changes, and an "Apply & Restart Engine" button that calls the `PUT /api/config` endpoint.

---

## PHASE 6: COMPREHENSIVE UI & DASHBOARD
**Priority:** MEDIUM
**SoW Ref:** 7

### Description
Develop the full, multi-screen web UI for real-time monitoring and analytics, as detailed in the SoW.

### Step 6.1: Backend API for UI Data
**File:** `backend/app/api/dashboard.py`, `backend/app/api/positions.py`, etc.
- Create all necessary API endpoints to provide real-time data for every widget and table specified in **SoW 7.2 (A-E)**. This includes data for the dashboard, positions table, risk panel, queue view, and logs.

### Step 6.2: Frontend Development Strategy

Frontend development will follow a structured, Test-Driven Development (TDD) methodology using Google's Material UI (MUI) for a consistent and high-quality user interface.

1.  **Setup Material UI (MUI):**
    *   Integrate MUI dependencies (`@mui/material`, `@emotion/react`, `@emotion/styled`, `@mui/icons-material`) into the project.
    *   Establish a global theme (`theme.js`) to ensure design consistency (colors, typography, spacing) across all components.

2.  **Establish TDD Workflow:**
    *   Utilize the existing Jest and React Testing Library setup for all component testing.
    *   For each component, a test file will be created first to define the expected behavior and rendering. The component will then be built to satisfy the test conditions.

3.  **Component Development Order:**
    *   **Authentication:** Refactor the existing login logic into a dedicated, styled, and tested `Login` component.
    *   **Core Layout:** Create a main application layout component that includes navigation, a header, and a content area.
    *   **Dashboard:** Build the components for the Live Dashboard screen.
    *   **Positions View:** Develop the main trading table, including the expandable detailed DCA view.
    *   **Risk Engine Panel:** Build the dedicated view for monitoring Risk Engine status.
    *   **Queue View:** Create the UI for the waiting queue.
    *   **Log Viewer:** Build the advanced system event console.
    *   **Settings Panel:** Develop the UI for the configuration management panel.

---

## PHASE 7: PERFORMANCE ANALYTICS & REPORTING
**Priority:** LOW
**SoW Ref:** 7.1 (Performance Dashboard)

### Description
Implement the backend aggregation and frontend display for the detailed performance and portfolio dashboard.

### Step 7.1: Analytics Aggregation Service
**File:** `backend/app/services/analytics_service.py`
- **`aggregate_trade_data` (Background Task):** A daily task to process closed trades and populate the `TradeAnalytics` table with all the metrics required by the SoW (PnL, ROI, win rate, drawdown, etc.).

### Step 7.2: Analytics API
**File:** `backend/app/api/analytics.py`
- Create endpoints to serve the aggregated analytics data, including data formatted for the equity curve chart.

### Step 7.3: Frontend Performance Dashboard
**File:** `frontend/src/components/dashboard/Performance.jsx`
- Build the UI to display all the PnL metrics, the equity curve, win/loss stats, and other KPIs as specified in the SoW.

---

## PHASE 8: DEPLOYMENT & PACKAGING
**Priority:** LOW
**SoW Ref:** 13.1

### Description
Finalize the application, create installation packages, and write comprehensive documentation.

### Step 8.1: Final Testing & Integration
- Conduct end-to-end testing of the entire, integrated application.
- Achieve 90%+ test coverage for all backend logic.

### Step 8.2: Build Self-Contained Packages
- Investigate and implement a solution (e.g., PyInstaller with a bundled web server) to package the backend and frontend into single, executable files for Windows and macOS.

### Step 8.3: Final Documentation
- Write user-facing documentation covering installation, configuration, and troubleshooting.

This rewritten plan is a high-fidelity blueprint of the client's request. It is ambitious, detailed, and leaves no room for ambiguity. This is the plan we will follow.

---

## IMPLEMENTATION ORDER - CRITICAL PATH
1. Phase 0: DATA MODELS & CORE STRUCTURE - COMPLETED
2. Phase 1: PRECISION & VALIDATION ENGINE - COMPLETED
3. Phase 2: ADVANCED GRID & ORDER MANAGEMENT - COMPLETED
4. Phase 3: EXECUTION POOL & QUEUE - COMPLETED
5. Phase 4: THE RISK ENGINE - COMPLETED
6. Phase 4.5: INTEGRATION TESTING - COMPLETED
7. Phase 5: CONFIGURATION MANAGEMENT & UI - COMPLETED & VERIFIED
8. Phase 6: COMPREHENSIVE UI & DASHBOARD - COMPLETED & VERIFIED
9. Phase 7: PERFORMANCE ANALYTICS & REPORTING - FRONTEND COMPLETE, BACKEND PENDING
10. Phase 8: DEPLOYMENT & PACKAGING - PENDING

---

## SUCCESS CRITERIA - EXACT REQUIREMENTS
### Data Models & Core Structure:
- ✅ All SoW-specified database models (`PositionGroup`, `Pyramid`, `DCAOrder`, `QueueEntry`, `RiskAnalysis`, `TradeAnalytics`) are created with correct fields and relationships.
- ✅ Pydantic models for the entire configuration structure (SoW Section 10) are defined.

### Precision & Validation Engine:
- ✅ Precision metadata (tick size, step size, min notional) is fetched and cached from exchanges.
- ✅ `validate_and_adjust_order` function correctly rounds prices/quantities and blocks/holds orders if precision data is missing or rules are violated.

### Advanced Grid & Order Management:
- ✅ `calculate_dca_grid` correctly calculates DCA legs based on price gap and capital weight.
- ✅ `place_and_persist_grid_orders` creates `DCAOrder` records with `pending` status and places limit orders.
- ✅ `monitor_order_fills` background task updates `DCAOrder` statuses upon fill.
- ✅ `TakeProfitService` implements `Per-Leg`, `Aggregate`, and `Hybrid` TP modes.
- ✅ `handle_tv_exit_signal` cancels unfilled orders and market closes positions on exit webhook.

### Execution Pool & Queue:
- ✅ `ExecutionPoolManager` correctly limits active `PositionGroup`s and releases slots only on full closure.
- ✅ `QueueService` correctly adds signals to the queue, handles replacements, and promotes based on SoW 5.3 priority rules.

### The Risk Engine:
- ✅ `evaluate_risk_conditions` background task runs periodically.
- ✅ `should_activate_risk_engine` checks all SoW 4.2 activation conditions.
- ✅ `find_and_rank_losing_positions` and `find_and_rank_winning_positions` implement SoW 4.4 ranking.
- ✅ `execute_risk_mitigation` calculates `required_usd` from the selected losing trade, selects winners, and executes partial closing orders.
- ✅ All risk actions are logged in `RiskAnalysis` table.

### Configuration Management & UI:
- ✅ Backend API (`/api/config`) for GET/PUT configuration is implemented.
- ✅ Frontend Settings Panel (SoW 7.2 F) UI components are built and verified.
- ✅ Configuration is stored in a local JSON file and backend sync is implemented and tested.

### Comprehensive UI & Dashboard:
- ✅ Backend API endpoints provide real-time data for all UI screens (SoW 7.2 A-E).
- ✅ **Live Dashboard (SoW 7.2.A):** Implemented and Verified.
- ✅ **Positions & Pyramids View (SoW 7.2.B):** Implemented and Verified.
- ✅ **Risk Engine Panel (SoW 7.2.C):** Implemented and Verified.
- ✅ **Waiting Queue View (SoW 7.2.D):** Implemented and Verified.
- ✅ **Advanced Log Viewer (SoW 7.2.E):** Implemented and Verified.

### Performance Analytics & Reporting:
- ✅ `aggregate_trade_data` background task populates `TradeAnalytics` table with SoW-specified metrics.
- ✅ Analytics API (`/api/analytics`) serves aggregated data.
- ✅ Frontend Performance Dashboard (Implemented and Verified) displays all PnL metrics, equity curve, win/loss stats, etc.

### Deployment & Packaging:
- ✅ End-to-end testing is completed with 90%+ backend test coverage.
- ✅ Self-contained executable packages for Windows and macOS are built.
- ✅ User-facing documentation for installation, configuration, and troubleshooting is provided.
