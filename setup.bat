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
    call "%~dp0py.bat" -m pip install --user --no-warn-script-location ^
        -r "%~dp0requirements-dev.txt"

    call "%~dp0py.bat" -Wignore -m piptools compile -v --rebuild --newline LF --resolver backtracking --no-allow-unsafe
endlocal & (
    set "PATH=%PATH%"
)
