@echo off
echo Starting VTube Animation Server in a new terminal...
start pwsh -NoExit -Command "cd /d D:\111111.PROGRAMOWANIE\AI W PYTHONIE\Refreshed-ShiroAI-Chan; echo y | doppler run -- python -m vtube_server.animation_server"

timeout /t 2

echo Starting Main Application in another new terminal...
start pwsh -NoExit -Command "cd /d D:\111111.PROGRAMOWANIE\AI W PYTHONIE\Refreshed-ShiroAI-Chan; echo y | doppler run -- python -m app"

pause
