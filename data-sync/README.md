# data-sync Service

DateUse 的 `data-sync` 负责从公司源库只读拉取数据，并做映射/结构化处理。

当前已实现能力：

- 工程师名字 -> `admin_id` 映射
- 映射结果 JSON / CSV 导出
- 映射状态标记（唯一命中、多命中、未命中）

## Quick Start

```bash
cd "/Users/mac/software project/DateUse"
.venv/bin/python app/data-sync/main.py map-admin-ids --all
```

按名字定向查询：

```bash
.venv/bin/python app/data-sync/main.py map-admin-ids --engineer "唐浩宇" --engineer "周杰彪(Jason)"
```

默认输出目录：`exports/`

- `data_sync_engineer_admin_mapping_<timestamp>.json`
- `data_sync_engineer_admin_mapping_summary_<timestamp>.csv`
- `data_sync_engineer_admin_mapping_detail_<timestamp>.csv`

## Docker 运行（DateUse 端口）

- 前端：`http://localhost:8082`
- 后端：`http://localhost:8002`
- 数据库：`localhost:3308`

```bash
cd "/Users/mac/software project/DateUse"
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose up -d
```

健康检查：

```bash
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8082/health
```

## 配置优先级

1. 环境变量（`SOURCE_DB_*` 或 `BT_DB_*`）
2. 项目根目录 `.env`
3. 项目根目录 `dataenv.txt`

支持键：

- `SOURCE_DB_HOST` / `BT_DB_HOST`
- `SOURCE_DB_PORT` / `BT_DB_PORT`
- `SOURCE_DB_USER` / `BT_DB_USER`
- `SOURCE_DB_PASSWORD` / `BT_DB_PASSWORD`
