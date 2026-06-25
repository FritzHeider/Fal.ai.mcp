"""
SQLite Database Layer with Dynamic Schema Migrations and Async Execution.

Handles job persistence, status updates, metadata storage, and error logging.
Ensures database schema is always up to date using PRAGMA table_info inspection.
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from settings import settings


def _get_connection() -> sqlite3.Connection:
    """Create a SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db_sync() -> None:
    """
    Synchronously initialize the database schema and apply migrations.
    Uses PRAGMA table_info to dynamically add missing columns without data loss.
    """
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with _get_connection() as conn:
        cursor = conn.cursor()

        # Create base table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'QUEUED',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Dynamic column migration check
        cursor.execute("PRAGMA table_info(jobs)")
        existing_cols = [row["name"] for row in cursor.fetchall()]

        # Target columns schema definition
        target_columns: Dict[str, str] = {
            "title": "TEXT",
            "video_path": "TEXT",
            "video_prompt": "TEXT",
            "full_script": "TEXT",
            "description": "TEXT",
            "visual_style": "TEXT",
            "voice_id_override": "TEXT",
            "recap_intro": "TEXT",
            "custom_cliffhanger": "TEXT",
            "target_duration_sec": "INTEGER DEFAULT 60",
            "focus_keyword": "TEXT",
            "niche": "TEXT",
            "target_demographic": "TEXT",
            "voice_tone": "TEXT",
            "model_id": "TEXT",
            "error_log": "TEXT",
            "metadata": "TEXT"  # JSON serialized metadata (visual cues, fal request ID, etc.)
        }

        for col_name, col_type in target_columns.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")

        # Create indices for quick status queries and timestamps
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
        conn.commit()


async def init_db() -> None:
    """Asynchronously initialize the database on application startup."""
    await asyncio.to_thread(init_db_sync)


async def create_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new job record into the database."""
    now = datetime.now(timezone.utc).isoformat()
    job_id = job_data.get("id")
    if not job_id:
        import uuid
        job_id = f"job_{uuid.uuid4().hex[:12]}"

    metadata_str = json.dumps(job_data.get("metadata", {}))

    def _sync_create():
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (
                    id, status, title, video_path, video_prompt, full_script,
                    description, visual_style, voice_id_override, recap_intro,
                    custom_cliffhanger, target_duration_sec, focus_keyword,
                    niche, target_demographic, voice_tone, model_id,
                    error_log, metadata, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
            """, (
                job_id,
                job_data.get("status", "QUEUED"),
                job_data.get("title", "Untitled Production"),
                job_data.get("video_path"),
                job_data.get("video_prompt"),
                job_data.get("full_script"),
                job_data.get("description"),
                job_data.get("visual_style", "Cinematic"),
                job_data.get("voice_id_override"),
                job_data.get("recap_intro"),
                job_data.get("custom_cliffhanger"),
                job_data.get("target_duration_sec", 60),
                job_data.get("focus_keyword"),
                job_data.get("niche"),
                job_data.get("target_demographic"),
                job_data.get("voice_tone"),
                job_data.get("model_id", settings.DEFAULT_MODEL_VIDEO),
                job_data.get("error_log"),
                metadata_str,
                now,
                now
            ))
            conn.commit()

    await asyncio.to_thread(_sync_create)
    return await get_job(job_id) or {}


async def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single job by its ID."""
    def _sync_get():
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            if data.get("metadata"):
                try:
                    data["metadata"] = json.loads(data["metadata"])
                except Exception:
                    data["metadata"] = {}
            return data

    return await asyncio.to_thread(_sync_get)


async def update_job(job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update fields on an existing job record."""
    now = datetime.now(timezone.utc).isoformat()
    updates = dict(updates)
    updates["updated_at"] = now

    if "metadata" in updates and isinstance(updates["metadata"], (dict, list)):
        updates["metadata"] = json.dumps(updates["metadata"])

    fields = [f"{k} = ?" for k in updates.keys()]
    values = list(updates.values()) + [job_id]

    def _sync_update():
        with _get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

    await asyncio.to_thread(_sync_update)
    return await get_job(job_id)


async def list_jobs(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Query jobs with optional status filter, search query, and pagination."""
    def _sync_list():
        with _get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params: List[Any] = []

            if status:
                conditions.append("status = ?")
                params.append(status)

            if search:
                conditions.append("(title LIKE ? OR focus_keyword LIKE ? OR video_prompt LIKE ? OR niche LIKE ?)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param, search_param])

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"SELECT * FROM jobs {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for row in rows:
                data = dict(row)
                if data.get("metadata"):
                    try:
                        data["metadata"] = json.loads(data["metadata"])
                    except Exception:
                        data["metadata"] = {}
                results.append(data)
            return results

    return await asyncio.to_thread(_sync_list)


async def log_job_error(job_id: str, error_message: str, stack_trace: Optional[str] = None) -> None:
    """Log an error message and full stack trace to the job record."""
    combined_log = f"ERROR: {error_message}"
    if stack_trace:
        combined_log += f"\n\nStack Trace:\n{stack_trace}"
    
    await update_job(job_id, {
        "status": "FAILED",
        "error_log": combined_log
    })
