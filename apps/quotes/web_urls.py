from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('', views.home, name='home'),
    path('precheck/', views.precheck_wizard, name='precheck_wizard'),
    path('faq/', views.faq, name='faq'),
    path('packages/', views.packages, name='packages'),
    path('compatible-systems/', views.compatible_systems, name='compatible_systems'),
    path('quote/<str:quote_number>/', views.quote_detail, name='quote_detail'),
    path('quote/<str:quote_number>/pdf/', views.quote_pdf, name='quote_pdf'),
]