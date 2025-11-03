from typing import Iterable, List, Optional
from .enums import Decision
from .models import Result, RegisterParams
from .hit import Hit

# Severity ladder: lower is stronger
_SEV = {Decision.BLOCK: 0, Decision.REVIEW: 1, Decision.ALLOW: 2}

def update_decision(acc: Result, new_decision: Decision) -> None:
    """Promote accumulator decision only if new one is stronger (lower severity index)."""
    if _SEV[new_decision] < _SEV[acc.decision]:
        acc.decision = new_decision

def extend_reasons(acc: Result, reasons: List[str]) -> None:
    """Append reason into the accumulator"""
    if reasons:
        acc.reasons.extend(reasons)

def extend_register(acc: Result, rp: Optional[RegisterParams] = None, want_register: bool = False) -> None:
    acc.register_blocklist = acc.register_blocklist or bool(want_register)
    if not rp:
        return
    if rp.user and not acc.register_params.user:
        acc.register_params.user = rp.user
    if rp.device and not acc.register_params.device:
        acc.register_params.device = rp.device
    if rp.card and not acc.register_params.card:
        acc.register_params.card = rp.card

def resolve_p0(hits: List[Hit]) -> Decision:
    """Global priority policy: any BLOCK -> BLOCK; else any REVIEW -> REVIEW; els ALLOW."""
    if any(h.decision == Decision.BLOCK for h in hits):
        return Decision.BLOCK
    if any(h.decision == Decision.REVIEW for h in hits):
        return Decision.REVIEW
    return Decision.ALLOW

def merge_hits(hits: Iterable[Hit]) -> Result:
    """Optional utility: merge a collection of Hit into a single Result."""
    hits = list(hits)
    if not hits:
        return Result(decision=Decision.ALLOW)
    final_decision = resolve_p0(hits)
    reasons = [f"[{h.rule_id}] {h.reason}" if h.reason else f"[{h.rule_id}]" for h in hits]
    register_blocklist = any(h.register_blocklist for h in hits) # True if any hit needs blocklist (stops at first True)

    return Result(
        decision=final_decision,
        reasons=reasons,
        register_blocklist=register_blocklist,
    )