# Execution Plan v2.0: From Current State to SoW-Compliant Execution Engine

## 1. Introduction

This document outlines the development plan to upgrade the application from its current state to be fully compliant with the detailed **Execution Engine Scope of Work (SoW)**. It serves as the primary roadmap for development, tracking our progress from the current foundation to a feature-complete, robust, and well-tested application.

### Current Application State

The project has a solid foundation, with a well-structured backend and a component-based frontend. However, there are several significant discrepancies between the current implementation and the `SoW.md`, particularly in the core trading logic, risk management, and UI. The application is not yet feature-complete and requires further development to meet the client's requirements.

**Backend:**
The backend is built on a clean, service-oriented architecture. However, several core services contain placeholder logic and do not fully implement the functionality described in the SoW. Key areas requiring attention are: Grid Trading Logic, Precision Validation, Execution Pool & Queue, and the Risk Engine.

**Frontend:**
The frontend has a solid component-based architecture, but most UI features are placeholders. Key areas requiring attention are: Live Dashboard, Positions View, Risk Engine Panel, Queue View, Logs & Alerts, Settings Panel, and the Performance Dashboard.

This plan will address these issues in a structured and test-driven manner.

---

## 2. Backend Development Plan

### Phase 1: Database Architecture

**Description:**
This phase will focus on designing and implementing the full data model for the application, including the database schema, migrations, and data access layer.

**Steps:**
1.  **Design Complete Schema:** Design the complete database schema for all the required tables (positions, groups, orders, signals, logs, risk_analysis, etc.).
2.  **Implement Database Migrations:** Implement database migrations using Alembic for schema evolution.
3.  **Create Repository Pattern for Data Access:** Create a repository pattern for accessing the database to abstract data logic.
4.  **Add Connection Pooling:** Configure and add connection pooling to the database connection for performance.
5.  **Implement Transaction Management:** Implement robust transaction management for all database operations to ensure data integrity.
6.  **Create Backup/Restore Procedures:** Script and document procedures for database backup and restore.
7.  **Add Database Health Checks:** Add database health checks to the application's health monitoring endpoint.

**Acceptance Criteria:**
*   **Functional:** The database schema fully supports all entities and relationships required by the SoW.
*   **Technical:** Migrations are repeatable and reversible. The repository pattern is used for all data access.
*   **Test Coverage:** Unit tests cover all repository methods.
*   **Error Handling:** The application handles database connection failures gracefully.

### Phase 2: Webhook & Signal Processing

**Description:**
This phase will focus on implementing the full webhook validation and parsing system, ensuring that all incoming signals are correctly authenticated, parsed, and validated before being processed.

**Steps:**
1.  **Implement Webhook Signature Validation:** Implement a middleware or dependency to validate webhook signatures using a shared secret.
2.  **Create Signal Parser:** Create a robust parser for the TradingView JSON payload structure.
3.  **Build Signal Validator:** Build a validator for signals (required fields, type checking) using Pydantic models.
4.  **Implement Signal Routing Logic:** Create logic to route signals based on their intent (new group vs. pyramid vs. exit).
5.  **Add Webhook Replay Functionality:** Implement a debugging endpoint to replay webhook payloads.
6.  **Implement Rate Limiting and Duplicate Detection:** Add middleware to prevent duplicate signal processing and limit request frequency.

**Acceptance Criteria:**
*   **Functional:** All incoming webhooks are correctly authenticated, parsed, and validated against the SoW's payload structure.
*   **Technical:** Pydantic models are used for validation. A dedicated service handles signal routing.
*   **Test Coverage:** Unit tests cover valid/invalid signatures, malformed payloads, and routing logic.
*   **Security:** Only authenticated webhooks are processed.

### Phase 3: Exchange Abstraction Layer

**Description:**
This phase will focus on creating a flexible and extensible exchange integration layer that can support multiple exchanges.

**Steps:**
1.  **Design Exchange Interface:** Design an abstract base class (`ExchangeInterface`) defining a common interface for all exchange operations.
2.  **Implement Binance Connector:** Implement a `BinanceConnector` that inherits from the interface.
3.  **Implement Bybit Connector:** Implement a `BybitConnector` that inherits from the interface.
4.  **Add Precision Fetching per Exchange:** Implement the logic for fetching and caching precision rules for each supported exchange.
5.  **Standardize Order Response Formats:** Create a set of internal Pydantic models to standardize responses from different exchanges.
6.  **Implement Exchange-Specific Error Mapping:** Map common exchange errors (e.g., `InsufficientFunds`, `InvalidOrder`) to a set of application-level exceptions.
7.  **Add Testnet Toggle Support:** Implement a testnet toggle for each supported exchange connector.
8.  **Create Exchange Health Monitoring:** Add methods to check API connectivity and account status for each exchange.

