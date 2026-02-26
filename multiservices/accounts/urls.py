from django.urls import path
from accounts import views
from booking import views as booking_views

urlpatterns = [
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),
    path('profile/', views.update_profile, name='profile_update'),
    path('provider_dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_dashboard/provider/<int:provider_id>/approve/', views.admin_approve_provider, name='admin_approve_provider'),
    path('admin_dashboard/provider/<int:provider_id>/remove/', views.admin_remove_provider, name='admin_remove_provider'),
    path('admin_dashboard/provider/<int:provider_id>/', views.admin_provider_detail, name='admin_provider_detail'),
    path('admin_dashboard/report/<int:report_id>/', views.admin_report_detail, name='admin_report_detail'),
    path('provider_dashboard/booking/<int:booking_id>/accept/', booking_views.accept_booking, name='accept_booking'),
    path('provider_dashboard/booking/<int:booking_id>/reject/', booking_views.reject_booking, name='reject_booking'),
    path('user_dashboard/booking/<int:booking_id>/reject/', booking_views.user_reject_booking, name='user_reject_booking'),
]


