from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('', views.home, name='home'),
    path('precheck/', views.precheck_wizard, name='precheck_wizard'),
    path('precheck/success/', views.precheck_success, name='precheck_success'),
    path('faq/', views.faq, name='faq'),
    path('packages/', views.packages, name='packages'),
    path('packages/inquiry/<str:package>/', views.package_inquiry, name='package_inquiry'),
    path('packages/success/', views.package_success, name='package_success'),
    path('compatible-systems/', views.compatible_systems, name='compatible_systems'),
    path('quote/<str:quote_number>/', views.quote_detail, name='quote_detail'),
    path('quote/<str:quote_number>/pdf/', views.quote_pdf, name='quote_pdf'),
    # Admin-Bereiche
    path('admin/quotes/review/', views.quote_review_list, name='quote_review_list'),
    path('admin/quotes/<int:quote_id>/approve/', views.approve_quote, name='approve_quote'),
]