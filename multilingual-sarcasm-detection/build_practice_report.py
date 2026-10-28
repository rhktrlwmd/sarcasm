from __future__ import annotations

import csv
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt


PROJECT_ROOT = Path("/Users/rhktrlwmd/Documents/New project/multilingual-sarcasm-detection")
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUT_PATH = RESULTS_DIR / "report_practice_sarcasm_detection.docx"
MODEL_METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"
MODEL_COMPARISON_PATH = RESULTS_DIR / "model_comparison.csv"
CLASSIFICATION_REPORT_PATH = RESULTS_DIR / "classification_report.txt"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "confusion_matrix.png"
MODEL_COMPARISON_PLOT_PATH = RESULTS_DIR / "model_comparison.png"


def add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char_begin)
    run._r.append(instr_text)
    run._r.append(fld_char_end)


def add_toc(paragraph) -> None:
    run = paragraph.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = 'TOC \\o "1-3" \\h \\z \\u'
    fld_char_separate = OxmlElement("w:fldChar")
    fld_char_separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Оглавление будет обновлено при открытии документа."
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char_begin)
    run._r.append(instr_text)
    run._r.append(fld_char_separate)
    run._r.append(placeholder)
    run._r.append(fld_char_end)


def set_document_defaults(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    section.different_first_page_header_footer = True

    footer = section.footer
    footer_para = footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(footer_para)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(14)
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.first_line_indent = Cm(1)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.space_after = Pt(0)

    for style_name in ["Heading 1", "Heading 2", "Heading 3"]:
        style = styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.bold = True
        style.font.size = Pt(14)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.first_line_indent = Cm(0)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)


def add_center_paragraph(doc: Document, text: str, bold: bool = False, size: int = 14) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.5
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)


