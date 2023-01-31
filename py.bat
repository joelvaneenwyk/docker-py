@echo off
setlocal EnableDelayedExpansion

set _py_app_name=PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0
set _py_app_root=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps
set _py_packages=%USERPROFILE%\AppData\Local\Packages\%_py_app_name%

if exist "%_py_app_root%\python3.10.exe" (
    set "PATH=%PATH%;%_py_packages%\LocalCache\local-packages\Python310\Scripts;%_py_app_root%"
    "%_py_app_root%\python3.10.exe" %*
) else (
    python3 %*
)
