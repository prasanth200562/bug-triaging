from sqlalchemy.orm import Session
from database.db_connection import SessionLocal
from api import models
from src.preprocessing.nlp_preprocessor import generate_tags

def backfill_tags():
    db = SessionLocal()
    try:
        bugs = db.query(models.Bug).filter(models.Bug.tags == None).all()
        print(f"Found {len(bugs)} bugs without tags. Starting backfill...")
        
        for bug in bugs:
            tags = generate_tags(f"{bug.title} {bug.body}")
            bug.tags = tags
            print(f"Bug #{bug.id}: {tags}")
        
        db.commit()
        print("Backfill complete.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill_tags()
