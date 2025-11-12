from pydantic import BaseModel
from typing import Any, Dict

class SignalPayload(BaseModel):
    secret: str
    tv: Dict[str, Any]
    execution_intent: Dict[str, Any]
