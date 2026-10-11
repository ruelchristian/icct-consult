from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('student', 'faculty', 'category', 'date', 'start_time', 'end_time', 'mode', 'status')
    list_filter = ('status', 'mode', 'date', 'category')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'faculty__user__first_name', 'faculty__user__last_name', 'reason')
    date_hierarchy = 'date'
