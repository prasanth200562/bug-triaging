
from database.db_connection import SessionLocal
from api import models

def cleanup_orphans():
    db = SessionLocal()
    try:
        # Find assignments without bugs
        bug_ids = [b.id for b in db.query(models.Bug.id).all()]
        deleted_count = db.query(models.BugAssignment).filter(~models.BugAssignment.bug_id.in_(bug_ids)).delete(synchronize_session=False)
        deleted_preds = db.query(models.ModelPrediction).filter(~models.ModelPrediction.bug_id.in_(bug_ids)).delete(synchronize_session=False)
        db.commit()
        print(f"Cleaned up {deleted_count} orphaned assignments and {deleted_preds} orphaned predictions.")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_orphans()
