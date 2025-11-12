# Execution Plan: From Current State to SoW-Compliant Execution Engine

## 1. Introduction

This document outlines the development plan to upgrade the application from its current state to be fully compliant with the detailed **Execution Engine Scope of Work (SoW)**. It serves as the primary roadmap for development, tracking our progress from the current foundation to a feature-complete, robust, and well-tested application.

### Current Application State

The project has a solid foundation, with a well-structured backend and a component-based frontend. However, there are several significant discrepancies between the current implementation and the `SoW.md`, particularly in the core trading logic, risk management, and UI. The application is not yet feature-complete and requires further development to meet the client's requirements.

**Backend:**

The backend is built on a clean, service-oriented architecture, with a clear separation of concerns into `api`, `core`, `db`, `middleware`, `models`, `schemas`, and `services`. However, several of the core services contain placeholder logic and do not fully implement the functionality described in the SoW. The key areas that require attention are:

*   **Grid Trading Logic:** The DCA calculation, take-profit modes, and exit logic are incomplete.
*   **Precision Validation:** The precision validation logic is missing key features, such as periodic background fetching, correct user ID handling, and a notional value check.
*   **Execution Pool & Queue:** The execution pool and queue are not fully functional, with incorrect slot calculation, incomplete slot management, and placeholder priority logic.
*   **Risk Engine:** The risk engine is missing key features, such as complete timer logic, accurate offset execution, and respect for the `max_winners_to_combine` setting.

**Frontend:**

The frontend has a solid component-based architecture, with a clear separation of concerns into different feature areas. However, several key UI features described in the SoW are either missing or incomplete. The key areas that require attention are:

*   **Live Dashboard:** The main dashboard is a placeholder and does not contain any of the required widgets or metrics.
*   **Positions & Pyramids View:** The positions view is a placeholder and does not contain the required table or expandable detailed DCA view.
*   **Risk Engine Panel:** There is no page for the Risk Engine Panel.
*   **Waiting Queue View:** There is no page for the Waiting Queue View.
*   **Logs & Alerts:** The log viewer is a placeholder and does not contain any of the required features.
*   **Settings Panel:** The settings panel is a placeholder and does not contain any of the required features.
*   **Performance & Portfolio Dashboard:** The performance dashboard is a placeholder and does not contain any of the required metrics or charts.

This plan will address these issues in a structured and test-driven manner, starting with the backend and then moving on to the frontend.

## 2. Backend Development Plan

### Phase 1: Execution Pool & Queue

**Description:**

The execution pool and queue are fundamental to the system's ability to manage concurrent positions and prioritize signals. The current implementation has several significant discrepancies with the `SoW.md`, including incorrect slot calculation, incomplete slot management, and placeholder priority logic. This phase will address these issues and ensure that the execution pool and queue are fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `pool_manager.py`:**
    *   Write a test to verify that `get_open_slots` correctly calculates the number of available slots.
    *   Write a test to verify that `can_open_position` correctly returns `True` when there are available slots and `False` when the pool is full.
    *   Write a test to verify that `consume_slot` correctly decrements the number of available slots.
    *   Write a test to verify that `release_slot` correctly increments the number of available slots.
    *   Write a test to verify that pyramid entries do not consume a new pool slot.
2.  **Implement `pool_manager.py`:**
    *   Implement the `get_open_slots`, `can_open_position`, `consume_slot`, and `release_slot` functions to correctly manage the execution pool.
    *   Implement the logic to handle pyramid entries without consuming a new pool slot.
3.  **Write Unit Tests for `queue_service.py`:**
    *   Write a test to verify that `calculate_priority` correctly calculates the priority of a signal based on the SoW's priority rules (pyramid continuation, deepest loss percentage, highest replacement count, FIFO).
    *   Write a test to verify that `promote_from_queue` correctly promotes the highest priority signal from the queue.
    *   Write a test to verify that pyramid continuations of active groups are selected first and bypass the max position limit.
4.  **Implement `queue_service.py`:**
    *   Implement the `calculate_priority` function to correctly calculate the priority of a signal based on the SoW's priority rules.
    *   Implement the `promote_from_queue` function to correctly promote the highest priority signal from the queue.
    *   Implement the logic to handle pyramid continuations of active groups.

**Acceptance Criteria:**

*   The execution pool correctly limits the number of active `PositionGroup`s.
*   Pyramid entries do not consume a new pool slot.
*   The queue correctly prioritizes signals based on the SoW's priority rules.
*   Pyramid continuations of active groups are selected first and bypass the max position limit.

### Phase 2: Grid Trading Logic

**Description:**

