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
    - Double-check the endpoint URL. The correct format is `/api/webhook/webhook/{user_id}`.
    - Verify the `user_id` exists in the database.
5.  **API returns 403 Forbidden:**
    - This indicates a permissions issue. Verify that the logged-in user has the required role (e.g., "admin") to access the requested endpoint.

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
  curl -X POST -H "Content-Type: application/json" -d '{"secret": "test", "tv": {"symbol": "BTC/USDT", "exchange": "binance"}, "execution_intent": {"action": "buy", "amount": 0.001, "strategy": "grid"}}' "http://localhost:8000/api/webhook/webhook/$USER_ID"
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

### Frontend Development Plan

The frontend will be developed using a Test-Driven Development (TDD) approach with Google's Material UI (MUI) for the component library.

1.  **Setup Material UI (MUI):** Add the necessary MUI dependencies (`@mui/material`, `@emotion/react`, `@emotion/styled`, `@mui/icons-material`) to the `frontend/package.json` to start using its components.
2.  **Establish TDD Workflow:** Utilize the existing Jest and React Testing Library setup. For each new component, the workflow will be:
    *   Write a test file (`.test.js`) that asserts the component renders correctly and handles user interactions.
    *   Create the component file, which will initially fail the tests.
    *   Implement the component to make the tests pass.
3.  **First Component (Login Page):** The first step is to refactor the existing login functionality in `App.js` into its own dedicated, well-structured, and styled `Login` component, following the TDD workflow.

### Google Material UI (MUI) - *Future Use*

*   **Theming:** All styling (colors, typography, spacing) must be managed through a central theme file using `createTheme` and `ThemeProvider`. Do not use hardcoded colors or styles in components.
*   **Grid System:** Use the `<Grid>` component for all page layouts to ensure responsiveness.
*   **Component Composition:** Prefer using and composing the built-in MUI components (`<Button>`, `<TextField>`, `<Card>`, etc.) over creating custom-styled elements from scratch.
*   **Styling:** For minor, one-off style adjustments, use the `sx` prop. For creating reusable, styled components, use the `styled()` utility.

### FastAPI Integration Testing (`pytest`)

This section outlines the definitive patterns for writing reliable integration tests for the FastAPI backend, covering both database setup and the critical challenge of database session management.

#### 1. The Core Problem: Transactional Session Isolation

*   **Symptom:** Tests consistently fail with `404 Not Found` errors when an API endpoint tries to fetch data that was just created in the test function. Diagnostic logs show the data exists in the test's session but is `None` in the endpoint's session.
*   **Root Cause:** The FastAPI `TestClient` runs the application in a separate thread. When a test creates data and a `TestClient` makes a request, they are operating in **different transactional scopes**. A `db.commit()` in the test will not make the data visible to the `TestClient`'s transaction, and relying on separate `db.commit()` and cleanup steps is unreliable and prone to race conditions.

#### 2. The Solution: A Unified, Transactional Fixture Set

The definitive solution is a set of fixtures that work together to create a clean database for each test run and ensure the entire test—from data setup to the API call and assertions—runs within a **single, shared database transaction**.

**Step 1: `db_engine` Fixture (Session-Scoped)**

This fixture is responsible for the database itself. It runs only once per test session.

*   **`conftest.py` - Database Engine Fixture:**
    ```python
    @pytest.fixture(scope="session")
    def db_engine():
        """
        Creates a test database with a random name, creates all tables, and yields an engine to it.
        """
        db_name = f"test_db_{uuid.uuid4().hex}"
        
        # Connect to default postgres to create test database
        default_db_url = str(settings.DATABASE_URL).replace(settings.DATABASE_URL.split("/")[-1], "postgres")
        default_engine = create_engine(default_db_url, isolation_level="AUTOCOMMIT")
        
        with default_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {db_name}"))
        
        # Now connect to the test database
        engine = create_engine(str(settings.DATABASE_URL).replace(settings.DATABASE_URL.split("/")[-1], db_name))
        
        Base.metadata.create_all(bind=engine)

        yield engine

        # Teardown: drop all tables and the test database
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        
        with default_engine.connect() as conn:
            # Terminate all connections to the test database
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                  AND pid <> pg_backend_pid();
            """))
            conn.execute(text(f"DROP DATABASE {db_name}"))
        default_engine.dispose()
    ```

