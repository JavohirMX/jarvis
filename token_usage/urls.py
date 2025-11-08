"""
URL configuration for token_usage app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.UsageStatsView.as_view(), name='usage-stats'),
    path('history/', views.UsageHistoryView.as_view(), name='usage-history'),
    path('quotas/', views.UsageQuotasView.as_view(), name='usage-quotas'),
    path('cost/', views.UsageCostView.as_view(), name='usage-cost'),
]

