from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import DetectOrderSerializer, DetectPurchaseSerializer
from .services.upsert_and_emit import upsert_order_and_emit, upsert_purchase_and_emit


class IngestOrderView(APIView):
    """
    Asynchronous ingestion endpoint for orders.
    - Upsert order
    - Enqueue detection to outbox
    - Actual detection runs on worker
    """
    def post(self, request, *args, **kwargs):
        s = DetectOrderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        upsert_order_and_emit(s.validated_data, shard_id="default")
        return Response({"status": "queued"}, status=status.HTTP_201_CREATED)


class IngestPurchaseView(APIView):
    """Asynchronous ingestion endpoint for purchases."""
    def post(self, request, *args, **kwargs):
        s = DetectPurchaseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        upsert_purchase_and_emit(s.validated_data, shard_id="default")
        return Response({"status": "queued"}, status=status.HTTP_201_CREATED)