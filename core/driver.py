"""Appium驱动管理模块"""
import subprocess
import time
import requests
from appium import webdriver
from appium.options.android import UiAutomator2Options
from typing import Optional
import logging

from .config import Config

logger = logging.getLogger(__name__)

# 连接重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒


class DriverManager:
    """Appium驱动管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver: Optional[webdriver.Remote] = None
        self._screen_size = None
    
    def _get_device_name(self) -> str:
        """自动获取已连接的设备名称"""
        if self.config.device.device_name != "auto":
            return self.config.device.device_name
        
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            for line in lines:
                if '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    logger.info(f"检测到设备: {device_id}")
                    return device_id
        except Exception as e:
            logger.error(f"获取设备失败: {e}")
        
        raise RuntimeError("未检测到已连接的Android设备，请检查USB连接")
    
    def _check_appium_server(self) -> bool:
        """检查Appium服务器是否就绪"""
        appium_url = self.config.get_appium_url()
        try:
            response = requests.get(f"{appium_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('value', {}).get('ready', False):
                    return True
        except Exception as e:
            logger.debug(f"Appium服务器检查失败: {e}")
        return False
    
    def _wait_for_appium(self, timeout: int = 30) -> bool:
        """等待Appium服务器就绪"""
        logger.info("等待Appium服务器就绪...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._check_appium_server():
                logger.info("Appium服务器已就绪")
                return True
            time.sleep(1)
        return False

    def connect(self) -> webdriver.Remote:
        """连接Appium服务器并初始化驱动（带重试）"""
        device_name = self._get_device_name()
        appium_url = self.config.get_appium_url()
        
        # 先检查Appium服务器
        if not self._check_appium_server():
            logger.warning("Appium服务器未响应，等待启动...")
            if not self._wait_for_appium(timeout=30):
                raise RuntimeError(
                    f"Appium服务器未就绪 ({appium_url})\n"
                    "请确保已运行 start_appium.bat 或 appium 命令"
                )
        
        options = UiAutomator2Options()
        options.platform_name = self.config.device.platform_name
        options.device_name = device_name
        options.no_reset = True
        
        # 设置自动化引擎
        options.automation_name = "UiAutomator2"
        
        # 关键：不启动任何应用，保持当前屏幕状态（用户已打开直播间）
        options.set_capability("autoLaunch", False)
        options.set_capability("skipUnlock", True)
        options.set_capability("noReset", True)
        # 防止长时间无命令断开连接（设置10分钟）
        options.set_capability("newCommandTimeout", 600)
        
        # 跳过服务器重复安装（已安装过就不再安装）
        options.set_capability("skipServerInstallation", True)
        options.set_capability("skipDeviceInitialization", True)
        
        logger.info(f"连接Appium服务器: {appium_url}")
        
        # 重试连接
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"尝试连接... (第{attempt}/{MAX_RETRIES}次)")
                self.driver = webdriver.Remote(appium_url, options=options)
                self._screen_size = self.driver.get_window_size()
                logger.info(f"连接成功，屏幕尺寸: {self._screen_size}")
                return self.driver
            except Exception as e:
                last_error = e
                logger.warning(f"连接失败: {e}")
                if attempt < MAX_RETRIES:
                    logger.info(f"{RETRY_DELAY}秒后重试...")
                    time.sleep(RETRY_DELAY)
        
        # 所有重试都失败
        error_msg = (
            f"连接Appium失败 (已重试{MAX_RETRIES}次)\n"
            f"错误: {last_error}\n\n"
            "请检查:\n"
            "1. Appium服务器是否正常运行\n"
            "2. 手机是否已连接并授权USB调试\n"
            "3. UiAutomator2驱动是否已安装 (appium driver list)"
        )
        raise RuntimeError(error_msg)
    
    @property
    def screen_width(self) -> int:
        """屏幕宽度"""
        return self._screen_size['width'] if self._screen_size else 0
    
    @property
    def screen_height(self) -> int:
        """屏幕高度"""
        return self._screen_size['height'] if self._screen_size else 0
    
    def tap(self, x: int, y: int):
        """快速点击指定坐标"""
        if self.driver:
            # duration=0 表示快速tap，不是长按
            self.driver.tap([(x, y)], duration=0)
    
    def disconnect(self):
        """断开连接"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("已断开Appium连接")
            except Exception as e:
                logger.warning(f"断开连接时出错: {e}")
            finally:
                self.driver = None
