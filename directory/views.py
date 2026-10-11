from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import FacultyProfile, Department, Category
from availability.models import AvailabilitySlot

def faculty_directory_view(request):
    """
    Searchable directory of all faculty members with department filters.
    """
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('dept', '').strip()

    faculty_qs = FacultyProfile.objects.select_related('user', 'department').all()

    if query:
        faculty_qs = faculty_qs.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(title__icontains=query) |
            Q(office_location__icontains=query)
        )

    if dept_id:
        faculty_qs = faculty_qs.filter(department_id=dept_id)

    departments = Department.objects.all()

    return render(request, 'directory/faculty_list.html', {
        'faculty_list': faculty_qs,
        'departments': departments,
        'query': query,
        'selected_dept': dept_id,
    })

def faculty_detail_view(request, faculty_id):
    """
    Profile of a faculty member with their published weekly consultation hours.
    """
    faculty = get_object_or_404(FacultyProfile.objects.select_related('user', 'department'), id=faculty_id)
    weekly_slots = AvailabilitySlot.objects.filter(faculty=faculty, is_active=True).order_by('day_of_week', 'start_time')
    categories = Category.objects.filter(is_active=True)

    return render(request, 'directory/faculty_detail.html', {
        'faculty': faculty,
        'weekly_slots': weekly_slots,
        'categories': categories,
    })
