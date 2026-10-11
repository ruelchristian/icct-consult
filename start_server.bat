@echo off
echo ========================================================
echo Starting ICCT Faculty Consultation & Scheduling System
echo ========================================================
echo.
"%~dp0.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
pause
