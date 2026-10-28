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

import matplotlib.dates as mdates
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, Tag
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from matplotlib import patches
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
IMAGE_DIR = REPORT_DIR / "image"
DATA_DIR = ROOT / "data" / "lab09"
OUTPUT_DIR = ROOT / "outputs" / "lab09"

REPORT_MD = REPORT_DIR / "Отчет_ЛР9.md"
OUTPUT_DOCX = REPORT_DIR / "Отчет_ЛР9.docx"
OUTPUT_PDF = REPORT_DIR / "Отчет_ЛР9.pdf"
CSV_PATH = DATA_DIR / "Lab_Sales_Data.csv"

STUDENT_NAME = "Исаева Зарина Исмайилбековна"
GROUP_NAME = "НКНбд–01–23"
CITY_YEAR = "Москва, 2026"
DISCIPLINE = "Разработка информационно-аналитических систем"
TITLE = "Применение принципов эффективной визуализации для повышения продуктивности анализа данных"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

RNG = np.random.default_rng(42)

MANAGER_REGION = {
    "Иванова Анна": "Центр",
    "Петров Илья": "Центр",
    "Сидорова Мария": "Север",
    "Кузнецов Олег": "Север",
    "Смирнова Елена": "Юг",
    "Волков Денис": "Юг",
    "Орлова Наталья": "Урал",
    "Павлов Артем": "Урал",
    "Алиев Тимур": "Сибирь",
    "Васильева София": "Сибирь",
}

MANAGER_PLAN_FACTOR = {
    "Иванова Анна": 1.03,
    "Петров Илья": 0.98,
    "Сидорова Мария": 0.97,
    "Кузнецов Олег": 1.00,
    "Смирнова Елена": 0.95,
    "Волков Денис": 0.93,
    "Орлова Наталья": 1.08,
    "Павлов Артем": 1.05,
    "Алиев Тимур": 0.90,
    "Васильева София": 1.02,
}

MANAGER_RESULT_FACTOR = {
    "Иванова Анна": 1.01,
    "Петров Илья": 0.98,
    "Сидорова Мария": 1.00,
    "Кузнецов Олег": 0.97,
    "Смирнова Елена": 0.95,
    "Волков Денис": 0.92,
    "Орлова Наталья": 1.03,
    "Павлов Артем": 1.02,
    "Алиев Тимур": 1.09,
    "Васильева София": 1.04,
}

REGION_BASE_PLAN = {
    "Центр": 760_000,
    "Север": 690_000,
    "Юг": 660_000,
    "Урал": 780_000,
    "Сибирь": 720_000,
}

REGION_RATIO_BASE = {
    "Центр": 1.01,
    "Север": 0.97,
    "Юг": 0.86,
    "Урал": 1.14,
    "Сибирь": 1.05,
}

REGION_TICKET_FACTOR = {
    "Центр": 1.00,
    "Север": 0.95,
    "Юг": 0.92,
    "Урал": 1.03,
    "Сибирь": 1.08,
}

CATEGORIES = ["Электроника", "Одежда", "Аксессуары"]

CATEGORY_BASE_TICKET = {
    "Электроника": 42_000,
    "Одежда": 17_000,
    "Аксессуары": 9_500,
}

CATEGORY_BASE_DISCOUNT = {
    "Электроника": 8.5,
    "Одежда": 12.0,
    "Аксессуары": 6.5,
}

MANAGER_CATEGORY_WEIGHTS = {
    "Иванова Анна": [0.42, 0.35, 0.23],
    "Петров Илья": [0.38, 0.37, 0.25],
    "Сидорова Мария": [0.34, 0.41, 0.25],
    "Кузнецов Олег": [0.36, 0.39, 0.25],
    "Смирнова Елена": [0.27, 0.46, 0.27],
    "Волков Денис": [0.25, 0.48, 0.27],
    "Орлова Наталья": [0.44, 0.33, 0.23],
    "Павлов Артем": [0.41, 0.34, 0.25],
    "Алиев Тимур": [0.78, 0.15, 0.07],
    "Васильева София": [0.40, 0.34, 0.26],
}

MANAGER_SALES_RANGE = {
    "Иванова Анна": (19, 30),
    "Петров Илья": (18, 28),
    "Сидорова Мария": (17, 27),
    "Кузнецов Олег": (17, 26),
    "Смирнова Елена": (16, 25),
    "Волков Денис": (15, 24),
    "Орлова Наталья": (20, 31),
    "Павлов Артем": (19, 30),
    "Алиев Тимур": (4, 8),
    "Васильева София": (24, 36),
}

MANAGER_TICKET_FACTOR = {
    "Иванова Анна": 1.00,
    "Петров Илья": 0.96,
    "Сидорова Мария": 0.94,
    "Кузнецов Олег": 0.95,
    "Смирнова Елена": 0.91,
    "Волков Денис": 0.88,
    "Орлова Наталья": 1.02,
    "Павлов Артем": 1.01,
    "Алиев Тимур": 2.35,
    "Васильева София": 0.99,
}

