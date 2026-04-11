# ENGINEER_DB_DISCOVERY_v1

- 生成时间: 2026-03-26T22:27:01
- 数据源: `btyc`, `btyc_statics`, `dev_btyc`, `manage_backend`, `schedule`, `schedule2`
- 访问方式: 只读 SQL 探索（未执行任何写入）
- 本轮目标: 验证“口味工程师 -> 客户/门店 -> 设备 -> 菜谱/执行数据”是否存在最小可行链路

## 0. 主问题结论（本轮）

- 结论: **可以部分成立**。已验证 3 位工程师存在可追踪链路，能定位到门店/设备，并关联到菜谱与烹饪执行日志。
- 但目前“本人当日亲自操作”仍是间接证据（通过配方归属 + 会话 + 设备日志），未在执行日志中直接看到明确的人名字段命中。

## 1. 名单匹配结果

- 名单总数: `36`
- 已命中工程师: `15`
- 未命中工程师: `21`
- 命中来源: `btyc.auth_user` + `btyc.ums_admin`（严格匹配为主，少量英文别名模糊）

### 1.1 命中记录明细

| engineer_name | confidence | source | user_id | username | nickname/full_name | mobile | feishu_id | role_name | company_id | company_name |
|---|---|---|---:|---|---|---|---|---|---:|---|
| Kevin Hartley | high | btyc.ums_admin | 2823 | 11111111 | Kevin hartley | 11111111 | - | 超级管理员 | - | - |
| 付强(Fonzie) | high | btyc.auth_user | 231983902788368 | fuq@botinkit.com | 付强 | +8618610966960 | 6bc278bd | 管理员 | - | - |
| 刘兰强 | high | btyc.ums_admin | 1747 | +8617600592298 | 刘兰强 | 17600592298 | - | 运营管理员 | 1992 | 上海日月光店 |
| 卢明辉 | high | btyc.auth_user | 232596516346640 | - | 卢明辉 | +8615892868631 | ddb3374e | 售后 | - | - |
| 周杰彪(Jason) | medium | btyc.ums_admin | 1286 | +8617707408153 | Jason Yang | 17707408153 | - | 普通成员 | - | - |
| 周杰彪(Jason) | medium | btyc.ums_admin | 1591 | +17074959035 | Jason Do | 7074959035 | - | 普通成员 | - | - |
| 周杰彪(Jason) | medium | btyc.ums_admin | 988 | +610425396668 | okami jason | 0425396668 | - | 运营管理员 | 1246 | Okami head office Okami Footscray |
| 唐浩宇 | high | btyc.auth_user | 234332471946000 | tanghy@botinkit.com | 唐浩宇 | +8615989160017 | 19ff8ef6 | 售后 | - | - |
| 唐浩宇 | high | btyc.ums_admin | 699 | 唐浩宇 | - | - | - | - | - | - |
| 尹龙强 | high | btyc.auth_user | 252461957630736 | - | 尹龙强 | +8613008606986 | ec8bc241 | 口味 | - | - |
| 尹龙强 | high | btyc.ums_admin | 2236 | +8613008606986 | 尹龙强 | 13008606986 | - | 运营管理员 | 2004 | 绿茶金华万达广场店 |
| 张海 | medium | btyc.auth_user | 301574856070000 | zhanghd@botinkit.com | 张海东 | +8613145550004 | e6b65d1f | 普通 | - | - |
| 李彦彪(REX) | high | btyc.ums_admin | 1543 | WTCE_REX | REX | 00120240829 | - | 运营管理员 | 548 | Showroom-UK |
| 王野 | high | btyc.auth_user | 252203223747344 | - | 王野 | +8618926096293 | g9d5f722 | 口味 | - | - |
| 罗刚 | high | btyc.auth_user | 249672767929104 | - | 罗刚 | +8613418665658 | a2c7b924 | 口味 | - | - |
| 胡光中 | high | btyc.auth_user | 232276321221392 | - | 胡光中 | +8615914250390 | efa2gec4 | 售后 | - | - |
| 许宝华 | high | btyc.ums_admin | 1377 | 17850821964 | 许宝华 | 17850821964 | - | 超级管理员 | - | - |
| 许宝华 | high | btyc.ums_admin | 1542 | +8615200588863 | 许宝华 | 15200588863 | - | 普通成员 | 3 | 深圳口味实验室 |
| 陈龙 | high | btyc.auth_user | 287481373414256 | - | 陈龙 | +8613713298869 | 2ae71gea | 开发 | - | - |
| 黄俊龙 | high | btyc.ums_admin | 1663 | 13244788672 | 黄俊龙 | 13244788672 | - | 普通成员 | 811 | 佬肥猫七宝宝龙店 |

