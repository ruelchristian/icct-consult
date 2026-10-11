from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('ICCT Role & School Info', {'fields': ('role', 'school_id', 'phone_number')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'school_id', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'school_id')
