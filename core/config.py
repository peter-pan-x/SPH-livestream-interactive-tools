"""配置加载模块"""
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class AppiumConfig:
    host: str
    port: int


@dataclass
class DeviceConfig:
    platform_name: str
    device_name: str


@dataclass
class LikeConfig:
    clicks_per_second: Tuple[int, int]
    x_min: float
    x_max: float
    y_min: float
    y_max: float


@dataclass
class CommentConfig:
    interval: Tuple[int, int]
    contents: List[str]


@dataclass
class RuntimeConfig:
    duration: int


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        self._load(config_path)
    
    def _load(self, config_path: str):
        """加载YAML配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 解析Appium配置
        self.appium = AppiumConfig(
            host=data['appium']['host'],
            port=data['appium']['port']
        )
        
        # 解析设备配置
        self.device = DeviceConfig(
            platform_name=data['device']['platform_name'],
            device_name=data['device']['device_name']
        )
        
        # 解析点赞配置
        like_data = data['like']
        self.like = LikeConfig(
            clicks_per_second=tuple(like_data['clicks_per_second']),
            x_min=like_data['area']['x_min'],
            x_max=like_data['area']['x_max'],
            y_min=like_data['area']['y_min'],
            y_max=like_data['area']['y_max']
        )
        
        # 解析评论配置
        comment_data = data['comment']
        self.comment = CommentConfig(
            interval=tuple(comment_data['interval']),
            contents=comment_data['contents']
        )
        
        # 解析运行配置
        self.runtime = RuntimeConfig(
            duration=data['runtime']['duration']
        )
    
    def get_appium_url(self) -> str:
        """获取Appium服务器URL"""
        return f"http://{self.appium.host}:{self.appium.port}"