### 1.2 未命中名单

`江飞`, `冯明`, `周洪亮`, `高豪`, `雷祖壮`, `杨梓锋`, `张连顺`, `周思来(Chef Chow)`, `马志明`, `周华玉`, `周潮凌`, `沈伯腾(Harry Shen)`, `陈尚贤`, `陈镭福(杰哥 Amos Tan)`, `周辰永(Jon)`, `Fami Taufeq Fakarudin`, `戴子扬(Joe)`, `李传灵`, `宗振兴`, `利伟锋(Liam Li)`, `唐清林`

### 1.3 模糊匹配注意点

- `周杰彪(Jason)` 目前命中到 3 条 `btyc.ums_admin`（`Jason Yang/Jason Do/okami jason`），需二次确认手机号或公司。
- `张海` 命中 `张海东`（包含匹配），建议结合手机号或飞书 ID 再确认。

## 2. 人员基础信息导出结论

### 2.1 关键字段（可用于身份映射）

- `btyc.auth_user`: `id`, `username`, `nickname`, `mobile`, `feishu_id`, `email`, `status`
- `btyc.auth_user_role_rel` + `btyc.auth_role`: `user_id -> role_id -> role_name`
- `btyc.ums_admin`: `id`, `username`, `full_name`, `phone_num`, `role_id`, `company_id`
- `btyc.ums_role`: `id`, `name`（角色）
- `btyc.ums_company`: `id`, `company_name`（门店/客户名锚点）

### 2.2 对后续飞书推送/身份映射有价值的字段

- 首选主键: `ums_admin.id`（与 `sop_recipe.create_user/update_user`、`btyc_user_session.user_id` 可直接关联）
- 人员触达: `auth_user.feishu_id`, `auth_user.mobile`, `ums_admin.phone_num`
- 组织锚点: `ums_admin.company_id -> ums_company.company_name`

## 3. 候选关系链（优先级）

1. 已验证: `btyc.ums_admin(id) -> btyc.sop_recipe(create_user/update_user) -> btyc.sop_machinelog(recipe_id,sn,owner) -> btyc.ums_company(id=owner)`
2. 已验证: `btyc.ums_admin(id) -> btyc.btyc_user_session(user_id,machine_code) -> btyc.sop_robot(machinecode,company_id) -> btyc.ums_company`，并可补 `sop_machinelog(sn=machine_code)`
3. 候选: `btyc.auth_user(mobile/昵称/飞书) -> btyc.ums_admin(phone_num/full_name)` 再并入链路 1/2（用于账号体系打通）
4. 候选: `btyc.sop_recipe(id) -> dev_btyc.oms_merchant_recipe_conf(recipe_id,company_id,config)` -> `dev_btyc.oms_merchant_machine_info(company_id,sn,extra_conf)` -> `schedule/schedule2.oms_merchant_cooking_log(company_id,sn,recepid_id)`
5. 候选统计链: `btyc.ums_company(id) -> btyc_statics.store_statistics(company_id)`（用于门店级烹饪规模验证）

## 4. 样例验证（1~3 人）

以下样例来自 `exports/engineer_activity_candidates.csv`。

### 4.1 尹龙强

- 账号定位: `btyc.auth_user` / user_id `252461957630736` / username `-` / mobile `+8613008606986` / role `口味`
- 关联规模概览: recipes≈591, machine_logs≈71218, session(machine_code非空)≈5

| path_type | machine_code/sn | company_id | company_name | recipe_id | recipe_name | 时间 |
|---|---|---:|---|---:|---|---|
| recipe_log_company | 0103202410100087 | 1168 | 绿茶上海浦江万达店 | 104630 | 油渣小白菜1份 | 2026-03-19 11:12:12 |
| recipe_log_company | 0103202410100087 | 1168 | 绿茶上海浦江万达店 | 104630 | 油渣小白菜1份 | 2026-03-19 10:49:00 |
| session_machine_log | 0103202404050011 | 1973 | 绿茶北京平谷万达店 | 0 | 2026-02-11 21:43:45 | 2026-02-11 21:41:52 |
| session_machine_log | 0105222506020103 | 1776 | 绿茶北京房山龙湖店 | 0 | 2026-03-03 18:01:46 | 2026-03-03 17:44:57 |

- 结论: 该工程师已可定位到门店/设备，并关联到菜谱与执行日志。

