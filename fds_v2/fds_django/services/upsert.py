# fds_django/services/upsert.py
from typing import Dict, Any
from django.db import transaction

from fds_django.models import Order, OrderItem, Purchase
from fds_django.services.model_utils import filter_model_defaults


def upsert_order_sync(data: Dict[str, Any]) -> None:
    """
    Synchronous upsert to DB (Order + OrderItem)
    """
    using = "default"

    order_defaults = filter_model_defaults(Order, data)
    items_data = data.get("items", [])

    with transaction.atomic(using=using):
        order_obj, _ = Order.objects.using(using).update_or_create(
            order_id=data["order_id"],
            defaults=order_defaults,
        )

        # Replace all items
        OrderItem.objects.using(using).filter(order=order_obj).delete()

        bulk_items = [
            OrderItem(
                order=order_obj,
                product_id=item["product_id"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
            )
            for item in items_data
        ]
        if bulk_items:
            OrderItem.objects.using(using).bulk_create(bulk_items)


def upsert_purchase_sync(data: Dict[str, Any]) -> None:
    """
    Synchronous upsert to Purchase table
    """
    using = "default"

    purchase_defaults = filter_model_defaults(Purchase, data)

    with transaction.atomic(using=using):
        Purchase.objects.using(using).update_or_create(
            purchase_id=data["purchase_id"],
            defaults=purchase_defaults,
        )
