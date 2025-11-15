from typing import Any, List

from django.db import transaction

from .models import RegisterParams
from ..fds_django.models import UserBlock, DeviceBlock, CardBlock


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