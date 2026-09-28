@echo off
rem First time only, on the lab's remote Windows: make the Python environment and write .env.
rem The NAS drive letter differs from person to person, so it is looked for, not asked for.
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo Making the Python environment ...
    python -m venv .venv || goto :fail
)
echo Installing Flask and Pillow ...
.venv\Scripts\python -m pip install -q -r requirements.txt || goto :fail

if exist .env (
    echo .env is already there, left as it is.
    goto :done
)
set "NAS="
for %%d in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if not defined NAS if exist "%%d:\datasets\hyperspectral\cvpr_work\" set "NAS=%%d:\datasets\hyperspectral"
    if not defined NAS if exist "%%d:\hyperspectral\cvpr_work\" set "NAS=%%d:\hyperspectral"
)
if not defined NAS (
    echo.
    echo The NAS folder with cvpr_work and cvpr_dataset in it was not found on any drive.
    echo Open it in Explorer, copy the path from the address bar, paste it here and press Enter.
    set /p "NAS=> "
)
if not exist "%NAS%\cvpr_work\" (
    echo No cvpr_work in "%NAS%".
    goto :fail
)
if not exist "%NAS%\cvpr_dataset\" (
    echo No cvpr_dataset in "%NAS%".
    goto :fail
)
(
    echo DATA_ROOT=%NAS%\cvpr_work
    echo RGB_ROOT=%NAS%\cvpr_dataset\*\rgb_sat
    echo SELECTION=%NAS%\cvpr_work\scenepick\selection.json
    echo PORT=5101
) > .env
echo Wrote .env:
type .env

:done
echo.
echo done. You can close this window.
pause
exit /b 0

:fail
echo.
echo Failed. Send a screenshot of this window.
pause
exit /b 1
