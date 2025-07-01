# backend.py (Version 3.0 - The Architect Edition)
# 引入异步后台任务，实现健壮的"仓储-提货"下载模型

import logging
import asyncio
import os
import datetime
import uuid
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

# --- 第三方库导入 ---
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pyrogram import Client
from pyrogram.errors import PeerIdInvalid, UsernameNotOccupied, FloodWait

# --- 本地模块导入 ---
from config import PyroConf

# ==========================================================
# 1. 配置和初始化
# ==========================================================

# 配置日志格式，增加更详细的信息
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)-15s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("backend.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("MediaBackend")

# [升级!] 使用更持久和组织化的存储结构
STORAGE_DIR = Path("storage")
TEMP_DIR = Path("temp")
LOG_DIR = Path("logs")

# 确保所有必要目录存在
for directory in [STORAGE_DIR, TEMP_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True)
    logger.info(f"Directory '{directory}' ready.")

# [全新!] 任务状态管理器 - 更完善的状态跟踪
DOWNLOAD_TASKS: Dict[str, Dict[str, Any]] = {}

# 任务状态常量
class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

app = FastAPI(
    title="Telegram Media Backend",
    version="3.0.0",
    description="Advanced Telegram media management with async download architecture"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pyrogram 客户端初始化
try:
    user = Client(
        "user_session",
        api_id=PyroConf.API_ID,
        api_hash=PyroConf.API_HASH,
        session_string=PyroConf.SESSION_STRING
    )
    logger.info("Pyrogram client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Pyrogram client: {e}")
    raise

# ==========================================================
# 2. 数据模型
# ==========================================================

class DownloadRequest(BaseModel):
    chat_id: int = Field(..., description="Telegram chat ID")
    message_id: int = Field(..., description="Message ID containing the video")
    priority: int = Field(default=1, ge=1, le=5, description="Download priority (1=lowest, 5=highest)")

class ForwardRequest(BaseModel):
    from_chat_id: int
    to_chat_id: str
    message_ids: List[int]

class TaskResponse(BaseModel):
    task_id: str
    status: str
    created_at: str
    progress: Optional[float] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
    estimated_completion: Optional[str] = None

# ==========================================================
# 3. 生命周期管理
# ==========================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化工作"""
    try:
        await user.start()
        me = await user.get_me()
        logger.info(f"🚀 Pyrogram client started successfully as '{me.first_name}' (ID: {me.id})")
        
        # 清理过期任务
        await cleanup_expired_tasks()
        
        # 启动定时清理任务
        asyncio.create_task(periodic_cleanup())
        
        logger.info("✅ Backend startup completed successfully.")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理工作"""
    try:
        await user.stop()
        logger.info("🛑 Pyrogram client stopped gracefully.")
        
        # 保存未完成任务状态到文件
        await save_tasks_state()
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# ==========================================================
# 4. 核心工具函数
# ==========================================================

async def cleanup_expired_tasks():
    """清理过期的任务"""
    current_time = time.time()
    expired_tasks = []
    
    for task_id, task_info in DOWNLOAD_TASKS.items():
        # 任务超过1小时未完成则标记为过期
        if current_time - task_info.get('created_at', 0) > 3600:
            expired_tasks.append(task_id)
    
    for task_id in expired_tasks:
        DOWNLOAD_TASKS[task_id]['status'] = TaskStatus.EXPIRED
        logger.warning(f"⏰ Task {task_id} marked as expired")

async def periodic_cleanup():
    """定期清理任务"""
    while True:
        try:
            await cleanup_expired_tasks()
            await asyncio.sleep(300)  # 每5分钟清理一次
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")
            await asyncio.sleep(60)

async def save_tasks_state():
    """保存任务状态到文件"""
    try:
        import json
        state_file = LOG_DIR / "tasks_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(DOWNLOAD_TASKS, f, indent=2, ensure_ascii=False)
        logger.info(f"Tasks state saved to {state_file}")
    except Exception as e:
        logger.error(f"Failed to save tasks state: {e}")

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

# ==========================================================
# 5. 核心业务函数
# ==========================================================

async def _fetch_videos_from_channel(
    channel_id: str,
    limit: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict[str, Any]:
    """从频道获取视频列表的核心函数"""
    
    logger.info(f"🔍 Fetching videos from channel '{channel_id}' (limit: {limit})")
    
    try:
        # 尝试解析为整数ID，否则使用字符串用户名
        try:
            chat_id = int(channel_id)
        except ValueError:
            chat_id = channel_id
            
        # 处理日期范围
        utc = datetime.timezone.utc
        start_date = (
            datetime.datetime.fromisoformat(date_from).replace(tzinfo=utc)
            if date_from else datetime.datetime(1970, 1, 1, tzinfo=utc)
        )
        end_date = (
            (datetime.datetime.fromisoformat(date_to) + datetime.timedelta(days=1)).replace(tzinfo=utc)
            if date_to else datetime.datetime.now(utc)
        )
        
        video_list = []
        processed_count = 0
        
        # 获取消息历史
        async for message in user.get_chat_history(chat_id, limit=limit):
            processed_count += 1
            
            if processed_count % 100 == 0:
                logger.info(f"📊 Processed {processed_count} messages, found {len(video_list)} videos")
            
            msg_date = message.date.replace(tzinfo=utc)
            
            # 如果消息早于开始日期，停止搜索
            if msg_date < start_date:
                logger.info(f"⏹️ Reached start date limit, stopping search")
                break
            
            # 检查是否为视频且在日期范围内
            if message.video and start_date <= msg_date < end_date:
                video_obj = message.video
                
                # 安全地获取视频属性
                file_name = getattr(video_obj, 'file_name', f"video_{message.id}.mp4")
                file_size = getattr(video_obj, 'file_size', 0)
                duration = getattr(video_obj, 'duration', 0)
                minutes, seconds = divmod(int(duration), 60) if duration else (0, 0)
                video_info = {
                    "message_id": message.id,
                    "chat_id": message.chat.id,
                    "file_name": file_name,
                    "file_size_bytes": file_size,
                    "file_size_formatted": format_file_size(file_size),
                    "duration_seconds": duration,
                    "duration_formatted": f"{minutes}:{seconds:02d}" 
                    if duration 
                        else "Unknown",
                    "date": msg_date.isoformat(),
                    "date_formatted": msg_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "link": message.link,
                    "caption": message.caption or "",
                    "has_thumbnail": hasattr(video_obj, 'thumbnail') and video_obj.thumbnail is not None
                }
                
                video_list.append(video_info)
        
        logger.info(f"✅ Successfully found {len(video_list)} videos from {processed_count} messages")
        
        return {
            "videos": video_list,
            "total_found": len(video_list),
            "messages_processed": processed_count,
            "date_range": {
                "from": start_date.isoformat(),
                "to": end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching videos from channel '{channel_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch videos: {str(e)}")

async def _process_download_task(task_id: str, chat_id: int, message_id: int):
    """后台下载任务的核心处理函数"""
    
    task_start_time = time.time()
    logger.info(f"🔄 [Task {task_id}] Starting download for message {message_id} from chat {chat_id}")
    
    try:
        # 更新任务状态为处理中
        DOWNLOAD_TASKS[task_id].update({
            "status": TaskStatus.PROCESSING,
            "started_at": task_start_time,
            "progress": 0.1
        })
        
        # 获取消息
        logger.debug(f"[Task {task_id}] Fetching message...")
        message = await user.get_messages(chat_id, message_id)
        
        if not message or not message.video:
            raise ValueError("Message not found or does not contain video")
        
        # 获取视频信息
        video = message.video
        file_name = getattr(video, 'file_name', f"video_{chat_id}_{message_id}.mp4")
        file_size = getattr(video, 'file_size', 0)
        
        # 确保文件名安全
        safe_file_name = "".join(c for c in file_name if c.isalnum() or c in "._-").rstrip()
        if not safe_file_name:
            safe_file_name = f"video_{chat_id}_{message_id}.mp4"
        
        file_path = STORAGE_DIR / safe_file_name
        
        # 更新任务信息
        DOWNLOAD_TASKS[task_id].update({
            "progress": 0.2,
            "file_name": safe_file_name,
            "file_size": file_size,
            "file_size_formatted": format_file_size(file_size)
        })
        
        logger.info(f"[Task {task_id}] Downloading '{safe_file_name}' ({format_file_size(file_size)})")
        
        # 下载文件
        await user.download_media(
            message=message,
            file_name=str(file_path),
            progress=lambda current, total: _update_download_progress(task_id, current, total)
        )
        
        # 验证下载完成
        if not file_path.exists():
            raise FileNotFoundError("Downloaded file not found")
        
        actual_size = file_path.stat().st_size
        download_time = time.time() - task_start_time
        
        # 更新任务状态为完成
        DOWNLOAD_TASKS[task_id].update({
            "status": TaskStatus.COMPLETED,
            "progress": 1.0,
            "file_path": str(file_path),
            "actual_file_size": actual_size,
            "download_time": download_time,
            "download_speed": format_file_size(int(actual_size / download_time)) + "/s" if download_time > 0 else "N/A",
            "completed_at": time.time()
        })
        
        logger.info(f"✅ [Task {task_id}] Download completed successfully in {download_time:.2f}s")
        logger.info(f"📁 File saved: {file_path} ({format_file_size(actual_size)})")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ [Task {task_id}] Download failed: {error_msg}", exc_info=True)
        
        # 更新任务状态为失败
        DOWNLOAD_TASKS[task_id].update({
            "status": TaskStatus.FAILED,
            "error": error_msg,
            "failed_at": time.time()
        })

def _update_download_progress(task_id: str, current: int, total: int):
    """更新下载进度"""
    if task_id in DOWNLOAD_TASKS and total > 0:
        progress = 0.2 + (current / total) * 0.8  # 20% 为准备阶段，80% 为下载阶段
        DOWNLOAD_TASKS[task_id]["progress"] = progress
        
        if current % (total // 10) == 0:  # 每10%记录一次
            logger.debug(f"[Task {task_id}] Progress: {progress:.1%} ({format_file_size(current)}/{format_file_size(total)})")

# ==========================================================
# 6. API 端点
# ==========================================================

@app.get("/")
async def read_root():
    """首页"""
    try:
        return FileResponse(os.path.join("web", "index.html"))
    except FileNotFoundError:
        return {"message": "Telegram Media Backend v3.0", "status": "running"}

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    try:
        me = await user.get_me()
        return {
            "status": "healthy",
            "version": "3.0.0",
            "user": f"{me.first_name} ({me.id})",
            "active_tasks": len([t for t in DOWNLOAD_TASKS.values() if t["status"] == TaskStatus.PROCESSING]),
            "total_tasks": len(DOWNLOAD_TASKS)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# --- 下载相关API ---

@app.post("/api/download/request", response_model=TaskResponse)
async def request_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """提交下载请求"""
    
    logger.info(f"📥 Received download request: chat_id={request.chat_id}, message_id={request.message_id}")
    
    try:
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        current_time = time.time()
        
        # 初始化任务状态
        task_info = {
            "status": TaskStatus.PENDING,
            "created_at": current_time,
            "chat_id": request.chat_id,
            "message_id": request.message_id,
            "priority": request.priority,
            "progress": 0.0,
            "file_path": None,
            "error": None
        }
        
        DOWNLOAD_TASKS[task_id] = task_info
        
        # 添加后台任务
        background_tasks.add_task(
            _process_download_task,
            task_id,
            request.chat_id,
            request.message_id
        )
        
        logger.info(f"✅ Download task created with ID: {task_id}")
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.datetime.fromtimestamp(current_time).isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create download task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create download task: {str(e)}")

@app.get("/api/download/status/{task_id}", response_model=TaskResponse)
async def get_download_status(task_id: str):
    """查询下载任务状态"""
    
    task = DOWNLOAD_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        created_at=datetime.datetime.fromtimestamp(task["created_at"]).isoformat(),
        progress=task.get("progress"),
        file_path=task.get("file_path"),
        file_size=task.get("actual_file_size"),
        error=task.get("error")
    )

@app.get("/api/download/fetch/{task_id}")
async def fetch_downloaded_file(task_id: str):
    """提取已下载的文件"""
    
    task = DOWNLOAD_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"File not ready. Current status: {task['status']}"
        )
    
    file_path = Path(task.get("file_path"))


    # 1. 在提供服务前，进行最终的、严格的文件验证
    if not file_path or not file_path.is_file() or file_path.stat().st_size == 0:
        logger.error(f"Attempted to serve an invalid file for task {task_id}: {file_path}")
        # 如果文件无效，将任务状态更新为失败
        task["status"] = TaskStatus.FAILED
        task["error"] = "Downloaded file is invalid or empty on the server."
        raise HTTPException(status_code=500, detail="Downloaded file is invalid. Please try again.")
        
    logger.info(f"📤 Preparing to stream file: {file_path.name} ({format_file_size(file_path.stat().st_size)})")

    # 2. 定义一个文件迭代器生成器，这可以防止内存溢出
    def file_iterator(path: Path, chunk_size: int = 8192):
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    # 3. 使用 StreamingResponse 进行响应
    # 这种方式对大文件非常友好，且能更好地处理与客户端的连接
    return StreamingResponse(
        file_iterator(file_path),
        media_type='application/octet-stream',
        headers={

            'Content-Length': str(file_path.stat().st_size),
            'Content-Disposition': f'attachment; filename="{file_path.name}"'
        }
    )

@app.get("/api/download/tasks")
async def list_download_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """列出下载任务"""
    
    tasks = []
    for task_id, task_info in list(DOWNLOAD_TASKS.items())[offset:offset+limit]:
        if status is None or task_info["status"] == status:
            task_response = TaskResponse(
                task_id=task_id,
                status=task_info["status"],
                created_at=datetime.datetime.fromtimestamp(task_info["created_at"]).isoformat(),
                progress=task_info.get("progress"),
                file_path=task_info.get("file_path"),
                file_size=task_info.get("actual_file_size"),
                error=task_info.get("error")
            )
            tasks.append(task_response)
    
    return {
        "tasks": tasks,
        "total": len(DOWNLOAD_TASKS),
        "filtered": len(tasks)
    }

# --- 缩略图API ---

@app.get("/api/thumbnail/{chat_id}/{message_id}")
async def get_thumbnail(chat_id: int, message_id: int):
    """获取视频缩略图"""
    
    logger.debug(f"🖼️ Thumbnail request for message {message_id} from chat {chat_id}")
    
    try:
        message = await user.get_messages(chat_id, message_id)
        
        if not message or not message.video or not message.video.thumbnail:
            # 返回默认占位图
            placeholder_path = Path("web") / "placeholder.png"
            if placeholder_path.exists():
                return FileResponse(str(placeholder_path))
            else:
                raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        # 生成临时缩略图文件名
        temp_thumb_path = TEMP_DIR / f"thumb_{chat_id}_{message_id}_{int(time.time())}.jpg"
        
        # 下载缩略图
        await user.download_media(
            message.video.thumbnail,
            file_name=str(temp_thumb_path)
        )
        
        return FileResponse(
            path=str(temp_thumb_path),
            media_type="image/jpeg",
            background=lambda: temp_thumb_path.unlink(missing_ok=True)
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get thumbnail for message {message_id}: {e}")
        # 尝试返回占位图
        placeholder_path = Path("web") / "placeholder.png"
        if placeholder_path.exists():
            return FileResponse(str(placeholder_path))
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get thumbnail: {str(e)}")

# --- 视频列表API ---

@app.get("/api/channel/{channel_id}/")
async def get_all_videos(channel_id: str, limit: int = 10000):
    """获取频道所有视频"""
    return await _fetch_videos_from_channel(channel_id=channel_id, limit=limit)

@app.get("/api/channel/{channel_id}/videos")
async def get_videos_by_date(
    channel_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 2000
):
    """按日期范围获取视频"""
    return await _fetch_videos_from_channel(
        channel_id=channel_id,
        limit=limit,
        date_from=date_from,
        date_to=date_to
    )

# --- 转发API ---

@app.post("/api/forward")
async def forward_media(request: ForwardRequest):
    """转发媒体消息"""
    
    logger.info(f"📤 Forward request: {len(request.message_ids)} messages from {request.from_chat_id} to {request.to_chat_id}")
    
    try:
        await user.forward_messages(
            chat_id=request.to_chat_id,
            from_chat_id=request.from_chat_id,
            message_ids=request.message_ids
        )
        
        logger.info(f"✅ Successfully forwarded {len(request.message_ids)} messages")
        return {"status": "success", "forwarded_count": len(request.message_ids)}
        
    except Exception as e:
        logger.error(f"❌ Forward failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forward failed: {str(e)}")

# --- 静态文件服务 ---

# 挂载静态文件目录
if Path("web").exists():
    app.mount("/web", StaticFiles(directory="web"), name="web")

# ==========================================================
# 7. 异常处理中间件
# ==========================================================

@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """全局错误处理中间件"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"❌ Unhandled error for {request.method} {request.url}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

# ==========================================================
# 8. 程序入口点
# ==========================================================

if __name__ == "__main__":
    logger.info("🚀 Starting Telegram Media Backend v3.0...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )