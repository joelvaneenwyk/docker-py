@echo off
setlocal EnableDelayedExpansion
    git --version
    if "%ERRORLEVEL%"=="0" goto:RunPython

    set "PATH=%PATH%;C:\Program Files\Git\bin"
    if "%ERRORLEVEL%"=="0" goto:RunPython

    choco --version
    if "%ERRORLEVEL%"=="0" goto:RunPython
    set ChocolateyUseWindowsCompression=false
    powershell Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Force
    powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
    choco install git.install -y --no-progress
    set "PATH=%PATH%;C:\ProgramData\chocolatey\bin"

    :RunPython
    python -m pip install --upgrade pip
    python -m pip install --no-warn-script-location ^
        -r "%~dp0requirements-dev.txt"
endlocal & (
    set "PATH=%PATH%"
)
