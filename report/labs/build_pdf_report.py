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
PLOTS_DIR = ROOT / "outputs" / "plots"
DATA_DIR = ROOT / "data" / "processed"
OUTPUT_PDF = REPORT_DIR / "Отчет_ЛР7.pdf"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def load_context() -> dict[str, object]:
    und = pd.read_csv(DATA_DIR / "metrics_undirected.csv", parse_dates=["time_start", "time_end", "time"])
    directed = pd.read_csv(DATA_DIR / "metrics_directed.csv")
    top_nodes = pd.read_csv(DATA_DIR / "top_betweenness_nodes.csv")
    arima_test = pd.read_csv(DATA_DIR / "arima_test_comparison.csv", parse_dates=["time"])
    arima_future = pd.read_csv(DATA_DIR / "arima_future_forecast.csv", parse_dates=["time"])
    events = pd.read_csv(DATA_DIR / "events_used.csv", parse_dates=["timestamp"])

    return {
        "und": und,
        "directed": directed,
        "top_nodes": top_nodes,
        "arima_test": arima_test,
        "arima_future": arima_future,
        "events": events,
    }


def format_num(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def add_title_page(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    fig.text(0.5, 0.88, "Лабораторная работа №7", ha="center", fontsize=22, fontweight="bold")
    fig.text(0.5, 0.83, "по дисциплине", ha="center", fontsize=14)
    fig.text(0.5, 0.79, "«Разработка информационно-аналитических систем»", ha="center", fontsize=16)
    fig.text(0.5, 0.72, "Тема:", ha="center", fontsize=14)
    fig.text(0.5, 0.67, "«Аналитика графов и временных рядов»", ha="center", fontsize=18, fontweight="bold")

    fig.text(0.14, 0.44, "Студент: ____________________", fontsize=13)
    fig.text(0.14, 0.39, "Группа: ____________________", fontsize=13)
    fig.text(0.14, 0.34, "Преподаватель: ____________________", fontsize=13)

    fig.text(0.5, 0.10, "Москва, 2026", ha="center", fontsize=13)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_text_pages(pdf: PdfPages, title: str, paragraphs: list[str], max_lines: int = 38) -> None:
    wrapped_lines: list[str] = []
    for paragraph in paragraphs:
        if not paragraph:
            wrapped_lines.append("")
            continue
        for line in paragraph.splitlines():
            if not line.strip():
                wrapped_lines.append("")
                continue
            initial_indent = ""
            subsequent_indent = ""
            if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or line.startswith("5.") or line.startswith("6.") or line.startswith("7.") or line.startswith("8.") or line.startswith("9."):
                subsequent_indent = "   "
            wrapped = textwrap.wrap(
                line,
                width=94,
                break_long_words=False,
                replace_whitespace=False,
                initial_indent=initial_indent,
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


def add_table_page(pdf: PdfPages, title: str, dataframe: pd.DataFrame, font_size: int = 10) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.03, 0.08, 0.94, 0.82])
    ax.axis("off")
    fig.text(0.03, 0.94, title, fontsize=16, fontweight="bold", va="top")

    table = ax.table(
        cellText=dataframe.values,
        colLabels=dataframe.columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.5)
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


def build_intro_section(ctx: dict[str, object]) -> list[str]:
    events = ctx["events"]
    return [
        "Цель работы: изучить методы анализа динамических графов и временных рядов на реальном наборе событий взаимодействия между узлами, представить графовые характеристики как временные ряды, проверить их стационарность, выполнить декомпозицию и прогнозирование.",
        "Краткое теоретическое обоснование. Динамический граф — это граф, структура которого меняется во времени. Для каждого временного окна можно строить отдельный граф-снимок и вычислять его характеристики: среднюю степень, плотность, коэффициент кластеризации, число компонент связности, диаметр и центральность по посредничеству.",
        "Временной ряд — последовательность значений, упорядоченных во времени. Для временных рядов важны проверка стационарности, выделение тренда и сезонности, а также прогнозирование. В лабораторной работе использовались тест Дики–Фуллера, аддитивная декомпозиция, скользящее среднее и модель ARIMA.",
        "Постановка задачи:",
        "1. Заменить синтетический датасет реальным.",
        "2. Разбить временную шкалу на равные интервалы.",
        "3. Для каждого окна построить граф.",
        "4. Рассчитать графовые метрики и представить их в виде временных рядов.",
        "5. Проверить стационарность, выделить тренд и сезонность, построить прогноз.",
        "6. Дополнительно проанализировать центральность по посредничеству, корреляцию метрик и отношение in/out степеней.",
        f"Описание данных. Использован датасет CollegeMsg: {len(events):,} событий, {len(set(events['source']).union(set(events['target']))):,} узлов, период наблюдения с {events['timestamp'].min().strftime('%d.%m.%Y')} по {events['timestamp'].max().strftime('%d.%m.%Y')}. Для анализа выбраны равные окна длиной 7 дней.",
    ]


def build_method_section() -> list[str]:
    return [
        "Этапы выполнения работы:",
        "1. Загрузка реального датасета из файла CollegeMsg.txt.gz и преобразование UNIX-времени в datetime.",
        "2. Разбиение событий на равные недельные интервалы времени. Это исправляет типичную ошибку, когда данные режут по фиксированному числу событий, а не по шкале времени.",
        "3. Построение для каждого окна неориентированного и ориентированного графа.",
        "4. Расчёт набора метрик: avg_degree, density, avg_clustering, n_components, diameter, betweenness_mean, betweenness_max, in_out_ratio_mean.",
        "5. Формирование отдельной таблицы с центральностью по посредничеству для каждой вершины во всех окнах.",
        "6. Построение временных рядов, тест Дики–Фуллера, аддитивная декомпозиция, сглаживание скользящим средним и прогноз ARIMA(1,1,1).",
        "Ключевые фрагменты кода:",
        "load_events_file(...): чтение файла, нормализация временных меток, сортировка событий.",
        "split_into_time_windows(...): определение window_id по разности timestamp и начала временной шкалы.",
        "compute_metrics_table(...): вычисление графовых метрик и формирование таблицы centrality по вершинам.",
        "fit_arima(...): разделение ряда на train/test, прогноз на тестовой выборке и несколько шагов вперёд.",
    ]


def build_results_section(ctx: dict[str, object]) -> list[str]:
    und = ctx["und"]
    directed = ctx["directed"]
    top_nodes = ctx["top_nodes"]
    return [
        "Основные результаты анализа:",
        f"1. Получено {len(und)} временных окон.",
        f"2. Средняя степень вершины: {format_num(und['avg_degree'].mean())}, диапазон от {format_num(und['avg_degree'].min())} до {format_num(und['avg_degree'].max())}.",
        f"3. Средняя плотность графа: {format_num(und['density'].mean())}.",
        f"4. Средний коэффициент кластеризации: {format_num(und['avg_clustering'].mean())}.",
        f"5. Среднее число компонент связности: {format_num(und['n_components'].mean())}, минимум {int(und['n_components'].min())}, максимум {int(und['n_components'].max())}.",
        "6. Диаметр не был вычислен ни в одном окне, поскольку граф оставался несвязным на всём периоде наблюдения.",
        f"7. Среднее значение betweenness_mean: {format_num(und['betweenness_mean'].mean())}.",
        f"8. Среднее значение in_out_ratio_mean: {format_num(directed['in_out_ratio_mean'].dropna().mean())}.",
        f"9. Вершина с наибольшей средней центральностью по посредничеству: {top_nodes.iloc[0]['node']} ({format_num(top_nodes.iloc[0]['mean_betweenness'], 6)}).",
        "Интерпретация. В начале периода сеть была существенно плотнее, затем avg_degree и density снижались, а число компонент возрастало. Это означает постепенную фрагментацию сети и снижение интенсивности связей.",
    ]


def build_stationarity_section() -> list[str]:
    summary_text = (ROOT / "outputs" / "summary.txt").read_text(encoding="utf-8")
    return [
        "Результаты проверки стационарности и прогноза извлечены из итоговой сводки.",
        summary_text,
        "Интерпретация. Ряд avg_degree признан стационарным, тогда как среднее отношение in/out степеней и временной ряд центральности вершины-лидера нестационарны. Это означает, что общая связность сети меняется относительно умеренно, а направленность взаимодействий и влияние отдельных посредников меняются значительно сильнее.",
        "По ARIMA видно, что модель улавливает общий нисходящий уровень ряда, но на тестовой части систематически завышает значения. Поэтому прогноз можно считать рабочим, но умеренно точным.",
    ]


def build_conclusion_section() -> list[str]:
    return [
        "Выводы:",
        "1. Лабораторная работа выполнена на реальном датасете CollegeMsg, как требовалось в задании.",
        "2. Разбиение данных выполнено по равным временным интервалам, что соответствует постановке задачи.",
        "3. Структура графа со временем стала более разреженной: средняя степень и плотность снижались, а число компонент связности росло.",
        "4. Коэффициент кластеризации оставался низким, поэтому устойчивые локальные группы выражены слабо.",
        "5. Сильная отрицательная корреляция между avg_degree и n_components подтверждает, что рост числа связей уменьшает фрагментацию сети.",
        "6. Анализ betweenness показал наличие вершин-посредников, но их влияние заметно менялось во времени.",
        "7. Ряд avg_degree оказался стационарным, а in_out_ratio_mean и betweenness вершины-лидера — нестационарными.",
        "8. Модель ARIMA дала приемлемый прогноз по тренду, но без высокой точности на тестовой выборке.",
    ]


def build_control_questions_pages() -> list[tuple[str, list[str]]]:
    text = (REPORT_DIR / "control_questions.md").read_text(encoding="utf-8")
    chunks: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_title:
                chunks.append((current_title, current_lines))
            current_title = line[3:]
            current_lines = []
        elif line.startswith("# "):
            continue
        else:
            current_lines.append(line)
    if current_title:
        chunks.append((current_title, current_lines))

    return chunks


def build_pdf() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ctx = load_context()
    und = ctx["und"]
    top_nodes = ctx["top_nodes"].copy()
    arima_test = ctx["arima_test"].copy()
    arima_future = ctx["arima_future"].copy()

    top_windows = (
        und.nlargest(5, "avg_degree")[["window_id", "time_start", "time_end", "avg_degree", "density", "n_components"]]
        .copy()
    )
    top_windows["time_start"] = top_windows["time_start"].dt.strftime("%d.%m.%Y")
    top_windows["time_end"] = top_windows["time_end"].dt.strftime("%d.%m.%Y")
    top_windows["avg_degree"] = top_windows["avg_degree"].map(lambda x: format_num(x))
    top_windows["density"] = top_windows["density"].map(lambda x: format_num(x))

    top_nodes["mean_betweenness"] = top_nodes["mean_betweenness"].map(lambda x: format_num(x, 6))

    arima_test["time"] = arima_test["time"].dt.strftime("%d.%m.%Y")
    arima_test["actual"] = arima_test["actual"].map(lambda x: format_num(x))
    arima_test["predicted"] = arima_test["predicted"].map(lambda x: format_num(x))
    arima_test["abs_error"] = arima_test["abs_error"].map(lambda x: format_num(x))

    arima_future["time"] = arima_future["time"].dt.strftime("%d.%m.%Y")
    arima_future["forecast"] = arima_future["forecast"].map(lambda x: format_num(x))

    with PdfPages(OUTPUT_PDF) as pdf:
        add_title_page(pdf)
        add_text_pages(pdf, "Цель, теория и постановка задачи", build_intro_section(ctx))
        add_text_pages(pdf, "Методика выполнения работы", build_method_section())
        add_text_pages(pdf, "Результаты и интерпретация", build_results_section(ctx))
        add_table_page(pdf, "Топ-5 окон по средней степени вершины", top_windows)
        add_table_page(pdf, "Топ-5 вершин по средней centrality betweenness", top_nodes)
        add_text_pages(pdf, "Стационарность и прогнозирование", build_stationarity_section())
        add_table_page(pdf, "Сравнение ARIMA с фактическими значениями", arima_test)
        add_table_page(pdf, "Прогноз ARIMA на 4 шага вперёд", arima_future)
        add_image_page(pdf, "Временные ряды графовых метрик", PLOTS_DIR / "metrics_timeseries.png")
        add_image_page(pdf, "Временные ряды betweenness для ключевых вершин", PLOTS_DIR / "betweenness_top_nodes.png")
        add_image_page(pdf, "Декомпозиция ряда avg_degree", PLOTS_DIR / "decomposition.png")
        add_image_page(pdf, "Скользящее среднее для avg_degree", PLOTS_DIR / "sma.png")
        add_image_page(pdf, "Прогноз ARIMA", PLOTS_DIR / "arima_forecast.png")
        add_text_pages(pdf, "Выводы", build_conclusion_section())

        for title, lines in build_control_questions_pages():
            add_text_pages(pdf, title, ["\n".join(lines)])


if __name__ == "__main__":
    build_pdf()
