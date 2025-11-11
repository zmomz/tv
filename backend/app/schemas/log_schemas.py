from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class SystemLogOut(BaseModel):
    id: UUID
    timestamp: datetime
    level: str
    category: str
    user_id: UUID = None
    message: str
    details: dict = None
    ip_address: str = None

    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    id: UUID
    timestamp: datetime
    user_id: UUID
    action: str
    resource: str
    resource_id: str = None
    details: dict = None
    ip_address: str = None

    class Config:
        from_attributes = True
