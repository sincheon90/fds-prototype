from decimal import Decimal
from typing import Dict, Any


def _normalize(obj: Any) -> Any:
    """
    Recursively convert Decimal -> str
    and ensure all nested structures are JSON-serializable.
    """
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize(i) for i in obj]
    return obj


def minimal_order_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build minimal payload for asynchronous detection.
    """
    payload = {
        "kind": "order",
        "order_id": data["order_id"],
        "account_id": data.get("account_id"),
        "device_id": data.get("device_id"),
        "country": data.get("order_country"),
        "price": (
            str(data.get("total_price"))
            if data.get("total_price") is not None else None
        ),
        "currency": data.get("currency"),
        "items": data.get("items", []),
        "metadata": data.get("metadata", {}),
    }
    return _normalize(payload)

def minimal_purchase_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build minimal payload for asynchronous detection.
    """
    return {
        "kind": "purchase",
        "purchase_id": data["purchase_id"],
        "order_id": data.get("order_id"),
        "device_id": data.get("device_id"),
        "card_id": data.get("card_id"),
        "card_brand": data.get("card_brand"),
        "bin": data.get("bin"),
        "country": data.get("payment_country"),
        "price": (
            str(data.get("price"))
            if data.get("price") is not None else None
        ),
        "currency": data.get("currency"),
        "payment_status": data.get("payment_status"),
        "failure_reason": data.get("failure_reason"),
        "metadata": data.get("metadata", {}),
    }