**Step 2: `client` Fixture (Function-Scoped)**

This is the most critical fixture. It uses the `db_engine` and runs for every single test function, providing both the `TestClient` and a transactional `db_session`.

*   **`conftest.py` - The Correct Transactional Client Fixture:**
    ```python
    @pytest.fixture(scope="function")
    def client(db_engine):
        """
        Creates a FastAPI TestClient that uses a single, shared transaction
        for the entire test. The transaction is rolled back after the test is
        finished, ensuring a clean state.

        This fixture yields both the TestClient and the transactional session.
        """
        # 1. Establish a connection and begin a transaction
        connection = db_engine.connect()
        transaction = connection.begin()

        # 2. Create a session bound to this transaction
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
        session = SessionLocal()

        # 3. CRITICAL: Override the app's database dependency to use our transactional session
        def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        # 4. Yield the client and session to the test
        with TestClient(app) as test_client:
            yield test_client, session

        # 5. Teardown: clean up everything
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()  # Roll back the transaction to isolate the test
        connection.close()
    ```

#### 3. Test Implementation Pattern

Tests must use the `client` fixture and follow a specific pattern for data creation and API calls.

*   **`test_trading_flow.py` - The Correct Test Pattern:**
    ```python
    from app.services.jwt_service import create_access_token # Don't forget this import

    def test_webhook_to_live_position(client): # Only the 'client' fixture is needed
        """
        Test the full trading flow from webhook ingestion to a live position.
        """
        # 1. Unpack the client and session from the fixture
        test_client, db_session = client

        # 2. Arrange: Create all test data using the provided db_session
        user_in = UserCreate(...)
        test_user = create_user(db_session, user_in)
        
        # 3. CRITICAL: Use flush() to persist data within the transaction.
        #    This makes the user object available in the database for the API
        #    call to find. DO NOT use commit() here, as it would end the
        #    transaction prematurely.
        db_session.flush()
        db_session.refresh(test_user) # Refresh to get DB-generated values like UUIDs

        # ... create other necessary data (e.g., ExchangeConfig) and flush ...

        # 4. Arrange: Prepare the API call (including authentication)
        access_token = create_access_token(
            user_id=test_user.id, email=test_user.email, role=test_user.role
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {...} # Your webhook payload
        
        # 5. Act: Make the API call using the TestClient
        response = test_client.post(
            f"/api/webhook/webhook/{test_user.id}", json=payload, headers=headers
        )

        # 6. Assert: Verify the response and the final database state
        assert response.status_code == 200
        
        # The db_session is the same one used by the endpoint, so the state is consistent
        position_group = db_session.query(PositionGroup).one_or_none()
        assert position_group is not None
    ```



### Testing Guidelines (`pytest`)



Testing is a critical part of our development process. All new business logic must be accompanied by comprehensive unit tests.



#### Core Principles

*   **Test-Driven Development (TDD):** Write a failing test *before* writing the implementation code.

*   **Isolation:** Unit tests must be isolated. They should not depend on external services like a running database or exchange. Use mocks to simulate these dependencies.

*   **Fixtures for Setup:** Use `@pytest.fixture` for all test setup (e.g., creating mock objects, test data). This keeps tests clean, readable, and focused on the logic being tested.



#### Asynchronous Code (`pytest-asyncio`)

*   All asynchronous test functions must be decorated with `@pytest.mark.asyncio`.

*   Ensure `pytest.ini` is configured with `asyncio_mode = auto`.



#### Mocking (`unittest.mock`)



Mocking is essential for isolating units of code. The following are critical patterns for this specific project.



**1. Mocking `await` calls:**

*   **Problem:** A `TypeError` occurs during an `await` call, often because the mock is returning another mock object instead of a final, awaitable value.

*   **Solution:** Use `unittest.mock.AsyncMock`. Set its `return_value` directly to the final, resolved value you expect the `await` to produce.

    ```python

    # Example: Mocking a service that fetches a value

    mock_service = AsyncMock()

    mock_service.get_value.return_value = 42



    # In the test:

    # This works because AsyncMock makes the call awaitable

    value = await mock_service.get_value()

    assert value == 42

    ```



**2. Mocking `async with` Context Managers:**

*   **Problem:** An `AttributeError: __aenter__` is raised. This is the most common and critical mocking challenge in this codebase, especially when testing services that use `get_exchange`.

