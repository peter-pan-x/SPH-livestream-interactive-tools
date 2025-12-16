# 微信视频号直播间自动化程序

基于 Appium 的 RPA 自动化工具，用于在微信视频号直播间自动执行点赞和评论操作。

## 功能

- **自动点赞**：在直播间屏幕中间区域持续点赞，每秒 6-8 次
- **自动评论**：每 20-40 秒从预设列表中随机选择一条评论发送
- **可配置**：所有参数均可通过 config.yaml 配置

## 环境要求

- Python 3.8+
- Appium Server 2.x
- Android 设备（已开启 USB 调试）
- ADB 工具

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Appium 服务器
appium
```

## 使用方法

1. **连接设备**：通过 USB 连接 Android 手机，确保 ADB 可识别
   ```bash
   adb devices
   ```

2. **打开直播间**：在手机上打开微信 → 视频号 → 进入目标直播间

3. **修改配置**：编辑 `config.yaml` 设置评论内容和运行时长

4. **运行程序**：
   ```bash
   python main.py
   ```

## 命令行参数

```
python main.py [-h] [-c CONFIG] [-v] [-d DURATION]

选项:
  -h, --help            显示帮助信息
  -c, --config CONFIG   配置文件路径 (默认: config.yaml)
  -v, --verbose         显示详细日志
  -d, --duration DURATION  覆盖运行时长(秒)
```

## 项目结构

```
sph-autointeraction/
├── config.yaml          # 配置文件
├── main.py              # 主入口
├── requirements.txt     # 依赖列表
├── README.md            # 说明文档
├── core/                # 核心模块
│   ├── __init__.py
│   ├── config.py        # 配置加载
│   ├── driver.py        # Appium驱动管理
│   └── scheduler.py     # 任务调度器
└── actions/             # 动作模块
    ├── __init__.py
    ├── like.py          # 点赞动作
    └── comment.py       # 评论动作
```

## 配置说明

```yaml
# 点赞配置
like:
  clicks_per_second: [6, 8]  # 每秒点击次数范围
  area:                       # 点击区域(屏幕比例)
    x_min: 0.3
    x_max: 0.7
    y_min: 0.3
    y_max: 0.7

# 评论配置
comment:
  interval: [20, 40]          # 评论间隔(秒)
  contents:                   # 预设评论列表
    - "666"
    - "主播加油"

# 运行配置
runtime:
  duration: 240               # 运行时长(秒)
```

## 注意事项

1. 确保 Appium 服务器已启动（默认端口 4723）
2. 运行前请先进入直播间，程序不会自动打开微信
3. 评论元素定位可能因微信版本更新而失效，需要调整 `actions/comment.py` 中的定位器
4. 请合理使用，避免违反平台规则

## License

MIT
