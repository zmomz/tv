# Project: Execution Engine

For a detailed, step-by-step implementation plan with data structures and acceptance criteria, see `upgrading_plan.md`.

## Project Overview

This project is a fully automated trading execution engine with an integrated web UI. It's designed to receive TradingView webhooks, execute complex grid-based trading strategies (including pyramids and DCA), manage risk autonomously, and provide a real-time monitoring dashboard.

**Key Technologies:**

*   **Backend:** Python with FastAPI
*   **Frontend:** React (TypeScript)
*   **Database:** PostgreSQL
*   **Deployment:** Docker

## High-Level Architecture

The application is a multi-container Docker setup orchestrated by `docker compose`.

1.  **Frontend:** A React application that communicates with the backend via a REST API.
2.  **Backend:** A Python FastAPI application that serves the API. It contains all business logic.
3.  **Database:** A PostgreSQL database that stores all persistent data (users, positions, keys, etc.).
4.  **Redis:** Used for caching and potentially for managing distributed tasks or locks in the future.
5.  **Exchange:** The backend communicates with external cryptocurrency exchanges (like the Binance testnet) via the `ccxt` library to execute trades.

The primary data flow for a trade is: `TradingView Webhook` -> `Backend API` -> `Signal Processor` -> `Position Manager` -> `Exchange Manager` -> `Binance Testnet`.

## Project Structure

This map explains the purpose of the most important directories in the backend.

```
backend/app/
├── api/         # Defines all HTTP API endpoints (FastAPI routers).
├── services/    # Contains all business logic (e.g., placing orders, processing signals).
├── models/      # Defines the database schema (SQLAlchemy models).
├── schemas/     # Defines the data shapes for API requests/responses (Pydantic models).
├── db/          # Database session management.
├── core/        # Core application configuration.
└── middleware/  # Custom FastAPI middleware (e.g., for authentication).
```

## Building and Running

The entire application is orchestrated using Docker Compose.

1.  **Build and start all services:**
    ```bash
    docker compose up --build
    ```

## Environment Variable Reference

All configuration is managed via the `.env` file. The `.env.example` file serves as a template.

| Variable | Description | Used By |
|---|---|---|
| `DATABASE_URL` | The connection string for the PostgreSQL database. | `backend` |
| `POSTGRES_PASSWORD` | The password for the PostgreSQL database user. | `docker-compose.yml` |
| `JWT_SECRET` | The secret key for encoding and decoding JWTs for user authentication. | `backend` |
| `ENCRYPTION_KEY` | The secret key for encrypting and decrypting user API keys at rest. | `backend` |
| `LOG_LEVEL` | The logging level for the application. | `backend` |
| `REDIS_URL` | The connection string for the Redis instance. | `backend` |

## Key Commands

- **Run Backend Tests:**
  ```bash
  docker compose exec app pytest
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

## Debugging Workflow

Follow this checklist to diagnose common issues.

1.  **API returns 500 Internal Server Error:**
    - Check the backend logs for a Python traceback:
      ```bash
      docker compose logs app --tail=50
      ```
2.  **Any container fails to start:**
    - Check the logs for that specific container.
      ```bash
      # Replace <service_name> with 'app', 'db', 'frontend', etc.
      docker compose logs <service_name>
      ```
3.  **Database connection issues:**
    - Verify that the `db` container is running: `docker compose ps`.
    - Ensure the `DATABASE_URL` in your `.env` file correctly points to the `db` service (e.g., `postgresql://tv_user:your_password@db:5432/tv_engine_db`).
4.  **Webhook fails with 404 Not Found:**
    - Double-check the endpoint URL. The correct format is `/api/webhook/{user_id}`.
    - Verify the `user_id` exists in the database.

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

### Core Patterns

*   **Dependency Injection:** FastAPI's dependency injection is used extensively. Database sessions (`db: Session = Depends(get_db)`) and services (`pool_manager: ExecutionPoolManager = Depends(get_pool_manager)`) are injected into API endpoints. **Never create your own database session in an endpoint.**
*   **Service Layer:** All business logic is encapsulated within the `services` directory. API endpoints in the `api` directory should be lightweight and delegate all real work to the services.
*   **Async Operations:** For performance, all API endpoints that perform I/O (database calls, exchange API calls) are defined with `async def`.

## Technology Best Practices

### FastAPI

*   **Routers:** Organize endpoints into logical groups using `APIRouter`. Each file in `app/api/` should correspond to a specific resource (e.g., `auth.py`, `keys.py`).
*   **Explicit Status Codes:** Use explicit status codes for responses (e.g., `status_code=status.HTTP_201_CREATED`) to be clear about the operation's result.
*   **Error Handling:** Use FastAPI's `HTTPException` for standard HTTP errors. For custom or unhandled exceptions, use a custom exception handler middleware.

### Pydantic

*   **Explicit Schemas:** Every API endpoint must define its request body and response model using Pydantic schemas located in `app/schemas/`. Do not use raw `dict`s.
*   **Specific Types:** Use Pydantic's specific types for validation where possible (e.g., `EmailStr`, `UUID`).
*   **Request vs. Response Models:** Create separate schemas for creating/updating data (e.g., `UserCreate`) and for reading data (`UserRead`). This is critical to prevent accidentally exposing sensitive fields like password hashes in API responses.

### Alembic (Database Migrations)

*   **Autogenerate & Review:** Always generate migrations with `alembic revision --autogenerate`. After generation, **you must manually review the migration file** to ensure it is correct and does not contain unintended changes.
*   **Atomic Migrations:** Each migration should represent a single, atomic change to the schema. Avoid bundling multiple unrelated changes into one migration.
*   **Never Edit Applied Migrations:** Never modify a migration file that has already been committed and potentially applied by others. If a change is needed, create a new migration.
*   **Test Downgrades:** Ensure the `downgrade()` function in a migration is tested and correctly reverts the schema.

