from django.contrib import admin
from .models import Department, Category, FacultyProfile, StudentProfile

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_duration_minutes', 'is_private', 'is_active')
    list_filter = ('is_private', 'is_active')
    search_fields = ('name',)

@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'title', 'office_location')
    list_filter = ('department', 'title')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__email')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_number', 'user', 'department', 'program', 'year_level', 'section')
    list_filter = ('department', 'year_level', 'program')
    search_fields = ('student_number', 'user__first_name', 'user__last_name', 'user__email')
