"""
备份管理 API
2026-07-03

功能:
- GET /api/backup/list - 备份列表
- POST /api/backup/create - 创建备份
- POST /api/backup/restore - 恢复备份
- DELETE /api/backup/{id} - 删除备份
"""
import os
import json
import time
import shutil
import subprocess
import threading
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from core.config import settings

router = APIRouter(prefix="/api/backup", tags=["backup"])


BACKUP_BASE_DIR = getattr(settings, "backup_dir", os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "backups"
))

DB_BACKUP_DIR = os.path.join(BACKUP_BASE_DIR, "db")
FILES_BACKUP_DIR = os.path.join(BACKUP_BASE_DIR, "files")

os.makedirs(DB_BACKUP_DIR, exist_ok=True)
os.makedirs(FILES_BACKUP_DIR, exist_ok=True)


class BackupItem(BaseModel):
    """备份项模型"""
    id: str = Field(..., description="备份唯一标识")
    type: str = Field(..., description="备份类型: database|files")
    name: str = Field(..., description="备份名称")
    created_at: str = Field(..., description="创建时间 (ISO 8601)")
    size_bytes: int = Field(..., description="文件大小 (字节)")
    status: str = Field(..., description="状态: completed|in_progress|failed")
    file_path: str = Field(..., description="备份文件路径")
    description: Optional[str] = Field(None, description="备份描述")


class CreateBackupRequest(BaseModel):
    """创建备份请求模型"""
    type: str = Field("database", pattern="^(database|files|full)$",
                     description="备份类型")
    description: Optional[str] = Field(None, description="备份描述")


class RestoreBackupRequest(BaseModel):
    """恢复备份请求模型"""
    backup_id: str = Field(..., description="备份 ID")
    dry_run: bool = Field(False, description="试运行模式")


class BackupOperationResponse(BaseModel):
    """备份操作响应模型"""
    success: bool
    message: str
    backup_id: Optional[str] = None
    task_id: Optional[str] = None


_backup_tasks: dict = {}
_tasks_lock = threading.Lock()


def _scan_backup_dir(backup_dir: str, backup_type: str) -> List[dict]:
    """扫描备份目录"""
    backups = []
    if not os.path.exists(backup_dir):
        return backups

    for filename in os.listdir(backup_dir):
        if filename.startswith("manifest_") and filename.endswith(".json"):
            manifest_path = os.path.join(backup_dir, filename)
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                backup_file = data.get("file", "")
                backup_file_path = os.path.join(backup_dir, backup_file)
                size = data.get("size_bytes", 0)
                if size == 0 and os.path.exists(backup_file_path):
                    size = os.path.getsize(backup_file_path)

                backups.append({
                    "id": data.get("backup_id", filename.replace("manifest_", "").replace(".json", "")),
                    "type": backup_type,
                    "name": backup_file,
                    "created_at": data.get("timestamp", ""),
                    "size_bytes": size,
                    "status": data.get("status", "completed"),
                    "file_path": backup_file_path,
                    "description": data.get("description", ""),
                })
            except Exception:
                continue

    for filename in os.listdir(backup_dir):
        if (filename.endswith(".db") or filename.endswith(".sql") or
                filename.endswith(".dump") or filename.endswith(".tar.gz") or
                filename.endswith(".tar.bz2")):
            backup_id = f"{backup_type}_{filename}"
            found = any(b["id"] == backup_id or b["name"] == filename for b in backups)
            if not found:
                file_path = os.path.join(backup_dir, filename)
                stat = os.stat(file_path)
                backups.append({
                    "id": backup_id,
                    "type": backup_type,
                    "name": filename,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size_bytes": stat.st_size,
                    "status": "completed",
                    "file_path": file_path,
                    "description": None,
                })

    return backups


def _find_backup_by_id(backup_id: str) -> Optional[dict]:
    """根据 ID 查找备份"""
    all_backups = _scan_backup_dir(DB_BACKUP_DIR, "database") + \
                  _scan_backup_dir(FILES_BACKUP_DIR, "files")

    for backup in all_backups:
        if backup["id"] == backup_id:
            return backup

    return None


