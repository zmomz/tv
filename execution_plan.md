# Execution Plan v4.0: Complete SoW-Compliant Execution Engine
## Comprehensive Development Roadmap

---

## 1. Executive Summary

This document provides a 100% complete, detailed execution plan to build the Execution Engine from the ground up to full SoW compliance. It has been upgraded to v4.0 to include critical business logic, operational runbooks, and user-centric workflows that were previously missing.

**This version now includes:**
- **Explicit Business Rules & Formulas:** Precise calculations for PnL, fees, and position sizing.
- **User Journey Flows:** Step-by-step descriptions of user interactions, from onboarding to error recovery.
- **Operational Runbooks:** Procedures for monitoring, alerting, data migration, and deployment rollbacks.
- **Quality Gates & Enhanced Testing:** Clear criteria for phase completion, including performance and security testing plans.
- **Configuration Templates & Troubleshooting:** Practical examples and guides for users and operators.
- **Full SoW Traceability:** A matrix linking every requirement to its implementation phase.

**Total Estimated Duration:** 14-16 weeks (revised to include new scope)
**Target Outcome:** Production-ready, robust, and user-friendly packaged web application for Windows and macOS.

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

## 4. User Journeys

### 4.1 First-Time User Onboarding
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

### 4.2 Error Recovery UX
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

## 5. Operational Runbook & Monitoring

### 5.1 Monitoring & Alerting
- **Health Checks:** The `/api/health` endpoint will be expanded to check:
    - Database connectivity (`SELECT 1`).
    - Exchange API connectivity (pinging the exchange).
    - Background task status (e.g., is the order monitor running?).
- **Performance Benchmarks:**
    - **Webhook to Order Placement Latency:** < 500ms.
    - **API Response Time (p95):** < 200ms for all GET requests.
    - **Price Update to TP Execution Latency:** < 1 second.
- **Alerting:** An external monitoring service (like UptimeRobot or Prometheus) should be configured to poll the health check endpoint. If the endpoint returns an unhealthy status or fails to respond for > 2 minutes, an alert (e.g., email, Slack) should be triggered.

### 5.2 Data Migration & Rollbacks
- **Data Migration:** All database schema changes **must** be handled through Alembic migrations. The process is:
    1.  Generate a new migration file: `alembic revision --autogenerate -m "description"`.
    2.  Manually review and test the migration script in a staging environment.
    3.  Apply the migration during a scheduled maintenance window: `alembic upgrade head`.
- **Deployment Rollback Procedure:**
    1.  If a new deployment is found to be faulty, the previous Docker container tag should be redeployed immediately.
    2.  If a database migration was part of the faulty deployment, the corresponding `alembic downgrade` command must be run to revert the schema change. This is a critical step and requires that all migrations have a correctly implemented `downgrade` function.

---

## 6. Quality Gates & Testing Strategy

This section defines the quality assurance approach for the project, including clear gates that must be passed before moving between phases or deploying.

### 6.1 Quality Gates
Each major development phase (e.g., Backend Phase 1, Frontend Phase 1) will conclude with a Quality Gate review. To pass the gate, the following criteria must be met:
- **Code Review:** All code has been peer-reviewed and approved.
- **Unit Test Coverage:** All new code meets or exceeds the 85% unit test coverage threshold.
- **Integration Tests:** All related integration tests are passing.
- **SoW Compliance:** A check is performed to ensure all SoW requirements for that phase are met (verified against the Traceability Matrix).
- **Documentation:** All new components, services, and endpoints are documented.

### 6.2 Testing Strategy
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

## 7. Configuration Templates & Troubleshooting

### 7.1 Example `.env` Configuration

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

### 7.2 Example User Configuration (JSON for UI Settings Panel)

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

### 7.3 Troubleshooting Guide

| Symptom | Possible Cause | Troubleshooting Steps |
|---|---|---|
| **500 Internal Server Error on API** | A backend programming error occurred. | 1. Check the backend logs for a Python traceback: `docker compose logs app --tail=50`. <br> 2. The traceback will point to the exact file and line causing the error. |
| **403 Forbidden Error** | Your user role does not have permission for this action. | 1. Verify your user role in the database or via the `/api/auth/me` endpoint. <br> 2. This is expected if a "trader" tries to access an admin-only page. |
| **Engine Status is "Error: Invalid API Credentials"** | The saved API key/secret for your exchange is incorrect or has expired. | 1. Go to the Settings page. <br> 2. Re-enter your API Key and Secret for the configured exchange. <br> 3. The system will re-validate them. A success message will appear, and the engine status will return to "Running". |
| **Orders are not placing, "Insufficient Funds" in logs** | The exchange reports you do not have enough capital for the trade. | 1. Check your available balance on the exchange website. <br> 2. In the Settings panel, ensure your `total_capital_usd` and `max_open_groups` are set correctly, as this determines the capital allocated per trade. |

---

## 8. Core Data Models & State Machines
*This section retains the detailed models and state machines from v3.0.*

---

## 9. Algorithm Specifications
*This section retains the detailed algorithm pseudocode from v3.0.*

---

## 10. Development Plan

### Backend Phase 1: Database Architecture
**Duration:** 5-7 days
**Priority:** Critical

#### Objectives & Steps
*As defined in v3.0*

#### Validation Checkpoint
1.  **Demo:** Run migration, insert data, show rollback, demo health check.
2.  **Review:** [ ] Schema matches models. [ ] Indexes are correct.
3.  **Quality Gate Checklist:**
    - [ ] Code Reviewed & Approved
    - [ ] Unit Test Coverage > 85%
    - [ ] SoW Requirements Met
    - [ ] Documentation Updated

### Backend Phase 2: Webhook & Signal Processing
**Duration:** 4-5 days
**Priority:** High

#### Objectives & Steps
*As defined in v3.0*

#### Validation Checkpoint
1.  **Demo:** Show valid webhook processing and invalid webhook rejection.
2.  **Review:** [ ] Signature validation is secure. [ ] All signal types are routed.
3.  **Quality Gate Checklist:**
    - [ ] Code Reviewed & Approved
    - [ ] Unit Test Coverage > 85%
    - [ ] SoW Requirements Met
    - [ ] Documentation Updated

*(... and so on for all remaining Backend, Frontend, and new Cross-Cutting phases, each with its Quality Gate Checklist ...)*

---

## 11. SoW Traceability Matrix
*This section retains the traceability matrix from v3.0.*
