from django.urls import path
from .views import report_dashboard_view, export_pdf_view

app_name = 'reports'

urlpatterns = [
    path('', report_dashboard_view, name='dashboard'),
    path('export/pdf/', export_pdf_view, name='export_pdf'),
]
