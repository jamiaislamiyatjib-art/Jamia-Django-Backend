

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
import os


def generate_official_marksheet(student, logo_path=None):
    """
    Generates a professional PDF marksheet with optional school logo.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)

    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        alignment=1,  # center
        fontSize=22,
        leading=28,
        textColor=colors.darkblue
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceAfter=6
    )
    normal_style = styles['Normal']

    content = []

    # --- School Logo ---
    if logo_path and os.path.exists(logo_path):
        img = Image(logo_path, width=80, height=80)
        img.hAlign = 'CENTER'
        content.append(img)
        content.append(Spacer(1, 12))

    # --- School Name ---
    content.append(Paragraph("XYZ INTERNATIONAL SCHOOL", title_style))
    content.append(Paragraph("Official Marksheet", header_style))
    content.append(Spacer(1, 20))

    # --- Student Info ---
    student_info_data = [
        ['Name:', student.student_name],
        ['Roll No:', student.roll_no],
        ['Class:', student.student_class],
        ['Session:', student.session],
        ['Medium:', student.medium],
        ['Center:', student.center.center_name if student.center else '-']
    ]

    student_info_table = Table(student_info_data, colWidths=[100, 300], hAlign='LEFT')
    student_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(student_info_table)
    content.append(Spacer(1, 20))

    # --- Marks Table ---
    table_data = [
        ['Subject', 'Marks Obtained'],
        ['Paper 1', student.paper1 if student.paper1 is not None else '-'],
        ['Paper 2', student.paper2 if student.paper2 is not None else '-'],
        ['Paper 3', student.paper3 if student.paper3 is not None else '-'],
        ['Paper 4', student.paper4 if student.paper4 is not None else '-'],
        ['Total', student.total],
        ['Percentage', f"{student.avg_percentage:.2f}%" if student.avg_percentage is not None else '-'],
        ['Result', student.result or '-'],
        ['Division', student.division or '-'],
    ]

    marks_table = Table(table_data, colWidths=[250, 150], hAlign='CENTER')
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))

    content.append(marks_table)
    content.append(Spacer(1, 40))

    # --- Footer Signatures ---
    footer_data = [
        ['________________________', '', '________________________'],
        ['Class Teacher', '', 'Principal']
    ]
    footer_table = Table(footer_data, colWidths=[200, 50, 200], hAlign='CENTER')
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12)
    ]))
    content.append(footer_table)

    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer
