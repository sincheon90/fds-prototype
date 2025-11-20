from rest_framework import serializers


# -------------------------
#  Order Detect Serializer
# -------------------------

class DetectOrderItemSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=64)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity = serializers.IntegerField(min_value=1)


class DetectOrderSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=64)
    account_id = serializers.CharField(max_length=64)
    device_id = serializers.CharField(max_length=64)
    order_country = serializers.CharField(max_length=16)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=8)
    order_status = serializers.CharField(max_length=32)

    items = DetectOrderItemSerializer(many=True)

    metadata = serializers.JSONField(required=False, default=dict)

'''
{
  "order_id": "ORD123",
  "account_id": "A100",
  "device_id": "D200",
  "order_country": "JP",
  "total_price": 3000.00,
  "currency": "JPY",
  "order_status": "CREATED",
  "items": [
    { "product_id": "P100", "unit_price": 1000, "quantity": 2 },
    { "product_id": "P200", "unit_price": 1000, "quantity": 1 }
  ]
}
'''

# -------------------------
#  Purchase Detect Serializer
# -------------------------

class DetectPurchaseSerializer(serializers.Serializer):
    purchase_id = serializers.CharField(max_length=64)
    order_id = serializers.CharField(max_length=64)

    method_type = serializers.CharField(max_length=32)
    card_brand = serializers.CharField(max_length=32, required=False, allow_null=True)
    bin = serializers.CharField(max_length=16, required=False, allow_null=True)
    card_id = serializers.CharField(max_length=64, required=False, allow_null=True)

    payment_country = serializers.CharField(max_length=16)
    payment_status = serializers.CharField(max_length=32)
    failure_reason = serializers.CharField(max_length=255, required=False, allow_null=True)

    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=8)
    metadata = serializers.JSONField(required=False, default=dict)
