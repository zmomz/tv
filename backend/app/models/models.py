from sqlalchemy import Column, String, Integer
from ..db.base import Base

class GlobalSettings(Base):
    __tablename__ = "global_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_name = Column(String, unique=True, index=True)
    setting_value = Column(String)