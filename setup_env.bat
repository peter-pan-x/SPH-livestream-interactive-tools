@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 工具安装目录
set "TOOLS_DIR=%SCRIPT_DIR%tools"

echo.
echo ============================================================
echo    微信视频号直播间自动化 - 环境检查与安装工具
echo    适用于 Windows 10/11
echo ============================================================
echo.

set "MISSING_COUNT=0"
set "INSTALL_COUNT=0"
set "NEED_RESTART=0"

:: ============================================================
:: 第一阶段：环境检查
:: ============================================================
echo [阶段1] 环境检查
echo ------------------------------------------------------------

:: 1. 检查 Python
echo [1/6] 检查 Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo       [X] Python 未安装
        set /a MISSING_COUNT+=1
        set "MISSING_PYTHON=1"
    ) else (
        echo       [√] Python 已安装 ^(py启动器^)
        set "PYTHON_CMD=py"
    )
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VER=%%i"
    echo       [√] Python !PYTHON_VER!
    set "PYTHON_CMD=python"
)

:: 2. 检查 pip
echo [2/6] 检查 pip...
if defined MISSING_PYTHON (
    echo       [X] pip ^(需要先安装Python^)
    set "MISSING_PIP=1"
) else (
    !PYTHON_CMD! -m pip --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo       [X] pip 未安装
        set /a MISSING_COUNT+=1
        set "MISSING_PIP=1"
    ) else (
        echo       [√] pip 已安装
    )
)

:: 3. 检查 Node.js
echo [3/6] 检查 Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    :: 检查常见安装路径
    if exist "C:\Program Files\nodejs\node.exe" (
        set "PATH=%PATH%;C:\Program Files\nodejs"
        echo       [√] Node.js 已安装 ^(已添加到PATH^)
    ) else (
        echo       [X] Node.js 未安装
        set /a MISSING_COUNT+=1
        set "MISSING_NODE=1"
    )
) else (
    for /f "tokens=*" %%i in ('node --version 2^>nul') do set "NODE_VER=%%i"
    echo       [√] Node.js !NODE_VER!
)

:: 4. 检查 ADB
echo [4/6] 检查 ADB...
where adb >nul 2>&1
if %errorlevel% neq 0 (
    :: 检查本地tools目录
    if exist "%TOOLS_DIR%\platform-tools\adb.exe" (
        set "PATH=%PATH%;%TOOLS_DIR%\platform-tools"
        echo       [√] ADB 已安装 ^(本地目录^)
    ) else if exist "%USERPROFILE%\android-platform-tools\platform-tools\adb.exe" (
        set "PATH=%PATH%;%USERPROFILE%\android-platform-tools\platform-tools"
        echo       [√] ADB 已安装 ^(用户目录^)
    ) else (
        echo       [X] ADB 未安装
        set /a MISSING_COUNT+=1
        set "MISSING_ADB=1"
    )
) else (
    echo       [√] ADB 已安装
)

:: 5. 检查 Appium
echo [5/6] 检查 Appium...
where appium >nul 2>&1
if %errorlevel% neq 0 (
    :: 检查npm全局目录
    for /f "tokens=*" %%i in ('npm root -g 2^>nul') do set "NPM_GLOBAL=%%i"
    if defined NPM_GLOBAL (
        if exist "!NPM_GLOBAL!\..\appium.cmd" (
            echo       [√] Appium 已安装 ^(npm全局^)
        ) else (
            echo       [X] Appium 未安装
            set /a MISSING_COUNT+=1
            set "MISSING_APPIUM=1"
        )
    ) else (
        echo       [X] Appium 未安装
        set /a MISSING_COUNT+=1
        set "MISSING_APPIUM=1"
    )
) else (
    for /f "tokens=*" %%i in ('appium --version 2^>nul') do set "APPIUM_VER=%%i"
    echo       [√] Appium !APPIUM_VER!
)

:: 6. 检查 UiAutomator2 驱动
echo [6/6] 检查 UiAutomator2 驱动...
if defined MISSING_APPIUM (
    echo       [X] UiAutomator2 ^(需要先安装Appium^)
    set "MISSING_UIA2=1"
) else (
    appium driver list --installed 2>nul | findstr /i "uiautomator2" >nul
    if !errorlevel! neq 0 (
        echo       [X] UiAutomator2 驱动未安装
        set /a MISSING_COUNT+=1
        set "MISSING_UIA2=1"
    ) else (
        echo       [√] UiAutomator2 驱动已安装
    )
)

echo.
echo ============================================================
echo    检查结果: 发现 %MISSING_COUNT% 个缺失项
echo ============================================================

if %MISSING_COUNT% equ 0 (
    echo.
    goto :install_python_deps
)