**Acceptance Criteria:**
*   **Functional:** The system can connect to and execute trades on both Binance and Bybit.
*   **Technical:** All exchange interactions go through the abstraction layer. Connectors are interchangeable.
*   **Test Coverage:** Unit tests with mock exchange APIs for each connector.
*   **Error Handling:** Exchange-specific errors are caught and mapped to standardized application exceptions.

### Phase 4: Order Management Service

**Description:**
This phase will focus on implementing a robust and reliable order management system that can handle the full lifecycle of an order.

**Steps:**
1.  **Implement Order Submission with Retry Logic:** Implement the logic for submitting orders to the exchange with a configurable number of retries on failure.
2.  **Create Order Fill Monitoring Loop:** Implement a background task that periodically queries the exchange for the status of open orders.
3.  **Add Partial Fill Handling:** Implement logic to handle and record partial order fills.
4.  **Implement Order Cancellation Workflow:** Implement the logic for cancelling open orders on the exchange.
5.  **Create Order State Machine:** Implement an order state machine (`pending`, `open`, `partially_filled`, `filled`, `cancelled`) to track the status of each order.
6.  **Add Order Reconciliation on Startup:** Implement logic to reconcile the status of open orders on application startup.
7.  **Implement Emergency Close All Functionality:** Create a service function to close all open positions for a user in an emergency.

**Acceptance Criteria:**
*   **Functional:** The system can reliably place, monitor, and cancel orders, and handle partial fills.
*   **Technical:** Order states are managed by a state machine. A background task handles monitoring.
*   **Test Coverage:** Unit tests for all state transitions and order operations.
*   **Performance:** Order status checks are batched to avoid hitting rate limits.
*   **Error Handling:** The system can recover from failures and reconcile order status on startup.

### Phase 5: Grid Trading Logic

**Description:**
This phase will address the core trading strategy, including DCA calculation, take-profit modes, and exit signals, ensuring full compliance with the SoW.

**Steps:**
1.  **Implement Per-Layer Configuration Parser:** Implement a parser for the per-layer DCA and TP configuration.
2.  **Create DCA Price Calculator with Rounding:** Create a DCA price calculator that incorporates precision rounding.
3.  **Build TP Price Calculator:** Build a TP price calculator that can handle all three modes: `Per-Leg`, `Aggregate`, and `Hybrid`.
4.  **Implement Fill Price Tracking:** Implement logic to track the actual fill price of each order.
5.  **Create Weighted Average Entry Calculator:** Create a calculator for the weighted average entry price of a position.
6.  **Add DCA Cancellation on Exit Logic:** Implement logic to cancel all unfilled DCA orders when an exit signal is received.
7.  **Implement Unfilled Order Cleanup:** Implement a cleanup process for any unfilled orders that are no longer valid.
8.  **Create Grid State Persistence:** Ensure that the state of the grid is persisted to the database.

**Acceptance Criteria:**
*   **Functional:** The DCA calculation is flexible and allows for per-layer configuration. All three take-profit modes are implemented and working correctly. Exit signals are handled correctly.
*   **Technical:** Calculations are performed using the `Decimal` type for precision.
*   **Test Coverage:** Unit tests for each calculation and take-profit mode.
*   **Performance:** Grid calculations are performed efficiently.

### Phase 6: Execution Pool & Queue

**Description:**
This phase will implement the system for managing concurrent positions and prioritizing incoming signals according to the SoW.

