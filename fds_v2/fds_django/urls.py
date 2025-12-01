from django.urls import path
from .views import DetectOrderView, DetectPurchaseView
from .views_async import IngestOrderView, IngestPurchaseView

urlpatterns = [
    # Synchronous detection (for debugging / direct calls)
    path("fds/detect/order", DetectOrderView.as_view(), name="detect-order"),
    path("fds/detect/purchase", DetectPurchaseView.as_view(), name="detect-purchase"),

    # Asynchronous ingestion (recommended for production)
    path("orders", IngestOrderView.as_view(), name="ingest-order"),
    path("purchases", IngestPurchaseView.as_view(), name="ingest-purchase"),
]