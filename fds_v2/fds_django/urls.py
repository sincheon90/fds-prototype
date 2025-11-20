from django.urls import path
from .views import DetectOrderView, DetectPurchaseView

urlpatterns = [
    # Synchronous detection (for debugging / direct calls)
    path("fds/detect/order", DetectOrderView.as_view(), name="detect-order"),
    path("fds/detect/purchase", DetectPurchaseView.as_view(), name="detect-purchase"),
]