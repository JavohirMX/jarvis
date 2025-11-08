"""
URL configuration for profiles app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('reset/', views.ProfileResetView.as_view(), name='profile-reset'),
    path('usage/', views.ProfileUsageView.as_view(), name='profile-usage'),
]

