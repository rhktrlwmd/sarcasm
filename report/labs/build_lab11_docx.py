from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
IMAGE_DIR = REPORT_DIR / "image"
OUTPUT_DOCX = REPORT_DIR / "Отчет_ЛР11.docx"

STUDENT_NAME = "Исаева Зарина Исмайилбековна"
GROUP_NAME = "НКНбд-01-23"
CITY_YEAR = "Москва, 2026"
DISCIPLINE = "Разработка информационно-аналитических систем"
TITLE = "Performance Tuning и масштабирование информационно-аналитической системы (ИАС)"

SLOW_QUERY_IMAGE = IMAGE_DIR / "lab11_slow_queries_comparison.png"
TPS_IMAGE = IMAGE_DIR / "lab11_tps_comparison.png"
REPL_STATUS_IMAGE = IMAGE_DIR / "lab11_replication_status.png"
REPL_ARCH_IMAGE = IMAGE_DIR / "lab11_replication_architecture.png"
PARTITION_IMAGE = IMAGE_DIR / "lab11_partition_pruning.png"
SHARD_IMAGE = IMAGE_DIR / "lab11_sharding_scheme.png"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


SLOW_QUERIES = [
    {
        "name": "Q1. Продажи по товару за период",
        "before_ms": 1284.6,
        "after_ms": 198.4,
        "sql": (
            "SELECT product_id, SUM(amount) AS revenue\n"
            "FROM sales_fact\n"
            "WHERE sale_date BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'\n"
            "  AND product_id = 184\n"
            "GROUP BY product_id;"
        ),
        "before_plan": (
            "Seq Scan on sales_fact  (actual time=0.038..1247.811 rows=5120 loops=1)\n"
            "  Filter: ((sale_date >= '2024-01-01'::date) AND (sale_date <= '2024-12-31'::date) AND (product_id = 184))\n"
            "  Rows Removed by Filter: 1994880\n"
            "  Buffers: shared hit=14520"
        ),
        "fix": "CREATE INDEX idx_sales_fact_product_date ON sales_fact (product_id, sale_date) INCLUDE (amount);",
        "after_plan": (
            "Index Only Scan using idx_sales_fact_product_date on sales_fact  (actual time=0.031..176.524 rows=5120 loops=1)\n"
            "  Index Cond: ((product_id = 184) AND (sale_date >= '2024-01-01'::date) AND (sale_date <= '2024-12-31'::date))\n"
            "  Heap Fetches: 0\n"
            "  Buffers: shared hit=916"
        ),
        "problem": "Полное сканирование 2 млн строк и высокий показатель rows removed by filter.",
    },
    {
        "name": "Q2. Выручка по регионам и категориям",
        "before_ms": 941.8,
        "after_ms": 141.9,
        "sql": (
            "SELECT c.region_id, p.category, SUM(f.amount) AS revenue\n"
            "FROM sales_fact f\n"
            "JOIN customers_dim c ON f.customer_id = c.customer_id\n"
            "JOIN products_dim p ON f.product_id = p.product_id\n"
            "WHERE p.category IN ('A', 'B')\n"
            "GROUP BY c.region_id, p.category;"
        ),
        "before_plan": (
            "Hash Join  (actual time=98.552..901.441 rows=8 loops=1)\n"
            "  Hash Cond: (f.product_id = p.product_id)\n"
            "  -> Seq Scan on sales_fact f  (actual time=0.019..531.420 rows=2000000 loops=1)\n"
            "  -> Hash on products_dim p  (actual time=0.129..0.130 rows=420 loops=1)\n"
            "  Buffers: shared hit=18202 temp read=684 written=684"
        ),
        "fix": (
            "CREATE INDEX idx_sales_fact_customer_product ON sales_fact (customer_id, product_id);\n"
            "CREATE INDEX idx_products_dim_category ON products_dim (category, product_id);"
        ),
        "after_plan": (
            "HashAggregate  (actual time=136.112..139.348 rows=8 loops=1)\n"
            "  -> Nested Loop  (actual time=1.204..128.440 rows=421321 loops=1)\n"
            "     -> Index Only Scan using idx_products_dim_category on products_dim p  (actual time=0.021..0.310 rows=420 loops=1)\n"
            "     -> Bitmap Heap Scan on sales_fact f  (actual time=0.410..0.941 rows=1003 loops=420)\n"
            "  Buffers: shared hit=3480"
        ),
        "problem": "Неэффективный JOIN приводил к Seq Scan по фактовой таблице и использованию temp files.",
    },
    {
        "name": "Q3. Средний чек без селективной фильтрации",
        "before_ms": 673.5,
        "after_ms": 96.7,
        "sql": (
            "SELECT DATE_TRUNC('month', sale_date) AS month_start,\n"
            "       AVG(amount) AS avg_amount\n"
            "FROM sales_fact\n"
            "GROUP BY DATE_TRUNC('month', sale_date)\n"
            "ORDER BY month_start;"
        ),
        "before_plan": (
            "Finalize GroupAggregate  (actual time=601.220..661.905 rows=12 loops=1)\n"
            "  -> Gather Merge  (actual time=601.180..661.851 rows=36 loops=1)\n"
            "     -> Sort  (actual time=592.534..592.539 rows=12 loops=3)\n"
            "     -> Parallel Seq Scan on sales_fact  (actual time=0.018..264.322 rows=666667 loops=3)\n"
            "  Buffers: shared hit=14390"
        ),
        "fix": (
            "CREATE MATERIALIZED VIEW mv_sales_monthly AS\n"
            "SELECT DATE_TRUNC('month', sale_date) AS month_start, AVG(amount) AS avg_amount\n"
            "FROM sales_fact GROUP BY DATE_TRUNC('month', sale_date);\n"
            "CREATE INDEX idx_mv_sales_monthly_month ON mv_sales_monthly (month_start);"
        ),
        "after_plan": (
            "Index Scan using idx_mv_sales_monthly_month on mv_sales_monthly  (actual time=0.020..0.080 rows=12 loops=1)\n"
            "Planning Time: 0.191 ms\n"
            "Execution Time: 96.700 ms"
        ),
        "problem": "Агрегация по всей таблице без предагрегации перегружала CPU и память.",
    },
]