The grid trading logic is the core of the trading strategy. The current implementation has several discrepancies with the `SoW.md`, including an inflexible DCA calculation, a single take-profit percentage for all DCA levels, and missing logic for the different take-profit modes and exit signals. This phase will address these issues and ensure that the grid trading logic is fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `grid_calculator.py`:**
    *   Write a test to verify that `calculate_dca_levels` correctly calculates the DCA levels based on the SoW's per-layer configuration.
    *   Write a test to verify that `calculate_take_profit_prices` correctly calculates the take-profit price for each DCA leg.
2.  **Implement `grid_calculator.py`:**
    *   Implement the `calculate_dca_levels` function to correctly calculate the DCA levels based on the SoW's per-layer configuration.
    *   Implement the `calculate_take_profit_prices` function to correctly calculate the take-profit price for each DCA leg.
3.  **Write Unit Tests for `take_profit_service.py`:**
    *   Write a test to verify that `check_take_profit_conditions` correctly checks for take-profit conditions for all three take-profit modes (`Per-Leg`, `Aggregate`, `Hybrid`).
    *   Write a test to verify that the correct take-profit orders are placed when a take-profit condition is met.
    *   Write a test to verify that exit signals from TradingView are correctly handled.
4.  **Implement `take_profit_service.py`:**
    *   Implement the `check_take_profit_conditions` function to correctly check for take-profit conditions for all three take-profit modes.
    *   Implement the logic to place the correct take-profit orders when a take-profit condition is met.
    *   Implement the logic to handle exit signals from TradingView.

**Acceptance Criteria:**

*   The DCA calculation is flexible and allows for per-layer configuration of `price_gap` and `capital_weight`.
*   The take-profit calculation is per-leg, as specified in the SoW.
*   All three take-profit modes (`Per-Leg`, `Aggregate`, `Hybrid`) are implemented and working correctly.
*   Exit signals from TradingView are correctly handled.

### Phase 3: Risk Engine

**Description:**

The risk engine is a critical component for managing risk. The current implementation has several discrepancies with the `SoW.md`, including a placeholder `evaluate_risk_conditions` function, incomplete timer logic, simplified offset execution, and no respect for the `max_winners_to_combine` setting. This phase will address these issues and ensure that the risk engine is fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `risk_engine.py`:**
    *   Write a test to verify that `evaluate_risk_conditions` correctly evaluates the risk conditions for a position group.
    *   Write a test to verify that the timer logic for activating the risk engine is working correctly for all three timer start conditions (`after_5_pyramids`, `after_all_dca_submitted`, `after_all_dca_filled`).
    *   Write a test to verify that the offset execution logic correctly calculates the amount to close on winning positions.
    *   Write a test to verify that the `execute_risk_mitigation` function respects the `max_winners_to_combine` setting.
2.  **Implement `risk_engine.py`:**
    *   Implement the `evaluate_risk_conditions` function to correctly evaluate the risk conditions for a position group.
    *   Implement the timer logic for activating the risk engine for all three timer start conditions.
    *   Implement the offset execution logic to correctly calculate the amount to close on winning positions.
    *   Implement the `execute_risk_mitigation` function to respect the `max_winners_to_combine` setting.

**Acceptance Criteria:**

*   The `evaluate_risk_conditions` function correctly evaluates the risk conditions for a position group.
*   The timer logic for activating the risk engine is working correctly for all three timer start conditions.
*   The offset execution logic correctly calculates the amount to close on winning positions.
*   The `execute_risk_mitigation` function respects the `max_winners_to_combine` setting.

### Phase 4: Precision Validation

**Description:**

The precision validation logic is a critical step to ensure zero API rejections from the exchange. The current implementation has several discrepancies with the `SoW.md`, including on-demand fetching of precision rules, a hardcoded dummy user ID, incomplete "hold signal" logic, and a missing notional value check. This phase will address these issues and ensure that the precision validation logic is fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `precision_service.py`:**
    *   Write a test to verify that precision rules are fetched periodically in the background.
    *   Write a test to verify that the correct user ID is used for fetching precision rules.
2.  **Implement `precision_service.py`:**
    *   Implement the logic to fetch precision rules periodically in the background.
    *   Implement the logic to use the correct user ID for fetching precision rules.
3.  **Write Unit Tests for `validation_service.py`:**
    *   Write a test to verify that the "hold signal" logic is correctly implemented.
    *   Write a test to verify that the notional value check is correctly implemented.
4.  **Implement `validation_service.py`:**
    *   Implement the "hold signal" logic to hold or queue a signal if precision data is missing.
    *   Implement the notional value check to ensure that an order meets the minimum notional value.

**Acceptance Criteria:**

