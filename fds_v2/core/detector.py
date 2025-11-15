from typing import Any

from .enums import CaseKind
from .models import Result
from .rules_engine import detect_order_core, detect_purchase_core
from .side_effects import register_blocklist


def detect_case(kind: CaseKind | str, ref_id: Any) -> Result:
    if isinstance(kind, str):
        kind = CaseKind(kind)

    if kind == CaseKind.ORDER:
        final, hits = detect_order_core(ref_id)
    elif kind == CaseKind.PURCHASE:
        final, hits = detect_purchase_core(ref_id)
    else:
        raise ValueError(f"Unsupported CaseKind: {kind}")

    if any(h.register_blocklist for h in hits):
        register_blocklist(kind.value, ref_id, hits)

    return Result(
        kind=kind,
        ref_id=str(ref_id),
        decision=final,
        hits=hits,
    )