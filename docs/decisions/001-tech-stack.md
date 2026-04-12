# 001. 技术选型

**日期：** 2026-04-12  
**状态：** 已采纳

## 背景
整合 CLM-Tools + DateUse 两套代码，需要统一技术栈。

## 决策
| 层 | 技术 | 理由 |
|----|------|------|
| 后端 | FastAPI + SQLAlchemy | 已有完整模型(7张表)，迁移成本高 |
| 前端 | React + Vite → 升级 TailwindCSS | 当前内联样式1200行难以维护 |
| 数据库 | MySQL 8.0 | 云环境已有 |
| 任务调度 | APScheduler | 简单够用 |
| 数据同步 | DateUse pymysql 逻辑 | 保留工程师映射代码 |

## 影响
- 前端需要逐步从内联样式迁移到 TailwindCSS（不阻塞功能开发）
- SQLAlchemy 确保使用 2.0 语法
- 其他层保持现状
