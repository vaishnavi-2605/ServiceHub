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
from notifications import views

urlpatterns = [
    path('', views.notifications_center, name='notifications_center'),
    path('poll/', views.notifications_poll, name='notifications_poll'),
    path('read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
