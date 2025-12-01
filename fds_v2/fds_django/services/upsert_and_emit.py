from typing import Dict, Any
from django.db import transaction

from fds_django.models import Order, OrderItem, Purchase, Outbox
from fds_django.services.payload import minimal_order_payload, minimal_purchase_payload
from fds_django.services.model_utils import filter_model_defaults


def upsert_order_and_emit(order_data: Dict[str, Any], shard_id: str = "default") -> None:
    """
    Ingest an order snapshot in an idempotent way and emit an outbox event.

    One transaction performs:
      1. Upsert the Order (update_or_create)
      2. Replace all OrderItems for that Order (full snapshot overwrite)
      3. Insert an Outbox event in READY state
    """
    using = "default"  # Later: route shard_id -> DB alias

    # Extract only model-backed fields for the Order table
    order_defaults = filter_model_defaults(Order, order_data)
    items_data = order_data.get("items", [])

    with transaction.atomic(using=using):
        # 1. Upsert Order
        order_obj, _ = Order.objects.using(using).update_or_create(
            order_id=order_data["order_id"],
            defaults=order_defaults,
        )

        # 2. Replace OrderItems (snapshot overwrite)
        OrderItem.objects.using(using).filter(order=order_obj).delete()

        order_items = [
            OrderItem(
                order=order_obj,
                product_id=item["product_id"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
            )
            for item in items_data
        ]
        if order_items:
            OrderItem.objects.using(using).bulk_create(order_items)

        # 3. Outbox event
        Outbox.objects.using(using).create(
            shard_id=shard_id,
            event_type="order_upserted",
            aggregate_id=order_data["order_id"],
            payload=minimal_order_payload(order_data),
            status="READY",
        )


def upsert_purchase_and_emit(purchase_data: Dict[str, Any], shard_id: str = "default") -> None:
    """
    Ingest a purchase snapshot idempotently and emit an outbox event.

    Steps inside a single transaction:
      1. Upsert the Purchase row
      2. Insert outbox event for downstream asynchronous detection
    """
    using = "default"

    purchase_defaults = filter_model_defaults(Purchase, purchase_data)

    with transaction.atomic(using=using):
        Purchase.objects.using(using).update_or_create(
            purchase_id=purchase_data["purchase_id"],
            defaults=purchase_defaults,
        )

        Outbox.objects.using(using).create(
            shard_id=shard_id,
            event_type="purchase_upserted",
            aggregate_id=purchase_data["purchase_id"],
            payload=minimal_purchase_payload(purchase_data),
            status="READY",
        )