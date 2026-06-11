@echo off
chcp 65001 >nul
if /i "%1"=="--gui" goto :gui
if /i "%1"=="-g" goto :gui
python "%~dp0cli.py" %*
if errorlevel 1 (
    echo Error occurred - check output above
    pause
)
exit /b

:gui
python "%~dp0gui.py" %*
if errorlevel 1 (
    echo Error occurred - check output above
    pause
)
