import uuid
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# --------------------------
# Order / OrderItem / Purchase
# --------------------------

class Order(TimestampedModel):
    order_id = models.CharField(max_length=64, primary_key=True)
    account_id = models.CharField(max_length=64)
    device_id = models.CharField(max_length=64)
    order_country = models.CharField(max_length=16)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8)
    order_status = models.CharField(max_length=32)   # CREATED, PENDING_PAYMENT, ...
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Order({self.order_id})"


class OrderItem(TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.CharField(max_length=64)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.IntegerField()

    def __str__(self):
        return f"OrderItem(product={self.product_id}, order={self.order_id})"


class Purchase(TimestampedModel):
    purchase_id = models.CharField(max_length=64, primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="purchases")

    method_type = models.CharField(max_length=32)  # CARD ...
    card_brand = models.CharField(max_length=32, blank=True, null=True)
    bin = models.CharField(max_length=16, blank=True, null=True)
    card_id = models.CharField(max_length=64, blank=True, null=True)

    payment_country = models.CharField(max_length=16)
    payment_status = models.CharField(max_length=32)  # PENDING | SUCCESS | FAIL ...
    failure_reason = models.CharField(max_length=255, blank=True, null=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Purchase({self.purchase_id})"


# --------------------------
# Rule / Blocklist
# --------------------------

class Rules(TimestampedModel):
    rule_id = models.CharField(max_length=64, primary_key=True)
    rule_sql = models.TextField()
    rule_action = models.CharField(max_length=16)  # BLOCK | REVIEW
    target = models.CharField(max_length=16)       # order | purchase
    register_blocklist = models.BooleanField(default=False)

    def __str__(self):
        return f"Rule({self.rule_id})"


class UserBlock(TimestampedModel):
    user_id = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"UserBlock({self.user_id})"


class DeviceBlock(TimestampedModel):
    device_id = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"DeviceBlock({self.device_id})"


class CardBlock(TimestampedModel):
    card_id = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"CardBlock({self.card_id})"


# --------------------------
# Detection Log
# --------------------------

class DetectionLog(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    case_kind = models.CharField(max_length=16)   # "order" | "purchase"
    case_id = models.CharField(max_length=64)     # order_id or purchase_id

    decision = models.CharField(max_length=16)    # BLOCK | REVIEW | ALLOW
    reasons = models.JSONField(default=list)      # list[str]
    extra = models.JSONField(default=dict)        # dict

    def __str__(self):
        return f"DetectionLog({self.id}, {self.case_kind}, {self.case_id})"


# --------------------------
# Outbox / Processed
# --------------------------

class Outbox(TimestampedModel):
    """
    Durable outbox for detection events.

    Each row represents one detection job to be dispatched to workers.
    """
    class Status(models.TextChoices):
        READY = "READY", "Ready"
        SENT = "SENT", "Sent"
        ERROR = "ERROR", "Error"

    shard_id = models.CharField(max_length=64, default="default")
    event_type = models.CharField(max_length=64)
    aggregate_id = models.CharField(max_length=128)
    payload = models.JSONField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.READY,
    )

    class Meta:
        db_table = "outbox"
        indexes = [
            models.Index(fields=["shard_id", "status", "id"]),
        ]

    def __str__(self):
        return f"Outbox({self.id}, {self.event_type}, {self.status})"


class Processed(TimestampedModel):
    """
    Idempotency log for processed detection events.
    Ensures each (shard_id, event_type, aggregate_id) is processed at most once.
    """
    shard_id = models.CharField(max_length=32)
    event_type = models.CharField(max_length=64)
    aggregate_id = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shard_id", "event_type", "aggregate_id"],
                name="uq_processed_event",
            )
        ]

    def __str__(self) -> str:
        return f"Processed({self.shard_id}, {self.event_type}, {self.aggregate_id})"