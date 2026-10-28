from __future__ import annotations

import os
import re
import tempfile
import textwrap
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import markdown
import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from bs4 import BeautifulSoup, Tag
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
REPORT_MD = REPORT_DIR / "Отчет_ЛР8.md"
OUTPUT_DOCX = REPORT_DIR / "Отчет_ЛР8.docx"
OUTPUT_PDF = REPORT_DIR / "Отчет_ЛР8.pdf"

STUDENT_NAME = "Исаева Зарина Исмайилбековна"
GROUP_NAME = "НКНбд–01–23"
CITY_YEAR = "Москва, 2026"
DISCIPLINE = "Разработка информационно-аналитических систем"
TITLE = "Современные подходы к визуализации данных и продуктивность аналитика"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("`", "")


def parse_table(tag: Tag) -> tuple[list[str], list[list[str]]]:
    rows = []
    for tr in tag.find_all("tr"):
        cells = [clean_text(cell.get_text(" ", strip=True)) for cell in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def parse_blocks() -> list[dict[str, object]]:
    source = REPORT_MD.read_text(encoding="utf-8")
    html = markdown.markdown(source, extensions=["tables", "fenced_code"])
    soup = BeautifulSoup(html, "html.parser")

    blocks: list[dict[str, object]] = []
    start = False
    for node in soup.children:
        if not isinstance(node, Tag):
            continue

        text = clean_text(node.get_text(" ", strip=True))
        if node.name == "h2" and text == "Цель работы":
            start = True
        if not start:
            continue

        if node.name in {"h2", "h3"}:
            blocks.append({"type": "heading", "level": 2 if node.name == "h2" else 3, "text": text})
        elif node.name == "p":
            img = node.find("img")
            if img is not None:
                src = img.get("src", "")
                caption = clean_text(img.get("alt", "Изображение"))
                blocks.append({"type": "image", "src": src, "caption": caption})
            else:
                if text:
                    blocks.append({"type": "paragraph", "text": text})
        elif node.name in {"ul", "ol"}:
            ordered = node.name == "ol"
            items = []
            for index, li in enumerate(node.find_all("li", recursive=False), start=1):
                prefix = f"{index}. " if ordered else "• "
                items.append(prefix + clean_text(li.get_text(" ", strip=True)))
            if items:
                blocks.append({"type": "list", "items": items})
        elif node.name == "blockquote":
            if text:
                blocks.append({"type": "blockquote", "text": text})
        elif node.name == "pre":
            code = node.get_text("\n", strip=False).strip("\n")
            if code:
                blocks.append({"type": "code", "text": code})
        elif node.name == "table":
            headers, rows = parse_table(node)
            if headers:
                blocks.append({"type": "table", "headers": headers, "rows": rows})

    return blocks


def set_run_font(run, name: str = "Times New Roman", size: int = 14, bold: bool = False, italic: bool = False) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_cm: float = 1.25) -> None:
    paragraph.alignment = align
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(first_line_cm) if first_line_cm else None
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_after = Pt(0)
    fmt.space_before = Pt(0)


def set_cell_text(cell, text: str, bold: bool = False, size: int = 11) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold)


def add_docx_paragraph(document: Document, text: str, bold: bool = False, italic: bool = False, first_line_cm: float = 1.25) -> None:
    p = document.add_paragraph()
    set_paragraph_format(p, first_line_cm=first_line_cm)
    run = p.add_run(text)
    set_run_font(run, bold=bold, italic=italic)


def add_docx_heading(document: Document, text: str, level: int) -> None:
    p = document.add_paragraph()
    set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    run = p.add_run(text)
    size = 16 if level == 2 else 14
    set_run_font(run, size=size, bold=True)


def normalize_image_for_docx(image_path: Path) -> Path:
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        temp_path = Path(tempfile.gettempdir()) / f"lab08_{image_path.stem}.png"
        rgb.save(temp_path, format="PNG")
        return temp_path


