# Upgrading Plan: From Skeleton to Full Execution Engine

## 1. Introduction

This document outlines the development plan to upgrade the current application from its foundational skeleton to the complete, feature-rich automated trading execution engine as defined in the original Scope of Work.

The current application has a functional backend for state management, a basic UI for displaying data, and is fully dockerized. The core trading logic, advanced features, and comprehensive UI are the key areas for development.

---

## 2. Current Application State

This section provides a clear summary of the application's current capabilities and limitations.

### What is Working:
- **Webhook Processing:** The backend can receive and validate TradingView webhooks.
- **State Management:** It correctly creates and stores records for `PositionGroups` and `Pyramids` in the PostgreSQL database.
- **Execution Pool & Queue:** The system enforces a maximum number of live positions and queues new signals when the limit is reached.
- **Risk Engine Foundation:** The basic logic for identifying losing trades and potential offsetting winners is in place.
- **Basic UI:** The React frontend can connect to the backend, fetch the list of all position groups, and display them in a simple table.
- **Dockerization:** The entire stack (backend, frontend, database) is containerized and runs via a single `docker-compose` command.

### What is Missing (The Gaps):
- **Core Trading Logic:** The application is a **state manager**, not an **execution engine**. It does not place any real orders on an exchange.
    - **No DCA/Pyramid Execution:** It does not calculate or place the required grid of DCA orders.
    - **No Take-Profit (TP) Logic:** The TP manager is a placeholder and does not monitor prices or close trades.
    - **No Exit Logic:** It does not handle exit signals from TradingView.
- **Advanced Features:**
    - **Sophisticated Queue Priority:** The queue is currently FIFO (First-In-First-Out) and lacks the advanced priority ranking.
    - **Incomplete Risk Engine:** The risk engine only checks the loss threshold and does not implement timers, pyramid counts, or precise partial-closing logic.
- **Comprehensive UI:** The UI is a proof-of-concept and lacks the vast majority of required features:
    - No dashboard, detailed DCA view, risk panel, queue manager, logs viewer, or settings panel.
- **Configuration:** All settings are managed via `.env` files, not a user-friendly UI with a JSON backend as required.
- **Security & Logging:** API keys are stored in plaintext, and logging is done via basic `print` statements.

---

# ULTRA-DETAILED TRADING ENGINE DEVELOPMENT PLAN
## ZERO-AMBIGUITY SPECIFICATION FOR AI CODING ASSISTANT

## PHASE 0: MULTI-USER AUTHENTICATION & SECURITY FOUNDATION
**Duration:** 2 Weeks | **Priority:** CRITICAL

### Step 0.1: Database Schema Creation
**File:** `backend/app/models/user_models.py`

Create SQLAlchemy models with exact field specifications:

**User model fields:**
- `id`: UUID (primary_key, auto-generate)
- `email`: String(255), unique, not null
- `username`: String(100), unique, not null
- `password_hash`: String(255), not null
- `role`: Enum('viewer', 'trader', 'manager', 'admin'), default='viewer'
- `is_active`: Boolean, default=True
- `created_at`: DateTime, default=now()
- `last_login`: DateTime, nullable

**UserSession model fields:**
- `session_id`: UUID (primary_key)
- `user_id`: UUID (foreign_key)
- `created_at`: DateTime
- `expires_at`: DateTime
- `ip_address`: String(45)
- `user_agent`: String(500)

### Step 0.2: Password Security Service
**File:** `backend/app/services/auth_service.py`

Implement exactly these functions:
- `hash_password(password: str) -> str`: Use bcrypt with 12 rounds
- `verify_password(password: str, hashed: str) -> bool`: Use bcrypt check
- `generate_password_reset_token() -> str`: 32 character random string
- `validate_password_strength(password: str) -> bool`: Minimum 8 chars, 1 uppercase, 1 number

### Step 0.3: JWT Token Management
**File:** `backend/app/services/jwt_service.py`

Implement exactly these functions:
- `create_access_token(user_id: UUID, email: str, role: str) -> str`: 24 hour expiry
- `verify_token(token: str) -> dict`: Return payload or raise Exception
- `refresh_token(old_token: str) -> str`: Create new token if old token < 1 hour from expiry

### Step 0.4: Authentication API Endpoints
**File:** `backend/app/api/auth.py`

Create these exact endpoints:
- `POST /api/auth/register`: `{email, username, password, role}` → `{user, token}`
- `POST /api/auth/login`: `{email, password}` → `{user, token}`
- `POST /api/auth/logout`: `{token}` → `{success}`
- `POST /api/auth/refresh`: `{token}` → `{new_token}`
- `POST /api/auth/forgot-password`: `{email}` → `{success}`
- `POST /api/auth/reset-password`: `{token, new_password}` → `{success}`

