from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# This will be initialized when settings are loaded
engine = None
SessionLocal = None

def init_db_session():
    global engine, SessionLocal
    if engine is None:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    if SessionLocal is None:
        init_db_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

init_db_session() # Initialize the session when the module is imported
