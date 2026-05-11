# Anya Desktop Pet

一个基于 Python、PySide6 和 LangChain 的阿尼亚桌宠项目。

这个项目实现了一个可在 Windows 桌面运行的阿尼亚桌宠，支持聊天、动作切换、提醒交互，以及自动检测部分观影/直播场景后切换状态。

## Features

- 桌面桌宠显示
- 聊天气泡交互
- 多种动作切换
  - 趴狗狗
  - 喝水
  - 看电影
  - 伸懒腰
  - 睡觉
- 定时喝水提醒
- 定时久坐提醒
- 自动检测部分视频/直播场景并切换到看电影动作
- 支持打包为 Windows 可执行程序
- 支持桌面快捷方式和开机启动

## Current Interaction Design

- 启动后默认不跟随鼠标
- 按 `F5` 开启或关闭跟随
- 右键桌宠可以切换动作
- 喝水提醒到时间后会切到喝水动作，并弹出确认气泡
- 久坐提醒到时间后会切到伸懒腰动作，并弹出确认气泡

## Tech Stack

- Python
- PySide6
- LangChain

## Environment

- Windows
- Python 3.11+
- PowerShell

## Project Structure

```text
.
├─ assets/                  # 动画帧、图标、素材文件
├─ src/                     # 聊天与逻辑相关代码
├─ gui_app.py               # 桌宠主程序入口
├─ build_exe.ps1            # 打包脚本
├─ install_shortcuts.ps1    # 桌面/启动快捷方式脚本
└─ launch_pet.vbs           # 启动脚本
```

## API Configuration

本项目不自带可直接使用的大模型接口。

聊天功能依赖 LangChain 和外部模型 API。使用前，你需要自行提供可用的 API key，并在项目根目录创建 `.env` 文件，例如：

```env
OPENAI_API_KEY=your_api_key_here
DASHSCOPE_API_KEY=your_api_key_here
```

注意：

- `.env` 中填写的是你自己的真实 key
- 不要把 `.env` 上传到 GitHub
- 建议只上传 `.env.example` 作为示例
- 如果你替换模型服务商，也需要同步调整 LangChain 调用配置

## Run

开发模式运行：

```powershell
cd "E:\Microsoft VS Code\智能体"
python gui_app.py
```

如果已经打包，也可以直接双击可执行文件启动。

## Build

项目支持打包为 Windows 应用程序：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

打包完成后，可执行文件通常位于：

```text
dist\AnyaPet\AnyaPet.exe
```

## Shortcut Installation

如果你想把桌宠快捷方式重新安装到桌面和启动目录，可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install_shortcuts.ps1
```

## Video / Live Detection

当前项目会根据前台窗口的标题和进程名，尝试识别部分视频或直播场景，并自动切换到看电影动作。

已兼容的关键词方向包括：

- Bilibili
- YouTube
- Netflix
- PotPlayer / VLC
- 斗鱼 / 虎牙 / Twitch
- 部分直播页标题关键词，如“直播间”“主播”“正在直播”等

说明：

- 目前逻辑主要依赖前台窗口标题和进程名
- 无法直接读取浏览器地址栏 URL
- 如果某个平台未命中，可以继续补关键词规则

## Notes

- 本项目的聊天能力依赖你自己接入的大模型 API
- 如果 `.env` 没有正确配置，聊天功能可能无法正常使用
- 部分动作素材和图标仍可以继续优化
- 打包产物 `dist/` 和 `build/` 一般不建议上传到 GitHub

## Suggested .gitignore

建议在项目根目录至少包含以下内容：

```gitignore
.venv/
__pycache__/
*.py[cod]

build/
dist/

.env
.env.*
!.env.example

.pytest_cache/
.mypy_cache/

*.log
Thumbs.db
Desktop.ini

assets/backups/
assets/test_outputs/
```

## License

如果你准备公开发布，建议补充合适的 License。

PR-Agent test branch