### Step 0.5: Permission Middleware
**File:** `backend/app/middleware/auth_middleware.py`

Create these exact decorators:
- `@require_authenticated`: Any logged-in user
- `@require_role('trader')`: Trader or higher
- `@require_role('admin')`: Admin only

---

## PHASE 1: COMPREHENSIVE LOGGING SYSTEM
**Duration:** 1.5 Weeks | **Priority:** HIGH

### Step 1.1: Log Database Schema
**File:** `backend/app/models/log_models.py`

Create these exact models:

**SystemLog:**
- `id`: UUID
- `timestamp`: DateTime
- `level`: Enum('DEBUG','INFO','WARNING','ERROR','CRITICAL')
- `category`: Enum('SECURITY','TRADING','SYSTEM','RISK','API')
- `user_id`: UUID (nullable)
- `message`: Text
- `details`: JSON (nullable)
- `ip_address`: String(45) (nullable)

**AuditLog:**
- `id`: UUID
- `timestamp`: DateTime
- `user_id`: UUID
- `action`: String(100)
- `resource`: String(100)
- `resource_id`: String(100) (nullable)
- `details`: JSON (nullable)
- `ip_address`: String(45)

### Step 1.2: Structured Logging Service
**File:** `backend/app/services/logging_service.py`

Implement exactly these methods:
- `log_debug(category, message, user_id=None, details=None)`
- `log_info(category, message, user_id=None, details=None)`
- `log_warning(category, message, user_id=None, details=None)`
- `log_error(category, message, user_id=None, details=None)`
- `log_critical(category, message, user_id=None, details=None)`
- `audit_log(user_id, action, resource, resource_id=None, details=None)`

### Step 1.3: Log Management API
**File:** `backend/app/api/logs.py`

Create these exact endpoints:
- `GET /api/logs/system`: Query params: `level`, `category`, `start_date`, `end_date`, `limit=100`
- `GET /api/logs/audit`: Query params: `user_id`, `action`, `start_date`, `end_date`, `limit=100`
- `DELETE /api/logs/system/{days_old}`: Delete logs older than X days (admin only)
- `POST /api/logs/export`: Export logs as CSV/JSON (admin only)

### Step 1.4: Log Rotation & Retention
**File:** `backend/app/tasks/log_cleanup.py`

Create scheduled task that runs daily:
- Delete system logs older than 30 days
- Delete audit logs older than 90 days
- Compress logs older than 7 days

---

## PHASE 2: SECURE API KEY MANAGEMENT
**Duration:** 1 Week | **Priority:** HIGH

### Step 2.1: Key Storage Schema
**File:** `backend/app/models/key_models.py`

Create these exact models:

**ExchangeConfig:**
- `id`: UUID
- `user_id`: UUID (foreign_key)
- `exchange_name`: String(50)
- `mode`: Enum('testnet','live')
- `api_key_encrypted`: Text
- `api_secret_encrypted`: Text
- `is_enabled`: Boolean, default=False
- `is_validated`: Boolean, default=False
- `last_validated`: DateTime (nullable)
- `created_at`: DateTime

### Step 2.2: Encryption Service
**File:** `backend/app/services/encryption_service.py`

Implement exactly these methods:
- `encrypt_data(plaintext: str, key: str) -> str`: Use AES-256-GCM
- `decrypt_data(ciphertext: str, key: str) -> str`: Use AES-256-GCM
- `generate_master_key() -> str`: 32 byte random key
- `derive_key_from_password(password: str, salt: str) -> str`: Use PBKDF2 with 100,000 iterations

### Step 2.3: Key Management API
**File:** `backend/app/api/keys.py`

Create these exact endpoints (all require authentication):
- `POST /api/keys/{exchange}`: `{mode, api_key, api_secret}` → Store encrypted
- `GET /api/keys`: List user's exchange configurations
- `PUT /api/keys/{exchange}/validate`: Test connection, update validation status
- `DELETE /api/keys/{exchange}`: Remove exchange configuration
- `PUT /api/keys/{exchange}/mode`: `{mode}` → Switch between testnet/live

---

## PHASE 3: CORE TRADING ENGINE
**Duration:** 2 Weeks | **Priority:** HIGH

### Step 3.1: Trading Database Schema
**File:** `backend/app/models/trading_models.py`

Create these exact models:

**PositionGroup:**
- `id`: UUID
- `user_id`: UUID
- `exchange`: String(50)
- `symbol`: String(20)
- `timeframe`: String(10)
- `status`: Enum('waiting','live','partially_filled','closing','closed')
- `entry_signal`: JSON - Store original webhook data
- `created_at`: DateTime
- `updated_at`: DateTime

