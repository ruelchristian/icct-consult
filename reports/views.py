import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from bookings.models import Booking
from directory.models import Department, FacultyProfile, Category
from .services import generate_consultation_pdf

@login_required
def report_dashboard_view(request):
    """
    Department head, Admin, and Faculty reporting dashboard.
    Faculty members can view their own analytics; admins can view department-wide.
    """
    user = request.user
    if not user.is_faculty and not user.is_department_admin:
        messages.error(request, "Access restricted to faculty and department administrators.")
        return redirect('core:home')

    # Base Queryset
    bookings_qs = Booking.objects.select_related('student__user', 'faculty__user', 'category', 'faculty__department')

    if user.is_faculty and not user.is_department_admin:
        faculty = getattr(user, 'faculty_profile', None)
        bookings_qs = bookings_qs.filter(faculty=faculty)

    # Filters
    dept_id = request.GET.get('dept', '')
    status = request.GET.get('status', '')
    category_id = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if dept_id and user.is_department_admin:
        bookings_qs = bookings_qs.filter(faculty__department_id=dept_id)

    if status:
        bookings_qs = bookings_qs.filter(status=status)

    if category_id:
        bookings_qs = bookings_qs.filter(category_id=category_id)

    if date_from:
        bookings_qs = bookings_qs.filter(date__gte=date_from)

    if date_to:
        bookings_qs = bookings_qs.filter(date__lte=date_to)

    total_count = bookings_qs.count()
    completed_count = bookings_qs.filter(status=Booking.Status.COMPLETED).count()
    no_show_count = bookings_qs.filter(status=Booking.Status.NO_SHOW).count()
    confirmed_count = bookings_qs.filter(status=Booking.Status.CONFIRMED).count()
    pending_count = bookings_qs.filter(status=Booking.Status.PENDING).count()

    completion_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 0
    no_show_rate = round((no_show_count / total_count * 100), 1) if total_count > 0 else 0

    departments = Department.objects.all()
    categories = Category.objects.filter(is_active=True)

    return render(request, 'reports/report_dashboard.html', {
        'bookings': bookings_qs.order_by('-date', '-start_time')[:100],
        'total_count': total_count,
        'completed_count': completed_count,
        'no_show_count': no_show_count,
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'completion_rate': completion_rate,
        'no_show_rate': no_show_rate,
        'departments': departments,
        'categories': categories,
        'selected_dept': dept_id,
        'selected_status': status,
        'selected_category': category_id,
        'date_from': date_from,
        'date_to': date_to,
        'statuses': Booking.Status.choices,
    })

@login_required
def export_pdf_view(request):
    """
    Exports filtered consultation records to a downloadable PDF document.
    """
    user = request.user
    if not user.is_faculty and not user.is_department_admin:
        return HttpResponseForbidden("Access denied.")

    bookings_qs = Booking.objects.select_related('student__user', 'faculty__user', 'category', 'faculty__department')

    dept_name = "All Departments"
    if user.is_faculty and not user.is_department_admin:
        faculty = getattr(user, 'faculty_profile', None)
        bookings_qs = bookings_qs.filter(faculty=faculty)
        dept_name = faculty.department.name if faculty and faculty.department else "Faculty Consultations"

    # Apply same filters
    dept_id = request.GET.get('dept', '')
    status = request.GET.get('status', '')
    category_id = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if dept_id and user.is_department_admin:
        dept = Department.objects.filter(id=dept_id).first()
        if dept:
            dept_name = dept.name
        bookings_qs = bookings_qs.filter(faculty__department_id=dept_id)

    if status:
        bookings_qs = bookings_qs.filter(status=status)

    if category_id:
        bookings_qs = bookings_qs.filter(category_id=category_id)

    if date_from:
        bookings_qs = bookings_qs.filter(date__gte=date_from)

    if date_to:
        bookings_qs = bookings_qs.filter(date__lte=date_to)

    pdf_buffer = generate_consultation_pdf(
        bookings_qs.order_by('-date', '-start_time'),
        title="Faculty Consultation Summary Report",
        department_name=dept_name
    )

    filename = f"ICCT_Consultation_Report_{timezone.localdate().strftime('%Y%m%d')}.pdf"
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
