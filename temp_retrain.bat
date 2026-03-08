@echo off
cd /d "C:\Users\Prem\OneDrive\Desktop\final yer project document\Bug Triaging\current version - Copy\Bug-Triaging-ML-System"
set PYTHONPATH=C:\Users\Prem\OneDrive\Desktop\final yer project document\Bug Triaging\current version - Copy\Bug-Triaging-ML-System
"C:\Users\Prem\AppData\Local\Programs\Python\Python314\python.exe" "C:\Users\Prem\OneDrive\Desktop\final yer project document\Bug Triaging\current version - Copy\Bug-Triaging-ML-System\train_pipeline_fast.py"
echo.
echo Projecting training results to API...
curl -X POST http://127.0.0.1:8000/retrain/finalize
echo.
echo Retraining Complete.
pause
del "%~f0" & exit