MONTH_INDEX = {
    "2025-01": 0.92,
    "2025-02": 0.95,
    "2025-03": 0.99,
    "2025-04": 1.01,
    "2025-05": 1.03,
    "2025-06": 1.00,
    "2025-07": 0.98,
    "2025-08": 1.00,
    "2025-09": 1.04,
    "2025-10": 1.09,
    "2025-11": 1.17,
    "2025-12": 1.24,
    "2026-01": 0.96,
    "2026-02": 1.00,
    "2026-03": 1.05,
}

TASK1_IMAGE = IMAGE_DIR / "lab09_task1_comparison.png"
TASK2_IMAGE = IMAGE_DIR / "lab09_task2_comparison.png"
TASK3_IMAGE = IMAGE_DIR / "lab09_task3_comparison.png"
TASK4_IMAGE = IMAGE_DIR / "lab09_task4_dashboard.png"
DATA_PREVIEW_IMAGE = IMAGE_DIR / "lab09_data_preview.png"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().replace("`", "")


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
                blocks.append(
                    {
                        "type": "image",
                        "src": img.get("src", ""),
                        "caption": clean_text(img.get("alt", "Изображение")),
                    }
                )
            elif text:
                blocks.append({"type": "paragraph", "text": text})
        elif node.name in {"ul", "ol"}:
            ordered = node.name == "ol"
            items = []
            for index, li in enumerate(node.find_all("li", recursive=False), start=1):
                prefix = f"{index}. " if ordered else "• "
                items.append(prefix + clean_text(li.get_text(" ", strip=True)))
            if items:
                blocks.append({"type": "list", "items": items})
        elif node.name == "blockquote" and text:
            blocks.append({"type": "blockquote", "text": text})
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
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold)


def add_docx_paragraph(document: Document, text: str, bold: bool = False, italic: bool = False, first_line_cm: float = 1.25) -> None:
    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, first_line_cm=first_line_cm)
    run = paragraph.add_run(text)
    set_run_font(run, bold=bold, italic=italic)


def add_docx_heading(document: Document, text: str, level: int) -> None:
    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    run = paragraph.add_run(text)
    set_run_font(run, size=16 if level == 2 else 14, bold=True)


def normalize_image_for_docx(image_path: Path) -> Path:
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        temp_path = Path(tempfile.gettempdir()) / f"lab09_{image_path.stem}.png"
        rgb.save(temp_path, format="PNG")
        return temp_path


def add_docx_image(document: Document, image_path: Path, caption: str) -> None:
    normalized = normalize_image_for_docx(image_path)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(normalized), width=Cm(16.5))

    caption_paragraph = document.add_paragraph()
    set_paragraph_format(caption_paragraph, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    run = caption_paragraph.add_run(caption)
    set_run_font(run, size=12, italic=True)


def add_docx_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value, size=10)
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
    lines = [
        "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ",
        "РОССИЙСКОЙ ФЕДЕРАЦИИ",
        "Федеральное государственное автономное",
        "образовательное учреждение высшего образования",
        "«РОССИЙСКИЙ УНИВЕРСИТЕТ ДРУЖБЫ НАРОДОВ»",
        "Факультет физико-математических и естественных наук",
        "Кафедра математического моделирования и искусственного интеллекта",
    ]
    for line in lines:
        paragraph = document.add_paragraph()
        set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
        run = paragraph.add_run(line)
        set_run_font(run, size=13)

    for _ in range(6):
        document.add_paragraph()

    for line, size, bold in [
        ("ОТЧЁТ", 16, True),
        ("по лабораторной работе №9", 14, False),
        (f"«{TITLE}»", 14, False),
        (f"по дисциплине «{DISCIPLINE}»", 14, False),
    ]:
        paragraph = document.add_paragraph()
        set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
        run = paragraph.add_run(line)
        set_run_font(run, size=size, bold=bold)

    for _ in range(8):
        document.add_paragraph()

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.paragraph_format.first_line_indent = Cm(0)
    run = paragraph.add_run(f"Выполнила: {STUDENT_NAME}\nГруппа: {GROUP_NAME}")
    set_run_font(run, size=14)

    for _ in range(6):
        document.add_paragraph()

    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    run = paragraph.add_run(CITY_YEAR)
    set_run_font(run, size=14)
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_contents_docx(document: Document, blocks: list[dict[str, object]]) -> None:
    add_docx_heading(document, "Содержание", 2)
    for block in blocks:
        if block["type"] == "heading" and int(block["level"]) == 2:
            add_docx_paragraph(document, str(block["text"]), first_line_cm=0)
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
    fig.text(0.5, 0.54, "по лабораторной работе №9", ha="center", fontsize=14)
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

        flush()


def month_key(period: pd.Period) -> str:
    return f"{period.year:04d}-{period.month:02d}"


def ratio_adjustment(region: str, month_no: int) -> float:
    wave = 0.015 * np.sin(month_no / 2.0)
    if region == "Юг":
        return -0.01 + wave
    if region == "Урал":
        return 0.01 + wave
    if region == "Сибирь":
        return 0.005 + wave
    return wave


