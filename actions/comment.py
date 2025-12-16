"""评论动作模块"""
import random
import subprocess
import time
import logging
from typing import TYPE_CHECKING, Optional
from appium.webdriver.common.appiumby import AppiumBy

if TYPE_CHECKING:
    from appium.webdriver import Remote
    from core.config import CommentConfig

logger = logging.getLogger(__name__)


class CommentAction:
    """评论动作执行器"""
    
    def __init__(self, driver: 'Remote', comment_config: 'CommentConfig',
                 calibrated_pos: tuple = None, send_pos: tuple = None):
        self.driver = driver
        self.config = comment_config
        self.pos = calibrated_pos      # (x, y) 聊一聊按钮位置
        self.send_pos = send_pos       # (x, y) 发送按钮位置
        self._comment_count = 0
    
    def _get_random_content(self) -> str:
        """随机获取一条评论内容"""
        return random.choice(self.config.contents)
    
    def _input_text(self, text: str) -> bool:
        """输入文字（支持中文）"""
        # 方法1: 使用 Appium 剪贴板
        try:
            import base64
            # 设置剪贴板内容
            self.driver.set_clipboard_text(text)
            time.sleep(0.3)
            # 长按粘贴
            subprocess.run(
                ['adb', 'shell', 'input', 'keyevent', '279'],  # KEYCODE_PASTE
                capture_output=True, timeout=5
            )
            logger.info(f"已输入: {text}")
            return True
        except Exception as e:
            logger.warning(f"Appium剪贴板失败: {e}")
        
        # 方法2: 直接 send_keys 到输入框
        try:
            elements = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if elements:
                elements[0].send_keys(text)
                logger.info(f"已输入: {text}")
                return True
        except Exception as e:
            logger.warning(f"send_keys失败: {e}")
        
        return False
    
    def _click_send(self) -> bool:
        """点击发送按钮（必须用校准坐标）"""
        if not self.send_pos:
            logger.warning("未校准发送按钮位置")
            return False
        
        x, y = self.send_pos
        logger.info(f"点击发送按钮: ({x}, {y})")
        self.driver.tap([(x, y)], duration=0)
        return True
    
    def execute(self) -> bool:
        """执行一次评论操作"""
        content = self._get_random_content()
        logger.info(f"准备发送评论: {content}")
        
        try:
            # 步骤1: 点击评论入口
            if not self.pos:
                logger.warning("未校准评论按钮位置")
                return False
            
            self.driver.tap([(self.pos[0], self.pos[1])], duration=0)
            time.sleep(1.0)  # 等待输入框弹出
            
            # 步骤2: 输入评论内容
            if not self._input_text(content):
                logger.warning("输入评论失败")
                return False
            
            time.sleep(1.0)  # 等待输入完成
            
            # 步骤3: 点击发送
            if not self._click_send():
                return False
            
            time.sleep(1.0)  # 等待发送完成
            
            self._comment_count += 1
            logger.info(f"评论发送成功 (第{self._comment_count}条)")
            return True
            
        except Exception as e:
            logger.error(f"评论发送失败: {e}")
            return False
    
    def get_next_interval(self) -> float:
        """获取下一次评论的间隔时间"""
        return random.uniform(*self.config.interval)
    
    @property
    def total_comments(self) -> int:
        """总评论数"""
        return self._comment_count
