@echo off
rem Every time: make the new thumbnails, start scenepick, open it in the browser.
rem Closing this window stops scenepick.
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo Run setup_nas.bat first.
    goto :end
)
set "PORT=5000"
for /f "tokens=1,* delims==" %%a in ('findstr /b /c:"PORT=" .env') do set "PORT=%%b"

rem Checked here first: otherwise the browser below would open whoever is already on this port.
.venv\Scripts\python -c "import settings; settings.refuse_taken_port()" || goto :end
.venv\Scripts\python tools\make_thumbs.py || goto :end

start "" /b .venv\Scripts\python -c "import time, webbrowser; time.sleep(4); webbrowser.open('http://localhost:%PORT%')"
.venv\Scripts\python app.py

:end
echo.
echo scenepick is not running. Read the lines above.
pause
