@echo off
cd /d "%~dp0"
set PYTHONPATH=.
py -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
