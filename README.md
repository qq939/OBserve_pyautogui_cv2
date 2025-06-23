# Referances - vediochat
## 导入必要的库
from videochat import VideoChatModel, VideoProcessor

## 初始化模型
model = VideoChatModel.from_pretrained("videochat-base")
processor = VideoProcessor()

## 加载视频文件
video_path = "path/to/your/video.mp4"
video_frames = processor.load_video(video_path, max_frames=100)  # 限制最大帧数

## 准备问题（文本输入）
user_question = "视频中发生了什么？"

## 进行多模态推理
response = model.generate_response(
    video=video_frames,
    question=user_question,
    max_length=512,
    temperature=0.7
)

## 打印AI回复
print("AI回答:", response)


# 屏幕录制和截图工具

使用 PyAutoGUI 和 OpenCV 实现的屏幕录制工具，支持录制5分钟视频并提取指定分钟的截图。

## 功能特性

- 🎥 录制5分钟高质量屏幕视频
- 📸 从录制的视频中提取任意分钟的截图
- 🎛️ 可调节录制参数（帧率、输出目录等）
- 💾 自动管理输出文件和目录
- 🔄 支持中断录制和进度显示

## 环境要求

- Python 3.7+
- Windows 操作系统

## 安装依赖

### 使用 uv（推荐）

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境（Windows）
.venv\Scripts\activate

# 安装依赖
uv pip install -r requirements.txt
```

### 使用 pip

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 1. 基本使用

```python
from screen_recorder import ScreenRecorder

# 创建录制器
recorder = ScreenRecorder(output_dir="recordings")

# 录制5分钟视频
video_path = recorder.record_screen(duration_minutes=5)

# 提取第3分钟的截图
screenshot_path = recorder.extract_frame_at_minute(video_path, minute=3)
```

### 2. 交互式使用

```bash
# 运行主程序
python screen_recorder.py

# 或运行示例程序
python example_usage.py
```

### 3. 快速演示

```bash
python example_usage.py
# 选择选项1进行快速演示
```

## API 参考

### ScreenRecorder 类

#### 初始化
```python
recorder = ScreenRecorder(output_dir="recordings")
```

#### 录制屏幕
```python
video_path = recorder.record_screen(
    duration_minutes=5,  # 录制时长（分钟）
    fps=20              # 帧率
)
```

#### 提取截图
```python
screenshot_path = recorder.extract_frame_at_minute(
    video_path,          # 视频文件路径
    minute,             # 要提取的分钟数（1-5）
    output_filename     # 输出文件名（可选）
)
```

#### 获取最新录制
```python
latest_video = recorder.get_latest_recording()
```

## 输出文件

- **视频文件**: `recordings/screen_recording_YYYYMMDD_HHMMSS.avi`
- **截图文件**: `recordings/screenshot_minute_X_YYYYMMDD_HHMMSS.png`

## 注意事项

1. **权限要求**: 程序需要屏幕截图权限
2. **性能影响**: 录制过程会占用一定的CPU和磁盘资源
3. **文件大小**: 5分钟视频文件大小约为几百MB（取决于屏幕分辨率和帧率）
4. **中断录制**: 可以使用 Ctrl+C 提前停止录制

## VSCode 快捷键提示

在 VSCode 中开发时，可以使用以下快捷键：

- `Ctrl + Shift + P`: 打开命令面板
- `Ctrl + \``: 打开终端
- `F5`: 运行调试
- `Ctrl + Shift + \``: 创建新终端
- `Ctrl + Space`: 代码补全
- `Ctrl + Shift + I`: 格式化代码
- `Ctrl + /`: 注释/取消注释
- `Alt + Shift + F`: 格式化整个文档

## 故障排除

### 常见问题

1. **导入错误**: 确保已安装所有依赖包
2. **权限错误**: 确保程序有屏幕截图权限
3. **文件路径错误**: 使用绝对路径或确保相对路径正确
4. **视频无法播放**: 确保系统支持XVID编码器

### 依赖问题解决

```bash
# 如果 pyautogui 安装失败
pip install --upgrade pip
pip install pyautogui

# 如果 opencv-python 安装失败
pip install opencv-python-headless
```

## 开发信息

- **开发者**: qq9393
- **邮箱**: 939342547@qq.com
- **版本**: 1.0.0
- **许可证**: MIT

## 更新日志

### v1.0.0 (2024)
- 初始版本发布
- 实现基本的屏幕录制功能
- 实现截图提取功能
- 添加交互式界面