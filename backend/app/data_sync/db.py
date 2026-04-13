from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, List, Dict, Any

import pymysql

from .config import SourceDBConfig


def connect_source_db(config: SourceDBConfig):
    conn = pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        charset=config.charset,
        connect_timeout=config.connect_timeout_seconds,
        read_timeout=config.read_timeout_seconds,
        write_timeout=config.write_timeout_seconds,
        cursorclass=pymysql.cursors.DictCursor,
    )
    with conn.cursor() as cur:
        try:
            cur.execute("SET SESSION TRANSACTION READ ONLY")
        except Exception:
            # Some mysql variants do not allow toggling this at session level.
            pass
    return conn


@contextmanager
def source_db_cursor(config: SourceDBConfig) -> Iterator[pymysql.cursors.DictCursor]:
    conn = connect_source_db(config)
    try:
        with conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


def fetch_account_pool(conn) -> List[Dict[str, Any]]:
    pool: List[Dict[str, Any]] = []
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              'ums_admin' AS source,
              CAST(a.id AS CHAR) AS account_id,
              a.id AS admin_id,
              a.username,
              a.full_name AS full_name,
              a.full_name AS nickname,
              a.phone_num AS mobile,
              NULL AS feishu_id,
              a.email,
              r.name AS role_name,
              a.company_id,
              c.company_name
            FROM btyc.ums_admin a
            LEFT JOIN btyc.ums_role r ON r.id = a.role_id
            LEFT JOIN btyc.ums_company c ON c.id = a.company_id
            """
        )
        pool.extend(cur.fetchall())

        cur.execute(
            """
            SELECT
              'auth_user' AS source,
              CAST(u.id AS CHAR) AS account_id,
              NULL AS admin_id,
              u.username,
              NULL AS full_name,
              u.nickname,
              u.mobile,
              u.feishu_id,
              u.email,
              GROUP_CONCAT(DISTINCT r.name ORDER BY r.name SEPARATOR '; ') AS role_name,
              NULL AS company_id,
              NULL AS company_name
            FROM btyc.auth_user u
            LEFT JOIN btyc.auth_user_role_rel ur ON ur.user_id = u.id
            LEFT JOIN btyc.auth_role r ON r.id = ur.role_id
            GROUP BY u.id, u.username, u.nickname, u.mobile, u.feishu_id, u.email
            """
        )
        pool.extend(cur.fetchall())
    return pool

