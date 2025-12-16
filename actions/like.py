"""点赞动作模块"""
import random
import time
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.driver import DriverManager
    from core.config import LikeConfig

logger = logging.getLogger(__name__)

# 随机偏移范围（像素）
OFFSET = 10


class LikeAction:
    """点赞动作执行器"""
    
    def __init__(self, driver_manager: 'DriverManager', like_config: 'LikeConfig', 
                 calibrated_pos: tuple = None):
        self.driver_manager = driver_manager
        self.config = like_config
        self.pos = calibrated_pos  # (x, y)
        self._click_count = 0
    
    def _get_position(self) -> tuple:
        """获取点击位置"""
        if self.pos:
            # 校准坐标 + 小偏移
            x = self.pos[0] + random.randint(-OFFSET, OFFSET)
            y = self.pos[1] + random.randint(-OFFSET, OFFSET)
            return x, y
        
        # 无校准则用配置区域
        w = self.driver_manager.screen_width
        h = self.driver_manager.screen_height
        x = random.randint(int(w * self.config.x_min), int(w * self.config.x_max))
        y = random.randint(int(h * self.config.y_min), int(h * self.config.y_max))
        return x, y
    
    def execute_once(self):
        """执行单次点赞"""
        x, y = self._get_position()
        self.driver_manager.tap(x, y)
        self._click_count += 1
    
    def execute_for_duration(self, duration: float, stop_event=None):
        """
        在指定时间内持续点赞
        
        Args:
            duration: 持续时间（秒）
            stop_event: 停止事件（threading.Event）
        """
        start_time = time.time()
        clicks_in_this_session = 0
        
        while time.time() - start_time < duration:
            # 检查停止信号
            if stop_event and stop_event.is_set():
                break
            
            # 计算本秒应执行的点击次数
            clicks_per_second = random.randint(*self.config.clicks_per_second)
            interval = 1.0 / clicks_per_second
            
            # 执行点赞
            self.execute_once()
            clicks_in_this_session += 1
            
            # 等待到下一次点击
            time.sleep(interval)
        
        logger.debug(f"本轮点赞完成，共点击 {clicks_in_this_session} 次")
    
    @property
    def total_clicks(self) -> int:
        """总点击次数"""
        return self._click_count
    
    def reset_count(self):
        """重置计数"""
        self._click_count = 0