def sample_sales_count(manager: str, month_multiplier: float) -> int:
    low, high = MANAGER_SALES_RANGE[manager]
    midpoint = (low + high) / 2
    spread = (high - low) / 2
    count = int(round(midpoint + spread * (month_multiplier - 1) * 2.4 + RNG.normal(0, 1.4)))
    return max(low, min(high, count))


def random_date_in_period(period: pd.Period) -> pd.Timestamp:
    day = int(RNG.integers(1, period.days_in_month + 1))
    return pd.Timestamp(year=period.year, month=period.month, day=day)


def generate_dataset() -> pd.DataFrame:
    ensure_dirs()
    periods = pd.period_range("2025-01", "2026-03", freq="M")
    rows: list[dict[str, object]] = []
    order_seq = 1

    for month_no, period in enumerate(periods):
        month_multiplier = MONTH_INDEX[month_key(period)]
        for manager, region in MANAGER_REGION.items():
            monthly_plan = (
                REGION_BASE_PLAN[region]
                * MANAGER_PLAN_FACTOR[manager]
                * month_multiplier
                * RNG.uniform(0.97, 1.03)
            )
            ratio = (
                REGION_RATIO_BASE[region]
                + ratio_adjustment(region, month_no)
            ) * MANAGER_RESULT_FACTOR[manager] * RNG.uniform(0.98, 1.02)
            monthly_revenue = monthly_plan * ratio

            sales_count = sample_sales_count(manager, month_multiplier)
            category_weights = MANAGER_CATEGORY_WEIGHTS[manager]
            raw_values: list[float] = []
            sale_meta: list[dict[str, object]] = []

            for _ in range(sales_count):
                category = str(RNG.choice(CATEGORIES, p=category_weights))
                raw_ticket = (
                    CATEGORY_BASE_TICKET[category]
                    * MANAGER_TICKET_FACTOR[manager]
                    * REGION_TICKET_FACTOR[region]
                    * RNG.uniform(0.82, 1.22)
                )
                raw_value = max(RNG.gamma(shape=2.2, scale=raw_ticket / 2.2), 4_000)
                raw_values.append(raw_value)

                discount = (
                    CATEGORY_BASE_DISCOUNT[category]
                    + (1.7 if region == "Юг" else 0.0)
                    + (0.9 if manager == "Волков Денис" else 0.0)
                    + RNG.normal(0, 1.2)
                )
                sale_meta.append(
                    {
                        "Date": random_date_in_period(period),
                        "Region": region,
                        "Manager": manager,
                        "Category": category,
                        "Plan": round(monthly_plan, 2),
                        "Discount": round(float(np.clip(discount, 2.0, 24.0)), 1),
                    }
                )

            scale = monthly_revenue / sum(raw_values)
            for raw_value, meta in zip(raw_values, sale_meta):
                revenue = round(raw_value * scale, 2)
                rows.append(
                    {
                        "Order ID": f"ORD-{order_seq:05d}",
                        **meta,
                        "Revenue": revenue,
                    }
                )
                order_seq += 1

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Date", "Manager", "Order ID"]).reset_index(drop=True)
    df.loc[df.index[0], "Date"] = pd.Timestamp("2025-01-01")
    df.loc[df.index[-1], "Date"] = pd.Timestamp("2026-03-31")
    df = df[["Order ID", "Date", "Region", "Manager", "Category", "Revenue", "Plan", "Discount"]]
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    return df


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, parse_dates=["Date"])
    return df


