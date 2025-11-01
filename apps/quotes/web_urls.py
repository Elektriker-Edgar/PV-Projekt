from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('', views.home, name='home'),
    path('precheck/', views.precheck_wizard, name='precheck_wizard'),
    path('quote/<str:quote_number>/', views.quote_detail, name='quote_detail'),
    path('quote/<str:quote_number>/pdf/', views.quote_pdf, name='quote_pdf'),
]