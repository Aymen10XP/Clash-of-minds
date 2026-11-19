"""Generate editable Word versions of the professor-facing project documents."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output' / 'docx'
EVALUATION_DATE = '19 November 2026'

SOURCES = [
    {
        'path': ROOT / 'docs' / 'FINAL_PROJECT_REPORT.md',
        'output': 'Final_Project_Report.docx',
        'title': 'Clash of Minds Final Design and Delivery Report',
        'subtitle': 'Architecture functional coverage test evidence and delivery inventory',
    },
    {
        'path': ROOT / 'docs' / 'PROJECT_DESIGN.md',
        'output': 'Project_Design.docx',
        'title': 'Clash of Minds Project Design',
        'subtitle': 'Architecture data model access boundaries and technology choices',
    },
    {
        'path': ROOT / 'docs' / 'TRACEABILITY_MATRIX.md',
        'output': 'Requirements_Traceability_Matrix.docx',
        'title': 'Clash of Minds Requirements Traceability Matrix',
        'subtitle': 'Requirement implementation test result and evidence mapping',
    },
    {
        'path': ROOT / 'docs' / 'ISO25010_COMPLIANCE_REPORT.md',
        'output': 'ISO25010_Compliance_Report.docx',
        'title': 'Clash of Minds ISO IEC 25010 Quality Evaluation',
        'subtitle': 'Measured evaluation against the eight product quality characteristics',
    },
    {
        'path': ROOT / 'docs' / 'TESTING_AND_CODE_COMMENTS.md',
        'output': 'Testing_and_Code_Documentation.docx',
        'title': 'Clash of Minds Testing and Code Documentation',
        'subtitle': 'Test layers commands measured results and documentation conventions',
    },
    {
        'path': ROOT / 'docs' / 'INSTALLATION_AND_EXECUTION_GUIDE.md',
        'output': 'Installation_and_Execution_Guide.docx',
        'title': 'Clash of Minds Installation and Execution Guide',
        'subtitle': 'Reproducible local installation execution and evidence generation',
    },
    {
        'path': ROOT / 'docs' / 'LIVE_DEMONSTRATION_GUIDE.md',
        'output': 'Live_Demonstration_Guide.docx',
        'title': 'Clash of Minds Live Demonstration Guide',
        'subtitle': 'Concise presentation sequence speaking notes and backup plan',
    },
    {
        'path': ROOT / 'reports' / 'README.md',
        'output': 'Generated_Evidence_Inventory.docx',
        'title': 'Clash of Minds Evidence Inventory',
        'subtitle': 'Generated quality evidence locations reproduction commands and interpretation',
    },
]

NAVY = '17365D'
PALE_BLUE = 'EAF1F8'
LIGHT_GRAY = 'F2F2F2'
GRID = 'D9D9D9'
TEXT = RGBColor(0, 0, 0)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = tc_pr.find(qn('w:shd'))
    if shading is None:
        shading = OxmlElement('w:shd')
        tc_pr.append(shading)
    shading.set(qn('w:fill'), fill)


def set_cell_margins(cell, top=90, start=110, bottom=90, end=110) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in('w:tcMar')
    if tc_mar is None:
        tc_mar = OxmlElement('w:tcMar')
        tc_pr.append(tc_mar)
    for margin, value in [('top', top), ('start', start), ('bottom', bottom), ('end', end)]:
        node = tc_mar.find(qn(f'w:{margin}'))
        if node is None:
            node = OxmlElement(f'w:{margin}')
            tc_mar.append(node)
        node.set(qn('w:w'), str(value))
        node.set(qn('w:type'), 'dxa')


def set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn('w:tblBorders'))
    if borders is None:
        borders = OxmlElement('w:tblBorders')
        tbl_pr.append(borders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        element = borders.find(qn(f'w:{edge}'))
        if element is None:
            element = OxmlElement(f'w:{edge}')
            borders.append(element)
        element.set(qn('w:val'), 'single')
        element.set(qn('w:sz'), '5')
        element.set(qn('w:color'), GRID)


def repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement('w:tblHeader')
    header.set(qn('w:val'), 'true')
    tr_pr.append(header)


def set_paragraph_shading(paragraph, fill: str) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    shading = p_pr.find(qn('w:shd'))
    if shading is None:
        shading = OxmlElement('w:shd')
        p_pr.append(shading)
    shading.set(qn('w:fill'), fill)


def set_keep_with_next(paragraph, enabled=True) -> None:
    paragraph.paragraph_format.keep_with_next = enabled


def set_repeat_table_layout(table) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    if table.rows:
        repeat_table_header(table.rows[0])


def add_page_field(paragraph) -> None:
    run = paragraph.add_run('Page ')
    run.font.size = Pt(8)
    begin = OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')
    instruction = OxmlElement('w:instrText')
    instruction.set(qn('xml:space'), 'preserve')
    instruction.text = ' PAGE '
    separate = OxmlElement('w:fldChar')
    separate.set(qn('w:fldCharType'), 'separate')
    text = OxmlElement('w:t')
    text.text = '1'
    end = OxmlElement('w:fldChar')
    end.set(qn('w:fldCharType'), 'end')
    run._r.extend([begin, instruction, separate, text, end])


def sanitize_heading(value: str) -> str:
    value = re.sub(r'`([^`]+)`', r'\1', value)
    value = re.sub(r'\[([^]]+)]\([^)]*\)', r'\1', value)
    value = value.replace('&', ' and ').replace('/', ' ').replace('-', ' ')
    value = re.sub(r'[^A-Za-z0-9 ]+', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()


def clean_inline(value: str) -> str:
    value = re.sub(r'\[([^]]+)]\(([^)]+)\)', r'\1 (\2)', value)
    return value.replace('&#8262;', '-').replace('&#8226;', '-')


INLINE_PATTERN = re.compile(r'(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)')


def add_inline(paragraph, value: str, *, base_font='Aptos', base_size=10.5) -> None:
    value = clean_inline(value)
    cursor = 0
    for match in INLINE_PATTERN.finditer(value):
        if match.start() > cursor:
            run = paragraph.add_run(value[cursor:match.start()])
            run.font.name = base_font
            run.font.size = Pt(base_size)
        token = match.group(0)
        if token.startswith('**'):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith('`'):
            run = paragraph.add_run(token[1:-1])
            run.font.name = 'Consolas'
            run._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), 'Consolas')
            run._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), 'Consolas')
        else:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        run.font.size = Pt(base_size)
        cursor = match.end()
    if cursor < len(value):
        run = paragraph.add_run(value[cursor:])
        run.font.name = base_font
        run.font.size = Pt(base_size)


def configure_document(document: Document, title: str) -> None:
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    normal = document.styles['Normal']
    normal.font.name = 'Aptos'
    normal._element.rPr.rFonts.set(qn('w:ascii'), 'Aptos')
    normal._element.rPr.rFonts.set(qn('w:hAnsi'), 'Aptos')
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = TEXT
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08

    title_style = document.styles['Title']
    title_style.font.name = 'Aptos Display'
    title_style.font.size = Pt(26)
    title_style.font.bold = True
    title_style.font.color.rgb = TEXT
    title_style.paragraph_format.space_after = Pt(10)
    title_style.paragraph_format.keep_with_next = True
    title_p_pr = title_style.element.get_or_add_pPr()
    title_border = title_p_pr.find(qn('w:pBdr'))
    if title_border is not None:
        title_p_pr.remove(title_border)

    for name, size, before, after in [
        ('Heading 1', 16, 14, 6),
        ('Heading 2', 13, 11, 5),
        ('Heading 3', 11, 9, 4),
    ]:
        style = document.styles[name]
        style.font.name = 'Aptos Display'
        style._element.rPr.rFonts.set(qn('w:ascii'), 'Aptos Display')
        style._element.rPr.rFonts.set(qn('w:hAnsi'), 'Aptos Display')
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = TEXT
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for list_style in ('List Bullet', 'List Number'):
        style = document.styles[list_style]
        style.font.name = 'Aptos'
        style.font.size = Pt(10.5)
        style.paragraph_format.left_indent = Inches(0.25)
        style.paragraph_format.first_line_indent = Inches(-0.16)
        style.paragraph_format.space_after = Pt(3)

    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(3)
    add_page_field(paragraph)
    for run in paragraph.runs:
        run.font.name = 'Aptos'
        run.font.color.rgb = RGBColor(89, 89, 89)

    document.core_properties.title = title
    document.core_properties.author = 'Clash of Minds project team'
    document.core_properties.subject = 'ISO IEC 25010 academic project evidence'
    document.core_properties.keywords = 'ISO 25010, testing, quality, Clash of Minds'


def add_document_title(document: Document, title: str, subtitle: str) -> None:
    title_paragraph = document.add_paragraph(style='Title')
    title_paragraph.add_run(title)
    subtitle_paragraph = document.add_paragraph()
    subtitle_paragraph.paragraph_format.space_after = Pt(4)
    subtitle_run = subtitle_paragraph.add_run(subtitle)
    subtitle_run.font.name = 'Aptos'
    subtitle_run.font.size = Pt(12)
    subtitle_run.font.color.rgb = RGBColor(64, 64, 64)
    date_paragraph = document.add_paragraph()
    date_paragraph.paragraph_format.space_after = Pt(16)
    date_run = date_paragraph.add_run(f'Evaluation date  {EVALUATION_DATE}')
    date_run.font.name = 'Aptos'
    date_run.font.size = Pt(9)
    date_run.font.color.rgb = RGBColor(89, 89, 89)


def add_code_block(document: Document, lines: list[str]) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.18)
    paragraph.paragraph_format.right_indent = Inches(0.12)
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(8)
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    set_paragraph_shading(paragraph, LIGHT_GRAY)
    run = paragraph.add_run('\n'.join(lines))
    run.font.name = 'Consolas'
    run._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), 'Consolas')
    run._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), 'Consolas')
    run.font.size = Pt(8.5)


def add_table(document: Document, rows: list[list[str]]) -> None:
    if len(rows) > 1 and all(re.fullmatch(r':?-{3,}:?', cell.strip()) for cell in rows[1]):
        rows = [rows[0], *rows[2:]]
    columns = max(len(row) for row in rows)
    normalized = [row + [''] * (columns - len(row)) for row in rows]
    table = document.add_table(rows=len(normalized), cols=columns)
    set_repeat_table_layout(table)
    width_patterns = {
        2: [0.34, 0.66],
        3: [0.22, 0.35, 0.43],
        4: [0.12, 0.29, 0.29, 0.30],
        5: [0.10, 0.20, 0.27, 0.20, 0.23],
    }
    fractions = width_patterns.get(columns, [1 / columns] * columns)
    total_width = 6.9
    for row_index, values in enumerate(normalized):
        for column_index, value in enumerate(values):
            cell = table.cell(row_index, column_index)
            cell.width = Inches(total_width * fractions[column_index])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            cell.text = ''
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            add_inline(paragraph, value.strip(), base_size=8.3)
            if row_index == 0:
                set_cell_shading(cell, NAVY)
                for run in paragraph.runs:
                    run.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
            elif row_index % 2 == 0:
                set_cell_shading(cell, PALE_BLUE)
    document.add_paragraph().paragraph_format.space_after = Pt(1)


def add_markdown(document: Document, source: Path, *, skip_title=True) -> None:
    lines = source.read_text(encoding='utf-8').splitlines()
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    table_rows: list[list[str]] = []
    in_code = False
    first_heading_seen = False

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        paragraph = document.add_paragraph()
        add_inline(paragraph, ' '.join(part.strip() for part in paragraph_lines))
        paragraph_lines.clear()

    def flush_table() -> None:
        if table_rows:
            add_table(document, table_rows[:])
            table_rows.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith('```'):
            flush_paragraph()
            flush_table()
            if in_code:
                add_code_block(document, code_lines)
                code_lines.clear()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
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
            if not first_heading_seen:
                first_heading_seen = True
                if skip_title:
                    continue
            level = min(len(heading.group(1)), 3)
            document.add_paragraph(sanitize_heading(heading.group(2)), style=f'Heading {level}')
            continue
        if line.startswith('> '):
            flush_paragraph()
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.28)
            paragraph.paragraph_format.right_indent = Inches(0.12)
            paragraph.paragraph_format.space_after = Pt(8)
            add_inline(paragraph, line[2:])
            for run in paragraph.runs:
                run.italic = True
            continue
        bullet = re.match(r'^\s*[-*]\s+(.+)$', line)
        numbered = re.match(r'^\s*(\d+)\.\s+(.+)$', line)
        if bullet or numbered:
            flush_paragraph()
            if bullet:
                paragraph = document.add_paragraph(style='List Bullet')
                add_inline(paragraph, bullet.group(1))
            else:
                paragraph = document.add_paragraph()
                paragraph.paragraph_format.left_indent = Inches(0.25)
                paragraph.paragraph_format.first_line_indent = Inches(-0.20)
                paragraph.paragraph_format.space_after = Pt(3)
                number_run = paragraph.add_run(f'{numbered.group(1)}.  ')
                number_run.font.size = Pt(10.5)
                add_inline(paragraph, numbered.group(2))
            continue
        paragraph_lines.append(line.strip())

    flush_paragraph()
    flush_table()
    if code_lines:
        add_code_block(document, code_lines)


def add_cover_metadata(document: Document) -> None:
    table = document.add_table(rows=4, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    values = [
        ('Scope', 'Design traceability quality evidence installation and live defense'),
        ('Evaluation date', EVALUATION_DATE),
        ('Application', 'Ionic React Django PostgreSQL'),
        ('Evidence status', 'Generated from recorded local executions'),
    ]
    for index, (label, value) in enumerate(values):
        left, right = table.rows[index].cells
        left.width = Inches(1.7)
        right.width = Inches(4.7)
        left.text = label
        right.text = value
        set_cell_shading(left, NAVY)
        set_cell_shading(right, PALE_BLUE if index % 2 == 0 else 'FFFFFF')
        for run in left.paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
        for cell in (left, right):
            set_cell_margins(cell, top=110, bottom=110)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_table_borders(table)


def build_individual(source: dict) -> Path:
    document = Document()
    configure_document(document, source['title'])
    add_document_title(document, source['title'], source['subtitle'])
    add_markdown(document, source['path'])
    path = OUTPUT / source['output']
    document.save(path)
    return path


def build_combined() -> Path:
    title = 'Clash of Minds ISO IEC 25010 Final Dossier'
    document = Document()
    configure_document(document, title)

    document.add_paragraph(title, style='Title')
    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = subtitle.add_run('Editable Word submission for academic review')
    run.font.name = 'Aptos'
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(64, 64, 64)
    document.add_paragraph().paragraph_format.space_after = Pt(10)
    add_cover_metadata(document)
    note = document.add_paragraph()
    note.paragraph_format.space_before = Pt(16)
    note.paragraph_format.space_after = Pt(0)
    add_inline(
        note,
        'This dossier consolidates the project design, traceability, ISO IEC 25010 evaluation, '
        'test evidence, installation procedure, live demonstration plan, and evidence inventory. '
        'All text and tables remain editable in Microsoft Word.',
    )

    document.add_page_break()
    document.add_paragraph('Dossier Contents', style='Heading 1')
    for number, source in enumerate(SOURCES, start=1):
        paragraph = document.add_paragraph(style='List Number')
        paragraph.style = document.styles['List Number']
        add_inline(paragraph, source['title'])

    for index, source in enumerate(SOURCES, start=1):
        # The final evidence inventory follows the short backup-plan ending on the
        # same page; forcing another break would leave an almost-empty page.
        if index != len(SOURCES):
            document.add_page_break()
        document.add_paragraph(f'Part {index} {source["title"]}', style='Heading 1')
        intro = document.add_paragraph()
        intro.paragraph_format.space_after = Pt(12)
        run = intro.add_run(source['subtitle'])
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(64, 64, 64)
        add_markdown(document, source['path'])

    path = OUTPUT / 'Clash_of_Minds_ISO25010_Final_Dossier.docx'
    document.save(path)
    return path


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    outputs = [build_individual(source) for source in SOURCES]
    outputs.append(build_combined())
    for path in outputs:
        print(path)


if __name__ == '__main__':
    main()
