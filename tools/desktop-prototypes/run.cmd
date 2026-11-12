@echo off
cd /d "%~dp0"
py -3 demo.py
if errorlevel 1 pause
