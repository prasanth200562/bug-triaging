from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from api import schemas, crud, models
from api.middleware import create_auth_token, require_admin, require_developer
from database.db_connection import get_db
from src.prediction.assign_developer import assigner
from src.preprocessing.nlp_preprocessor import generate_tags
from typing import List
import json
import os
import random

from src.data_collection.github_collector import fetch_bugs_from_github
from src.utils.developer_matcher import DeveloperMatcher
from src.retraining.retrain_controller import RetrainController

router = APIRouter()


def _normalize_name(value: str) -> str:
    return (value or "").strip().lower().replace(" ", "_")


@router.post("/auth/login", response_model=schemas.LoginResponse)
async def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    password = payload.password.strip()

    # Static admin login as requested.
    if username == "admin" and password == "admin123":
        admin_user = crud.get_user_by_username(db, "admin")
        if not admin_user:
            admin_user = models.User(
                username="admin",
                full_name="System Admin",
                password_hash="admin123",
                role="admin",
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        token = create_auth_token(admin_user.username, "admin")
        return {
            "token": token,
            "username": admin_user.username,
            "role": "admin",
            "full_name": admin_user.full_name,
        }

    if password != "dev123":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Developer username can be entered as full name or system username.
    normalized = _normalize_name(username)
    developers = crud.get_users(db, role="developer")
    matched = None
    for dev in developers:
        if _normalize_name(dev.username) == normalized or _normalize_name(dev.full_name or "") == normalized:
            matched = dev
            break

    if not matched:
        raise HTTPException(status_code=401, detail="Developer not found")

    token = create_auth_token(matched.username, "developer")
    return {
        "token": token,
        "username": matched.username,
        "role": "developer",
        "full_name": matched.full_name,
    }

async def process_bug_report(report: schemas.BugCreate, db: Session, match_result: dict = None):
    """
    Helper to process a bug report.
    match_result: dict from DeveloperMatcher.match()
    """
    ASSIGNMENT_THRESHOLD = 0.30
    
    # 1. Generate auto-tags
    auto_tags_list = generate_tags(f"{report.title} {report.body}").split(",")
    if match_result and match_result["status"] == "NOT_IN_LIST":
        auto_tags_list.append("New Developer")
    
    auto_tags = ",".join([t.strip() for t in auto_tags_list if t.strip()])

    # 2. Persist Bug with tags
    db_bug = crud.create_bug(db, report, tags=auto_tags)
    
    # 3. Get Prediction
    results = assigner.predict(report.title, report.body)
    if not results:
        return None, "Model not loaded or prediction failed"
    
    # 4. Developer Validation & Decision Logic
    top_prediction = results[0]
    ml_confidence = top_prediction["confidence"]
    
    # Threshold is strict for AUTO assignment
    is_auto_assigned = ml_confidence >= ASSIGNMENT_THRESHOLD
    
    developer_exists = False
    issue_status = "MANUAL_REQUIRED"
    top_developer = top_prediction["predicted_developer"]

    if match_result:
        # Handling Case: From GitHub with an Assignee
        if match_result["developer_found"]:
            # CASE 1: Developer exists in our list
            developer_exists = True
            top_developer = match_result["matched_developer_name"]
            issue_status = "AUTO_PROCESS" 
            is_auto_assigned = True # GitHub assignment is higher truth than ML
            
            # Queue for retraining to reinforce existing patterns
            RetrainController.queue_for_retraining(db, db_bug.id, db_bug.title, db_bug.body, top_developer)
        
        elif match_result["status"] == "NOT_IN_LIST" and match_result.get("incoming_name"):
            # CASE 2: Assignee exists on GitHub but NOT in our local list
            issue_status = "NEW_DEVELOPER_CASE"
            is_auto_assigned = True # Force auto-assignment for new developers found on GitHub
            
            new_dev_name = match_result.get("incoming_name")
            if new_dev_name:
                # Add new developer to database immediately
                existing_user = db.query(models.User).filter(models.User.username == new_dev_name.lower().replace(" ", "_")).first()
                if not existing_user:
                    existing_user = db.query(models.User).filter(models.User.full_name == new_dev_name).first()
                
                if not existing_user:
                    new_user = models.User(
                        username=new_dev_name.lower().replace(" ", "_"),
                        full_name=new_dev_name,
                        password_hash="temp_pass",
                        role="developer"
                    )
                    db.add(new_user)
                    db.commit()
                    db.refresh(new_user)
                    # Flag for full retraining since we have a new class
                    RetrainController.set_system_config(db, "full_retrain_pending", "true")
                
                top_developer = new_dev_name
                developer_exists = True
                
                # ALWAYS auto-assign and queue for retraining for new developers
                RetrainController.queue_for_retraining(db, db_bug.id, db_bug.title, db_bug.body, new_dev_name)
    else:
        # CASE 3: Manual Report or No GitHub Assignee - Strictly ML decision
        if is_auto_assigned:
            issue_status = "AUTO_PROCESS"
            developer_exists = True
        else:
            issue_status = "MANUAL_REQUIRED"
            developer_exists = False

    # Check if a retrain is already triggered
    retrain_triggered = RetrainController.check_retrain_trigger(db)

    # 5. Save Prediction Result
    res_payload = {
        "predictions": results,
        "threshold": ASSIGNMENT_THRESHOLD,
        "is_auto_assigned": is_auto_assigned,
        "tags": auto_tags,
        "issue_status": issue_status,
        "developer_exists": developer_exists,
        "retrain_triggered": retrain_triggered,
        "model_version": RetrainController.get_current_model_version(db)
    }
    crud.create_prediction(db, db_bug.id, res_payload, ASSIGNMENT_THRESHOLD)
    
    # 6. Handle Assignment
    final_status = 'assigned' if is_auto_assigned else 'manual-review'
    if issue_status == 'NEW_DEVELOPER_CASE':
        final_status = 'new-developer'
        
    crud.create_assignment(db, db_bug.id, top_developer, "auto" if is_auto_assigned else "manual", status=final_status)
        
    # Strictly return requested JSON structure
    res_payload["bug_id"] = db_bug.id
    res_payload["title"] = report.title
    
    return res_payload, None

@router.post("/predict", response_model=schemas.PredictionResponse)
async def predict_assignee(report: schemas.BugCreate, db: Session = Depends(get_db)):
    try:
        result, error = await process_bug_report(report, db)
        if error:
            raise HTTPException(status_code=500, detail=error)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch-github")
async def fetch_github_issues(req: schemas.GithubFetchRequest, db: Session = Depends(get_db)):
    try:
        # 0. Initialize Matcher
        developers = crud.get_users(db, role="developer")
        dev_list = []
        for d in developers:
            dev_list.append({
                "id": d.id,
                "username": d.username,
                "full_name": d.full_name,
                "email": f"{d.username}@internal.com" # Placeholder for email check
            })
        matcher = DeveloperMatcher(dev_list)

        # 1. Fetch from GitHub - Fetch a larger pool to handle duplicates
        # We fetch up to 50 or 3x the request to find unique ones
        fetch_limit = max(50, req.count * 3)
        raw_issues = fetch_bugs_from_github(total_limit=fetch_limit, state="open")
        
        imported = []
        skipped = []
        errors = []
        
        for issue in raw_issues:
            # STOP if we reached the requested count
            if len(imported) >= req.count:
                break

            # 2. Check for duplicates by title
            existing = crud.get_bug_by_title(db, issue["title"])
            if existing:
                skipped.append(issue["title"])
                continue
            
            # 3. Try to match GitHub assignee to local developer
            match_res = {"developer_found": False, "status": "INPUT_EMPTY"}
            if issue.get("assignee") and issue["assignee"] != "unassigned":
                match_res = matcher.match(issue["assignee"])
            
            # 4. Process new bug
            report = schemas.BugCreate(
                title=issue["title"],
                body=issue["body"],
                priority="medium",
                source="github",
                reporter_username=req.reporter_username,
            )
            
            result, error = await process_bug_report(report, db, match_result=match_res)
            if error:
                errors.append({"title": issue["title"], "error": error})
            else:
                imported.append(result)
                
        return {
            "total_scanned": len(imported) + len(skipped) + len(errors),
            "imported_count": len(imported),
            "skipped_count": len(skipped),
            "error_count": len(errors),
            "imported": imported,
            "skipped_titles": skipped,
            "errors": errors
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-local")
async def import_local_bugs(req: schemas.LocalImportRequest, db: Session = Depends(get_db)):
    try:
        # 0. Initialize Matcher
        developers = crud.get_users(db, role="developer")
        dev_list = []
        for d in developers:
            dev_list.append({
                "id": d.id, "username": d.username, "full_name": d.full_name, "email": f"{d.username}@internal.com"
            })
        matcher = DeveloperMatcher(dev_list)

        # Resolve path relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_dir, "data", "processed", "bug_reports_cleaned.json")
        
        if not os.path.exists(data_path):
            raise HTTPException(status_code=404, detail=f"Local data file not found at {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            all_bugs = json.load(f)
        
        # Take a sample to avoid duplicates and test variety
        count = min(len(all_bugs), req.count)
        sampled = random.sample(all_bugs, count)
        
        imported = []
        skipped = []
        errors = []
        
        for bug in sampled:
            # 1. Check for duplicates
            existing = crud.get_bug_by_title(db, bug["title"])
            if existing:
                skipped.append(bug["title"])
                continue
            
            # 2. Match Assignee
            match_res = {"developer_found": False, "status": "INPUT_EMPTY"}
            if bug.get("assignee"):
                match_res = matcher.match(bug["assignee"])

            # 3. Process
            report = schemas.BugCreate(
                title=bug["title"],
                body=bug.get("body", ""),
                priority="medium",
                source="local",
                reporter_username=req.reporter_username,
            )
            
            result, error = await process_bug_report(report, db, match_result=match_res)
            if error:
                errors.append({"title": bug["title"], "error": error})
            else:
                imported.append(result)
                
        return {
            "total_sampled": len(sampled),
            "imported_count": len(imported),
            "skipped_count": len(skipped),
            "error_count": len(errors),
            "imported": imported,
            "skipped_titles": skipped,
            "errors": errors
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bugs", response_model=List[schemas.BugResponse])
async def read_bugs(skip: int = 0, limit: int = 500, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    bugs = crud.get_bugs(db, skip=skip, limit=limit)
    return bugs

@router.get("/stats", response_model=schemas.DashboardStats)
async def read_stats(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return crud.get_dashboard_stats(db)

@router.get("/users", response_model=List[schemas.UserBase])
async def read_users(role: str = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return crud.get_users(db, role=role)


@router.get("/user/bugs", response_model=List[schemas.UserBugItem])
async def read_user_bugs(reporter: str, db: Session = Depends(get_db)):
    normalized = _normalize_name(reporter)
    return crud.get_user_bug_items(db, normalized)


@router.get("/developer/bugs", response_model=List[schemas.UserBugItem])
async def read_developer_bugs(db: Session = Depends(get_db), current_developer: models.User = Depends(require_developer)):
    return crud.get_developer_bug_items(db, current_developer)


@router.patch("/developer/bugs/{bug_id}/status", response_model=schemas.UserBugItem)
async def update_developer_bug_status(
    bug_id: int,
    payload: schemas.DeveloperStatusUpdate,
    db: Session = Depends(get_db),
    current_developer: models.User = Depends(require_developer),
):
    updated = crud.update_bug_status_for_developer(db, bug_id, current_developer, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Assigned bug not found")
    return updated


@router.patch("/admin/bugs/{bug_id}/status")
async def update_admin_bug_status(
    bug_id: int,
    payload: schemas.AdminStatusUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    updated = crud.update_bug_status_admin(db, bug_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Bug not found")
    return {"message": "Bug status updated", "bug_id": bug_id, "status": updated.status}


@router.post("/admin/bugs/resolve-all")
async def resolve_all_admin_bugs(
    payload: schemas.ResolveAllRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    count = crud.resolve_all_bugs_admin(db, payload.bug_ids)
    return {"message": f"Resolved {count} bugs", "resolved_count": count}

@router.get("/bugs/{bug_id}/predictions")
async def read_bug_predictions(bug_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    pred = crud.get_prediction_by_bug(db, bug_id)
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    import json
    predictions = json.loads(pred.top_alternatives)
    
    # Enrich with workload
    workloads = crud.get_developer_workload(db)
    for p in predictions:
        p["workload"] = workloads.get(p["predicted_developer"], 0)
        
    return {
        "bug_id": bug_id,
        "predictions": predictions,
        "threshold": pred.threshold_used
    }

@router.post("/bugs/{bug_id}/assign")
async def manual_assign(bug_id: int, update: schemas.AssignmentUpdate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    crud.create_assignment(db, bug_id, update.developer_name, "manual", update.developer_id, status="assigned")
    
    # Trigger verification logic for retraining
    status_report = RetrainController.process_assignment(db, bug_id, update.developer_name)
    
    return {
        "message": "Assignment updated successfully",
        "verification_status": status_report
    }

@router.delete("/bugs/{bug_id}")
async def delete_bug(bug_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    success = crud.delete_bug(db, bug_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bug not found")
    return {"message": "Bug deleted successfully"}

@router.post("/bugs/bulk-delete")
async def bulk_delete_bugs(req: schemas.BulkDeleteRequest, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    count = crud.delete_bugs(db, req.bug_ids)
    return {"message": f"Successfully deleted {count} bugs"}

@router.get("/retrain/status", response_model=schemas.RetrainStatus)
async def get_retrain_status(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    from src.retraining.retrain_controller import RETRAIN_THRESHOLD_CASES, RETRAIN_THRESHOLD_DAYS
    
    pending_count = db.query(models.RetrainQueue).filter(models.RetrainQueue.status == "pending").count()
    retrained_count = db.query(models.RetrainQueue).filter(models.RetrainQueue.status == "retrained").count()
    last_retrain = RetrainController.get_system_config(db, "last_retrain_date")
    full_retrain = RetrainController.get_system_config(db, "full_retrain_pending") == "true"
    version = RetrainController.get_current_model_version(db)
    
    return {
        "pending_count": pending_count,
        "retrained_count": retrained_count,
        "threshold_cases": RETRAIN_THRESHOLD_CASES,
        "threshold_days": RETRAIN_THRESHOLD_DAYS,
        "last_retrain_date": last_retrain,
        "full_retrain_pending": full_retrain,
        "model_version": version
    }

@router.get("/retrain/queue", response_model=List[schemas.RetrainQueueItem])
async def get_retrain_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return crud.get_retrain_queue(db, skip=skip, limit=limit)

@router.post("/retrain/trigger")
async def trigger_retraining(_admin=Depends(require_admin)):
    import subprocess
    import sys
    from pathlib import Path
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, "train_pipeline_fast.py")
    
    try:
        # Create a temporary batch file to handle everything cleanly
        bat_path = os.path.join(base_dir, "temp_retrain.bat")
        with open(bat_path, "w") as f:
            f.write(f'@echo off\n')
            f.write(f'cd /d "{base_dir}"\n')
            f.write(f'set PYTHONPATH={base_dir}\n')
            # Use the exact executable used to run the server
            f.write(f'"{sys.executable}" "{script_path}"\n')
            f.write(f'echo.\n')
            f.write(f'echo Projecting training results to API...\n')
            # Call finalize endpoint to update version and clear queue
            f.write(f'curl -X POST http://127.0.0.1:8000/retrain/finalize\n')
            f.write(f'echo.\n')
            f.write(f'echo Retraining Complete.\n')
            f.write(f'pause\n')
            f.write(f'del "%~f0" & exit\n') # Delete itself and exit
        
        subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', bat_path], 
                         cwd=base_dir,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
                         
        return {"message": "Retraining triggered. A new console window has opened to show live progress."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrain/finalize")
async def finalize_retrain(db: Session = Depends(get_db)):
    new_version = RetrainController.finalize_retraining(db)
    return {"message": "Model status updated successfully", "new_version": new_version}

@router.get("/health")
async def health_check():
    if assigner.model and assigner.vectorizer and assigner.encoder:
        return {"status": "healthy", "model_loaded": True}
    return {"status": "unhealthy", "model_loaded": False}
