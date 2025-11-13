from typing import Any

from fds_v2.core.enums import CaseKind
from fds_v2.core.models import Result
from fds_v2.core.rules_engine import detect_order_core, detect_purchase_core
from fds_v2.core.side_effects import register_blocklist


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