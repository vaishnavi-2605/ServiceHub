from django.contrib import admin

from .models import CustomUser, ProviderProfile


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'email', 'role', 'mobile_no')
    search_fields = ('username', 'first_name', 'email', 'mobile_no')
    list_filter = ('role',)


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'experience')
    search_fields = ('user__username', 'user__email', 'phone')
