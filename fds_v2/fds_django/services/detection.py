from typing import Dict, Any

from fds_core.enums import CaseKind
from fds_core.models import CaseParams, EntityRefs, RegisterParams, Result
from fds_core.detector import detect_case


def build_case_params(kind: CaseKind, payload: Dict[str, Any]) -> CaseParams:
    """
    Build CaseParams from a validated payload (serializer output).
    """
    if kind == CaseKind.ORDER:
        case_id = payload["order_id"]
    else:
        case_id = payload["purchase_id"]

    refs = EntityRefs(
        user=payload.get("user_id") or None,
        device=payload.get("device_id") or None,
        card=payload.get("card_id") or None,
    )
    return CaseParams(kind=kind, case_id=case_id, refs=refs)


def run_detection_sync(kind: CaseKind, payload: Dict[str, Any]) -> Result:
    """
    Call fds_core detect_case with DB connection (include blocklist side effects)
    """
    params = build_case_params(kind, payload)

    return detect_case(kind, params)