echo.
echo [阶段2] 安装缺失依赖
echo ------------------------------------------------------------
echo.

:: ============================================================
:: 安装 Python
:: ============================================================
if defined MISSING_PYTHON (
    echo [安装] Python 3.11...
    echo.
    
    :: 方案1: 尝试 winget
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo     尝试通过 winget 安装...
        winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements -h
        if !errorlevel! equ 0 (
            set /a INSTALL_COUNT+=1
            set "NEED_RESTART=1"
            echo     [√] Python 安装成功
            echo     [!] 需要重启此脚本使Python生效
            goto :need_restart
        )
    )
    
    :: 方案2: 引导手动安装
    echo     自动安装失败，请手动安装:
    echo.
    echo     1. 打开浏览器访问: https://www.python.org/downloads/
    echo     2. 下载 Python 3.11 或更高版本
    echo     3. 安装时务必勾选 "Add Python to PATH"
    echo     4. 安装完成后重新运行此脚本
    echo.
    echo     按任意键打开下载页面...
    pause >nul
    start https://www.python.org/downloads/
    goto :end_error
)

:: ============================================================
:: 安装 pip
:: ============================================================
if defined MISSING_PIP (
    echo [安装] pip...
    !PYTHON_CMD! -m ensurepip --upgrade >nul 2>&1
    if !errorlevel! equ 0 (
        echo     [√] pip 安装成功
        set /a INSTALL_COUNT+=1
    ) else (
        echo     [!] 尝试在线安装pip...
        powershell -Command "& {Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py'}" 2>nul
        if exist "%TEMP%\get-pip.py" (
            !PYTHON_CMD! "%TEMP%\get-pip.py"
            del "%TEMP%\get-pip.py"
            echo     [√] pip 安装成功
            set /a INSTALL_COUNT+=1
        ) else (
            echo     [X] pip 安装失败
        )
    )
    echo.
)

:: ============================================================
:: 安装 Node.js
:: ============================================================
if defined MISSING_NODE (
    echo [安装] Node.js LTS...
    echo.
    
    :: 方案1: 尝试 winget
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo     尝试通过 winget 安装...
        winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements -h
        if !errorlevel! equ 0 (
            set /a INSTALL_COUNT+=1
            set "NEED_RESTART=1"
            echo     [√] Node.js 安装成功
            echo     [!] 需要重启此脚本使Node.js生效
            goto :need_restart
        )
    )
    
    :: 方案2: 直接下载安装
    echo     尝试直接下载安装包...
    set "NODE_MSI=%TEMP%\node-install.msi"
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi' -OutFile '%NODE_MSI%'}" 2>nul
    
    if exist "!NODE_MSI!" (
        echo     正在安装 Node.js...
        msiexec /i "!NODE_MSI!" /qn /norestart
        del "!NODE_MSI!"
        set /a INSTALL_COUNT+=1
        set "NEED_RESTART=1"
        echo     [√] Node.js 安装成功
        goto :need_restart
    )
    
    :: 方案3: 引导手动安装
    echo     自动安装失败，请手动安装:
    echo     https://nodejs.org/
    start https://nodejs.org/
    goto :end_error
)

:: ============================================================
:: 安装 ADB
:: ============================================================
if defined MISSING_ADB (
    echo [安装] ADB ^(Android Platform Tools^)...
    
    :: 创建本地工具目录
    if not exist "%TOOLS_DIR%" mkdir "%TOOLS_DIR%"
    
    set "ADB_ZIP=%TEMP%\platform-tools.zip"
    echo     正在下载 platform-tools...
    
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile '%ADB_ZIP%'}" 2>nul
    
    if exist "!ADB_ZIP!" (
        echo     正在解压到 %TOOLS_DIR%...
        powershell -Command "& {Expand-Archive -Path '%ADB_ZIP%' -DestinationPath '%TOOLS_DIR%' -Force}" 2>nul
        del "!ADB_ZIP!"
        
        if exist "%TOOLS_DIR%\platform-tools\adb.exe" (
            set "PATH=%PATH%;%TOOLS_DIR%\platform-tools"
            set /a INSTALL_COUNT+=1
            echo     [√] ADB 安装成功: %TOOLS_DIR%\platform-tools
        ) else (
            echo     [X] 解压失败
        )
    ) else (
        echo     [X] 下载失败，请手动下载:
        echo     https://developer.android.com/studio/releases/platform-tools
        start https://developer.android.com/studio/releases/platform-tools
    )
    echo.
)

