from database.db_connection import SessionLocal
from api import models

db = SessionLocal()
bugs = db.query(models.Bug).filter(models.Bug.status == 'new-developer').all()
print(f"Bugs with new-developer status: {len(bugs)}")
for b in bugs:
    print(f"ID: {b.id}, Title: {b.title[:50]}...")
db.close()
