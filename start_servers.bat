@echo off
echo Starting all services...

:: Start Brain Service
start cmd /k "cd services/brain && python -m uvicorn main:app --port 8015"

:: Start AI Service
start cmd /k "cd services/ai && python main_ai.py"

:: Start VTube Service
start cmd /k "cd services/vtube && python -m uvicorn main:app --port 8002"

:: Start Frontend Service (last)
start cmd /k "cd services/frontend && python app.py"

echo All services started!
pause
