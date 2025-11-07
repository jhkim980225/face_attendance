from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection, Result
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Optional
import time

from config import Config

_engine: Engine | None = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            Config.sqlalchemy_url(),
            poolclass=QueuePool,
            pool_size=Config.MYSQL_POOL_SIZE,
            max_overflow=Config.MYSQL_MAX_OVERFLOW,
            pool_pre_ping=True,          # 끊긴 커넥션 자동 복구
            pool_recycle=1800,           # 30분마다 재생성 (idle timeout 회피)
            isolation_level="AUTOCOMMIT" # 단순 쿼리 편의
        )
    return _engine

@contextmanager
def get_conn() -> Connection:
    conn = get_engine().connect()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """
    앱 기동 시 테이블 존재여부만 보수적으로 보정.
    (실제 스키마 생성은 제공된 DDL 먼저 실행 권장)
    """
    users_sql = """
    CREATE TABLE IF NOT EXISTS users (
      user_id    VARCHAR(128) NOT NULL,
      created_at BIGINT NOT NULL,
      PRIMARY KEY (user_id),
      KEY idx_users_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    samples_sql = """
    CREATE TABLE IF NOT EXISTS samples (
      sample_id     VARCHAR(64) NOT NULL,
      user_id       VARCHAR(128) NOT NULL,
      image_path    VARCHAR(512) NOT NULL,
      encoding_path VARCHAR(512) NOT NULL,
      created_at    BIGINT NOT NULL,
      PRIMARY KEY (sample_id),
      KEY idx_samples_user_id (user_id),
      KEY idx_samples_created_at (created_at),
      CONSTRAINT fk_samples_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    with get_conn() as conn:
        conn.execute(text(users_sql))
        conn.execute(text(samples_sql))

"""사용자 존재 보장(없으면 생성) """
def ensure_user(user_id: str):
    ts = int(time.time())
    sql = "INSERT IGNORE INTO users(user_id, created_at) VALUES (:uid, :ts)"
    with get_conn() as conn:
        conn.execute(text(sql), {"uid": user_id, "ts": ts})


def insert_capture(capture_id: str, name: Optional[str], image_path: str,
                   encoding_path: Optional[str], captured_at: int):
    sql = """
    INSERT INTO face_captures(capture_id, name, image_path, encoding_path, captured_at)
    VALUES (:cid, :name, :img, :enc, :ts)
    """
    with get_conn() as conn:
        conn.execute(text(sql), {"cid": capture_id, "name": name, "img": image_path,
                                 "enc": encoding_path, "ts": captured_at})

def list_all_encoding_paths() -> list[str]:
    sql = "SELECT encoding_path FROM face_captures WHERE encoding_path IS NOT NULL"
    with get_conn() as conn:
        return [r[0] for r in conn.execute(text(sql)).fetchall()]


def list_user_encoding_paths(user_id: str) -> list[str]:
    sql = "SELECT encoding_path FROM samples WHERE user_id=:uid"
    with get_conn() as conn:
        rows: Result = conn.execute(text(sql), {"uid": user_id})
        return [r[0] for r in rows.fetchall()]


def delete_user_all(user_id: str) -> list[tuple[str, str]]:
    """
    삭제 전 파일 경로 반환(이미지/임베딩 파일 실제 삭제는 서비스 레이어에서 처리)
    """
    sel = "SELECT image_path, encoding_path FROM samples WHERE user_id=:uid"
    with get_conn() as conn:
        paths = conn.execute(text(sel), {"uid": user_id}).fetchall()

    with get_conn() as conn:
        conn.execute(text("DELETE FROM samples WHERE user_id=:uid"), {"uid": user_id})
        conn.execute(text("DELETE FROM users WHERE user_id=:uid"), {"uid": user_id})

    return [(p[0], p[1]) for p in paths]

def list_users_with_counts():
    sql = """
    SELECT u.user_id, COUNT(s.sample_id) AS samples, u.created_at
    FROM users u
    LEFT JOIN samples s ON s.user_id = u.user_id
    GROUP BY u.user_id
    ORDER BY u.created_at ASC
    """
    with get_conn() as conn:
        rows: Result = conn.execute(text(sql))
        return [dict(rows=m._mapping) if hasattr(m, "_mapping") else dict(user_id=m[0], samples=m[1], created_at=m[2]) for m in rows]






def get_all_registered_users() -> list[tuple[str, str]]:
    """
    등록된 모든 사용자 이름(name)과 인코딩 경로(encoding_path) 목록 반환
    """
    sql = """
    SELECT name, encoding_path 
    FROM face_captures
    WHERE encoding_path IS NOT NULL
    """
    with get_conn() as conn:
        rows: Result = conn.execute(text(sql))
        return [(r[0], r[1]) for r in rows.fetchall()]