from __future__ import annotations

from pathlib import Path
import re
import tempfile

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image


REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent
IMAGE_DIR = REPORT_DIR / "image"
DATA_DIR = PROJECT_ROOT / "data" / "processed"
PLOTS_DIR = PROJECT_ROOT / "outputs" / "plots"
OUTPUT_DOCX = REPORT_DIR / "Отчет_ЛР7.docx"

STUDENT_NAME = "Исаева Зарина Исмайилбековна"
GROUP_NAME = "НКНбд–01–23"
CITY_YEAR = "Москва, 2026"


def set_cell_text(cell, text: str, bold: bool = False) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(str(text))
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(12)


def set_run_font(run, name: str = "Times New Roman", size: int = 14, bold: bool = False, italic: bool = False) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def set_paragraph_format(paragraph, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_cm: float = 1.25, spacing: float = 1.5) -> None:
    paragraph.alignment = align
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(first_line_cm) if first_line_cm else None
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_after = Pt(0)
    fmt.space_before = Pt(0)


def add_text_paragraph(document: Document, text: str, bold: bool = False) -> None:
    p = document.add_paragraph()
    set_paragraph_format(p)
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", 14, bold=bold)


def add_center_paragraph(document: Document, text: str, size: int = 14, bold: bool = False, first_line_cm: float = 0) -> None:
    p = document.add_paragraph()
    set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=first_line_cm)
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", size, bold=bold)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    p = document.add_paragraph()
    set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", 16 if level == 1 else 14, bold=True)


def add_page_break(document: Document) -> None:
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_table(document: Document, dataframe: pd.DataFrame) -> None:
    table = document.add_table(rows=1, cols=len(dataframe.columns))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for idx, col in enumerate(dataframe.columns):
        set_cell_text(hdr[idx], str(col), bold=True)
    for _, row in dataframe.iterrows():
        cells = table.add_row().cells
        for idx, value in enumerate(row.tolist()):
            set_cell_text(cells[idx], value)
    document.add_paragraph()


