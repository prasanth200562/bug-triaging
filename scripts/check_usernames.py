from database.db_connection import SessionLocal
from api import models

db = SessionLocal()
users = db.query(models.User).filter(models.User.role == 'developer').all()
usernames = [u.username for u in users]
print(", ".join(usernames))
db.close()
