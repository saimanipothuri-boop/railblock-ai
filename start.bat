@echo off
title RailBlock-AI - Indian Railways Block Planning System
echo =====================================================================
echo    RailBlock-AI: Automatic Block Planning for Indian Railways
echo =====================================================================
echo.

set "PY_FALLBACK=C:\Users\saima\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PY_CMD=py"
    ) else (
        set "PY_CMD=%PY_FALLBACK%"
    )
)

echo Starting RailBlock-AI Web Server...
echo Opening dashboard at http://localhost:8000 ...
start "" "http://localhost:8000"
"%PY_CMD%" server.py
pause