def add_body_paragraph(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph(style="Normal")
    paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.first_line_indent = Cm(1)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.add_run(text)


def add_caption(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.5
    run = paragraph.add_run(text)
    run.bold = True
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(14)


def add_table(doc: Document, rows: list[list[str]]) -> None:
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    table.autofit = True
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.text = value
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.line_spacing = 1.5
                paragraph.paragraph_format.first_line_indent = Cm(0)
                if row_idx == 0:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in paragraph.runs:
                    run.font.name = "Times New Roman"
                    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
                    run.font.size = Pt(13)
                    if row_idx == 0:
                        run.bold = True


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="Normal")
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(1)
        paragraph.paragraph_format.line_spacing = 1.5
        paragraph.add_run(f"– {item}")


def add_code_block(doc: Document, code_text: str) -> None:
    for line in code_text.strip("\n").splitlines():
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(1)
        paragraph.paragraph_format.line_spacing = 1.15
        run = paragraph.add_run(line)
        run.font.name = "Courier New"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")
        run.font.size = Pt(10)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_classification_report(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_list() -> list[str]:
    access_date = "03.06.2026"
    return [
        f"Jurafsky D., Martin J. H. Speech and Language Processing. URL: https://web.stanford.edu/~jurafsky/slp3/ed3book.pdf (дата обращения: {access_date}).",
        f"pandas documentation. Getting started. URL: https://pandas.pydata.org/pandas-docs/stable/getting_started/index.html (дата обращения: {access_date}).",
        f"NumPy documentation. URL: https://numpy.org/doc/stable/ (дата обращения: {access_date}).",
        f"Manning C. D., Raghavan P., Schutze H. Introduction to Information Retrieval. URL: https://nlp.stanford.edu/IR-book/ (дата обращения: {access_date}).",
        f"scikit-learn documentation. LogisticRegression. URL: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html (дата обращения: {access_date}).",
        f"scikit-learn documentation. LinearSVC. URL: https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html (дата обращения: {access_date}).",
        f"scikit-learn documentation. Naive Bayes. URL: https://scikit-learn.org/stable/modules/naive_bayes.html (дата обращения: {access_date}).",
        f"scikit-learn documentation. TfidfVectorizer. URL: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html (дата обращения: {access_date}).",
        f"Joshi A., Bhattacharyya P., Carman M. J. Automatic Sarcasm Detection: A Survey. URL: https://arxiv.org/abs/1602.03426 (дата обращения: {access_date}).",
        f"Ghanem B., Karoui J., Benamara F., Moriceau V., Rosso P. Irony Detection in a Multilingual Context. URL: https://arxiv.org/abs/2002.02427 (дата обращения: {access_date}).",
    ]


def get_code_snippet(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1:end])


def add_title_page(doc: Document) -> None:
    add_center_paragraph(doc, "Федеральное государственное автономное образовательное учреждение", size=14)
    add_center_paragraph(doc, "высшего образования", size=14)
    add_center_paragraph(doc, "«РОССИЙСКИЙ УНИВЕРСИТЕТ ДРУЖБЫ НАРОДОВ", bold=True, size=14)
    add_center_paragraph(doc, "ИМЕНИ ПАТРИСА ЛУМУМБЫ»", bold=True, size=14)
    add_center_paragraph(doc, "(РУДН)", size=14)
    doc.add_paragraph()
    add_center_paragraph(doc, "ОТЧЕТ", bold=True, size=16)
    add_center_paragraph(
        doc,
        "о прохождении Учебной практики\n(Научно-исследовательская работа\n(получение первичных навыков научно-исследовательской работы)))",
        bold=True,
        size=14,
    )
    add_center_paragraph(doc, "(вид и наименование практики)", size=12)
    doc.add_paragraph()
    add_center_paragraph(doc, "Исаева Зарина Исмайилбековна", size=14)
    add_center_paragraph(doc, "(Ф.И.О. обучающегося)", size=12)
    add_body_paragraph(doc, "Основное учебное подразделение: факультет физико-математических и естественных наук.")
    add_body_paragraph(doc, "Направление/специальность: 02.03.01 «Математика и компьютерные науки».")
    add_body_paragraph(doc, "Курс, группа: 3 курс, НКНбд–01–023.")
    add_body_paragraph(
        doc,
        "Место прохождения практики: Научный центр вычислительных методов и моделирования киберфизических систем РУДН.",
    )
    add_body_paragraph(doc, "Сроки прохождения практики: c 07.02.2026 г. по 13.06.2026 г.")
    add_body_paragraph(doc, "Руководитель практики от РУДН: Кройтор О.К., асс. каф. ММиИИ.")
    add_body_paragraph(doc, "Руководитель практики от организации: проф. Самуйлов К.Е., директор ИКНиТ.")
    add_body_paragraph(doc, "Оценка: ____________________.")
    doc.add_paragraph()
    add_center_paragraph(doc, "Москва 2026 г.", size=14)
    doc.add_page_break()


def build_report() -> Path:
    metadata = load_metadata(MODEL_METADATA_PATH)
    model_rows = read_csv_rows(MODEL_COMPARISON_PATH)

    doc = Document()
    set_document_defaults(doc)
    add_title_page(doc)

    doc.add_heading("Оглавление", level=1)
    toc_paragraph = doc.add_paragraph()
    toc_paragraph.paragraph_format.first_line_indent = Cm(0)
    add_toc(toc_paragraph)
    doc.add_page_break()

    doc.add_heading("Список сокращений", level=1)
    doc.add_heading("Русскоязычные сокращения", level=2)
    add_table(
        doc,
        [
            ["Сокращение", "Расшифровка"],
            ["РУДН", "Российский университет дружбы народов имени Патриса Лумумбы"],
            ["ИИ", "искусственный интеллект"],
            ["НИР", "научно-исследовательская работа"],
            ["ВКР", "выпускная квалификационная работа"],
        ],
    )
    doc.add_heading("Англоязычные сокращения", level=2)
    add_table(
        doc,
        [
            ["Abbreviation", "Meaning"],
            ["NLP", "Natural Language Processing"],
            ["TF-IDF", "Term Frequency – Inverse Document Frequency"],
            ["SVM", "Support Vector Machine"],
            ["CSV", "Comma-Separated Values"],
            ["JSON", "JavaScript Object Notation"],
        ],
    )

    doc.add_heading("Список основных обозначений", level=1)
    add_table(
        doc,
        [
            ["Обозначение", "Смысл"],
            ["x", "текстовое сообщение, подаваемое на вход модели"],
            ["y", "класс сообщения: 0 — не сарказм, 1 — сарказм"],
            ["N", "общее количество объектов выборки"],
            ["n-грамма", "последовательность из n символов текста"],
            ["p(y=1|x)", "оценка вероятности сарказма для текста x"],
        ],
    )

    doc.add_heading("Введение", level=1)
    add_body_paragraph(
        doc,
        "Целью прохождения практики являлось получение практических навыков научно-исследовательской и проектной деятельности в области обработки естественного языка, машинного обучения и разработки программных систем для автоматического анализа текстовых данных. При выполнении практики использовались базовые подходы NLP и методы машинного обучения, применяемые для анализа текстов и решения задач классификации [1].",
    )
    add_body_paragraph(
        doc,
        "Место прохождения практики: Научный центр вычислительных методов и моделирования киберфизических систем РУДН. Сроки прохождения практики: с 07.02.2026 г. по 13.06.2026 г. Тема практики была связана с курсовым проектом «Разработка системы автоматического определения сарказма в многоязычных текстах методами машинного обучения». При этом практическая реализация и экспериментальная проверка в отчете ориентированы преимущественно на русскоязычные и англоязычные тексты.",
    )
    add_body_paragraph(
        doc,
        "В ходе практики выполнялась последовательная работа: анализ предметной области, изучение методов обработки текстов, подбор и объединение датасетов, программная реализация системы, проведение экспериментов и оформление полученных результатов. Для обработки данных и построения программной части проекта применялись библиотеки pandas [2], NumPy [3], scikit-learn [5–8] и дополнительные средства визуализации и сериализации моделей.",
    )
    add_body_paragraph(doc, "Последовательность прохождения практики, перечень работ, выполненных в процессе практики, представлены в таблице 1.1.")
    add_caption(doc, "Таблица 1.1 – Этапы прохождения практики")
    add_table(
        doc,
        [
            ["№", "Этап работы", "Содержание работы", "Результат"],
            ["1", "Изучение требований к отчету", "Анализ методических требований РУДН к отчету и приложениям", "Определена структура отчета"],
            ["2", "Анализ предметной области", "Изучение литературы по NLP и задачам классификации текста", "Сформирована теоретическая база"],
            ["3", "Изучение задачи определения сарказма", "Анализ особенностей сарказма как объекта автоматического распознавания", "Сформулирована постановка задачи"],
            ["4", "Подбор и подготовка датасетов", "Объединение англоязычных и русскоязычных наборов данных", "Сформирован корпус для обучения"],
            ["5", "Разработка структуры проекта", "Проектирование структуры каталогов и модулей системы", "Собран каркас программного проекта"],
            ["6", "Реализация модулей загрузки и обработки данных", "Создание модулей data_loader.py и preprocessing.py", "Реализована загрузка и очистка текста"],
            ["7", "Реализация TF-IDF-векторизации", "Преобразование текста в числовые признаки с помощью TF-IDF", "Подготовлено признаковое пространство"],
            ["8", "Обучение моделей машинного обучения", "Обучение Logistic Regression, Linear SVM и Naive Bayes", "Получены обученные модели"],
            ["9", "Сравнение моделей", "Сопоставление метрик Accuracy, F1-score, Precision и Recall", "Выбрана наилучшая модель"],
            ["10", "Тестирование системы", "Проверка на пользовательских примерах", "Оценена работа системы на коротких фразах"],
            ["11", "Подготовка отчета и приложений", "Оформление текста отчета, таблиц и приложений", "Подготовлен комплект отчетных материалов"],
        ],
    )

    doc.add_heading("1 Основная часть", level=1)
    doc.add_heading("1.1 Организация работы в процессе практики", level=2)
    add_body_paragraph(
        doc,
        "Работа в процессе практики была организована поэтапно. На начальном этапе был проведен обзор теоретических материалов по обработке естественного языка, задачам тонального анализа и автоматическому распознаванию сарказма. Далее была сформулирована практическая задача, определены требования к программной системе и подобраны исходные данные для обучения моделей.",
    )
    add_body_paragraph(
        doc,
        "Следующий этап включал подготовку данных и разработку модульной структуры проекта. Система реализовывалась на языке Python как набор взаимосвязанных модулей, отвечающих за загрузку данных, предварительную обработку текста, извлечение признаков, обучение моделей, вычисление метрик, прогнозирование и визуализацию результатов. Такой подход обеспечил понятную архитектуру проекта и возможность его дальнейшего расширения.",
    )
    add_body_paragraph(
        doc,
        "После реализации базовых модулей был выполнен цикл вычислительных экспериментов: обучение нескольких моделей машинного обучения, сравнение их качества на единых данных и тестирование системы на пользовательских примерах. На завершающем этапе были подготовлены результаты, сохранены артефакты экспериментов и оформлен итоговый отчет по практике.",
    )

    doc.add_heading("1.2 Постановка практической задачи", level=2)
    add_body_paragraph(
        doc,
        "В рамках практики была поставлена задача разработки программной системы, предназначенной для автоматического определения сарказма в текстовых сообщениях. Задача рассматривалась как задача бинарной классификации текста, где каждому тексту необходимо присвоить один из двух классов: «саркастичный» или «не саркастичный».",
    )
    add_body_paragraph(
        doc,
        "Формально каждому сообщению x сопоставлялась метка y, где 0 обозначает отсутствие сарказма, а 1 — наличие сарказма. Такая постановка соответствует классическим задачам классификации текстов и позволяет применять распространенные методы машинного обучения при наличии размеченных данных [4].",
    )
    add_body_paragraph(
        doc,
        "Особенность рассматриваемой задачи заключается в том, что сарказм часто выражается не прямым утверждением, а несоответствием между буквальным смыслом фразы и реальной коммуникативной ситуацией. Поэтому система должна учитывать не только отдельные слова, но и более мелкие структурные признаки, например символьные шаблоны, эмоциональные усилители, использование прописных букв и характерные речевые конструкции [9].",
    )

    doc.add_heading("1.3 Описание используемых данных", level=2)
    add_body_paragraph(
        doc,
        "Для обучения и тестирования системы использовались несколько датасетов, объединенных в единый корпус. В итоговую выборку вошли англоязычные заголовки с разметкой сарказма, русскоязычные новости без сарказма, русскоязычные сатирические заголовки, а также дополнительно собранный разговорный русский корпус саркастических и несаркастических реплик. Такой подход позволил увеличить разнообразие входных данных и учесть как нейтральный, так и разговорный стиль текста.",
    )
    add_body_paragraph(
        doc,
        f"По итогам подготовки данных общее количество объектов составило {metadata['total_samples']}. Из них {metadata['train_samples']} объектов использовались для обучения, а {metadata['test_samples']} — для тестирования. Количество использованных исходных файлов составило {len(metadata['source_files'])}. Задача классификации является бинарной, поскольку каждому объекту присваивается один из двух классов.",
    )
    add_caption(doc, "Таблица 1.2 – Основные характеристики датасета")
    add_table(
        doc,
        [
            ["Показатель", "Значение"],
            ["Общее количество объектов", str(metadata["total_samples"])],
            ["Обучающая выборка", str(metadata["train_samples"])],
            ["Тестовая выборка", str(metadata["test_samples"])],
            ["Количество источников данных", str(len(metadata["source_files"]))],
            ["Тип задачи", "Бинарная классификация"],
        ],
    )
    add_body_paragraph(
        doc,
        "Использование нескольких источников данных было необходимо, поскольку задача определения сарказма чувствительна к жанру текста и языковому контексту. Для русскоязычной части особое внимание было уделено расширению корпуса разговорных реплик, поскольку новости и сатирические заголовки не полностью отражают реальные пользовательские сообщения.",
    )

    doc.add_heading("1.4 Предварительная обработка текстовых данных", level=2)
    add_body_paragraph(
        doc,
        "Предварительная обработка текста выполнялась с целью приведения исходных данных к единому формату и устранения шумовых элементов. На данном этапе осуществлялись перевод текста в нижний регистр, удаление ссылок, удаление лишних пробелов и очищение текста от лишних символов. При этом сохранялись Unicode-символы, а также русские и английские символы, что особенно важно для работы с англоязычными и русскоязычными сообщениями.",
    )
    add_body_paragraph(
        doc,
        "Так как система ориентирована на обработку многоязычных данных, при предварительной обработке текста не удалялись символы кириллицы и другие Unicode-символы. Это позволило избежать потери информации и использовать единый подход как для английских, так и для русских текстов. Для табличной обработки данных использовалась библиотека pandas, а базовые численные операции выполнялись при помощи NumPy [2–3].",
    )
    add_body_paragraph(
        doc,
        "Кроме нормализованного текста, в проекте сохранялась и версия строки с учетом регистра, поскольку написание слов заглавными буквами, повторяющиеся знаки препинания и эмфатические конструкции могут выступать дополнительными индикаторами сарказма. Поэтому в системе используются как очищенные, так и частично исходные текстовые представления.",
    )

    doc.add_heading("1.5 Векторизация текста методом TF-IDF", level=2)
    add_body_paragraph(
        doc,
        "Для преобразования текстов в числовой формат использовался метод TF-IDF. В отличие от обычного словарного подхода, в проекте применялись символьные n-граммы, что позволяет работать с текстами на разных языках и снижает зависимость модели от конкретного словаря [4, 8]. Такой подход особенно удобен в задачах, где важны морфологические вариации, опечатки, усилители и фрагменты слов.",
    )
    add_body_paragraph(
        doc,
        "В реализованной системе TF-IDF-признаки строились как на символьных последовательностях, так и на словарных признаках очищенного текста. Дополнительно формировались прагматические признаки: доля заглавных букв, количество восклицательных и вопросительных знаков, наличие многоточий, повторяющейся пунктуации и типичных саркастических паттернов. Описание метода векторизации и его программная реализация опирались на официальную документацию scikit-learn [8].",
    )
    add_body_paragraph(
        doc,
        f"Максимальное количество признаков для векторизации в итоговой версии проекта составляло {metadata['max_features']}. Это позволило сохранить достаточно богатое пространство признаков и при этом избежать чрезмерного роста размерности, который мог бы усложнить обучение линейных моделей.",
    )

    doc.add_heading("1.6 Обучение моделей машинного обучения", level=2)
    add_body_paragraph(
        doc,
        "В рамках практики были обучены три модели машинного обучения: Logistic Regression, Linear SVM и Naive Bayes. Все модели обучались на одинаковых данных и одинаковом TF-IDF-представлении, что позволило корректно сравнить их качество. Для обучения и оценки моделей использовались средства библиотеки scikit-learn [5–8].",
    )
    add_body_paragraph(
        doc,
        "Модель Logistic Regression использовалась как основной линейный классификатор для разреженных признаков. Ее достоинством является хорошая интерпретируемость, устойчивость и высокая эффективность в задачах текстовой классификации [5]. Модель Linear SVM также относится к линейным методам и часто показывает близкое или более высокое качество на разреженных матрицах признаков [6]. Модель Naive Bayes была включена как базовый вероятностный алгоритм для сравнения [7].",
    )
    add_body_paragraph(
        doc,
        "В итоговой реализации после обучения базовой модели дополнительно подбирался порог принятия решения на валидационной части обучающей выборки. Кроме того, для коротких пользовательских реплик применялись дополнительные эвристические признаки, связанные с усилением интонации, использованием заглавных букв и типичных саркастических конструкций.",
    )

    doc.add_heading("1.7 Сравнение результатов моделей", level=2)
    add_body_paragraph(
        doc,
        "Для сравнения моделей использовались четыре метрики качества: Accuracy, F1-score, Precision и Recall. Все модели оценивались на одной и той же тестовой выборке. Итоговые результаты приведены в таблице 1.3.",
    )
    add_caption(doc, "Таблица 1.3 – Сравнение качества моделей")
    comparison_rows = [["Модель", "Accuracy", "F1-score", "Precision", "Recall"]]
    for row in model_rows:
        comparison_rows.append(
            [
                row["Model"],
                f"{float(row['Accuracy']):.4f}",
                f"{float(row['F1']):.4f}",
                f"{float(row['Precision']):.4f}",
                f"{float(row['Recall']):.4f}",
            ]
        )
    add_table(doc, comparison_rows)
    add_body_paragraph(
        doc,
        "Наилучший результат по Accuracy и F1-score показала модель Logistic Regression. Модель Linear SVM продемонстрировала близкие значения качества, однако немного уступила Logistic Regression. Модель Naive Bayes показала наиболее низкие результаты среди рассмотренных моделей, но также может использоваться как базовый алгоритм для решения задачи классификации текста.",
    )
    add_body_paragraph(
        doc,
        "Дополнительно в проекте была построена матрица ошибок, позволяющая увидеть распределение верных и неверных ответов. Матрица ошибок для итоговой модели представлена на рисунке 1.1.",
    )
    add_caption(doc, "Рисунок 1.1 – Матрица ошибок итоговой модели")
    doc.add_picture(str(CONFUSION_MATRIX_PATH), width=Inches(5.8))
    add_body_paragraph(
        doc,
        "Из матрицы ошибок видно, что итоговая модель достаточно устойчиво распознает оба класса, хотя часть саркастических и несаркастических сообщений остается неоднозначной. Это связано с тем, что сарказм часто зависит от контекста, который отсутствует в коротких отдельных репликах [9–10].",
    )

    doc.add_heading("1.8 Тестирование системы на пользовательских примерах", level=2)
    add_body_paragraph(
        doc,
        "После обучения моделей была проведена проверка системы на пользовательских примерах. Такая проверка позволила оценить поведение модели на коротких фразах, близких к реальным сообщениям. В таблице 1.4 приведены два примера предсказаний итоговой системы.",
    )
    add_caption(doc, "Таблица 1.4 – Примеры предсказаний системы")
    add_table(
        doc,
        [
            ["Текст", "Предсказание", "Вероятность сарказма"],
            ["это шаурма ТАКАЯ вкусная", "Sarcastic", "95.21%"],
            ["я люблю эту песню", "Not Sarcastic", "6.37%"],
        ],
    )
    add_body_paragraph(
        doc,
        "Полученные результаты показывают, что разработанная система способна классифицировать как саркастичные, так и несаркастичные пользовательские фразы. При этом необходимо учитывать, что сарказм часто зависит от контекста, поэтому отдельные короткие фразы могут классифицироваться ошибочно. Именно поэтому в проекте дополнительно анализировались порог принятия решения и специальные эмфатические признаки.",
    )

    doc.add_heading("1.9 Возникшие затруднения и способы их решения", level=2)
    add_body_paragraph(
        doc,
        "В ходе практики возникло несколько затруднений. Во-первых, определение сарказма без контекста является сложной задачей, поскольку короткая фраза может интерпретироваться по-разному в зависимости от ситуации. Во-вторых, в англоязычных и русскоязычных текстах наблюдаются разные речевые маркеры сарказма, что усложняет использование полностью унифицированного подхода. В-третьих, исходные датасеты относились к разным жанрам текста, поэтому требовалось их аккуратное объединение.",
    )
    add_body_paragraph(
        doc,
        "Также отдельной задачей стал подбор подходящего способа векторизации. Обычный словарный подход оказался менее удобным для работы с разнородными текстами, поэтому был выбран символьный TF-IDF, дополненный словарными и прагматическими признаками. Кроме того, возникали ошибки модели на неоднозначных фразах, особенно если фраза была очень короткой и не содержала явных событийных индикаторов.",
    )
    add_body_paragraph(
        doc,
        "Для решения указанных проблем использовались несколько подходов: объединение нескольких датасетов, применение Unicode-safe preprocessing, использование символьного TF-IDF, сравнение нескольких моделей и анализ метрик Accuracy, Precision, Recall и F1-score. Дополнительно были введены эвристические признаки для обработки эмоционального усиления и использования прописных букв, а для русскоязычной части корпуса был расширен набор разговорных примеров.",
    )

    doc.add_heading("Заключение", level=1)
    add_heading = doc.add_heading
    doc.add_heading("8.1 Приобретенные знания, умения и навыки", level=2)
    add_body_paragraph(
        doc,
        "В ходе практики были приобретены навыки анализа предметной области, работы с текстовыми данными, предварительной обработки данных, применения методов NLP, обучения моделей машинного обучения, оценки качества моделей и разработки программной системы на Python. Кроме того, была отработана практика оформления результатов исследования в виде таблиц, визуализаций и итогового отчета.",
    )
    doc.add_heading("8.2 Информационно-программные продукты", level=2)
    add_body_paragraph(
        doc,
        "При выполнении практики использовались следующие информационно-программные продукты: Python, pandas, scikit-learn, NumPy, matplotlib, joblib, Streamlit, Visual Studio Code / PyCharm и Git. Указанные инструменты обеспечили загрузку и подготовку данных, обучение и сохранение моделей, проведение вычислительных экспериментов и создание пользовательского интерфейса.",
    )
    doc.add_heading("8.3 Предложения и рекомендации", level=2)
    add_body_paragraph(
        doc,
        "В дальнейшем разработанную систему можно улучшить за счет использования более крупных многоязычных датасетов, расширения набора языков, применения трансформерных моделей mBERT и XLM-RoBERTa, а также учета контекста сообщения и анализа эмоциональной окраски текста. Также представляется полезным дальнейшее расширение русскоязычного разговорного корпуса и анализ более длинных диалоговых сообщений.",
    )

    doc.add_heading("Список использованных источников", level=1)
    for idx, item in enumerate(source_list(), start=1):
        paragraph = doc.add_paragraph(style="Normal")
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.5
        paragraph.add_run(f"{idx}. {item}")

    doc.add_heading("Приложения", level=1)
    doc.add_heading("Приложение А. Фрагмент программного кода", level=2)
    add_body_paragraph(doc, "В приложении А приведены фрагменты кода, реализующие загрузку данных, предварительную обработку текста, обучение моделей и предсказание для пользовательского сообщения.")
    add_caption(doc, "Листинг А.1 – Загрузка данных")
    add_code_block(doc, get_code_snippet(PROJECT_ROOT / "src" / "data_loader.py", 56, 83))
    add_caption(doc, "Листинг А.2 – Предварительная обработка текста")
    add_code_block(doc, get_code_snippet(PROJECT_ROOT / "src" / "preprocessing.py", 8, 28))
    add_caption(doc, "Листинг А.3 – Обучение модели")
    add_code_block(doc, get_code_snippet(PROJECT_ROOT / "src" / "train.py", 19, 112))
    add_caption(doc, "Листинг А.4 – Предсказание текста")
    add_code_block(doc, get_code_snippet(PROJECT_ROOT / "src" / "predict.py", 14, 59))

    doc.add_heading("Приложение Б. Результаты сравнения моделей", level=2)
    add_body_paragraph(doc, "В приложении Б представлены таблица и график, полученные в ходе сравнения моделей машинного обучения.")
    add_caption(doc, "Таблица Б.1 – Сравнение моделей")
    add_table(doc, comparison_rows)
    add_caption(doc, "Рисунок Б.1 – Графическое сравнение моделей")
    doc.add_picture(str(MODEL_COMPARISON_PLOT_PATH), width=Inches(5.8))

    doc.add_heading("Приложение В. Примеры работы программы", level=2)
    add_body_paragraph(doc, "В приложении В приведены примеры предсказаний программы, выполненные после обучения итоговой модели Logistic Regression.")
    add_table(
        doc,
        [
            ["Текст", "Предсказание", "Вероятность сарказма"],
            ["это шаурма ТАКАЯ вкусная", "Sarcastic", "95.21%"],
            ["я люблю эту песню", "Not Sarcastic", "6.37%"],
            ["это ТАК интересно", "Sarcastic", "100.00%"],
            ["Мне понравился этот фильм.", "Not Sarcastic", "1.55%"],
        ],
    )
    add_body_paragraph(doc, "Также к отчету приложены сохраненные артефакты эксперимента: матрица ошибок, отчет по метрикам и таблица сравнения моделей.")

    doc.add_heading("Приложение Г. Структура проекта", level=2)
    add_body_paragraph(doc, "Структура программного проекта представлена ниже.")
    add_code_block(
        doc,
        """multilingual-sarcasm-detection/
├── data/
├── models/
├── results/
├── src/
├── app.py
├── main.py
├── requirements.txt
└── README.md""",
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    output_path = build_report()
    print(output_path)
