"""
URL configuration for multiservices project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.service, name='service'),
    path('provider/manage/', views.provider_services, name='provider_services'),
    path('provider/manage/<int:service_id>/edit/', views.edit_provider_service, name='edit_provider_service'),
    path('provider/manage/<int:service_id>/delete/', views.delete_provider_service, name='delete_provider_service'),
    path('<int:service_id>/', views.service_detail, name='service_detail'),
    path('<int:service_id>/book/', views.create_booking, name='create_booking'),
]
