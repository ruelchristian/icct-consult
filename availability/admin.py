from django.contrib import admin
from .models import AvailabilitySlot

@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'day_of_week', 'start_time', 'end_time', 'mode', 'is_active')
    list_filter = ('day_of_week', 'mode', 'is_active')
    search_fields = ('faculty__user__first_name', 'faculty__user__last_name', 'location_or_link')
