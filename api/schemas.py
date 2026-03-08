from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from typing import Literal

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    role: str

class BugBase(BaseModel):
    title: str
    body: str
    priority: Optional[str] = "medium"
    tags: Optional[str] = None
    source: Optional[str] = "manual"


class BugCreate(BugBase):
    reporter_username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    full_name: Optional[str] = None
class Prediction(BaseModel):
    predicted_developer: str
    confidence: float

class PredictionResponse(BaseModel):
    bug_id: int
    title: str
    predictions: List[Prediction]
    threshold: float
    is_auto_assigned: bool
    issue_status: str
    developer_exists: bool
    retrain_triggered: bool
    model_version: str
    tags: Optional[str] = None

class BugAssignmentResponse(BaseModel):
    developer_name: Optional[str] = None
    assignment_type: str
    assigned_at: datetime

    class Config:
        from_attributes = True

class BugResponse(BugBase):
    id: int
    status: str
    source: str
    reporter_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assignments: List[BugAssignmentResponse] = []
    predictions: List[Prediction] = []
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_bugs: int
    auto_assigned: int
    manual_review: int
    bugs_per_developer: dict
    pending_bugs: int

class AssignmentUpdate(BaseModel):
    developer_id: Optional[int] = None
    developer_name: str
    notes: Optional[str] = None

class GithubFetchRequest(BaseModel):
    repo_owner: Optional[str] = "microsoft"
    repo_name: Optional[str] = "vscode"
    count: int = Field(default=5, ge=1, le=50)
    reporter_username: Optional[str] = None

class LocalImportRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=100)
    reporter_username: Optional[str] = None

class BulkDeleteRequest(BaseModel):
    bug_ids: List[int]


class RetrainQueueItem(BaseModel):
    id: int
    bug_id: int
    title: str
    verified_developer: str
    added_at: datetime
    status: str

    class Config:
        from_attributes = True

class RetrainStatus(BaseModel):
    pending_count: int
    retrained_count: int
    threshold_cases: int
    threshold_days: int
    last_retrain_date: Optional[str] = None
    full_retrain_pending: bool
    model_version: str


class UserBugItem(BaseModel):
    id: int
    title: str
    status: str
    workflow_status: Literal["pending", "resolved"]
    assigned_to: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime


class DeveloperStatusUpdate(BaseModel):
    status: Literal["pending", "resolved"]


class AdminStatusUpdate(BaseModel):
    status: Literal["pending", "resolved"]


class ResolveAllRequest(BaseModel):
    bug_ids: Optional[List[int]] = None

