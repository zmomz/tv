from pydantic import BaseModel
from typing import List, Optional

class AppSettings(BaseModel):
    mode: str
    data_dir: str
    log_level: str

class ExchangeSettings(BaseModel):
    name: str
    api_key: str
    api_secret: str
    testnet: bool
    precision_refresh_sec: int

class ExecutionPoolSettings(BaseModel):
    max_open_groups: int
    count_pyramids: bool

class GridStrategySettings(BaseModel):
    dca_config: dict
    tp_config: dict

class RiskEngineSettings(BaseModel):
    loss_threshold_percent: float
    require_full_pyramids: bool
    post_full_wait_minutes: int

class AppConfig(BaseModel):
    app: AppSettings
    exchange: ExchangeSettings
    execution_pool: ExecutionPoolSettings
    grid_strategy: GridStrategySettings
    risk_engine: RiskEngineSettings