**Steps:**
1.  **Implement `pool_manager.py`:** Implement the `get_open_slots`, `can_open_position`, `consume_slot`, and `release_slot` functions to correctly manage the execution pool.
2.  **Implement Priority Score Calculator:** Implement a priority score calculator with the four-tier system (pyramid continuation, deepest loss %, highest replacement count, FIFO).
3.  **Create Signal Replacement Detection Logic:** Implement logic to detect and handle replacement signals in the queue.
4.  **Build Queue Promotion Algorithm:** Build the algorithm to promote signals from the queue based on their priority score.
5.  **Add Queue Size Limit Enforcement:** Add enforcement for the maximum queue size.
6.  **Implement Queue Overflow Handling:** Implement logic to handle queue overflow.
7.  **Create Time-in-Queue Tracker:** Implement a tracker for the time each signal spends in the queue.
8.  **Add Force Promote Functionality:** Add a manual override to force a signal to be promoted from the queue.
9.  **Implement Queue Persistence on Shutdown:** Implement logic to persist the queue to the database on shutdown.

**Acceptance Criteria:**
*   **Functional:** The execution pool correctly limits active positions. The queue correctly prioritizes signals based on the SoW's rules.
*   **Technical:** Pool and queue operations are atomic and thread-safe.
*   **Test Coverage:** Unit tests for all pool and queue operations, including priority calculation and promotion.
*   **Performance:** Queue and pool checks are performed in <10ms.

### Phase 7: Risk Engine

**Description:**
This phase will implement the sophisticated, multi-conditional Risk Engine to offset losing trades with profits from winners.

**Steps:**
1.  **Implement Configurable Timer:** Implement a configurable timer with the three start modes (`after_5_pyramids`, `after_all_dca_submitted`, `after_all_dca_filled`).
2.  **Create Timer Reset Logic:** Create the timer reset logic for when a replacement signal is received.
3.  **Build Age Filter:** Build the age filter with a configurable threshold.
4.  **Implement Winner Selection Algorithm:** Implement the winner selection algorithm that ranks winners by profit in USD.
5.  **Create Partial Close Quantity Calculator:** Create a calculator for the partial close quantity needed to realize a specific profit.
6.  **Add `max_winners_to_combine` Enforcement:** Add enforcement for the `max_winners_to_combine` setting.
7.  **Implement Risk Action Logging:** Implement logging of all risk actions to the `RiskAnalysis` table.
8.  **Create Risk Projection Calculator for UI:** Create a calculator to project the outcome of a risk action for the UI.
9.  **Add Manual Override Controls:** Add manual override controls (Run Now, Skip, Block) for the risk engine.

**Acceptance Criteria:**
*   **Functional:** The risk engine correctly identifies and offsets losing trades based on the SoW's rules. All three timer modes are implemented.
*   **Technical:** Risk engine evaluations are performed in a background task.
*   **Test Coverage:** Unit tests for all risk conditions, timer modes, and selection algorithms.
*   **Performance:** Risk engine evaluations are performed efficiently.

---

## 3. Frontend Development Plan

### Phase 1: Frontend Architecture Setup

**Description:**
This phase will focus on setting up the frontend architecture, including the project structure, state management, routing, API client, and component library.

**Steps:**
1.  **Set up React Project with TypeScript:** Set up a new React project with TypeScript.
2.  **Configure State Management:** Configure a state management library (e.g., Redux Toolkit, Zustand).
3.  **Set up React Router:** Set up React Router for routing.
4.  **Configure API Client:** Configure an API client (e.g., Axios, Fetch) with interceptors for handling authentication and errors.
5.  **Implement Authentication Context:** Implement an authentication context to manage the user's authentication state.
6.  **Set up WebSocket Connection Manager:** Set up a WebSocket connection manager for real-time updates.
7.  **Create Error Boundary Components:** Create error boundary components to handle errors gracefully.
8.  **Configure Theme Provider:** Configure a theme provider for light and dark mode.
9.  **Set up Component Library:** Set up a component library (e.g., Material-UI, Ant Design).
10. **Implement Loading and Notification Systems:** Implement loading and notification systems.

**Acceptance Criteria:**
*   The frontend architecture is well-structured and scalable.
*   The state management, routing, and API client are correctly configured.
*   The authentication context, WebSocket connection manager, and error boundary components are implemented.

### Phase 2: Real-time Data Layer

**Description:**
This phase will focus on implementing the real-time data layer, which will be responsible for fetching and synchronizing data between the frontend and the backend.

