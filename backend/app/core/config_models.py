from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from decimal import Decimal

# --- App Settings ---
class AppConfig(BaseModel):
    mode: str = Field("webapp_self_contained", description="Application mode (e.g., webapp_self_contained)")
    data_dir: str = Field("./engine_data", description="Directory for engine data")
    log_level: str = Field("info", description="Logging level (info, debug, warning, error)")

# --- Exchange Settings ---
class ExchangeConfig(BaseModel):
    name: str = Field("binance", description="Name of the exchange")
    api_key: str = Field("REDACTED", description="API Key for the exchange")
    api_secret: str = Field("REDACTED", description="API Secret for the exchange")
    testnet: bool = Field(True, description="Use testnet environment")
    precision_refresh_sec: int = Field(60, description="Interval to refresh precision rules in seconds")

# --- Execution Pool Settings ---
class ExecutionPoolConfig(BaseModel):
    max_open_groups: int = Field(10, description="Maximum number of active Position Groups")
    count_pyramids_toward_pool: bool = Field(False, description="Whether pyramids count towards max_open_groups")
    count_dca_toward_pool: bool = Field(False, description="Whether DCA orders count towards max_open_groups")

# --- Grid Strategy Settings ---
class GridStrategyConfig(BaseModel):
    max_pyramids_per_group: int = Field(5, description="Maximum number of pyramids per Position Group")
    max_dca_per_pyramid: int = Field(7, description="Maximum DCA layers per pyramid")
    tp_mode: str = Field("leg", description="Take-profit mode (leg, aggregate, hybrid)")

# --- Waiting Rule Settings ---
class WaitingRuleConfig(BaseModel):
    queue_replace_same_symbol: bool = Field(True, description="Replace queued signal if new signal for same symbol arrives")
    selection_priority: List[str] = Field(
        ["pyramid_continuation", "highest_loss_percent", "highest_replacement_count", "highest_expected_profit", "fifo"],
        description="Ordered list of rules for queue selection priority"
    )

# --- Risk Engine Settings ---
class RiskEngineConfig(BaseModel):
    require_full_pyramids: bool = Field(True, description="Require all pyramids to be received before risk engine activates")
    enable_post_full_wait: bool = Field(True, description="Enable waiting period after full pyramids before risk engine activates")
    post_full_wait_minutes: int = Field(60, description="Waiting time in minutes after full pyramids")
    timer_start_condition: str = Field("after_5_pyramids", description="Condition to start risk engine timer")
    reset_timer_on_replacement: bool = Field(False, description="Reset timer if replacement pyramid is received")
    loss_threshold_percent: Decimal = Field(Decimal("-5"), description="Loss percentage threshold to activate risk engine")
    use_trade_age_filter: bool = Field(False, description="Enable trade age filter for risk engine activation")
    age_threshold_minutes: int = Field(200, description="Trade age threshold in minutes")
    offset_mode: str = Field("usd", description="Offset execution mode (usd, percent)")
    max_winners_to_combine: int = Field(3, description="Maximum number of winning trades to combine for offset")
    partial_close_enabled: bool = Field(True, description="Enable partial closing of winning trades")
    min_close_notional: Decimal = Field(Decimal("20"), description="Minimum notional value for partial close")
    evaluate_on_fill: bool = Field(True, description="Evaluate risk engine on order fill events")
    evaluate_interval_sec: int = Field(10, description="Interval to evaluate risk conditions in seconds")

# --- Precision Settings ---
class PrecisionConfig(BaseModel):
    enforce_tick_size: bool = Field(True, description="Enforce tick size rounding")
    enforce_step_size: bool = Field(True, description="Enforce step size rounding")
    enforce_min_notional: bool = Field(True, description="Enforce minimum notional value")

# --- Logging Settings ---
class LoggingConfig(BaseModel):
    audit_log_enabled: bool = Field(True, description="Enable audit logging")
    rotate_daily: bool = Field(True, description="Rotate logs daily")
    keep_days: int = Field(30, description="Number of days to keep logs")

# --- Security Settings ---
class SecurityConfig(BaseModel):
    store_secrets_encrypted: bool = Field(True, description="Store API keys encrypted")
    webhook_signature_validation: bool = Field(True, description="Enable webhook signature validation")

# --- UI Preferences ---
class UIConfig(BaseModel):
    framework: str = Field("proposer_choice", description="Frontend UI framework choice")
    theme: str = Field("dark", description="UI theme (light, dark)")
    realtime_update_ms: int = Field(500, description="Real-time update interval in milliseconds")

# --- Packaging Settings ---
class PackagingConfig(BaseModel):
    target_platforms: List[str] = Field(["win", "mac"], description="Target platforms for packaging")
    auto_update: bool = Field(False, description="Enable auto-updates for packaged application")

# --- Main Configuration Model ---
class Config(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    exchange: ExchangeConfig = Field(default_factory=ExchangeConfig)
    execution_pool: ExecutionPoolConfig = Field(default_factory=ExecutionPoolConfig)
    grid_strategy: GridStrategyConfig = Field(default_factory=GridStrategyConfig)
    waiting_rule: WaitingRuleConfig = Field(default_factory=WaitingRuleConfig)
    risk_engine: RiskEngineConfig = Field(default_factory=RiskEngineConfig)
    precision: PrecisionConfig = Field(default_factory=PrecisionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    packaging: PackagingConfig = Field(default_factory=PackagingConfig)
