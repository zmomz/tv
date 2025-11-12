from pydantic import BaseModel

class DashboardStats(BaseModel):
    open_positions: int
    total_positions: int
    pnl: float