def add_docx_image(document: Document, image_path: Path, caption: str) -> None:
    normalized = normalize_image_for_docx(image_path)
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(normalized), width=Cm(16.5))

    cap = document.add_paragraph()
    set_paragraph_format(cap, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    run = cap.add_run(caption)
    set_run_font(run, size=12, italic=True)


def add_docx_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for idx, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[idx], header, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            set_cell_text(cells[idx], value, size=10)
    document.add_paragraph()


def set_document_styles(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)

    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(14)


def add_title_page_docx(document: Document) -> None:
    center_lines = [
        "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ",
        "РОССИЙСКОЙ ФЕДЕРАЦИИ",
        "Федеральное государственное автономное",
        "образовательное учреждение высшего образования",
        "«РОССИЙСКИЙ УНИВЕРСИТЕТ ДРУЖБЫ НАРОДОВ»",
        "Факультет физико-математических и естественных наук",
        "Кафедра математического моделирования и искусственного интеллекта",
    ]
    for line in center_lines:
        p = document.add_paragraph()
        set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
        run = p.add_run(line)
        set_run_font(run, size=13)

    for _ in range(6):
        document.add_paragraph()

    for line, size, bold in [
        ("ОТЧЁТ", 16, True),
        ("по лабораторной работе №8", 14, False),
        (f"«{TITLE}»", 14, False),
        (f"по дисциплине «{DISCIPLINE}»", 14, False),
    ]:
        p = document.add_paragraph()
        set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
        run = p.add_run(line)
        set_run_font(run, size=size, bold=bold)

    for _ in range(8):
        document.add_paragraph()

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(f"Выполнила: {STUDENT_NAME}\nГруппа: {GROUP_NAME}")
    set_run_font(run, size=14)

    for _ in range(6):
        document.add_paragraph()

    p = document.add_paragraph()
    set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    run = p.add_run(CITY_YEAR)
    set_run_font(run, size=14)

    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_contents_docx(document: Document, blocks: list[dict[str, object]]) -> None:
    add_docx_heading(document, "Содержание", 2)
    for block in blocks:
        if block["type"] == "heading":
            text = str(block["text"])
            if str(block["level"]) == "2":
                add_docx_paragraph(document, text, first_line_cm=0)
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def build_docx(blocks: list[dict[str, object]]) -> None:
    document = Document()
    set_document_styles(document)
    add_title_page_docx(document)
    add_contents_docx(document, blocks)

    for block in blocks:
        block_type = block["type"]
        if block_type == "heading":
            add_docx_heading(document, str(block["text"]), int(block["level"]))
        elif block_type == "paragraph":
            add_docx_paragraph(document, str(block["text"]))
        elif block_type == "blockquote":
            add_docx_paragraph(document, str(block["text"]), italic=True)
        elif block_type == "list":
            for item in block["items"]:
                add_docx_paragraph(document, str(item))
        elif block_type == "table":
            add_docx_table(document, list(block["headers"]), list(block["rows"]))
        elif block_type == "image":
            image_path = (REPORT_DIR / str(block["src"])).resolve()
            add_docx_image(document, image_path, str(block["caption"]))
        elif block_type == "code":
            p = document.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            for line in str(block["text"]).splitlines():
                run = p.add_run(line + "\n")
                set_run_font(run, name="Courier New", size=9)

    document.save(OUTPUT_DOCX)


def add_title_page_pdf(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    y = 0.94
    for line in [
        "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ",
        "РОССИЙСКОЙ ФЕДЕРАЦИИ",
        "Федеральное государственное автономное",
        "образовательное учреждение высшего образования",
        "«РОССИЙСКИЙ УНИВЕРСИТЕТ ДРУЖБЫ НАРОДОВ»",
        "Факультет физико-математических и естественных наук",
        "Кафедра математического моделирования и искусственного интеллекта",
    ]:
        fig.text(0.5, y, line, ha="center", fontsize=12)
        y -= 0.035

    fig.text(0.5, 0.58, "ОТЧЁТ", ha="center", fontsize=18, fontweight="bold")
    fig.text(0.5, 0.54, "по лабораторной работе №8", ha="center", fontsize=14)
    fig.text(0.5, 0.50, f"«{TITLE}»", ha="center", fontsize=14)
    fig.text(0.5, 0.46, f"по дисциплине «{DISCIPLINE}»", ha="center", fontsize=14)

    fig.text(0.68, 0.25, f"Выполнила: {STUDENT_NAME}\nГруппа: {GROUP_NAME}", fontsize=13)
    fig.text(0.5, 0.08, CITY_YEAR, ha="center", fontsize=13)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_contents_pdf(pdf: PdfPages, blocks: list[dict[str, object]]) -> None:
    headings = [str(block["text"]) for block in blocks if block["type"] == "heading" and int(block["level"]) == 2]
    add_text_pages(pdf, "Содержание", headings, max_lines=36)


def add_text_pages(pdf: PdfPages, title: str, paragraphs: list[str], max_lines: int = 38) -> None:
    wrapped_lines: list[str] = []
    for paragraph in paragraphs:
        if not paragraph:
            wrapped_lines.append("")
            continue
        wrapped = textwrap.wrap(paragraph, width=94, break_long_words=False, replace_whitespace=False)
        wrapped_lines.extend(wrapped or [""])
        wrapped_lines.append("")

    chunks = [wrapped_lines[i : i + max_lines] for i in range(0, len(wrapped_lines), max_lines)] or [[]]
    for index, chunk in enumerate(chunks, start=1):
        fig = plt.figure(figsize=(8.27, 11.69))
        ax = fig.add_axes([0.07, 0.05, 0.86, 0.90])
        ax.axis("off")
        page_title = title if len(chunks) == 1 else f"{title} ({index})"
        fig.text(0.07, 0.95, page_title, fontsize=16, fontweight="bold", va="top")
        y = 0.91
        for line in chunk:
            fig.text(0.07, y, line, fontsize=11, va="top")
            y -= 0.0225
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def add_table_page(pdf: PdfPages, title: str, headers: list[str], rows: list[list[str]]) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.03, 0.08, 0.94, 0.82])
    ax.axis("off")
    fig.text(0.03, 0.94, title, fontsize=16, fontweight="bold", va="top")

    df = pd.DataFrame(rows, columns=headers)
    table = ax.table(cellText=df.values, colLabels=df.columns, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_image_page(pdf: PdfPages, title: str, image_path: Path, caption: str) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.04, 0.10, 0.92, 0.78])
    ax.axis("off")
    fig.text(0.04, 0.95, title, fontsize=16, fontweight="bold", va="top")
    ax.imshow(mpimg.imread(image_path))
    fig.text(0.5, 0.04, caption, ha="center", fontsize=11, style="italic")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_code_pages(pdf: PdfPages, title: str, code_text: str) -> None:
    lines = code_text.splitlines()
    chunks = [lines[i : i + 44] for i in range(0, len(lines), 44)] or [[]]
    for index, chunk in enumerate(chunks, start=1):
        fig = plt.figure(figsize=(8.27, 11.69))
        ax = fig.add_axes([0.05, 0.04, 0.90, 0.92])
        ax.axis("off")
        page_title = title if len(chunks) == 1 else f"{title} ({index})"
        fig.text(0.05, 0.96, page_title, fontsize=15, fontweight="bold", va="top")
        y = 0.92
        for line in chunk:
            fig.text(0.05, y, line, fontsize=8.7, family="monospace", va="top")
            y -= 0.0198
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def build_pdf(blocks: list[dict[str, object]]) -> None:
    with PdfPages(OUTPUT_PDF) as pdf:
        add_title_page_pdf(pdf)
        add_contents_pdf(pdf, blocks)

        current_title = "Раздел"
        pending_paragraphs: list[str] = []

        def flush() -> None:
            nonlocal pending_paragraphs
            if pending_paragraphs:
                add_text_pages(pdf, current_title, pending_paragraphs)
                pending_paragraphs = []

        for block in blocks:
            block_type = block["type"]
            if block_type == "heading":
                flush()
                current_title = str(block["text"])
            elif block_type == "paragraph":
                pending_paragraphs.append(str(block["text"]))
            elif block_type == "blockquote":
                pending_paragraphs.append("Цитата: " + str(block["text"]))
            elif block_type == "list":
                pending_paragraphs.extend([str(item) for item in block["items"]])
            elif block_type == "table":
                flush()
                add_table_page(pdf, current_title, list(block["headers"]), list(block["rows"]))
            elif block_type == "image":
                flush()
                image_path = (REPORT_DIR / str(block["src"])).resolve()
                add_image_page(pdf, current_title, image_path, str(block["caption"]))
            elif block_type == "code":
                flush()
                add_code_pages(pdf, current_title, str(block["text"]))

        flush()


def main() -> None:
    blocks = parse_blocks()
    build_docx(blocks)
    build_pdf(blocks)
    print(f"DOCX saved to {OUTPUT_DOCX}")
    print(f"PDF saved to {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