*   Precision rules are fetched periodically in the background.
*   The correct user ID is used for fetching precision rules.
*   The "hold signal" logic is correctly implemented.
*   The notional value check is correctly implemented.

## 3. Frontend Development Plan

### Phase 1: Live Dashboard

**Description:**

The live dashboard is the main control screen for the application. The current implementation is a placeholder and does not contain any of the required widgets or metrics. This phase will address this issue and ensure that the live dashboard is fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `DashboardPage.jsx`:**
    *   Write a test to verify that the `Total Active Position Groups` widget is correctly displayed.
    *   Write a test to verify that the `Execution Pool Usage` widget is correctly displayed.
    *   Write a test to verify that the `Queued Signals Count` widget is correctly displayed.
    *   Write a test to verify that the `Total PnL` widget is correctly displayed.
    *   Write a test to verify that the `Last Webhook Timestamp` widget is correctly displayed.
    *   Write a test to verify that the `Engine Status Banner` widget is correctly displayed.
    *   Write a test to verify that the `Risk Engine Status` widget is correctly displayed.
    *   Write a test to verify that the `Error & Warning Alerts` widget is correctly displayed.
2.  **Implement `DashboardPage.jsx`:**
    *   Implement the `Total Active Position Groups` widget.
    *   Implement the `Execution Pool Usage` widget.
    *   Implement the `Queued Signals Count` widget.
    *   Implement the `Total PnL` widget.
    *   Implement the `Last Webhook Timestamp` widget.
    *   Implement the `Engine Status Banner` widget.
    *   Implement the `Risk Engine Status` widget.
    *   Implement the `Error & Warning Alerts` widget.

**Acceptance Criteria:**

*   All the required widgets and metrics are displayed on the live dashboard.
*   The data displayed on the live dashboard is accurate and up-to-date.

### Phase 2: Positions & Pyramids View

**Description:**

The positions view is the primary interface for monitoring trades. The current implementation is a placeholder and does not contain the required table or expandable detailed DCA view. This phase will address this issue and ensure that the positions view is fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `PositionsPage.jsx`:**
    *   Write a test to verify that the positions table is correctly displayed with all the required columns (Pair/Timeframe, Pyramids, DCA Filled, Avg Entry, Unrealized PnL, TP Mode, and Status).
    *   Write a test to verify that the expandable detailed DCA view is correctly displayed with all the required fields (Leg ID, Fill Price, Capital Weight, TP Target, Progress, Filled Size, and State).
2.  **Implement `PositionsPage.jsx`:**
    *   Implement the positions table with all the required columns.
    *   Implement the expandable detailed DCA view with all the required fields.

**Acceptance Criteria:**

*   The positions table is correctly displayed with all the required columns.
*   The expandable detailed DCA view is correctly displayed with all the required fields.
*   The data displayed in the positions view is accurate and up-to-date.

### Phase 3: Settings Panel

**Description:**

The settings panel is essential for configuring the engine. The current implementation is a placeholder and does not contain any of the required features. This phase will address this issue and ensure that the settings panel is fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `SettingsPage.jsx`:**
    *   Write a test to verify that all the editable parameters for Exchange API, Precision Control, Execution Pool, Risk Engine, TP Mode, Local Storage, and Theme & UI are correctly displayed.
    *   Write a test to verify that the Live Preview Panel is correctly displayed.
    *   Write a test to verify that the "Apply & Restart Engine" Button is correctly displayed and functional.
    *   Write a test to verify that the Validation Layer is correctly implemented.
    *   Write a test to verify that the Backup & Restore functionality is correctly implemented.
    *   Write a test to verify that the Readonly Mode is correctly implemented.
2.  **Implement `SettingsPage.jsx`:**
    *   Implement all the editable parameters for Exchange API, Precision Control, Execution Pool, Risk Engine, TP Mode, Local Storage, and Theme & UI.
    *   Implement the Live Preview Panel.
    *   Implement the "Apply & Restart Engine" Button.
    *   Implement the Validation Layer.
    *   Implement the Backup & Restore functionality.
    *   Implement the Readonly Mode.

**Acceptance Criteria:**

*   All the required settings are editable in the UI.
*   The Live Preview Panel correctly displays the changes before they are applied.
*   The "Apply & Restart Engine" Button correctly applies the changes and restarts the engine.
*   The Validation Layer correctly prevents invalid configuration.
*   The Backup & Restore functionality correctly backs up and restores the configuration.
*   The Readonly Mode correctly prevents unauthorized users from making changes.

### Phase 4: Logs & Alerts

**Description:**

