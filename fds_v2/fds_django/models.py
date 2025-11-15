from django.db import models

class TimestampedModel(models.Model):
    """Common created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# ---------------------------------------------------------------------
# Blocklists
# ---------------------------------------------------------------------

class UserBlock(TimestampedModel):
    user_id = models.CharField(max_length=128, unique=True)

    def __str__(self) -> str:
        return f"UserBlock({self.user_id})"


class DeviceBlock(TimestampedModel):
    device_id = models.CharField(max_length=128, unique=True)

    def __str__(self) -> str:
        return f"DeviceBlock({self.device_id})"


class CardBlock(TimestampedModel):
    card_id = models.CharField(max_length=128, unique=True)

    def __str__(self) -> str:
        return f"CardBlock({self.card_id})"