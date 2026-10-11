from django.contrib import admin
from .models import SessionRecord

@admin.register(SessionRecord)
class SessionRecordAdmin(admin.ModelAdmin):
    list_display = ('booking', 'attendance', 'recorded_at')
    list_filter = ('attendance', 'recorded_at')
    search_fields = ('booking__student__user__first_name', 'booking__student__user__last_name', 'advice_given')
