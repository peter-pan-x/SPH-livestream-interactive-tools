@echo off
chcp 65001 >nul
echo ============================================
echo     坐标校准器 - 换手机时运行一次
echo ============================================
echo.
echo 请确保:
echo   1. Appium 服务器已启动
echo   2. 手机已连接
echo   3. 手机已打开视频号直播间
echo.
pause

cd /d "%~dp0"
python calibrate.py

echo.
pause