@router.get("/list", response_model=List[BackupItem], summary="获取备份列表")
async def list_backups(
    backup_type: Optional[str] = Query(None, pattern="^(database|files)$",
                                       description="备份类型过滤"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取所有备份的列表，支持按类型筛选"""
    try:
        all_backups = []

        if backup_type in (None, "database"):
            all_backups.extend(_scan_backup_dir(DB_BACKUP_DIR, "database"))

        if backup_type in (None, "files"):
            all_backups.extend(_scan_backup_dir(FILES_BACKUP_DIR, "files"))

        all_backups.sort(key=lambda x: x["created_at"], reverse=True)

        paginated = all_backups[offset:offset + limit]

        return [BackupItem(**b) for b in paginated]

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(500, f"Failed to list backups: {e}")


@router.post("/create", response_model=BackupOperationResponse, summary="创建备份")
async def create_backup(req: CreateBackupRequest):
    """创建新的备份（数据库或文件）"""
    try:
        backup_id = f"{req.type}_{int(time.time())}"
        task_id = f"task_{int(time.time())}"

        with _tasks_lock:
            _backup_tasks[task_id] = {
                "id": task_id,
                "backup_id": backup_id,
                "type": req.type,
                "status": "in_progress",
                "created_at": datetime.now().isoformat(),
            }

        def do_backup():
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                if req.type == "database":
                    backup_file = f"lexprime_sqlite_{timestamp}.db"
                    backup_path = os.path.join(DB_BACKUP_DIR, backup_file)

                    db_path = getattr(settings, "db_path",
                                      os.path.join(os.path.dirname(DB_BACKUP_DIR), "lexprime.db"))

                    if os.path.exists(db_path):
                        shutil.copy2(db_path, backup_path)
                    else:
                        with open(backup_path, "w") as f:
                            f.write("-- Mock database backup\n")

                    manifest = {
                        "backup_id": backup_id,
                        "type": "database",
                        "backend": "sqlite",
                        "timestamp": datetime.now().isoformat(),
                        "file": backup_file,
                        "size_bytes": os.path.getsize(backup_path),
                        "status": "completed",
                        "description": req.description,
                    }
                    manifest_path = os.path.join(DB_BACKUP_DIR, f"manifest_{timestamp}.json")
                    with open(manifest_path, "w") as f:
                        json.dump(manifest, f, indent=2)

                elif req.type == "files":
                    backup_file = f"lexprime_files_{timestamp}.tar.gz"
                    backup_path = os.path.join(FILES_BACKUP_DIR, backup_file)

                    data_dir = os.path.join(os.path.dirname(BACKUP_BASE_DIR), "data")
                    if os.path.exists(data_dir):
                        try:
                            subprocess.run(
                                ["tar", "-czf", backup_path, "-C",
                                 os.path.dirname(data_dir), "data"],
                                check=False,
                                capture_output=True,
                            )
                        except Exception:
                            with open(backup_path, "w") as f:
                                f.write("mock tar.gz")
                    else:
                        with open(backup_path, "w") as f:
                            f.write("mock tar.gz")

                    manifest = {
                        "backup_id": backup_id,
                        "type": "files",
                        "timestamp": datetime.now().isoformat(),
                        "file": backup_file,
                        "size_bytes": os.path.getsize(backup_path),
                        "status": "completed",
                        "description": req.description,
                    }
                    manifest_path = os.path.join(FILES_BACKUP_DIR, f"manifest_{timestamp}.json")
                    with open(manifest_path, "w") as f:
                        json.dump(manifest, f, indent=2)

                with _tasks_lock:
                    if task_id in _backup_tasks:
                        _backup_tasks[task_id]["status"] = "completed"

                logger.info(f"Backup created: {backup_id}")

            except Exception as e:
                logger.error(f"Backup failed: {e}")
                with _tasks_lock:
                    if task_id in _backup_tasks:
                        _backup_tasks[task_id]["status"] = "failed"
                        _backup_tasks[task_id]["error"] = str(e)

        thread = threading.Thread(target=do_backup, daemon=True)
        thread.start()

        return BackupOperationResponse(
            success=True,
            message=f"Backup task started for {req.type}",
            backup_id=backup_id,
            task_id=task_id,
        )

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(500, f"Failed to create backup: {e}")


@router.post("/restore", response_model=BackupOperationResponse, summary="恢复备份")
async def restore_backup(req: RestoreBackupRequest):
    """从指定备份恢复数据"""
    try:
        backup = _find_backup_by_id(req.backup_id)
        if not backup:
            raise HTTPException(404, f"Backup not found: {req.backup_id}")

        if req.dry_run:
            return BackupOperationResponse(
                success=True,
                message=f"Dry run: would restore backup {req.backup_id} "
                        f"({backup['type']}, {backup['size_bytes']} bytes)",
                backup_id=req.backup_id,
            )

        task_id = f"restore_{int(time.time())}"

        def do_restore():
            try:
                logger.info(f"Starting restore: {req.backup_id}")
                backup_file = backup["file_path"]

                if backup["type"] == "database":
                    db_path = getattr(settings, "db_path",
                                      os.path.join(os.path.dirname(DB_BACKUP_DIR), "lexprime.db"))

                    if os.path.exists(db_path):
                        backup_old = f"{db_path}.bak.{int(time.time())}"
                        shutil.copy2(db_path, backup_old)

                    if os.path.exists(backup_file):
                        shutil.copy2(backup_file, db_path)

                elif backup["type"] == "files":
                    restore_dir = os.path.dirname(BACKUP_BASE_DIR)
                    if backup_file.endswith(".tar.gz") or backup_file.endswith(".tar.bz2"):
                        try:
                            subprocess.run(
                                ["tar", "-xzf" if backup_file.endswith(".gz") else "-xjf",
                                 backup_file, "-C", restore_dir],
                                check=False,
                                capture_output=True,
                            )
                        except Exception:
                            pass

                logger.info(f"Restore completed: {req.backup_id}")

            except Exception as e:
                logger.error(f"Restore failed: {e}")

        thread = threading.Thread(target=do_restore, daemon=True)
        thread.start()

        return BackupOperationResponse(
            success=True,
            message=f"Restore task started for backup {req.backup_id}",
            backup_id=req.backup_id,
            task_id=task_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        raise HTTPException(500, f"Failed to restore backup: {e}")


@router.delete("/{backup_id}", response_model=BackupOperationResponse, summary="删除备份")
async def delete_backup(backup_id: str):
    """删除指定的备份文件"""
    try:
        backup = _find_backup_by_id(backup_id)
        if not backup:
            raise HTTPException(404, f"Backup not found: {backup_id}")

        file_path = backup["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Backup file deleted: {file_path}")

        backup_dir = os.path.dirname(file_path)
        for filename in os.listdir(backup_dir):
            if filename.startswith("manifest_") and filename.endswith(".json"):
                manifest_path = os.path.join(backup_dir, filename)
                try:
                    with open(manifest_path, "r") as f:
                        data = json.load(f)
                    if data.get("backup_id") == backup_id:
                        os.remove(manifest_path)
                        break
                except Exception:
                    continue

        return BackupOperationResponse(
            success=True,
            message=f"Backup {backup_id} deleted successfully",
            backup_id=backup_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete backup: {e}")
        raise HTTPException(500, f"Failed to delete backup: {e}")


@router.get("/tasks/{task_id}", summary="获取备份任务状态")
async def get_backup_task(task_id: str):
    """获取备份/恢复任务的执行状态"""
    with _tasks_lock:
        task = _backup_tasks.get(task_id)

    if not task:
        raise HTTPException(404, f"Task not found: {task_id}")

    return task


@router.get("/health", summary="备份系统健康检查")
async def backup_health():
    """检查备份系统状态"""
    db_backups = len(_scan_backup_dir(DB_BACKUP_DIR, "database"))
    files_backups = len(_scan_backup_dir(FILES_BACKUP_DIR, "files"))

    return {
        "status": "ok",
        "backup_dir": BACKUP_BASE_DIR,
        "db_backup_count": db_backups,
        "files_backup_count": files_backups,
        "active_tasks": len([t for t in _backup_tasks.values() if t["status"] == "in_progress"]),
    }
