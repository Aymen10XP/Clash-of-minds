"""Build the professor-facing ISO 25010 dossier from the maintained Markdown reports."""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output' / 'pdf' / 'Clash_of_Minds_ISO25010_Final_Report.pdf'
SOURCES = [
    ROOT / 'docs' / 'FINAL_PROJECT_REPORT.md',
    ROOT / 'docs' / 'TRACEABILITY_MATRIX.md',
    ROOT / 'docs' / 'ISO25010_COMPLIANCE_REPORT.md',
    ROOT / 'docs' / 'INSTALLATION_AND_EXECUTION_GUIDE.md',
    ROOT / 'docs' / 'LIVE_DEMONSTRATION_GUIDE.md',
]


def inline_markup(value: str) -> str:
    """Convert the small Markdown subset used by the reports into ReportLab markup."""
    value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    value = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
    value = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', value)
    return value


def page_decoration(canvas, document):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor('#D4A72C'))
    canvas.setLineWidth(1)
    canvas.line(18 * mm, height - 16 * mm, width - 18 * mm, height - 16 * mm)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#5B6472'))
    canvas.drawString(18 * mm, 10 * mm, 'Clash of Minds - ISO/IEC 25010 academic evidence')
    canvas.drawRightString(width - 18 * mm, 10 * mm, f'Page {document.page}')
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='CoverTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=30,
    leading=34, textColor=colors.HexColor('#10233F'), alignment=TA_CENTER, spaceAfter=10 * mm,
))
styles.add(ParagraphStyle(
    name='CoverSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=14,
    leading=19, textColor=colors.HexColor('#41536D'), alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name='DocH1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20,
    leading=24, textColor=colors.HexColor('#10233F'), spaceBefore=4 * mm, spaceAfter=4 * mm,
))
styles.add(ParagraphStyle(
    name='DocH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14,
    leading=18, textColor=colors.HexColor('#1E5A7A'), spaceBefore=4 * mm, spaceAfter=2 * mm,
))
styles.add(ParagraphStyle(
    name='DocH3', parent=styles['Heading3'], fontName='Helvetica-Bold', fontSize=11,
    leading=14, textColor=colors.HexColor('#6B4E00'), spaceBefore=3 * mm, spaceAfter=1.5 * mm,
))
styles.add(ParagraphStyle(
    name='BodySmall', parent=styles['BodyText'], fontName='Helvetica', fontSize=8.8,
    leading=12, textColor=colors.HexColor('#202A36'), spaceAfter=2.2 * mm,
))
styles.add(ParagraphStyle(
    name='BulletSmall', parent=styles['BodyText'], fontName='Helvetica', fontSize=8.8,
    leading=12, leftIndent=5 * mm, firstLineIndent=-3 * mm, bulletIndent=1 * mm,
    textColor=colors.HexColor('#202A36'), spaceAfter=1.2 * mm,
))
styles.add(ParagraphStyle(
    name='Quote', parent=styles['BodyText'], fontName='Helvetica-Oblique', fontSize=9,
    leading=12, leftIndent=6 * mm, rightIndent=4 * mm, borderColor=colors.HexColor('#D4A72C'),
    borderWidth=1, borderPadding=3, textColor=colors.HexColor('#324156'), spaceAfter=2 * mm,
))


def markdown_story(path: Path):
    lines = path.read_text(encoding='utf-8').splitlines()
    story = []
    paragraph = []
    code = []
    in_code = False
    table_rows = []

    def flush_paragraph():
        if paragraph:
            story.append(Paragraph(inline_markup(' '.join(paragraph)), styles['BodySmall']))
            paragraph.clear()

    def flush_table():
        if not table_rows:
            return
        rows = table_rows[:]
        table_rows.clear()
        if len(rows) > 1 and all(re.fullmatch(r':?-{3,}:?', cell.strip()) for cell in rows[1]):
            rows.pop(1)
        rendered = [[Paragraph(inline_markup(cell.strip()), styles['BodySmall']) for cell in row] for row in rows]
        available = 174 * mm
        column_count = max(len(row) for row in rendered)
        widths = [available / column_count] * column_count
        table = Table(rendered, colWidths=widths, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8EEF5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#10233F')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#AEB8C5')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7F9FC')]),
        ]))
        story.extend([table, Spacer(1, 3 * mm)])

    for line in lines:
        if line.startswith('```'):
            flush_paragraph()
            flush_table()
            if in_code:
                story.append(Preformatted('\n'.join(code), ParagraphStyle(
                    name='CodeBlock', fontName='Courier', fontSize=7.2, leading=9,
                    leftIndent=3 * mm, rightIndent=3 * mm, borderColor=colors.HexColor('#CBD4E0'),
                    borderWidth=0.5, borderPadding=5, backColor=colors.HexColor('#F4F6F8'),
                    spaceAfter=3 * mm,
                )))
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith('|') and line.endswith('|'):
            flush_paragraph()
            table_rows.append([cell.strip() for cell in line.strip('|').split('|')])
            continue
        flush_table()
        if not line.strip():
            flush_paragraph()
            continue
        heading = re.match(r'^(#{1,3})\s+(.+)$', line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            story.append(Paragraph(inline_markup(heading.group(2)), styles[f'DocH{level}']))
            continue
        if line.startswith('> '):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), styles['Quote']))
            continue
        bullet = re.match(r'^\s*[-*]\s+(.+)$', line)
        numbered = re.match(r'^\s*(\d+)\.\s+(.+)$', line)
        if bullet or numbered:
            flush_paragraph()
            marker = '\u2022' if bullet else f'{numbered.group(1)}.'
            content = bullet.group(1) if bullet else numbered.group(2)
            story.append(Paragraph(inline_markup(content), styles['BulletSmall'], bulletText=marker))
            continue
        paragraph.append(line.strip())

    flush_paragraph()
    flush_table()
    return story


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=22 * mm, bottomMargin=17 * mm,
        title='Clash of Minds ISO/IEC 25010 Final Report',
        author='Clash of Minds project team',
        subject='Design, traceability, compliance evidence, installation, and live demonstration guide',
    )
    story = [
        Spacer(1, 42 * mm),
        Paragraph('CLASH OF MINDS', styles['CoverTitle']),
        Paragraph('ISO/IEC 25010 Final Project Dossier', styles['CoverSubtitle']),
        Spacer(1, 10 * mm),
        Table([
            ['Scope', 'Design, traceability, quality evidence, installation, live defense'],
            ['Evaluation date', '19 November 2026'],
            ['Application', 'Ionic/React + Django + PostgreSQL'],
            ['Evidence status', 'Generated from real local executions'],
        ], colWidths=[42 * mm, 105 * mm], style=[
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#10233F')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F0F4F8')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#AEB8C5')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 7),
        ]),
        Spacer(1, 14 * mm),
        Paragraph(
            'Academic quality evaluation against the eight product-quality characteristics requested in the professor\'s brief. This dossier does not claim formal ISO certification.',
            ParagraphStyle(name='CoverNote', parent=styles['BodyText'], fontSize=10, leading=15,
                           alignment=TA_CENTER, textColor=colors.HexColor('#41536D')),
        ),
        PageBreak(),
        Paragraph('Dossier contents', styles['DocH1']),
    ]
    titles = [
        'Part I - Final design and delivery report',
        'Part II - Requirements traceability matrix',
        'Part III - ISO/IEC 25010 quality evaluation',
        'Part IV - Installation and execution guide',
        'Part V - Concise live demonstration guide',
    ]
    for title in titles:
        story.append(Paragraph(title, styles['DocH2']))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        'Raw machine-readable and HTML evidence is stored under reports/. The command npm run evidence:full regenerates the core evidence package.',
        styles['Quote'],
    ))

    for title, source in zip(titles, SOURCES):
        story.extend([PageBreak(), Paragraph(title, styles['DocH1']), Spacer(1, 2 * mm)])
        source_story = markdown_story(source)
        if source_story and isinstance(source_story[0], Paragraph):
            source_story = source_story[1:]
        story.extend(source_story)

    document.build(story, onFirstPage=page_decoration, onLaterPages=page_decoration)
    print(OUTPUT)


if __name__ == '__main__':
    build()