def add_image(document: Document, image_path: Path, caption: str, width_cm: float = 16.0) -> None:
    normalized_path = normalize_image_for_docx(image_path)
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(normalized_path), width=Cm(width_cm))

    cap = document.add_paragraph()
    set_paragraph_format(cap, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    run = cap.add_run(caption)
    set_run_font(run, "Times New Roman", 12, italic=True)


def normalize_image_for_docx(image_path: Path) -> Path:
    with Image.open(image_path) as image:
        converted = image.convert("RGB")
        temp_dir = Path(tempfile.gettempdir())
        temp_path = temp_dir / f"codex_docx_{image_path.stem}.png"
        converted.save(temp_path, format="PNG")
        return temp_path


def add_code_listing(document: Document, file_path: Path, title: str) -> None:
    p = document.add_paragraph()
    set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    run = p.add_run(title)
    set_run_font(run, "Times New Roman", 12, bold=True)

    code_text = file_path.read_text(encoding="utf-8")
    code_paragraph = document.add_paragraph()
    code_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fmt = code_paragraph.paragraph_format
    fmt.first_line_indent = Cm(0)
    fmt.left_indent = Cm(0.5)
    fmt.line_spacing_rule = WD_LINE_SPACING.SINGLE
    fmt.space_after = Pt(6)
    for line_no, line in enumerate(code_text.splitlines(), start=1):
        run = code_paragraph.add_run(f"{line_no:>3} {line}\n")
        set_run_font(run, "Courier New", 9)


def enable_table_borders(table) -> None:
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        elem = OxmlElement(f"w:{edge}")
        elem.set(qn("w:val"), "single")
        elem.set(qn("w:sz"), "8")
        elem.set(qn("w:space"), "0")
        elem.set(qn("w:color"), "000000")
        borders.append(elem)
    tblPr.append(borders)


def parse_summary(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    patterns = {
        "source": r"Источник данных: (.+)",
        "window_size": r"Размер окна: (.+)",
        "windows": r"Количество окон: ([0-9]+)",
        "adf_avg_stat": r"ADF для avg_degree:\s+statistic = ([^\n]+)",
        "adf_avg_p": r"ADF для avg_degree:\s+statistic = [^\n]+\s+p_value = ([^\n]+)",
        "adf_avg_conclusion": r"ADF для avg_degree:\s+statistic = [^\n]+\s+p_value = [^\n]+\s+conclusion = ([^\n]+)",
        "adf_ratio_p": r"ADF для in_out_ratio_mean:\s+statistic = [^\n]+\s+p_value = ([^\n]+)",
        "adf_ratio_conclusion": r"ADF для in_out_ratio_mean:\s+statistic = [^\n]+\s+p_value = [^\n]+\s+conclusion = ([^\n]+)",
        "correlation": r"Корреляция avg_degree и n_components: ([^\n]+)",
        "mae": r"MAE = ([^\n]+)",
        "rmse": r"RMSE = ([^\n]+)",
    }
    result: dict[str, str] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE)
        result[key] = match.group(1).strip() if match else "n/a"
    return result


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
    add_center_paragraph(document, "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ", 13)
    add_center_paragraph(document, "РОССИЙСКОЙ ФЕДЕРАЦИИ", 13)
    add_center_paragraph(document, "Федеральное государственное автономное", 13)
    add_center_paragraph(document, "образовательное учреждение высшего образования", 13)
    add_center_paragraph(document, "«РОССИЙСКИЙ УНИВЕРСИТЕТ ДРУЖБЫ НАРОДОВ»", 13)
    add_center_paragraph(document, "Факультет физико-математических и естественных наук", 13)
    add_center_paragraph(document, "Кафедра математического моделирования и искусственного интеллекта", 13)

    for _ in range(6):
        document.add_paragraph()

    add_center_paragraph(document, "ОТЧЁТ", 16, bold=True)
    add_center_paragraph(document, "по лабораторной работе №7", 14)
    add_center_paragraph(document, "«Аналитика графов и временных рядов»", 14)
    add_center_paragraph(document, "по дисциплине «Разработка информационно-аналитических систем»", 14)

    for _ in range(8):
        document.add_paragraph()

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.first_line_indent = Cm(0)
    r = p.add_run(f"Выполнила: {STUDENT_NAME}\nГруппа: {GROUP_NAME}")
    set_run_font(r, "Times New Roman", 14)

    for _ in range(6):
        document.add_paragraph()

    add_center_paragraph(document, CITY_YEAR, 14)
    add_page_break(document)


def add_contents(document: Document) -> None:
    add_heading(document, "Содержание", 1)
    for item in [
        "1. Цель работы",
        "2. Краткое теоретическое обоснование",
        "3. Описание данных",
        "4. Ход работы",
        "5. Графики и интерпретация",
        "6. Выводы",
        "7. Ответы на контрольные вопросы",
        "8. Листинг исходного кода",
    ]:
        p = document.add_paragraph()
        set_paragraph_format(p, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
        run = p.add_run(item)
        set_run_font(run, "Times New Roman", 14)
    add_page_break(document)


def build_document() -> Document:
    document = Document()
    set_document_styles(document)

    und = pd.read_csv(DATA_DIR / "metrics_undirected.csv", parse_dates=["time_start", "time_end", "time"])
    directed = pd.read_csv(DATA_DIR / "metrics_directed.csv")
    events = pd.read_csv(DATA_DIR / "events_used.csv", parse_dates=["timestamp"])
    top_nodes = pd.read_csv(DATA_DIR / "top_betweenness_nodes.csv")
    arima_test = pd.read_csv(DATA_DIR / "arima_test_comparison.csv", parse_dates=["time"])
    arima_future = pd.read_csv(DATA_DIR / "arima_future_forecast.csv", parse_dates=["time"])
    summary = parse_summary(PROJECT_ROOT / "outputs" / "summary.txt")

    add_title_page(document)
    add_contents(document)

    add_heading(document, "1. Цель работы", 1)
    add_text_paragraph(
        document,
        "Целью лабораторной работы является исследование методов анализа динамических графов и временных рядов на последовательности взаимодействий между узлами, построение графов по окнам наблюдения, вычисление графовых метрик, представление этих метрик в виде временных рядов и проведение анализа стационарности, декомпозиции и прогнозирования.",
    )

    add_heading(document, "2. Краткое теоретическое обоснование", 1)
    add_text_paragraph(
        document,
        "Динамический граф представляет собой граф, структура которого изменяется во времени. Для анализа таких данных удобно использовать последовательность снимков сети, полученных по временным окнам. Для каждого снимка рассчитываются характеристики, отражающие интенсивность взаимодействий и структурные свойства сети.",
    )
    add_text_paragraph(
        document,
        "Наиболее важными метриками в данной работе являются средняя степень вершины, плотность, коэффициент кластеризации, число компонент связности, диаметр и центральность по посредничеству. Для ориентированных графов дополнительно полезно анализировать входящие и исходящие степени и их отношение.",
    )
    add_text_paragraph(
        document,
        "Временные ряды графовых метрик позволяют изучать эволюцию сети. Для их анализа применяются визуализация, тест Дики–Фуллера на стационарность, декомпозиция, сглаживание и прогнозирование. В работе использовались аддитивная декомпозиция, скользящее среднее и модель ARIMA.",
    )

    add_heading(document, "3. Описание данных", 1)
    add_text_paragraph(
        document,
        f"В базовой постановке лабораторной предлагается использовать синтетический поток рёбер, однако в данной работе он был заменён реальным датасетом CollegeMsg в рамках дополнительного задания по замене синтетики на реальные данные. Набор содержит {len(events):,} событий взаимодействия между {len(set(events['source']).union(set(events['target']))):,} узлами за период с {events['timestamp'].min().strftime('%d.%m.%Y')} по {events['timestamp'].max().strftime('%d.%m.%Y')}.",
    )
    add_text_paragraph(
        document,
        f"Для построения динамических графов последовательность событий была разбита на окна по {summary['window_size']} событий. Такой вариант ближе к примеру выполнения задания: сначала формируются окна, затем по каждому окну строится граф, вычисляются метрики, а после этого сами значения метрик рассматриваются как временные ряды. Всего было получено {summary['windows']} окон.",
    )

    add_heading(document, "4. Ход работы", 1)
    add_heading(document, "4.1. Подготовка проекта и данных", 2)
    add_text_paragraph(
        document,
        "Для выполнения лабораторной был подготовлен проект с каталогами для исходных данных, обработанных таблиц, графиков и отчёта. Были созданы скрипты для загрузки данных, вычисления метрик графа, анализа временных рядов и генерации отчётных материалов.",
    )
    add_image(document, IMAGE_DIR / "1proj_struct.png", "Рисунок 1 – Структура проекта лабораторной работы", 15.8)
    add_image(document, IMAGE_DIR / "2dataset.txt.png", "Рисунок 2 – Содержимое каталога data/raw", 14.5)
    add_image(document, IMAGE_DIR / "3dataset_content.png", "Рисунок 3 – Фрагмент содержимого датасета CollegeMsg", 15.2)

    add_heading(document, "4.2. Построение динамических графов", 2)
    add_text_paragraph(
        document,
        "Сначала поток событий был отсортирован по времени, затем разбит на последовательные окна по 50 событий. Для каждого окна строился отдельный граф-снимок. Анализ выполнялся как для неориентированного, так и для ориентированного представления сети.",
    )
    add_text_paragraph(
        document,
        "После построения графа для каждого окна вычислялись средняя степень вершин, плотность, средний коэффициент кластеризации, число компонент связности и диаметр в тех случаях, когда граф оказывался связным. Дополнительно для выполнения расширенных заданий рассчитывались средняя и максимальная центральность по посредничеству, а для ориентированного графа — среднее отношение входящих и исходящих степеней.",
    )

    add_heading(document, "4.3. Анализ временных рядов", 2)
    add_text_paragraph(
        document,
        "Полученные по окнам значения метрик были представлены как временные ряды. Поскольку окна формировались по числу событий, а не по календарному шагу, для декомпозиции и прогноза был добавлен регулярный индекс. После этого для ряда avg_degree были построены графики, выполнен тест Дики–Фуллера, аддитивная декомпозиция, сглаживание скользящим средним и прогнозирование с помощью модели ARIMA. Отдельно был проанализирован временной ряд центральности по посредничеству для вершин-лидеров.",
    )
    add_image(document, IMAGE_DIR / "4run_report.png", "Рисунок 4 – Скриншот выполнения скрипта и итоговой сводки", 15.4)
    add_image(document, IMAGE_DIR / "5plots_collage.png", "Рисунок 5 – Коллаж основных графиков анализа", 16.0)

    add_heading(document, "5. Графики и интерпретация", 1)
    add_text_paragraph(
        document,
        f"Среднее значение avg_degree составило {und['avg_degree'].mean():.4f}, минимум {und['avg_degree'].min():.4f}, максимум {und['avg_degree'].max():.4f}. Средняя плотность графа равна {und['density'].mean():.4f}, среднее число компонент связности — {und['n_components'].mean():.2f}.",
    )
    add_text_paragraph(
        document,
        "Для CollegeMsg сеть в большинстве окон остаётся разреженной и фрагментированной: плотность мала, а число компонент связности заметно больше единицы. Это означает, что взаимодействия распределены по нескольким слабо связанным фрагментам, а не образуют единую плотную сеть.",
    )
    add_text_paragraph(
        document,
        f"Диаметр удалось вычислить лишь в небольшой части окон, поскольку в большинстве случаев граф несвязен. Именно поэтому для CollegeMsg диаметр часто отсутствует: метрика корректно определяется только для связного графа. Тест Дики–Фуллера показал, что ряд avg_degree стационарен (p-value = {summary['adf_avg_p']}), а ряд in_out_ratio_mean также прошёл проверку на стационарность (p-value = {summary['adf_ratio_p']}). Корреляция между avg_degree и n_components составила {summary['correlation']}, что указывает на сильную отрицательную связь между этими метриками.",
    )
    add_text_paragraph(
        document,
        f"Качество модели ARIMA на тестовой части: MAE = {summary['mae']}, RMSE = {summary['rmse']}. Модель хорошо воспроизводит общий уровень ряда, но отдельные колебания структуры сети предсказывает лишь приближённо, что типично для реальных разреженных сетевых данных.",
    )

    top_windows = und.nlargest(5, "avg_degree")[
        ["window_id", "time_start", "time_end", "avg_degree", "density", "n_components"]
    ].copy()
    top_windows["time_start"] = top_windows["time_start"].dt.strftime("%d.%m.%Y")
    top_windows["time_end"] = top_windows["time_end"].dt.strftime("%d.%m.%Y")
    top_windows["avg_degree"] = top_windows["avg_degree"].map(lambda x: f"{x:.4f}")
    top_windows["density"] = top_windows["density"].map(lambda x: f"{x:.4f}")
    top_windows["n_components"] = top_windows["n_components"].map(lambda x: int(x))

    add_text_paragraph(document, "Таблица 1 – Окна с максимальной средней степенью вершины.")
    add_table(document, top_windows)

    top_nodes = top_nodes.copy()
    top_nodes["mean_betweenness"] = top_nodes["mean_betweenness"].map(lambda x: f"{x:.6f}")
    add_text_paragraph(document, "Таблица 2 – Вершины с максимальной средней центральностью по посредничеству.")
    add_table(document, top_nodes)

    arima_test = arima_test.copy()
    arima_test["time"] = arima_test["time"].dt.strftime("%d.%m.%Y")
    arima_test["actual"] = arima_test["actual"].map(lambda x: f"{x:.4f}")
    arima_test["predicted"] = arima_test["predicted"].map(lambda x: f"{x:.4f}")
    arima_test["abs_error"] = arima_test["abs_error"].map(lambda x: f"{x:.4f}")
    add_text_paragraph(document, "Таблица 3 – Сравнение прогноза ARIMA с фактическими значениями.")
    add_table(document, arima_test)

    arima_future = arima_future.copy()
    arima_future["time"] = arima_future["time"].dt.strftime("%d.%m.%Y")
    arima_future["forecast"] = arima_future["forecast"].map(lambda x: f"{x:.4f}")
    add_text_paragraph(document, "Таблица 4 – Прогноз ARIMA на следующие окна.")
    add_table(document, arima_future)

    add_image(document, IMAGE_DIR / "metrics_timeseries.png", "Рисунок 6 – Временные ряды графовых метрик", 16.0)
    add_image(document, IMAGE_DIR / "betweenness_top_nodes.png", "Рисунок 7 – Временные ряды centrality betweenness для ключевых вершин", 16.0)
    add_image(document, IMAGE_DIR / "decomposition.png", "Рисунок 8 – Декомпозиция ряда avg_degree", 16.0)
    add_image(document, IMAGE_DIR / "sma.png", "Рисунок 9 – Скользящее среднее для avg_degree", 16.0)
    add_image(document, IMAGE_DIR / "arima_forecast.png", "Рисунок 10 – Прогноз ARIMA", 16.0)

    add_heading(document, "6. Выводы", 1)
    add_text_paragraph(
        document,
        "В ходе выполнения лабораторной работы был проведён анализ динамического графа на основе реального датасета CollegeMsg, использованного как замена синтетических данных в рамках дополнительного задания. Последовательность событий была разбита на окна по 50 событий, после чего для каждого окна построен граф и рассчитаны основные графовые характеристики.",
    )
    add_text_paragraph(
        document,
        "Полученные метрики были представлены как временные ряды и проанализированы методами визуализации, теста Дики–Фуллера, декомпозиции, скользящего среднего и ARIMA. Для реального датасета сеть оказалась разреженной и фрагментированной: плотность невелика, число компонент часто велико, а диаметр в большинстве окон не вычисляется из-за несвязности графа.",
    )
    add_text_paragraph(
        document,
        "Сильная отрицательная корреляция между avg_degree и n_components подтверждает, что увеличение числа связей уменьшает фрагментацию графа. Ряды avg_degree, in_out_ratio_mean и betweenness для вершины-лидера были дополнительно проверены на стационарность, а прогноз ARIMA позволил сравнить ожидаемое поведение ряда с фактическими значениями.",
    )
    add_text_paragraph(
        document,
        "Полученные результаты позволяют сделать обоснованные выводы о динамике структуры сети и показать применение методов аналитики графов и временных рядов на практическом наборе данных. Дополнительные пункты задания про реальный датасет, betweenness, корреляцию, ARIMA и анализ in/out-степеней также были рассмотрены в рамках отчёта.",
    )

    add_heading(document, "7. Ответы на контрольные вопросы", 1)
    control_text = (REPORT_DIR / "control_questions.md").read_text(encoding="utf-8")
    current_title = None
    current_lines: list[str] = []
    for line in control_text.splitlines():
        if line.startswith("## "):
            if current_title:
                add_heading(document, current_title, 2)
                for body_line in current_lines:
                    if body_line.strip():
                        add_text_paragraph(document, body_line.strip())
            current_title = line[3:]
            current_lines = []
        elif line.startswith("# "):
            continue
        else:
            current_lines.append(line)
    if current_title:
        add_heading(document, current_title, 2)
        for body_line in current_lines:
            if body_line.strip():
                add_text_paragraph(document, body_line.strip())

    add_page_break(document)
    add_heading(document, "8. Листинг исходного кода", 1)
    for file_path, title in [
        (PROJECT_ROOT / "lab07.py", "Листинг 1 – lab07.py"),
        (PROJECT_ROOT / "src" / "config.py", "Листинг 2 – src/config.py"),
        (PROJECT_ROOT / "src" / "data_loader.py", "Листинг 3 – src/data_loader.py"),
        (PROJECT_ROOT / "src" / "graph_metrics.py", "Листинг 4 – src/graph_metrics.py"),
        (PROJECT_ROOT / "src" / "time_series_analysis.py", "Листинг 5 – src/time_series_analysis.py"),
        (PROJECT_ROOT / "src" / "main.py", "Листинг 6 – src/main.py"),
    ]:
        add_code_listing(document, file_path, title)
        document.add_section(WD_SECTION.NEW_PAGE)

    return document


def main() -> None:
    document = build_document()
    document.save(OUTPUT_DOCX)


if __name__ == "__main__":
    main()