**DCAOrder:**
- `id`: UUID
- `position_group_id`: UUID
- `pyramid_level`: Integer
- `dca_level`: Integer
- `expected_price`: Decimal(20,8)
- `quantity`: Decimal(20,8)
- `filled_price`: Decimal(20,8) (nullable)
- `filled_quantity`: Decimal(20,8) (nullable)
- `status`: Enum('pending','filled','cancelled','failed')
- `exchange_order_id`: String(100) (nullable)

### Step 3.2: Exchange Manager Service
**File:** `backend/app/services/exchange_manager.py`

Implement exactly these methods:
- `get_balance(exchange: str, user_id: UUID) -> dict`
- `place_order(exchange: str, user_id: UUID, symbol: str, side: str, order_type: str, quantity: decimal, price: decimal = None) -> dict`
- `cancel_order(exchange: str, user_id: UUID, symbol: str, order_id: str) -> bool`
- `get_order_status(exchange: str, user_id: UUID, symbol: str, order_id: str) -> dict`
- `get_precision_rules(exchange: str, symbol: str) -> dict`

### Step 3.3: Precision Validation Service
**File:** `backend/app/services/precision_service.py`

Implement exactly these methods:
- `validate_and_adjust_order(exchange: str, symbol: str, side: str, quantity: decimal, price: decimal) -> tuple[decimal, decimal]`
- `fetch_precision_info(exchange: str, symbol: str) -> dict`
- `calculate_min_notional(quantity: decimal, price: decimal) -> decimal`

### Step 3.4: Webhook Processing
**File:** `backend/app/services/webhook_service.py`

Implement exactly these methods:
- `process_tradingview_webhook(webhook_data: dict, user_id: UUID) -> PositionGroup`
- `validate_webhook_signature(payload: dict, signature: str) -> bool`
- `create_position_group_from_signal(signal: dict, user_id: UUID) -> PositionGroup`
- `add_pyramid_to_group(position_group_id: UUID, signal: dict) -> PositionGroup`

---

## PHASE 4: DCA & PYRAMID EXECUTION
**Duration:** 1.5 Weeks | **Priority:** HIGH

### Step 4.1: Grid Calculator Service
**File:** `backend/app/services/grid_calculator.py`

Implement exactly these methods:
- `calculate_dca_levels(entry_price: decimal, dca_config: dict) -> list[dict]`
- `calculate_position_size(total_risk_usd: decimal, dca_weights: list) -> list[decimal]`
- `calculate_take_profit_prices(entry_prices: list[decimal], tp_percent: decimal) -> list[decimal]`

### Step 4.2: Order Placement Service
**File:** `backend/app/services/order_service.py`

Implement exactly these methods:
- `place_dca_orders(position_group: PositionGroup) -> list[DCAOrder]`
- `monitor_order_fills() -> None` - Background task
- `handle_filled_order(dca_order: DCAOrder, fill_data: dict) -> None`
- `cancel_pending_orders(position_group_id: UUID) -> None`

### Step 4.3: Take Profit Manager
**File:** `backend/app/services/take_profit_service.py`

Implement exactly these methods:
- `check_take_profit_conditions() -> None` - Background task
- `execute_per_leg_tp(position_group: PositionGroup) -> None`
- `execute_aggregate_tp(position_group: PositionGroup) -> None`
- `execute_hybrid_tp(position_group: PositionGroup) -> None`

---

## PHASE 5: RISK ENGINE & QUEUE MANAGEMENT
**Duration:** 1.5 Weeks | **Priority:** MEDIUM

### Step 5.1: Risk Engine Service
**File:** `backend/app/services/risk_engine.py`

Implement exactly these methods:
- `evaluate_risk_conditions() -> None` - Background task
- `should_activate_risk_engine(position_group: PositionGroup) -> bool`
- `find_losing_positions(user_id: UUID) -> list[PositionGroup]`
- `find_winning_positions(user_id: UUID) -> list[PositionGroup]`
- `execute_risk_mitigation(losing_position: PositionGroup, winning_positions: list[PositionGroup]) -> None`

### Step 5.2: Queue Management Service
**File:** `backend/app/services/queue_service.py`

Implement exactly these methods:
- `add_to_queue(signal: dict, user_id: UUID) -> QueueEntry`
- `promote_from_queue() -> QueueEntry`
- `calculate_priority(queue_entry: QueueEntry) -> float`
- `handle_signal_replacement(new_signal: dict, user_id: UUID) -> None`

---

## PHASE 6: BACKGROUND TASKS & SCHEDULING
**Duration:** 1 Week | **Priority:** MEDIUM

### Step 6.1: Task Scheduler Setup
**File:** `backend/app/services/task_scheduler.py`

