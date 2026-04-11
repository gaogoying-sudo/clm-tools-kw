#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_sync.config import resolve_source_db_config
from data_sync.db import connect_source_db, fetch_account_pool
from data_sync.engineers import select_engineers
from data_sync.mapper import export_mapping_result, now_stamp, run_engineer_mapping


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DateUse data-sync CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_map = sub.add_parser(
        "map-admin-ids",
        help="Map engineer names to admin_id by reading BT-cooking source DB.",
    )
    p_map.add_argument(
        "--engineer",
        action="append",
        default=[],
        help="Engineer display/name/alias. Repeat for multiple engineers.",
    )
    p_map.add_argument(
        "--all",
        action="store_true",
        help="Map all engineers in default roster (36).",
    )
    p_map.add_argument(
        "--output-dir",
        default="exports",
        help="Output directory for JSON/CSV files. Default: exports",
    )
    p_map.add_argument(
        "--print-json",
        action="store_true",
        help="Print result JSON to stdout after execution.",
    )
    return parser


def run_map_admin_ids(args) -> int:
    root = Path(__file__).resolve().parents[2]
    config = resolve_source_db_config(project_root=root)

    if args.all or not args.engineer:
        engineers = select_engineers(None)
    else:
        engineers = select_engineers(args.engineer)
        if not engineers:
            raise SystemExit("No engineer matched input names in default roster.")

    conn = connect_source_db(config)
    try:
        pool = fetch_account_pool(conn)
        result = run_engineer_mapping(engineers=engineers, pool=pool, conn=conn)
    finally:
        conn.close()

    stamp = now_stamp()
    output_dir = (root / args.output_dir).resolve()
    file_map = export_mapping_result(result=result, output_dir=output_dir, stamp=stamp)

    summary = result.get("summary", {})
    print("data-sync mapping done")
    print(
        json.dumps(
            {
                "engineers_total": summary.get("engineers_total"),
                "mapped_engineers": summary.get("mapped_engineers"),
                "unique_mapped_engineers": summary.get("unique_mapped_engineers"),
                "multiple_mapped_engineers": summary.get("multiple_mapped_engineers"),
                "unmatched_engineers": summary.get("unmatched_engineers"),
                "files": file_map,
            },
            ensure_ascii=False,
        )
    )
    if args.print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "map-admin-ids":
        return run_map_admin_ids(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

