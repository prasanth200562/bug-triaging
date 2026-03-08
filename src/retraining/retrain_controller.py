
import datetime
import json
from sqlalchemy.orm import Session
from api import models, crud

RETRAIN_THRESHOLD_CASES = 50
RETRAIN_THRESHOLD_DAYS = 7

class RetrainController:
    @staticmethod
    def get_system_config(db: Session, key: str, default: str = None):
        cfg = db.query(models.SystemConfig).filter(models.SystemConfig.key == key).first()
        if not cfg:
            return default
        return cfg.value

    @staticmethod
    def set_system_config(db: Session, key: str, value: str):
        cfg = db.query(models.SystemConfig).filter(models.SystemConfig.key == key).first()
        if not cfg:
            cfg = models.SystemConfig(key=key, value=value)
            db.add(cfg)
        else:
            cfg.value = value
        db.commit()

    @staticmethod
    def check_retrain_trigger(db: Session) -> bool:
        """
        Check if retraining should be triggered based on:
        a) Verified manual cases >= 50
        OR
        b) 7 days have passed since last retraining.
        """
        # Check if a new developer was recently added
        if RetrainController.get_system_config(db, "full_retrain_pending") == "true":
            return True

        # Count pending verified cases in retrain_queue
        pending_count = db.query(models.RetrainQueue).filter(models.RetrainQueue.status == "pending").count()
        if pending_count >= RETRAIN_THRESHOLD_CASES:
            return True

        # Check last retrain date
        last_retrain_str = RetrainController.get_system_config(db, "last_retrain_date")
        if not last_retrain_str:
            # If never retrained, we might need a baseline
            return False
            
        last_retrain = datetime.datetime.fromisoformat(last_retrain_str)
        days_passed = (datetime.datetime.utcnow() - last_retrain).days
        if days_passed >= RETRAIN_THRESHOLD_DAYS:
            return True

        return False

    @staticmethod
    def get_current_model_version(db: Session) -> str:
        return RetrainController.get_system_config(db, "model_version", "1.0.0")

    @staticmethod
    def finalize_retraining(db: Session):
        """
        Called after the training script finishes successfully.
        Updates model version, clears queue, and sets last retrain date.
        """
        # Increment version
        current_v = RetrainController.get_current_model_version(db)
        parts = current_v.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        new_v = '.'.join(parts)
        
        RetrainController.set_system_config(db, "model_version", new_v)
        RetrainController.set_system_config(db, "last_retrain_date", datetime.datetime.utcnow().isoformat())
        RetrainController.set_system_config(db, "full_retrain_pending", "false")
        
        # Mark all pending cases as retrained
        db.query(models.RetrainQueue).filter(models.RetrainQueue.status == "pending").update({"status": "retrained"})
        db.commit()
        return new_v

    @staticmethod
    def queue_for_retraining(db: Session, bug_id: int, title: str, body: str, developer: str):
        # Only add if not already in queue
        existing = db.query(models.RetrainQueue).filter(models.RetrainQueue.bug_id == bug_id).first()
        if not existing:
            new_entry = models.RetrainQueue(
                bug_id=bug_id,
                title=title,
                body=body,
                verified_developer=developer,
                status="pending"
            )
            db.add(new_entry)
            db.commit()
            return True
        return False

    @staticmethod
    def process_assignment(db: Session, bug_id: int, developer: str, is_new_dev: bool = False):
        """
        Called when a manual reviewer assigns a verified developer.
        """
        bug = db.query(models.Bug).filter(models.Bug.id == bug_id).first()
        if not bug:
            return None

        # Mark as verified (we can use status or a separate flag, but here we move to queue)
        RetrainController.queue_for_retraining(db, bug.id, bug.title, bug.body, developer)
        
        status = "VERIFIED_READY_FOR_TRAINING"
        retrain_triggered = RetrainController.check_retrain_trigger(db)
        
        return {
            "developer_exists": True, # Since it was manually assigned
            "issue_status": status,
            "retrain_triggered": retrain_triggered,
            "model_version": RetrainController.get_current_model_version(db)
        }