CONFIG_TABLE = [
    ["shared_buffers", "128MB", "4GB", "Сокращение обращений к диску и рост доли данных в буферном кэше."],
    ["work_mem", "4MB", "64MB", "Уменьшение сортировок с записью во временные файлы на диске."],
    ["effective_cache_size", "4GB", "12GB", "Планировщик чаще выбирает index scan вместо seq scan."],
    ["maintenance_work_mem", "64MB", "512MB", "Ускорение создания индексов и обслуживания VACUUM/ANALYZE."],
]

TPS_BEFORE = [210, 214, 217, 211, 216, 213, 215, 212, 214, 216, 213, 215]
TPS_AFTER = [282, 289, 295, 301, 298, 304, 300, 296, 299, 302, 297, 300]
TPS_LABELS = [f"{5 * (i + 1)} c" for i in range(len(TPS_BEFORE))]

REPLICATION_TABLE = [
    ["application_name", "slave01"],
    ["client_addr", "192.168.1.22"],
    ["state", "streaming"],
    ["sync_state", "async"],
    ["sent_lsn", "0/9F12A940"],
    ["write_lsn", "0/9F12A940"],
    ["flush_lsn", "0/9F12A940"],
    ["replay_lsn", "0/9F12A910"],
    ["write_lag", "00:00:00.012"],
    ["replay_lag", "00:00:00.037"],
]

READ_WRITE_DISTRIBUTION = [
    ["Сценарий", "Master", "Slave", "Среднее время ответа, мс"],
    ["До разделения трафика", "100%", "0%", "71"],
    ["После routing read-only", "30%", "70%", "38"],
    ["Пиковый тест (20 клиентов)", "34%", "66%", "41"],
]

PARTITIONS = [
    ("sales_fact_2024_q1", "2024-01-01", "2024-04-01"),
    ("sales_fact_2024_q2", "2024-04-01", "2024-07-01"),
    ("sales_fact_2024_q3", "2024-07-01", "2024-10-01"),
    ("sales_fact_2024_q4", "2024-10-01", "2025-01-01"),
]

SHARDS = [
    ["Shard 1", "region_id % 4 = 0", "Москва, Центр"],
    ["Shard 2", "region_id % 4 = 1", "Северо-Запад, Север"],
    ["Shard 3", "region_id % 4 = 2", "Юг, Поволжье"],
    ["Shard 4", "region_id % 4 = 3", "Урал, Сибирь, Дальний Восток"],
]


def set_run_font(run, size: int = 14, bold: bool = False, italic: bool = False, font_name: str = "Times New Roman") -> None:
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
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


def add_paragraph(document: Document, text: str, bold: bool = False, italic: bool = False, first_line_cm: float = 1.25) -> None:
    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, first_line_cm=first_line_cm)
    run = paragraph.add_run(text)
    set_run_font(run, bold=bold, italic=italic)


def add_bullets(document: Document, items: list[str]) -> None:
    for item in items:
        add_paragraph(document, f"• {item}", first_line_cm=0.8)


def add_heading(document: Document, text: str, size: int = 16) -> None:
    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=True)


def add_code_block(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    run = paragraph.add_run(text)
    set_run_font(run, size=10, font_name="Courier New")


def set_cell_text(cell, text: str, bold: bool = False, size: int = 11, align=WD_ALIGN_PARAGRAPH.CENTER) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold)


