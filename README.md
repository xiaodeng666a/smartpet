一个基于 Python、PySide6 和 LangChain 的阿尼亚桌宠项目。

这个项目实现了一个可在 Windows 桌面运行的阿尼亚桌宠，支持桌面跟随、动作切换、聊天气泡交互，以及喝水提醒等功能。

## Features

- 桌面桌宠显示
- 鼠标跟随
- 聊天气泡交互
- 多种动作切换
  - 趴狗狗
  - 喝水
  - 看电影
  - 睡觉
- 定时喝水提醒
- 支持打包为 Windows 可执行程序

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
├─ install_shortcuts.ps1    # 快捷方式安装脚本
└─ launch_pet.vbs           # 启动脚本

## API 配置

本项目不自带可直接使用的模型接口。

使用前，你需要自己配置 API key。请在项目根目录创建 `.env` 文件，例如：

```env
OPENAI_API_KEY=your_api_key_here
DASHSCOPE_API_KEY=your_api_key_here
