from database.db_connection import SessionLocal
from api import models

db = SessionLocal()
count = db.query(models.Bug).count()
print(f"Total bugs in DB: {count}")
db.close()
