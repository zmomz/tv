# Project: Execution Engine

For a detailed, step-by-step implementation plan, see `upgrading_plan.md`.

## Project Overview

This project is a fully automated trading execution engine with an integrated web UI. It's designed to receive TradingView webhooks, execute complex grid-based trading strategies (including pyramids and DCA), manage risk autonomously, and provide a real-time monitoring dashboard.

**Key Technologies:**

*   **Backend:** Python with FastAPI
*   **Frontend:** React (TypeScript)
*   **Database:** PostgreSQL
*   **Deployment:** Docker

## Current Plan
Following the detailed `upgrading_plan.md`.

1.  **[COMPLETED] Phase 0: Multi-User Authentication & Security Foundation**
2.  **[COMPLETED] Phase 1: Comprehensive Logging System**
3.  **[COMPLETED] Phase 2: Secure API Key Management**
4.  **[COMPLETED] Phase 3: Core Trading Engine** - The application is now a functional execution engine, not just a state manager.
5.  **[IN PROGRESS] Phase 3.5: Live Exchange Integration** - Successfully integrated with Binance Testnet. Webhook-to-order pipeline is functional.
6.  **[PENDING] Phase 4: DCA & Pyramid Execution**
7.  **[PENDING] Phase 5: Risk Engine & Queue Management**
8.  **[PENDING] Phase 6: Background Tasks & Scheduling**
9.  **[PENDING] Phase 7: Comprehensive Testing Suite**
10. **[PENDING] Phase 8: Frontend UI Development**
11. **[PENDING] Deployment & Configuration**

## Building and Running

### Docker

The entire application can be orchestrated using Docker Compose.

1.  **Build and start all services:**
    ```bash
    docker-compose up --build
    ```

## Key Commands

- **Run Backend Tests:**
  ```bash
  docker-compose exec app pytest
  ```
- **Run Backend Linting:**
  ```bash
  docker-compose exec app ruff check .
  ```
- **Generate a Database Migration:**
  ```bash
  docker-compose exec app alembic revision --autogenerate -m "Your migration message"
  ```
- **Apply Database Migrations:**
  ```bash
  docker-compose exec app alembic upgrade head
  ```

## API Quick Reference

- **Register a New User:**
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"username": "testuser", "email": "test@example.com", "password": "Password123", "role": "trader"}' http://localhost:8000/api/auth/register
  ```
- **Login and Get Token:**
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "Password123"}' http://localhost:8000/api/auth/login
  ```
- **Simulate a "New Entry" Webhook:**
  ```bash
  # Replace {user_id} with a valid user ID
  USER_ID="your-user-id-here"
  curl -X POST -H "Content-Type: application/json" -d '{"secret": "test", "tv": {"symbol": "BTC/USDT", "exchange": "binance"}, "execution_intent": {"action": "buy", "amount": 0.001, "strategy": "grid"}}' "http://localhost:8000/api/webhook/$USER_ID"
  ```

## Development Conventions

### Code Quality Standards

*   **Backend:** All functions must have type hints. Public methods should have docstrings.
*   **Frontend:** TypeScript should be used in strict mode, and the `any` type should be avoided.
*   **Database:** All database queries must use the SQLAlchemy ORM. Raw SQL is not permitted.
*   **Testing:** Tests should be written *before* implementing complex logic. The target code coverage is 80%+.
*   **Git:** Commits should be made after each working feature is complete, not just at the end of the day.

### AI Assistant Protocol

*   **Verification First:** Before starting a work session, verify the current state (running processes, git status, directory structure).
*   **One Task at a Time:** Focus on a single, specific task. Propose code or commands before executing and wait for approval.
*   **Verify After Changes:** After every modification, confirm that the change was applied correctly, there are no syntax errors, services are running, and relevant tests pass.
*   **Error Handling:** If an error occurs, stop immediately, present the full error message, explain the cause, and propose a solution before retrying.
*   **End of Session:** Commit all changes with a clear message, document what was completed, and list any pending tasks.