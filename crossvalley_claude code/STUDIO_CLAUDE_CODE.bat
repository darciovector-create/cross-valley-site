@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title APP CROSSVALLEY STUDIO_CLAUDE CODE

echo Verificando dependencias...
python -m pip install customtkinter pillow -q 2>nul

echo Iniciando APP CROSSVALLEY STUDIO_CLAUDE CODE...
start "" pythonw "%~dp0Cross_Valley_Studio_GUI.py"