### React

*   **Functional Components & Hooks:** All new components must be functional components using Hooks (`useState`, `useEffect`, etc.). Avoid class components.
*   **Component Structure:** Keep components small and focused on a single responsibility. If a component becomes too large or complex, break it down into smaller, reusable components.
*   **State Management:** For simple, local state, use `useState`. For state that needs to be shared across multiple components, use the Context API (`useContext`). For complex, application-wide state, a dedicated library like Redux or Zustand should be considered. Avoid "prop drilling."
*   **Services:** All API interactions should be handled in a dedicated service layer (`src/services/api.js`), not directly within components.

### Google Material UI (MUI) - *Future Use*

*   **Theming:** All styling (colors, typography, spacing) must be managed through a central theme file using `createTheme` and `ThemeProvider`. Do not use hardcoded colors or styles in components.
*   **Grid System:** Use the `<Grid>` component for all page layouts to ensure responsiveness.
*   **Component Composition:** Prefer using and composing the built-in MUI components (`<Button>`, `<TextField>`, `<Card>`, etc.) over creating custom-styled elements from scratch.
*   **Styling:** For minor, one-off style adjustments, use the `sx` prop. For creating reusable, styled components, use the `styled()` utility.

### Pytest

*   **Fixtures for Setup & Mocks:** Use `@pytest.fixture` for all test setup, including creating mock objects. This keeps tests clean, readable, and focused on the logic being tested.
*   **`pytest-asyncio` for Async Tests:**
    *   All asynchronous tests must be decorated with `@pytest.mark.asyncio`.
    *   Configure `pytest.ini` with `[pytest]\nasyncio_mode = auto` to ensure the asyncio event loop is managed correctly by the test runner.
*   **Mocking with `unittest.mock`:**
    *   Use `unittest.mock.patch` to replace dependencies (like services or external clients) within the scope of a test.
    *   **Crucially for async code:** Use `unittest.mock.AsyncMock`.
    *   **Mocking `await` calls:** To mock `await some_async_function()`, ensure the mock is an `AsyncMock` and set its `return_value` directly to the final, resolved value you expect. The `AsyncMock` wrapper makes the method call itself awaitable. For example: `mock_redis.get.return_value = 'some_value'`. A `TypeError` during an `await` call often means the mock is incorrectly returning another mock object instead of a final value.
    *   **Mocking `async with` Context Managers:** This is a complex but critical pattern that has been a major blocker. The `AttributeError: __aenter__` is the primary symptom of getting this wrong. The core issue arises when testing a service that calls an `async def` function which, in turn, returns an async context manager object (e.g., `async with await get_exchange(...) as manager:`).
        *   **The Problem:** Simply patching the `async def` function with `new_callable=AsyncMock` is not enough. The `async with` statement `await`s the patched function, receives the mock's `return_value`, and then tries to call `__aenter__` on that `return_value`. If the `return_value` is not a properly configured async context manager, the test fails.
        *   **The Solution:** The most robust and reliable solution is to create a dedicated helper class that impersonates the async context manager. This class is then used as the `return_value` of the patched `async def` function.

            ```python
            # In your test file (e.g., conftest.py or the test file itself)
            from unittest.mock import AsyncMock

            class MockAsyncContextManager:
                """
                A helper class to robustly mock an async context manager.
                """
                def __init__(self, mock_instance_to_return):
                    # This is the mock that will be assigned to the 'as' variable
                    self.mock_instance = mock_instance_to_return
                async def __aenter__(self):
                    return self.mock_instance
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            # --- Example Usage in a test ---
            # @pytest.mark.asyncio
            # async def test_my_function(mock_exchange_manager):
            #     # 1. Create the mock context manager, telling it what to return
            #     mock_context = MockAsyncContextManager(mock_exchange_manager)
            #
            #     # 2. Patch the 'async def' function that returns the context manager
            #     with patch('path.to.get_exchange', new_callable=AsyncMock) as mock_get_exchange:
            #         # 3. Set its return_value to be our helper instance
            #         mock_get_exchange.return_value = mock_context
            #
            #         # 4. Now, when the application code runs, it will work as expected
            #         await function_that_uses_get_exchange()
            #
            #         # 5. Assert that the original function was awaited
            #         mock_get_exchange.assert_awaited_once()
            ```
*   **Debugging Failing Tests:** When a test fails, especially with mocks:
    *   Read the full traceback. Errors like `TypeError: object X can't be used in 'await' expression` are a strong clue that a mock is returning another mock instead of a value.
    *   Don't hesitate to temporarily add `print(type(my_variable))` to the *application code* being tested to see exactly what the mock is providing at runtime. This was critical in solving our `precision_service` test failures.
*   **Assertions:** Use simple, clear `assert` statements. Pytest's rich assertion introspection provides detailed failure messages without needing special `assertEqual` methods.

### AI Assistant Protocol

*   **Verification First:** Before starting a work session, verify the current state (running processes, git status, directory structure).
*   **One Task at a Time:** Focus on a single, specific task. Propose code or commands before executing and wait for approval.
*   **Verify After Changes:** After every modification, confirm that the change was applied correctly, there are no syntax errors, services are running, and relevant tests pass.
*   **Error Handling:** If an error occurs, stop immediately, present the full error message, explain the cause, and propose a solution before retrying.
*   **End of Session:** Commit all changes with a clear message, document what was completed, and list any pending tasks.