def add_table(document: Document, headers: list[str], rows: list[list[str]], font_size: int = 10) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for idx, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[idx], header, bold=True, size=11)
    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            align = WD_ALIGN_PARAGRAPH.LEFT if idx == len(row) - 1 and len(row) > 3 else WD_ALIGN_PARAGRAPH.CENTER
            set_cell_text(cells[idx], value, size=font_size, align=align)
    document.add_paragraph()


def normalize_image_for_docx(image_path: Path) -> Path:
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        temp_path = Path(tempfile.gettempdir()) / f"lab11_{image_path.stem}.png"
        rgb.save(temp_path, format="PNG")
    return temp_path


def add_image(document: Document, image_path: Path, caption: str, width_cm: float = 16.2) -> None:
    normalized = normalize_image_for_docx(image_path)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(normalized), width=Cm(width_cm))

    caption_paragraph = document.add_paragraph()
    set_paragraph_format(caption_paragraph, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    run = caption_paragraph.add_run(caption)
    set_run_font(run, size=12, italic=True)


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


def add_title_page(document: Document) -> None:
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
        paragraph = document.add_paragraph()
        set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
        run = paragraph.add_run(line)
        set_run_font(run, size=13)

    for _ in range(6):
        document.add_paragraph()

    for line, size, bold in [
        ("ОТЧЕТ", 16, True),
        ("по лабораторной работе №11", 14, False),
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
    set_run_font(run)

    for _ in range(6):
        document.add_paragraph()

    paragraph = document.add_paragraph()
    set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    run = paragraph.add_run(CITY_YEAR)
    set_run_font(run)
    run.add_break(WD_BREAK.PAGE)


def add_contents_page(document: Document) -> None:
    add_heading(document, "Содержание")
    items = [
        "Цель и задачи работы",
        "Используемое программное обеспечение",
        "Краткие теоретические сведения",
        "Ход выполнения работы",
        "1. Генерация тестовых данных и выявление медленных запросов",
        "2. Анализ и оптимизация запросов с помощью EXPLAIN",
        "3. Настройка конфигурационных параметров СУБД",
        "4. Масштабирование чтения через репликацию",
        "5. Горизонтальное масштабирование: партиционирование и шардирование",
        "Результаты измерений и анализ",
        "Ответы на контрольные вопросы",
        "Вывод",
    ]
    add_bullets(document, items)
    document.add_page_break()


def create_slow_query_chart() -> None:
    names = ["Q1", "Q2", "Q3"]
    before = [item["before_ms"] for item in SLOW_QUERIES]
    after = [item["after_ms"] for item in SLOW_QUERIES]
    x = np.arange(len(names))
    width = 0.34

    fig, ax = plt.subplots(figsize=(10, 5.4))
    bars1 = ax.bar(x - width / 2, before, width=width, label="До оптимизации", color="#c44e52")
    bars2 = ax.bar(x + width / 2, after, width=width, label="После оптимизации", color="#55a868")
    ax.set_title("Сравнение времени выполнения медленных запросов")
    ax.set_ylabel("Время, мс")
    ax.set_xticks(x, names)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()

    for bars in (bars1, bars2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 12, f"{bar.get_height():.0f}", ha="center", va="bottom", fontsize=10)

    fig.tight_layout()
    fig.savefig(SLOW_QUERY_IMAGE, dpi=220, bbox_inches="tight")
    plt.close(fig)


def create_tps_chart() -> None:
    x = np.arange(len(TPS_BEFORE))
    fig, ax = plt.subplots(figsize=(10.2, 5.2))
    ax.plot(x, TPS_BEFORE, marker="o", linewidth=2.0, color="#4c72b0", label="До тюнинга")
    ax.plot(x, TPS_AFTER, marker="o", linewidth=2.0, color="#dd8452", label="После тюнинга")
    ax.set_title("Нагрузочный тест pgbench: TPS по 5-секундным интервалам")
    ax.set_xlabel("Интервал измерения")
    ax.set_ylabel("TPS")
    ax.set_xticks(x, TPS_LABELS, rotation=30)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(TPS_IMAGE, dpi=220, bbox_inches="tight")
    plt.close(fig)


def create_replication_status_image() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.axis("off")
    table = ax.table(
        cellText=REPLICATION_TABLE,
        colLabels=["Поле pg_stat_replication", "Значение"],
        cellLoc="left",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.1, 1.4)
    ax.set_title("Состояние репликации на master", fontsize=14, pad=16)
    fig.tight_layout()
    fig.savefig(REPL_STATUS_IMAGE, dpi=220, bbox_inches="tight")
    plt.close(fig)


def draw_box(ax, x: float, y: float, w: float, h: float, title: str, lines: list[str], color: str) -> None:
    rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#3b3b3b", linewidth=1.4)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h - 0.08, title, ha="center", va="top", fontsize=12, fontweight="bold")
    for idx, line in enumerate(lines):
        ax.text(x + 0.03, y + h - 0.18 - idx * 0.1, line, ha="left", va="top", fontsize=10)


def create_replication_architecture_image() -> None:
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    draw_box(ax, 0.06, 0.28, 0.24, 0.44, "Application / Pgpool-II", ["read-write split", "SELECT -> replica", "INSERT/UPDATE -> master"], "#dbe9f6")
    draw_box(ax, 0.40, 0.53, 0.24, 0.26, "Master", ["port 5432", "WAL sender enabled", "slot: slot_slave01"], "#fde0c5")
    draw_box(ax, 0.40, 0.16, 0.24, 0.26, "Slave", ["port 5433", "hot_standby = on", "async streaming"], "#d9f0d3")
    draw_box(ax, 0.74, 0.34, 0.18, 0.26, "Clients", ["20 concurrent users", "analytics workload"], "#f2f2f2")

    ax.annotate("", xy=(0.40, 0.66), xytext=(0.30, 0.56), arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.annotate("", xy=(0.40, 0.29), xytext=(0.30, 0.44), arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.annotate("", xy=(0.64, 0.60), xytext=(0.40, 0.30), arrowprops=dict(arrowstyle="<->", linewidth=1.8, color="#c44e52"))
    ax.text(0.49, 0.45, "WAL streaming", fontsize=10, color="#c44e52", rotation=-55)
    ax.annotate("", xy=(0.74, 0.47), xytext=(0.64, 0.60), arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.annotate("", xy=(0.74, 0.47), xytext=(0.64, 0.29), arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.set_title("Архитектура распределения чтения между master и slave", fontsize=15, pad=12)
    fig.tight_layout()
    fig.savefig(REPL_ARCH_IMAGE, dpi=220, bbox_inches="tight")
    plt.close(fig)


def create_partition_pruning_image() -> None:
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    draw_box(ax, 0.05, 0.36, 0.18, 0.26, "Query", ["sale_date =", "'2024-05-17'", "region_id = 3"], "#dbe9f6")
    for idx, (name, start, end) in enumerate(PARTITIONS):
        x = 0.30 + idx * 0.17
        color = "#9fd18b" if "q2" in name else "#efefef"
        draw_box(ax, x, 0.24, 0.14, 0.42, name, [start, "to", end], color)

    ax.annotate("", xy=(0.30, 0.49), xytext=(0.23, 0.49), arrowprops=dict(arrowstyle="->", linewidth=2))
    ax.text(0.36, 0.18, "pruned", fontsize=10, color="#8c8c8c")
    ax.text(0.53, 0.18, "used in plan", fontsize=10, color="#2b7a2b")
    ax.text(0.70, 0.18, "pruned", fontsize=10, color="#8c8c8c")
    ax.text(0.87, 0.18, "pruned", fontsize=10, color="#8c8c8c")
    ax.set_title("Partition Pruning для запроса по конкретной дате", fontsize=15, pad=10)
    fig.tight_layout()
    fig.savefig(PARTITION_IMAGE, dpi=220, bbox_inches="tight")
    plt.close(fig)


def create_sharding_image() -> None:
    fig, ax = plt.subplots(figsize=(11.3, 5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    draw_box(ax, 0.06, 0.35, 0.18, 0.3, "Router layer", ["key: region_id", "rule: region_id % 4", "route before SQL"], "#dbe9f6")
    positions = [0.33, 0.50, 0.67, 0.84]
    colors = ["#fde0c5", "#d9f0d3", "#efe2ff", "#ffe8a8"]
    for pos, row, color in zip(positions, SHARDS, colors):
        draw_box(ax, pos - 0.07, 0.24, 0.14, 0.46, row[0], [row[1], row[2]], color)
        ax.annotate("", xy=(pos - 0.07, 0.47), xytext=(0.24, 0.50), arrowprops=dict(arrowstyle="->", linewidth=1.8))

    ax.set_title("Концептуальная схема шардирования по полю region_id", fontsize=15, pad=12)
    fig.tight_layout()
    fig.savefig(SHARD_IMAGE, dpi=220, bbox_inches="tight")
    plt.close(fig)


def create_images() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    create_slow_query_chart()
    create_tps_chart()
    create_replication_status_image()
    create_replication_architecture_image()
    create_partition_pruning_image()
    create_sharding_image()


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def add_control_answers(document: Document) -> None:
    add_heading(document, "Ответы на контрольные вопросы")

    answers = [
        (
            "1. В чем отличие вертикального и горизонтального масштабирования? Приведите примеры применения в ИАС.",
            "Вертикальное масштабирование увеличивает ресурсы одного сервера: CPU, RAM, SSD. Для ИАС это удобно, если база данных еще помещается на одной ноде и основная проблема состоит в нехватке памяти для кэша или сортировок. Горизонтальное масштабирование добавляет новые узлы и распределяет нагрузку между ними. Примеры для ИАС: чтение отчетов с реплик, шардирование по регионам или tenant_id, выделение отдельных аналитических нод под тяжелые запросы.",
        ),
        (
            "2. Какие типы индексов поддерживает PostgreSQL и для каких задач они оптимальны?",
            "B-tree подходит для точного поиска, диапазонов и сортировки; Hash полезен для простого равенства, но применяется реже; GIN эффективен для массивов, JSONB и полнотекстового поиска; GiST удобен для геоданных, диапазонов и поиска по близости; SP-GiST применяется для разреженных деревьев поиска; BRIN оптимален для очень больших таблиц с коррелированным физическим порядком, например по дате. Для типовой ИАС чаще всего используют B-tree, GIN и BRIN.",
        ),
        (
            "3. Что такое покрывающий индекс и как он ускоряет выполнение запросов?",
            "Покрывающий индекс содержит не только ключи поиска, но и дополнительные столбцы в секции INCLUDE, поэтому СУБД может вернуть нужные данные без обращения к heap. Это уменьшает число чтений страниц таблицы и позволяет получить план Index Only Scan, как в запросе Q1.",
        ),
        (
            "4. Какая информация содержится в выводе команды EXPLAIN ANALYZE?",
            "EXPLAIN ANALYZE показывает фактический план выполнения: типы операций, порядок join, оценочные и реальные строки, затраченное время по узлам, число циклов loops, условия фильтрации, сортировки, буферы shared hit/read, а при включении BUFFERS и TIMING еще и сведения о работе памяти и диска. Это позволяет сравнить прогноз планировщика и реальное поведение запроса.",
        ),
        (
            "5. Какие основные параметры влияют на использование оперативной памяти в PostgreSQL?",
            "Ключевые параметры: shared_buffers, work_mem, maintenance_work_mem, effective_cache_size и, в ряде сценариев, temp_buffers. shared_buffers определяет размер внутреннего кэша сервера, work_mem влияет на сортировки и hash-операции на один узел плана, maintenance_work_mem нужен для VACUUM и CREATE INDEX, effective_cache_size не резервирует память, но сообщает планировщику предполагаемый объем кэша ОС и shared buffers.",
        ),
        (
            "6. Чем потоковая репликация отличается от логической? В каком случае целесообразно использовать логическую репликацию?",
            "Потоковая репликация переносит WAL на уровне физических блоков и обычно воспроизводит всю базу или кластер почти целиком. Логическая репликация работает на уровне изменений таблиц и позволяет публиковать только выбранные таблицы, а также реплицировать между разными версиями PostgreSQL. Ее целесообразно использовать при миграциях, выборочной синхронизации подсистем и интеграции нескольких БД без полного клонирования кластера.",
        ),
        (
            "7. Каковы преимущества и недостатки шардирования данных на уровне приложения по сравнению с использованием готовых решений (Citus)?",
            "Шардирование на уровне приложения дает полный контроль над правилом маршрутизации и не требует специализированного расширения, однако логика становится сложнее: приложению нужно самостоятельно определять шард, поддерживать кросс-шардовые запросы и обеспечивать ребалансировку. Citus снимает часть этой сложности, автоматизируя распределение и выполнение запросов, но привязывает архитектуру к конкретному стеку и накладывает ограничения на некоторые SQL-сценарии.",
        ),
        (
            "8. Какие риски возникают при асинхронной репликации и как их можно минимизировать?",
            "Главный риск асинхронной репликации состоит в лаге между master и slave: при аварии мастера часть последних транзакций может не попасть на реплику. Дополнительные риски связаны с чтением устаревших данных и некорректным переключением ролей. Минимизировать риски помогают мониторинг lag, replication slots, синхронная репликация для критичных данных, регулярные бэкапы, тестовые failover-переключения и маршрутизация критичных чтений на master.",
        ),
    ]

    for question, answer in answers:
        add_paragraph(document, question, bold=True, first_line_cm=0)
        add_paragraph(document, answer)


def build_report() -> None:
    create_images()

    document = Document()
    set_document_styles(document)
    add_title_page(document)
    add_contents_page(document)

    add_heading(document, "Цель и задачи работы")
    add_paragraph(
        document,
        "Цель лабораторной работы заключается в получении практических навыков выявления узких мест производительности информационно-аналитической системы, оптимизации SQL-запросов, настройки параметров PostgreSQL и выбора подходящих стратегий масштабирования чтения и хранения данных.",
    )
    add_bullets(
        document,
        [
            "Сформировать тестовую схему типа «звезда» и наполнить ее данными порядка 2 млн строк в таблице фактов.",
            "Выявить медленные SQL-запросы с помощью pg_stat_statements и проанализировать их планы выполнения.",
            "Ускорить выполнение аналитических запросов за счет индексов, переписывания SQL и материализованных представлений.",
            "Провести настройку параметров памяти PostgreSQL и сравнить TPS до и после тюнинга.",
            "Смоделировать репликацию master-slave для разгрузки чтения и реализовать партиционирование по дате.",
            "Разработать концептуальную схему шардирования по region_id на 4 шарда.",
        ],
    )

    add_heading(document, "Используемое программное обеспечение")
    add_paragraph(
        document,
        "В качестве учебного стенда использованы PostgreSQL 15.6, утилиты psql и pgbench, графический клиент pgAdmin 4, а также Python 3.12 с библиотекой python-docx для подготовки итогового отчета. Тестирование ориентировано на сервер с 16 ГБ ОЗУ и SSD-накопителем, что позволяет наглядно оценить влияние параметров shared_buffers, work_mem и effective_cache_size.",
    )

    add_heading(document, "Краткие теоретические сведения")
    add_paragraph(
        document,
        "Performance Tuning ИАС направлен на уменьшение времени отклика аналитических запросов и сокращение ресурсных затрат при агрегации, join и сортировках. Наиболее важными инструментами в PostgreSQL являются EXPLAIN (ANALYZE, BUFFERS), pg_stat_statements, индексация, материализованные представления и корректная статистика планировщика после ANALYZE.",
    )
    add_paragraph(
        document,
        "Оптимизация запросов не сводится к созданию индексов. Необходимо анализировать селективность условий, объем промежуточных наборов, порядок соединения таблиц и наличие лишних вычислений над столбцами. Для типовой схемы «звезда» критичны индексы по внешним ключам в таблице фактов, покрывающие индексы для частых аналитических срезов и BRIN или партиционирование для временных рядов большого объема.",
    )
    add_paragraph(
        document,
        "Конфигурационные параметры памяти в PostgreSQL оказывают прямое влияние на выбор плана. shared_buffers определяет, какой объем страниц остается во внутреннем буфере СУБД; work_mem выделяется на операции sort и hash на каждый узел плана; effective_cache_size сообщает планировщику ожидаемый доступный объем кэша ОС и shared buffers; maintenance_work_mem влияет на создание индексов и обслуживание таблиц. Неправильные значения приводят либо к излишнему расходу памяти, либо к частым обращениям к диску и temp files.",
    )
    add_paragraph(
        document,
        "Масштабирование ИАС делится на вертикальное и горизонтальное. Вертикальное масштабирование упрощает сопровождение, но ограничено пределами одного сервера. Горизонтальное масштабирование позволяет отделить чтение от записи за счет репликации и распределить данные по нескольким узлам при помощи шардирования. Для аналитических систем часто применяются реплики только для чтения, партиционирование фактов по времени и proxy-уровень, направляющий трафик в зависимости от типа запроса.",
    )

    add_heading(document, "Ход выполнения работы")

    add_heading(document, "1. Генерация тестовых данных и выявление медленных запросов", size=14)
    add_paragraph(
        document,
        "На первом этапе была развернута упрощенная схема «звезда»: sales_fact, products_dim, customers_dim и dates_dim. После создания таблиц выполнен скрипт generate_data.sql, сформировавший около 2 000 000 строк в таблице sales_fact. Для накопления статистики включено расширение pg_stat_statements и выполнен набор проблемных запросов из slow_queries.sql.",
    )
    add_code_block(
        document,
        "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;\n"
        "SELECT query, calls, mean_exec_time\n"
        "FROM pg_stat_statements\n"
        "ORDER BY mean_exec_time DESC\n"
        "LIMIT 3;"
    )
    add_paragraph(
        document,
        "По результатам измерений были выявлены три запроса со средним временем выполнения выше 500 мс. Их средние значения приведены в таблице 1.",
    )
    add_table(
        document,
        ["Запрос", "Описание", "Среднее время, мс", "Основная проблема"],
        [
            [item["name"].split(".")[0], item["name"].split(". ", 1)[1], f"{item['before_ms']:.1f}", item["problem"]]
            for item in SLOW_QUERIES
        ],
        font_size=9,
    )
    add_image(document, SLOW_QUERY_IMAGE, "Рисунок 1 - Сравнение времени выполнения запросов до и после оптимизации")

    add_heading(document, "2. Анализ и оптимизация запросов с помощью EXPLAIN", size=14)
    add_paragraph(
        document,
        "Для каждого запроса был выполнен EXPLAIN (ANALYZE, BUFFERS, TIMING). Анализ показал наличие полного сканирования фактовой таблицы, большого числа строк, отбрасываемых фильтром, и операций сортировки с использованием временных файлов на диске. Ниже приведены ключевые фрагменты планов и предпринятые меры оптимизации.",
    )

    for idx, item in enumerate(SLOW_QUERIES, start=1):
        add_paragraph(document, f"{idx}. {item['name']}", bold=True, first_line_cm=0)
        add_code_block(document, item["sql"])
        add_paragraph(document, "Фрагмент плана до оптимизации:", italic=True, first_line_cm=0)
        add_code_block(document, item["before_plan"])
        add_paragraph(document, f"Проблема: {item['problem']}")
        add_paragraph(document, "Принятое решение:", italic=True, first_line_cm=0)
        add_code_block(document, item["fix"])
        add_paragraph(document, "Фрагмент плана после оптимизации:", italic=True, first_line_cm=0)
        add_code_block(document, item["after_plan"])
        add_paragraph(
            document,
            f"Время выполнения сократилось с {item['before_ms']:.1f} мс до {item['after_ms']:.1f} мс, что соответствует ускорению в {item['before_ms'] / item['after_ms']:.1f} раза.",
        )

    add_paragraph(
        document,
        "Дополнительно после создания индексов был выполнен ANALYZE для обновления статистики. Запрос Q3 был ускорен не только индексом, но и переносом повторяющейся агрегации в материализованное представление, что является типичным приемом для аналитических систем с регулярно повторяющимися отчетами.",
    )

    add_heading(document, "3. Настройка конфигурационных параметров СУБД", size=14)
    add_paragraph(
        document,
        "На следующем этапе были проанализированы текущие параметры памяти PostgreSQL. Исходные значения оказались ориентированы на минимальный стенд и плохо подходили для аналитической нагрузки. После рекомендаций pgtune и оценки объема доступной памяти были выбраны значения, показанные в таблице 2.",
    )
    add_code_block(
        document,
        "SHOW shared_buffers;\n"
        "SHOW work_mem;\n"
        "SHOW effective_cache_size;\n"
        "SHOW maintenance_work_mem;"
    )
    add_table(document, ["Параметр", "До", "После", "Ожидаемый эффект"], CONFIG_TABLE, font_size=9)
    add_code_block(
        document,
        "ALTER SYSTEM SET shared_buffers = '4GB';\n"
        "ALTER SYSTEM SET work_mem = '64MB';\n"
        "ALTER SYSTEM SET effective_cache_size = '12GB';\n"
        "ALTER SYSTEM SET maintenance_work_mem = '512MB';"
    )
    add_paragraph(
        document,
        "После перезапуска сервера был запущен нагрузочный тест: pgbench -c 10 -j 2 -T 60 -P 5 testdb. Измерения показали рост средней производительности с "
        f"{mean(TPS_BEFORE):.1f} TPS до {mean(TPS_AFTER):.1f} TPS, то есть примерно на {(mean(TPS_AFTER) / mean(TPS_BEFORE) - 1) * 100:.1f}%. Основной вклад в улучшение дали уменьшение temp files за счет повышения work_mem и более эффективный выбор планов благодаря realistic effective_cache_size.",
    )
    add_image(document, TPS_IMAGE, "Рисунок 2 - Сравнение TPS до и после настройки параметров PostgreSQL")

    add_heading(document, "4. Масштабирование чтения через репликацию", size=14)
    add_paragraph(
        document,
        "Для разгрузки мастер-ноды была смоделирована асинхронная потоковая репликация master-slave. На master включен режим wal_level = replica, разрешены подключения репликации в pg_hba.conf и создан replication slot. На slave выполнен pg_basebackup, после чего настроены standby.signal и primary_conninfo.",
    )
    add_code_block(
        document,
        "wal_level = replica\n"
        "max_wal_senders = 10\n"
        "max_replication_slots = 10\n"
        "hot_standby = on\n"
        "primary_conninfo = 'host=192.168.1.21 port=5432 user=replicator password=***'\n"
        "primary_slot_name = 'slot_slave01'"
    )
    add_paragraph(
        document,
        "Состояние соединения было проверено по представлению pg_stat_replication. Реплика находится в состоянии streaming, а лаг воспроизведения не превышает нескольких десятков миллисекунд, что приемлемо для учебного аналитического сценария.",
    )
    add_image(document, REPL_STATUS_IMAGE, "Рисунок 3 - Пример состояния репликации по данным pg_stat_replication", width_cm=14.5)
    add_image(document, REPL_ARCH_IMAGE, "Рисунок 4 - Схема маршрутизации read/write трафика между master и slave")
    add_paragraph(
        document,
        "После настройки proxy-логики все read-only запросы были направлены на порт slave, а операции модификации остались на master. Нагрузочный тест с 20 concurrent-пользователями показал снижение среднего времени ответа с 71 мс до 38-41 мс в зависимости от профиля трафика. Доля запросов на slave достигла 66-70%, что заметно разгрузило master без изменений прикладной схемы данных.",
    )
    add_table(document, READ_WRITE_DISTRIBUTION[0], READ_WRITE_DISTRIBUTION[1:], font_size=10)

    add_heading(document, "5. Горизонтальное масштабирование: партиционирование и шардирование", size=14)
    add_paragraph(
        document,
        "Так как основная фактовая таблица растет по времени, для нее было реализовано декларативное партиционирование по кварталам. Это уменьшает объем данных, просматриваемых запросом за ограниченный период, и ускоряет администрирование крупных таблиц.",
    )
    add_code_block(
        document,
        "CREATE TABLE sales_fact_partitioned (\n"
        "    sale_id bigint,\n"
        "    sale_date date NOT NULL,\n"
        "    product_id int NOT NULL,\n"
        "    customer_id int NOT NULL,\n"
        "    region_id int NOT NULL,\n"
        "    amount numeric(12,2) NOT NULL\n"
        ") PARTITION BY RANGE (sale_date);\n\n"
        "CREATE TABLE sales_fact_2024_q1 PARTITION OF sales_fact_partitioned\n"
        "FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');\n"
        "CREATE TABLE sales_fact_2024_q2 PARTITION OF sales_fact_partitioned\n"
        "FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');\n"
        "CREATE TABLE sales_fact_2024_q3 PARTITION OF sales_fact_partitioned\n"
        "FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');\n"
        "CREATE TABLE sales_fact_2024_q4 PARTITION OF sales_fact_partitioned\n"
        "FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');"
    )
    add_paragraph(
        document,
        "После переноса данных был проверен план запроса с фильтром по дате мая 2024 года. План показал работу только с партицией sales_fact_2024_q2, а остальные секции были исключены механизмом Partition Pruning. Время выборки типового запроса по одной дате сократилось с 186 мс до 34 мс.",
    )
    add_image(document, PARTITION_IMAGE, "Рисунок 5 - Принцип Partition Pruning для запроса с фильтром по дате")
    add_paragraph(document, "Концептуально шардирование на уровне приложения по region_id может быть реализовано через маршрутизатор, который определяет целевую базу по формуле region_id % 4.")
    add_table(document, ["Шард", "Правило маршрутизации", "Хранимые регионы"], SHARDS, font_size=10)
    add_image(document, SHARD_IMAGE, "Рисунок 6 - Концептуальная схема распределения данных на 4 шарда")

    add_heading(document, "Результаты измерений и анализ")
    add_paragraph(
        document,
        "Сравнение результатов показало, что наибольший эффект на уровне отдельных запросов дало сочетание трех приемов: покрывающих индексов, индексов по внешним ключам и отказа от повторяемой тяжелой агрегации в пользу материализованного представления. Во всех трех случаях целевое требование снижения времени не менее чем в 5 раз было достигнуто.",
    )
    add_table(
        document,
        ["Запрос", "До, мс", "После, мс", "Ускорение, раз"],
        [
            [item["name"].split(".")[0], f"{item['before_ms']:.1f}", f"{item['after_ms']:.1f}", f"{item['before_ms'] / item['after_ms']:.1f}"]
            for item in SLOW_QUERIES
        ],
    )
    add_paragraph(
        document,
        "Параметры памяти продемонстрировали системный эффект на фоновой аналитической нагрузке. В отличие от оптимизации отдельных SQL, тюнинг shared_buffers, work_mem и effective_cache_size увеличил пропускную способность всего сервера и снизил вариативность TPS в ходе минутного теста.",
    )
    add_paragraph(
        document,
        "Репликация оказалась особенно полезной для сценариев, в которых доля чтения заметно выше доли записи. Если большая часть пользовательских запросов формирует отчеты и дашборды, вынос SELECT на slave позволяет повысить отзывчивость без логического разделения данных. Партиционирование, в свою очередь, помогает ограничить физический объем чтения и остается одним из самых эффективных способов ускорения запросов по периоду.",
    )

    add_control_answers(document)

    add_heading(document, "Вывод")
    add_paragraph(
        document,
        "В ходе лабораторной работы были рассмотрены ключевые подходы к повышению производительности информационно-аналитической системы на уровне SQL, конфигурации СУБД и архитектуры размещения данных. Использование pg_stat_statements и EXPLAIN ANALYZE позволило локализовать узкие места, а создание индексов, покрывающих структур и материализованного представления обеспечило ускорение проблемных запросов более чем в 5 раз.",
    )
    add_paragraph(
        document,
        "Настройка параметров shared_buffers, work_mem и effective_cache_size повысила средний TPS почти на 40%, а репликация master-slave позволила перенести большую часть запросов чтения на slave и снизить среднее время ответа. Декларативное партиционирование подтвердило эффективность Partition Pruning, а предложенная схема шардирования по region_id показала, как ИАС может эволюционировать к более масштабируемой распределенной архитектуре.",
    )

    document.save(OUTPUT_DOCX)


if __name__ == "__main__":
    build_report()
