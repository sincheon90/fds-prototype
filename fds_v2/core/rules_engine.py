from typing import Dict, List, Tuple, Any

from django.db import connection

from .hit import Hit

# structure: target -> list of (rule_id, rule_sql, action, register_blocklist)
RULES: Dict[str, List[Tuple[str, str, str, bool]]] = {"order": [], "purchase": []}

Decision = str  # "ALLOW" | "REVIEW" | "BLOCK"

def resolve_p0(hits: List[Hit]) -> Decision:
    """
    Priority policy:
      - any BLOCK -> BLOCK
      - else any REVIEW -> REVIEW
      - else ALLOW
    """
    if any(h.decision == "BLOCK" for h in hits):
        return "BLOCK"
    if any(h.decision == "REVIEW" for h in hits):
        return "REVIEW"
    return "ALLOW"


def _run_one_rule(rule_sql: str, params: Dict[str, Any], target: str) -> bool:
    """
    Execute a single rule.

    The rule SQL should use %s placeholders instead of named ones.
    Example:
        SELECT 1 FROM orders WHERE id = %s
    """

    # Safety guard: ensure target consistency
    if target == "order" and "order_id" not in params:
        return False
    if target == "purchase" and "purchase_id" not in params:
        return False

    # Prepare parameters for case binding
    if target == "order":
        args = [params["order_id"]]
    else:
        args = [params["purchase_id"]]

    with connection.cursor() as cur:
        cur.execute(rule_sql, args)
        row = cur.fetchone()

    return bool(row)


def _evaluate_target_rules(target: str, params: Dict[str, Any]) -> List[Hit]:
    """
    Evaluate all rules for the given target.
    """
    hits: List[Hit] = []
    for rule_id, rule_sql, action, register_bl in RULES.get(target, []):
        try:
            if _run_one_rule(rule_sql, params, target):
                hits.append(
                    Hit(rule_id=str(rule_id), decision=action, register_blocklist=register_bl)
                )
        except Exception:
            continue
    return hits


def detect_order_core(order_id: Any) -> Tuple[Decision, List[Hit]]:
    """
    Core detection for an order_id using in-memory rules.
    """
    params = {"order_id": order_id}
    hits = _evaluate_target_rules("order", params)

    sev = {"BLOCK": 0, "REVIEW": 1}
    hits_sorted = sorted(hits, key=lambda h: (sev.get(h.decision, 9), h.rule_id))
    final = resolve_p0(hits_sorted)

    return final, hits_sorted


def detect_purchase_core(purchase_id: Any) -> Tuple[Decision, List[Hit]]:
    """
    Core detection for a purchase_id using in-memory rules.
    """
    params = {"purchase_id": purchase_id}
    hits = _evaluate_target_rules("purchase", params)

    sev = {"BLOCK": 0, "REVIEW": 1}
    hits_sorted = sorted(hits, key=lambda h: (sev.get(h.decision, 9), h.rule_id))
    final = resolve_p0(hits_sorted)

    return final, hits_sorted