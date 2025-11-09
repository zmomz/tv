import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, init_db_session
from app.models import models
from app.services.tp_manager import TPManager
from app.core.config import settings

async def main():
    init_db_session()
    db: Session = SessionLocal()
    try:
        # Retrieve the dummy position group created earlier (assuming ID 2)
        group = db.query(models.PositionGroup).filter(models.PositionGroup.id == 2).first()
        
        if not group:
            print("Position Group with ID 2 not found. Please run the webhook test first.")
            return

        tp_manager = TPManager(db=db)
        tp_hit = tp_manager.check_per_leg_tp(group)

        print(f"TP hit result: {tp_hit}")
        assert tp_hit is not None
        assert tp_hit['group_id'] == group.id

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
