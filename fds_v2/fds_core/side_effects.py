from dataclasses import asdict
from typing import Any, List, Dict

from django.db import transaction

from .hit import Hit
from .models import RegisterParams
from .rules_engine import Decision
from fds_django.models import UserBlock, DeviceBlock, CardBlock, DetectionLog


def register_blocklist(db: Any, rp: RegisterParams) -> None:
    """
    Blocklist registration

    - Executes all operations within a single transaction
    - Ensures idempotency using get_or_create
    - The `db` argument is currently unused but kept for signature compatibility
    """
    if rp.is_empty():
        return

    with transaction.atomic():
        if rp.user:
            UserBlock.objects.get_or_create(user_id=rp.user)
        if rp.device:
            DeviceBlock.objects.get_or_create(device_id=rp.device)
        if rp.card:
            CardBlock.objects.get_or_create(card_id=rp.card)


def log_decision(kind: str, ref_id: Any, final: Decision, hits: List[Hit]) -> None:
    """
    Persist detection result into DetectionLog.
    """
    ref_str = str(ref_id)

    reasons: List[str] = []
    for h in hits:
        if h.reason:
            reasons.append(h.reason)
        else:
            reasons.append(f"rule={h.rule_id}, decision={h.decision}")

    extra: Dict[str, Any] = {
        "hits": [asdict(h) for h in hits],
    }

    DetectionLog.objects.create(
        case_kind=kind,
        case_id=ref_str,
        decision=str(final),
        reasons=reasons,
        extra=extra,
    )