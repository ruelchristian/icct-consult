import io
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from bookings.models import Booking

# Exact ICCT Brand Colors (Extracted from icct.edu.ph)
ICCT_NAVY = colors.HexColor("#0A315A")      # Main Brand Navy Blue
ICCT_GOLD = colors.HexColor("#FAD35F")      # Official Brand Yellow / Gold
ICCT_DARK = colors.HexColor("#0B233B")      # Midnight Topbar Navy
ICCT_RED = colors.HexColor("#C8102E")       # Official Seal Red Accent
ICCT_LIGHT = colors.HexColor("#F4F7FA")     # Background Tint

def generate_consultation_pdf(bookings_qs, title="Consultation Summary Report", department_name="All Departments"):
    """
    Generates a professional PDF consultation report matching ICCT Colleges branding.
    Returns a BytesIO buffer containing the PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    header_style = ParagraphStyle(
        'HeaderInstitution',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=ICCT_NAVY,
        alignment=1, # Center
        spaceAfter=2,
    )
    sub_header_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=ICCT_DARK,
        alignment=1,
        spaceAfter=3,
    )
    motto_style = ParagraphStyle(
        'Motto',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
        spaceAfter=10,
    )
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=ICCT_NAVY,
        alignment=1,
        spaceAfter=14,
    )
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        textColor=colors.dimgrey,
        spaceAfter=10,
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
    )
    cell_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.whitesmoke,
    )

    story = []

    # 1. Official Institution Header
    story.append(Paragraph("ICCT COLLEGES FOUNDATION INC.", header_style))
    story.append(Paragraph("OFFICE OF ACADEMIC AFFAIRS · FACULTY CONSULTATION SYSTEM", sub_header_style))
    story.append(Paragraph("A Global Pinoy Distinction · ISO 9001:2015 Certified", motto_style))
    story.append(Paragraph(title.upper(), title_style))
    
    # Meta Info
    now_str = timezone.localtime().strftime("%B %d, %Y - %I:%M %p")
    meta_text = f"<b>Department:</b> {department_name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Generated:</b> {now_str} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Total Records:</b> {bookings_qs.count()}"
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 8))

    # 2. Statistics Summary Table
    total = bookings_qs.count()
    completed = bookings_qs.filter(status=Booking.Status.COMPLETED).count()
    no_show = bookings_qs.filter(status=Booking.Status.NO_SHOW).count()
    confirmed = bookings_qs.filter(status=Booking.Status.CONFIRMED).count()
    pending = bookings_qs.filter(status=Booking.Status.PENDING).count()
    cancelled = bookings_qs.filter(status=Booking.Status.CANCELLED).count()

    stats_data = [
        [
            Paragraph("<b>Total Bookings</b>", cell_style),
            Paragraph("<b>Completed</b>", cell_style),
            Paragraph("<b>Confirmed / Active</b>", cell_style),
            Paragraph("<b>No-Shows</b>", cell_style),
            Paragraph("<b>Pending</b>", cell_style),
            Paragraph("<b>Cancelled / Declined</b>", cell_style),
        ],
        [
            Paragraph(f"<font size=11><b>{total}</b></font>", cell_style),
            Paragraph(f"<font size=11 color='#1b7a2d'><b>{completed}</b></font>", cell_style),
            Paragraph(f"<font size=11 color='#0a315a'><b>{confirmed}</b></font>", cell_style),
            Paragraph(f"<font size=11 color='#c8102e'><b>{no_show}</b></font>", cell_style),
            Paragraph(f"<font size=11 color='#d97706'><b>{pending}</b></font>", cell_style),
            Paragraph(f"<font size=11 color='#6b7280'><b>{cancelled}</b></font>", cell_style),
        ]
    ]

    stats_table = Table(stats_data, colWidths=[1.4 * inch, 1.1 * inch, 1.4 * inch, 1.1 * inch, 1.1 * inch, 1.4 * inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ICCT_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, ICCT_NAVY),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 15))

    # 3. Main Bookings Log Table
    table_headers = [
        Paragraph("Date & Time", cell_header),
        Paragraph("Student", cell_header),
        Paragraph("Faculty Member", cell_header),
        Paragraph("Category", cell_header),
        Paragraph("Mode", cell_header),
        Paragraph("Status", cell_header),
    ]

    table_rows = [table_headers]

    for b in bookings_qs[:250]: # Safety limit on single export
        date_time_str = f"{b.date.strftime('%b %d, %Y')}<br/>{b.start_time.strftime('%I:%M%p')}-{b.end_time.strftime('%I:%M%p')}"
        student_str = f"{b.student.user.get_full_name()}<br/><font color='grey'>{b.student.student_number}</font>"
        faculty_str = f"{b.faculty.user.get_full_name()}<br/><font color='grey'>{b.faculty.department.code if b.faculty.department else ''}</font>"
        
        status_color = "#1b7a2d" if b.status == Booking.Status.COMPLETED else ("#c8102e" if b.status == Booking.Status.NO_SHOW else "#0a315a")
        status_str = f"<font color='{status_color}'><b>{b.get_status_display()}</b></font>"

        table_rows.append([
            Paragraph(date_time_str, cell_style),
            Paragraph(student_str, cell_style),
            Paragraph(faculty_str, cell_style),
            Paragraph(b.category.name, cell_style),
            Paragraph(b.get_mode_display(), cell_style),
            Paragraph(status_str, cell_style),
        ])

    table = Table(table_rows, colWidths=[1.3 * inch, 1.6 * inch, 1.6 * inch, 1.3 * inch, 0.9 * inch, 1.1 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ICCT_NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 25))

    # 4. Verification & Sign-off Block
    sign_data = [
        [
            Paragraph("Prepared by:<br/><br/><br/>_____________________________________<br/>Consultation System Administrator", cell_style),
            Paragraph("Noted by:<br/><br/><br/>_____________________________________<br/>Dean / Department Head", cell_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[3.7 * inch, 3.7 * inch])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(KeepTogether([sign_table]))

    doc.build(story)
    buffer.seek(0)
    return buffer
