# Execution Engine - Development Plan

## 📋 Project Overview
Building a fully automated trading execution engine with integrated web UI that:
- Receives TradingView webhooks
- Executes grid-based entries with pyramids and DCA
- Runs autonomous risk management
- Enforces position limits via pool + queue system
- Provides real-time monitoring dashboard

**Tech Stack:** Python FastAPI (Backend) + React (Frontend) + PostgreSQL (Database)

---

## 🎯 Phase 1: Foundation & Core Infrastructure (Week 1-2)

### 1.1 Project Setup & Environment
**Goal:** Establish clean, reproducible development environment

**Tasks:**
- [ ] Initialize Git repository with proper `.gitignore`
- [ ] Create project structure:
  ```
  ex_engine/
  ├── backend/
  │   ├── app/
  │   │   ├── api/
  │   │   ├── core/
  │   │   ├── models/
  │   │   ├── services/
  │   │   └── utils/
  │   ├── tests/
  │   ├── alembic/
  │   ├── requirements.txt
  │   └── main.py
  ├── frontend/
  │   ├── src/
  │   ├── public/
  │   └── package.json
  ├── docker-compose.yml
  └── README.md
  ```
- [ ] Set up Python virtual environment
- [ ] Create `requirements.txt` with core dependencies:
  - FastAPI
  - uvicorn
  - SQLAlchemy
  - alembic
  - psycopg2
  - python-jose (JWT)
  - python-multipart
  - ccxt (exchange connectivity)
  - pydantic
  - redis (optional for rate limiting)

**Validation:**
```bash
# Test backend starts without errors
cd backend
uvicorn main:app --reload

# Verify it responds
curl http://localhost:8000/health
```

---

### 1.2 Database Schema Design
**Goal:** Create robust data models for all entities

**Models to Create:**

1. **User** (authentication)
   - id, username, hashed_password, created_at

2. **APIKey** (exchange credentials)
   - id, user_id, exchange, encrypted_api_key, encrypted_secret, is_testnet, is_active

3. **PositionGroup** (core trading entity)
   - id, user_id, api_key_id, pair, timeframe, status, avg_entry_price
   - unrealized_pnl_percent, unrealized_pnl_usd, tp_mode
   - created_at, closed_at, last_pyramid_at

4. **Pyramid** (entry layers)
   - id, position_group_id, entry_price, created_at

5. **DCALeg** (individual orders within pyramid)
   - id, pyramid_id, price_gap, capital_weight, tp_target
   - fill_price, status, order_id, filled_at

6. **QueuedSignal** (waiting entries)
   - id, user_id, pair, timeframe, payload, status
   - replacement_count, priority_rank, created_at

7. **WebhookLog** (audit trail)
   - id, timestamp, payload, status, error_message

**Database Tasks:**
- [ ] Create SQLAlchemy models in `backend/app/models/`
- [ ] Set up Alembic for migrations
- [ ] Create initial migration: `alembic revision --autogenerate -m "initial schema"`
- [ ] Apply migration: `alembic upgrade head`
- [ ] Create indexes on frequently queried fields (pair, timeframe, status, user_id)

**Validation:**
```bash
# Check tables created
psql -U postgres -d ex_engine_db -c "\dt"

# Verify relationships
psql -U postgres -d ex_engine_db -c "\d+ position_groups"
```

---

### 1.3 Configuration Management
**Goal:** Centralized, type-safe configuration

**Tasks:**
- [ ] Create `backend/app/core/config.py` using Pydantic BaseSettings
- [ ] Define config groups:
  ```python
  class AppSettings(BaseSettings):
      mode: str = "webapp_self_contained"
      data_dir: str = "./engine_data"
      log_level: str = "info"
  
  class ExchangeSettings(BaseSettings):
      name: str = "binance"
      api_key: str
      api_secret: str
      testnet: bool = True
      precision_refresh_sec: int = 60
  
  class ExecutionPoolSettings(BaseSettings):
      max_open_groups: int = 10
      count_pyramids_toward_pool: bool = False
  
  class RiskEngineSettings(BaseSettings):
      loss_threshold_percent: float = -5.0
      require_full_pyramids: bool = True
      post_full_wait_minutes: int = 60
  ```
- [ ] Create `.env.example` template
- [ ] Implement config validation
- [ ] Add config reload endpoint for UI changes

**Validation:**
```python
# Test config loads correctly
from app.core.config import settings
print(settings.exchange.testnet)  # Should print True
```

---

## 🔧 Phase 2: Exchange Integration & Precision (Week 3)

### 2.1 Exchange Manager
**Goal:** Safe, validated order execution across exchanges

**Tasks:**
- [ ] Create `backend/app/services/exchange_manager.py`
- [ ] Implement exchange factory pattern:
  ```python
  class ExchangeManager:
      def __init__(self, api_key_record):
          self.exchange = self._init_exchange(api_key_record)
      
      def fetch_precision(self, symbol) -> PrecisionData:
          """Get tick_size, step_size, min_notional"""
      
      def validate_order(self, symbol, side, price, quantity):
          """Pre-flight validation before order"""
      
      def place_order(self, symbol, side, order_type, quantity, price):
          """Execute order with error handling"""
  ```
- [ ] Implement precision caching (Redis or in-memory)
- [ ] Add precision refresh scheduler
- [ ] Create precision validation utilities:
  - `round_to_tick_size(price, tick_size)`
  - `round_to_step_size(quantity, step_size)`
  - `validate_min_notional(price, quantity, min_notional)`

**Validation:**
```python
# Test precision fetching
manager = ExchangeManager(api_key)
precision = manager.fetch_precision("BTCUSDT")
assert precision.tick_size == 0.01
assert precision.step_size == 0.00001

# Test order validation
is_valid, reason = manager.validate_order(
    "BTCUSDT", "buy", 50000.0, 0.001
)
```

---

### 2.2 Exchange Mock for Testing
**Goal:** Test without real API calls

**Tasks:**
- [ ] Create `backend/app/services/mock_exchange.py`
- [ ] Implement simulated order fills
- [ ] Mock precision data
- [ ] Add configurable latency and error injection

---

## 📡 Phase 3: Webhook Receiver & Signal Processing (Week 4)

### 3.1 Webhook Endpoint
**Goal:** Secure, validated webhook ingestion

**Tasks:**
- [ ] Create `backend/app/api/webhooks.py`
- [ ] Implement signature verification:
  ```python
  @router.post("/webhook")
  async def receive_webhook(
      request: Request,
      signature: str = Header(None)
  ):
      payload = await request.json()
      
      # Verify signature
      if not verify_signature(payload, signature):
          raise HTTPException(401, "Invalid signature")
      
      # Log webhook
      log_webhook(payload)
      
      # Queue for processing
      await process_signal(payload)
  ```
- [ ] Create `WebhookPayload` Pydantic model for validation
- [ ] Implement async signal processing queue
- [ ] Add webhook logging to database

**Validation:**
```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Signature: test_signature" \
  -d '{
    "secret": "test",
    "tv": {
      "exchange": "BINANCE",
      "symbol": "BTCUSDT",
      "action": "buy"
    },
    "execution_intent": {
      "type": "signal",
      "side": "buy"
    }
  }'
```

---

### 3.2 Signal Parser & Validator
**Goal:** Transform webhook into actionable trade signal

**Tasks:**
- [ ] Create `backend/app/services/signal_processor.py`
- [ ] Implement signal classification:
  - New entry (creates Position Group)
  - Pyramid (adds to existing group)
  - Exit (closes group)
- [ ] Validate signal completeness
- [ ] Enrich signal with precision data
- [ ] Add signal deduplication logic

---

## 🎯 Phase 4: Core Trading Logic (Week 5-6)

### 4.1 Position Group Manager
**Goal:** Manage lifecycle of Position Groups

**Tasks:**
- [ ] Create `backend/app/services/position_manager.py`
- [ ] Implement methods:
  ```python
  class PositionGroupManager:
      def create_group(signal) -> PositionGroup:
          """Create new Position Group from signal"""
      
      def add_pyramid(group_id, signal) -> Pyramid:
          """Add pyramid to existing group"""
      
      def calculate_dca_orders(pyramid, config) -> List[DCALeg]:
          """Generate DCA orders based on grid config"""
      
      def place_pyramid_orders(pyramid):
          """Submit entry + all DCA orders"""
      
      def close_group(group_id, reason):
          """Close all positions and cancel orders"""
  ```
- [ ] Implement DCA calculation logic:
  ```python
  # Example: 5 DCA legs with -0.5%, -1%, -1.5%, -2% gaps
  for i, leg in enumerate(dca_config):
      price_gap = leg.gap_percent
      fill_price = entry_price * (1 + price_gap)
      quantity = total_capital * leg.weight / fill_price
  ```
- [ ] Add order tracking and fill monitoring
- [ ] Implement partial fill handling

**Validation:**
```python
# Test Position Group creation
signal = parse_webhook(webhook_payload)
group = position_manager.create_group(signal)
assert group.status == "Live"
assert len(group.pyramids) == 1
assert len(group.pyramids[0].dca_legs) == 5
```

---

### 4.2 Take-Profit Manager
**Goal:** Monitor and execute TP logic

**Tasks:**
- [ ] Create `backend/app/services/tp_manager.py`
- [ ] Implement TP modes:
  ```python
  class TPManager:
      def check_per_leg_tp(group: PositionGroup):
          """Close individual legs when TP hit"""
      
      def check_aggregate_tp(group: PositionGroup):
          """Close entire group when avg TP hit"""
      
      def check_hybrid_tp(group: PositionGroup):
          """Run both, first trigger wins"""
  ```
- [ ] Add continuous price monitoring loop
- [ ] Implement TP execution with order cancellation
- [ ] Handle partial closes vs full closes

**Validation:**
```python
# Test TP detection
group = get_position_group(group_id)
current_price = 51000  # Assume entry was 50000
tp_hit = tp_manager.check_per_leg_tp(group)
assert tp_hit.leg_id == "DCA0"
assert tp_hit.profit_percent == 2.0
```

---

## 🛡️ Phase 5: Execution Pool & Queue System (Week 7)

### 5.1 Execution Pool Manager
**Goal:** Enforce max position limits

**Tasks:**
- [ ] Create `backend/app/services/pool_manager.py`
- [ ] Implement slot management:
  ```python
  class ExecutionPoolManager:
      def get_open_slots(user_id) -> int:
          """Count available slots"""
      
      def can_open_position(user_id) -> bool:
          """Check if new group allowed"""
      
      def consume_slot(group: PositionGroup):
          """Mark slot as used"""
      
      def release_slot(group_id):
          """Free slot when group closes"""
  ```
- [ ] Add slot reservation system
- [ ] Implement pyramid exemption logic (doesn't consume slot)

---

### 5.2 Queue Manager
**Goal:** Priority-based signal queuing

**Tasks:**
- [ ] Create `backend/app/services/queue_manager.py`
- [ ] Implement queue operations:
  ```python
  class QueueManager:
      def add_to_queue(signal, user_id):
          """Add signal to waiting queue"""
      
      def replace_signal(existing_id, new_signal):
          """Replace queued signal, increment counter"""
      
      def calculate_priority(signal) -> float:
          """Score signal based on priority rules"""
      
      def promote_next(user_id) -> QueuedSignal:
          """Get highest priority queued signal"""
  ```
- [ ] Implement priority algorithm:
  1. Same pair/timeframe (pyramid continuation) = auto-priority
  2. Highest loss % (deepest discount)
  3. Highest replacement count
  4. FIFO fallback
- [ ] Add queue cleanup (remove on exit signal)

**Validation:**
```python
# Test queue priority
queue_manager.add_to_queue(signal1, user_id)
queue_manager.add_to_queue(signal2, user_id)
next_signal = queue_manager.promote_next(user_id)
assert next_signal.priority_rank == 1
```

---

## ⚠️ Phase 6: Risk Engine (Week 8-9)

### 6.1 Risk Evaluator
**Goal:** Identify losing trades and offsetting winners

**Tasks:**
- [ ] Create `backend/app/services/risk_engine.py`
- [ ] Implement activation checks:
  ```python
  class RiskEngine:
      def should_activate(group: PositionGroup) -> bool:
          """Check: 5 pyramids + timer + loss threshold"""
      
      def select_losing_group(user_id) -> PositionGroup:
          """Rank by loss %, then loss USD, then age"""
      
      def calculate_required_usd(group: PositionGroup) -> float:
          """Get absolute unrealized loss"""
      
      def select_winning_groups(user_id, required_usd) -> List[PositionGroup]:
          """Pick up to 3 winners by profit USD"""
  ```
- [ ] Implement timer logic:
  - Track timer start based on config (after_5_pyramids, after_all_dca_submitted, etc.)
  - Handle timer reset on replacement
- [ ] Add age filter if enabled

---

### 6.2 Risk Executor
**Goal:** Execute offset trades

**Tasks:**
- [ ] Implement partial close logic:
  ```python
  def execute_risk_offset(loser: PositionGroup, winners: List[PositionGroup]):
      required_usd = abs(loser.unrealized_pnl_usd)
      covered_usd = 0.0
      
      for winner in winners:
          if covered_usd >= required_usd:
              break
          
          close_usd = min(
              winner.unrealized_pnl_usd,
              required_usd - covered_usd
          )
          
          close_quantity = calculate_close_quantity(winner, close_usd)
          place_close_order(winner, close_quantity)
          covered_usd += close_usd
  ```
- [ ] Add risk action logging
- [ ] Implement post-close validation
- [ ] Handle edge cases (winner closes before loser)

**Validation:**
```python
# Test risk engine activation
loser = get_position_group(loser_id)
assert loser.unrealized_pnl_percent < -5.0
assert risk_engine.should_activate(loser) == True

# Test offset calculation
winners = risk_engine.select_winning_groups(user_id, 100.0)
assert sum(w.unrealized_pnl_usd for w in winners) >= 100.0
```

---

## 🔄 Phase 7: Background Tasks & Monitoring (Week 10)

### 7.1 Task Scheduler
**Goal:** Continuous monitoring loops

**Tasks:**
- [ ] Create `backend/app/services/scheduler.py`
- [ ] Implement background tasks:
  ```python
  @repeat_every(seconds=10)
  async def check_take_profits():
      """Monitor all live groups for TP"""
  
  @repeat_every(seconds=10)
  async def run_risk_engine():
      """Evaluate risk engine conditions"""
  
  @repeat_every(seconds=60)
  async def refresh_precision_data():
      """Update tick/step sizes"""
  
  @repeat_every(seconds=30)
  async def process_queue():
      """Check for available pool slots"""
  ```
- [ ] Add task error handling and recovery
- [ ] Implement task status monitoring

---

### 7.2 PnL Calculator
**Goal:** Real-time PnL tracking

**Tasks:**
- [ ] Create `backend/app/services/pnl_calculator.py`
- [ ] Implement calculations:
  ```python
  def calculate_unrealized_pnl(group: PositionGroup, current_price) -> PnL:
      total_quantity = sum(leg.filled_quantity for leg in group.dca_legs)
      avg_entry = group.avg_entry_price
      unrealized_usd = (current_price - avg_entry) * total_quantity
      unrealized_percent = (unrealized_usd / (avg_entry * total_quantity)) * 100
      return PnL(usd=unrealized_usd, percent=unrealized_percent)
  ```
- [ ] Update PnL on every price update
- [ ] Store PnL history for performance dashboard

---

## 🎨 Phase 8: Frontend - Core UI (Week 11-12)

### 8.1 React Project Setup
**Goal:** Clean, modern React app

**Tasks:**
- [ ] Initialize React app: `npx create-react-app frontend --template typescript`
- [ ] Install dependencies:
  - React Router
  - Axios
  - TanStack Query (React Query)
  - Tailwind CSS
  - Recharts (for charts)
  - date-fns (date formatting)
- [ ] Set up folder structure:
  ```
  src/
  ├── components/
  ├── pages/
  ├── services/
  ├── hooks/
  ├── types/
  └── App.tsx
  ```
- [ ] Configure Tailwind CSS
- [ ] Create dark/light theme system

**Validation:**
```bash
npm start
# Should open http://localhost:3000
```

---

### 8.2 Authentication UI
**Goal:** Login/register system

**Tasks:**
- [ ] Create login page
- [ ] Create registration page
- [ ] Implement JWT token storage
- [ ] Add protected route wrapper
- [ ] Create API service:
  ```typescript
  // src/services/api.ts
  export const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  
  api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  ```

---

### 8.3 Dashboard - Live Overview
**Goal:** Main monitoring screen

**Components to Create:**

1. **Stats Cards Row**
   - Total Active Position Groups
   - Execution Pool Usage (X/10)
   - Queued Signals Count
   - Total PnL (USD + %)

2. **Position Groups Table**
   ```typescript
   interface PositionGroup {
     id: number;
     pair: string;
     timeframe: string;
     pyramids_count: number;
     dca_filled: string; // "3/5"
     avg_entry: number;
     unrealized_pnl: {
       usd: number;
       percent: number;
     };
     status: string;
   }
   ```

3. **Real-time Updates**
   - Use WebSocket or polling (React Query with refetchInterval)
   - Auto-refresh every 500ms

**Tasks:**
- [ ] Create `pages/Dashboard.tsx`
- [ ] Create `components/StatsCard.tsx`
- [ ] Create `components/PositionGroupsTable.tsx`
- [ ] Add expandable rows for DCA leg details
- [ ] Implement color-coded PnL (green/red)

---

### 8.4 Queue & Pool View
**Goal:** Visualize waiting signals and pool status

**Tasks:**
- [ ] Create `pages/QueueView.tsx`
- [ ] Show pool slots visually (10 circles, filled/empty)
- [ ] Display queued signals table with:
  - Priority rank
  - Replacement count
  - Time in queue
  - Expected profit
- [ ] Add "Promote" and "Remove" actions

---

### 8.5 Risk Engine Panel
**Goal:** Monitor risk actions

**Tasks:**
- [ ] Create `pages/RiskEnginePanel.tsx`
- [ ] Display for each Position Group:
  - Loss % and USD
  - Timer remaining
  - 5 pyramids reached? (✅/❌)
  - Available winning offsets
- [ ] Add manual controls:
  - "Run Now" button
  - "Skip Once" button
  - "Block Group" toggle

---

### 8.6 Logs Viewer
**Goal:** Searchable event log

**Tasks:**
- [ ] Create `pages/LogsViewer.tsx`
- [ ] Implement filters:
  - By level (Error, Warning, Info)
  - By category (Webhook, Order, Risk, Precision)
  - By date range
  - By pair/timeframe
- [ ] Add search bar
- [ ] Implement color-coded severity
- [ ] Add export to CSV button

---

### 8.7 Settings Panel
**Goal:** Full config editing UI

**Tasks:**
- [ ] Create `pages/Settings.tsx`
- [ ] Create form sections for each config group:
  - Exchange API (masked key input)
  - Execution Pool
  - Risk Engine
  - Grid Strategy
  - Queue Logic
- [ ] Add validation before saving
- [ ] Implement "Apply & Restart Engine" button
- [ ] Add "Reset to Defaults" button
- [ ] Show config preview before applying

---

## 📊 Phase 9: Performance Dashboard (Week 13)

### 9.1 Analytics Backend
**Goal:** Calculate performance metrics

**Tasks:**
- [ ] Create `backend/app/services/analytics.py`
- [ ] Implement calculations:
  ```python
  def calculate_equity_curve(user_id) -> List[EquityPoint]:
      """Daily cumulative PnL"""
  
  def calculate_win_rate(user_id) -> float:
      """Win % of closed trades"""
  
  def calculate_sharpe_ratio(user_id) -> float:
      """Risk-adjusted returns"""
  
  def calculate_max_drawdown(user_id) -> float:
      """Peak to trough decline"""
  ```
- [ ] Create API endpoints for analytics data

---

### 9.2 Performance UI
**Goal:** Visual performance metrics

**Tasks:**
- [ ] Create `pages/Performance.tsx`
- [ ] Add metric cards:
  - Realized PnL (day/week/month/all-time)
  - Win Rate %
  - Avg Win vs Avg Loss
  - Sharpe Ratio
  - Max Drawdown
- [ ] Create equity curve chart (Recharts LineChart)
- [ ] Create trade distribution histogram
- [ ] Add P&L by pair/timeframe breakdown
- [ ] Export performance report to CSV

---

## 🧪 Phase 10: Testing & Quality Assurance (Week 14)

### 10.1 Unit Tests
**Goal:** Comprehensive test coverage

**Tasks:**
- [ ] Set up pytest for backend
- [ ] Write tests for:
  - Signal parsing
  - DCA calculation
  - TP logic (all 3 modes)
  - Risk engine selection
  - Queue priority algorithm
  - Precision validation
- [ ] Create test fixtures for Position Groups
- [ ] Mock exchange API responses

**Target:** 80%+ code coverage

---

### 10.2 Integration Tests
**Goal:** End-to-end workflow testing

**Tasks:**
- [ ] Test complete signal flow:
  1. Webhook arrives
  2. Position Group created
  3. DCA orders placed
  4. TP monitoring starts
  5. TP hit, position closes
- [ ] Test queue promotion on slot release
- [ ] Test risk engine offset execution
- [ ] Test precision validation rejection

---

### 10.3 Load Testing
**Goal:** Ensure performance under load

**Tasks:**
- [ ] Simulate 100 concurrent webhooks
- [ ] Test with 50+ active Position Groups
- [ ] Measure response times
- [ ] Test database performance
- [ ] Identify bottlenecks

---

## 📦 Phase 11: Packaging & Deployment (Week 15)

### 11.1 Docker Setup
**Goal:** Containerized deployment

**Tasks:**
- [ ] Create `Dockerfile` for backend
- [ ] Create `Dockerfile` for frontend
- [ ] Create `docker-compose.yml`:
  ```yaml
  version: '3.8'
  services:
    postgres:
      image: postgres:15
      environment:
        POSTGRES_DB: ex_engine_db
        POSTGRES_USER: ex_engine_user
        POSTGRES_PASSWORD: ${DB_PASSWORD}
      volumes:
        - postgres_data:/var/lib/postgresql/data
    
    backend:
      build: ./backend
      ports:
        - "8000:8000"
      depends_on:
        - postgres
      environment:
        DATABASE_URL: postgresql://ex_engine_user:${DB_PASSWORD}@postgres/ex_engine_db
    
    frontend:
      build: ./frontend
      ports:
        - "3000:3000"
  
  volumes:
    postgres_data:
  ```
- [ ] Test full stack with `docker-compose up`

---

## 📚 Phase 12: Documentation (Week 16)

### 12.1 User Documentation
**Tasks:**
- [ ] Write installation guide
- [ ] Create quickstart tutorial
- [ ] Document configuration options
- [ ] Add troubleshooting section
- [ ] Create video walkthrough (optional)

---

### 12.2 Technical Documentation
**Tasks:**
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Database schema diagram
- [ ] Architecture overview
- [ ] Development setup guide
- [ ] Contributing guidelines

---

## 🚀 Phase 13: Launch Preparation (Week 17)

### 13.1 Security Audit
**Tasks:**
- [ ] Review API key encryption
- [ ] Test webhook signature validation
- [ ] Check SQL injection vulnerabilities
- [ ] Verify CORS settings
- [ ] Test rate limiting
- [ ] Review error messages (no sensitive data leakage)

---

### 13.2 Final Checks
**Tasks:**
- [ ] Load testing with realistic scenarios
- [ ] Cross-platform testing (Windows + macOS)
- [ ] Browser compatibility (Chrome, Firefox, Safari)
- [ ] Performance profiling
- [ ] Memory leak detection
- [ ] Log rotation verification

---

## 📋 AI Assistant Working Protocol

### For Each Development Session:

1. **Start with Verification**
   ```
   "Before starting, please:
   1. List all currently running screen/tmux sessions
   2. Show me the status of Docker containers
   3. Confirm the last git commit message
   4. Show me the current directory structure"
   ```

2. **One Task at a Time**
   ```
   "Let's work on [SPECIFIC TASK]. 
   Please show me the code/command first before executing.
   Wait for my approval before proceeding."
   ```

3. **After Each Change**
   ```
   "Please verify:
   1. The change was applied correctly
   2. No syntax errors
   3. Services are still running
   4. Run relevant tests"
   ```

4. **Error Handling**
   ```
   "If you encounter an error:
   1. Stop immediately
   2. Show me the full error message
   3. Explain what went wrong
   4. Propose a solution
   5. Wait for my approval before retrying"
   ```

5. **End of Session**
   ```
   "Before ending:
   1. Commit all changes with clear message
   2. Document what was completed
   3. List any pending tasks
   4. Save current state of services"
   ```

---

## 🎯 Success Criteria

### Minimum Viable Product (MVP)
- ✅ Receives and processes TradingView webhooks
- ✅ Creates Position Groups with pyramids and DCA
- ✅ Monitors and executes take-profit
- ✅ Enforces execution pool limits
- ✅ Queue system with priority ranking
- ✅ Basic risk engine (manual trigger)
- ✅ Dashboard showing live positions
- ✅ Logs viewer

### Full Feature Set
- ✅ All 3 TP modes working
- ✅ Automated risk engine with timer
- ✅ Performance dashboard with charts
- ✅ Full configuration UI
- ✅ Complete documentation

---

## 📝 Development Notes

### Common Pitfalls to Avoid
1. **Screen Session Hell**: Use `systemd` or Docker instead
2. **Database Permission Errors**: Grant ALL privileges to app user on schema, not just database
3. **Import Errors**: Always use relative imports in packages (`from .module import`)
4. **Config Changes**: Restart services properly after config updates
5. **Testing**: Always test with exchange in testnet mode first

### Recommended Development Order
1. Get backend API responding first
2. Test database CRUD operations manually
3. Build one complete vertical slice (webhook → database → UI)
4. Then expand horizontally (add more features)
5. UI can lag behind backend by 1-2 phases

### Code Quality Standards
- **Backend**: Type hints on all functions, docstrings for public methods
- **Frontend**: TypeScript strict mode, no `any` types
- **Database**: All queries use SQLAlchemy ORM, no raw SQL
- **Testing**: Write tests BEFORE implementing complex logic
- **Git**: Commit after each working feature, not at end of day

---

## 🎓 AI Assistant Training Examples

### Example 1: Creating a Model
```
Human: "Let's create the PositionGroup model"

Good AI Response:
"I'll create the PositionGroup model. Here's what I propose:

[shows code]

This model includes:
- Relationship to User and APIKey
- Fields for PnL tracking
- Status field for lifecycle management
- Timestamps

Should I proceed with creating this file?"

Bad AI Response:
"Done! I created the model and also updated 3 other files and ran migrations."
```

### Example 2: Debugging
```
Human: "The backend won't start"

Good AI Response:
"Let me investigate. I'll:
1. Check the screen session logs
2. Verify the imports
3. Check database connection

[shows logs]

I found the issue: ImportError on line 15 of main.py
The problem is we're trying to import 'models' but haven't created __init__.py
Should I add the __init__.py file?"

Bad AI Response:
"I'll fix it" [makes 10 changes without explanation]
```

---

## ✅ Deliverables Checklist