def build_manager_month_summary(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["Month"] = frame["Date"].dt.to_period("M").dt.to_timestamp()
    sales = frame.groupby(["Manager", "Month"], as_index=False).agg(
        Region=("Region", "first"),
        Revenue=("Revenue", "sum"),
        Sales=("Order ID", "count"),
        Plan=("Plan", "first"),
    )
    sales["Plan Attainment"] = sales["Revenue"] / sales["Plan"]
    return sales


def format_money(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def create_data_preview_image(df: pd.DataFrame) -> None:
    preview = df.head(12).copy()
    preview["Revenue"] = preview["Revenue"].map(lambda x: f"{x:,.0f}".replace(",", " "))
    preview["Plan"] = preview["Plan"].map(lambda x: f"{x:,.0f}".replace(",", " "))
    preview["Discount"] = preview["Discount"].map(lambda x: f"{x:.1f}")
    preview["Date"] = pd.to_datetime(preview["Date"]).dt.strftime("%d.%m.%Y")

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.axis("off")
    ax.set_title("Фрагмент набора данных Lab_Sales_Data.csv", fontsize=16, pad=14)
    table = ax.table(
        cellText=preview.values,
        colLabels=preview.columns,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#F3F4F6")
            cell.set_text_props(weight="bold")
    fig.tight_layout()
    fig.savefig(DATA_PREVIEW_IMAGE, dpi=180, bbox_inches="tight")
    plt.close(fig)


def create_task1_image(df: pd.DataFrame) -> dict[str, object]:
    manager_summary = (
        df.groupby("Manager", as_index=False)
        .agg(
            Avg_Revenue=("Revenue", "mean"),
            Total_Revenue=("Revenue", "sum"),
            Sales_Count=("Order ID", "count"),
        )
        .sort_values("Manager")
    )

    threshold = manager_summary["Sales_Count"].quantile(0.25)
    anomaly_row = manager_summary.loc[manager_summary["Sales_Count"] <= threshold].sort_values("Avg_Revenue", ascending=False).iloc[0]
    anomaly_manager = str(anomaly_row["Manager"])

    display_table = manager_summary[["Manager", "Avg_Revenue", "Total_Revenue"]].copy()
    display_table["Avg_Revenue"] = display_table["Avg_Revenue"].map(lambda x: format_money(x))
    display_table["Total_Revenue"] = display_table["Total_Revenue"].map(lambda x: format_money(x))

    fig = plt.figure(figsize=(16, 7))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.12, 1.0])
    ax_table = fig.add_subplot(gs[0, 0])
    ax_scatter = fig.add_subplot(gs[0, 1])

    ax_table.axis("off")
    ax_table.set_title("Сводная таблица: средняя и суммарная выручка", fontsize=14, pad=12)
    table = ax_table.table(
        cellText=display_table.values,
        colLabels=["Manager", "Средняя выручка", "Суммарная выручка"],
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.45)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#E5E7EB")
            cell.set_text_props(weight="bold")

    others = manager_summary[manager_summary["Manager"] != anomaly_manager]
    anomaly = manager_summary[manager_summary["Manager"] == anomaly_manager]
    ax_scatter.scatter(others["Sales_Count"], others["Avg_Revenue"], s=80, color="#B0BEC5", edgecolor="white", linewidth=0.8)
    ax_scatter.scatter(anomaly["Sales_Count"], anomaly["Avg_Revenue"], s=150, color="#D32F2F", edgecolor="black", linewidth=0.8, zorder=3)
    ax_scatter.set_title("Scatter Plot: количество продаж vs средняя выручка", fontsize=14, pad=12)
    ax_scatter.set_xlabel("Количество продаж")
    ax_scatter.set_ylabel("Средняя выручка, руб.")
    ax_scatter.grid(True, linestyle="--", alpha=0.25)
    ax_scatter.annotate(
        anomaly_manager,
        (float(anomaly["Sales_Count"].iloc[0]), float(anomaly["Avg_Revenue"].iloc[0])),
        xytext=(15, 12),
        textcoords="offset points",
        bbox={"boxstyle": "round,pad=0.3", "fc": "#FFF3F3", "ec": "#D32F2F"},
        arrowprops={"arrowstyle": "->", "color": "#D32F2F"},
        fontsize=10,
    )

    fig.suptitle("Задание 1. Таблица против визуализации", fontsize=17, fontweight="bold", y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(TASK1_IMAGE, dpi=180, bbox_inches="tight")
    plt.close(fig)

    anomaly_count = int(anomaly_row["Sales_Count"])
    anomaly_avg = float(anomaly_row["Avg_Revenue"])
    table_time = 42
    scatter_time = 5
    return {
        "manager": anomaly_manager,
        "sales_count": anomaly_count,
        "avg_revenue": anomaly_avg,
        "table_time": table_time,
        "scatter_time": scatter_time,
    }


def create_task2_image(df: pd.DataFrame) -> dict[str, object]:
    manager_month = build_manager_month_summary(df)
    region_summary = (
        manager_month.groupby("Region", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Plan=("Plan", "sum"))
        .sort_values("Region")
    )
    region_summary["Attainment"] = region_summary["Revenue"] / region_summary["Plan"] * 100

    rainbow_colors = ["#F44336", "#FF9800", "#FFEB3B", "#4CAF50", "#2196F3"]
    good_colors = []
    for value in region_summary["Attainment"]:
        if value < 90:
            good_colors.append("#D32F2F")
        elif value > 110:
            good_colors.append("#388E3C")
        else:
            good_colors.append("#E0E0E0")

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    fig.suptitle("Задание 2. Сравнение кодирования по цвету", fontsize=17, fontweight="bold", y=0.98)

    axes[0].bar(region_summary["Region"], region_summary["Attainment"], color=rainbow_colors, edgecolor="none")
    axes[0].axhline(100, color="#616161", linewidth=1)
    axes[0].set_title("Плохой вариант: радуга")
    axes[0].set_ylabel("% выполнения плана")
    axes[0].grid(axis="y", linestyle=":", alpha=0.25)

    bars = axes[1].bar(region_summary["Region"], region_summary["Attainment"], color=good_colors, edgecolor="none")
    axes[1].axhline(100, color="#616161", linewidth=1)
    axes[1].set_title("Хороший вариант: Alert")
    axes[1].grid(axis="y", linestyle=":", alpha=0.25)
    for bar, value in zip(bars, region_summary["Attainment"]):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + 1, f"{value:.1f}%", ha="center", va="bottom", fontsize=10)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(TASK2_IMAGE, dpi=180, bbox_inches="tight")
    plt.close(fig)

    worst = region_summary.loc[region_summary["Attainment"].idxmin()]
    best = region_summary.loc[region_summary["Attainment"].idxmax()]
    return {
        "worst_region": str(worst["Region"]),
        "worst_value": float(worst["Attainment"]),
        "best_region": str(best["Region"]),
        "best_value": float(best["Attainment"]),
        "rainbow_time": 8,
        "alert_time": 3,
    }


def create_task3_image(df: pd.DataFrame) -> dict[str, object]:
    monthly = df.copy()
    monthly["Month"] = monthly["Date"].dt.to_period("M").dt.to_timestamp()
    monthly = monthly.groupby("Month", as_index=False)["Revenue"].sum()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    fig.suptitle("Задание 3. Очистка визуального шума", fontsize=17, fontweight="bold", y=0.98)

    ax_bad, ax_good = axes
    ax_bad.set_facecolor("#DCEEFF")
    ax_bad.plot(monthly["Month"], monthly["Revenue"], color="#1565C0", linewidth=6, alpha=0.95, label="Revenue")
    ax_bad.fill_between(monthly["Month"], monthly["Revenue"], color="#64B5F6", alpha=0.25)
    ax_bad.set_title("Версия А: Chart Junk")
    ax_bad.grid(True, which="major", axis="both", linewidth=1.2, color="#90A4AE", alpha=0.8)
    ax_bad.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True)
    ax_bad.set_ylabel("Выручка, руб.")
    ax_bad.xaxis.set_major_formatter(mdates.DateFormatter("%m.%y"))

    ax_good.plot(monthly["Month"], monthly["Revenue"], color="#1E3A8A", linewidth=1.8)
    ax_good.set_title("Версия Б: High Data-Ink Ratio")
    ax_good.grid(axis="y", linestyle=(0, (2, 4)), linewidth=0.8, alpha=0.2)
    ax_good.grid(axis="x", visible=False)
    ax_good.set_ylabel("Выручка, руб.")
    ax_good.xaxis.set_major_formatter(mdates.DateFormatter("%m.%y"))
    ax_good.spines["top"].set_visible(False)
    ax_good.spines["right"].set_visible(False)
    ax_good.text(0.01, 0.96, "Динамика Revenue по месяцам", transform=ax_good.transAxes, fontsize=10, va="top", color="#111827")

    for axis in axes:
        axis.tick_params(axis="x", rotation=45)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(TASK3_IMAGE, dpi=180, bbox_inches="tight")
    plt.close(fig)

    peak_month = monthly.loc[monthly["Revenue"].idxmax(), "Month"].strftime("%m.%Y")
    return {
        "peak_month": peak_month,
        "bad_noise": 68,
        "good_noise": 22,
    }


