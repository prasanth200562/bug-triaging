from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_URL = f"sqlite:///{BASE_DIR}/database/bug_triaging.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # This will create tables if they don't exist based on models
    # We call this in app.py or a migration script
    import api.models
    Base.metadata.create_all(bind=engine)
    
    # Optional: Run the SQL schema file for extra constraints/seeds not captured in models 
    # (though usually we'd do this via SQLAlchemy)
    schema_path = BASE_DIR / "database/db_schema.sql"
    if schema_path.exists():
        with open(schema_path, "r") as f:
            sql = f.read()
            with engine.connect() as conn:
                # SQLite execute script can be tricky via engine.execute
                # Better to use raw connection for script execution
                import sqlite3
                raw_conn = sqlite3.connect(str(BASE_DIR / "database/bug_triaging.db"))
                raw_conn.executescript(sql)
                raw_conn.close()