Implement exactly these scheduled tasks:
- `monitor_order_fills`: Run every 10 seconds
- `check_take_profit_conditions`: Run every 15 seconds
- `evaluate_risk_conditions`: Run every 30 seconds
- `cleanup_old_logs`: Run once per day at 2:00 AM
- `validate_exchange_connections`: Run every 5 minutes

### Step 6.2: Health Monitoring
**File:** `backend/app/services/health_service.py`

Implement exactly these methods:
- `check_system_health() -> dict`
- `check_exchange_health(user_id: UUID) -> dict`
- `check_database_health() -> dict`
- `get_performance_metrics() -> dict`

---

## PHASE 7: COMPREHENSIVE TESTING SUITE
**Duration:** 1.5 Weeks | **Priority:** HIGH

### Step 7.1: Unit Test Structure
**File Structure:**
```
tests/
├── unit/
│   ├── test_auth_service.py
│   ├── test_exchange_manager.py
│   ├── test_precision_service.py
│   ├── test_grid_calculator.py
│   └── test_risk_engine.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_webhook_processing.py
│   └── test_trading_flow.py
└── conftest.py
```

### Step 7.2: Test Fixtures & Mocks
**File:** `tests/conftest.py`

Create these exact fixtures:
- `mock_exchange_api`: Mock all exchange API calls
- `test_user`: Create test user with trader role
- `test_position_group`: Create sample position group
- `mock_webhook_payload`: Sample TradingView webhook data

### Step 7.3: Test Coverage Requirements
- Achieve 90%+ code coverage
- Test all error conditions
- Test all edge cases
- Test all permission scenarios

---

## PHASE 8: FRONTEND UI DEVELOPMENT
**Duration:** 2 Weeks | **Priority:** MEDIUM

### Step 8.1: React Component Structure
**File Structure:**
```
frontend/src/
├── components/
│   ├── auth/
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   └── ForgotPassword.jsx
│   ├── trading/
│   │   ├── Dashboard.jsx
│   │   ├── Positions.jsx
│   │   └── OrderPanel.jsx
│   ├── risk/
│   │   ├── RiskEngine.jsx
│   │   └── QueueManager.jsx
│   └── admin/
│       ├── UserManagement.jsx
│       └── SystemLogs.jsx
├── services/
│   ├── api.js
│   └── websocket.js
└── hooks/
    ├── useAuth.js
    └── useWebSocket.js
```

### Step 8.2: API Service Layer
**File:** `frontend/src/services/api.js`

Implement exactly these methods:
- `auth.login(email, password)`
- `auth.register(userData)`
- `trading.getPositions()`
- `trading.placeOrder(orderData)`
- `risk.getQueue()`
- `admin.getLogs()`

---

## DEPLOYMENT & CONFIGURATION
**Duration:** 0.5 Weeks | **Priority:** LOW

### Step 9.1: Docker Configuration
**File:** `docker-compose.yml`
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/trading
      - JWT_SECRET=your-secret-key
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=trading
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:alpine
```

### Step 9.2: Environment Configuration
**File:** `.env.example`
```
DATABASE_URL=postgresql://user:pass@localhost:5432/trading
JWT_SECRET=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379
```

---

## IMPLEMENTATION ORDER - CRITICAL PATH
1. Phase 0.1-0.5 - Authentication & Security
2. Phase 1.1-1.4 - Logging System
3. Phase 2.1-2.3 - API Key Management
4. Phase 3.1-3.4 - Core Trading Models & Services
5. Phase 4.1-4.3 - DCA Execution
6. Phase 6.1-6.2 - Background Tasks
7. Phase 5.1-5.2 - Risk & Queue Management
8. Phase 7.1-7.3 - Testing Suite
9. Phase 8.1-8.2 - Frontend UI
10. Phase 9.1-9.2 - Deployment

---

## SUCCESS CRITERIA - EXACT REQUIREMENTS
### Authentication:
- ✅ Users can register, login, logout
- ✅ JWT tokens work with 24hr expiry
- ✅ Role-based permissions enforce correctly
- ✅ Password reset flow works

### Trading:
- ✅ TradingView webhooks processed correctly
- ✅ DCA orders placed with precision validation
- ✅ Take-profit triggers execute properly
- ✅ Risk engine mitigates losses automatically

### Security:
- ✅ API keys encrypted at rest
- ✅ All actions logged and auditable
- ✅ No sensitive data exposed in logs
- ✅ Rate limiting prevents abuse

### Testing:
- ✅ 90%+ code coverage achieved
- ✅ All critical paths tested
- ✅ Error conditions handled gracefully
- ✅ Performance meets requirements (<100ms per operation)

This plan provides zero-ambiguity specifications. An AI coding assistant can execute this step-by-step without confusion, following the exact file structures, method names, and implementation details provided.