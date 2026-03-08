import base64
import hashlib
import hmac
import json
import os
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from api import models
from database.db_connection import get_db


SECRET_KEY = os.getenv("BUG_TRIAGE_SECRET", "bug-triage-dev-secret")


def _b64url_encode(raw: bytes) -> str:
	return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
	padding = "=" * (-len(value) % 4)
	return base64.urlsafe_b64decode(value + padding)


def create_auth_token(username: str, role: str) -> str:
	payload = {"username": username, "role": role}
	payload_raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
	payload_b64 = _b64url_encode(payload_raw)
	signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
	return f"{payload_b64}.{signature}"


def decode_auth_token(token: str) -> Optional[dict]:
	try:
		payload_b64, signature = token.split(".", 1)
	except ValueError:
		return None

	expected = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
	if not hmac.compare_digest(expected, signature):
		return None

	try:
		payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
	except Exception:
		return None

	if "username" not in payload or "role" not in payload:
		return None
	return payload


def get_current_user(
	authorization: Optional[str] = Header(default=None),
	db: Session = Depends(get_db),
):
	if not authorization or not authorization.lower().startswith("bearer "):
		raise HTTPException(status_code=401, detail="Missing authorization token")

	token = authorization.split(" ", 1)[1].strip()
	payload = decode_auth_token(token)
	if not payload:
		raise HTTPException(status_code=401, detail="Invalid or expired token")

	user = db.query(models.User).filter(models.User.username == payload["username"]).first()
	if not user:
		raise HTTPException(status_code=401, detail="User no longer exists")
	return user


def require_admin(current_user: models.User = Depends(get_current_user)):
	if current_user.role != "admin":
		raise HTTPException(status_code=403, detail="Admin access required")
	return current_user


def require_developer(current_user: models.User = Depends(get_current_user)):
	if current_user.role != "developer":
		raise HTTPException(status_code=403, detail="Developer access required")
	return current_user

