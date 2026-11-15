@echo off
cd /d "%~dp0"
py -m pip install -r requirements-v3.txt
if errorlevel 1 (echo Dependencies could not be installed. & pause & exit /b 1)
py run_v3.py
if errorlevel 1 pause
