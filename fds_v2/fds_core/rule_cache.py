# fds_v2/fds_core/rule_cache.py
"""
Rule Cache Layer

This module provides an in-memory cache for SQL-based fraud detection rules.
It is designed to be lightweight, thread-safe, and fast to query during
runtime detection.

Responsible for:
  - Load rule definitions from the database at application startup
  - Store rules separately per detection target (“order” / “purchase”)
  - Expose efficient read-only access for the rule-engine layer

Schema reference (fds_django.models.Rule):
  - rule_id: unique rule identifier (str)
  - rule_sql: SQL fragment evaluated by the engine (str)
  - rule_action: result on hit ("BLOCK" | "REVIEW")
  - target: detection type ("order" | "purchase")
  - register_blocklist: whether a hit requests blocklist registration (bool)
"""

from typing import Dict, List, Tuple
from django.db import connection
from threading import Lock


# Structure: target -> list of (rule_id, rule_sql, action, register_blocklist)
_RULES: Dict[str, List[Tuple[str, str, str, bool]]] = {"order": [], "purchase": []}

# Simple thread lock for safe concurrent access and refresh
_LOCK = Lock()


def load_rules_from_db() -> None:
    """
    Load rules from the 'rules' table at Django startup (AppConfig.ready)
    """
    sql = """
        SELECT
            rule_id,
            rule_sql,
            rule_action,
            target,
            COALESCE(register_blocklist, 0) AS register_blocklist
        FROM fds_django_rules
        ORDER BY rule_id ASC
    """
    with connection.cursor() as cur:
        cur.execute(sql)
        cols = [col[0] for col in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    cache: Dict[str, List[Tuple[str, str, str, bool]]] = {"order": [], "purchase": []}
    for r in rows:
        rule_id = str(r["rule_id"])
        rule_sql = r["rule_sql"]
        action = str((r.get("rule_action") or "BLOCK")).upper()
        target = (r.get("target") or "order").lower()
        register_bl = bool(r.get("register_blocklist", False))

        if action not in ("BLOCK", "REVIEW"):
            action = "REVIEW"

        if target not in ("order", "purchase"):
            if ":order_id" in rule_sql:
                target = "order"
            elif ":purchase_id" in rule_sql:
                target = "purchase"
            else:
                continue

        cache[target].append((rule_id, rule_sql, action, register_bl))

    with _LOCK:
        _RULES["order"] = cache["order"]
        _RULES["purchase"] = cache["purchase"]

    print(f"[rules_cache] Loaded {len(cache['order'])} order rules, {len(cache['purchase'])} purchase rules.")


def get_rules(target: str) -> List[Tuple[str, str, str, bool]]:
    """
    Retrieve cached rules for a given target ("order" or "purchase").
    """
    with _LOCK:
        return list(_RULES.get(target, []))


def get_all_rules() -> Dict[str, List[Tuple[str, str, str, bool]]]:
    """
    Return all cached rules for both targets.
    """
    with _LOCK:
        return {
            "order": list(_RULES["order"]),
            "purchase": list(_RULES["purchase"]),
        }


def clear_rules() -> None:
    """
    Clear the in-memory rule cache.
    """
    with _LOCK:
        _RULES["order"].clear()
        _RULES["purchase"].clear()
    print("[rules_cache] Cleared rule cache.")


def reload_rules() -> None:
    """
    Force reload of rule cache from the database.
    Equivalent to clear_rules() + load_rules_from_db().
    """
    clear_rules()
    load_rules_from_db()