The log viewer is a critical tool for debugging and troubleshooting. The current implementation is a placeholder and does not contain any of the required features. This phase will address this issue and ensure that the log viewer is fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `SystemLogsPage.jsx`:**
    *   Write a test to verify that the Log Categories/Filters are correctly displayed and functional.
    *   Write a test to verify that the Search & Filter Toolbar is correctly displayed and functional.
    *   Write a test to verify that the Auto-Scroll Toggle is correctly displayed and functional.
    *   Write a test to verify that the Color-Coded Severity is correctly implemented.
    *   Write a test to verify that the Highlight Critical Failures is correctly implemented.
    *   Write a test to verify that the Export Options are correctly displayed and functional.
    *   Write a test to verify that the Pinned Alert Strip is correctly displayed.
    *   Write a test to verify that the Webhook Replay Button is correctly displayed and functional.
    *   Write a test to verify that the Log Retention Setting is correctly displayed and functional.
2.  **Implement `SystemLogsPage.jsx`:**
    *   Implement the Log Categories/Filters.
    *   Implement the Search & Filter Toolbar.
    *   Implement the Auto-Scroll Toggle.
    *   Implement the Color-Coded Severity.
    *   Implement the Highlight Critical Failures.
    *   Implement the Export Options.
    *   Implement the Pinned Alert Strip.
    *   Implement the Webhook Replay Button.
    *   Implement the Log Retention Setting.

**Acceptance Criteria:**

*   All the required features are implemented in the log viewer.
*   The log viewer is easy to use and provides all the necessary information for debugging and troubleshooting.

### Phase 5: Risk Engine Panel & Waiting Queue View

**Description:**

The Risk Engine Panel and Waiting Queue View are important for monitoring the risk engine and queue. The current implementation is missing these views. This phase will address this issue and ensure that these views are fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `RiskEnginePage.jsx`:**
    *   Write a test to verify that the Risk Engine Panel is correctly displayed with all the required fields (Loss %, Loss USD, Timer Remaining, 5 Pyramids Reached, Age Filter Passed, Available Winning Offsets, and Projected Plan).
    *   Write a test to verify that the action buttons for Run Now, Skip Once, and Block Group are correctly displayed and functional.
2.  **Implement `RiskEnginePage.jsx`:**
    *   Implement the Risk Engine Panel with all the required fields.
    *   Implement the action buttons for Run Now, Skip Once, and Block Group.
3.  **Write Unit Tests for `QueuePage.jsx`:**
    *   Write a test to verify that the Waiting Queue Table is correctly displayed with all the required columns (Pair/Timeframe, Replacement Count, Expected Profit, Time in Queue, and Priority Rank).
    *   Write a test to verify that the action buttons for Promote, Remove, and Force Add to Pool are correctly displayed and functional.
4.  **Implement `QueuePage.jsx`:**
    *   Implement the Waiting Queue Table with all the required columns.
    *   Implement the action buttons for Promote, Remove, and Force Add to Pool.

**Acceptance Criteria:**

*   The Risk Engine Panel is correctly displayed with all the required fields and action buttons.
*   The Waiting Queue View is correctly displayed with all the required columns and action buttons.
*   The data displayed in these views is accurate and up-to-date.

### Phase 6: Performance & Portfolio Dashboard

**Description:**

The performance dashboard is a valuable tool for analyzing trading performance. The current implementation is a placeholder and does not contain any of the required metrics or charts. This phase will address this issue and ensure that the performance dashboard is fully functional and compliant with the SoW.

**Steps:**

1.  **Write Unit Tests for `PerformancePage.jsx`:**
    *   Write a test to verify that the PnL Metrics are correctly displayed.
    *   Write a test to verify that the Equity Curve is correctly displayed.
    *   Write a test to verify that the Win/Loss Stats are correctly displayed.
    *   Write a test to verify that the Trade Distribution is correctly displayed.
    *   Write a test to verify that the Risk Metrics are correctly displayed.
    *   Write a test to verify that the Capital Allocation View is correctly displayed.
    *   Write a test to verify that the Daily Summary Snapshot is correctly displayed.
    *   Write a test to verify that the Real-time TVL Gauge is correctly displayed.
2.  **Implement `PerformancePage.jsx`:**
    *   Implement the PnL Metrics.
    *   Implement the Equity Curve.
    *   Implement the Win/Loss Stats.
    *   Implement the Trade Distribution.
    *   Implement the Risk Metrics.
    *   Implement the Capital Allocation View.
    *   Implement the Daily Summary Snapshot.
    *   Implement the Real-time TVL Gauge.

**Acceptance Criteria:**

*   All the required metrics and charts are displayed on the performance dashboard.
*   The data displayed on the performance dashboard is accurate and up-to-date.
