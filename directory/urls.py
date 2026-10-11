from django.urls import path
from .views import faculty_directory_view, faculty_detail_view

app_name = 'directory'

urlpatterns = [
    path('faculty/', faculty_directory_view, name='faculty_list'),
    path('faculty/<int:faculty_id>/', faculty_detail_view, name='faculty_detail'),
]
