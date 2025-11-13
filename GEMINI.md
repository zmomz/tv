# Project: Execution Engine v4.0

## Project Overview

This project is a fully automated trading execution engine with an integrated web UI. It's designed to receive TradingView webhooks, execute complex grid-based trading strategies (including pyramids and DCA), manage risk autonomously, and provide a real-time monitoring dashboard.

This `GEMINI.md` file serves as the primary operational guide for the AI development assistant, complementing the strategic roadmap outlined in `execution_plan.md`.

**Key Technologies:**
*   **Backend:** Python with FastAPI
*   **Frontend:** React (TypeScript) with Material-UI (MUI)
*   **State Management:** Zustand
*   **Database:** PostgreSQL
*   **Deployment:** Docker

---

## Core Business Logic & Rules

### PnL Calculation
- **Unrealized PnL (USD):** `(Current Market Price - Weighted Average Entry Price) * Total Filled Quantity` (For shorts: `(Weighted Average Entry Price - Current Market Price) * ...`)
- **Unrealized PnL (%):** `(Unrealized PnL (USD) / Total Invested USD) * 100`
- **Realized PnL (USD):** `(Exit Price - Entry Price) * Closed Quantity - Fees`. Must account for exchange fees provided by `ccxt`.

### Capital Allocation
- **Capital Per Position Group:** `Total Capital / Max Concurrent Positions`.
- **Position Sizing (Per DCA Leg):** `(Capital Per Position Group) * (DCA Leg Weight % / 100)`.

---

## AI Assistant Protocol (v4.0)

This protocol is designed to work with the phased approach in `execution_plan.md`.

### 1. Phase-Driven Workflow
- **Declare Phase:** At the beginning of a work session, state the specific phase and objective you are working on (e.g., "Starting Backend Phase 1: Database Architecture, Objective: Implement SQLAlchemy models.").
- **Adhere to Plan:** Follow the **Steps** outlined for the current phase in `execution_plan.md` sequentially. Do not skip steps or move to the next phase without explicit approval.
- **Implement Business Logic:** When implementing features, refer to the **Business Rules & Formulas** and **Algorithm Specifications** sections of the execution plan to ensure the logic is correct.

### 2. Test-Driven Development (TDD)
- **Write Tests First:** For any new business logic (e.g., a new service, a complex calculation), you must write the failing `pytest` unit tests *before* writing the implementation code.
- **Verify Coverage:** Before submitting work for a Quality Gate review, run a test coverage report and ensure the new code meets the >85% threshold.

### 3. Quality Gates
- **Request Review:** Upon completing all steps in a phase, formally request a "Quality Gate Review."
- **Provide Checklist:** Present the completed **Quality Gate Checklist** for that phase, confirming that all criteria (Code Review, Test Coverage, SoW Compliance, Documentation) have been met.
- **Await Approval:** Do not begin the next phase until the Quality Gate has been approved.

### 4. Operational & Error Handling
- **Follow Runbooks:** When performing operational tasks like database migrations or deployments, follow the procedures outlined in the **Operational Runbook**.
- **Implement for Recovery:** When building features, consider the **User Journeys** for error recovery. Ensure that the application provides clear feedback to the user in case of errors like invalid API keys or insufficient funds.
- **Troubleshooting:** If an error is encountered during development, first consult the **Troubleshooting Guide**. If the issue is not listed, diagnose the problem, propose a solution, and then add the new solution to the guide.

### 5. Verification and Committing
- **Verify Changes:** After every modification, confirm that the change was applied correctly, there are no syntax errors, services are running, and all relevant tests pass.
- **Atomic Commits:** Make small, atomic commits after each logical piece of work is complete. Commit messages should be clear and reference the relevant phase of the execution plan (e.g., `feat(backend-p1): Implement PositionGroup model`).

---

## Key Commands & Procedures

- **Run Backend Tests:**
  ```bash
  docker compose exec app pytest
  ```
- **Run Backend Test Coverage:**
  ```bash
  docker compose exec app pytest --cov=app
  ```
- **Run Backend Linting:**
  ```bash
  docker compose exec app ruff check .
  ```
- **Generate a Database Migration:**
  ```bash
  docker compose exec app alembic revision --autogenerate -m "Your migration message"
  ```
- **Apply Database Migrations:**
  ```bash
  docker compose exec app alembic upgrade head
  ```
- **Downgrade a Database Migration:**
  ```bash
  docker compose exec app alembic downgrade -1
  ```

---

## Lessons Learned (Live Log)

- **SQLAlchemy 2.0 Async Mocking:** Unit tests for services using `db.execute()` require a specific mocking pattern. The mock for `db.execute` must *not* be an `asyncio.Future` itself. Instead, it should be a `MagicMock` instance whose `scalars()` and `all()` methods are pre-configured. The application code's `await result.scalars().all()` will then resolve correctly without needing the mock to be a future.
  - **Correct Pattern:** `mock_result = MagicMock(); mock_result.scalars.return_value.all.return_value = [...]; mock_db_session.execute.return_value = mock_result`
- **Tool Brittleness:** The `replace` tool is extremely sensitive to whitespace and context. When fixing multiple similar errors across files, this led to repeated `IndentationError`s. The path forward is to be extremely precise with the `old_string` parameter, including significant and unique surrounding context, and to fix issues one file at a time, re-reading the file if a replacement fails.
- **Database Fixture Resolution:** Pytest fixtures that are `async_generator`s (like the `db_session` fixture) must be resolved within an `async for` loop in the test function (e.g., `async for session in db_session: ...`). Passing the generator directly to a service that expects a session object will cause `AttributeError`s.