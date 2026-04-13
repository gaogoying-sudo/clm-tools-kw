from __future__ import annotations

import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _dget(row: Dict[str, Any], key: str, default: Any = None) -> Any:
    if key in row:
        return row[key]
    upper = key.upper()
    if upper in row:
        return row[upper]
    lower = key.lower()
    if lower in row:
        return row[lower]
    return default


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", "", str(value)).strip().lower()


def normalize_phone(value: Any) -> str:
    return re.sub(r"[^0-9]", "", str(value or ""))


def phone_variants(value: Any) -> List[str]:
    digits = normalize_phone(value)
    if not digits:
        return []
    out = {digits}
    # China mobile is often stored as +86xxxxxxxxxxx or plain 11 digits.
    if digits.startswith("86") and len(digits) > 11:
        out.add(digits[-11:])
    return sorted(out)


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def iter_tokens(engineer: Dict[str, Any]) -> List[str]:
    tokens = [engineer.get("name", "")] + list(engineer.get("aliases", []))
    out: List[str] = []
    seen = set()
    for token in tokens:
        token = str(token or "").strip()
        if token and token not in seen:
            seen.add(token)
            out.append(token)
    return out


def match_accounts(engineer: Dict[str, Any], pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    matched: List[Dict[str, Any]] = []
    tokens = iter_tokens(engineer)

    for rec in pool:
        fields = {
            "username": normalize_text(_dget(rec, "username")),
            "full_name": normalize_text(_dget(rec, "full_name")),
            "nickname": normalize_text(_dget(rec, "nickname")),
            "email": normalize_text(_dget(rec, "email")),
            "mobile": normalize_text(_dget(rec, "mobile")),
            "feishu_id": normalize_text(_dget(rec, "feishu_id")),
        }

        best: Tuple[int, str, str, str] | None = None
        for token in tokens:
            norm_token = normalize_text(token)
            if not norm_token:
                continue

            for field_name, value in fields.items():
                if not value:
                    continue

                if value == norm_token:
                    score = 100
                    hit_type = "exact"
                elif has_cjk(token) and len(norm_token) >= 2 and norm_token in value:
                    score = 70
                    hit_type = "contains_cjk"
                elif (not has_cjk(token)) and len(norm_token) >= 4 and norm_token in value:
                    score = 60
                    hit_type = "contains_latin"
                else:
                    continue

                candidate = (score, token, field_name, hit_type)
                if best is None or candidate[0] > best[0]:
                    best = candidate

        if best:
            score, token, field_name, hit_type = best
            item = dict(rec)
            item["match_score"] = int(score)
            item["match_token"] = token
            item["match_field"] = field_name
            item["match_type"] = hit_type
            item["confidence"] = "high" if score >= 90 else "medium"
            matched.append(item)

    # Keep the highest score by (source, account_id).
    uniq: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for item in matched:
        key = (str(_dget(item, "source") or ""), str(_dget(item, "account_id") or ""))
        prev = uniq.get(key)
        if prev is None or int(_dget(item, "match_score") or 0) > int(_dget(prev, "match_score") or 0):
            uniq[key] = item

    return sorted(
        uniq.values(),
        key=lambda x: (
            0 if _dget(x, "confidence") == "high" else 1,
            str(_dget(x, "source") or ""),
            str(_dget(x, "admin_id") or _dget(x, "account_id") or ""),
        ),
    )


def bridge_admin_ids(matches: List[Dict[str, Any]], conn) -> List[int]:
    admin_ids = set()

    for item in matches:
        if str(_dget(item, "source") or "") == "ums_admin" and _dget(item, "admin_id") is not None:
            admin_ids.add(int(_dget(item, "admin_id")))

    auth_users = [m for m in matches if str(_dget(m, "source") or "") == "auth_user"]
    if not auth_users:
        return sorted(admin_ids)

    mobiles = set()
    names = set()
    usernames = set()
    for item in auth_users:
        for val in phone_variants(_dget(item, "mobile")):
            mobiles.add(val)
        nickname = str(_dget(item, "nickname") or "").strip()
        if nickname:
            names.add(nickname)
        username = str(_dget(item, "username") or "").strip()
        if username:
            usernames.add(username)

    with conn.cursor() as cur:
        if mobiles:
            placeholders = ",".join(["%s"] * len(mobiles))
            cur.execute(
                f"""
                SELECT id
                FROM btyc.ums_admin
                WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(phone_num, '+', ''), ' ', ''), '-', ''), '(', ''), ')', '')
                  IN ({placeholders})
                """,
                list(mobiles),
            )
            for row in cur.fetchall():
                admin_ids.add(int(_dget(row, "id")))

        if names:
            placeholders = ",".join(["%s"] * len(names))
            cur.execute(
                f"SELECT id FROM btyc.ums_admin WHERE full_name IN ({placeholders})",
                list(names),
            )
            for row in cur.fetchall():
                admin_ids.add(int(_dget(row, "id")))

        if usernames:
            placeholders = ",".join(["%s"] * len(usernames))
            cur.execute(
                f"SELECT id FROM btyc.ums_admin WHERE username IN ({placeholders})",
                list(usernames),
            )
            for row in cur.fetchall():
                admin_ids.add(int(_dget(row, "id")))

    return sorted(admin_ids)


def _mapping_status(matches: List[Dict[str, Any]], admin_ids: List[int]) -> str:
    if not matches:
        return "no_match"
    if not admin_ids:
        return "matched_no_admin_bridge"
    if len(admin_ids) == 1:
        return "mapped_unique"
    return "mapped_multiple"


def build_engineer_mapping(engineer: Dict[str, Any], pool: List[Dict[str, Any]], conn) -> Dict[str, Any]:
    matches = match_accounts(engineer, pool)
    admin_ids = bridge_admin_ids(matches, conn)

    auth_user_ids = sorted(
        {
            str(_dget(m, "account_id"))
            for m in matches
            if str(_dget(m, "source") or "") == "auth_user" and _dget(m, "account_id") is not None
        }
    )
    ums_admin_ids = sorted(
        {
            int(_dget(m, "admin_id"))
            for m in matches
            if str(_dget(m, "source") or "") == "ums_admin" and _dget(m, "admin_id") is not None
        }
    )
    high_conf_count = sum(1 for m in matches if _dget(m, "confidence") == "high")

    return {
        "engineer_display": engineer.get("display"),
        "engineer_name": engineer.get("name"),
        "aliases": list(engineer.get("aliases", [])),
        "admin_ids": admin_ids,
        "primary_admin_id": admin_ids[0] if len(admin_ids) == 1 else None,
        "auth_user_ids": auth_user_ids,
        "ums_admin_ids": ums_admin_ids,
        "match_count": len(matches),
        "high_conf_count": high_conf_count,
        "source_mapping_status": _mapping_status(matches, admin_ids),
        "matches": matches,
    }


def run_engineer_mapping(engineers: List[Dict[str, Any]], pool: List[Dict[str, Any]], conn) -> Dict[str, Any]:
    rows = [build_engineer_mapping(engineer, pool=pool, conn=conn) for engineer in engineers]
    summary = {
        "engineers_total": len(rows),
        "mapped_engineers": sum(1 for r in rows if r.get("admin_ids")),
        "unique_mapped_engineers": sum(1 for r in rows if r.get("source_mapping_status") == "mapped_unique"),
        "multiple_mapped_engineers": sum(1 for r in rows if r.get("source_mapping_status") == "mapped_multiple"),
        "unmatched_engineers": sum(1 for r in rows if r.get("source_mapping_status") == "no_match"),
    }
    return {"summary": summary, "rows": rows}


def export_mapping_result(result: Dict[str, Any], output_dir: Path, stamp: str) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"data_sync_engineer_admin_mapping_{stamp}.json"
    summary_csv_path = output_dir / f"data_sync_engineer_admin_mapping_summary_{stamp}.csv"
    detail_csv_path = output_dir / f"data_sync_engineer_admin_mapping_detail_{stamp}.csv"

    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    summary_fields = [
        "engineer_display",
        "source_mapping_status",
        "match_count",
        "high_conf_count",
        "admin_ids",
        "auth_user_ids",
        "ums_admin_ids",
    ]
    with summary_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields)
        writer.writeheader()
        for row in result.get("rows", []):
            writer.writerow(
                {
                    "engineer_display": row.get("engineer_display"),
                    "source_mapping_status": row.get("source_mapping_status"),
                    "match_count": row.get("match_count"),
                    "high_conf_count": row.get("high_conf_count"),
                    "admin_ids": ";".join(str(x) for x in row.get("admin_ids", [])),
                    "auth_user_ids": ";".join(str(x) for x in row.get("auth_user_ids", [])),
                    "ums_admin_ids": ";".join(str(x) for x in row.get("ums_admin_ids", [])),
                }
            )

    detail_fields = [
        "engineer_display",
        "source",
        "account_id",
        "admin_id",
        "username",
        "full_name",
        "nickname",
        "mobile",
        "feishu_id",
        "role_name",
        "company_name",
        "match_token",
        "match_field",
        "match_type",
        "match_score",
        "confidence",
    ]
    with detail_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=detail_fields)
        writer.writeheader()
        for row in result.get("rows", []):
            engineer_display = row.get("engineer_display")
            for match in row.get("matches", []):
                writer.writerow(
                    {
                        "engineer_display": engineer_display,
                        "source": _dget(match, "source"),
                        "account_id": _dget(match, "account_id"),
                        "admin_id": _dget(match, "admin_id"),
                        "username": _dget(match, "username"),
                        "full_name": _dget(match, "full_name"),
                        "nickname": _dget(match, "nickname"),
                        "mobile": _dget(match, "mobile"),
                        "feishu_id": _dget(match, "feishu_id"),
                        "role_name": _dget(match, "role_name"),
                        "company_name": _dget(match, "company_name"),
                        "match_token": _dget(match, "match_token"),
                        "match_field": _dget(match, "match_field"),
                        "match_type": _dget(match, "match_type"),
                        "match_score": _dget(match, "match_score"),
                        "confidence": _dget(match, "confidence"),
                    }
                )

    return {
        "json": str(json_path),
        "summary_csv": str(summary_csv_path),
        "detail_csv": str(detail_csv_path),
    }


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")

