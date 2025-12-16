"""任务调度器模块"""
import time
import json
import threading
import logging
from pathlib import Path
from typing import Optional

from .config import Config
from .driver import DriverManager
from actions.like import LikeAction
from actions.comment import CommentAction

logger = logging.getLogger(__name__)

CALIBRATION_FILE = Path(__file__).parent.parent / "calibration.json"


class TaskScheduler:
    """任务调度器 - 协调点赞和评论任务"""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver_manager: Optional[DriverManager] = None
        self.like_action: Optional[LikeAction] = None
        self.comment_action: Optional[CommentAction] = None
        
        self._running = False
        self._stop_event = threading.Event()
        self._start_time: Optional[float] = None
        
        # 校准坐标
        self.like_pos = None
        self.comment_pos = None
        self.send_pos = None
    
    def _load_calibration(self) -> bool:
        """加载校准数据"""
        if not CALIBRATION_FILE.exists():
            return False
        
        try:
            with open(CALIBRATION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.like_pos = tuple(data["like_pos"]) if data.get("like_pos") else None
            self.comment_pos = tuple(data["comment_pos"]) if data.get("comment_pos") else None
            self.send_pos = tuple(data["send_pos"]) if data.get("send_pos") else None
            
            logger.info(f"已加载校准数据: 点赞{self.like_pos}, 评论{self.comment_pos}, 发送{self.send_pos}")
            return True
        except Exception as e:
            logger.error(f"加载校准数据失败: {e}")
            return False
    
    def initialize(self):
        """初始化驱动和动作模块"""
        logger.info("初始化任务调度器...")
        
        # 加载校准数据
        if not self._load_calibration():
            logger.error("未找到校准数据，请先运行 calibrate.bat 进行校准")
            raise RuntimeError("未找到校准数据，请先运行 calibrate.bat")
        
        # 初始化驱动管理器
        self.driver_manager = DriverManager(self.config)
        self.driver_manager.connect()
        
        # 初始化动作模块
        self.like_action = LikeAction(
            self.driver_manager,
            self.config.like,
            calibrated_pos=self.like_pos
        )
        self.comment_action = CommentAction(
            self.driver_manager.driver,
            self.config.comment,
            calibrated_pos=self.comment_pos,
            send_pos=self.send_pos
        )
        
        logger.info("初始化完成")
    
    def _get_remaining_time(self) -> float:
        """获取剩余运行时间"""
        if not self._start_time:
            return self.config.runtime.duration
        elapsed = time.time() - self._start_time
        return max(0, self.config.runtime.duration - elapsed)
    
    def _is_time_up(self) -> bool:
        """检查是否超时"""
        return self._get_remaining_time() <= 0
    
    def run(self):
        """
        运行主任务循环
        
        执行逻辑：
        1. 获取下一次评论的间隔时间
        2. 在间隔时间内持续点赞
        3. 执行评论
        4. 重复直到时间结束
        """
        if not self.driver_manager or not self.like_action or not self.comment_action:
            raise RuntimeError("调度器未初始化，请先调用 initialize()")
        
        self._running = True
        self._stop_event.clear()
        self._start_time = time.time()
        
        duration = self.config.runtime.duration
        logger.info(f"开始执行任务，总时长 {duration} 秒")
        
        try:
            while not self._is_time_up() and not self._stop_event.is_set():
                # 获取本轮等待时间
                wait_time = self.comment_action.get_next_interval()
                remaining = self._get_remaining_time()
                
                # 确保不超过剩余时间
                actual_wait = min(wait_time, remaining)
                
                if actual_wait > 0:
                    logger.info(f"点赞中... (持续 {actual_wait:.1f}秒，剩余 {remaining:.1f}秒)")
                    
                    # 在等待期间执行点赞
                    self.like_action.execute_for_duration(
                        actual_wait,
                        self._stop_event
                    )
                
                # 检查是否该结束了
                if self._is_time_up() or self._stop_event.is_set():
                    break
                
                # 执行评论
                logger.info("执行评论...")
                self.comment_action.execute()
            
            self._print_summary()
            
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止...")
        except Exception as e:
            logger.error(f"任务执行出错: {e}")
            raise
        finally:
            self._running = False
    
    def stop(self):
        """停止任务"""
        logger.info("正在停止任务...")
        self._stop_event.set()
    
    def cleanup(self):
        """清理资源"""
        if self.driver_manager:
            self.driver_manager.disconnect()
    
    def _print_summary(self):
        """打印执行摘要"""
        elapsed = time.time() - self._start_time if self._start_time else 0
        likes = self.like_action.total_clicks if self.like_action else 0
        comments = self.comment_action.total_comments if self.comment_action else 0
        
        logger.info("=" * 40)
        logger.info("任务执行完成")
        logger.info(f"  运行时长: {elapsed:.1f} 秒")
        logger.info(f"  总点赞数: {likes}")
        logger.info(f"  总评论数: {comments}")
        logger.info("=" * 40)
