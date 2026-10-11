import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from .models import AvailabilitySlot
from .forms import AvailabilitySlotForm
from directory.models import FacultyProfile

def faculty_calendar_events_json(request, faculty_id):
    """
    JSON feed consumed by FullCalendar to render the weekly consultation slots.
    FullCalendar recurrence: daysOfWeek = [1, 2, ..] (0=Sunday in FullCalendar, in Python 0=Monday).
    """
    faculty = get_object_or_404(FacultyProfile, id=faculty_id)
    slots = AvailabilitySlot.objects.filter(faculty=faculty, is_active=True)

    events = []
    # FullCalendar daysOfWeek: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
    # Our model: 0=Monday .. 5=Saturday, 6=Sunday
    python_to_fc_day = {
        0: 1, # Mon
        1: 2, # Tue
        2: 3, # Wed
        3: 4, # Thu
        4: 5, # Fri
        5: 6, # Sat
        6: 0, # Sun
    }

    for slot in slots:
        fc_day = python_to_fc_day.get(slot.day_of_week, 1)
        mode_label = slot.get_mode_display()
        events.append({
            'title': f"Consultation ({mode_label})",
            'daysOfWeek': [fc_day],
            'startTime': slot.start_time.strftime('%H:%M:%S'),
            'endTime': slot.end_time.strftime('%H:%M:%S'),
            'color': '#0B2545',
            'textColor': '#FFFFFF',
            'extendedProps': {
                'mode': mode_label,
                'location': slot.location_or_link or 'Department Office',
                'duration': slot.slot_duration_minutes,
            }
        })

    return JsonResponse(events, safe=False)

@login_required
def manage_slots_view(request):
    """
    Faculty interface to manage their weekly availability hours.
    """
    if not request.user.is_faculty and not request.user.is_department_admin:
        messages.error(request, "Only faculty members can manage consultation hours.")
        return redirect('core:home')

    faculty = getattr(request.user, 'faculty_profile', None)
    if not faculty:
        messages.error(request, "Faculty profile not configured.")
        return redirect('core:home')

    if request.method == 'POST':
        form = AvailabilitySlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.faculty = faculty
            slot.save()
            messages.success(request, f"Consultation hours for {slot.get_day_of_week_display()} added successfully.")
            return redirect('availability:manage_slots')
    else:
        form = AvailabilitySlotForm()

    slots = AvailabilitySlot.objects.filter(faculty=faculty).order_by('day_of_week', 'start_time')

    return render(request, 'availability/manage_slots.html', {
        'form': form,
        'slots': slots,
        'faculty': faculty,
    })

@login_required
def delete_slot_view(request, slot_id):
    faculty = getattr(request.user, 'faculty_profile', None)
    slot = get_object_or_404(AvailabilitySlot, id=slot_id)

    if slot.faculty != faculty and not request.user.is_department_admin:
        return HttpResponseForbidden("Not authorized.")

    slot.delete()
    messages.info(request, "Consultation slot removed.")
    return redirect('availability:manage_slots')
