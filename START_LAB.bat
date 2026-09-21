@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
title Lab 10 - setup and run

rem Always use this project's Python, even if another environment is active.
set "LAB10_PYTHON=%~dp0.venv312\Scripts\python.exe"

if not exist "main.py" goto missing_files
if not exist "requirements.txt" goto missing_files
if not exist "prepare_model.py" goto missing_files
if exist "%LAB10_PYTHON%" goto check_environment
if exist ".venv312" goto invalid_environment

echo Looking for Python 3.12, 64-bit...
py -3.12 -c "import sys, struct; sys.exit(sys.version_info[:2] != (3, 12) or struct.calcsize('P') != 8)" >nul 2>&1
if not errorlevel 1 goto create_with_launcher

set "LAB10_BASE_PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
if exist "%LAB10_BASE_PYTHON%" goto create_with_path
set "LAB10_BASE_PYTHON=%ProgramFiles%\Python312\python.exe"
if exist "%LAB10_BASE_PYTHON%" goto create_with_path
goto missing_python

:create_with_launcher
py -3.12 -m venv ".venv312"
if errorlevel 1 goto failed
goto check_environment

:create_with_path
"%LAB10_BASE_PYTHON%" -c "import sys, struct; sys.exit(sys.version_info[:2] != (3, 12) or struct.calcsize('P') != 8)"
if errorlevel 1 goto missing_python
"%LAB10_BASE_PYTHON%" -m venv ".venv312"
if errorlevel 1 goto failed

:check_environment
"%LAB10_PYTHON%" -c "import sys, struct; sys.exit(sys.version_info[:2] != (3, 12) or struct.calcsize('P') != 8)"
if errorlevel 1 goto invalid_environment
"%LAB10_PYTHON%" -c "import requests, pyttsx3, pyaudio, vosk" >nul 2>&1
if not errorlevel 1 goto prepare_model

echo.
echo Installing the required packages. Internet access is needed. Please wait...
"%LAB10_PYTHON%" -m pip install --only-binary=pyaudio -r "requirements.txt"
if errorlevel 1 goto failed
"%LAB10_PYTHON%" -c "import requests, pyttsx3, pyaudio, vosk; print('All required packages imported successfully.')"
if errorlevel 1 goto failed

:prepare_model
echo.
"%LAB10_PYTHON%" "prepare_model.py"
if errorlevel 1 goto failed

echo.
echo Starting your Lab 10 assistant...
echo VS Code interpreter for this project:
echo "%LAB10_PYTHON%"
echo.
"%LAB10_PYTHON%" "main.py" %*
if errorlevel 1 goto failed
echo.
echo The program has finished.
pause
exit /b 0

:missing_files
echo.
echo This folder is incomplete.
echo Extract the entire ZIP into a fresh folder using Extract All.
echo Keep START_LAB.bat, main.py, requirements.txt and prepare_model.py together.
goto stop_with_error

:missing_python
echo.
echo Python 3.12, 64-bit, was not found.
echo Install the Windows installer - 64-bit - from this official page:
echo https://www.python.org/downloads/release/python-31210/
echo Keep the Python launcher option enabled during installation.
echo Then double-click START_LAB.bat again.
goto stop_with_error

:invalid_environment
echo.
echo The .venv312 folder is not a working Python 3.12, 64-bit environment.
echo Rename that folder to an unused name, then run this launcher again.
goto stop_with_error

:failed
echo.
echo A step failed. The error is printed above.
echo Copy the error output if you need help with it.

:stop_with_error
echo.
pause
exit /b 1