**Steps:**
1.  **Implement WebSocket Client:** Implement a WebSocket client for receiving real-time updates from the backend.
2.  **Create Data Synchronization Service:** Create a data synchronization service to manage the flow of data between the frontend and the backend.
3.  **Add Optimistic UI Updates:** Add optimistic UI updates to improve the user experience.
4.  **Implement Polling Fallback Mechanism:** Implement a polling fallback mechanism for browsers that do not support WebSockets.
5.  **Create Data Caching Strategy:** Create a data caching strategy to improve performance.
6.  **Add Stale Data Detection:** Add stale data detection to ensure that the data displayed in the UI is always up-to-date.
7.  **Implement Reconnection Logic:** Implement reconnection logic to automatically reconnect to the backend if the connection is lost.

**Acceptance Criteria:**
*   The real-time data layer is robust and reliable.
*   The data displayed in the UI is always up-to-date.
*   The user experience is smooth and responsive.

### Phase 3: UI Components & Views

**Description:**
This phase will focus on building all the UI components and views as specified in the SoW.

**Steps:**
1.  **Implement Live Dashboard:** Implement the Live Dashboard with all the required widgets and metrics.
2.  **Implement Positions & Pyramids View:** Implement the Positions & Pyramids View with the required table and expandable detailed DCA view.
3.  **Implement Risk Engine Panel:** Implement the Risk Engine Panel with all the required fields and action buttons.
4.  **Implement Waiting Queue View:** Implement the Waiting Queue View with the required table and action buttons.
5.  **Implement Logs & Alerts:** Implement the Logs & Alerts view with all the required features.
6.  **Implement Settings Panel:** Implement the Settings Panel with all the required features.
7.  **Implement Performance & Portfolio Dashboard:** Implement the Performance & Portfolio Dashboard with all the required metrics and charts.

**Acceptance Criteria:**
*   All UI components and views are implemented as specified in the SoW.
*   The UI is intuitive, easy to use, and provides all the necessary information to the user.

---

## 4. Cross-Cutting Phases

### Phase 1: Integration Testing

**Description:**
This phase will focus on building a suite of integration tests to verify that the core services of the application work together as expected.

**Steps:**
1.  **Create Mock Exchange:** Create a mock exchange for testing.
2.  **Build End-to-End Test Scenarios:** Build end-to-end test scenarios for the most critical user flows.
3.  **Test Signal-to-Order Full Flow:** Test the full flow from receiving a signal to placing an order.
4.  **Test Risk Engine Trigger Scenarios:** Test the different scenarios that can trigger the risk engine.
5.  **Test Queue Promotion Logic:** Test the queue promotion logic.
6.  **Simulate Exchange Errors:** Simulate exchange errors to test the error handling logic.
7.  **Test Recovery After Crash:** Test the application's ability to recover after a crash.
8.  **Performance Test with 100+ Concurrent Positions:** Performance test the application with a high number of concurrent positions.

**Acceptance Criteria:**
*   The application is robust and can handle a wide range of scenarios.
*   The application can recover from failures.
*   The application can handle a high number of concurrent positions.

### Phase 2: Monitoring & Observability

**Description:**
This phase will focus on implementing monitoring and observability features to ensure that the application is running smoothly and that any issues can be quickly identified and resolved.

**Steps:**
1.  **Implement Structured Logging:** Implement structured logging throughout the application.
2.  **Create Performance Metrics Collection:** Create a system for collecting performance metrics.
3.  **Add Health Check Endpoints:** Add health check endpoints to the application.
4.  **Implement Alert Thresholds:** Implement alert thresholds for key performance metrics.
5.  **Create Diagnostic Dump Functionality:** Create a functionality to dump diagnostic information for debugging.
6.  **Add Memory Profiling Hooks:** Add memory profiling hooks to the application.
7.  **Implement Request/Response Logging:** Implement request/response logging for all API endpoints.

**Acceptance Criteria:**
*   The application is easy to monitor and debug.
*   Any issues can be quickly identified and resolved.

### Phase 3: Configuration Management

**Description:**
This phase will focus on implementing a robust and flexible configuration management system.

**Steps:**
1.  **Create Configuration Schema Validation:** Create a schema validation for the configuration file.
2.  **Implement Hot-Reload Mechanism:** Implement a hot-reload mechanism for the configuration.
3.  **Build Configuration Migration System:** Build a migration system for the configuration.
4.  **Add Configuration Versioning:** Add versioning to the configuration.
5.  **Create Validation Rules for Each Parameter:** Create validation rules for each parameter in the configuration.
6.  **Implement Configuration Backup/Restore:** Implement a backup and restore functionality for the configuration.
7.  **Add Configuration Diff Viewer in UI:** Add a diff viewer to the UI to show the changes between different versions of the configuration.
8.  **Create Readonly Mode Enforcement:** Create a readonly mode enforcement for the configuration.

