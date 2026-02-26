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
    path('booking/<int:booking_id>/', views.booking_status, name='booking_status'),
    path('booking/<int:booking_id>/live-location/update/', views.update_live_location, name='update_live_location'),
    path('booking/<int:booking_id>/provider-live-location/update/', views.update_provider_live_location, name='update_provider_live_location'),
    path('booking/<int:booking_id>/live-location/data/', views.live_location_data, name='live_location_data'),
    path('booking/<int:booking_id>/start/', views.start_service, name='start_service'),
    path('booking/<int:booking_id>/mark-done/', views.mark_done, name='mark_done'),
    path('booking/<int:booking_id>/pay/', views.confirm_payment, name='confirm_payment'),
    path('booking/<int:booking_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('booking/<int:booking_id>/report/', views.submit_report, name='submit_report'),
]

