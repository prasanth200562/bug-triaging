from sqlalchemy.orm import Session
from api import models, schemas
import json


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_bug(db: Session, bug_id: int):
    return db.query(models.Bug).filter(models.Bug.id == bug_id).first()

def get_bug_by_title(db: Session, title: str):
    return db.query(models.Bug).filter(models.Bug.title == title).first()

from sqlalchemy.orm import Session, joinedload

def get_bugs(db: Session, skip: int = 0, limit: int = 500):
    return db.query(models.Bug).options(
        joinedload(models.Bug.assignments),
        joinedload(models.Bug.predictions),
        joinedload(models.Bug.reporter)
    ).order_by(models.Bug.id.desc()).offset(skip).limit(limit).all()

def create_bug(db: Session, bug: schemas.BugCreate, tags: str = None):
    bug_data = bug.dict(exclude={"reporter_username"})
    if tags:
        bug_data["tags"] = tags

    reporter_username = bug.reporter_username
    if reporter_username:
        normalized = reporter_username.strip().lower().replace(" ", "_")
        reporter = db.query(models.User).filter(models.User.username == normalized).first()
        if not reporter:
            reporter = models.User(
                username=normalized,
                full_name=reporter_username.strip(),
                password_hash="user_portal",
                role="reporter"
            )
            db.add(reporter)
            db.commit()
            db.refresh(reporter)
        bug_data["reporter_id"] = reporter.id

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
        assignment_type=assignment_type,
        assigned_by_id=None
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


def _workflow_status(raw_status: str) -> str:
    if raw_status in {"closed", "resolved"}:
        return "resolved"
    return "pending"


def get_user_bug_items(db: Session, reporter_username: str):
    reporter = db.query(models.User).filter(models.User.username == reporter_username).first()
    if not reporter:
        return []

    bugs = db.query(models.Bug).options(joinedload(models.Bug.assignments)).filter(
        models.Bug.reporter_id == reporter.id
    ).order_by(models.Bug.id.desc()).all()

    result = []
    for bug in bugs:
        latest = bug.assignments[-1] if bug.assignments else None
        result.append({
            "id": bug.id,
            "title": bug.title,
            "status": bug.status,
            "workflow_status": _workflow_status(bug.status),
            "assigned_to": latest.developer_name if latest else None,
            "source": bug.source,
            "created_at": bug.created_at,
            "updated_at": bug.updated_at,
        })
    return result


def get_developer_bug_items(db: Session, developer_user: models.User):
    assignments = db.query(models.BugAssignment).filter(
        models.BugAssignment.developer_id == developer_user.id
    ).order_by(models.BugAssignment.id.desc()).all()

    bug_ids = []
    seen = set()
    for assignment in assignments:
        if assignment.bug_id not in seen:
            seen.add(assignment.bug_id)
            bug_ids.append(assignment.bug_id)

    if not bug_ids:
        return []

    bugs = db.query(models.Bug).options(joinedload(models.Bug.assignments)).filter(models.Bug.id.in_(bug_ids)).all()
    by_id = {bug.id: bug for bug in bugs}

    result = []
    for bug_id in bug_ids:
        bug = by_id.get(bug_id)
        if not bug:
            continue
        latest = bug.assignments[-1] if bug.assignments else None
        result.append({
            "id": bug.id,
            "title": bug.title,
            "status": bug.status,
            "workflow_status": _workflow_status(bug.status),
            "assigned_to": latest.developer_name if latest else None,
            "source": bug.source,
            "created_at": bug.created_at,
            "updated_at": bug.updated_at,
        })
    return result


def update_bug_status_for_developer(db: Session, bug_id: int, developer_user: models.User, new_status: str):
    assignment = db.query(models.BugAssignment).filter(
        models.BugAssignment.bug_id == bug_id,
        models.BugAssignment.developer_id == developer_user.id
    ).order_by(models.BugAssignment.id.desc()).first()

    if not assignment:
        return None

    bug = db.query(models.Bug).filter(models.Bug.id == bug_id).first()
    if not bug:
        return None

    # Keep DB status compatible with current schema while exposing pending/resolved in API.
    bug.status = "closed" if new_status == "resolved" else "in-progress"
    db.commit()
    db.refresh(bug)

    latest = bug.assignments[-1] if bug.assignments else None
    return {
        "id": bug.id,
        "title": bug.title,
        "status": bug.status,
        "workflow_status": _workflow_status(bug.status),
        "assigned_to": latest.developer_name if latest else None,
        "source": bug.source,
        "created_at": bug.created_at,
        "updated_at": bug.updated_at,
    }

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


def update_bug_status_admin(db: Session, bug_id: int, status: str):
    bug = db.query(models.Bug).filter(models.Bug.id == bug_id).first()
    if not bug:
        return None

    bug.status = "closed" if status == "resolved" else "in-progress"
    db.commit()
    db.refresh(bug)
    return bug


def resolve_all_bugs_admin(db: Session, bug_ids: list[int] | None = None):
    query = db.query(models.Bug)
    if bug_ids:
        query = query.filter(models.Bug.id.in_(bug_ids))

    bugs = query.all()
    updated = 0
    for bug in bugs:
        if bug.status != "closed":
            bug.status = "closed"
            updated += 1

    db.commit()
    return updated
