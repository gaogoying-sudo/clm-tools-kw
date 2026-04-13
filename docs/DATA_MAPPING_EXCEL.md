# Excel 数据映射设计 (DATA_MAPPING)

## 源文件
1. `全球口味工程师调度看板.xlsx`
   - `口味日程安排`: 项目/任务级 (207 行)
   - `口味日报`: 每日工作记录级 (384 行)

## 解析策略

### 1. 工程师信息提取 (Engineers)
从两表的 `口味工程师`, `跟进人`, `创建人` 字段提取去重名单。
- **字段映射**: 
  - Name <- `口味工程师` / `跟进人`
  - Role <- 默认为 "口味工程师" (可根据后续需求补充)
  - Region <- 从 `部门` 或 `国家/地区` 推断 (e.g., "新马" -> 海外)

### 2. 任务数据生成 (Sync Tasks)
**核心逻辑**: 以 `口味日报` 为主轴，每一天一条记录代表一次工作。
- **日期**: 解析 `进展标题` 中的日期 (e.g., `2026-04-06 ...` -> `2026-04-06`) 或 `日期` 列。
- **工程师**: `跟进人`。
- **客户**: `客户（品牌名）` 或从 `进展标题` 提取 (e.g., `...-Oscar Food Mart-...` -> `Oscar Food Mart`)。
- **菜品 (Dish Name)**: 从 `菜品SKU及状态` 列提取 (e.g., `"Fried rice, lomein, tofu"` -> 拆分为 3 条 `sync_tasks`)。
  - *仿真*: 如果该列为空，则生成随机的标准菜谱（如辣椒炒肉）。
- **过程数据 (Mock)**:
  - 功率轨迹/投料时序: 暂时使用随机生成的标准数据 (因为 Excel 没有这么细)。
  - 异常标记: 如果 `现场问题` 不为空，标记 `has_abnormal = True`，并将问题文本存入 `modifications`。

### 3. 会话生成 (Daily Sessions)
- 基于生成的 `sync_tasks` 按 (Engineer, Date) 聚合。
- 创建 `daily_sessions`，关联 `session_tasks`。
- **状态模拟**: 
  - 随机分配 `submitted` / `pending`。
  - 如果分配 `submitted`，随机生成几条 `answers` (基于问题模板)。

## 实施步骤
1. 清洗 Excel，构建 Engineer 列表并入库。
2. 遍历 Excel Rows -> 生成 Tasks -> 入库。
3. 生成 Sessions -> 入库。
4. 验证数据完整性。
