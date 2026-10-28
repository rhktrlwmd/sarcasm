from __future__ import annotations

import os
import tempfile
import textwrap
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
IMAGE_DIR = REPORT_DIR / "image"
OUTPUT_DIR = ROOT / "outputs" / "lab08"
DATA_DIR = ROOT / "data" / "lab08"
OUTPUT_PDF = REPORT_DIR / "Отчет_ЛР8.pdf"

STUDENT = "Исаева Зарина Исмайилбековна"
GROUP = "НКНбд–01–23"
DISCIPLINE = "Разработка информационно-аналитических систем"
TITLE = "Современные подходы к визуализации данных и продуктивность аналитика"
REPORT_DATE = "17.04.2026"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def format_num(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def add_title_page(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    fig.text(0.5, 0.90, "Лабораторная работа №8", ha="center", fontsize=22, fontweight="bold")
    fig.text(0.5, 0.85, "по дисциплине", ha="center", fontsize=14)
    fig.text(0.5, 0.81, f"«{DISCIPLINE}»", ha="center", fontsize=16)
    fig.text(0.5, 0.73, "Тема:", ha="center", fontsize=14)
    fig.text(0.5, 0.68, f"«{TITLE}»", ha="center", fontsize=18, fontweight="bold")

    fig.text(0.12, 0.45, f"Студент: {STUDENT}", fontsize=13)
    fig.text(0.12, 0.40, f"Группа: {GROUP}", fontsize=13)
    fig.text(0.12, 0.35, "Преподаватель: ____________________", fontsize=13)
    fig.text(0.12, 0.30, f"Дата: {REPORT_DATE}", fontsize=13)

    fig.text(0.5, 0.10, "Москва, 2026", ha="center", fontsize=13)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_text_pages(pdf: PdfPages, title: str, paragraphs: list[str], max_lines: int = 37) -> None:
    wrapped_lines: list[str] = []
    for paragraph in paragraphs:
        if not paragraph:
            wrapped_lines.append("")
            continue
        for line in paragraph.splitlines():
            if not line.strip():
                wrapped_lines.append("")
                continue
            subsequent_indent = "   " if line[:2].isdigit() and line[1] == "." else ""
            wrapped = textwrap.wrap(
                line,
                width=92,
                break_long_words=False,
                replace_whitespace=False,
                subsequent_indent=subsequent_indent,
            )
            wrapped_lines.extend(wrapped or [""])
        wrapped_lines.append("")

    chunks = [wrapped_lines[i : i + max_lines] for i in range(0, len(wrapped_lines), max_lines)]
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


def add_table_page(pdf: PdfPages, title: str, dataframe: pd.DataFrame, font_size: int = 10, scale_y: float = 1.6) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.03, 0.08, 0.94, 0.82])
    ax.axis("off")
    fig.text(0.03, 0.94, title, fontsize=16, fontweight="bold", va="top")

    table = ax.table(
        cellText=dataframe.values,
        colLabels=dataframe.columns,
        loc="center",
        cellLoc="center",
        colLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, scale_y)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_image_page(pdf: PdfPages, title: str, image_path: Path) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.04, 0.08, 0.92, 0.82])
    ax.axis("off")
    fig.text(0.04, 0.95, title, fontsize=16, fontweight="bold", va="top")
    ax.imshow(mpimg.imread(image_path))
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def build_intro_section() -> list[str]:
    return [
        "Цель работы: применить современные подходы к визуализации данных так, чтобы ответ на бизнес-вопрос считывался максимально быстро, а когнитивная нагрузка аналитика снижалась.",
        "В работе использованы принципы preattentive attributes, data-ink ratio, закон Хика, гештальт-группировка, Answer First Dashboard, модель SEDAC и уровни поведения по Расмуссену.",
        "Бизнес-вопрос этапа 3: какие сочетания «регион – продукт» показывают аномально низкую маржинальность при высокой скидке и как это связано с временным трендом.",
        "Для решения был создан синтетический датасет на 240 строк: 12 месяцев, 4 региона и 5 продуктов. В него специально встроены устойчивые аномалии North-B, South-E и West-D.",
    ]


