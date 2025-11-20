from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DetectOrderSerializer, DetectPurchaseSerializer
from .services.upsert import upsert_order_sync, upsert_purchase_sync
from .services.detection import run_detection_sync
from fds_core.enums import CaseKind


class DetectOrderView(APIView):
    def post(self, request, *args, **kwargs):
        s = DetectOrderSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        # Upsert
        upsert_order_sync(s.validated_data)

        # Run detection
        acc = run_detection_sync(CaseKind.ORDER, s.validated_data)

        return Response(
            {
                "decision": acc.decision,
                "reasons": acc.reasons,
                "register_blocklist": acc.register_blocklist,
                "register_params": acc.register_params.dict(),
            },
            status=status.HTTP_200_OK,
        )


class DetectPurchaseView(APIView):
    def post(self, request, *args, **kwargs):
        s = DetectPurchaseSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        # Upsert
        upsert_purchase_sync(s.validated_data)

        # Run detection
        acc = run_detection_sync(CaseKind.PURCHASE, s.validated_data)

        return Response(
            {
                "decision": acc.decision,
                "reasons": acc.reasons,
                "register_blocklist": acc.register_blocklist,
                "register_params": acc.register_params.dict(),
            },
            status=status.HTTP_200_OK,
        )