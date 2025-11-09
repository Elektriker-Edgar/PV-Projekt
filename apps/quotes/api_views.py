from typing import Dict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from .models import Component, Precheck, Quote
from .pricing import (
    pricing_input_from_request,
    calculate_pricing,
    pricing_to_response,
)


# Placeholders to satisfy router imports. Minimal list() returning JSON.
class ComponentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Component.objects.all()
    serializer_class = None

    def list(self, request, *args, **kwargs):
        data = [
            {
                'id': c.id,
                'name': c.name,
                'type': c.type,
                'vendor': c.vendor,
                'sku': c.sku,
                'unit_price': str(c.unit_price),
            }
            for c in self.get_queryset()
        ]
        return JsonResponse(data, safe=False)


class PrecheckViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Precheck.objects.all()
    serializer_class = None

    def list(self, request, *args, **kwargs):
        return JsonResponse([], safe=False)


class QuoteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quote.objects.all()
    serializer_class = None

    def list(self, request, *args, **kwargs):
        return JsonResponse([], safe=False)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def pricing_preview(request):
    payload: Dict = request.data if hasattr(request, 'data') else request.POST
    pricing_input = pricing_input_from_request(payload)
    pricing = calculate_pricing(pricing_input)
    return JsonResponse(pricing_to_response(pricing))


@api_view(['POST'])
def create_precheck(request):
    return JsonResponse({'detail': 'not implemented'}, status=501)


@api_view(['POST'])
def approve_quote(request, pk):
    return JsonResponse({'detail': 'not implemented'}, status=501)


@api_view(['POST'])
def n8n_webhook(request):
    return JsonResponse({'detail': 'ok'})