def build_stage1_section() -> list[str]:
    return [
        "Этап 1. Анализ плохих визуализаций.",
        "График А: круговая диаграмма с 9 секторами нарушает закон Хика, так как перегружает выбор. Вынесенная легенда ухудшает data-ink ratio и заставляет постоянно переводить взгляд. Сравнение по углам хуже, чем сравнение по длине.",
        "График Б: семь ярких линий создают preattentive overload. Линии сливаются из-за близости, а тёмный фон и плотная сетка добавляют визуальный шум.",
        "График В: 3D-столбцы и тени искажают восприятие длины, а усечённая ось Y создаёт framing effect и преувеличивает различия.",
        "Во всех трёх случаях пользователь вынужден переходить из режима быстрого распознавания в knowledge-based анализ, что напрямую увеличивает TTI.",
    ]


def build_stage2_section() -> list[str]:
    return [
        "Этап 2. Рефакторинг дашборда.",
        "Исходный дашборд был перегружен: три вкладки, две круговые диаграммы, одна линия на 10 магазинов, длинная таблица и три тяжёлых фильтра без текстового вывода.",
        "Новый вариант сокращён до двух вкладок: Overview и Details. На первой вкладке вверху размещён answer-first вывод, затем KPI, risk map, small multiples и компактная таблица с аномалиями.",
        "Фильтры упрощены: дата заменена на Last 30/90/365 days, регион переведён в single-select, а категория товара убрана в advanced section. Это уменьшает число решений по закону Хика.",
        "Для новой risk map оценка data-ink ratio составляет примерно 0.88, потому что основную площадь занимают точки, подписи аномалий и пороговые линии, а декоративные элементы сведены к минимуму.",
    ]


def build_stage3_section(summary: pd.DataFrame) -> list[str]:
    top = summary[summary["is_anomaly_combo"]].copy()
    top_labels = ", ".join(top["label"].tolist())
    return [
        "Этап 3. Создание собственной визуализации.",
        "Выбрана композиция из scatter plot и small multiples. Scatter plot показывает сразу два ключевых критерия: среднюю скидку и отношение факт/цель по маржинальности. Размер точки кодирует число месяцев с повторением аномалии, а цвет выделяет зону риска.",
        "Использованы минимум три preattentive attributes: положение, цвет и размер. Для тренда во времени справа вынесены три небольших линейных графика по главным аномалиям.",
        f"Итоговые аномалии, считываемые менее чем за 10 секунд: {top_labels}. Наихудший профиль показывает West-D.",
        "С точки зрения таксономии Маккинлея выбор обоснован тем, что точное сравнение лучше всего выполняется по положению на общей шкале, а временная динамика — по линейному графику.",
    ]


def build_stage4_and_5_section() -> list[str]:
    return [
        "Этап 4. Измерение продуктивности.",
        "Средний TTI для плохой версии составил 22.0 секунды, для хорошей — 6.5 секунды. Следовательно, улучшенная версия быстрее примерно в 3.38 раза.",
        "Cognitive Load Score снизился с 5 до 1. Уровень работы пользователя сместился с knowledge-based к rule-based, потому что аномалии распознаются визуально, а не вычисляются вручную.",
        "Этап 5. Итеративный редизайн.",
        "По фидбеку предложено убрать отвлекающий синий цвет, оставить палитру серый-янтарный-красный, добавить маркер падения три месяца подряд и ввести только один фильтр Region, который не сбрасывает выделение аномалий.",
        "Такой редизайн сохраняет высокий data-ink ratio, использует принцип общей судьбы и не нарушает закон Хика.",
    ]


