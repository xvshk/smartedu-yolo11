@echo off
echo 启动课堂行为检测桌面应用...
cd /d %~dp0
python desktop/detection_app.py
pause
