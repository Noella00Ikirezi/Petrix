"""Export service for SMSI documents - Multi-format support."""
import io
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, BinaryIO
from pathlib import Path
import uuid

from loguru import logger

from app.infrastructure.database.smsi_models import GeneratedDocument, DocumentType


class ExportService:
    """Service for exporting documents to multiple formats."""

    SUPPORTED_FORMATS = ["md", "html", "docx", "pdf", "xlsx", "csv", "pptx"]

    async def export_document(
        self,
        document: GeneratedDocument,
        format: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export a document to the specified format."""
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.SUPPORTED_FORMATS}")

        export_methods = {
            "md": self._export_markdown,
            "html": self._export_html,
            "docx": self._export_docx,
            "pdf": self._export_pdf,
            "xlsx": self._export_xlsx,
            "csv": self._export_csv,
            "pptx": self._export_pptx,
        }

        try:
            content, filename = await export_methods[format](document)

            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(content)
                return {
                    "success": True,
                    "format": format,
                    "filename": filename,
                    "path": output_path,
                    "size": len(content)
                }

            return {
                "success": True,
                "format": format,
                "filename": filename,
                "content": content,
                "size": len(content)
            }

        except Exception as e:
            logger.error(f"Export error ({format}): {str(e)}")
            return {
                "success": False,
                "format": format,
                "error": str(e)
            }

    async def _export_markdown(self, document: GeneratedDocument) -> tuple[bytes, str]:
        """Export to Markdown format."""
        content = document.content_markdown or ""

        # Add metadata header
        header = f"""---
title: {document.name}
code: {document.code}
version: {document.version}
type: {document.document_type.value}
status: {document.status.value}
generated: {document.created_at.isoformat()}
---

"""
        full_content = header + content
        filename = f"{document.code}_v{document.version}.md"

        return full_content.encode('utf-8'), filename

    async def _export_html(self, document: GeneratedDocument) -> tuple[bytes, str]:
        """Export to HTML format with styling."""
        html_content = document.content_html or self._markdown_to_html(document.content_markdown)

        # Wrap in HTML document with CSS
        full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{document.name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #4facfe; padding-bottom: 10px; }}
        h2 {{ color: #1a1a2e; margin-top: 30px; }}
        h3 {{ color: #555; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4facfe; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .metadata {{
            background-color: #f8f9fa;
            border-left: 4px solid #4facfe;
            padding: 15px;
            margin-bottom: 30px;
        }}
        .metadata p {{ margin: 5px 0; }}
        ul, ol {{ padding-left: 25px; }}
        li {{ margin: 8px 0; }}
        @media print {{
            body {{ max-width: 100%; padding: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="metadata">
        <p><strong>Document:</strong> {document.code}</p>
        <p><strong>Version:</strong> {document.version}</p>
        <p><strong>Type:</strong> {document.document_type.value}</p>
        <p><strong>Statut:</strong> {document.status.value}</p>
        <p><strong>Genere le:</strong> {document.created_at.strftime('%d/%m/%Y %H:%M')}</p>
    </div>
    {html_content}
</body>
</html>"""

        filename = f"{document.code}_v{document.version}.html"
        return full_html.encode('utf-8'), filename

    async def _export_docx(self, document: GeneratedDocument) -> tuple[bytes, str]:
        """Export to DOCX format using python-docx."""
        from docx import Document as DocxDocument
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.style import WD_STYLE_TYPE

        doc = DocxDocument()

        # Set up styles
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)

        # Add header with metadata
        header = doc.sections[0].header
        header_para = header.paragraphs[0]
        header_para.text = f"{document.code} | Version {document.version} | {document.status.value.upper()}"
        header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # Add title
        title = doc.add_heading(document.name, level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add metadata table
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Table Grid'
        cells = [
            ("Code document", document.code),
            ("Version", document.version),
            ("Type", document.document_type.value),
            ("Date de generation", document.created_at.strftime('%d/%m/%Y'))
        ]
        for i, (label, value) in enumerate(cells):
            table.rows[i].cells[0].text = label
            table.rows[i].cells[1].text = str(value)

        doc.add_paragraph()

        # Parse and add content
        self._parse_markdown_to_docx(doc, document.content_markdown or "")

        # Add footer
        footer = doc.sections[0].footer
        footer_para = footer.paragraphs[0]
        footer_para.text = f"Genere par GRC Platform - {datetime.now().strftime('%d/%m/%Y')}"
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Save to bytes
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f"{document.code}_v{document.version}.docx"
        return buffer.getvalue(), filename

    def _parse_markdown_to_docx(self, doc, markdown_content: str):
        """Parse Markdown content and add to DOCX document."""
        from docx.shared import Pt

        lines = markdown_content.split('\n')
        in_table = False
        table_data = []
        in_list = False
        list_items = []

        for line in lines:
            stripped = line.strip()

            # Headers
            if stripped.startswith('# '):
                if in_table:
                    self._add_table_to_docx(doc, table_data)
                    in_table = False
                    table_data = []
                doc.add_heading(stripped[2:], level=1)
            elif stripped.startswith('## '):
                doc.add_heading(stripped[3:], level=2)
            elif stripped.startswith('### '):
                doc.add_heading(stripped[4:], level=3)
            elif stripped.startswith('#### '):
                doc.add_heading(stripped[5:], level=4)

            # Tables
            elif stripped.startswith('|'):
                if not in_table:
                    in_table = True
                if not stripped.replace('|', '').replace('-', '').replace(' ', ''):
                    continue  # Skip separator line
                row = [cell.strip() for cell in stripped.split('|')[1:-1]]
                if row:
                    table_data.append(row)

            # Lists
            elif stripped.startswith('- ') or stripped.startswith('* '):
                text = stripped[2:]
                para = doc.add_paragraph(text, style='List Bullet')
            elif stripped.startswith('1. ') or (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == '.'):
                text = stripped.split('. ', 1)[1] if '. ' in stripped else stripped
                para = doc.add_paragraph(text, style='List Number')

            # Regular paragraphs
            elif stripped:
                if in_table:
                    self._add_table_to_docx(doc, table_data)
                    in_table = False
                    table_data = []
                # Handle bold and italic
                para = doc.add_paragraph()
                self._add_formatted_text(para, stripped)

            # Empty line
            else:
                if in_table:
                    self._add_table_to_docx(doc, table_data)
                    in_table = False
                    table_data = []

        # Handle remaining table
        if in_table and table_data:
            self._add_table_to_docx(doc, table_data)

    def _add_table_to_docx(self, doc, table_data: List[List[str]]):
        """Add a table to the DOCX document."""
        if not table_data:
            return

        rows = len(table_data)
        cols = max(len(row) for row in table_data)

        table = doc.add_table(rows=rows, cols=cols)
        table.style = 'Table Grid'

        for i, row_data in enumerate(table_data):
            for j, cell_text in enumerate(row_data):
                if j < cols:
                    table.rows[i].cells[j].text = cell_text

                    # Bold header row
                    if i == 0:
                        for paragraph in table.rows[i].cells[j].paragraphs:
                            for run in paragraph.runs:
                                run.bold = True

        doc.add_paragraph()

    def _add_formatted_text(self, paragraph, text: str):
        """Add text with basic Markdown formatting to a paragraph."""
        import re

        # Simple pattern for bold and italic
        parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', text)

        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
            elif part.startswith('*') and part.endswith('*') and not part.startswith('**'):
                run = paragraph.add_run(part[1:-1])
                run.italic = True
            elif part.startswith('`') and part.endswith('`'):
                run = paragraph.add_run(part[1:-1])
                run.font.name = 'Consolas'
            else:
                paragraph.add_run(part)

    async def _export_pdf(self, document: GeneratedDocument) -> tuple[bytes, str]:
        """Export to PDF format using WeasyPrint."""
        try:
            from weasyprint import HTML, CSS

            # Get HTML content
            html_content, _ = await self._export_html(document)

            # Convert to PDF
            html = HTML(string=html_content.decode('utf-8'))
            pdf_content = html.write_pdf()

            filename = f"{document.code}_v{document.version}.pdf"
            return pdf_content, filename

        except ImportError:
            # Fallback: return HTML with PDF note
            logger.warning("WeasyPrint not available, returning HTML instead of PDF")
            html_content, _ = await self._export_html(document)
            return html_content, f"{document.code}_v{document.version}.html"

    async def _export_xlsx(self, document: GeneratedDocument) -> tuple[bytes, str]:
        """Export to XLSX format (for registers and matrices)."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        wb = Workbook()
        ws = wb.active
        ws.title = document.code[:31]  # Max 31 chars for sheet name

        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4FACFE", end_color="4FACFE", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Add metadata
        ws['A1'] = "Document:"
        ws['B1'] = document.code
        ws['A2'] = "Version:"
        ws['B2'] = document.version
        ws['A3'] = "Type:"
        ws['B3'] = document.document_type.value
        ws['A4'] = "Date:"
        ws['B4'] = document.created_at.strftime('%d/%m/%Y')

        # Parse tables from markdown
        tables = self._extract_tables_from_markdown(document.content_markdown or "")

        current_row = 6

        if tables:
            for table_idx, table in enumerate(tables):
                if table:
                    # Add table header
                    for col_idx, header in enumerate(table[0], 1):
                        cell = ws.cell(row=current_row, column=col_idx, value=header)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = border
                        cell.alignment = Alignment(horizontal='center')

                    current_row += 1

                    # Add data rows
                    for row_data in table[1:]:
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws.cell(row=current_row, column=col_idx, value=value)
                            cell.border = border
                        current_row += 1

                    current_row += 2  # Space between tables
        else:
            # No tables found, create content sheet
            ws.cell(row=6, column=1, value="Contenu du document:")
            lines = (document.content_markdown or "").split('\n')
            for i, line in enumerate(lines[:100], 7):  # Limit to 100 lines
                ws.cell(row=i, column=1, value=line)

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)

        # Save to bytes
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f"{document.code}_v{document.version}.xlsx"
        return buffer.getvalue(), filename

    async def _export_csv(self, document: GeneratedDocument) -> tuple[bytes, str]:
        """Export to CSV format (for registers)."""
        import csv

        tables = self._extract_tables_from_markdown(document.content_markdown or "")

        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # Write metadata
        writer.writerow(["# Document", document.code])
        writer.writerow(["# Version", document.version])
        writer.writerow(["# Type", document.document_type.value])
        writer.writerow([])

        if tables:
            for table in tables:
                for row in table:
                    writer.writerow(row)
                writer.writerow([])
        else:
            # Write content as single column
            lines = (document.content_markdown or "").split('\n')
            for line in lines:
                writer.writerow([line])

        filename = f"{document.code}_v{document.version}.csv"
        return buffer.getvalue().encode('utf-8'), filename

    async def _export_pptx(self, document: GeneratedDocument) -> tuple[bytes, str]:
        """Export to PPTX format (for presentations and schemas)."""
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN

        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        # Title slide
        slide_layout = prs.slide_layouts[6]  # Blank
        slide = prs.slides.add_slide(slide_layout)

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(9), Inches(1))
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = document.name
        p.font.size = Pt(36)
        p.font.bold = True
        p.font.color.rgb = RGBColor(26, 26, 46)
        p.alignment = PP_ALIGN.CENTER

        # Subtitle
        sub_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.8), Inches(9), Inches(0.5))
        tf2 = sub_box.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = f"{document.code} | Version {document.version}"
        p2.font.size = Pt(18)
        p2.font.color.rgb = RGBColor(136, 136, 136)
        p2.alignment = PP_ALIGN.CENTER

        # Content slides
        sections = self._extract_sections_from_markdown(document.content_markdown or "")

        for section_title, section_content in sections[:10]:  # Limit to 10 slides
            slide = prs.slides.add_slide(prs.slide_layouts[6])

            # Section title
            title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.8))
            tf = title_box.text_frame
            p = tf.paragraphs[0]
            p.text = section_title
            p.font.size = Pt(28)
            p.font.bold = True
            p.font.color.rgb = RGBColor(26, 26, 46)

            # Content
            content_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.3), Inches(9), Inches(5.5))
            tf = content_box.text_frame
            tf.word_wrap = True

            # Add content lines
            lines = section_content.split('\n')[:15]  # Limit lines per slide
            for i, line in enumerate(lines):
                if i == 0:
                    p = tf.paragraphs[0]
                else:
                    p = tf.add_paragraph()

                p.text = line.strip()
                p.font.size = Pt(14)
                p.font.color.rgb = RGBColor(51, 51, 51)

        # Save to bytes
        buffer = io.BytesIO()
        prs.save(buffer)
        buffer.seek(0)

        filename = f"{document.code}_v{document.version}.pptx"
        return buffer.getvalue(), filename

    def _extract_tables_from_markdown(self, content: str) -> List[List[List[str]]]:
        """Extract tables from Markdown content."""
        tables = []
        current_table = []
        in_table = False

        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('|'):
                # Skip separator lines
                if stripped.replace('|', '').replace('-', '').replace(' ', '').replace(':', ''):
                    in_table = True
                    row = [cell.strip() for cell in stripped.split('|')[1:-1]]
                    if row:
                        current_table.append(row)
            else:
                if in_table and current_table:
                    tables.append(current_table)
                    current_table = []
                in_table = False

        if current_table:
            tables.append(current_table)

        return tables

    def _extract_sections_from_markdown(self, content: str) -> List[tuple]:
        """Extract sections (h1/h2) from Markdown content."""
        sections = []
        current_title = "Introduction"
        current_content = []

        for line in content.split('\n'):
            if line.startswith('# '):
                if current_content:
                    sections.append((current_title, '\n'.join(current_content)))
                current_title = line[2:].strip()
                current_content = []
            elif line.startswith('## '):
                if current_content:
                    sections.append((current_title, '\n'.join(current_content)))
                current_title = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append((current_title, '\n'.join(current_content)))

        return sections

    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown to HTML."""
        try:
            import markdown
            return markdown.markdown(
                markdown_content or "",
                extensions=['tables', 'toc', 'fenced_code']
            )
        except ImportError:
            return f"<pre>{markdown_content}</pre>"


# Singleton instance
export_service = ExportService()
