@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "TOOLS_DIR=%SCRIPT_DIR%tools"

:: 添加本地工具到PATH
if exist "%TOOLS_DIR%\platform-tools\adb.exe" (
    set "PATH=%PATH%;%TOOLS_DIR%\platform-tools"
)

title 微信视频号直播间自动化

echo.
echo ============================================================
echo    微信视频号直播间自动化 - 一键启动
echo ============================================================
echo.

:: ============================================================
:: 1. 检查环境
:: ============================================================
echo [1/4] 检查环境...

:: 检查Python
set "PYTHON_CMD="
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=py"
    )
)

if not defined PYTHON_CMD (
    echo       [X] Python 未安装
    echo.
    echo       请先运行 setup_env.bat 安装环境
    pause
    exit /b 1
)
echo       [√] Python 已就绪 ^(%PYTHON_CMD%^)

:: 检查Appium
where appium >nul 2>&1
if %errorlevel% neq 0 (
    echo       [X] Appium 未安装
    echo.
    echo       请先运行 setup_env.bat 安装环境
    pause
    exit /b 1
)
echo       [√] Appium 已就绪

:: 检查ADB
where adb >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "%TOOLS_DIR%\platform-tools\adb.exe" (
        echo       [X] ADB 未安装
        echo.
        echo       请先运行 setup_env.bat 安装环境
        pause
        exit /b 1
    )
)
echo       [√] ADB 已就绪

:: ============================================================
:: 2. 检查设备连接
:: ============================================================
echo.
echo [2/4] 检查设备连接...

adb kill-server >nul 2>&1
adb start-server >nul 2>&1

adb devices | findstr /r "device$" >nul
if %errorlevel% neq 0 (
    echo       [X] 未检测到Android设备
    echo.
    echo       请连接手机并开启USB调试后重试
    echo.
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('adb devices ^| findstr /r "device$"') do (
    echo       [√] 设备已连接: %%i
)

:: ============================================================
:: 3. 启动Appium服务器
:: ============================================================
echo.
echo [3/4] 启动 Appium 服务器...

:: 检查Appium是否已在运行
powershell -Command "& {try { $null = Invoke-WebRequest -Uri 'http://127.0.0.1:4723/status' -TimeoutSec 1 -UseBasicParsing; exit 0 } catch { exit 1 }}" >nul 2>&1
if %errorlevel% equ 0 (
    echo       [√] Appium 服务器已在运行
) else (
    echo       启动中，请稍候...
    
    :: 在新窗口启动Appium（保持窗口打开）
    start "Appium Server" cmd /k "appium --relaxed-security"
    
    :: 等待Appium启动（最多30秒）
    set "WAIT_COUNT=0"
    :wait_appium
    timeout /t 2 /nobreak >nul
    set /a WAIT_COUNT+=1
    
    powershell -Command "& {try { $null = Invoke-WebRequest -Uri 'http://127.0.0.1:4723/status' -TimeoutSec 2 -UseBasicParsing; exit 0 } catch { exit 1 }}" >nul 2>&1
    if !errorlevel! equ 0 (
        echo       [√] Appium 服务器启动成功
        goto :appium_ready
    )
    
    if !WAIT_COUNT! lss 15 (
        goto :wait_appium
    )
    
    echo       [X] Appium 启动超时
    echo.
    echo       请检查 Appium Server 窗口是否有错误信息
    pause
    exit /b 1
)
:appium_ready

:: ============================================================
:: 4. 提示用户准备
:: ============================================================
echo.
echo [4/4] 准备就绪
echo.
echo ============================================================
echo.
echo    [!] 请在手机上打开微信视频号直播间
echo.
echo    准备好后按任意键开始自动化...
echo.
echo ============================================================
pause >nul

:: ============================================================
:: 运行主程序
:: ============================================================
cls
echo.
echo ============================================================
echo    正在运行自动化程序
echo    按 Ctrl+C 可停止
echo ============================================================
echo.

%PYTHON_CMD% "%SCRIPT_DIR%main.py" %*

:: ============================================================
:: 结束
:: ============================================================
echo.
echo ============================================================
echo    程序已结束
echo ============================================================
echo.
echo 是否关闭 Appium 服务器？
echo   [Y] 关闭并退出
echo   [N] 保持运行（可继续使用）
echo.
choice /c YN /n /m "请选择: "
if %errorlevel% equ 1 (
    echo.
    echo 正在关闭 Appium 服务器...
    taskkill /f /im node.exe /fi "WINDOWTITLE eq Appium Server" >nul 2>&1
    taskkill /f /fi "WINDOWTITLE eq Appium Server" >nul 2>&1
    echo 已关闭
)

echo.
pause