**Acceptance Criteria:**
*   The configuration management system is robust and flexible.
*   The configuration can be easily updated and managed.

### Phase 4: Security

**Description:**
This phase will address the security requirements outlined in the SoW, ensuring that sensitive data is protected and that the application is not vulnerable to common attack vectors.

**Steps:**
1.  **Implement Encryption of Secrets:** Implement encryption for all secrets, including API keys and passwords.
2.  **Implement Webhook Signature Validation:** Implement webhook signature validation to prevent unauthorized access.
3.  **Implement Role-Based Access Control:** Implement role-based access control to restrict access to sensitive data and functionality.
4.  **Implement Secure Configuration File Handling:** Implement secure handling of the configuration file.
5.  **Implement Audit Logging:** Implement audit logging for all sensitive operations.
6.  **Prevent SQL Injection:** Implement measures to prevent SQL injection.

**Acceptance Criteria:**
*   All sensitive data is protected.
*   The application is not vulnerable to common attack vectors.

### Phase 5: Error Handling & Recovery

**Description:**
This phase will address the error handling and recovery requirements outlined in the SoW, ensuring that the application is robust and can handle unexpected errors gracefully.

**Steps:**
1.  **Implement Exchange-Specific Error Handling:** Implement handling for exchange-specific error codes.
2.  **Implement Retry Strategy:** Implement a retry strategy for failed requests.
3.  **Implement Circuit Breaker Pattern:** Implement a circuit breaker pattern to prevent cascading failures.
4.  **Implement Graceful Degradation Plan:** Implement a graceful degradation plan for when the application is under heavy load.

**Acceptance Criteria:**
*   The application is robust and can handle unexpected errors gracefully.
*   The application can recover from failures.

### Phase 6: Deployment & Packaging

**Description:**
This phase will address the deployment and packaging requirements outlined in the SoW, ensuring that the final product is delivered as a self-contained web app with installation packages for Windows and macOS.

**Steps:**
1.  **Create Build Scripts:** Create build scripts for packaging the backend and frontend into a single executable.
2.  **Test Packaged Application:** Test the packaged application on target platforms (Windows, macOS).
3.  **Create Installers:** Create installers for each platform.
4.  **Implement Update/Rollback Mechanism:** Implement an update/rollback mechanism for the application.
5.  **Set up Production Monitoring:** Set up a production monitoring system for the application.

**Acceptance Criteria:**
*   The application is easy to deploy and manage.
*   The application can be updated and rolled back easily.

### Phase 7: Documentation

**Description:**
This phase will address the documentation requirements outlined in the SoW, ensuring that the final product is delivered with full documentation for installation, configuration, and troubleshooting.

**Steps:**
1.  **Write Installation Guide:** Write a detailed installation guide for the packaged application on Windows and macOS.
2.  **Write Configuration Guide:** Write a comprehensive configuration guide that explains every setting in the UI's Settings Panel.
3.  **Write Troubleshooting Guide:** Write a troubleshooting guide that covers common errors and their solutions.
4.  **Update `README.md`:** Update the `README.md` file for developers.

**Acceptance Criteria:**
*   The documentation is clear, comprehensive, and easy to understand.

---

## 5. SoW Traceability Matrix

| SoW Section | SoW Requirement | Execution Plan Phase |
|-------------|----------------|---------------------|
| 2.2 | First signal creates Position Group | Backend Phase 5 |
| 2.2 | Pyramids don't create new positions | Backend Phase 6 |
| 2.3 | DCA per-layer configuration | Backend Phase 5 |
| 2.4 | Take-Profit Modes | Backend Phase 5 |
| 2.5 | Exit Logic | Backend Phase 5 |
| 3 | Precision Validation | Backend Phase 4 |
| 4 | Risk Engine | Backend Phase 7 |
| 5 | Execution Pool & Queue | Backend Phase 6 |
| 7 | UI Requirements | Frontend Phases 1-3 |
| 10 | Configuration | Cross-Cutting Phase 3 |
| 11 | Logging, Security, Storage | Cross-Cutting Phases 2, 4 |
| 13 | Deliverables | Cross-Cutting Phase 6, 7 |