from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from database.db_connection import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="reporter") # admin, developer, reporter
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Bug(Base):
    __tablename__ = "bugs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    priority = Column(String, default="medium")
    tags = Column(String)
    source = Column(String, default="manual")
    status = Column(String, default="open")
    reporter_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    predictions = relationship("ModelPrediction", back_populates="bug", cascade="all, delete-orphan")
    assignments = relationship("BugAssignment", back_populates="bug", cascade="all, delete-orphan")

class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(Integer, ForeignKey("bugs.id"))
    predicted_developer = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    top_alternatives = Column(Text) # JSON string
    prediction_time = Column(DateTime, default=datetime.datetime.utcnow)
    threshold_used = Column(Float, default=0.50)

    bug = relationship("Bug", back_populates="predictions")

class BugAssignment(Base):
    __tablename__ = "bug_assignments"
    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(Integer, ForeignKey("bugs.id"))
    developer_id = Column(Integer, ForeignKey("users.id"))
    developer_name = Column(String)
    assigned_by_id = Column(Integer, ForeignKey("users.id"))
    assignment_type = Column(String) # auto, manual
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)

    bug = relationship("Bug", back_populates="assignments")

class RetrainQueue(Base):
    __tablename__ = "retrain_queue"
    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(Integer, ForeignKey("bugs.id"), unique=True)
    title = Column(String)
    body = Column(Text)
    verified_developer = Column(String)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="pending") # pending, retrained

class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String, primary_key=True)
    value = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