:: ============================================================
:: 安装 Appium
:: ============================================================
if defined MISSING_APPIUM (
    echo [安装] Appium...
    
    :: 检查npm是否可用
    where npm >nul 2>&1
    if !errorlevel! neq 0 (
        echo     [X] npm 不可用，请先安装 Node.js
        goto :end_error
    )
    
    echo     正在通过 npm 全局安装 appium...
    call npm install -g appium 2>nul
    
    if !errorlevel! equ 0 (
        set /a INSTALL_COUNT+=1
        echo     [√] Appium 安装成功
    ) else (
        echo     [!] 尝试使用淘宝镜像...
        call npm install -g appium --registry=https://registry.npmmirror.com 2>nul
        if !errorlevel! equ 0 (
            set /a INSTALL_COUNT+=1
            echo     [√] Appium 安装成功 ^(淘宝镜像^)
        ) else (
            echo     [X] Appium 安装失败
            echo     请尝试手动运行: npm install -g appium
        )
    )
    echo.
)

:: ============================================================
:: 安装 UiAutomator2 驱动
:: ============================================================
if defined MISSING_UIA2 (
    if not defined MISSING_APPIUM (
        echo [安装] UiAutomator2 驱动...
        call appium driver install uiautomator2 2>nul
        if !errorlevel! equ 0 (
            set /a INSTALL_COUNT+=1
            echo     [√] UiAutomator2 驱动安装成功
        ) else (
            echo     [X] UiAutomator2 驱动安装失败
            echo     请尝试手动运行: appium driver install uiautomator2
        )
        echo.
    )
)

:: ============================================================
:: 安装 Python 依赖
:: ============================================================
:install_python_deps
echo [安装] Python 依赖包...

:: 确定pip命令
if defined PYTHON_CMD (
    set "PIP_CMD=!PYTHON_CMD! -m pip"
) else (
    set "PIP_CMD=pip"
)

:: 检查requirements.txt是否存在
if not exist "%SCRIPT_DIR%requirements.txt" (
    echo     [X] 未找到 requirements.txt
    goto :verify_device
)

:: 使用清华镜像安装
!PIP_CMD! install -r "%SCRIPT_DIR%requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -q
if %errorlevel% equ 0 (
    set /a INSTALL_COUNT+=1
    echo     [√] Python 依赖安装成功
) else (
    echo     [!] 清华镜像失败，尝试官方源...
    !PIP_CMD! install -r "%SCRIPT_DIR%requirements.txt" -q
    if !errorlevel! equ 0 (
        set /a INSTALL_COUNT+=1
        echo     [√] Python 依赖安装成功
    ) else (
        echo     [X] Python 依赖安装失败
    )
)
echo.

:: ============================================================
:: 验证设备连接
:: ============================================================
:verify_device
echo ============================================================
echo    验证 Android 设备连接
echo ============================================================
echo.

where adb >nul 2>&1
if %errorlevel% equ 0 (
    adb kill-server >nul 2>&1
    adb start-server >nul 2>&1
    echo 已连接的设备:
    adb devices
    echo.
) else if exist "%TOOLS_DIR%\platform-tools\adb.exe" (
    "%TOOLS_DIR%\platform-tools\adb" kill-server >nul 2>&1
    "%TOOLS_DIR%\platform-tools\adb" start-server >nul 2>&1
    echo 已连接的设备:
    "%TOOLS_DIR%\platform-tools\adb" devices
    echo.
) else (
    echo [!] ADB 不可用，无法检测设备
    echo.
)

echo 如果没有显示设备ID，请检查:
echo   1. USB线是否连接牢固
echo   2. 手机是否开启 USB调试 ^(开发者选项中^)
echo   3. 手机是否授权此电脑调试
echo.

goto :end_success

:: ============================================================
:: 需要重启
:: ============================================================
:need_restart
echo.
echo ============================================================
echo    [!] 需要重启脚本
echo ============================================================
echo.
echo 部分组件安装后需要重新加载环境变量
echo 请关闭此窗口，然后重新运行 setup_env.bat
echo.
pause
exit /b 0

:: ============================================================
:: 安装出错
:: ============================================================
:end_error
echo.
echo ============================================================
echo    [X] 安装未完成
echo ============================================================
echo.
echo 请解决上述问题后重新运行此脚本
echo.
pause
exit /b 1

:: ============================================================
:: 安装成功
:: ============================================================
:end_success
echo ============================================================
echo    [√] 环境配置完成! 共安装 %INSTALL_COUNT% 个组件
echo ============================================================
echo.
echo 使用方法:
echo   1. 双击 start_appium.bat 启动Appium服务器
echo   2. 在手机上打开微信视频号直播间
echo   3. 双击 run.bat 运行自动化程序
echo.
echo 或使用命令行:
echo   appium                     ^(启动服务器^)
echo   python main.py             ^(运行程序^)
echo   python main.py -d 120      ^(运行120秒^)
echo.
echo ============================================================
pause
exit /b 0
