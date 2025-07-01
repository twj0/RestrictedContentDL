<h1 align="center">Restricted Content Downloader Telegram Bot</h1>

<p align="center">
  <a href="https://github.com/bisnuray/RestrictedContentDL/stargazers"><img src="https://img.shields.io/github/stars/bisnuray/RestrictedContentDL?color=blue&style=flat" alt="GitHub Repo stars"></a>
  <a href="https://github.com/bisnuray/RestrictedContentDL/issues"><img src="https://img.shields.io/github/issues/bisnuray/RestrictedContentDL" alt="GitHub issues"></a>
  <a href="https://github.com/bisnuray/RestrictedContentDL/pulls"><img src="https://img.shields.io/github/issues-pr/bisnuray/RestrictedContentDL" alt="GitHub pull requests"></a>
  <a href="https://github.com/bisnuray/RestrictedContentDL/graphs/contributors"><img src="https://img.shields.io/github/contributors/bisnuray/RestrictedContentDL?style=flat" alt="GitHub contributors"></a>
  <a href="https://github.com/bisnuray/RestrictedContentDL/network/members"><img src="https://img.shields.io/github/forks/bisnuray/RestrictedContentDL?style=flat" alt="GitHub forks"></a>
</p>

<p align="center">
  <em>Restricted Content Downloader: An advanced Telegram bot script to download restricted content such as photos, videos, audio files, or documents from Telegram private chats or channels. This bot can also copy text messages from Telegram posts.</em>
</p>
<hr>

---

下面是我对这个项目的一些二次开发的说明
喜欢的话就给原作者点赞吧

---


这是一个基于Python、FastAPI和Pyrogram构建的功能强大的Web应用程序

