import joblib
from sqlalchemy.orm import Session
from database.db_connection import SessionLocal
from api import models

def seed_model_developers():
    try:
        encoder = joblib.load('data/features/label_encoder.pkl')
        developers = encoder.classes_
        
        db = SessionLocal()
        for dev_name in developers:
            if dev_name == 'Other': continue
            
            # Check if exists
            exists = db.query(models.User).filter(models.User.full_name == dev_name).first()
            if not exists:
                user = models.User(
                    username=dev_name.lower().replace(' ', '_'),
                    password_hash='pbkdf2:sha256:260000$placeholder',
                    full_name=dev_name,
                    role='developer'
                )
                db.add(user)
        
        db.commit()
        db.close()
        print(f"Successfully seeded {len(developers)} developers")
    except Exception as e:
        print(f"Error seeding: {e}")

if __name__ == "__main__":
    seed_model_developers()
