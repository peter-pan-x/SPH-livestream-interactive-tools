"""
坐标校准器 - 换手机时运行一次
校准数据保存到 calibration.json
"""
import sys
import json
import subprocess
import re
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config
from core.driver import DriverManager
from core.logger import setup_logger

CALIBRATION_FILE = PROJECT_ROOT / "calibration.json"
logger = setup_logger(__name__, verbose=True)


class Calibrator:
    def __init__(self, config: Config):
        self.config = config
        self.driver_manager = None
        self._touch_max = (None, None)
        
        # 校准结果
        self.data = {
            "like_pos": None,
            "comment_pos": None,
            "send_pos": None,
            "screen_size": None
        }
    
    def _get_touch_max(self) -> tuple:
        """获取触摸屏最大坐标值"""
        try:
            result = subprocess.run(
                ['adb', 'shell', 'getevent', '-p'],
                capture_output=True, text=True, timeout=5
            )
            max_x, max_y = None, None
            for line in result.stdout.split('\n'):
                if 'ABS_MT_POSITION_X' in line or '0035' in line:
                    match = re.search(r'max\s+(\d+)', line)
                    if match:
                        max_x = int(match.group(1))
                elif 'ABS_MT_POSITION_Y' in line or '0036' in line:
                    match = re.search(r'max\s+(\d+)', line)
                    if match:
                        max_y = int(match.group(1))
            return (max_x, max_y)
        except:
            return (None, None)
    
    def _wait_for_tap(self) -> tuple:
        """等待用户点击，返回屏幕坐标"""
        try:
            result = subprocess.run(
                ['adb', 'shell', 'getevent', '-c', '50', '-l'],
                capture_output=True, text=True, timeout=30
            )
            raw_x, raw_y = None, None
            for line in result.stdout.split('\n'):
                if 'ABS_MT_POSITION_X' in line:
                    match = re.search(r'([0-9a-fA-F]+)\s*$', line)
                    if match:
                        raw_x = int(match.group(1), 16)
                elif 'ABS_MT_POSITION_Y' in line:
                    match = re.search(r'([0-9a-fA-F]+)\s*$', line)
                    if match:
                        raw_y = int(match.group(1), 16)
            
            if raw_x and raw_y:
                screen_w = self.driver_manager.screen_width
                screen_h = self.driver_manager.screen_height
                max_x, max_y = self._touch_max
                
                if max_x and max_y:
                    x = int(raw_x * screen_w / max_x)
                    y = int(raw_y * screen_h / max_y)
                else:
                    x, y = raw_x, raw_y
                return (x, y)
        except Exception as e:
            print(f"  获取坐标失败: {e}")
        return None
    
    def run(self):
        """运行校准"""
        print("\n" + "=" * 50)
        print("         坐标校准器")
        print("=" * 50)
        print("\n请确保手机已打开视频号直播间\n")
        
        # 连接设备
        print("正在连接设备...")
        self.driver_manager = DriverManager(self.config)
        self.driver_manager.connect()
        
        self._touch_max = self._get_touch_max()
        self.data["screen_size"] = {
            "width": self.driver_manager.screen_width,
            "height": self.driver_manager.screen_height
        }
        print(f"屏幕尺寸: {self.driver_manager.screen_width}x{self.driver_manager.screen_height}")
        
        # 校准点赞
        print("\n>>> 请点击 [赞] 按钮 3 次")
        like_coords = []
        for i in range(3):
            print(f"  等待第 {i+1}/3 次点击...")
            pos = self._wait_for_tap()
            if pos:
                like_coords.append(pos)
                print(f"  记录: ({pos[0]}, {pos[1]})")
        
        if like_coords:
            avg_x = sum(p[0] for p in like_coords) // len(like_coords)
            avg_y = sum(p[1] for p in like_coords) // len(like_coords)
            self.data["like_pos"] = [avg_x, avg_y]
        
        # 校准评论入口
        print("\n>>> 请点击 [聊一聊] 按钮 1 次")
        pos = self._wait_for_tap()
        if pos:
            self.data["comment_pos"] = [pos[0], pos[1]]
        
        # 校准发送按钮
        print("\n>>> 请点击 [聊一聊] 打开输入框，然后点击 [发送] 按钮")
        pos = self._wait_for_tap()
        if pos:
            self.data["send_pos"] = [pos[0], pos[1]]
        
        # 保存
        self.save()
        
        # 显示结果
        print("\n" + "=" * 50)
        print("         校准完成!")
        print("=" * 50)
        print(f"  点赞: {self.data['like_pos']}")
        print(f"  评论: {self.data['comment_pos']}")
        print(f"  发送: {self.data['send_pos']}")
        print(f"\n已保存到: {CALIBRATION_FILE}")
        print("\n现在可以运行 run.bat 启动自动化程序了!")
        print("=" * 50)
        
        # 断开连接
        self.driver_manager.disconnect()
    
    def save(self):
        """保存校准数据"""
        with open(CALIBRATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)


def load_calibration() -> dict:
    """加载校准数据"""
    if not CALIBRATION_FILE.exists():
        return None
    try:
        with open(CALIBRATION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def main():
    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        sys.exit(1)
    
    config = Config(str(config_path))
    calibrator = Calibrator(config)
    
    try:
        calibrator.run()
    except KeyboardInterrupt:
        print("\n用户取消")
    except Exception as e:
        print(f"校准失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