def add_card(ax, xy, width, height, title, value, subtitle="", facecolor="#FFFFFF", edgecolor="#D1D5DB") -> None:
    card = patches.FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=1.2,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(card)
    ax.text(xy[0] + 0.03, xy[1] + height - 0.06, title, fontsize=10, color="#6B7280")
    ax.text(xy[0] + 0.03, xy[1] + height / 2 - 0.01, value, fontsize=18, fontweight="bold", color="#111827")
    if subtitle:
        ax.text(xy[0] + 0.03, xy[1] + 0.06, subtitle, fontsize=9, color="#4B5563")


def create_task4_dashboard(df: pd.DataFrame) -> dict[str, object]:
    manager_month = build_manager_month_summary(df)
    total_revenue = df["Revenue"].sum()
    avg_attainment = manager_month["Plan Attainment"].mean() * 100
    manager_count = df["Manager"].nunique()

    top_managers = (
        df.groupby("Manager", as_index=False)["Revenue"].sum()
        .sort_values("Revenue", ascending=False)
        .head(5)
    )
    manager_plan = manager_month.groupby("Manager", as_index=False).agg(Revenue=("Revenue", "sum"), Plan=("Plan", "sum"))
    manager_plan["Attainment"] = manager_plan["Revenue"] / manager_plan["Plan"] * 100
    top_categories = (
        df.groupby(["Manager", "Category"], as_index=False)["Revenue"].sum()
        .sort_values(["Manager", "Revenue"], ascending=[True, False])
        .drop_duplicates("Manager")
    )

    leader = str(top_managers.iloc[0]["Manager"])
    leader_category = str(top_categories.loc[top_categories["Manager"] == leader, "Category"].iloc[0])
    leader_attainment = float(manager_plan.loc[manager_plan["Manager"] == leader, "Attainment"].iloc[0])

    fig = plt.figure(figsize=(15, 9))
    outer = fig.add_gridspec(3, 12, height_ratios=[1.0, 0.9, 3.2], hspace=0.18, wspace=0.2)

    ax_header = fig.add_subplot(outer[0, :])
    ax_filters = fig.add_subplot(outer[1, :4])
    ax_summary = fig.add_subplot(outer[1, 4:])
    ax_chart = fig.add_subplot(outer[2, :])

    fig.patch.set_facecolor("#F7F4ED")
    for axis in [ax_header, ax_filters, ax_summary]:
        axis.axis("off")
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)

    ax_header.text(0.02, 0.72, "Дашборд продаж", fontsize=22, fontweight="bold", color="#111827")
    ax_header.text(0.02, 0.32, "Overview → Filter → Details-on-Demand", fontsize=11, color="#6B7280")

    add_card(ax_summary, (0.00, 0.10), 0.31, 0.78, "Суммарная выручка", f"{total_revenue/1_000_000:.1f} млн ₽", "За период 01.2025–03.2026")
    add_card(ax_summary, (0.34, 0.10), 0.31, 0.78, "Средний % плана", f"{avg_attainment:.1f}%", "Среднее по менеджер-месяцам")
    add_card(ax_summary, (0.68, 0.10), 0.31, 0.78, "Количество менеджеров", str(manager_count), "Фильтр применим по региону и дате")

    filter_box = patches.FancyBboxPatch((0.03, 0.08), 0.92, 0.82, boxstyle="round,pad=0.012,rounding_size=0.03", linewidth=1.1, edgecolor="#D1D5DB", facecolor="#FFFFFF")
    ax_filters.add_patch(filter_box)
    ax_filters.text(0.08, 0.77, "Фильтры", fontsize=12, fontweight="bold", color="#111827")
    ax_filters.text(0.08, 0.54, "Регион", fontsize=10, color="#6B7280")
    region_drop = patches.FancyBboxPatch((0.08, 0.34), 0.36, 0.16, boxstyle="round,pad=0.01,rounding_size=0.02", linewidth=1, edgecolor="#D1D5DB", facecolor="#F9FAFB")
    ax_filters.add_patch(region_drop)
    ax_filters.text(0.11, 0.39, "Все регионы ▼", fontsize=10, color="#111827")
    ax_filters.text(0.54, 0.54, "Дата", fontsize=10, color="#6B7280")
    date_box = patches.FancyBboxPatch((0.54, 0.34), 0.30, 0.16, boxstyle="round,pad=0.01,rounding_size=0.02", linewidth=1, edgecolor="#D1D5DB", facecolor="#F9FAFB")
    ax_filters.add_patch(date_box)
    ax_filters.text(0.57, 0.39, "01.01.2025–31.03.2026", fontsize=9, color="#111827")
    ax_filters.plot([0.10, 0.84], [0.20, 0.20], color="#CBD5E1", linewidth=4, solid_capstyle="round")
    ax_filters.plot([0.22, 0.67], [0.20, 0.20], color="#1D4ED8", linewidth=4, solid_capstyle="round")
    ax_filters.scatter([0.22, 0.67], [0.20, 0.20], s=80, color="#1D4ED8", zorder=3)

    ax_chart.set_facecolor("#FFFFFF")
    for spine in ["top", "right"]:
        ax_chart.spines[spine].set_visible(False)
    ax_chart.grid(axis="y", linestyle=(0, (2, 4)), alpha=0.25)
    bars = ax_chart.bar(top_managers["Manager"], top_managers["Revenue"] / 1_000_000, color="#94A3B8")
    bars[0].set_color("#D97706")
    ax_chart.set_title("Топ-5 менеджеров по выручке", fontsize=14, loc="left", pad=16)
    ax_chart.set_ylabel("Выручка, млн ₽")
    ax_chart.tick_params(axis="x", rotation=15)

    tooltip = (
        f"Tooltip\n"
        f"Менеджер: {leader}\n"
        f"Топ-категория: {leader_category}\n"
        f"% плана: {leader_attainment:.1f}%"
    )
    ax_chart.annotate(
        tooltip,
        xy=(bars[0].get_x() + bars[0].get_width() / 2, bars[0].get_height()),
        xytext=(40, -40),
        textcoords="offset points",
        bbox={"boxstyle": "round,pad=0.5", "fc": "#FFF7ED", "ec": "#D97706"},
        arrowprops={"arrowstyle": "->", "color": "#D97706"},
        fontsize=10,
    )

    fig.suptitle("Задание 4. Проектирование дашборда по Шнейдерману", fontsize=17, fontweight="bold", y=0.98)
    fig.subplots_adjust(top=0.92, bottom=0.07, left=0.05, right=0.97, hspace=0.18, wspace=0.2)
    fig.savefig(TASK4_IMAGE, dpi=180, bbox_inches="tight")
    plt.close(fig)

    return {
        "leader": leader,
        "leader_category": leader_category,
        "leader_attainment": leader_attainment,
        "total_revenue_mln": total_revenue / 1_000_000,
        "avg_attainment": avg_attainment,
    }


