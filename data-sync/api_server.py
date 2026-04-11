#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data_sync.config import resolve_source_db_config
from data_sync.db import connect_source_db, fetch_account_pool
from data_sync.engineers import select_engineers
from data_sync.mapper import export_mapping_result, now_stamp, run_engineer_mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = PROJECT_ROOT / "exports"

app = FastAPI(title="DateUse data-sync", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MapAdminIdsRequest(BaseModel):
    all: bool = True
    engineers: List[str] = Field(default_factory=list)


def _run_mapping(all_engineers: bool, engineers: List[str]):
    config = resolve_source_db_config(project_root=PROJECT_ROOT)
    selected = select_engineers(None if all_engineers or not engineers else engineers)
    if not selected:
        raise HTTPException(status_code=404, detail="No engineer matched input names.")

    conn = connect_source_db(config)
    try:
        pool = fetch_account_pool(conn)
        result = run_engineer_mapping(engineers=selected, pool=pool, conn=conn)
    finally:
        conn.close()

    stamp = now_stamp()
    files = export_mapping_result(result=result, output_dir=EXPORT_DIR, stamp=stamp)
    return {
        "summary": result.get("summary", {}),
        "files": files,
        "rows": result.get("rows", []),
    }


@app.get("/")
def root():
    return {
        "name": "DateUse data-sync",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "dateuse-data-sync"}


@app.get("/api/map-admin-ids")
def map_admin_ids_get(
    all: bool = True,
    engineer: List[str] = Query(default_factory=list),
):
    return _run_mapping(all_engineers=all, engineers=engineer)


@app.post("/api/map-admin-ids")
def map_admin_ids_post(payload: MapAdminIdsRequest):
    return _run_mapping(all_engineers=payload.all, engineers=payload.engineers)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, app_dir=str(Path(__file__).resolve().parent))
