from typing import Dict, Any

from celery import shared_task
from django.db import transaction

from fds_core.enums import CaseKind
from fds_core.models import CaseParams, EntityRefs
from fds_core.detector import detect_case
from fds_django.models import Outbox, Processed, UserBlock, DeviceBlock, CardBlock


def _build_case_params_from_payload(payload: Dict[str, Any]) -> CaseParams:
    """Convert minimal payload into CaseParams for core detector."""
    kind_str = payload.get("kind")
    if kind_str == "order":
        kind = CaseKind.ORDER
        case_id = payload["order_id"]
    else:
        kind = CaseKind.PURCHASE
        case_id = payload["purchase_id"]

    refs = EntityRefs(
        user=payload.get("user_id") or None,
        device=payload.get("device_id") or None,
        card=payload.get("card_id") or None,
    )
    return CaseParams(kind=kind, case_id=case_id, refs=refs)


def _apply_blocklist_transactionally(acc, using: str) -> None:
    """Apply blocklist updates atomically and idempotently on a specific DB alias."""
    if not acc.register_blocklist or acc.register_params.is_empty():
        return
    rp = acc.register_params
    with transaction.atomic(using=using):
        if rp.user:
            UserBlock.objects.using(using).get_or_create(user_id=rp.user)
        if rp.device:
            DeviceBlock.objects.using(using).get_or_create(device_id=rp.device)
        if rp.card:
            CardBlock.objects.using(using).get_or_create(card_id=rp.card)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def detect_case_task(self, event_type: str, shard_id: str, aggregate_id: str, payload: Dict[str, Any]):
    """
    Worker task:
    1) idempotency guard via Processed table
    2) run core detection
    3) apply blocklist side effects
    4) mark as processed
    """
    using = "default"  # map shard_id to DB alias here if needed

    # 1) Idempotency guard
    if Processed.objects.using(using).filter(
        shard_id=shard_id,
        event_type=event_type,
        aggregate_id=aggregate_id,
    ).exists():
        return {"status": "skipped"}

    # 2) Detection
    params = _build_case_params_from_payload(payload)
    acc = detect_case(params.kind, params)

    # 3) Blocklist side effects
    _apply_blocklist_transactionally(acc, using=using)

    # 4) Mark as processed (UNIQUE constraint enforces idempotency at DB level)
    Processed.objects.using(using).create(
        shard_id=shard_id,
        event_type=event_type,
        aggregate_id=aggregate_id,
    )
    return {"status": "done", "decision": acc.decision}


@shared_task
def dispatch_outbox_batch(shard_id: str, batch: int = 500):
    """
    Dispatcher task:
    - Select READY outbox rows for a shard
    - Enqueue detect_case_task for each
    - Mark them as SENT
    Typically triggered by Celery Beat.
    """
    using = "default"

    rows = (
        Outbox.objects.using(using)
        .select_for_update(skip_locked=True)
        .filter(shard_id=shard_id, status="READY")
        .order_by("id")[:batch]
    )

    if not rows:
        return {"status": "empty"}

    dispatched = 0
    with transaction.atomic(using=using):
        for row in rows:
            detect_case_task.delay(
                event_type=row.event_type,
                shard_id=row.shard_id,
                aggregate_id=row.aggregate_id,
                payload=row.payload,
            )
            row.status = "SENT"
            row.save(using=using, update_fields=["status"])
            dispatched += 1

    return {"status": "ok", "dispatched": dispatched}