*   **Solution:** The function that *returns* the async context manager (e.g., `get_exchange`) must be patched. Its `return_value` must be set to a helper object that correctly implements the `async def __aenter__` and `async def __aexit__` methods.



    ```python

    # In conftest.py or your test file, create this reusable helper:

    from unittest.mock import AsyncMock



    class MockAsyncContextManager:

        """A helper to robustly mock an async context manager."""

        def __init__(self, mock_instance_to_return):

            # This is the mock that will be assigned to the 'as' variable

            self.mock_instance = mock_instance_to_return

        async def __aenter__(self):

            return self.mock_instance

        async def __aexit__(self, exc_type, exc_val, exc_tb):

            pass



    # --- Example Usage in a test ---

    @pytest.mark.asyncio

    async def test_my_function_using_exchange(mock_exchange_manager):

        # 1. Create the mock context, telling it what the 'as' variable should be

        mock_context = MockAsyncContextManager(mock_exchange_manager)



        # 2. Patch the function that RETURNS the context manager

        with patch('path.to.get_exchange', return_value=mock_context) as mock_get_exchange:

            # 3. Now, the application code will work as expected

            await function_that_uses_get_exchange()



            # 4. Assert that the function was awaited to get the context

            mock_get_exchange.assert_awaited_once()

    ```



**3. Mocking Chained SQLAlchemy Queries:**

*   **Problem:** An `AssertionError` occurs when trying to assert calls on a mocked SQLAlchemy query chain (e.g., `db.query(...).filter(...).all()`). Often, the filter arguments are complex `BinaryExpression` objects that are difficult to match directly.

*   **Solution:**

    *   For asserting the filter call itself, use `unittest.mock.ANY`. This verifies that `filter` was called without being brittle about the exact SQLAlchemy expression.

    *   To return data, mock the final method in the chain (e.g., `.all()`, `.first()`, `.one_or_none()`) to return the desired test data (e.g., a list of mock model instances).



    ```python

    # In your test:

    mock_entry = MagicMock(spec=QueueEntry)

    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_entry]



    # In your application code:

    results = db.query(QueueEntry).filter(QueueEntry.user_id == user_id).all()



    # In your test assertions:

    mock_db_session.query.assert_called_once_with(QueueEntry)

    mock_db_session.query.return_value.filter.assert_called_once_with(ANY)

    assert results == [mock_entry]

    ```



**4. Mocking Configuration (`settings`):**

*   **Problem:** An `AttributeError` is raised when trying to patch a configuration object that doesn't exist (e.g., `settings.RISK_ENGINE_CONFIG`), or a `SyntaxError` occurs with multi-line `with patch.object(...)` statements.

*   **Solution:**

    *   Patch individual attributes on the `settings` object directly (e.g., `settings.RISK_LOSS_THRESHOLD_PERCENT`).

    *   For multi-line `with` statements, enclose the entire `patch.object` block in parentheses `()` to ensure correct parsing and avoid syntax errors.



    ```python

    # In your test:

    with (

        patch.object(settings, 'RISK_LOSS_THRESHOLD_PERCENT', Decimal("-10.0")),

        patch.object(settings, 'RISK_REQUIRE_FULL_PYRAMIDS', False),

        patch.object(settings, 'RISK_POST_FULL_WAIT_MINUTES', 30),

    ):

        # Your test logic here...

        result = my_function_that_uses_settings()

        assert result is True

    ```



#### Debugging Failing Tests

*   Read the full traceback carefully. Errors like `TypeError: object X can't be used in 'await' expression` or `AttributeError: __aenter__` are strong clues that a mock is configured incorrectly.

*   Use `print(type(my_variable))` or `print(my_mock.mock_calls)` inside the *application code* being tested to see exactly what the mock is providing at runtime. This is invaluable for debugging.



### AI Assistant Protocol



*   **Verification First:** Before starting a work session, verify the current state (running processes, git status, directory structure).

*   **One Task at a Time:** Focus on a single, specific task. Propose code or commands before executing and wait for approval.

*   **Verify After Changes:** After every modification, confirm that the change was applied correctly, there are no syntax errors, services are running, and relevant tests pass.

*   **Error Handling:** If an error occurs, stop immediately, present the full error message, explain the cause, and propose a solution before retrying.

*   **End of Session:** Commit all changes with a clear message, document what was completed, and list any pending tasks.
