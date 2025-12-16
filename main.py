"""
微信视频号直播间自动化程序
基于Appium的RPA自动化工具

功能：
- 自动点赞：在直播间持续点赞，每秒6-8次
- 自动评论：每20-40秒发送一条随机评论

使用方法：
1. 确保Appium服务器已启动
2. 确保手机已通过USB连接并开启调试模式
3. 在手机上打开微信视频号直播间
4. 运行本程序: python main.py
"""
import sys
import signal
import argparse
import traceback
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config
from core.scheduler import TaskScheduler
from core.logger import setup_logger, log_exception


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='微信视频号直播间自动化程序'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    parser.add_argument(
        '-d', '--duration',
        type=int,
        help='覆盖配置文件中的运行时长(秒)'
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 初始化日志系统（同时输出到控制台和文件）
    logger = setup_logger(__name__, args.verbose)
    
    logger.info("微信视频号直播间自动化程序")
    
    scheduler = None
    exit_code = 0
    
    try:
        # 加载配置
        config_path = PROJECT_ROOT / args.config
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            sys.exit(1)
        
        config = Config(str(config_path))
        
        # 覆盖运行时长
        if args.duration:
            config.runtime.duration = args.duration
            logger.info(f"运行时长已覆盖为: {args.duration}秒")
        
        logger.info(f"配置加载完成:")
        logger.info(f"  - 运行时长: {config.runtime.duration}秒")
        logger.info(f"  - 评论间隔: {config.comment.interval[0]}-{config.comment.interval[1]}秒")
        logger.info(f"  - 点赞频率: {config.like.clicks_per_second[0]}-{config.like.clicks_per_second[1]}次/秒")
        logger.info(f"  - 预设评论: {len(config.comment.contents)}条")
        
        # 创建调度器
        scheduler = TaskScheduler(config)
        
        # 注册信号处理
        def signal_handler(signum, frame):
            sig_name = signal.Signals(signum).name
            logger.info(f"收到信号 {sig_name}，正在优雅退出...")
            if scheduler:
                scheduler.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 初始化
        logger.info("正在连接设备...")
        scheduler.initialize()
        
        # 提示用户
        logger.info("")
        logger.info(">>> 请确保手机已打开视频号直播间 <<<")
        logger.info(">>> 程序将在3秒后开始执行... <<<")
        logger.info("")
        
        import time
        time.sleep(3)
        
        # 运行主循环
        scheduler.run()
        
    except KeyboardInterrupt:
        logger.info("用户手动中断 (Ctrl+C)")
    except Exception as e:
        exit_code = 1
        logger.error(f"程序异常退出: {e}")
        logger.error(f"异常堆栈:\n{traceback.format_exc()}")
    finally:
        # 清理资源
        if scheduler:
            try:
                scheduler.cleanup()
            except Exception as e:
                logger.error(f"清理资源时出错: {e}")
        
        logger.info(f"程序退出，退出码: {exit_code}")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
