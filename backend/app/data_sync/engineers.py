from __future__ import annotations

from typing import Dict, Any, List


ENGINEER_ROSTER: List[Dict[str, Any]] = [
    {"display": "付强(Fonzie)", "name": "付强", "aliases": ["Fonzie"]},
    {"display": "唐浩宇", "name": "唐浩宇", "aliases": []},
    {"display": "胡光中", "name": "胡光中", "aliases": []},
    {"display": "江飞", "name": "江飞", "aliases": []},
    {"display": "刘兰强", "name": "刘兰强", "aliases": []},
    {"display": "张海", "name": "张海", "aliases": []},
    {"display": "冯明", "name": "冯明", "aliases": []},
    {"display": "周洪亮", "name": "周洪亮", "aliases": []},
    {"display": "高豪", "name": "高豪", "aliases": []},
    {"display": "罗刚", "name": "罗刚", "aliases": []},
    {"display": "雷祖壮", "name": "雷祖壮", "aliases": []},
    {"display": "尹龙强", "name": "尹龙强", "aliases": []},
    {"display": "杨梓锋", "name": "杨梓锋", "aliases": []},
    {"display": "张连顺", "name": "张连顺", "aliases": []},
    {"display": "许宝华", "name": "许宝华", "aliases": []},
    {"display": "周思来(Chef Chow)", "name": "周思来", "aliases": ["Chef Chow"]},
    {"display": "马志明", "name": "马志明", "aliases": []},
    {"display": "陈龙", "name": "陈龙", "aliases": []},
    {"display": "卢明辉", "name": "卢明辉", "aliases": []},
    {"display": "王野", "name": "王野", "aliases": []},
    {"display": "周华玉", "name": "周华玉", "aliases": []},
    {"display": "周潮凌", "name": "周潮凌", "aliases": []},
    {"display": "沈伯腾(Harry Shen)", "name": "沈伯腾", "aliases": ["Harry Shen"]},
    {"display": "陈尚贤", "name": "陈尚贤", "aliases": []},
    {"display": "李彦彪(REX)", "name": "李彦彪", "aliases": ["REX"]},
    {"display": "陈镭福(杰哥 Amos Tan)", "name": "陈镭福", "aliases": ["杰哥", "Amos Tan"]},
    {"display": "周辰永(Jon)", "name": "周辰永", "aliases": ["Jon"]},
    {"display": "Kevin Hartley", "name": "Kevin Hartley", "aliases": []},
    {"display": "Fami Taufeq Fakarudin", "name": "Fami Taufeq Fakarudin", "aliases": []},
    {"display": "戴子扬(Joe)", "name": "戴子扬", "aliases": ["Joe"]},
    {"display": "黄俊龙", "name": "黄俊龙", "aliases": []},
    {"display": "周杰彪(Jason)", "name": "周杰彪", "aliases": ["Jason"]},
    {"display": "李传灵", "name": "李传灵", "aliases": []},
    {"display": "宗振兴", "name": "宗振兴", "aliases": []},
    {"display": "利伟锋(Liam Li)", "name": "利伟锋", "aliases": ["Liam Li"]},
    {"display": "唐清林", "name": "唐清林", "aliases": []},
]


def select_engineers(names: List[str] | None = None) -> List[Dict[str, Any]]:
    if not names:
        return list(ENGINEER_ROSTER)

    wanted = {str(x).strip().lower() for x in names if str(x).strip()}
    selected: List[Dict[str, Any]] = []
    seen = set()

    for engineer in ENGINEER_ROSTER:
        candidates = [
            str(engineer.get("display", "")).strip().lower(),
            str(engineer.get("name", "")).strip().lower(),
            *[str(a).strip().lower() for a in engineer.get("aliases", [])],
        ]
        if any(c in wanted for c in candidates):
            key = engineer.get("display")
            if key not in seen:
                seen.add(key)
                selected.append(engineer)

    return selected