本应用从一个简单的下载脚本（[RestrictedContentDL](https://github.com/bisnuray/RestrictedContentDL)）二次开发而来，通过引入Web界面、异步后台任务和健壮的错误处理，将其升级为一个成熟的、可靠的个人媒体中心。


---

## 🏛️ 技术架构



*   **后端 (`backend.py`)**: 基于 **FastAPI** 框架，负责处理所有核心逻辑。它使用 **Pyrogram** 的**用户会话 (User Session)** 来模拟真实用户，从而访问Telegram API获取数据和执行操作。
*   **前端 (`web/index.html`)**: 一个纯粹的HTML、CSS和JavaScript单页应用，负责与用户交互，并通过API与后端通信。
*   **一体化部署**: 后端服务同时负责托管前端静态文件，您无需配置额外的Web服务器。

---

## 🛠️ 安装与配置指南

请严格按照以下步骤操作，以确保程序顺利运行。

### 第1步：准备环境

*   确保您的电脑上安装了 **Python 3.8+** 和 **Git**。

### 第2步：克隆项目

在您的终端（命令行）中运行：
```bash
git clone [<项目Git仓库地址>](https://github.com/twj0/RestrictedContentDL.git)
cd <项目文件夹名称>如(d:\py_work\RestrictedContentDL)
```

### 第3步：获取4个关键凭证

这是整个配置过程中最重要的一步，请务必使用**您自己的凭证**。

1.  **API_ID 和 API_HASH**:
    *   使用您的Telegram账号登录官方网站 [my.telegram.org](https://my.telegram.org)。
    *   输入电话号码验证如：+8613211451400，然后接码。
    *   进入 "API development tools" 部分。
    *   创建一个新应用，随便填写应用名称，您将会得到 `api_id` 和 `api_hash`。

2.  **BOT_TOKEN**:
    *   在Telegram中，与官方的 `@BotFather` 对话。
    *   发送 `/newbot` 命令，按照提示创建您的机器人。
    *   BotFather会给您一长串由数字和字母组成的Token，这就是 `BOT_TOKEN`。

3.  **SESSION_STRING**:
    *   这是驱动整个应用的核心！它代表您个人账户的登录会话。
    *   在Telegram中，找到 `@StringSessionGen_Bot` 或其他信誉良好的会话生成机器人。
    *   启动机器人，选择Pyrogram v2，然后按照提示输入您的 `API_ID`, `API_HASH`, 手机号和验证码。
    *   机器人会返回给您一长串复杂的字符串，这就是 `SESSION_STRING`。
    *   **安全警告：`SESSION_STRING` 等同于您的账户密码，绝对不要泄露给任何人！**

### 第4步：配置项目

1.  在项目的根目录，创建或找到一个名为 `config.env` 的文件。
2.  将以下内容复制进去，并填上您刚刚获取到的值：

    ```env
    # 请替换为您的真实凭证
    API_ID=1234567
    API_HASH=abcdef1234567890abcdef1234567890
    SESSION_STRING=BAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    BOT_TOKEN=789123:ABCDEFGHIJKLMNOPQRSTUVWXYZ-abcde
    ```

### 第5步：安装依赖

1.  在项目根目录，创建或找到一个名为 `requirements.txt` 的文件。
2.  将以下库名称复制到文件中：
    ```
    Pyrofork
    TgCrypto
    Pyleaves
    python-dotenv
    psutil
    pillow
    fastapi
    uvicorn
    "pyrogram[fastapi]"
    pydantic
    ```
3.  在终端中，运行以下命令来安装所有必需的库：
    ```bash
    pip install -r requirements.txt
    ```

---

## ධ 运行与使用

### 启动后端服务

在您的项目根目录的终端中，运行：
```bash
python backend.py
```
如果一切顺利，您会看到类似 `Uvicorn running on http://0.0.0.0:8000` 的输出。

### 使用Web界面

1.  打开您的浏览器（推荐使用Chrome或Firefox）。
2.  在地址栏输入： `http://127.0.0.1:8000` 并回车。
3.  您将看到精心设计的媒体管理器界面。
4.  在输入框中输入您已加入的频道的用户名（如 `jurunvshen`）或ID（如 `-100123456789`）。
5.  选择您感兴趣的日期范围（或留空以获取全部）。
6.  点击“获取视频”按钮，开始您的媒体探索之旅！

---

## 🩺 疑难解答 (避坑指南)

如果您在运行或使用中遇到问题，99%的可能性都可以在这里找到答案。

#### **问题1：点击“获取视频”后，浏览器弹窗提示 `获取失败: Failed to fetch`。**

这是最常见的问题，由“跨源策略(CORS)”导致。
*   **错误操作**: 您直接用浏览器打开了 `index.html` 文件，导致其地址为 `file://...`。
*   **正确操作**: **请始终通过 `http://127.0.0.1:8000` 这个地址来访问本应用。** 我们的 `backend.py` 已经配置好，会自动为您提供前端页面。

#### **问题2：启动 `backend.py` 正常，但获取视频时长时间无响应，或Pyrogram在终端中报错 `Timeout`。**

这通常是您的**本地网络环境**问题，您的电脑无法稳定连接到Telegram服务器。

*   **解决方案A：配置防火墙**
    *   您的Windows Defender防火墙或第三方杀毒软件可能阻止了Python程序的网络连接。
    *   **操作**: 请为您的 `python.exe` 程序在防火墙的“出站规则”中添一个“允许连接”的例外。

*   **解决方案B：开启网络代理的TUN/增强模式**
    *   如果您正在使用VPN或网络代理，请确保它工作在**全局模式**下，而不仅仅是为浏览器代理。
    *   很多代理工具（如Clash, V2RayN等）提供一个名为 **"TUN Mode"** 或 **"增强模式"** 的选项。**请务必开启它！** 这会创建一个虚拟网卡，接管您电脑上所有程序的网络流量（包括Python），从而让 `backend.py` 也能通过代理访问Telegram。

#### **问题3：获取视频时，返回 `错误 404: Channel not found`。**

*   **原因**: 您用来生成 `SESSION_STRING` 的那个Telegram个人账户，**没有加入**您正在尝试获取的频道。
*   **解决方案**: 请先用您的个人账户加入目标频道，然后再尝试获取。

#### **问题4：一切正常，但下载的文件是0KB或损坏的。**

这可能是文件在下载到服务器 `storage` 目录时出现了问题。
*   **检查**: 查看项目文件夹下的 `storage` 目录，看是否有文件生成，以及文件大小是否正常。
*   **权限**: 确保程序有在项目目录中创建和写入文件的权限。

---

## 📂 项目文件结构

```
/
|-- web/
|   |-- index.html          # 前端界面文件
|   
|-- storage/                # 下载任务完成后，视频文件永久存储在这里
|
|-- temp/                   # 临时文件目录 (如下载的封面图)
|
|-- backend.py              # FastAPI后端主程序
|-- backend.log             # 后端运行日志
|-- config.env              # 私人凭证配置文件
|-- requirements.txt        # 项目依赖库
|-- README.md               # 说明文档
```

---

感谢使用！希望这个工具能为您带来便利。

---
下面是原作者的README.md
---

# Restricted Content Downloader
## Features

- 📥 Download media (photos, videos, audio, documents).
- ✅ Supports downloading from both single media posts and media groups.
- 🔄 Progress bar showing real-time downloading progress.
- ✍️ Copy text messages or captions from Telegram posts.

## Requirements

Before you begin, ensure you have met the following requirements:

- Python 3.8 or higher. recommended Python 3.11
- `pyrofork`, `pyleaves` and `tgcrypto` libraries.
- A Telegram bot token (you can get one from [@BotFather](https://t.me/BotFather) on Telegram).
- API ID and Hash: You can get these by creating an application on [my.telegram.org](https://my.telegram.org).
- To Get `SESSION_STRING` Open [@SmartUtilBot](https://t.me/SmartUtilBot). Bot and use /pyro command and then follow all instructions.

## Installation

To install `pyrofork`, `pyleaves` and `tgcrypto`, run the following command:

```bash
pip install -r -U requirements.txt
```

**Note: If you previously installed `pyrogram`, uninstall it before installing `pyrofork`.**

## Configuration

1. Open the `config.env` file in your favorite text editor.
2. Replace the placeholders for `API_ID`, `API_HASH`, `SESSION_STRING`, and `BOT_TOKEN` with your actual values:
   - **`API_ID`**: Your API ID from [my.telegram.org](https://my.telegram.org).
   - **`API_HASH`**: Your API Hash from [my.telegram.org](https://my.telegram.org).
   - **`SESSION_STRING`**: The session string generated using [@SmartUtilBot](https://t.me/SmartUtilBot).
   - **`BOT_TOKEN`**: The token you obtained from [@BotFather](https://t.me/BotFather).

## Deploy the Bot

```sh
git clone https://github.com/bisnuray/RestrictedContentDL
cd RestrictedContentDL
python main.py
```

## Deploy the Bot Using Docker Compose

```sh
git clone https://github.com/bisnuray/RestrictedContentDL
cd RestrictedContentDL
docker compose up --build --remove-orphans
```

Make sure you have Docker and Docker Compose installed on your system. The bot will run in a containerized environment with all dependencies automatically managed.

To stop the bot:

```sh
docker compose down
```

## Usage

- **`/start`** – Welcomes you and gives a brief introduction.  
- **`/help`** – Shows detailed instructions and examples.  
- **`/dl <post_URL>`** or simply paste a Telegram post link – Fetch photos, videos, audio, or documents from that post.  
- **`/bdl <start_link> <end_link>`** – Batch-download a range of posts in one go.  

  > 💡 Example: `/bdl https://t.me/mychannel/100 https://t.me/mychannel/120`  
- **`/killall`** – Cancel any pending downloads if the bot hangs.  
- **`/logs`** – Download the bot’s logs file.  
- **`/stats`** – View current status (uptime, disk, memory, network, CPU, etc.).  

> **Note:** Make sure that your user session is a member of the source chat or channel before downloading.

## Author

- Name: Bisnu Ray
- Telegram: [@itsSmartDev](https://t.me/itsSmartDev)

> **Note**: If you found this repo helpful, please fork and star it. Also, feel free to share with proper credit!
