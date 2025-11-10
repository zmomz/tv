# Upgrading Plan: From Skeleton to Full Execution Engine

## 1. Introduction

This document outlines the development plan to upgrade the current application from its foundational skeleton to the complete, feature-rich automated trading execution engine as defined in the original Scope of Work.

The current application has a functional backend for state management, a basic UI for displaying data, and is fully dockerized. The core trading logic, advanced features, and comprehensive UI are the key areas for development.

---

## Phase 1: Core Trading Logic Implementation

This is the most critical phase, focused on transforming the application from a state manager into a functional trading bot that executes orders.

### Step 1.1: Exchange Integration & Order Execution
- **Task:** Enhance `ExchangeManager` to handle real order execution.
- **Details:**
    - Implement methods for placing `LIMIT` and `MARKET` orders.
    - Implement methods for cancelling open orders.
    - Implement methods for fetching the status of a specific order by its ID.
    - Ensure all methods correctly handle exchange-specific API responses and errors.
    - The `testnet` flag will be used to switch between live and paper trading endpoints.

### Step 1.2: DCA & Pyramid Calculation Logic
- **Task:** Create a new service, `GridCalculator`, to handle all grid-related calculations.
- **Details:**
    - Create a function `calculate_dca_orders(entry_price, dca_levels, trade_risk_usd, precision)` that returns a list of DCA orders with their calculated entry price and quantity.
    - The quantity will be derived from the `dca_risk_fraction` and the total capital allocated for the trade.
    - All calculations must respect the precision rules (tick size, step size) provided.

### Step 1.3: Position Manager Enhancement for Order Placement
- **Task:** Upgrade `PositionGroupManager` to place live orders.
- **Details:**
    - When `create_group` is called for a new entry, it will:
        1. Call the `GridCalculator` to get the list of DCA orders.
        2. Use the `ExchangeManager` to place `LIMIT` orders for each DCA leg on the exchange.
        3. Store the exchange-provided `order_id` for each DCA leg in the `dca_legs` database table (a new model will be needed).
    - When a `pyramid` signal arrives, it will repeat the process, creating and placing a new set of DCA orders.

### Step 1.4: Main Loop - Order Fill & Status Monitoring
- **Task:** Implement the core monitoring logic within the `main_loop_task`.
- **Details:**
    - The loop will query the database for all `PositionGroup`s with a "Live" status and open orders.
    - For each open order, it will use the `ExchangeManager` to check its status on the exchange.
    - If an order is filled, the loop will update the database to mark the corresponding DCA leg as "filled" and record the `fill_price` and `filled_qty`.

### Step 1.5: Take-Profit (TP) Manager Implementation
- **Task:** Implement the three take-profit modes.
- **Details:**
    - The `main_loop_task` will call the `TPManager` for each active position.
    - The `TPManager` will fetch the current market price for the symbol.
    - **Per-Leg TP:** It will check each filled DCA leg. If `current_price` exceeds the leg's TP target, it will execute a `MARKET` order to close that leg's quantity.
    - **Aggregate TP:** It will calculate the weighted average entry price of all filled legs. If `current_price` exceeds the aggregate TP target, it will close the entire `PositionGroup`.
    - **Hybrid TP:** It will run both checks, and the first one to trigger will be executed.

### Step 1.6: Exit Signal Handling
- **Task:** Implement logic in the webhook to handle `exit` signals.
- **Details:**
    - When a webhook with `execution_intent.type == "exit"` is received, the system will:
        1. Identify the corresponding `PositionGroup`.
        2. Use the `ExchangeManager` to cancel all open (unfilled) DCA limit orders for that group.
        3. Execute a single `MARKET` order to close the entire current position size.
        4. Update the `PositionGroup` status to "Closed" in the database.

---

## Phase 2: Advanced Manager Logic & Risk Engine

This phase focuses on implementing the more sophisticated business logic for queuing and risk management.

### Step 2.1: Advanced Queue Logic
- **Task:** Rework `QueueManager` to implement the specified priority ranking.
- **Details:**
    - The `promote_next` method will be rewritten to query all queued signals and sort them based on the following priority:
        1. **Pyramid Continuation:** Signals for an already active group.
        2. **Deepest Loss %:** Requires fetching the current market price and comparing it to the signal's entry price.
        3. **Highest Replacement Count:** Based on the `replacement_count` field.
        4. **FIFO:** The oldest signal as a final tie-breaker.

### Step 2.2: Risk Engine - Full Activation Conditions
- **Task:** Enhance the `RiskEngine`'s `should_activate` method.
- **Details:**
    - Add a check to see if the `PositionGroup` has 5 associated pyramids.
    - Implement the "post-full waiting time" timer logic based on the configured `timer_start_condition`.
    - Add the optional trade age threshold check.