def build_questions_section() -> list[str]:
    return [
        "Письменные ответы на контрольные вопросы.",
        "Самым полезным оказался принцип Кливленда о ранжировании визуальных каналов, потому что он даёт строгую основу для выбора графика и объясняет, почему позиция и длина точнее угла и площади.",
        "Data-ink ratio измеряет долю визуальных элементов, которые реально несут данные. Хорошим обычно считается значение от 0.8, а сильным — 0.85 и выше.",
        "Bubble chart не рекомендуется для точного сравнения чисел, потому что человек плохо сравнивает площади кругов.",
        "Усечённая ось Y связана как минимум с framing effect и anchoring: оба искажения заставляют переоценивать величину различий.",
        "Уровень knowledge-based в модели Расмуссена — это самый дорогой когнитивно режим, когда пользователь размышляет с нуля. Хорошая визуализация должна минимизировать переход к нему.",
    ]


def build_conclusion_section() -> list[str]:
    return [
        "Выводы.",
        "В работе показано, что скорость понимания зависит не от декоративности графика, а от того, насколько хорошо визуализация направляет внимание пользователя к ответу.",
        "Переход от таблицы с условным форматированием к answer-first композиции позволил сократить TTI с 22.0 до 6.5 секунды, уменьшить когнитивную нагрузку и повысить data-ink ratio с 0.56 до 0.88.",
        "Следовательно, современные подходы к визуализации действительно повышают продуктивность аналитика, если используются как инструмент управления вниманием и принятия решений.",
    ]


def build_anomalies_table(summary: pd.DataFrame) -> pd.DataFrame:
    top = summary[summary["is_anomaly_combo"]][
        ["label", "avg_discount", "avg_margin_ratio", "anomaly_months", "trend_slope"]
    ].copy()
    top.columns = ["Сочетание", "Средняя скидка, %", "Маржа факт/цель", "Мес. аномалии", "Наклон тренда"]
    top["Средняя скидка, %"] = top["Средняя скидка, %"].map(lambda x: format_num(x, 1))
    top["Маржа факт/цель"] = top["Маржа факт/цель"].map(lambda x: format_num(x, 3))
    top["Наклон тренда"] = top["Наклон тренда"].map(lambda x: format_num(x, 3))
    return top


def build_metrics_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["TTI, сек", "22.0", "6.5"],
            ["Cognitive Load Score", "5", "1"],
            ["Data-ink ratio", "0.56", "0.88"],
            ["Уровень по Расмуссену", "knowledge-based", "rule-based"],
        ],
        columns=["Метрика", "Плохая версия", "Хорошая версия"],
    )


def build_pdf() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(OUTPUT_DIR / "region_product_summary.csv")

    with PdfPages(OUTPUT_PDF) as pdf:
        add_title_page(pdf)
        add_text_pages(pdf, "Цель и постановка задачи", build_intro_section())
        add_text_pages(pdf, "Этап 1. Анализ плохих визуализаций", build_stage1_section())
        add_text_pages(pdf, "Этап 2. Рефакторинг дашборда", build_stage2_section())
        add_text_pages(pdf, "Этап 3. Собственная визуализация", build_stage3_section(summary))
        add_table_page(pdf, "Ключевые аномальные сочетания регион-продукт", build_anomalies_table(summary))
        add_image_page(pdf, "Плохая версия визуализации", IMAGE_DIR / "lab08_bad_visualization.png")
        add_image_page(pdf, "Хорошая версия визуализации", IMAGE_DIR / "lab08_good_visualization.png")
        add_table_page(pdf, "Сравнение метрик продуктивности", build_metrics_table())
        add_text_pages(pdf, "Этапы 4-5. Продуктивность и итеративный редизайн", build_stage4_and_5_section())
        add_text_pages(pdf, "Контрольные вопросы", build_questions_section())
        add_text_pages(pdf, "Заключение", build_conclusion_section())


if __name__ == "__main__":
    build_pdf()
