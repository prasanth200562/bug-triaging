from sqlalchemy.orm import Session
from api import models, schemas
import json

def get_bug(db: Session, bug_id: int):
    return db.query(models.Bug).filter(models.Bug.id == bug_id).first()

def get_bug_by_title(db: Session, title: str):
    return db.query(models.Bug).filter(models.Bug.title == title).first()

from sqlalchemy.orm import Session, joinedload

def get_bugs(db: Session, skip: int = 0, limit: int = 500):
    return db.query(models.Bug).options(
        joinedload(models.Bug.assignments),
        joinedload(models.Bug.predictions)
    ).order_by(models.Bug.id.desc()).offset(skip).limit(limit).all()

def create_bug(db: Session, bug: schemas.BugCreate, tags: str = None):
    bug_data = bug.dict()
    if tags:
        bug_data["tags"] = tags
    db_bug = models.Bug(**bug_data)
    db.add(db_bug)
    db.commit()
    db.refresh(db_bug)
    return db_bug

def create_prediction(db: Session, bug_id: int, prediction: dict, threshold: float):
    db_prediction = models.ModelPrediction(
        bug_id=bug_id,
        predicted_developer=prediction["predictions"][0]["predicted_developer"],
        confidence=prediction["predictions"][0]["confidence"],
        top_alternatives=json.dumps(prediction["predictions"]),
        threshold_used=threshold
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction

def create_assignment(db: Session, bug_id: int, developer_name: str, assignment_type: str, developer_id: int = None, status: str = None):
    # If developer_id is missing, check if this developer exists by full_name
    if not developer_id:
        existing_user = db.query(models.User).filter(models.User.full_name == developer_name).first()
        if existing_user:
            developer_id = existing_user.id
        else:
            # Create new developer record
            import random
            username = developer_name.lower().replace(" ", "_")
            new_user = models.User(
                username=username,
                full_name=developer_name,
                password_hash="temp_pass", # Should be managed via auth
                role="developer"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            developer_id = new_user.id
            # Log that a new developer was added (RetrainController uses this info)
            from src.retraining.retrain_controller import RetrainController
            RetrainController.set_system_config(db, "full_retrain_pending", "true")

    db_assignment = models.BugAssignment(
        bug_id=bug_id,
        developer_id=developer_id,
        developer_name=developer_name,
        assignment_type=assignment_type
    )
    db.add(db_assignment)
    
    # Update bug status
    bug = db.query(models.Bug).filter(models.Bug.id == bug_id).first()
    if status:
        bug.status = status
    elif assignment_type == 'auto':
        bug.status = 'assigned'
    else:
        bug.status = 'manual-review'
    
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

def get_developer_workload(db: Session):
    """Returns a dictionary of {developer_name: bug_count} for active assignments."""
    dev_counts = {}
    # Join with assignments to get the counts for each developer
    # We count all assignments in the database as "workload" for now
    active_assignments = db.query(models.BugAssignment).all()
    for a in active_assignments:
        dev = a.developer_name
        if dev:
            dev_counts[dev] = dev_counts.get(dev, 0) + 1
    return dev_counts

def get_dashboard_stats(db: Session):
    total = db.query(models.Bug).count()
    auto = db.query(models.Bug).filter(models.Bug.status == 'assigned').count()
    manual = db.query(models.Bug).filter(models.Bug.status == 'manual-review').count()
    pending = db.query(models.Bug).filter(models.Bug.status == 'open').count()
    
    dev_counts = get_developer_workload(db)
        
    return {
        "total_bugs": total,
        "auto_assigned": auto,
        "manual_review": manual,
        "bugs_per_developer": dev_counts,
        "pending_bugs": pending
    }

def get_users(db: Session, role: str = None):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)
    return query.all()

def get_prediction_by_bug(db: Session, bug_id: int):
    return db.query(models.ModelPrediction).filter(models.ModelPrediction.bug_id == bug_id).first()

def delete_bug(db: Session, bug_id: int):
    # Manually delete related records to be safe
    db.query(models.BugAssignment).filter(models.BugAssignment.bug_id == bug_id).delete(synchronize_session=False)
    db.query(models.ModelPrediction).filter(models.ModelPrediction.bug_id == bug_id).delete(synchronize_session=False)
    
    db_bug = db.query(models.Bug).filter(models.Bug.id == bug_id).first()
    if db_bug:
        db.delete(db_bug)
        db.commit()
        return True
    return False

def delete_bugs(db: Session, bug_ids: list):
    # Manually delete related records first because bulk delete doesn't trigger cascade
    db.query(models.BugAssignment).filter(models.BugAssignment.bug_id.in_(bug_ids)).delete(synchronize_session=False)
    db.query(models.ModelPrediction).filter(models.ModelPrediction.bug_id.in_(bug_ids)).delete(synchronize_session=False)
    
    count = db.query(models.Bug).filter(models.Bug.id.in_(bug_ids)).delete(synchronize_session=False)
    db.commit()
    return count

def get_retrain_queue(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.RetrainQueue).filter(models.RetrainQueue.status == "pending").offset(skip).limit(limit).all()
