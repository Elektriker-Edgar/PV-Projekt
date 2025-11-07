from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'components', api_views.ComponentViewSet)
router.register(r'prechecks', api_views.PrecheckViewSet)
router.register(r'quotes', api_views.QuoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('precheck/', api_views.create_precheck, name='api_create_precheck'),
    path('pricing/preview/', api_views.pricing_preview, name='api_pricing_preview'),
    path('quote/<int:pk>/approve/', api_views.approve_quote, name='api_approve_quote'),
    path('integrations/n8n/webhook/', api_views.n8n_webhook, name='n8n_webhook'),
]