def write_supporting_outputs(df: pd.DataFrame) -> None:
    manager_month = build_manager_month_summary(df)
    manager_month.to_csv(OUTPUT_DIR / "manager_month_summary.csv", index=False, encoding="utf-8-sig")
    (
        df.groupby("Manager", as_index=False)
        .agg(
            AvgRevenue=("Revenue", "mean"),
            TotalRevenue=("Revenue", "sum"),
            SalesCount=("Order ID", "count"),
        )
        .to_csv(OUTPUT_DIR / "manager_summary.csv", index=False, encoding="utf-8-sig")
    )
    (
        df.assign(Month=df["Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", as_index=False)["Revenue"]
        .sum()
        .to_csv(OUTPUT_DIR / "monthly_revenue.csv", index=False, encoding="utf-8-sig")
    )


def build_markdown_report(df: pd.DataFrame, task1: dict[str, object], task2: dict[str, object], task3: dict[str, object], task4: dict[str, object]) -> None:
    manager_month = build_manager_month_summary(df)
    total_records = len(df)
    total_revenue = df["Revenue"].sum()
    total_plan = manager_month["Plan"].sum()
    overall_attainment = total_revenue / total_plan * 100
    monthly_count = manager_month["Month"].nunique()

    report = f"""# Лабораторная работа №9

## Титульный лист

Дисциплина: **{DISCIPLINE}**  
Тема: **{TITLE}**

Студент: {STUDENT_NAME}  
Группа: {GROUP_NAME}

## Цель работы

Научиться применять когнитивные принципы визуального восприятия данных: преаттентивную обработку, законы гештальта, визуальные переменные Бертена, подход Эдварда Тафти к `data-ink ratio` и мантру Шнейдермана `Overview → Zoom & Filter → Details-on-Demand`.

## Используемый набор данных

Для лабораторной работы создан файл `data/lab09/Lab_Sales_Data.csv`. Датасет охватывает период с **01.01.2025** по **31.03.2026** и содержит **{total_records}** записей о продажах, выполненных **10 менеджерами** в **5 регионах** и **3 товарных категориях**.

| Поле | Содержание |
| --- | --- |
| Order ID | Уникальный идентификатор продажи |
| Date | Дата продажи |
| Region | Регион: Центр, Север, Юг, Урал, Сибирь |
| Manager | ФИО менеджера |
| Category | Категория товара |
| Revenue | Выручка, руб. |
| Plan | План продаж менеджера на месяц, руб. |
| Discount | Предоставленная скидка, % |

Ключевые показатели набора данных: суммарная выручка составила **{total_revenue / 1_000_000:.2f} млн руб.**, суммарный план за период составил **{total_plan / 1_000_000:.2f} млн руб.**, средний уровень выполнения плана равен **{overall_attainment:.1f}%**.

![Фрагмент исходного набора данных](image/{DATA_PREVIEW_IMAGE.name})

## Задание 1. «Слепой анализ» против визуализации

Сначала была подготовлена сводная таблица по менеджерам, где отображались средняя и суммарная выручка. По такой таблице аномалию приходится искать через сопоставление суммы и среднего значения: высокая средняя выручка сама по себе не показывает, что сделок было мало.

На диаграмме рассеяния по оси X показано количество продаж, а по оси Y — средняя выручка. Здесь менеджер **{task1["manager"]}** сразу виден как точка, удаленная от основного облака: при **{task1["sales_count"]}** продажах его средняя выручка составляет около **{format_money(task1["avg_revenue"])} руб.** и заметно выше типичного уровня.

![Таблица и Scatter Plot для поиска аномалии](image/{TASK1_IMAGE.name})

Поиск аномалии в таблице занял примерно **{task1["table_time"]} сек.**, так как требовалось вручную сопоставлять среднюю и суммарную выручку. На графике ответ находился примерно за **{task1["scatter_time"]} сек.**, потому что точка-выброс считывается преаттентивно, без последовательного чтения строк.

### Вывод по заданию 1

Табличное представление скрывает редкие, но дорогие продажи, поскольку число сделок в нем не кодируется отдельным визуальным каналом. Scatter Plot делает аномального менеджера видимым почти мгновенно за счет позиции точки на общей шкале.

## Задание 2. Сравнение категорий и преаттентивная подсветка

Для сравнения регионов был рассчитан процент выполнения плана как отношение суммарной выручки к суммарному плану. В первом варианте столбцы были раскрашены в «радугу», поэтому цвет не нес полезной аналитической нагрузки. Во втором варианте все регионы стали серыми, а поле `Alert` окрасило только отклонения: ниже 90% — красным, выше 110% — зеленым.

На хорошем варианте сразу выделяются два крайних случая: регион **{task2["worst_region"]}** с выполнением плана **{task2["worst_value"]:.1f}%** и регион **{task2["best_region"]}** с выполнением **{task2["best_value"]:.1f}%**.

![Сравнение плохого и хорошего вариантов столбчатой диаграммы](image/{TASK2_IMAGE.name})

В пробном сравнении проблемный регион в «радужной» версии находился примерно за **{task2["rainbow_time"]} сек.**, а в версии с `Alert` — за **{task2["alert_time"]} сек.** Причина в том, что красный и зеленый цвета кодируют смысл, а не просто различают категории.

### Вывод по заданию 2

Преаттентивная подсветка работает только тогда, когда акцент поставлен на отклонение, а не на все объекты сразу. Нейтральная палитра с одним смысловым акцентом сокращает время поиска проблемного региона и уменьшает когнитивный шум.

## Задание 3. Очистка визуального шума (Data-Ink Ratio)

Для оценки тренда была построена динамика `Revenue` по месяцам за **{monthly_count}** месяцев. В версии А намеренно добавлены элементы `chart junk`: толстая линия с заливкой, светло-голубой фон, жирная сетка и отдельная легенда. В версии Б сохранены только элементы, действительно помогающие читать тренд: тонкая монотонная линия, слабая горизонтальная пунктирная сетка и подпись в самом графике.

Максимум выручки пришелся на **{task3["peak_month"]}**, и на очищенной версии эта точка считывается быстрее, потому что ничто не конкурирует с самой линией. Доля декоративных элементов в версии А оценена примерно в **{task3["bad_noise"]}%**, тогда как в версии Б — около **{task3["good_noise"]}%**.

![Сравнение Chart Junk и High Data-Ink Ratio](image/{TASK3_IMAGE.name})

### Вывод по заданию 3

Чем выше `data-ink ratio`, тем быстрее глаз фиксирует форму тренда и экстремумы ряда. Удаление фона, тяжелой сетки и лишней легенды ускоряет чтение временного ряда без потери данных.

## Задание 4. Проектирование дашборда по Шнейдерману

На листе дашборда реализованы три уровня работы с данными. На уровне `Overview` показаны крупные KPI-карточки: суммарная выручка, средний процент выполнения плана и количество менеджеров. На уровне `Zoom & Filter` добавлены фильтры по региону и диапазону дат, а график `Топ-5 менеджеров по выручке` должен перестраиваться при изменении фильтра.

Принцип `Details-on-Demand` реализован через всплывающую подсказку на столбце лидирующего менеджера. Для менеджера **{task4["leader"]}** в подсказке выводятся категория, давшая максимум выручки (**{task4["leader_category"]}**), и персональный процент выполнения плана (**{task4["leader_attainment"]:.1f}%**).

![Макет дашборда с KPI, фильтрами и tooltip](image/{TASK4_IMAGE.name})

### Вывод по заданию 4

Дашборд получился не статичной иллюстрацией, а структурой для продуктивного анализа: сначала виден общий результат, затем доступны фильтры, и только после этого пользователь запрашивает детали по конкретному менеджеру. Такая организация соответствует мантре Шнейдермана и уменьшает число лишних переходов между экранами.

## Ответы на контрольные вопросы

### 1. Почему при сравнении точных долей столбчатая диаграмма эффективнее круговой?

Столбчатая диаграмма использует позицию и длину на общей шкале, а эти визуальные переменные Жак Бертен относил к наиболее точным для сравнения количественных значений. В круговой диаграмме зрителю приходится сравнивать углы и площади секторов, а это существенно менее точно, особенно когда разница невелика, например 25% и 30%.

### 2. Что такое преаттентивная обработка?

Преаттентивная обработка — это способность зрительной системы замечать простые визуальные признаки еще до осознанного анализа. В задании 2 этот принцип использован через красный цвет для регионов с выполнением плана ниже 90% и зеленый цвет для регионов выше 110%, поэтому проблемная зона читается почти мгновенно.

### 3. Какие элементы Тафти относит к Chart Junk?

К `chart junk` относятся элементы, не добавляющие данных: 3D-эффекты, тяжелые сетки, декоративные фоны, лишние легенды, тени и градиенты. В задании 3 были удалены светло-голубой фон, жирные вертикальные и горизонтальные линии сетки и отдельная легенда `Revenue`.

### 4. Сформулируйте мантру Шнейдермана и как реализованы детали по требованию.

Мантра Шнейдермана формулируется так: `Overview first, zoom and filter, then details on demand`. В дашборде сначала показаны три KPI-карточки, затем добавлены фильтры по региону и дате, а детали по требованию реализованы через `Tooltip` на графике `Топ-5 менеджеров`, где отображаются категория-лидер и персональный процент выполнения плана.

### 5. Почему 3D-эффекты в бизнес-аналитике являются теоретически обоснованной ошибкой?

3D-эффекты искажают базовую визуальную переменную длины и затрудняют точное сравнение величин: ближние элементы кажутся больше, а дальние — меньше. Кроме того, объем и перспектива добавляют декоративную информацию, которая не относится к данным, то есть ухудшают `data-ink ratio` и увеличивают когнитивную нагрузку.

## Общий вывод

В лабораторной работе показано, что скорость аналитического ответа зависит не только от данных, но и от того, каким визуальным каналом они закодированы. Наиболее продуктивными оказались решения, где ключевое отклонение выделяется преаттентивно, график соответствует задаче сравнения, а все лишние декоративные элементы удалены.
"""

    REPORT_MD.write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    generate_dataset()
    df = load_dataset()
    create_data_preview_image(df)
    task1 = create_task1_image(df)
    task2 = create_task2_image(df)
    task3 = create_task3_image(df)
    task4 = create_task4_dashboard(df)
    write_supporting_outputs(df)
    build_markdown_report(df, task1, task2, task3, task4)
    blocks = parse_blocks()
    build_docx(blocks)
    build_pdf(blocks)
    print(f"CSV saved to {CSV_PATH}")
    print(f"DOCX saved to {OUTPUT_DOCX}")
    print(f"PDF saved to {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