### 4.2 刘兰强

- 账号定位: `btyc.ums_admin` / user_id `1747` / username `+8617600592298` / mobile `17600592298` / role `运营管理员`
- 关联规模概览: recipes≈75, machine_logs≈17019, session(machine_code非空)≈2

| path_type | machine_code/sn | company_id | company_name | recipe_id | recipe_name | 时间 |
|---|---|---:|---|---:|---|---|
| recipe_log_company | 0104212410150018 | 1020 | 李下饭总店 | 79079 | 茄子豆角刘志成成 | 2026-03-26 20:00:26 |
| recipe_log_company | 0104212410150018 | 1020 | 李下饭总店 | 79079 | 茄子豆角刘志成成 | 2026-03-26 19:41:54 |
| session_machine_log | 0104212410150018 | 1020 | 李下饭总店 | 79426 | 爆炒鱿鱼须刘志成 | 2026-03-26 20:57:11 |
| session_machine_log | 0104212410150001 | 895 | 李下饭辣椒炒肉（研发门店） | 114938 | 酸辣炒鸡 | 2025-08-28 18:44:48 |

- 结论: 该工程师已可定位到门店/设备，并关联到菜谱与执行日志。

### 4.3 许宝华

- 账号定位: `btyc.ums_admin` / user_id `1377` / username `17850821964` / mobile `17850821964` / role `超级管理员`
- 关联规模概览: recipes≈66, machine_logs≈26959, session(machine_code非空)≈2

| path_type | machine_code/sn | company_id | company_name | recipe_id | recipe_name | 时间 |
|---|---|---:|---|---:|---|---|
| recipe_log_company | 0103202409010016 | 805 | 陈记小辣椒 | 57177 | 酸包菜粉皮1份 | 2026-03-26 18:24:23 |
| recipe_log_company | 0103202409010016 | 805 | 陈记小辣椒 | 57177 | 酸包菜粉皮1份 | 2026-03-26 18:04:37 |
| session_machine_log | 0103202406010075 | 1134 | 四道菜 福州东百元洪 | 161573 | 鹿茸菌炒肥肠1份 | 2026-03-26 19:15:47 |
| session_machine_log | 0103202406010077 | 1052 | 四道菜 福州中骏世界城店 | 0 | 2026-03-26 20:22:32 | 2026-03-26 20:21:26 |

- 结论: 该工程师已可定位到门店/设备，并关联到菜谱与执行日志。

## 5. JSON / config / result 字段抽样

| 表 | 字段 | 样例摘要 |
|---|---|---|
| `btyc.machine_execution_record_log` | `execution_status_trace` | `client not connected to server`（执行状态追踪文本） |
| `btyc.sop_curve_record` | `cook_curve` | 逗号分隔温度/曲线序列（可用于复盘烹饪过程） |
| `dev_btyc.oms_merchant_machine_info` | `extra_conf(json)` | 含 `stall/sn/stallType/mainRelatedRecipes` 等结构化配置 |
| `dev_btyc.oms_merchant_update_recipe_all` | `result(longtext)` | 返回大体量 JSON（包含 recipe 列表、版本、标签、菜谱属性） |
| `dev_btyc.oms_merchant_recipe_conf` | `config(json)` | 当前表本次查询未取到数据（0 行） |
| `schedule/schedule2.oms_merchant_cooking_log` | 多字段 | 当前库表本次查询未取到数据（0 行） |

## 6. 当前卡点与下一步

### 6.1 当前卡点

- `sop_machinelog.username` 未命中这批工程师姓名，说明“本人直接操作”证据还不够直接。
- `dev_btyc` 与 `schedule/schedule2` 的部分目标表当前数据为空，跨库链路 4 暂无法实证闭环。

### 6.2 本轮结论（只回答主问题）

- **这条链现在已能部分成立**：通过 `ums_admin.id` 能连到 `sop_recipe`，再连到 `sop_machinelog` 与 `ums_company`，并且能在样例里看到具体门店、设备、菜名、时间。

### 6.3 下一步最该深挖的表（优先顺序）

1. `btyc.sop_recipe`（工程师与菜谱归属核心）
2. `btyc.sop_machinelog`（真实烹饪执行核心）
3. `btyc.btyc_user_session`（人到设备会话）
4. `btyc.sop_robot` + `btyc.ums_company`（设备到门店/客户）
5. `dev_btyc.oms_merchant_machine_info` + `dev_btyc.oms_merchant_update_recipe_all`（跨库运营链与配置链）