### Step 2.3: Risk Engine - Partial Close Logic
- **Task:** Implement precise partial closing for winning trades.
- **Details:**
    - The `mitigate_risk` function will be updated.
    - It will calculate the exact quantity of the winning positions to sell to cover the `required_usd` of the losing trade.
    - It will then execute `MARKET` sell orders for those precise quantities, leaving the rest of the winning positions open.

---

## Phase 3: Configuration & Security

This phase decouples the application's configuration from environment variables and enhances security.

### Step 3.1: JSON Configuration Store
- **Task:** Move all configurable parameters to a single `config.json` file.
- **Details:**
    - Create a `config.json` file in a data directory.
    - Modify `app.core.config` to load all settings from this file. The `.env` file will only be used for the database password, which is injected by Docker Compose.

### Step 3.2: Secure API Key Storage
- **Task:** Encrypt API keys at rest.
- **Details:**
    - Use a library like `cryptography` to encrypt the `api_key` and `api_secret` before storing them in the database or config file.
    - The encryption key will be a user-defined password that is entered when the application starts (or stored in an environment variable for Docker).

### Step 3.3: Backend API for Configuration
- **Task:** Create FastAPI endpoints to manage the configuration.
- **Details:**
    - `GET /api/settings`: Returns the current `config.json` content (with secrets redacted).
    - `POST /api/settings`: Overwrites the `config.json` file with the new settings provided by the UI and triggers a hot-reload of the engine's configuration.

---

## Phase 4: Comprehensive UI Development

This phase focuses on building the full webtop UI as specified in the scope.

### Step 4.1: UI Foundation & Layout
- **Task:** Integrate a component library and build the main application shell.
- **Details:**
    - Install a library like Material-UI or Ant Design.
    - Create a main layout with a sidebar for navigation between the different screens (Dashboard, Positions, Risk, Queue, Logs, Settings).

### Step 4.2: Settings Panel
- **Task:** Build the UI for editing the application configuration.
- **Details:**
    - Create a form that represents the structure of `config.json`.
    - The form will fetch its initial state from `GET /api/settings`.
    - A "Save & Restart Engine" button will `POST` the updated configuration to `POST /api/settings`.

### Step 4.3: Live Positions & Pyramids View
- **Task:** Enhance the positions table.
- **Details:**
    - The table will fetch data from `/api/position_groups` and update in real-time.
    - Implement an expandable row feature. When a user clicks on a `PositionGroup`, it will expand to show a detailed table of all its associated DCA legs and their statuses (pending, filled, TP-hit).

### Step 4.4: Dashboard & Other UI Panels
- **Task:** Build the remaining UI screens.
- **Details:**
    - **Dashboard:** Create widgets for the key metrics. This will require new backend endpoints to compute and serve this summary data (e.g., `GET /api/dashboard/summary`).
    - **Risk Engine & Queue Panels:** Build the dedicated UI panels. This will require new endpoints to provide the necessary data (e.g., `GET /api/risk_engine/status`, `GET /api/queue/signals`).

### Step 4.5: Logging System & UI
- **Task:** Implement a robust logging system.
- **Details:**
    - **Backend:** Replace all `print()` statements with a structured logging library (e.g., `loguru`) configured to write to rotating log files.
    - **Backend:** Create an endpoint `GET /api/logs` that can stream or paginate log entries.
    - **Frontend:** Build the Log Viewer UI with features to filter by level, search by keyword, and auto-scroll.

---

## Phase 5: Finalization & Packaging

This phase focuses on long-term data storage, advanced analytics, and deployment.

### Step 5.1: Historical Trade Database
- **Task:** Implement logic to archive closed trades.
- **Details:**
    - When a `PositionGroup` is closed, move its data from the "live" tables to "history" tables in the database. This keeps the active tables small and fast.

### Step 5.2: Performance Dashboard
- **Task:** Build the advanced analytics UI.
- **Details:**
    - Create the necessary backend endpoints to perform calculations on the historical trade data (e.g., `GET /api/performance/equity_curve`).
    - Build the frontend components to visualize this data (charts, graphs, tables).

### Step 5.3: Documentation & Cleanup
- **Task:** Finalize all project documentation.
- **Details:**
    - Thoroughly update the `README.md` with final setup, configuration, and troubleshooting instructions.
    - Add inline code comments where the logic is complex.

### Step 5.4: Desktop Packaging (Stretch Goal)
- **Task:** Package the application as a standalone desktop app.
- **Details:**
    - Use a framework like **Tauri** or **Electron** to wrap the existing web UI and backend.
    - The packaging process will need to include the Python runtime and all dependencies.
    - Create installers for Windows (`.msi`) and macOS (`.dmg`).
