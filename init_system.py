
from database.db_connection import SessionLocal
from src.retraining.retrain_controller import RetrainController
import datetime

def init_system():
    db = SessionLocal()
    try:
        # Set last retrain date to today if not set
        if not RetrainController.get_system_config(db, "last_retrain_date"):
            RetrainController.set_system_config(db, "last_retrain_date", datetime.datetime.utcnow().isoformat())
            print("Initialized last_retrain_date")
        
        # Set initial model version
        if not RetrainController.get_system_config(db, "model_version"):
            RetrainController.set_system_config(db, "model_version", "1.0.0")
            print("Initialized model_version")
            
    finally:
        db.close()

if __name__ == "__main__":
    init_system()
